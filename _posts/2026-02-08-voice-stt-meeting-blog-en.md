---
title: 'From Voice Message to Meeting Notes + Blog Post — The Power of Gemini STT'
description: 'Send a voice message to the Telegram bot and Gemini transcribes it, then auto-converts it into meeting notes or a blog post. Just record on your iPhone and you are done.'
date: 2026-02-08 00:00:00 +0900
tags: ['voice', 'stt', 'gemini', 'telegram', 'meeting-notes', 'automation', 'claude-code']
categories: [ai-automation]
image:
  path: /images/blog/voice-stt-telegram-1.webp
  width: 800
  height: 800
author: wonder
lang: en
twin: voice-stt-meeting-blog
---

## I Hated Writing Meeting Notes

Meetings are fine. Writing meeting notes after? That I hate.

Record on the MacBook, run STT, organize with Gemini, copy-paste into Notion. I kept repeating this process every time. Same thing when writing blog posts about dates or meetup reviews. Record a voice memo while the memory is fresh, transcribe it later, polish it into blog format.

**Every single step in between is manual labor.**

I'm the kind of person who can't tolerate repetitive work. Time to automate.

## The Idea Was Simple

The existing bot already had text → blog functionality. What if I just added **voice input** on top?

```
Record voice on iPhone
  ↓
Send via Telegram
  ↓
Gemini STT → Text transcription
  ↓
[📋 Meeting Notes]  [📝 Blog]  ← Inline keyboard
  ↓                    ↓
Notion-ready markdown  Blog post + 3 images
```

One button press and you get either meeting notes or a blog post.
Send the recording to Telegram after a meeting and the result arrives in 5 minutes. All the middle steps just disappear.

![Concept diagram](/images/blog/voice-stt-telegram-2.webp)

## Gemini STT — Using What I Already Have

I didn't want to add a new service. The **Gemini API I'm already using for image generation also handles audio**.

It's multimodal — it understands text, images, and audio simultaneously. Just feed it an audio file and say "transcribe this" and you're done. Zero additional dependencies.

```python
# bot/stt.py — core section
from google import genai
from google.genai import types

async def transcribe_audio(audio_data: bytes, mime_type: str = "audio/ogg") -> dict:
    client = genai.Client(vertexai=True, project="...", location="us-central1")

    audio_part = types.Part(
        inline_data=types.Blob(mime_type=mime_type, data=audio_data)
    )

    response = await asyncio.to_thread(
        client.models.generate_content,
        model="gemini-2.5-flash",
        contents=[audio_part, "이 오디오를 한국어로 정확하게 전사해줘."],
    )

    return {"text": response.candidates[0].content.parts[0].text}
```

Key points:
- Uses `types.Blob` to pass the audio binary directly. Inline, no file upload needed.
- Telegram voice messages use OGG Opus format, which Gemini supports natively.
- `gemini-2.5-flash` is the primary, `gemini-2.0-flash` is the fallback. Same pattern as image generation.
- Uses the existing `google-genai` SDK. Nothing new to install.

## Telegram Voice Handler

To receive voice messages, use the `filters.VOICE | filters.AUDIO` filter.

```python
# bot/main.py
app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))
app.add_handler(CallbackQueryHandler(handle_voice_callback, pattern="^voice_"))
```

When a voice message arrives:

1. **Download** — `media.get_file()` → `download_as_bytearray()`
2. **Gemini STT** — Pass the audio binary to Gemini
3. **Preview** — Show 300-character transcription preview + inline keyboard

```python
keyboard = [[
    InlineKeyboardButton("📋 회의록", callback_data="voice_minutes"),
    InlineKeyboardButton("📝 블로그", callback_data="voice_blog"),
]]
reply_markup = InlineKeyboardMarkup(keyboard)
```

Two buttons. Meeting notes or blog. That's all there is to it.

![Inline keyboard selection](/images/blog/voice-stt-telegram-3.webp)

## Meeting Notes Mode — Copy-Paste Straight to Notion

Hit the "📋 Meeting Notes" button and Claude transforms the transcription into structured markdown.

```markdown
## Meeting Notes — 2026-02-08

### Attendees
- John, Jane

### Key Agenda
1. Q1 marketing strategy discussion
2. New feature roadmap finalization

### Discussion
**1. Q1 Marketing Strategy**
- Proposed 30% increase in SNS ad budget
- 3 influencer collaborations planned
...

### Decisions
- [ ] Final review of SNS ad budget (Jane, by 2/15)
- [ ] Create influencer list (John, by 2/12)

### Action Items
| Owner | Item | Deadline |
|-------|------|----------|
| Jane | Budget review | 2/15 |
| John | Influencer list | 2/12 |
```

Copy this straight into Notion and it renders perfectly. Checkboxes, tables — everything just works.

Send one recording file after a meeting and the notes are done. No more spending 30 minutes organizing after every meeting.

## Blog Mode — Images Included in One Shot

Hit the "📝 Blog" button and it flows through the existing `/blog` pipeline.

1. Nanobanana (Gemini) generates 3 images
2. Claude restructures the transcription into a blog post
3. Generates a markdown file with frontmatter + embedded images
4. Saved as `draft: true` → Publish with `/publish`

Walk home after a date, record a voice memo while walking → send to Telegram → tap the Blog button → 5 minutes later, a complete blog draft with images.

This works. It actually works. I built it and I'm still amazed.

![Result image](/images/blog/voice-stt-telegram-4.webp)

## Full Architecture

```
📱 iPhone
  │ Voice recording / audio file
  ↓
🤖 Telegram Bot (handle_voice)
  │ 1. Download audio
  │ 2. Gemini STT (audio → text)
  ↓
📝 Transcription result + inline keyboard
  ├─ [📋 Meeting Notes] → Claude → Notion-ready markdown
  │
  └─ [📝 Blog] → Nanobanana: 3 images
                → Claude → Blog post (draft)
                → /publish → git push → deployed
```

Only one new file: `bot/stt.py`. Everything else was just adding handlers to existing code.

## Code Changes Summary

| File | Change | Description |
|------|--------|-------------|
| `bot/stt.py` | **New** | Gemini STT module (80 lines) |
| `bot/handlers.py` | Added | Voice handler + callback handler (170 lines) |
| `bot/main.py` | Added | Handler registration (6 lines) |

Additional dependencies: **None**. Everything was done with the `google-genai` and `python-telegram-bot` packages I was already using.

## Series Progress

1. [AI Assistant Intro](/posts/telegram-ai-assistant-intro-en) ✅
2. [Telegram Bot Setup](/posts/telegram-bot-setup-en) ✅
3. [OpenClaw-Style Memory](/posts/openclaw-style-memory-en) ✅
4. [Nanobanana Image Generation](/posts/nanobanana-image-gen-en) ✅
5. Voice → Meeting Notes/Blog Auto-Generation ← **This post**

---

One voice message becomes a full article. Additional cost: $0. Laziness created yet another feature.

In the end, the best automation is the kind that eliminates the steps in between.
