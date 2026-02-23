---
title: "AI 봇이 거짓말하는 문제를 어떻게 해결했나 — 4단계 검증 시스템"
description: "Claude Code 기반 텔레그램 봇이 '완료했습니다'라고 거짓 보고하는 문제. 원인을 분석하고 git diff + 파일 검증 + 배포 확인까지 4단계 검증 시스템을 구축한 실전기."
date: 2026-02-21 09:00:00 +0900
image: /images/blog/ai-bot-lies-verification-system-1.webp
tags: ['AI자동화', 'Claude-Code', '텔레그램봇', 'LLM', '검증시스템', 'Python']
categories: [tech]
author: wonder
lang: ko
twin: ai-bot-lies-verification-system-en
---

## "완료했습니다" — 진짜?

텔레그램으로 AI 봇에게 블로그 글을 써달라고 했다. 5분 후 답이 왔다.

> ✅ 블로그 포스팅 완료! 한글, 영문 버전 모두 작성하고 git push까지 마쳤습니다.

사이트에 들어가봤다. **글이 없다.**

git log를 확인했다. **커밋이 없다.**

_posts 폴더를 열어봤다. **파일 자체가 생성되지 않았다.**

AI가 거짓말을 한 거다. 의도적으로? 아니다. 하지만 결과적으로 **"완료했다"는 보고가 완전히 거짓**이었다. 이 일이 한 번이 아니라 반복적으로 벌어졌다.

---

## 왜 AI가 "거짓 완료 보고"를 하는가

Claude Code CLI를 백엔드로 쓰는 텔레그램 봇을 운영하면서, AI의 거짓 완료 보고 패턴을 분석했다. 크게 세 가지 원인이 있었다.

### 1. 예외 처리가 씹히는 경우

가장 흔한 케이스. Claude가 파일을 생성하려다 permission 에러, 경로 에러, 혹은 파일 시스템 문제가 발생했는데 **예외를 제대로 처리하지 않고 넘어간다.** "파일을 작성하겠습니다" → 실패 → 하지만 전체 프로세스는 계속 진행 → "완료했습니다."

실제로 봇 로그를 뒤져보면 이런 패턴이 반복된다:

```
[INFO] Claude 작업 시작: 블로그 한/영 생성
[INFO] Claude 응답 수신 (status: success)
[ERROR] _posts/ 파일 확인: No such file
```

Claude는 "success"를 반환했지만, 실제 파일은 없다.

### 2. 비동기 타이밍 이슈

Python의 `asyncio` 기반 봇에서 Claude CLI는 subprocess로 실행된다. timeout이 600초인데, 실제 작업이 그 안에 끝나지 않으면 중간 결과만 반환된다. Claude가 "한글 파일은 생성했고, 영문 파일은 지금 작성 중—" 여기서 잘렸는데, 봇은 이걸 완료로 처리한다.

### 3. LLM의 "낙관적 보고" 본성

이게 가장 근본적인 문제다. LLM은 **태생적으로 긍정적 완료를 보고하는 쪽으로 편향**되어 있다. "파일을 생성하겠습니다"라고 계획을 세운 후, 실행 중 문제가 생겨도 "생성을 완료했습니다"라고 답하는 경향이 있다. 계획과 실행을 구분하지 못하는 것이다.

---

## 4단계 검증 시스템

거짓 보고를 막기 위해 **AI의 말을 절대 믿지 않는** 검증 시스템을 구축했다. Trust, but verify — 아니, **don't trust, just verify.**

### Step 1: 파일 존재 확인

```python
# Step 1.5: 파일 생성 확인 — 한글+영문 2개 (verification)
verify_result = await run_claude(
    f"ls -la _posts/ | grep '{slug}' 으로 "
    f"한글({slug}.md)과 영문({slug}-en.md) 두 파일이 있는지 확인해줘. "
    f"두 파일 중 하나라도 없으면 'NO_FILE_FOUND'라고만 답해.",
    cwd=BLOG_PROJECT_PATH,
    timeout=30,
)

if "NO_FILE_FOUND" in verify_result:
    await status_msg.edit_text(
        f"❌ 블로그 파일이 생성되지 않았다 (한/영 2개 필요)."
    )
    return
```

