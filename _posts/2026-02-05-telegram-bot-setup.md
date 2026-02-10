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

## 결론부터: 30분이면 동작하는 봇이 나온다

[시리즈 소개편](/posts/telegram-ai-assistant-intro)에서 아키텍처를 그렸다. 이번 글은 실제 구현편이다. 코드 전문을 공개한다.

소요 시간은 30분이었다. 정확히 말하면, 나는 텔레그램에 요청을 보내고 커피를 내리러 갔다. Claude Code가 프로젝트 구조를 잡고, 코드를 작성하고, 테스트까지 돌렸다. 내가 한 일은 "의도"를 전달한 것뿐이다.

이것이 바이브 코딩(Vibe Coding)의 핵심이다. 구현 디테일은 AI에게 위임하고, 개발자는 방향만 잡는다.

## Step 1 — Telegram 봇 생성 (3분)

BotFather를 통해 봇을 생성한다. 텔레그램의 모든 봇은 이 공식 봇을 통해 등록된다.

1. Telegram에서 **@BotFather** 검색
2. `/newbot` 입력
3. 봇 이름 입력 (예: `WonderX Assistant`)
4. 봇 유저네임 입력 (예: `wonderclaw_bot`)
5. **토큰을 복사**해둔다

```
Use this token to access the HTTP API:
8349xxxxx:AAGxxxxxxxxxxxxxxxxxx
```

이 토큰은 봇의 인증 키다. 유출되면 제3자가 봇을 완전히 제어할 수 있다. 반드시 환경변수로 관리하고, `.env` 파일은 `.gitignore`에 추가해야 한다.

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

핵심 파일은 5개다. 이 프로젝트에서 중요한 설계 원칙은 "먼저 동작하게 만들고, 나중에 구조를 개선한다"는 것이다. 완벽한 디렉토리 구조를 설계하느라 시간을 쓰는 것보다, 빠르게 MVP를 돌리고 피드백 루프를 도는 쪽이 효율적이다.

![프로젝트 구조](/images/blog/telegram-bot-2.webp)

## Step 3 — 핵심 코드 분석

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

여기서 `ALLOWED_USER_IDS`가 핵심 보안 레이어다. 이 값을 설정하지 않으면 누구든 봇에 명령을 보낼 수 있고, 그 명령은 맥북에서 직접 실행된다. 로컬 머신의 터미널 접근 권한을 외부에 개방하는 것과 동일한 위험이다.

실제로 나는 초기 테스트 단계에서 이 값을 빈 문자열로 둔 채 하루를 운영했다. 다행히 아무 일도 없었지만, 이후 로그를 확인하고 나서야 위험성을 인지했다.

본인 Telegram User ID는 `@userinfobot`에게 메시지를 보내면 즉시 확인할 수 있다.

### Claude Code 실행 래퍼 (claude.py) — 시스템의 핵심

이 파일이 전체 아키텍처의 핵심이다. `claude -p "프롬프트"`를 subprocess로 실행하는 비동기 래퍼다.

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

이 래퍼에서 이해해야 할 핵심 파라미터가 세 가지 있다:

- **`--allowedTools`**: `-p`(파이프) 모드에서는 대화형 승인이 불가능하다. 이 플래그 없이 실행하면 Claude가 도구 사용 승인을 요청하며 멈춘다. 봇은 사용자와 대화형으로 소통하지 않으므로, 허용할 도구를 사전에 명시해야 한다.
- **`cwd` 파라미터**: Claude Code가 작업할 디렉토리를 지정한다. 블로그 관련 작업이면 블로그 리포 경로를, 봇 관련 작업이면 봇 리포 경로를 넘긴다. 이 값이 없으면 홈 디렉토리에서 작업하게 되어 파일이 엉뚱한 위치에 생성된다.
- **타임아웃 300초**: Claude Code는 복잡한 작업에서 파일을 읽고, 코드를 분석하고, 수정하고, 테스트까지 돌린다. 60초로 설정했을 때 블로그 글 하나 생성하는 작업에서 매번 타임아웃이 발생했다. 300초(5분)가 대부분의 작업에 적절한 값이었다.

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

텔레그램에서 `/blog Claude Code 팁 모음`이라고 보내면, Claude가 마크다운 파일을 생성하고, frontmatter를 채우고, 본문까지 작성한다. 전체 과정이 하나의 명령어로 완결된다.

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

이 시점에서 텔레그램으로 메시지를 보내면 Claude Code가 응답한다. 로컬 머신 위의 완전한 AI 비서가 동작하기 시작한 것이다.

