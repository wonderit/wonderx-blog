---
title: 'Setting Up a Telegram Bot with Claude Code — The Practical Guide'
description: 'Creating a Telegram bot with BotFather, connecting it to Claude Code CLI with Python — the full setup walkthrough. Including the gotchas I ran into.'
date: 2026-02-05 00:00:00 +0900
tags: ['claude-code', 'telegram', 'python', 'automation', 'vibe-coding']
categories: [ai-automation]
image:
  path: /images/blog/telegram-bot-1.webp
  width: 800
  height: 800
author: wonder
lang: en
twin: telegram-bot-setup
---

## 30 Minutes. That's It.

In the [series intro](/posts/telegram-ai-assistant-intro-en), I laid out the architecture.
This post is the one where we actually build it. Full code included.

I finished it in 30 minutes.
To be precise, Claude Code finished it in 30 minutes.
I typed a command into Telegram and went to make coffee.

Laziness creates systems. I mean that.

## Step 1 — Create the Telegram Bot

Go to BotFather and make a bot. 3 minutes.

1. Search for **@BotFather** on Telegram
2. Type `/newbot`
3. Enter the bot name (e.g., `WonderX Assistant`)
4. Enter the bot username (e.g., `wonderclaw_bot`)
5. **Copy the token**

```
Use this token to access the HTTP API:
8349xxxxx:AAGxxxxxxxxxxxxxxxxxx
```

This token is the key to your bot. If it leaks, you're done. Put it in an environment variable and don't commit it to git.

## Step 2 — Project Structure

```
wonderx-bot/
├── bot/
│   ├── __init__.py
│   ├── main.py          # Entry point (polling)
│   ├── config.py         # Environment variable management
│   ├── claude.py         # Claude Code CLI wrapper
│   └── handlers.py       # Command handlers
├── scripts/
│   └── install-service.sh  # macOS auto-start
├── com.wonderx.bot.plist   # launchd config
├── .env                    # Token (not tracked by git)
└── pyproject.toml
```

5 files. That's all you need.
I don't understand people who spend 30 minutes on project structure. Just get it running first, refactor later.

![Project structure](/images/blog/telegram-bot-2.webp)

## Step 3 — Core Code

### Config (config.py)

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
CLAUDE_TIMEOUT = 300  # 5 minutes
```

What happens if you forget `ALLOWED_USER_IDS`?
Anyone can fire commands at your MacBook.
I actually left it blank for a whole day. Nothing happened, but I was drenched in cold sweat after I realized it.

To find your Telegram User ID, just message `@userinfobot` — it'll tell you instantly.

### Claude Code Execution Wrapper (claude.py)

This file is the heart. It's a subprocess wrapper that runs `claude -p "prompt"`.

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

Three things to remember:

- **`--allowedTools`**: Skip this and Claude will ask for permission every single time. A bot isn't interactive. Auto-allow is mandatory.
- **`cwd` parameter**: Point it to the blog folder and Claude works inside it. Without this, it'll create files in random places.
- **300-second timeout**: You need to give Claude time to figure things out. Set it too short and complex tasks get cut off.

I started with a 60-second timeout. Every blog post generation timed out. That was dumb.

### Telegram Handler (handlers.py)

```python
async def cmd_blog(update, context):
    """Auto-generate blog draft"""
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

Send `/blog Claude Code tips collection` and you're done.
Claude creates the markdown file, fills in the frontmatter, writes the content.
I was lying on the couch the whole time, just typing into Telegram.

### Entry Point (main.py)

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

## Step 4 — Run It

```bash
# Create conda environment
conda create -n wonderx-bot python=3.11 -y
conda activate wonderx-bot
pip install python-telegram-bot python-dotenv

# Create .env file
cp .env.example .env
# Enter your token and User ID

# Run
python -m bot.main
```

```
🤖 WonderX Bot starting...
✅ Bot ready. Polling started...
```

Done. Really done. Nothing else to do.

![Bot running](/images/blog/telegram-bot-3.webp)

## Step 5 — macOS Auto-Start (launchd)

Opening a terminal and typing `python -m bot.main` every time the MacBook boots is not something a human should have to do.
Register it with launchd and the bot starts at boot.

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

The `KeepAlive` with `SuccessfulExit: false` means if the bot dies, it automatically comes back. Like a zombie. I like that.

```bash
# Register the service
./scripts/install-service.sh

# Check status
launchctl list | grep wonderx
```

## Available Commands

| Command | Function |
|------|------|
| Any text | Claude Code handles it |
| `/blog topic` | Auto-generate blog draft |
| `/publish` | draft → publish + git push |
| `/posts` | View post list |
| `/status` | MacBook system status |
| `/git status` | Git command on blog repo |

## Gotchas

I'll be honest. I messed up three times.

### 1. Forgot `--allowedTools`

Didn't include it at first. Claude would say "Bash execution approval required" and freeze.
A bot isn't interactive. There's no one to ask. In `-p` mode, you absolutely must pre-authorize tools with `--allowedTools`.

Lost 30 minutes on this. My fault for not reading the logs.

### 2. Left the example value in ALLOWED_USER_IDS

Left `123456789` as-is. Obviously got hit with "Permission denied" non-stop.
I needed my Telegram User ID in there, but I never changed the placeholder. The curse of auto-complete.

### 3. Claude Code Path Issue

Running via launchd means a different PATH. It can't find `claude`.
Either put the absolute path in `.env`, or add `/opt/homebrew/bin` to the PATH in the plist file.

If you've done macOS development, you've been through this rite of passage. There's no avoiding it.

## Revamped the Blog Too

I didn't stop at building the bot. I gave the blog a makeover too.

- **SEO optimization**: Meta tags, JSON-LD structured data, robots.txt
- **Category sidebar**: AI Automation / Side Projects / Dev Log / Social / Tutorial
- **Giscus comments**: Comment system powered by GitHub Discussions
- **Anonymization**: Removed GitHub links, switched to email contact
- **About page renewal**: "Why a lazy developer builds automation" concept

Claude Code did all of it. I just made requests.
"Do some SEO." "Add comments." "Rewrite the About page."
Three sentences, and Claude created files, wrote CSS, and even ran build tests.

That's vibe coding. State your intent and code appears.

## Next Episode Preview

- **Conversation context management**: Right now it loses its memory with every message. I'm going to make it continue previous conversations.
- **System prompt**: I'm going to give Claude a personality. "You are a lazy developer's assistant."

---

Building automation isn't about being lazy.
It's about earning the right to be lazy.

---

*Full code is in a private repo. Questions? Reach out at [x@wonderx.co.kr](mailto:x@wonderx.co.kr).*
