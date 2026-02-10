---
title: "Implementing OpenClaw-Style Memory — Teaching My AI to Remember"
description: 'Analyzed OpenClaw''s file-based memory system and applied it to my Claude Code Telegram bot. MEMORY.md + daily notes — only remembering what matters.'
date: 2026-02-06 00:00:00 +0900
tags: ['claude-code', 'telegram', 'openclaw', 'memory', 'automation', 'vibe-coding']
categories: [ai-automation]
image:
  path: /images/blog/openclaw-memory-1.webp
  width: 800
  height: 800
author: wonder
lang: en
twin: openclaw-style-memory
---

## My Assistant Had the Memory of a Goldfish

In the [previous post](/posts/telegram-bot-setup-en), I built the Telegram bot.
But this thing couldn't remember a conversation from 3 seconds ago.

"Hey, modify that code from earlier" → "What code?"

This isn't an assistant. It's like meeting a stranger every single time.

Honestly, I was a bit annoyed. I built you. Why don't you know me?

## I Tore Apart OpenClaw

I analyzed OpenClaw's memory system, which has been getting a lot of buzz lately. The core idea turned out to be surprisingly simple.

**Files are the memory.** Not the entire conversation — just the important stuff, saved to markdown files.

### OpenClaw Memory Structure

```
MEMORY.md              ← Long-term memory (preferences, decisions)
memory/2026-02-06.md   ← Today's daily notes
memory/2026-02-05.md   ← Yesterday's daily notes
```

Here's how it works:

1. Session starts → Only loads `MEMORY.md` + today/yesterday notes
2. During conversation → AI decides "this is worth remembering" and writes it down
3. Context fills up → Auto-save
4. Next session → Reads saved files to maintain context

Vector DB? RAG? Nope. **Just markdown files.**
A human can even open them and edit manually. That simplicity is the whole point.

I'm someone who hates complexity. I saw this and decided to copy it immediately.

![OpenClaw memory structure](/images/blog/openclaw-memory-2.webp)

## First, I Saved the Entire Conversation

### v1: The Dumb Approach

```json
[
  {"role": "user", "content": "Deploy the blog", "timestamp": "..."},
  {"role": "assistant", "content": "Deploy complete...", "timestamp": "..."},
  ...40 messages saved in full
]
```

That was dumb. Token waste, useless chatter included, files growing endlessly. Even keeping just 20 messages made the prompt absurdly long.

### v2: OpenClaw Style — Only the Important Stuff

```
data/
├── MEMORY.md         ← "User prefers conda", "ENFP developer"
└── daily/
    ├── 2026-02-07.md  ← What happened today
    └── 2026-02-06.md  ← What happened yesterday
```

Prompt length dropped to 1/5. Should've done this from the start.

## Implementation — Easier Than You'd Think

### 1. The [MEMO] Tag — AI Picks What to Remember

I added this to the system prompt:

```
Important: If there's information worth remembering during conversation,
add it at the end of your response in this format:
[MEMO] Content to remember
```

When Claude responds and decides something is important, it attaches a `[MEMO]` tag.
The bot parses it and auto-saves. The user only sees a clean response with no tags.

```python
def extract_and_save_memos(response: str) -> str:
    lines = response.split("\n")
    clean_lines = []
    memos = []

    for line in lines:
        if line.strip().startswith("[MEMO]"):
            memo = line.strip()[6:].strip()
            memos.append(memo)
        else:
            clean_lines.append(line)

    for memo in memos:
        # Keywords like "prefers", "always" → long-term memory
        # Everything else → daily note
        if any(kw in memo for kw in ["선호", "항상", "기본", "설정"]):
            append_memory(memo)
        else:
            append_daily_note(memo)

    return "\n".join(clean_lines).strip()
```

### 2. Long-Term Memory (MEMORY.md)

Preferences, profile info, decisions. Loaded at the start of every session.

```markdown
# WonderX Long-Term Memory

- [2026-02-06 17:30] User prefers conda environments
- [2026-02-06 17:45] Blog framework: Astro + GitHub Pages
- [2026-02-06 18:00] Comment system: Disqus (guest comments enabled)
```

You can manually add entries too:

```
/remember conda env name is wonderx-bot
```

### 3. Daily Notes (daily/YYYY-MM-DD.md)

What happened today. Only today and yesterday's notes get auto-loaded.

```markdown
# 2026-02-06 Daily Notes

- [17:00] User: Build me a Telegram bot
- [17:15] Started blog SEO optimization
- [17:30] Added category sidebar
- [18:00] Implemented OpenClaw-style memory system
```

### 4. Prompt Assembly

Here's the structure sent to Claude:

```
[System Instructions]
You are WonderX AI assistant. A lazy developer's assistant...

---

[Long-Term Memory]
# WonderX Long-Term Memory
- Prefers conda, Astro blog, Disqus comments...

[Recent Notes]
# 2026-02-06 Daily Notes
- Telegram bot implementation, memory system implementation...

---

[Current Request]
Add search functionality to the memory system we built earlier
```

This way, Claude responds **already knowing what happened today**.
It knows what "that code from earlier" refers to. Goldfish no more.

![Memory system in action](/images/blog/openclaw-memory-3.webp)

## OpenClaw vs My Bot — Side by Side

| | OpenClaw | WonderX Bot |
|---|---|---|
| **Memory approach** | Markdown files | Markdown files (same) |
| **Auto-save** | Memory flush + AI judgment | [MEMO] tag + AI judgment |
| **Manual save** | "Remember this" in natural language | `/remember` command |
| **Cost** | API token billing (Heartbeat costs ~$20/night) | Included in Max plan ($0) |
| **Search** | SQLite + vector + BM25 hybrid | Only loads today/yesterday (simple) |
| **Complexity** | TypeScript, 39 files | Python, 1 file (memory.py) |

OpenClaw has semantic search, embeddings, SQLite indexes — the whole nine yards. Impressive.
But honestly, for a personal assistant, it's overkill.

Today/yesterday notes + long-term memory is enough. If I need search later, I'll add it then.
**Over-engineering is the enemy of laziness.**

## New Commands

| Command | Function |
|---|---|
| `/memory` | View current memory state |
| `/remember content` | Manually save to long-term memory |
| `/clear` | Reset long-term memory |

## Gotchas

### Writing vague instructions like "save things worth remembering" is a recipe for failure

I wrote the system prompt lazily at first. Claude didn't know what to save — so it either saved nothing or saved useless stuff.

Once I defined a clear format with `[MEMO]` and gave examples, it worked perfectly.
**Give AI vague instructions, get vague results.** Obvious, but I keep forgetting.

### Long-term vs daily classification matters

"User prefers conda" → Long-term memory
"Deployed the blog today" → Daily note

Mess up the classification and long-term memory gets polluted with noise. Keyword-based classification isn't perfect, but it's right about 80% of the time. The other 20% I fix manually.

## Next Episode Preview

- **Scheduling & Heartbeat**: Automatic morning status alerts, blog build check automation
- This is OpenClaw's most popular feature. Once this works, it becomes a real "autonomous assistant"

---

AI without memory is a tool. AI with memory becomes a colleague.

---

*Full code is in a private repo. Questions? Reach out at [x@wonderx.co.kr](mailto:x@wonderx.co.kr).*
