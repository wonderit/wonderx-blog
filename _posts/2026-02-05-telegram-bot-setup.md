---
title: 'Telegram 봇 만들고 Claude Code 연동하기 — 실전 세팅편'
description: 'BotFather로 텔레그램 봇 만들고, Python으로 Claude Code CLI를 연동하는 과정을 정리했다. 삽질 포인트까지 솔직하게 털어놓는다.'
date: 2026-02-05 00:00:00 +0900
tags: ['claude-code', 'telegram', 'python', 'automation', 'vibe-coding']
categories: [ai-automation]
image:
  path: /images/blog/telegram-bot-1.webp
  width: 800
  height: 800
author: wonder
twin: telegram-bot-setup-en
---

## 30분이면 끝난다

[시리즈 소개편](/posts/telegram-ai-assistant-intro)에서 아키텍처를 그렸다.
이번 글은 진짜 만드는 글이다. 코드 전문 포함.

나는 30분 만에 끝냈다.
정확히 말하면, Claude Code가 끝냈다.
나는 텔레그램에 명령어 치고 커피 한 잔 내렸다.

게으름이 시스템을 만든다. 진심이다.

## Step 1 — Telegram 봇 생성

BotFather한테 가서 봇을 만든다. 3분이면 된다.

1. Telegram에서 **@BotFather** 검색
2. `/newbot` 입력
3. 봇 이름 입력 (예: `WonderX Assistant`)
4. 봇 유저네임 입력 (예: `wonderclaw_bot`)
5. **토큰을 복사**해둔다

```
Use this token to access the HTTP API:
8349xxxxx:AAGxxxxxxxxxxxxxxxxxx
```

이 토큰은 봇의 열쇠다. 유출되면 끝이다. 환경변수에 넣고 git에 올리지 마라.

## Step 2 — 프로젝트 구조

```
wonderx-bot/
├── bot/
│   ├── __init__.py
│   ├── main.py          # 진입점 (polling)
│   ├── config.py         # 환경변수 관리
│   ├── claude.py         # Claude Code CLI 래퍼
│   └── handlers.py       # 명령어 핸들러
├── scripts/
│   └── install-service.sh  # macOS 자동 시작
├── com.wonderx.bot.plist   # launchd 설정
├── .env                    # 토큰 (git 추적 안 함)
└── pyproject.toml
```

파일 5개다. 더 필요 없다.
나는 프로젝트 구조에 30분 쓰는 사람을 이해 못 한다. 일단 돌리고, 나중에 고치면 된다.

![프로젝트 구조](/images/blog/telegram-bot-2.webp)

## Step 3 — 핵심 코드

### 환경 설정 (config.py)

```python
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
ALLOWED_USER_IDS = [
    int(uid.strip())
    for uid in os.getenv("ALLOWED_USER_IDS", "").split(",")
    if uid.strip()
]
CLAUDE_CODE_PATH = os.getenv("CLAUDE_CODE_PATH", "claude")
BLOG_PROJECT_PATH = Path(os.getenv("BLOG_PROJECT_PATH", ""))
CLAUDE_TIMEOUT = 300  # 5분
```

여기서 `ALLOWED_USER_IDS`를 빼먹으면 어떻게 되냐고?
아무나 내 맥북에 명령을 때릴 수 있다.
나는 실제로 이걸 빈 값으로 두고 하루를 보냈다. 아무 일도 안 일어났지만, 등에 식은땀이 흘렀다.

본인 Telegram User ID는 `@userinfobot`한테 물어보면 바로 알려준다.

### Claude Code 실행 래퍼 (claude.py)

이 파일이 심장이다. `claude -p "프롬프트"`를 subprocess로 실행하는 래퍼.

```python
async def run_claude(prompt: str, cwd: Path | None = None) -> str:
    cmd = [
        CLAUDE_CODE_PATH,
        "-p", prompt,
        "--allowedTools", "Bash,Read,Write,Edit,Glob,Grep",
    ]

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd,
    )

    stdout, stderr = await asyncio.wait_for(
        process.communicate(),
        timeout=CLAUDE_TIMEOUT,
    )

    return stdout.decode("utf-8").strip()
```

세 가지만 기억하면 된다.

- **`--allowedTools`**: 이거 안 넣으면 Claude가 매번 허락을 구한다. 봇은 대화형이 아니다. 자동 허용 필수.
- **`cwd` 파라미터**: 블로그 폴더를 지정하면 그 안에서 작업한다. 이게 없으면 엉뚱한 데서 파일을 만든다.
- **타임아웃 300초**: Claude가 삽질할 시간을 줘야 한다. 짧게 잡으면 복잡한 작업에서 잘린다.

나는 처음에 타임아웃을 60초로 잡았다. 블로그 글 하나 쓰는데 매번 타임아웃이 터졌다. 멍청했다.

### Telegram 핸들러 (handlers.py)

```python
async def cmd_blog(update, context):
    """블로그 초안 자동 생성"""
    topic = " ".join(context.args)

    prompt = (
        f"블로그 포스트를 작성해줘. 주제: {topic}\n"
        f"src/content/blog/ 폴더에 마크다운 파일 생성\n"
        f"draft: true로 설정\n"
        f"말투: 반말, 친근하고 실용적."
    )

    result = await run_claude(prompt, cwd=BLOG_PROJECT_PATH)
    await update.message.reply_text(f"📝 완료:\n{result}")
```

