---
title: 'Telegram 봇 만들고 Claude Code 연동하기 — 실전 세팅편'
description: 'BotFather로 텔레그램 봇 만들고, Python으로 Claude Code CLI를 연동하는 과정. 블로그 자동화 명령까지 한 번에 세팅한다.'
pubDate: '2026-02-06'
tags: ['claude-code', 'telegram', 'python', 'automation', 'vibe-coding']
category: 'ai-automation'
heroImage: '/images/blog/telegram-bot-1.png'
draft: false
---

## 지난 글 요약

[시리즈 소개편](/blog/telegram-ai-assistant-intro)에서 아키텍처를 설명했다.
이번 글에서는 **실제로 동작하는 봇**을 만든다. 코드 전문 포함.

결론부터 말하면, Claude Code한테 시키니까 30분이면 끝났다.
게으른 개발자의 승리다.

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

이 토큰이 봇의 열쇠다. 절대 공개하면 안 된다.

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

심플하다. 파일 5개면 충분하다.

![프로젝트 구조](/images/blog/telegram-bot-2.png)

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

`ALLOWED_USER_IDS`가 중요하다. 이걸 안 넣으면 아무나 내 맥북에 명령을 날릴 수 있다.
본인 Telegram User ID는 `@userinfobot`한테 물어보면 알려준다.

### Claude Code 실행 래퍼 (claude.py)

여기가 핵심이다. `claude -p "프롬프트"` 명령을 subprocess로 실행한다.

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

포인트:
- **`--allowedTools`**: 이걸 안 넣으면 Claude가 매번 "이 도구 실행해도 될까요?" 하고 물어본다. 봇은 대화형이 아니니까 자동 허용해야 한다.
- **`cwd` 파라미터**: 블로그 프로젝트 폴더를 지정하면 그 안에서 작업한다.
- **타임아웃 300초**: Claude가 복잡한 작업을 할 수 있으니 넉넉하게.

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

`/blog Claude Code 팁 모음` 이라고 보내면 Claude가 알아서 마크다운 파일을 만들고, frontmatter도 채우고, 내용도 쓴다.

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

이게 끝이다.

![봇 실행 화면](/images/blog/telegram-bot-3.png)

## Step 5 — macOS 자동 시작 (launchd)

맥북 켜면 자동으로 봇이 실행되게 하려면 launchd plist를 등록한다.

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

`KeepAlive`의 `SuccessfulExit: false`는 봇이 비정상 종료되면 자동 재시작한다는 뜻이다.

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

### 1. `--allowedTools` 필수

처음에 이걸 안 넣었더니 Claude가 "Bash 실행 승인이 필요합니다" 하면서 멈췄다.
`-p` 모드에서는 대화형 승인이 안 되니까 반드시 `--allowedTools`로 허용할 도구를 지정해야 한다.

### 2. ALLOWED_USER_IDS 설정

처음에 예시 값(`123456789`)을 그대로 뒀다가 "🚫 권한이 없습니다" 세례를 받았다.
본인 Telegram User ID를 꼭 확인해서 넣자.

### 3. Claude Code 경로

launchd로 실행할 때 `claude`가 PATH에 없을 수 있다.
`.env`에 절대 경로를 넣거나, plist의 PATH에 `/opt/homebrew/bin`을 포함시켜야 한다.

## 블로그도 같이 업그레이드했다

이번에 봇만 만든 게 아니라 블로그도 좀 손봤다:

- **SEO 최적화**: 메타태그 강화, JSON-LD 구조화 데이터, robots.txt 추가
- **카테고리 사이드바**: AI 자동화 / 사이드 프로젝트 / 개발 일지 / 소셜링 / 튜토리얼
- **Giscus 댓글**: GitHub Discussions 기반 댓글 시스템 연동
- **익명화**: GitHub 링크 빼고 이메일 연락처로 전환
- **About 리뉴얼**: "게으른 개발자가 자동화를 만드는 이유" 컨셉

전부 Claude Code한테 시켰다. 하나하나 설명하고 요청하면 알아서 파일 만들고, CSS 쓰고, 빌드 테스트까지 해준다. 이게 바이브 코딩이다.

## 다음 편 예고

- **대화 맥락 관리**: 지금은 메시지마다 새 세션이다. 이전 대화를 기억하게 만들 것이다.
- **시스템 프롬프트**: Claude에게 "넌 게으른 개발자의 비서야" 라는 성격을 부여할 것이다.

---

*전체 코드는 비공개 레포에 있다. 궁금한 건 [x@wonderx.co.kr](mailto:x@wonderx.co.kr)로.*
