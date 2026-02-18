---
title: 'Building a 24/7 AI Assistant with Claude Code + Telegram — Series Intro'
description: 'My MacBook is always on. Claude Code Max plan is $100/month. Connecting them to a Telegram bot to build a personal AI assistant — here is how this project begins.'
date: 2026-02-04 00:00:00 +0900
tags: ['Claude-Code', 'Telegram', 'automation', 'AI']
categories: [tech]
image:
  path: /images/blog/ai-assistant-intro-1.webp
  width: 800
  height: 800
author: wonder
lang: en
twin: telegram-ai-assistant-intro
---

## A $100 Subscription Generating $0 of Value After Hours

Claude Code Max plan: $100 per month. My work MacBook runs 24/7. Yet after work hours, the combined value output of these two resources was exactly zero. Claude Code was sitting idle on a machine that never sleeps.

This is not just a waste of a subscription. It is a **waste of infrastructure**.

I ran the numbers. Based on an 8-hour workday, I was actively using Claude Code for roughly 16% of available time. The remaining 84% — a resource I had already paid for — was sitting completely idle. Connect it to a Telegram bot, and suddenly I have a 24/7 personal AI assistant at zero additional cost.

I looked at open-source alternatives like OpenClaw. Well-built project. But unnecessary for my setup. Claude Code CLI's `-p` flag (pipe mode), already included in the Max plan, is all I need. No separate API key. No per-token billing.

## Architecture: Four Steps, Total

```
📱 Telegram → 🐍 Python Bot (MacBook) → 💻 Claude Code CLI → Result
```

No complex microservices. No cloud infrastructure. The entire flow completes in four steps:

1. Send a message on Telegram
2. A Python bot running on the MacBook receives it
3. Execute Claude Code via `claude -p "command"`
4. Return the result to Telegram

The simpler the architecture, the fewer failure points. In this design, only two things can break: the network connection and the MacBook's power supply.

## Why Claude Code — Fundamentally Different from an API Call

Here is the core thesis in one line: **Claude Code does not just generate text — it directly controls the local machine.**

The difference between a standard LLM API and Claude Code CLI:

| Capability | Standard LLM API | Claude Code CLI |
|-----------|-----------------|----------------|
| Code generation | Outputs code as text | Creates/modifies files directly |
| Deployment | "Here's how to do it" | Actually runs the build and deploy |
| Git operations | Tells you the commands | Executes commit, push itself |
| File system | No access | Navigates directories, reads/writes files |
| Terminal | Cannot execute | Runs arbitrary shell commands |

Ask ChatGPT to "deploy this for me" and it explains the **method**. Ask Claude Code the same thing and it **actually deploys**. That gap is what separates a "chatbot" from an "AI assistant."

## Series Roadmap

Here is what this series will cover:

1. **Project Setup** — Creating a Telegram bot and connecting Claude Code (next post)
2. **Conversation Context** — Maintaining history, designing system prompts
3. **Automation** — launchd-based auto-start, cron job configuration
4. **Feature Expansion** — MCP integration, file management, notification systems

I will document every failed attempt and dead end along the way. A post that shows where things broke and how I fixed them is far more useful in practice than one where everything works on the first try.

## Cost Breakdown

| Item | Cost |
|------|------|
| Claude Max subscription | $100/mo (already paying) |
| Telegram Bot API | Free |
| MacBook always-on | A bit of electricity |
| **Additional cost** | **$0** |

The structure here is straightforward: hiring an additional 24/7 AI assistant using the $100 I am already spending. From an ROI perspective, this takes the utilization rate of my existing subscription from roughly 16% to nearly 100%.

Next post covers the full code and setup process.

---

The best tool was already in my hands. I just was not using it properly.