Claude가 "완료했습니다"라고 해도, **별도의 Claude 세션**에서 `ls -la`로 파일이 실제로 존재하는지 물리적으로 확인한다. 없으면 바로 실패 처리.

핵심은 **작업한 Claude와 검증하는 Claude를 분리**한 것이다. 같은 세션에서 "파일 만들었지?" 하면 "네, 만들었습니다"라고 답할 가능성이 높다. 별개 세션에서 파일 시스템을 직접 확인해야 한다.

### Step 2: git 상태 확인

```python
# Step 3.5: git push 확인 (verification)
push_verify = await run_claude(
    "git log --oneline -1 결과와 git status 결과를 알려줘. "
    "push가 안 됐으면 'NOT_PUSHED'라고 답해.",
    cwd=BLOG_PROJECT_PATH,
    timeout=30,
)

push_failed = "NOT_PUSHED" in push_verify
```

파일이 있어도 git push가 안 됐을 수 있다. rebase 충돌, 인증 만료, 네트워크 에러 — push가 실패하는 경우는 다양하다. Claude의 "push 완료" 보고를 믿지 않고 `git log`와 `git status`를 별도로 확인한다.

### Step 3: 상태 이모지 3종 분류

보고를 받으면 사람은 "완료"와 "실패" 두 가지로만 판단하기 쉽다. 하지만 실제로는 세 가지 상태가 필요하다:

| 이모지 | 상태 | 의미 |
|--------|------|------|
| ✅ | 완료 | 파일 생성됨 + push 성공 + 배포 확인 |
| ⚠️ | 부분 완료 | 파일은 있지만 push 실패 or 배포 미확인 |
| ❌ | 실패 | 파일 자체가 생성되지 않음 |

"부분 완료" 상태를 도입한 게 큰 차이를 만들었다. 이전에는 push가 실패해도 ✅로 보고했기 때문에 문제를 인지하지 못했다.

### Step 4: 배포 후 실제 URL 접근 검증

가장 강력한 마지막 관문. GitHub Pages로 배포된 후 **실제 URL에 접근해서 페이지가 존재하는지 확인**한다.

```python
async def _verify_blog_deployment(slug, max_wait=90):
    """배포 후 실제 사이트에서 검증"""
    post_url = f"{BLOG_BASE_URL}/posts/{slug}/"

    async with aiohttp.ClientSession() as session:
        for attempt in range(max_wait // 10):
            await asyncio.sleep(10)
            status, length = await _check_url(session, post_url)
            if status == 200 and length > 5000:
                deployed = True
                break
```

10초 간격으로 최대 90초까지 폴링한다. 200 응답이 와도 content_length가 5000 미만이면 빈 페이지로 간주한다. 이미지 URL까지 개별 체크해서 "페이지는 있는데 이미지가 깨진" 상태도 잡아낸다.

이 검증은 비동기 백그라운드 태스크로 돌린다. 사용자에게 "배포 완료" 알림을 먼저 보내고, 실제 배포 확인은 뒤에서 진행해서 문제가 있으면 별도 알림을 보낸다.

---

## "이미지 URL인데 HTML이 오면" — 함정 잡기

배포 검증에서 한 가지 교묘한 함정이 있었다. 이미지 URL에 GET 요청을 보냈는데 **200 OK가 돌아온다.** 하지만 실제 응답은 이미지가 아니라 **404 HTML 페이지**였다.

```python
async def _check_url(session, url):
    async with session.get(url, ssl=False) as resp:
        content_type = resp.headers.get("Content-Type", "")
        # 이미지 URL인데 HTML이 오면 → 실패 처리
        if any(ext in url.lower() for ext in [".webp", ".png", ".jpg"]):
            if "text/html" in content_type:
                return 404, len(body)  # 실제 404로 재분류
```

GitHub Pages의 커스텀 404 페이지가 200 OK를 반환하는 경우가 있다. URL이 `.webp`로 끝나는데 `Content-Type: text/html`이 오면 — 그건 이미지가 아니라 404 페이지다. 이 한 줄 체크가 없었으면 "이미지 배포 완료"라는 거짓 보고가 계속됐을 것이다.

