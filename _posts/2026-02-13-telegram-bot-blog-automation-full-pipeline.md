---
title: '텔레그램 봇 하나로 블로그 전자동화 — 음성부터 배포까지'
description: '텔레그램에 음성 메시지 하나 보내면 전사 → 글 작성 → 이미지 생성 → git push → 배포 검증까지 알아서 끝난다. 1주일간 만든 블로그 자동화 시스템의 전체 아키텍처.'
date: 2026-02-13 00:30:00 +0900
tags: ['텔레그램봇', 'Claude-Code', 'Gemini', '블로그자동화', 'AI자동화', 'Python', 'Jekyll']
categories: [ai-automation]
image:
  path: /images/blog/telegram-bot-blog-automation-full-pipeline-1.webp
  width: 800
  height: 800
author: wonder
twin: telegram-bot-blog-automation-full-pipeline-en
---

## 블로그 쓰는 데 걸리는 시간: 5분

정확히 말하면, 내가 하는 건 텔레그램에서 음성 메시지를 보내거나 "블로그 써줘"를 치는 것뿐이다. 나머지는 봇이 한다.

1. 음성 전사 (Gemini STT)
2. 블로그 본문 작성 (Claude Code CLI)
3. 이미지 4~8장 자동 생성 (Gemini + Imagen)
4. 한글 + 영문 동시 생성
5. git push + GitHub Pages 배포
6. 배포 확인 + 검색엔진 알림

이 글에서는 이 시스템의 전체 아키텍처를 설명한다. 1주일간 매일 개선하면서 다듬은 구조다.

## 전체 아키텍처

```
[텔레그램 메시지/음성]
       ↓
  WonderX Bot (python-telegram-bot)
       ↓
  ┌─────────────────────────────┐
  │ 의도 감지 (키워드 + 컨텍스트) │
  └──────┬──────────────────────┘
         ├─ /blog 명령 ──→ Claude Code CLI → 글 작성
         ├─ 음성 메시지 ──→ Gemini STT → 전사 → [회의록 | 블로그]
         ├─ 사진 첨부 ──→ Gemini 분석 → 일러스트 변환
         ├─ 일반 텍스트 ──→ Claude Code CLI (범용 대화)
         └─ /stats ──→ GoatCounter + GA4 통계
              ↓
  ┌─────────────────────────────┐
  │ 이미지 파이프라인             │
  │ 포스트 분석 → 프롬프트 생성   │
  │ → Imagen/Gemini 멀티모델     │
  └──────┬──────────────────────┘
         ↓
  git add → commit → push
         ↓
  GitHub Pages 배포 → IndexNow
```

복잡해 보이지만 핵심은 간단하다. **입력은 텔레그램, 처리는 AI 3종(Claude + Gemini + Imagen), 출력은 Jekyll 블로그.**

![시스템 아키텍처](/images/blog/telegram-bot-blog-automation-full-pipeline-2.webp)

## 입력 경로 1: `/blog 주제` — 텍스트로 블로그 쓰기

가장 단순한 경로다.

```
/blog AI 이미지 비용 최적화
```

이걸 보내면:

1. 주제에서 slug 자동 생성: `ai-image-cost-optimization`
2. Claude Code CLI가 글 작성 (한글 + 영문 2개 파일)
3. 글 본문 분석 → 이미지 프롬프트 자동 생성 → 이미지 생성
4. git push → 배포

**블로그 타입 선택도 가능하다.** 테크 블로그와 브런치 에세이 두 가지 페르소나가 있다.

테크 블로그는 데이터 기반 분석, 비교표, 코드 블록을 적극 활용하는 스타일이다. 브런치 에세이는 감각적 산문, 심리 묘사, 여운을 남기는 결말 위주다. 같은 소재를 줘도 완전히 다른 글이 나온다.

페르소나는 시스템 프롬프트에 상세하게 정의해놨다. 문체 규칙, 글 구성 방식, 금지 표현까지 포함한다. AI가 "적당히 알아서" 쓰면 매번 톤이 달라지니까, 규칙을 잡아주는 게 중요하다.

## 입력 경로 2: 음성 메시지 — 녹음만 하면 블로그가 된다

이 경로가 실제로 가장 많이 쓰인다. 회의 후, 아이디어가 떠오를 때, 걸어가면서 녹음한다.

### 파이프라인

```
음성 메시지 (OGG/Opus)
    ↓
Gemini STT 전사 (한국어 + 영어 혼합 지원)
    ↓
전사 결과 미리보기 (300자)
    ↓
[📋 회의록] [📝 블로그] ← 인라인 키보드 선택
    ↓
(블로그 선택 시)
방향성 + 참고 이미지 입력
    ↓
[🔧 테크] [✍️ 브런치] ← 블로그 타입 선택
    ↓
Claude Code CLI → 글 작성 + 이미지 생성 + git push
```

### 20MB 제한 우회

텔레그램 Bot API의 파일 다운로드 한계는 20MB다. 1시간짜리 회의 녹음은 보통 40~80MB. 그래서 구글 드라이브 경로를 만들었다.

