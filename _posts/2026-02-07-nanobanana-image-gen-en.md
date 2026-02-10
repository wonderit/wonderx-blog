---
title: 'Auto-Generating Blog Images with Nanobanana — The $0 API Secret'
description: 'Integrated Google Gemini''s Nanobanana image generation into the Telegram bot. Automatically generating blog images with a free API.'
date: 2026-02-07 00:00:00 +0900
tags: ['nanobanana', 'gemini', 'image-generation', 'telegram', 'claude-code', 'automation', 'vibe-coding']
categories: [ai-automation]
image:
  path: /images/blog/nanobanana-1.webp
  width: 800
  height: 800
author: wonder
lang: en
twin: nanobanana-image-gen
---

## Making Images Is Annoying

A text-only blog looks bland. I know that.
But opening Canva every time to make images is even worse.

I'm a lazy developer. Wouldn't it be nice if images just appeared automatically when I say "write me a blog post"?
So I built it.

## Nanobanana vs DALL-E

I had to pick an image generation API. Two candidates.

| Item | Nanobanana (Gemini Flash) | DALL-E 3 |
|---|---|---|
| **Price** | **Free** (500/day) | $0.04~$0.12/image |
| **Credit card** | Not required | Required |
| **Korean** | Native support | Internal translation |
| **Quality** | Good enough for blogs | Good |

**Nanobanana = Google Gemini's image generation feature**. Set `response_modalities=["IMAGE"]` and it spits out images.

500 free images per day. Put 3 in a blog post and that's 0.6% usage. Practically unlimited.
No reason to pay DALL-E for every image. The decision took 1 second.

![Concept diagram](/images/blog/nanobanana-2.webp)

## Implementation: 10 Minutes

### 1. Get an API Key

Grab one for free at [Google AI Studio](https://aistudio.google.com/apikey). No credit card needed. That's the key point.

### 2. Image Generation Module

```python
# bot/image_gen.py — core section only
from google import genai
from google.genai import types

async def generate_image(prompt: str, filename: str = None) -> dict:
    client = genai.Client(api_key=GEMINI_API_KEY)

    enhanced_prompt = (
        f"{prompt}\n\n"
        "Style: Modern tech blog illustration, clean and minimal, "
        "flat design with subtle gradients."
    )

    response = await asyncio.to_thread(
        client.models.generate_content,
        model="gemini-2.0-flash-exp",
        contents=enhanced_prompt,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
        ),
    )

    # Extract image → save to file
    for part in response.candidates[0].content.parts:
        if part.inline_data:
            save_path.write_bytes(part.inline_data.data)

    return {"path": str(save_path), "blog_path": f"/images/blog/{filename}"}
```

Three key points:
- Uses the `gemini-2.0-flash-exp` model. Free tier.
- `response_modalities=["IMAGE"]` is the magic spell. This single setting activates image generation mode.
- The Gemini SDK is synchronous, so I wrapped it with `asyncio.to_thread` for async support.

### 3. Batch Image Generation for Blog Posts

3 images per post. Each with a different vibe.

```python
async def generate_blog_images(topic: str, count: int = 3) -> list:
    prompts = [
        # 1. Hero: dark background, abstract
        f"Hero illustration about: {topic}. Dark background, vibrant accents.",
        # 2. Concept: light background, structural
        f"Conceptual diagram about: {topic}. Isometric view, connections.",
        # 3. Result: developer workspace
        f"Developer workspace showing: {topic}. Multiple screens, cozy.",
    ]

    results = []
    for i, prompt in enumerate(prompts):
        result = await generate_image(prompt, filename=f"{slug}-{i+1}.jpg")
        results.append(result)
    return results
```

### 4. Telegram Bot Integration

Two modes.

**Standalone image generation (`/image`):**
```
/image illustration of a Telegram bot chatting with AI
```
→ Generates 1 image, shows preview in Telegram, saves to blog folder.

**Automated blog generation (`/blog`):**
```
/blog nanobanana image generation integration
```
→ Auto-generates 3 images → Claude writes the body with image paths included → Complete draft in one shot.

![Result image](/images/blog/nanobanana-3.webp)

## The Full Flow

```
Telegram: /blog topic
  │
  ├→ Nanobanana: Generate 3 images (free)
  │   ├→ hero.jpg (hero)
  │   ├→ concept.jpg (concept)
  │   └→ result.jpg (result)
  │
  ├→ Claude Code: Write body (with image paths)
  │
  └→ Result: draft post + images complete
       └→ /publish → git push → deployed
```

One command to get a **complete post + images**. That's automation. Real automation.

## The Struggle: From AI Studio to Vertex AI

The code above didn't work cleanly from the start. There were struggles. Honestly, it took quite a while.

### AI Studio API Key Was Blocked

I initially got a free API key from AI Studio. But all the image generation models had **quota = 0**.

```
429 RESOURCE_EXHAUSTED: Quota exceeded for
GenerateContent:imageGeneration
```

Tried `gemini-2.0-flash-exp`, `gemini-2.5-flash-image` — same error everywhere. Google had restricted image generation on the free tier.

Free, they said? Felt like a scam.

### Vertex AI Was the Answer

The solution was [Google Cloud Vertex AI](https://console.cloud.google.com/vertex-ai/studio). Same Gemini model, but billed per GCP project, so there are no quota restrictions.

The switch was easy:

```bash
# 1. Enable Vertex AI API in GCP project
# 2. Set up Application Default Credentials
gcloud auth application-default login

# 3. Authenticate Google account in browser → done
```

One line of code changed:

```python
# Before: AI Studio (API key)
client = genai.Client(api_key=GEMINI_API_KEY)

# After: Vertex AI (ADC)
client = genai.Client(
    vertexai=True,
    project="my-project-id",
    location="us-central1"
)
```

Just added `vertexai=True`. Same model name. Worked immediately after that.
2 hours of struggle, 2 minutes to fix. Always goes like this.

### 3-Tier Fallback Strategy

The final architecture looks like this:

```
Priority 1: Vertex AI (ADC auth) → Stable, billing-based
Priority 2: AI Studio (API key) → Free but quota-limited
Priority 3: SVG placeholder → Last resort
```

No matter what, blog generation never stops. If images can't be generated, at least hold the spot with an SVG. Shipping beats perfection.

## Cost Summary

| Item | Monthly Cost |
|---|---|
| Claude Code Max | Already subscribed |
| Nanobanana images | **$0** (free 500/day) |
| Telegram Bot API | **$0** |
| GitHub Pages hosting | **$0** |
| **Total** | **Additional cost $0** |

Services like OpenClaw cost $20+/month. Build it yourself and it's $0.
That difference is why I build things myself.

## Series Progress

1. [AI Assistant Intro](/posts/telegram-ai-assistant-intro-en) ✅
2. [Telegram Bot Setup](/posts/telegram-bot-setup-en) ✅
3. [OpenClaw-Style Memory](/posts/openclaw-style-memory-en) ✅
4. Nanobanana Image Generation ← **This post**
5. Voice → Meeting Notes/Blog Auto-Generation (next)

Type one line in Telegram and a blog with images pops out automatically. Almost there.

---

There's no end to automation. But that's what makes it fun.
