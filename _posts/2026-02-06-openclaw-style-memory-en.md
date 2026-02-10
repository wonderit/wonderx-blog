---
title: "Implementing OpenClaw-Style Memory — Teaching My AI to Remember"
description: 'Analyzed OpenClaw''s file-based memory system and applied it to my Claude Code Telegram bot. MEMORY.md + daily notes — only remembering what matters.'
date: 2026-02-06 00:00:00 +0900
tags: ['Claude-Code', 'Telegram', 'OpenClaw', 'memory', 'automation', 'vibe-coding']
categories: [ai-automation]
image:
  path: /images/blog/openclaw-memory-1.webp
  width: 800
  height: 800
author: wonder
lang: en
twin: openclaw-style-memory
---

## An Assistant with Zero Context Window Is Not an Assistant

In the [previous post](/posts/telegram-bot-setup-en), I built the Telegram bot. It worked. But it had one critical flaw: it could not remember a conversation from 3 seconds ago.

"Hey, modify that code from earlier" → "What code?"

Every message was a first encounter. No prior context was retained. This is not an AI "assistant" — it is a call center that starts from scratch on every interaction.

The root cause is straightforward. Claude Code's `-p` mode is fundamentally stateless. Each invocation is an independent session with no automatic transfer of conversation history. A memory system has to be built explicitly.

## Analyzing OpenClaw's Memory Architecture

I dug into the memory system of OpenClaw, a project that has been gaining significant traction recently. I expected complex infrastructure — vector databases, RAG pipelines, embedding models. The core turned out to be surprisingly simple.

**Files are the memory.** Instead of storing entire conversations, the AI decides what is worth remembering and writes only that to markdown files.

### OpenClaw Memory Structure

```
MEMORY.md              ← Long-term memory (preferences, decisions)
memory/2026-02-06.md   ← Today's daily notes
memory/2026-02-05.md   ← Yesterday's daily notes
```

The operating principle breaks down into four steps:

1. **Session start** → Load only `MEMORY.md` + today/yesterday daily notes
2. **During conversation** → AI judges "this is worth remembering" and auto-records
3. **Context saturation** → Auto-save and memory flush
4. **Next session** → Read saved files to restore context

Vector DB? RAG pipeline? None of that. **Just markdown files.** A human can open them and edit directly. A debuggable memory system — this transparency is OpenClaw's core design philosophy.

I concluded this approach was optimal for a personal assistant and decided to implement it immediately.

![OpenClaw memory structure](/images/blog/openclaw-memory-2.webp)

## From v1 to v2: Full Dump vs Selective Storage

### v1: Dumping the Entire Conversation as JSON

The first approach was to save every message verbatim.

```json
[
  {"role": "user", "content": "Deploy the blog", "timestamp": "..."},
  {"role": "assistant", "content": "Deploy complete...", "timestamp": "..."},
  ...40 messages saved in full
]
```

The problems surfaced immediately. Severe token waste, trivial exchanges like "thanks lol" included alongside critical information, and file size growing exponentially. Even retaining only 20 messages consumed a substantial portion of the available context window.

### v2: OpenClaw Style — Selective Storage of Important Information

```
data/
├── MEMORY.md         ← "User prefers conda", "ENFP developer"
└── daily/
    ├── 2026-02-07.md  ← What happened today
    └── 2026-02-06.md  ← What happened yesterday
```

Prompt length dropped to roughly 1/5 of v1 while conveying equivalent information. The core principle behind this shift is simple: **"what to remember" matters more than "what happened."**

## Implementation Details

### 1. The [MEMO] Tag System — AI Self-Selects What to Remember

I added the following instruction to the system prompt:

```
Important: If there's information worth remembering during conversation,
add it at the end of your response in this format:
[MEMO] Content to remember
```

When Claude generates a response, it attaches a `[MEMO]` tag to information it judges worth preserving. The bot parses these tags, saves them automatically, and delivers only the clean, tag-free response to the user.

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