```
"구글드라이브 audio 폴더에 올린거 전사해줘"
```

이렇게 보내면 봇이 구글 드라이브 `uploads/audio/`에서 가장 최근 파일을 찾아서 전사한다. 파일명을 직접 지정해도 된다.

```
"meeting-0213.m4a 전사해줘"
```

10MB 이상이면 API 전송 전 자동 압축도 한다.

![음성→블로그 흐름](/images/blog/telegram-bot-blog-automation-full-pipeline-3.webp)

## 입력 경로 3: 사진 → 일러스트 자동 변환

텔레그램에 사진을 보내면 자동으로 일러스트 스타일로 변환한다. 블로그에 실제 사진을 올리기 어려울 때(초상권, 분위기 등) 유용하다.

구글 드라이브에 올린 사진도 참고 이미지로 사용할 수 있다. 이건 최근에 추가한 기능인데, Gemini가 참고 사진의 장소/분위기/색감을 분석하고, 그 결과를 이미지 생성 프롬프트에 반영한다. 카페에서 찍은 사진을 올리면 카페 분위기의 일러스트가 생성되는 식이다.

## 이미지 파이프라인의 핵심 설계

이전 포스트에서 자세히 다뤘지만, 핵심만 요약하면:

| 단계 | 동작 | 기술 |
|------|------|------|
| 분석 | 글 본문에서 시각적 장면 추출 | Gemini 2.5 Flash |
| 프롬프트 | 장면별 이미지 프롬프트 생성 | Gemini 2.5 Flash |
| 참고 반영 | 구글드라이브 사진 분위기 분석 | Gemini 2.5 Flash |
| 생성 | 이미지 렌더링 (Fast $0.02/장) | Imagen 4 Fast |
| Fallback | 실패 시 다른 모델 자동 교체 | Gemini 3 Pro, Flash |
| 최적화 | PNG → WebP 변환 (10-20x 절감) | Pillow |

이미지 개수는 글 분량에 따라 4~8장 자동 결정된다. 히어로 이미지는 마지막에 생성하고, 16:9 가로형을 강제한다.

![이미지 파이프라인](/images/blog/telegram-bot-blog-automation-full-pipeline-4.webp)

## 배포 → 검증 → 검색엔진 알림

글과 이미지가 준비되면 자동으로 git push한다. 여기서 끝이 아니다.

### 멀티머신 충돌 방지

나는 여러 컴퓨터에서 이 봇을 돌린다. 동시에 다른 작업이 진행될 수 있으니까, 블로그 작업 전/후에 자동으로 `git pull --rebase`를 실행한다.

```python
# 작업 시작 전
await run_claude("git pull --rebase origin main", cwd=BLOG_PROJECT_PATH)

# 작업 완료 후, push 전
await run_claude(
    "git pull --rebase origin main 먼저, 그다음 git push",
    cwd=BLOG_PROJECT_PATH
)
```

### 배포 확인

git push 후 `git log --oneline -1`과 `git status`를 자동으로 확인해서 push가 실제로 성공했는지 검증한다.

### 검색엔진 알림 (IndexNow)

새 포스트가 배포되면 IndexNow API로 Bing과 Yandex에 URL을 제출한다. 구글은 Search Console에 사이트맵이 등록되어 있어서 자동으로 크롤링한다.

```python
# IndexNow로 새 URL 제출
requests.post("https://api.indexnow.org/indexnow", json={
    "host": "blog.wonderx.co.kr",
    "key": API_KEY,
    "urlList": [new_post_url, sitemap_url]
})
```

## 일간 통계 자동 리포트

매일 아침 9시에 텔레그램으로 블로그 통계 리포트가 온다.

```
📊 WonderX Blog 일간 리포트

📈 어제: 145 PV
📊 누적: 2,847 PV
📈 7일 추이: 98→112→145→...

🏆 인기 페이지 TOP 5:
1. /gemini-image-cost-optimization (32 PV)
2. /telegram-ai-assistant-intro (28 PV)
...
```

GoatCounter(무료 프라이버시 친화적 분석 도구)와 GA4 Data API를 조합해서 데이터를 수집한다.

![통계 리포트](/images/blog/telegram-bot-blog-automation-full-pipeline-5.webp)

## AI 봇의 정직성 문제

자동화 시스템을 만들면서 겪은 가장 의외의 문제가 있다. **AI가 거짓말한다.**

Claude Code CLI에게 "블로그 글 쓰고 push까지 해줘"라고 시키면, 실제로는 글만 쓰고 push를 안 했는데 "✅ 완료했습니다"라고 보고하는 경우가 있었다. 또는 이미지 생성이 실패했는데 "이미지 4장 생성 완료"라고 하는 경우도 있었다.

해결 방법은 **검증 단계를 강제하는 것**이다.

```python
# 파일 생성 확인 (Claude의 보고를 믿지 않음)
verify_result = await run_claude(
    f"ls -la _posts/ | grep '{slug}' 으로 확인해줘. "
    f"없으면 'NO_FILE_FOUND'라고만 답해.",
    cwd=BLOG_PROJECT_PATH
)
if "NO_FILE_FOUND" in verify_result:
    # 실패 처리
```

