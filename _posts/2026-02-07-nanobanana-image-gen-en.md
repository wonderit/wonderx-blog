---
title: 'Auto-Generating Blog Images with Nanobanana — The $0 API Secret'
description: 'Integrated Google Gemini''s Nanobanana image generation into the Telegram bot. Automatically generating blog images with a free API.'
date: 2026-02-07 00:00:00 +0900
tags: ['Nanobanana', 'Gemini', 'image-generation', 'Telegram', 'Claude-Code', 'automation', 'vibe-coding']
categories: [tech]
image:
  path: /images/blog/nanobanana-1.webp
  width: 800
  height: 800
author: wonder
lang: en
twin: nanobanana-image-gen
---

## Do You Really Need to Create Blog Images Manually?

Here's the bottom line: **Google Gemini's Nanobanana image generation API gives you 500 images per day for free.** Put 3 images in a blog post and that's 0.6% of the daily quota. No per-image billing like DALL-E. No credit card required.

I know text-only blogs look bland. But I also know I don't want to open Canva every time I publish a post. I'm a lazy developer -- if I type "write a blog post" and the images don't generate themselves, that's not real automation. So I built it.

## Nanobanana vs DALL-E — The Numbers Speak for Themselves

I needed to pick an image generation API. Two candidates, one comparison table, and the decision was already made.

| Feature | Nanobanana (Gemini Flash) | DALL-E 3 |
|---|---|---|
| **Price** | **Free** (500/day) | $0.04~$0.12/image |
| **Credit card** | Not required | Required |
| **Korean prompts** | Native support | Internal translation |
| **Blog-quality output** | Good enough | Good |

**Nanobanana** is Google Gemini's built-in image generation capability. Add `response_modalities=["IMAGE"]` to your API call, and it returns images instead of text. That's the entire integration surface.

500 free images per day is effectively unlimited for individual bloggers -- unless you're publishing 166 posts a day. Paying DALL-E $0.04-$0.12 per image suddenly makes no sense. The decision took about one second.

![Concept diagram](/images/blog/nanobanana-2.webp)

## Implementation — 10 Minutes of Code

### 1. Get an API Key

Grab one for free at [Google AI Studio](https://aistudio.google.com/apikey). No credit card needed. This is the single biggest barrier-to-entry difference compared to DALL-E.

### 2. Image Generation Module — Core Code

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

Three things worth noting here:

- **`gemini-2.0-flash-exp`** is the model that supports image generation on the free tier.
- **`response_modalities=["IMAGE"]`** is the key parameter. This single line switches Gemini from a text model to an image generation model.
- The Gemini SDK only provides a synchronous API, so I wrapped it with **`asyncio.to_thread`** for async compatibility. Essential since the Telegram bot runs on an async event loop.

### 3. Batch Image Generation for Blog Posts

Each post gets 3 images, each serving a different purpose.

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

### 4. Telegram Bot Integration — Two Modes

**Standalone image generation (`/image`):**
```
/image illustration of a Telegram bot chatting with AI
```
Generates 1 image, shows a preview in Telegram, and saves it to the blog folder simultaneously.

**Automated blog generation (`/blog`):**
```
/blog nanobanana image generation integration
```
Auto-generates 3 images, then Claude writes the body with embedded image paths, producing a complete draft in one shot.

![Result image](/images/blog/nanobanana-3.webp)

## The Full Pipeline — One Command, Done

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

One Telegram command produces a **complete post with images**. Zero human intervention in between. That's the core of automation -- eliminating the middle steps.

## The Detour — Why I Had to Switch from AI Studio to Vertex AI

The code above didn't work on the first try. There was a significant debugging detour, and documenting it here might save someone else two hours.

### The AI Studio API Key Trap — quota = 0

I started with a free API key from AI Studio. The documentation clearly stated that free image generation was available. But when I actually made the call:

```
429 RESOURCE_EXHAUSTED: Quota exceeded for
GenerateContent:imageGeneration
```

`gemini-2.0-flash-exp`, `gemini-2.5-flash-image` -- same error across the board. After digging into it, I found that Google had set the image generation quota to 0 on the free tier. A classic case of documentation not matching reality.

### Switching to Vertex AI — Same Model, Different Infrastructure

The solution was [Google Cloud Vertex AI](https://console.cloud.google.com/vertex-ai/studio). Same Gemini models, but billed per GCP project, which means no arbitrary quota restrictions.

The migration was surprisingly straightforward:

```bash
# 1. Enable Vertex AI API in GCP project
# 2. Set up Application Default Credentials
gcloud auth application-default login

# 3. Authenticate Google account in browser → done
```

The code change was exactly one line:

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

Added `vertexai=True`. That's it. Same model name. Worked immediately. Two hours of debugging, two minutes to fix. Software engineering in a nutshell.

### 3-Tier Fallback Strategy — The Service Must Never Stop

Here's the final fallback architecture I settled on:

```
Priority 1: Vertex AI (ADC auth) → Stable, billing-based
Priority 2: AI Studio (API key) → Free but potentially quota-limited
Priority 3: SVG placeholder → Last resort
```

No matter what happens, the blog generation pipeline never stops. If image generation fails, an SVG placeholder holds the spot. Shipping beats perfection -- a philosophy I picked up from production environments.

## Cost Breakdown — $0 Additional When You Build It Yourself

| Item | Monthly Cost |
|---|---|
| Claude Code Max | Already subscribed |
| Nanobanana images | **$0** (free 500/day) |
| Telegram Bot API | **$0** |
| GitHub Pages hosting | **$0** |
| **Total** | **Additional cost $0** |

Third-party blog image services run $20+/month. Building it yourself costs $0. Yes, the initial implementation takes time, but once built, you can generate hundreds of images indefinitely for free. In terms of ROI, it's not even close.

## Series Progress

1. [AI Assistant Intro](/posts/telegram-ai-assistant-intro-en) ✅
2. [Telegram Bot Setup](/posts/telegram-bot-setup-en) ✅
3. [OpenClaw-Style Memory](/posts/openclaw-style-memory-en) ✅
4. Nanobanana Image Generation ← **This post**
5. Voice → Meeting Notes/Blog Auto-Generation (next)

Type one line in Telegram and a complete blog post with images appears. The final puzzle piece of the full pipeline is almost in place.

---

There's no end to automation. But image generation? That part is done -- nothing left to touch.
