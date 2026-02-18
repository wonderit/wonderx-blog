---
title: 'How I Made AI Read My Blog and Draw the Images — Gemini Blog Image Pipeline'
description: 'A system that analyzes blog content and auto-generates scene-specific images. Reference photo mood matching, hero image strategy, and model fallbacks.'
date: 2026-02-12 14:00:00 +0900
tags: ['Gemini-API', 'AI-image-generation', 'telegram-bot', 'automation', 'Python', 'Imagen']
categories: [tech]
image:
  path: /images/blog/gemini-blog-image-pipeline-1.webp
  width: 800
  height: 800
author: wonder
lang: en
twin: gemini-blog-image-pipeline
---

## "Generate 4 images" Is Not Automation

When people add images to blog posts, they usually do this: write the post, mentally picture what images would match, then manually craft prompts for each one. Four images means four separate prompts. Eight images, eight prompts.

I found this tedious. If I write a post, the images should just appear. A system that reads the content, figures out what scenes are needed, generates mood-appropriate prompts, and produces the images. That's what I built.

Here's how my Telegram bot works now:

1. Gemini analyzes the full blog post
2. Auto-generates scene-specific image prompts
3. If reference photos exist, their mood gets reflected
4. The hero image is generated last
5. If a model fails, it automatically falls back to the next

This post covers the technical structure behind each step and the reasoning behind the design decisions.

![Pipeline overview](/images/blog/gemini-blog-image-pipeline-2.webp)

## Step 1: Post Analysis → Auto-Generated Prompts

The core is the `analyze_post_for_images()` function. It sends the blog post's markdown body to Gemini 2.5 Flash, which returns scene-specific image prompts.

```python
analysis_prompt = (
    f"You are generating image prompts for a Korean blog post.\n"
    f"Topic: {topic}\n"
    f"Post content:\n{post_content[:3000]}\n\n"
    f"Generate exactly {count} image prompts.\n"
    f"Rules:\n"
    f"1. Prompt #1 is the HERO image (wide 16:9 landscape).\n"
    f"2. Prompts #2-N: specific scenes from different sections.\n"
    f"3. Each prompt MUST describe a concrete, specific scene.\n"
    f"4. Match the mood: winter → cool tones, cafe → warm tones.\n"
    f"5. Style: stylized digital illustration, NOT cartoonish.\n"
)
```

The critical rule here is **"draw concrete scenes."** Not "an abstract image about dating" but "a person standing in front of a convenience store on a winter night, holding an Americano" — the actual scene described in the writing.

Early on, I only passed the topic to the image generator. The results felt disconnected from the content. The post talked about a café but the image showed a mountain landscape. Switching to full-text analysis dramatically improved coherence.

### Image Count Adapts to Content Length

Generating exactly 4 images every time is wasteful. Eight images on a short post is overkill; three on a long one is not enough.

```python
def _calc_image_count(post_content: str) -> int:
    sections = post_content.count('\n## ') + post_content.count('\n---')
    count = max(4, min(8, sections // 2 + 1))
    return count
```

Section count determines image count. More headings and dividers mean more visual scenes. Minimum 4, maximum 8.

![Post analysis → prompt generation](/images/blog/gemini-blog-image-pipeline-3.webp)

## Step 2: Reflecting Reference Photo Atmosphere

This is a recent addition. When reference photos exist for a post (e.g., actual photos taken at a café), their atmosphere gets baked into the image generation.

The implementation has two stages.

**Stage 1**: Send reference photos to Gemini for analysis.

```python
async def _analyze_reference_images(ref_image_paths):
    analyze_prompt = (
        "Analyze these reference photos and describe:\n"
        "1. Location/setting\n"
        "2. Atmosphere/mood\n"
        "3. Color palette\n"
        "4. Key visual elements\n"
        "5. Time of day and season indicators\n"
    )
    contents = image_parts + [analyze_prompt]
    response = client.models.generate_content(
        model="gemini-2.5-flash", contents=contents
    )
    return response.text  # "Warm-lit café, wooden tables..."
```

**Stage 2**: Inject the analysis into prompt generation.

```
📷 REFERENCE PHOTOS CONTEXT:
Warm-lit café interior with wooden tables, ambient
lighting, and minimalist decor. Cozy evening atmosphere.

IMPORTANT: Use the atmosphere, setting, colors from
these reference photos in your image prompts.
```

