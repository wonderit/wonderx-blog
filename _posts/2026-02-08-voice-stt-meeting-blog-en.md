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

## How Many Steps Does It Take to Turn a Voice Recording Into a Finished Document?

Here's the answer: **one.** Send a voice message to Telegram, and 5 minutes later you get either polished meeting notes or a complete blog post. No new services added. The same Gemini API I was already using handles everything. Additional cost: $0.

I don't hate meetings. I hate the 30 minutes after every meeting spent organizing notes. The four-step routine: record on MacBook, run STT, organize with Gemini, copy-paste into Notion. Blog posts are the same story -- record voice while the experience is fresh, transcribe later, polish into blog format.

**Every single one of those middle steps is an automation target.** So I eliminated them.

## Design — Adding Voice Input to an Existing Pipeline

The core idea is straightforward. The bot already had text-to-blog functionality. All I needed was a **voice-to-text** conversion layer on top.

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

From the user's perspective: send a recording to Telegram, get a transcription preview with two buttons. Tap one button, and either meeting notes or a blog post is done. The entire middle process vanishes.

![Concept diagram](/images/blog/voice-stt-telegram-2.webp)

## Gemini STT — Solving It Without Adding a New Service

I didn't want to add a dedicated STT service. More dependencies mean more maintenance overhead and more failure points.

Fortunately, the **Gemini API I was already using for image generation also processes audio**. Gemini is a multimodal model -- it understands text, images, and audio simultaneously. Feed it an audio binary with the instruction "transcribe this" and you're done. Zero additional dependencies, zero additional API keys.

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

Four technical points worth noting:

- **`types.Blob` passes the audio binary inline** -- no separate file upload API call required.
- Telegram voice messages use **OGG Opus** format, which Gemini supports natively. No format conversion needed.
- **`gemini-2.5-flash` is the primary model**, with `gemini-2.0-flash` as fallback. Same resilience pattern as image generation.
- Uses the existing `google-genai` SDK. No new packages to install.

## Telegram Voice Handler — Implementation Details

To receive voice messages, register the `filters.VOICE | filters.AUDIO` filter.

```python
# bot/main.py
app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))
app.add_handler(CallbackQueryHandler(handle_voice_callback, pattern="^voice_"))
```

The processing flow when a voice message arrives has three stages:

1. **Download** -- `media.get_file()` then `download_as_bytearray()` to get the binary
2. **Gemini STT** -- pass the audio binary to Gemini for transcription
3. **Preview + Selection** -- display a 300-character transcription preview with an inline keyboard

```python
keyboard = [[
    InlineKeyboardButton("📋 회의록", callback_data="voice_minutes"),
    InlineKeyboardButton("📝 블로그", callback_data="voice_blog"),
]]
reply_markup = InlineKeyboardMarkup(keyboard)
```

The interface is just two buttons. Meeting notes or blog. The downstream pipeline branches based on this single selection.

![Inline keyboard selection](/images/blog/voice-stt-telegram-3.webp)

## Meeting Notes Mode — Structured Output Ready for Notion

Tapping "📋 Meeting Notes" triggers Claude to transform the transcription into structured markdown. The output format was designed specifically for Notion compatibility.

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

Paste this directly into Notion and everything renders cleanly -- checkboxes, tables, the works. Send one recording after a meeting and your notes are done. The 30 minutes you used to spend organizing? Gone.

## Blog Mode — From Voice to a Full Post With Images, One Shot

Tapping "📝 Blog" routes through the existing `/blog` pipeline. This is where the system really shows its power.

1. **Nanobanana** (Gemini) auto-generates 3 images
2. Claude restructures the transcription into a blog post
3. Generates a markdown file with frontmatter + embedded images
4. Saved as `draft: true`, then publish with `/publish`

Here's a real scenario: walk home after a meetup, record voice notes while walking. Send to Telegram. Tap the Blog button. Five minutes later, a complete blog draft with 3 images is waiting. This actually works. I built it and I'm still surprised every time.

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

Only one new file was created: `bot/stt.py`. Everything else was just adding handlers to existing code. This was possible because the pipeline was modularized from the start.

## Code Changes Summary

| File | Change | Description |
|------|--------|-------------|
| `bot/stt.py` | **New** | Gemini STT module (80 lines) |
| `bot/handlers.py` | Added | Voice handler + callback handler (170 lines) |
| `bot/main.py` | Added | Handler registration (6 lines) |

Additional dependencies: **zero.** Everything was accomplished with the `google-genai` and `python-telegram-bot` packages already in use. The fact that a new feature required no new libraries validates the original architecture choices.

## Series Progress

1. [AI Assistant Intro](/posts/telegram-ai-assistant-intro-en) ✅
2. [Telegram Bot Setup](/posts/telegram-bot-setup-en) ✅
3. [OpenClaw-Style Memory](/posts/openclaw-style-memory-en) ✅
4. [Nanobanana Image Generation](/posts/nanobanana-image-gen-en) ✅
5. Voice → Meeting Notes/Blog Auto-Generation ← **This post**

---

One voice message becomes a finished article. Additional cost: $0. Additional dependencies: zero. The best automation eliminates the middle steps entirely.
