---
title: 'Setting Up a Telegram Bot with Claude Code — The Practical Guide'
description: 'Creating a Telegram bot with BotFather, connecting it to Claude Code CLI with Python — the full setup walkthrough. Including the gotchas I ran into.'
date: 2026-02-05 00:00:00 +0900
tags: ['Claude-Code', 'Telegram', 'Python', 'automation', 'vibe-coding']
categories: [tech]
image:
  path: /images/blog/telegram-bot-1.webp
  width: 800
  height: 800
author: wonder
lang: en
twin: telegram-bot-setup
---

## Bottom Line Up Front: A Working Bot in 30 Minutes

In the [series intro](/posts/telegram-ai-assistant-intro-en), I laid out the architecture. This post is the implementation. Full code included.

Total time: 30 minutes. To be precise, I sent a request to Telegram and went to make coffee. Claude Code set up the project structure, wrote the code, and ran the tests. My contribution was communicating the intent.

This is the essence of vibe coding: delegate implementation details to the AI, and as a developer, focus on direction.

## Step 1 — Create the Telegram Bot (3 Minutes)

Create a bot through BotFather. Every Telegram bot is registered through this official bot.

1. Search for **@BotFather** on Telegram
2. Type `/newbot`
3. Enter the bot name (e.g., `WonderX Assistant`)
4. Enter the bot username (e.g., `wonderclaw_bot`)
5. **Copy the token**

```
Use this token to access the HTTP API:
8349xxxxx:AAGxxxxxxxxxxxxxxxxxx
```

This token is the bot's authentication key. If it leaks, a third party gains full control over the bot. Store it as an environment variable and make sure `.env` is in your `.gitignore`.

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

Five core files. The design principle here is "get it running first, refine the structure later." Spending time perfecting directory layout upfront is less efficient than shipping a fast MVP and iterating on feedback.

![Project structure](/images/blog/telegram-bot-2.webp)

## Step 3 — Core Code Breakdown

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

`ALLOWED_USER_IDS` is the critical security layer here. Without it, anyone can send commands to your bot — and those commands execute directly on your MacBook. It is functionally equivalent to opening your local terminal to the outside world.

I actually ran the bot with this value empty for an entire day during initial testing. Nothing happened, but the moment I reviewed the logs and realized what was exposed, the implications were clear.

To find your Telegram User ID, message `@userinfobot` — it responds instantly.

### Claude Code Execution Wrapper (claude.py) — The System's Core

This file is the architectural centerpiece. It is an async wrapper that executes `claude -p "prompt"` via subprocess.

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

Three parameters matter here:

- **`--allowedTools`**: In `-p` (pipe) mode, interactive approval is impossible. Without this flag, Claude requests tool-use confirmation and stalls. Since a bot cannot interactively approve actions, you must pre-authorize the tools it can use.
- **`cwd` parameter**: Specifies the working directory for Claude Code. For blog tasks, point it to the blog repo. For bot tasks, point it to the bot repo. Without this, Claude operates from the home directory and creates files in unexpected locations.
- **300-second timeout**: Claude Code reads files, analyzes code, makes changes, and runs tests during complex operations. A 60-second timeout caused every blog post generation to fail. 300 seconds (5 minutes) proved adequate for the vast majority of tasks.

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

Send `/blog Claude Code tips collection` on Telegram, and Claude generates the markdown file, fills in the frontmatter, and writes the body content. The entire pipeline completes from a single command.

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

At this point, any message sent on Telegram triggers a Claude Code response. A fully functional AI assistant running on your local machine is now operational.

![Bot running](/images/blog/telegram-bot-3.webp)

## Step 5 — macOS Auto-Start (launchd)

Manually starting the bot after every reboot defeats the purpose of automation. Register it with macOS's launchd, and the bot starts automatically at boot.

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

The critical setting is `KeepAlive` with `SuccessfulExit: false`. If the bot process terminates abnormally, launchd automatically restarts it. This provides daemon-level reliability without a separate process monitoring tool.

```bash
# Register the service
./scripts/install-service.sh

# Check status
launchctl list | grep wonderx
```

## Available Commands Summary

| Command | Function |
|------|------|
| Any text | Claude Code handles it |
| `/blog topic` | Auto-generate blog draft |
| `/publish` | draft → publish + git push |
| `/posts` | View post list |
| `/status` | MacBook system status |
| `/git status` | Git command on blog repo |

## Three Gotchas I Actually Hit

Here are the problems I encountered during development, documented so that anyone attempting the same setup can avoid these pitfalls.

### 1. Missing `--allowedTools`

The initial version omitted this flag. Claude returned "Bash execution approval required" and stopped. In `-p` mode, the process is non-interactive — there is no approval prompt. Without pre-authorized tools, Claude cannot perform any operations.

Took 30 minutes to diagnose. Would have been instant if I had checked stderr first.

### 2. Unchanged Example Value in ALLOWED_USER_IDS

Left the `123456789` placeholder from `.env.example` unchanged. Every message returned "Permission denied." When copying environment files, verify that all placeholders are replaced with actual values. A basic step, but a surprisingly common oversight.

### 3. PATH Resolution in launchd

launchd does not inherit the user shell's PATH. The `claude` binary becomes unfindable. Two solutions:

1. Specify the absolute path to Claude Code in `.env` (e.g., `/opt/homebrew/bin/claude`)
2. Add PATH to the plist file's `EnvironmentVariables` section

A familiar issue for anyone who has run daemons on macOS. Understanding the difference between shell environment and launchd environment is key.

## Blog Improvements, Also Via the Bot

I did not stop at building the bot. Using the same workflow, I also improved the blog.

- **SEO optimization**: Meta tags, JSON-LD structured data, robots.txt
- **Category sidebar**: AI Automation / Side Projects / Dev Log / Social / Tutorial
- **Giscus comments**: Comment system powered by GitHub Discussions
- **Anonymization**: Removed GitHub profile links, switched to email contact
- **About page renewal**: Page concept redesign

All done by sending requests to Claude Code via Telegram. "Optimize SEO," "add a comment system," "rewrite the About page" — these three messages resulted in file creation, CSS authoring, and build test execution.

Communicating intent and receiving implementation — that is what vibe coding looks like in practice.

## Next Episode Preview

- **Conversation context management**: The bot currently loses context with every message. I will implement a memory system that maintains conversation continuity.
- **System prompt design**: Prompt engineering to give Claude a defined role and personality.

---

Building automation is not about being lazy. It is about freeing yourself from repetitive tasks to focus on work that matters.

---

*Full code is in a private repo. Questions? Reach out at [x@wonderx.co.kr](mailto:x@wonderx.co.kr).*