![봇 실행 화면](/images/blog/telegram-bot-3.webp)

## Step 5 — macOS 자동 시작 (launchd)

매번 부팅할 때마다 수동으로 봇을 실행하는 것은 자동화의 취지에 맞지 않다. macOS의 launchd에 등록하면 부팅과 동시에 봇이 자동 시작된다.

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

`KeepAlive`의 `SuccessfulExit: false` 설정이 핵심이다. 봇 프로세스가 비정상 종료되면 launchd가 자동으로 재시작한다. 별도의 프로세스 모니터링 도구 없이 데몬 수준의 안정성을 확보할 수 있다.

```bash
# 서비스 등록
./scripts/install-service.sh

# 상태 확인
launchctl list | grep wonderx
```

## 사용 가능한 명령어 요약

| 명령 | 기능 |
|------|------|
| 아무 텍스트 | Claude Code가 처리 |
| `/blog 주제` | 블로그 초안 자동 생성 |
| `/publish` | draft → 발행 + git push |
| `/posts` | 글 목록 확인 |
| `/status` | 맥북 시스템 상태 |
| `/git status` | 블로그 repo git 명령 |

## 삽질 기록 — 실제로 겪은 3가지 문제

개발 과정에서 마주친 문제들을 정리한다. 동일한 구성을 시도하는 사람이 같은 함정에 빠지지 않도록.

### 1. `--allowedTools` 누락

초기 버전에서 이 플래그를 빠뜨렸다. Claude가 "Bash 실행 승인이 필요합니다"라는 메시지를 반환하며 멈췄다. `-p` 모드는 비대화형(non-interactive)이므로 승인 창이 뜨지 않는다. 사용할 도구를 사전에 명시하지 않으면 Claude는 아무 작업도 수행하지 못한다.

이 문제를 파악하는 데 30분이 걸렸다. stderr 로그를 바로 확인했다면 즉시 발견할 수 있었다.

### 2. ALLOWED_USER_IDS 예시 값 미변경

`.env.example`의 `123456789`를 그대로 두고 실행했다. 모든 메시지에 "권한이 없습니다"가 반환됐다. 환경변수 파일을 복사할 때 모든 플레이스홀더를 실제 값으로 교체했는지 확인하는 것은 기본이지만, 예상외로 빈번하게 발생하는 실수다.

### 3. launchd 환경에서의 PATH 문제

launchd로 실행하면 사용자 셸의 PATH를 상속받지 않는다. `claude` 바이너리를 찾지 못하는 문제가 발생한다. 해결 방법은 두 가지다:

1. `.env`에 Claude Code의 절대 경로를 명시 (예: `/opt/homebrew/bin/claude`)
2. plist 파일의 `EnvironmentVariables`에 PATH를 추가

macOS에서 데몬을 운영해본 사람이라면 익숙한 문제다. 셸 환경과 launchd 환경의 차이를 이해하는 것이 핵심이다.

## 블로그도 함께 개선했다

봇 구축에 그치지 않고, 같은 방식으로 블로그도 개선했다.

- **SEO 최적화**: 메타태그, JSON-LD 구조화 데이터, robots.txt 생성
- **카테고리 사이드바**: AI 자동화 / 사이드 프로젝트 / 개발 일지 / 소셜링 / 튜토리얼
- **Giscus 댓글**: GitHub Discussions 기반 댓글 시스템 연동
- **익명화**: GitHub 프로필 링크 제거, 이메일 연락처로 전환
- **About 리뉴얼**: 페이지 컨셉 재설계

전부 텔레그램에서 Claude Code에 요청해서 처리한 작업이다. "SEO 최적화 해줘", "댓글 시스템 달아줘", "About 페이지 다시 써줘" — 이 세 마디가 파일 생성, CSS 작성, 빌드 테스트 실행으로 이어졌다.

의도를 전달하면 구현이 나오는 이 워크플로우가 바이브 코딩의 실체다.

## 다음 편 예고

- **대화 맥락 관리**: 현재 봇은 메시지마다 컨텍스트를 잃는다. 이전 대화를 기억하고 이어가는 메모리 시스템을 구현한다.
- **시스템 프롬프트 설계**: Claude에게 역할과 성격을 부여하는 프롬프트 엔지니어링.

---

자동화를 구축하는 목적은 게으르기 위해서가 아니다. 반복 작업에서 해방되어 더 가치 있는 일에 집중하기 위해서다.

---

*전체 코드는 비공개 레포에 있다. 궁금한 건 [x@wonderx.co.kr](mailto:x@wonderx.co.kr)로.*
