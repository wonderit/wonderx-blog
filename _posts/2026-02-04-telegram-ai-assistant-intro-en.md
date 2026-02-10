---
title: 'Building a 24/7 AI Assistant with Claude Code + Telegram — Series Intro'
description: 'My MacBook is always on. Claude Code Max plan is $100/month. Connecting them to a Telegram bot to build a personal AI assistant — here is how this project begins.'
date: 2026-02-04 00:00:00 +0900
tags: ['claude-code', 'telegram', 'automation', 'ai']
categories: [ai-automation]
image:
  path: /images/blog/ai-assistant-intro-1.webp
  width: 800
  height: 800
author: wonder
lang: en
twin: telegram-ai-assistant-intro
---

## My MacBook Was Just Sitting There

My work MacBook stays on 24/7. I'm also paying $100 a month for the Claude Code Max plan.
And what was I doing with it after work? Absolutely nothing.

Honestly, that was dumb.

One day it hit me. What if I connect this MacBook to Telegram and turn it into a **24/7 personal assistant**?

I'd seen tools like OpenClaw. But I'm already on the Max plan. Additional cost: $0. Just use Claude Code's `-p` mode and you're done. That's it.

## The Architecture Is This Simple

```
📱 Telegram → 🐍 Python Bot (MacBook) → 💻 Claude Code CLI → Result
```

Nothing fancy. Seriously.

1. Send a message on Telegram
2. Python bot on the MacBook receives it
3. Runs `claude -p "command"` to execute Claude Code
4. Sends the result back to Telegram

I hate complicated things. The fact that the entire system fits in four lines is exactly why I loved it.

## Why Claude Code Specifically?

This is a completely different league from a regular API call. Claude Code **controls the MacBook itself**.

- Build & deploy projects
- Check git status, commit, push
- Read log files
- Edit code directly
- Execute terminal commands

Ask ChatGPT to "deploy this for me" and it tells you how. Ask Claude Code and it **actually deploys it.**

That's the whole difference.

## What's Coming in This Series

1. **Project Setup** — Creating a Telegram bot & connecting Claude Code (next post)
2. **Conversation Context** — Maintaining history & system prompts
3. **Automation** — launchd auto-start, cron jobs
4. **Feature Expansion** — MCP integration, file management, notifications

I'll include all the mistakes and dead ends too. Posts where everything works perfectly on the first try are boring.

## Cost Breakdown

| Item | Cost |
|------|------|
| Claude Max subscription | $100/mo (already paying) |
| Telegram Bot API | Free |
| MacBook always-on | A bit of electricity |
| **Additional cost** | **$0** |

It's like hiring an extra assistant with money I'm already spending. You can't beat that value.

Next post, I'll crack open the actual code.

---

The best tool was already in my hands. I just didn't realize it.
