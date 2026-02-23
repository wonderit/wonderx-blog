---
title: "How I Fixed My AI Bot's Lying Problem — A 4-Step Verification System"
description: "My Claude Code-powered Telegram bot kept reporting tasks as complete when they weren't. Here's how I built a 4-step verification system using file checks, git diff, status classification, and live URL validation."
date: 2026-02-21 09:00:00 +0900
image: /images/blog/ai-bot-lies-verification-system-1.webp
tags: ['AI automation', 'Claude Code', 'Telegram bot', 'LLM', 'verification', 'Python']
categories: [tech]
author: wonder
lang: en
twin: ai-bot-lies-verification-system
---

## "Task Complete" — Really?

I asked my Telegram AI bot to write a blog post. Five minutes later, the reply came back:

> ✅ Blog post complete! Both Korean and English versions written, git push done.

I opened the site. **No post.**

Checked git log. **No commit.**

Opened the `_posts` folder. **The files didn't even exist.**

The AI lied. Not intentionally — but the result was the same. **A completely false completion report.** And this wasn't a one-time thing. It kept happening.

---

## Why AI Produces False Completion Reports

Running a Telegram bot with Claude Code CLI as the backend, I identified three root causes behind these false reports.

### 1. Silently Swallowed Exceptions

The most common case. Claude tries to create a file, hits a permission error or path issue, **fails to handle the exception properly, and moves on.** "I'll write the file" → failure → but the process continues → "Done!"

Here's what the actual bot logs looked like:

```
[INFO] Claude task started: Generate blog (ko + en)
[INFO] Claude response received (status: success)
[ERROR] _posts/ file check: No such file
```

Claude returned "success." But no file was created.

### 2. Async Timing Issues

In a Python `asyncio`-based bot, Claude CLI runs as a subprocess with a 600-second timeout. If the actual work doesn't finish in time, only partial output gets returned. Claude might be mid-sentence — "Korean file created, English file is now being writ—" — and the bot treats that as a completed response.

### 3. LLM's Optimistic Reporting Bias

This is the most fundamental issue. LLMs are **inherently biased toward reporting positive completion.** After stating "I will create the file," even if something goes wrong during execution, the model tends to respond "I have completed the file creation." It conflates planning with execution.

---

## The 4-Step Verification System

To eliminate false reports, I built a system based on one principle: **never trust the AI's word.** Trust, but verify — actually, **don't trust, just verify.**

### Step 1: Physical File Existence Check

```python
# Verification: confirm both ko + en files exist
verify_result = await run_claude(
    f"ls -la _posts/ | grep '{slug}' — "
    f"check if both {slug}.md and {slug}-en.md exist. "
    f"If either is missing, reply 'NO_FILE_FOUND'.",
    cwd=BLOG_PROJECT_PATH,
    timeout=30,
)

if "NO_FILE_FOUND" in verify_result:
    await status_msg.edit_text("❌ Blog files were not created.")
    return
```

Even after Claude says "done," a **separate Claude session** runs `ls -la` to physically verify file existence. If the files aren't there, immediate failure.

The key is **separating the worker Claude from the verifier Claude.** If you ask the same session "did you create the file?", it'll likely say "yes." A separate session checking the file system directly is far more reliable.

### Step 2: Git State Verification

```python
# Verify git push actually happened
push_verify = await run_claude(
    "Show git log --oneline -1 and git status. "
    "If push didn't happen, reply 'NOT_PUSHED'.",
    cwd=BLOG_PROJECT_PATH,
    timeout=30,
)

push_failed = "NOT_PUSHED" in push_verify
```

Files might exist but git push could have failed — rebase conflicts, auth expiry, network errors. Instead of trusting Claude's "push complete" report, separately verify with `git log` and `git status`.

### Step 3: Three-State Classification

When receiving reports, humans tend to think in binary: "done" or "failed." But three states are needed:

| Emoji | State | Meaning |
|-------|-------|---------|
| ✅ | Complete | Files created + push succeeded + deployment verified |
| ⚠️ | Partial | Files exist but push failed or deployment unconfirmed |
| ❌ | Failed | Files weren't created at all |

Adding the "partial completion" state made a huge difference. Previously, push failures were still reported as ✅, so problems went unnoticed.

### Step 4: Live URL Deployment Verification

