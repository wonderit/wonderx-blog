---
title: 'OpenClaw 스타일 메모리 시스템 구현하기 — AI 비서가 기억하는 법'
description: 'OpenClaw의 파일 기반 메모리를 분석하고, Claude Code 텔레그램 봇에 적용했다. MEMORY.md + 일일 노트로 대화 전체가 아닌 중요한 것만 기억한다.'
date: 2026-02-06 00:00:00 +0900
tags: ['claude-code', 'telegram', 'openclaw', 'memory', 'automation', 'vibe-coding']
categories: [ai-automation]
image: /assets/img/blog/openclaw-memory-1.png
author: wonder
---

## 왜 메모리가 필요한가

[지난 편](/posts/telegram-bot-setup)에서 텔레그램 봇을 만들었다.
문제는, 이 봇이 **금붕어**라는 거다. 메시지를 보낼 때마다 새 세션이라 아무것도 기억 못 한다.

"아까 그 코드 수정해줘" → "무슨 코드요?"

이러면 비서가 아니라 그냥 챗봇이다.

## OpenClaw는 어떻게 하나

요즘 핫한 OpenClaw의 메모리 시스템을 분석해봤다. 핵심은 의외로 단순하다:

> **파일이 기억이다.** 대화 전체가 아니라, 중요한 것만 마크다운 파일에 저장한다.

### OpenClaw 메모리 구조

```
MEMORY.md              ← 장기 기억 (선호도, 결정사항)
memory/2026-02-06.md   ← 오늘 일일 노트
memory/2026-02-05.md   ← 어제 일일 노트
```

**동작 원리:**

1. 세션 시작 → `MEMORY.md` + 오늘/어제 노트만 읽음
2. 대화 중 → AI가 "이건 기억해야겠다" 판단하면 파일에 기록
3. 컨텍스트 다 찰 때 → 자동으로 중요한 거 저장 (memory flush)
4. 다음 세션 → 저장된 파일을 읽어서 맥락 유지

벡터 DB도 아니고, 복잡한 RAG도 아니다. **그냥 마크다운 파일**이다.
사람이 직접 열어서 편집할 수도 있다. 이게 핵심이다.

![OpenClaw 메모리 구조](/assets/img/blog/openclaw-memory-2.png)

## 우리 봇에 적용

### v1 (이전): 대화 전체를 JSON에 저장

```json
[
  {"role": "user", "content": "블로그 배포해줘", "timestamp": "..."},
  {"role": "assistant", "content": "배포 완료...", "timestamp": "..."},
  ...40개 메시지 전부 저장
]
```

문제: 토큰 낭비, 쓸데없는 대화도 다 포함, 파일이 점점 커짐.

### v2 (현재): OpenClaw 스타일 — 중요한 것만 저장

```
data/
├── MEMORY.md         ← "사용자는 conda 선호", "ENFP 개발자"
└── daily/
    ├── 2026-02-07.md  ← 오늘 뭐 했는지
    └── 2026-02-06.md  ← 어제 뭐 했는지
```

## 구현

### 1. [MEMO] 태그 — AI가 알아서 기억할 걸 고른다

시스템 프롬프트에 이렇게 넣었다:

```
중요: 대화 중 기억할 만한 정보가 있으면 답변 마지막에 아래 형식으로 알려줘:
[MEMO] 기억할 내용
```

Claude가 응답할 때 중요하다고 판단하면 `[MEMO]` 태그를 붙여준다.
봇이 이걸 파싱해서 자동 저장하고, 사용자에겐 태그 없는 깨끗한 응답만 보여준다.

```python
def extract_and_save_memos(response: str) -> str:
    lines = response.split("\n")
    clean_lines = []
    memos = []

    for line in lines:
        if line.strip().startswith("[MEMO]"):
            memo = line.strip()[6:].strip()
            memos.append(memo)
        else:
            clean_lines.append(line)

    for memo in memos:
        # "선호", "항상" 같은 키워드 → 장기 기억
        # 그 외 → 일일 노트
        if any(kw in memo for kw in ["선호", "항상", "기본", "설정"]):
            append_memory(memo)
        else:
            append_daily_note(memo)

    return "\n".join(clean_lines).strip()
```

### 2. 장기 기억 (MEMORY.md)