This way, "warm café ambiance" permeates every image prompt. Upload real café photos, and the illustrations capture that exact vibe.

Why not feed the images directly to the generation model? Because Imagen 4 (Fast/Ultra) is a text-to-image model — it doesn't accept reference images as input. Hence the detour: reference image → text analysis → prompt enrichment.

![Reference image analysis flow](/images/blog/gemini-blog-image-pipeline-4.webp)

## Step 3: Why the Hero Image Comes Last

The hero image is the most important image in a blog post. It's the first thing people see in search results, social shares, and RSS feeds. But generating it first creates a problem.

The reasoning is simple. **When body images are generated first, the full visual context of the post is established.** The hero image should synthesize that context, so it turns out best when created last.

```python
# 1) Body images first (index 1~N)
for i in range(1, len(prompts)):
    results[i] = await generate_image(
        prompt=prompts[i], filename=f"{slug}-{i+1}.webp"
    )

# 2) Hero image last (index 0)
hero_prompt = (
    f"{prompts[0]}\n\n"
    f"IMPORTANT: This is a HERO image. "
    f"Must be wide 16:9 landscape aspect ratio."
)
results[0] = await generate_image(
    prompt=hero_prompt, filename=f"{slug}-1.webp"
)
```

One additional constraint for the hero: **forced 16:9 landscape ratio.** A portrait hero image breaks blog layouts.

![Hero image strategy](/images/blog/gemini-blog-image-pipeline-5.webp)

## Step 4: Model Fallback — Failure Is Expected

AI image generation APIs fail more often than you'd think. Quota exhaustion, content filtering, server errors, timeouts. Depending on a single model means seeing "Image generation failed" far too often.

My model fallback chain:

### Fast Mode (default, $0.02/image)
```
Imagen 4 Fast → Gemini 2.5 Flash → Gemini 3 Pro → Placeholder
```

### Pro Mode (high quality, $0.134/image)
```
Gemini 3 Pro → Gemini 2.5 Flash → Imagen 4 Fast → Placeholder
```

Each model tries both Vertex AI and AI Studio clients. When one side's quota is exhausted, the other handles the request.

Worst case, if every model fails, an SVG placeholder is generated. A post shouldn't be blocked just because images couldn't be created.

### Fallback Prompts Too

Gemini's analysis can fail as well. For this, I prepared 8 prompt templates that activate in sequential order.

Initially I only had 4 templates, and discovered a bug where an 8-image post only generated the first 4. More scenes require more fallback variety.

## Preventing Duplication — Hero Image Appearing in Body

A bug I discovered after building the pipeline: Claude sometimes placed the hero image (`slug-1.webp`) in the body text too. Since Jekyll's Chirpy theme auto-renders the frontmatter `image:` as the hero, having it appear again in the body creates duplication.

The fix was a single prompt rule:

```
⚠️ Hero image (slug-1.webp) is for frontmatter only.
Never place it in the body. Body images start from -2.
```

With AI-based automation, if you don't explicitly state a rule, the AI makes "reasonable decisions" that create problems. Humans wouldn't make this mistake, but AI does it naturally. Discovering these edge cases and adding rules — that's how this system is maintained.

![Final output](/images/blog/gemini-blog-image-pipeline-6.webp)

## How It All Works Now

When I send "write a blog post" on Telegram:

1. Claude writes the post first (under 5 minutes)
2. Gemini analyzes the content → generates 4–8 scene prompts
3. If reference photos exist, mood analysis → reflected in prompts
4. Body images generated first → hero image last
5. Failed models auto-swap to the next in chain
6. Images saved to blog directory + Google Drive backup
7. git push → deployed

All from a single message.

Cost in Fast mode: ~**$0.08** for 4 images, **$0.12** for 6. Writing 30 posts a month keeps image costs under **$3.60**.

If quality feels lacking, pressing "Regenerate in Pro quality" switches to Gemini 3 Pro at $0.134 per image. The default stays cheap and fast; quality upgrades happen only on demand.

The core principle of automation is "keep defaults cheap and fast, handle exceptions robustly." This image pipeline follows that principle.