Stores user preferences, profile information, and project decisions — information that must persist across sessions. Loaded automatically at the start of every session.

```markdown
# WonderX Long-Term Memory

- [2026-02-06 17:30] User prefers conda environments
- [2026-02-06 17:45] Blog framework: Astro + GitHub Pages
- [2026-02-06 18:00] Comment system: Disqus (guest comments enabled)
```

Manual entries are also supported:

```
/remember conda env name is wonderx-bot
```

### 3. Daily Notes (daily/YYYY-MM-DD.md)

Records tasks performed on a given date. The load scope is limited to today plus yesterday. Notes from three days ago are not auto-loaded — if something is important enough to persist, it gets promoted to long-term memory.

```markdown
# 2026-02-06 Daily Notes

- [17:00] User: Build me a Telegram bot
- [17:15] Started blog SEO optimization
- [17:30] Added category sidebar
- [18:00] Implemented OpenClaw-style memory system
```

### 4. Prompt Assembly Structure

The final prompt sent to Claude is assembled in this structure:

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

The effect is clear. Claude responds **with knowledge of what happened today**, which means it can infer what "that code from earlier" refers to. The stateless problem is solved.

![Memory system in action](/images/blog/openclaw-memory-3.webp)

## OpenClaw vs WonderX Bot — Comparative Analysis

| | OpenClaw | WonderX Bot |
|---|---|---|
| **Memory approach** | Markdown files | Markdown files (same) |
| **Auto-save** | Memory flush + AI judgment | [MEMO] tag + AI judgment |
| **Manual save** | "Remember this" in natural language | `/remember` command |
| **Cost** | API token billing (Heartbeat costs ~$20/night) | Included in Max plan ($0) |
| **Search** | SQLite + vector + BM25 hybrid | Only loads today/yesterday (simple) |
| **Complexity** | TypeScript, 39 files | Python, 1 file (memory.py) |

OpenClaw ships with semantic search, embeddings, and SQLite indexes — a fully-featured system. But does a personal assistant need all of this? My assessment was "not yet."

Today/yesterday notes plus long-term memory cover the vast majority of everyday development support scenarios. This is the YAGNI (You Ain't Gonna Need It) principle in action. When the memory store grows to hundreds of entries and search becomes a bottleneck, I will add SQLite or vector search at that point.

**Implementing features you do not yet need is voluntarily creating technical debt.**

## New Commands

| Command | Function |
|---|---|
| `/memory` | View current memory state |
| `/remember content` | Manually save to long-term memory |
| `/clear` | Reset long-term memory |

## Gotchas

### Vague Instructions Produce Vague Results

I initially wrote the system prompt as a loose directive: "save things worth remembering." The outcome was predictable. Claude could not determine what to save — it either saved nothing, or recorded meaningless entries like "user said hello."

Defining a clear format with `[MEMO]` and providing concrete examples immediately improved accuracy. Giving AI vague instructions yields vague results — a fundamental principle of prompt engineering, yet one that is surprisingly easy to forget in practice.

### Classification Accuracy Between Long-Term and Daily

- "User prefers conda" → Long-term memory (correct)
- "Deployed the blog today" → Daily note (correct)

When this classification fails, long-term memory becomes polluted with ephemeral information. The current implementation uses keyword matching ("prefers," "always," "default," "setting"), achieving roughly 80% accuracy. The remaining 20% requires manual correction.

A future improvement path is delegating classification to Claude itself. Having the AI tag entries as `[MEMO:long-term]` vs `[MEMO:daily]` would likely outperform keyword matching in accuracy.

## Next Episode Preview

- **Scheduling and Heartbeat**: Automatic morning status alerts, blog build check automation
- This is OpenClaw's most popular feature. Once operational, the bot upgrades from "works when you ask" to "finds work on its own"

---

AI without memory is a tool. AI with memory becomes a colleague.

---

*Full code is in a private repo. Questions? Reach out at [x@wonderx.co.kr](mailto:x@wonderx.co.kr).*
