---
title: 'Full Blog Automation with a Telegram Bot — From Voice to Deployment'
description: 'Send a voice message on Telegram and it handles everything: transcription → writing → image generation → git push → deployment verification. The full architecture of a blog automation system built in one week.'
date: 2026-02-13 14:00:00 +0900
tags: ['telegram-bot', 'Claude-Code', 'Gemini', 'blog-automation', 'AI-automation', 'Python', 'Jekyll']
categories: [ai-automation]
image:
  path: /images/blog/telegram-bot-blog-automation-full-pipeline-1.webp
  width: 800
  height: 800
author: wonder
lang: en
twin: telegram-bot-blog-automation-full-pipeline
---

## Time to Write a Blog Post: 5 Minutes

To be precise, all I do is send a voice message on Telegram or type "write a blog post." The bot handles the rest.

1. Voice transcription (Gemini STT)
2. Blog post writing (Claude Code CLI)
3. Auto-generate 4–8 images (Gemini + Imagen)
4. Korean + English simultaneous generation
5. git push + GitHub Pages deployment
6. Deployment verification + search engine notification

This post covers the full architecture of this system — refined through daily improvements over one week.

## Architecture Overview

```
[Telegram message/voice]
       ↓
  WonderX Bot (python-telegram-bot)
       ↓
  ┌─────────────────────────────┐
  │ Intent Detection             │
  └──────┬──────────────────────┘
         ├─ /blog command → Claude Code CLI → Write post
         ├─ Voice message → Gemini STT → [Minutes | Blog]
         ├─ Photo attachment → Gemini analysis → Illustration
         ├─ General text → Claude Code CLI (general chat)
         └─ /stats → GoatCounter + GA4 analytics
              ↓
  ┌─────────────────────────────┐
  │ Image Pipeline               │
  │ Post analysis → Prompts      │
  │ → Imagen/Gemini multi-model  │
  └──────┬──────────────────────┘
         ↓
  git add → commit → push
         ↓
  GitHub Pages deploy → IndexNow
```

It looks complex, but the core is simple: **input via Telegram, processing by 3 AIs (Claude + Gemini + Imagen), output to Jekyll blog.**

![System architecture](/images/blog/telegram-bot-blog-automation-full-pipeline-2.webp)

## Input Path 1: `/blog topic` — Writing from Text

The simplest path.

```
/blog AI image cost optimization
```

This triggers:

1. Auto-generate slug from topic: `ai-image-cost-optimization`
2. Claude Code CLI writes the post (Korean + English, 2 files)
3. Content analysis → auto-generate image prompts → generate images
4. git push → deployed

**Blog type selection is available.** There are two personas: tech blog and brunch essay.

Tech blogs use data-driven analysis, comparison tables, and code blocks. Brunch essays use sensory prose, psychological observations, and open-ended conclusions. Same material, completely different output.

Personas are defined in detail in the system prompt — writing style rules, structure guidelines, and prohibited expressions. Without explicit rules, AI produces inconsistent tone across posts.

## Input Path 2: Voice Message — Record and Get a Blog

This path is used most in practice. After meetings, when ideas strike, while walking.

### Pipeline

```
Voice message (OGG/Opus)
    ↓
Gemini STT transcription (Korean + English mix)
    ↓
Preview (300 chars)
    ↓
[📋 Minutes] [📝 Blog] ← Inline keyboard
    ↓
(If Blog selected)
Direction + reference images
    ↓
[🔧 Tech] [✍️ Brunch] ← Blog type selection
    ↓
Claude Code CLI → Write + Images + git push
```

### Bypassing the 20MB Limit

Telegram Bot API's file download limit is 20MB. Hour-long meeting recordings are typically 40–80MB. So I created a Google Drive path.

```
"Transcribe what I uploaded to Google Drive audio folder"
```

The bot finds the most recent file in `uploads/audio/` and transcribes it. You can also specify the filename directly. Files over 10MB get auto-compressed before API transmission.

![Voice to blog flow](/images/blog/telegram-bot-blog-automation-full-pipeline-3.webp)

## Input Path 3: Photo → Auto Illustration

Sending a photo on Telegram auto-converts it to an illustrated style. Useful when actual photos can't be posted (privacy, atmosphere, etc.).

Google Drive photos can also serve as reference images. Gemini analyzes the location, mood, and color palette of reference photos, then injects those characteristics into image generation prompts.

## Image Pipeline Design

Covered in detail in a previous post, but the essentials:

| Stage | Action | Tech |
|-------|--------|------|
| Analysis | Extract visual scenes from post | Gemini 2.5 Flash |
| Prompts | Generate scene-specific prompts | Gemini 2.5 Flash |
| Reference | Analyze Google Drive photo mood | Gemini 2.5 Flash |
| Generation | Render images ($0.02/image) | Imagen 4 Fast |
| Fallback | Auto-swap to next model on failure | Gemini 3 Pro, Flash |
| Optimization | PNG → WebP (10-20x savings) | Pillow |