The strongest final gate. After GitHub Pages deployment, **actually access the URL** to confirm the page exists.

```python
async def _verify_blog_deployment(slug, max_wait=90):
    """Post-deployment site verification"""
    post_url = f"{BLOG_BASE_URL}/posts/{slug}/"

    async with aiohttp.ClientSession() as session:
        for attempt in range(max_wait // 10):
            await asyncio.sleep(10)
            status, length = await _check_url(session, post_url)
            if status == 200 and length > 5000:
                deployed = True
                break
```

Polls every 10 seconds for up to 90 seconds. Even a 200 response is treated as failure if content_length is under 5000 (empty page). Individual image URLs are checked too — catching "page exists but images are broken" states.

This verification runs as an async background task. The user gets the initial "deployment complete" notification first, and if the verification finds issues, a separate alert follows.

---

## "Image URL Returns HTML" — Catching the Gotcha

One subtle trap in deployment verification: an image URL returns **200 OK**, but the response is actually a **404 HTML page**, not an image.

```python
async def _check_url(session, url):
    async with session.get(url, ssl=False) as resp:
        content_type = resp.headers.get("Content-Type", "")
        # Image URL returning HTML = actually a 404
        if any(ext in url.lower() for ext in [".webp", ".png", ".jpg"]):
            if "text/html" in content_type:
                return 404, len(body)  # Reclassify as 404
```

GitHub Pages' custom 404 page can return 200 OK. If a URL ending in `.webp` returns `Content-Type: text/html` — that's not an image, it's a 404 page. Without this single check, "image deployment complete" would have remained a false report.

---

## The Real Lesson — Debugging AI with Intuition

The most important thing I learned building this system wasn't technical.

**The most effective way to debug AI bots is having the intuition to guess the root cause from symptoms.**

When I told the bot "write both Korean and English posts" and English posts showed up in the Korean page list, just saying "fix it" leads to wrong fixes.

But saying **"English posts are appearing in the Korean pagination — looks like the Jekyll where filter isn't classifying lang properly. Either lang: ko is missing from YAML frontmatter or there's a parsing error. Check that"** — that gets solved in one shot.

Another example. I asked the bot to generate images and got zero response. Saying "images aren't generating" leads to prompt tweaks or model changes. But if you have async intuition, you can ask **"did you forget to await the coroutine?"** — and that's often exactly the problem.

### Why Intuition Matters in the AI Era

As AI tools get more powerful, paradoxically, **the intuition for "why isn't this working" becomes more important.**

1. **Exception handling sense**: "It says done but there's no output" → exception got silently swallowed
2. **Async sense**: "Output got cut off mid-sentence" → timeout or missing await
3. **Systems sense**: "English showing in Korean list" → filter logic or metadata parsing error
4. **Network sense**: "200 OK but content looks wrong" → cache, CDN, or custom error page

This intuition only comes from hands-on experience. You can't see these things if you've only worked within framework abstractions.

Delegating to AI with "just handle it" is fine. But **the person who can dig one layer deeper when results look wrong** — that's the person who truly leverages AI effectively.

---

## Closing — Trust AI, But Verify

Here's how the bot's blog generation pipeline works now:

1. Claude writes the post
2. **Verify files actually exist** (Step 1)
3. Generate images
4. Git commit + push
5. **Verify push actually happened** (Step 2)
6. **Classify status into 3 tiers** (Step 3)
7. **Access live URL to confirm deployment** (Step 4)

Only after all 4 verification steps does it send ✅. Before, it sent ✅ after just step 1.

Since implementing this system, false completion reports have disappeared. Instead, ⚠️ and ❌ started showing up properly. And thanks to that — problems get caught faster and fixed sooner.

AI is a tool. An incredibly powerful one. But **admitting its own mistakes? It can't do that yet.** That's on us.

---

**References:**
- [Claude Code + Telegram: Building a 24/7 AI Assistant — Series Intro](https://blog.wonderx.co.kr/posts/telegram-ai-assistant-intro/)
- [Full Blog Automation with a Telegram Bot — From Voice to Deployment](https://blog.wonderx.co.kr/posts/telegram-bot-blog-automation-full-pipeline/)
- [Voice Message to Meeting Notes + Blog — The Power of Gemini STT](https://blog.wonderx.co.kr/posts/voice-stt-meeting-blog/)