`/blog Claude Code 팁 모음`이라고 보내면 끝이다.
Claude가 마크다운 파일 만들고, frontmatter 채우고, 내용까지 쓴다.
나는 소파에 누워서 텔레그램만 쳤다.

### 진입점 (main.py)

```python
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

app.add_handler(CommandHandler("start", cmd_start))
app.add_handler(CommandHandler("blog", cmd_blog))
app.add_handler(CommandHandler("publish", cmd_publish))
app.add_handler(CommandHandler("status", cmd_status))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

app.run_polling(drop_pending_updates=True)
```

## Step 4 — 실행

```bash
# conda 환경 생성
conda create -n wonderx-bot python=3.11 -y
conda activate wonderx-bot
pip install python-telegram-bot python-dotenv

# .env 파일 생성
cp .env.example .env
# 토큰과 User ID 입력

# 실행
python -m bot.main
```

```
🤖 WonderX Bot 시작...
✅ 봇 준비 완료. Polling 시작...
```

끝이다. 진짜로 끝이다. 더 할 게 없다.

![봇 실행 화면](/images/blog/telegram-bot-3.webp)

## Step 5 — macOS 자동 시작 (launchd)

맥북 켤 때마다 터미널 열고 `python -m bot.main` 치는 건 인간이 할 짓이 아니다.
launchd에 등록하면 부팅과 동시에 봇이 뜬다.

```xml
<key>ProgramArguments</key>
<array>
    <string>/path/to/conda/envs/wonderx-bot/bin/python</string>
    <string>-m</string>
    <string>bot.main</string>
</array>

<key>RunAtLoad</key>
<true/>

<key>KeepAlive</key>
<dict>
    <key>SuccessfulExit</key>
    <false/>
</dict>
```

`KeepAlive`의 `SuccessfulExit: false`는 봇이 죽으면 자동으로 다시 살린다는 뜻이다. 좀비처럼. 나는 이게 좋다.

```bash
# 서비스 등록
./scripts/install-service.sh

# 상태 확인
launchctl list | grep wonderx
```

## 사용 가능한 명령어

| 명령 | 기능 |
|------|------|
| 아무 텍스트 | Claude Code가 처리 |
| `/blog 주제` | 블로그 초안 자동 생성 |
| `/publish` | draft → 발행 + git push |
| `/posts` | 글 목록 확인 |
| `/status` | 맥북 시스템 상태 |
| `/git status` | 블로그 repo git 명령 |

## 삽질 포인트

솔직하게 말한다. 나는 세 번 삽질했다.

### 1. `--allowedTools` 빼먹음

처음에 이걸 안 넣었다. Claude가 "Bash 실행 승인이 필요합니다" 하면서 멈췄다.
봇은 대화형이 아니다. 물어볼 사람이 없다. `-p` 모드에서는 반드시 `--allowedTools`로 도구를 미리 열어줘야 한다.

이걸 몰라서 30분을 날렸다. 로그를 안 본 내 잘못이다.

### 2. ALLOWED_USER_IDS에 예시 값을 그대로 둠

`123456789`를 그대로 뒀다. 당연히 "권한이 없습니다" 세례를 받았다.
내 Telegram User ID를 넣어야 하는데, 예시 값을 왜 바꾸지 않았을까. 자동 완성의 저주다.

### 3. Claude Code 경로 문제

launchd로 실행하면 PATH가 다르다. `claude`를 못 찾는다.
`.env`에 절대 경로를 넣거나, plist에 `/opt/homebrew/bin`을 PATH로 추가해야 한다.

이건 macOS 개발자라면 한 번쯤 겪는 통과의례다. 피할 수 없다.

## 블로그도 같이 뜯어고쳤다

봇만 만들고 끝낸 게 아니다. 블로그도 손봤다.

- **SEO 최적화**: 메타태그, JSON-LD 구조화 데이터, robots.txt
- **카테고리 사이드바**: AI 자동화 / 사이드 프로젝트 / 개발 일지 / 소셜링 / 튜토리얼
- **Giscus 댓글**: GitHub Discussions 기반 댓글 시스템
- **익명화**: GitHub 링크 빼고 이메일 연락처로 전환
- **About 리뉴얼**: "게으른 개발자가 자동화를 만드는 이유" 컨셉

전부 Claude Code가 했다. 나는 요청만 던졌다.
"SEO 좀 해줘." "댓글 달아줘." "About 페이지 다시 써줘."
이 세 마디에 Claude가 파일 만들고, CSS 쓰고, 빌드 테스트까지 돌렸다.

이게 바이브 코딩이다. 의도를 말하면 코드가 나온다.

## 다음 편 예고

- **대화 맥락 관리**: 지금은 메시지마다 기억을 잃는다. 이전 대화를 이어가게 만들 거다.
- **시스템 프롬프트**: Claude에게 성격을 심을 거다. "넌 게으른 개발자의 비서야."

---

자동화를 만드는 건 게으르기 위해서가 아니다.
게으를 수 있는 자격을 얻기 위해서다.

---

*전체 코드는 비공개 레포에 있다. 궁금한 건 [x@wonderx.co.kr](mailto:x@wonderx.co.kr)로.*