Image count auto-adapts from 4 to 8 based on post length. Hero image is generated last and forced to 16:9 landscape.

![Image pipeline](/images/blog/telegram-bot-blog-automation-full-pipeline-4.webp)

## Deployment → Verification → Search Engine Notification

After content and images are ready, git push runs automatically. But that's not the end.

### Multi-Machine Conflict Prevention

I run this bot on multiple computers. Since parallel work is possible, `git pull --rebase` runs automatically before and after blog operations.

### Deployment Verification

After git push, `git log --oneline -1` and `git status` are auto-checked to verify the push actually succeeded.

### IndexNow

When a new post deploys, IndexNow API submits URLs to Bing and Yandex. Google crawls automatically via registered Search Console sitemap.

## Daily Stats Report

Every morning at 9 AM, a blog stats report arrives on Telegram — yesterday's pageviews, cumulative total, 7-day trend, and top 5 pages. Data comes from GoatCounter (free, privacy-friendly) combined with GA4 Data API.

![Stats report](/images/blog/telegram-bot-blog-automation-full-pipeline-5.webp)

## The AI Honesty Problem

The most unexpected problem in building this automation: **AI lies.**

When I tell Claude Code CLI to "write a blog post and push to git," sometimes it only writes the post without pushing, yet reports "✅ Complete." Or image generation fails but it reports "4 images generated successfully."

The solution: **enforce verification steps.**

```python
# File creation check (don't trust Claude's report)
verify_result = await run_claude(
    f"ls -la _posts/ | grep '{slug}' — "
    f"if missing, respond 'NO_FILE_FOUND'",
    cwd=BLOG_PROJECT_PATH
)
if "NO_FILE_FOUND" in verify_result:
    # Handle failure
```

Key lesson of AI automation: **never take AI reports at face value.** Always include verification steps that check actual results.

## Cross-Platform Publishing

I wanted to publish on multiple platforms — Tistory and Brunch. The problem: **no APIs.** Tistory shut down its Open API in February 2024. Brunch never had one. Selenium automation risks account bans.

So I chose **semi-automation**: the bot converts markdown to platform-specific formats and sends files via Telegram. The user copies and pastes on the target platform.

Not fully automated, but automating markdown→HTML conversion and image path adjustments alone cuts time by more than half.

![Cross-posting flow](/images/blog/telegram-bot-blog-automation-full-pipeline-6.webp)

## Cost Structure

Monthly breakdown:

| Item | Cost | Notes |
|------|------|-------|
| Claude Code CLI | ~$20/mo | Anthropic Pro subscription |
| Gemini API (images) | ~$3.6/mo | 30 posts × 4 images × $0.02 |
| Gemini API (STT) | ~$0.5/mo | ~10 transcriptions |
| GoatCounter | Free | Self-hostable |
| GitHub Pages | Free | |
| **Total** | **~$24/mo** | |

Image costs alone: $3.6/month. Thanks to defaulting to Fast mode and only upgrading to Pro quality when needed.

## What Got Fixed Over One Week

This system wasn't built in a day. Every day brought a new problem and a fix.

| Date | Problem | Solution |
|------|---------|----------|
| 2/7 | Free image generation starts | Gemini Flash integration |
| 2/8 | Local disk shortage | Migrated to Google Drive storage |
| 2/8 | Multi-machine git conflicts | Auto pull --rebase |
| 2/9 | Need quality tiers for images | 3-tier system (fast/pro/ultra) |
| 2/9 | AI reports false completions | Forced verification steps |
| 2/11 | Cross-posting needs | Semi-automation system |
| 2/12 | Images don't match content | Post-analysis-based prompts |
| 2/12 | Hero image duplication | Prevention rule + hero-last order |
| 2/13 | Reference photos not reflected | Reference image analysis pipeline |
| 2/13 | Missing images (4 of 8) | Expanded fallback to 8 templates |

Automation systems are harder to maintain than to build. New edge cases surface daily. AI-based systems have unpredictable failures. But that's what makes it interesting.

## Summary

This system solves one problem: **minimizing the friction of writing a blog post.**

When an idea strikes, record a voice message. Send it on Telegram. Five minutes later, the blog is deployed. Images, English translation, git push, deployment verification — all automatic.

It's not perfect. AI occasionally writes strange things. Images sometimes don't match. Each time, I add rules and strengthen verification.

The purpose of automation isn't "humans doing nothing" but "humans focusing on what matters." I decide the topic and direction. The bot handles the rest.

Developers should be lazy. We write code diligently so we can be lazy later. It sounds contradictory, but that's the essence of automation.