선호도, 프로필, 중요 결정사항. 세션마다 항상 로드된다.

```markdown
# WonderX 장기 기억

- [2026-02-06 17:30] 사용자는 conda 환경을 선호한다
- [2026-02-06 17:45] 블로그 프레임워크: Astro + GitHub Pages
- [2026-02-06 18:00] 댓글 시스템: Disqus (게스트 댓글 가능)
```

수동 저장도 가능하다:

```
/remember conda 환경 이름은 wonderx-bot
```

### 3. 일일 노트 (daily/YYYY-MM-DD.md)

오늘 뭘 했는지. 오늘 + 어제 노트만 자동 로드된다.

```markdown
# 2026-02-06 일일 노트

- [17:00] 사용자: 텔레그램 봇 만들어줘
- [17:15] 블로그 SEO 최적화 작업 시작
- [17:30] 카테고리 사이드바 추가
- [18:00] OpenClaw 스타일 메모리 시스템 구현
```

### 4. 프롬프트 조합

Claude에게 보내는 프롬프트 구조:

```
[시스템 지시]
너는 WonderX AI 비서야. 게으른 개발자의 비서...

---

[장기 기억]
# WonderX 장기 기억
- conda 선호, Astro 블로그, Disqus 댓글...

[최근 노트]
# 2026-02-06 일일 노트
- 텔레그램 봇 구현, 메모리 시스템 구현...

---

[현재 요청]
아까 만든 메모리 시스템에 검색 기능 추가해줘
```

이렇게 하면 Claude가 **오늘 뭘 했는지 알고 있는 상태**에서 답변한다.

![메모리 시스템 동작 화면](/assets/img/blog/openclaw-memory-3.png)

## OpenClaw vs WonderX Bot 비교

| | OpenClaw | WonderX Bot |
|---|---|---|
| **메모리 방식** | 마크다운 파일 | 마크다운 파일 (동일) |
| **자동 저장** | memory flush + AI 판단 | [MEMO] 태그 + AI 판단 |
| **수동 저장** | "이거 기억해" 자연어 | `/remember` 명령어 |
| **비용** | API 토큰 과금 (Heartbeat에 하룻밤 $20) | Max 플랜 포함 ($0) |
| **검색** | SQLite + 벡터 + BM25 하이브리드 | 오늘/어제만 로드 (심플) |
| **복잡도** | TypeScript 39개 파일 | Python 1개 파일 (memory.py) |

OpenClaw은 시맨틱 검색, 임베딩, SQLite 인덱스까지 있지만, 솔직히 개인 비서 수준에서는 과하다.
오늘/어제 노트 + 장기 기억이면 충분하다. **나중에 필요하면 검색 기능을 추가하면 된다.**

## 새 명령어

| 명령 | 기능 |
|---|---|
| `/memory` | 현재 기억 상태 조회 |
| `/remember 내용` | 장기 기억에 수동 저장 |
| `/clear` | 장기 기억 초기화 |

## 삽질 포인트

### 대화 전체 저장은 비효율적이다

처음에 v1으로 대화 전체를 JSON에 저장했다. 20개 메시지만 유지해도 프롬프트가 엄청 길어진다.
OpenClaw 방식으로 바꾸니까 프롬프트 길이가 1/5로 줄었다.

### [MEMO] 태그는 시스템 프롬프트에 명확하게

"기억해야 할 것을 저장해줘"라고 모호하게 쓰면 Claude가 뭘 저장해야 할지 헷갈려한다.
`[MEMO]` 같은 명확한 포맷을 지정하고, 예시를 주는 게 핵심이다.

### 장기 vs 일일 분류가 중요

"사용자는 conda를 선호한다" → 장기 기억
"오늘 블로그 배포했다" → 일일 노트

이걸 잘 분류해야 장기 기억이 쓸데없는 정보로 오염되지 않는다.

## 다음 편 예고

- **스케줄링 & Heartbeat**: 매일 아침 상태 알림, 블로그 빌드 체크 자동화
- OpenClaw에서 제일 인기 있는 기능이고, 이게 되면 진짜 "자동 비서"가 된다

---

*전체 코드는 비공개 레포에 있다. 궁금한 건 [x@wonderx.co.kr](mailto:x@wonderx.co.kr)로.*