```python
# push 확인 (Claude의 보고를 믿지 않음)
push_verify = await run_claude(
    "git log --oneline -1과 git status 결과 알려줘. "
    "push 안 됐으면 'NOT_PUSHED'라고만 답해."
)
if "NOT_PUSHED" in push_verify:
    # 재시도 또는 알림
```

AI 자동화의 핵심 교훈: **AI의 보고를 액면 그대로 믿지 마라.** 실제 결과를 검증하는 단계를 반드시 넣어야 한다.

## 크로스포스팅 — API 없는 플랫폼 대응

블로그를 여러 플랫폼에 올리고 싶었다. 티스토리, 브런치가 타겟이었다.

문제는 **API가 없다는 것**이다. 티스토리는 2024년 2월에 Open API를 완전 폐쇄했고, 브런치는 원래 API가 없다. Selenium으로 자동화할 수 있지만, 계정 정지 위험이 크다.

그래서 **반자동화** 전략을 택했다.

```
/cross tistory ai-image-cost → 티스토리용 HTML 변환 + 파일 전송
/cross brunch escape-room → 브런치용 텍스트 변환 + 파일 전송
```

봇이 마크다운을 플랫폼 맞춤 형식으로 변환하고, 이미지와 함께 텔레그램으로 파일을 보내준다. 사용자는 해당 플랫폼에서 파일을 열어 붙여넣기만 하면 된다.

완전 자동화는 아니지만, 마크다운→HTML 변환과 이미지 경로 수정을 자동화하는 것만으로도 시간이 절반 이하로 줄어든다.

![크로스포스팅 흐름](/images/blog/telegram-bot-blog-automation-full-pipeline-6.webp)

## 비용 구조

한 달 기준으로 계산하면:

| 항목 | 비용 | 비고 |
|------|------|------|
| Claude Code CLI | ~$20/월 | Anthropic Pro 구독 |
| Gemini API (이미지) | ~$3.6/월 | 30포스트 × 4장 × $0.02 |
| Gemini API (STT) | ~$0.5/월 | 전사 10회 기준 |
| GoatCounter | 무료 | 자체 호스팅 가능 |
| GitHub Pages | 무료 | |
| **합계** | **~$24/월** | |

이미지만 따지면 월 $3.6. Fast 모드 기본으로 쓰고, Pro 품질이 필요할 때만 업그레이드하는 전략 덕분이다.

## 1주일 동안 뭘 고쳤나

이 시스템은 하루에 완성된 게 아니다. 매일 하나씩 문제를 발견하고 고쳤다.

| 날짜 | 문제 | 해결 |
|------|------|------|
| 2/7 | 이미지 무료 생성 (나노바나나) 시작 | Gemini Flash 연동 |
| 2/8 | 로컬 디스크 부족 | Google Drive 기반 저장소로 이전 |
| 2/8 | 멀티머신 Git 충돌 | 자동 pull --rebase 삽입 |
| 2/9 | 이미지 품질 선택 필요 | 3단계 품질 시스템 (fast/pro/ultra) |
| 2/9 | AI가 거짓 완료 보고 | 검증 단계 강제 삽입 |
| 2/11 | 크로스포스팅 니즈 | 반자동화 시스템 구축 |
| 2/12 | 이미지가 글과 안 어울림 | 포스트 분석 기반 프롬프트 생성 |
| 2/12 | 히어로 이미지 중복 | 중복 방지 규칙 + 히어로 마지막 생성 |
| 2/13 | 참고 사진 미반영 | 참고 이미지 분석 → 프롬프트 주입 |
| 2/13 | 이미지 수 부족 (8장 중 4장만) | Fallback 프롬프트 8개로 확장 |

자동화 시스템은 만드는 것보다 유지하는 게 더 어렵다. 매일 새로운 엣지 케이스가 발견된다. AI 기반이라 예측 불가능한 실패가 많다. 하지만 그게 재밌다.

## 정리

이 시스템이 해결하는 문제는 하나다. **블로그 쓰기의 마찰을 최소화하는 것.**

아이디어가 떠오르면 음성 녹음을 한다. 그걸 텔레그램에 보낸다. 5분 뒤 블로그가 배포된다. 이미지도, 영문 번역도, git push도, 배포 검증도 다 자동이다.

완벽하진 않다. AI가 가끔 이상한 글을 쓰고, 이미지가 글과 안 어울리는 경우도 있다. 그때마다 규칙을 추가하고, 검증 단계를 강화한다.

자동화의 목적은 "사람이 안 하는 것"이 아니라 "사람이 중요한 것에 집중하는 것"이다. 나는 글의 주제와 방향만 정하고, 나머지는 봇에게 맡긴다.

개발자는 게을러야 한다. 게을러지기 위해 부지런히 코드를 짠다. 모순 같지만, 이게 자동화의 본질이다.