---

## 실전에서 배운 것 — AI 디버깅의 핵심

이 검증 시스템을 만드는 과정에서 가장 중요하게 배운 건 기술적인 부분이 아니었다.

**AI 봇과 일하면서 가장 효과적인 디버깅 방법은 "현상을 보고 원인을 대강 짐작하는 능력"이다.**

봇에게 "블로그 한/영 두 개 써줘"라고 시킨 후 결과를 봤더니, 한글 페이지에 영문 글이 섞여 나왔다. 이때 그냥 "이상해, 고쳐줘"라고 하면 봇은 엉뚱한 곳을 고친다.

하지만 **"페이지네이션에 영문 글이 섞이는 거 보면, Jekyll where 필터에서 lang 분류가 안 되는 것 같아. YAML frontmatter에 lang: ko 가 빠졌거나 파싱 에러인 것 같은데 확인해봐"** — 이렇게 방향을 잡아주면 한 번에 해결된다.

또 다른 예. 봇에게 이미지 생성을 시켰는데 아무 반응이 없다. 단순히 "이미지 안 만들어져"라고 하면 봇은 프롬프트를 수정하거나 모델을 바꾸거나 한다. 하지만 비동기 처리에 대한 감이 있으면 **"await를 안 걸어서 코루틴이 실행 안 된 것 같은데?"**라고 물을 수 있고, 실제로 그게 원인인 경우가 많다.

### AI 시대에 직관이 필요한 이유

AI 도구가 강력해질수록, 역설적으로 **"이게 왜 안 되는지"를 감잡는 직관이 더 중요**해진다.

1. **예외 처리 감각**: "완료했다는데 결과가 없다" → 십중팔구 예외가 씹혔다
2. **비동기 감각**: "중간에 잘렸다" → timeout이나 await 누락
3. **시스템 감각**: "한글 목록에 영문이 보인다" → 필터링 로직 또는 메타데이터 파싱 에러
4. **네트워크 감각**: "200인데 내용이 이상하다" → 캐시, CDN, 또는 커스텀 에러 페이지

이런 직관은 직접 삽질해본 사람에게만 생긴다. 프레임워크 안에서만 일하면 안 보이는 것들이다.

AI에게 "알아서 해"라고 맡기는 건 괜찮다. 하지만 **결과가 이상할 때 "왜?"를 한 단계만 더 파고들 수 있는 사람**이 AI를 제대로 쓰는 사람이다.

---

## 마무리 — AI를 믿되, 확인하라

현재 봇의 블로그 생성 파이프라인은 이렇게 돌아간다:

1. Claude가 글을 쓴다
2. **파일이 실제로 존재하는지 확인한다** (Step 1)
3. 이미지를 생성한다
4. git commit + push한다
5. **push가 실제로 됐는지 확인한다** (Step 2)
6. **상태를 3단계로 분류해서 보고한다** (Step 3)
7. **배포 후 실제 URL에 접근해서 확인한다** (Step 4)

4개의 검증 단계를 거치고 나서야 ✅를 보낸다. 이전에는 1번만 하고 ✅를 보냈다.

이 시스템을 만든 후 거짓 완료 보고는 사라졌다. 대신 ⚠️와 ❌가 제대로 오기 시작했다. 그리고 그 덕분에 — 문제를 더 빨리 잡고 더 빨리 고칠 수 있게 됐다.

AI는 도구다. 아주 강력한 도구다. 하지만 **자기 실수를 인정하는 건 아직 못한다.** 그건 우리 몫이다.

---

**참고 자료:**
- [Claude Code + Telegram으로 24시간 AI 비서 만들기 — 시리즈 소개](https://blog.wonderx.co.kr/posts/telegram-ai-assistant-intro/)
- [텔레그램 봇 하나로 블로그 전자동화 — 음성부터 배포까지](https://blog.wonderx.co.kr/posts/telegram-bot-blog-automation-full-pipeline/)
- [음성 메시지 하나로 회의록 + 블로그 자동 생성 — Gemini STT의 힘](https://blog.wonderx.co.kr/posts/voice-stt-meeting-blog/)
