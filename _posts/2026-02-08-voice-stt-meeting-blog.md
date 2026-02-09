---
title: '음성 메시지 하나로 회의록 + 블로그 자동 생성 — Gemini STT의 힘'
description: '텔레그램 봇에 음성 메시지를 보내면 Gemini가 전사하고, 회의록이나 블로그로 자동 변환한다. 아이폰에서 녹음만 하면 끝이다.'
date: 2026-02-08 00:00:00 +0900
tags: ['voice', 'stt', 'gemini', 'telegram', 'meeting-minutes', 'automation', 'claude-code']
categories: [ai-automation]
image:
  path: /images/blog/voice-stt-telegram-1.jpg
  width: 800
  height: 800
author: wonder
---

## 회의록을 쓰기 싫었다

회의는 괜찮다. 회의록 쓰는 게 싫다.

맥북에서 녹음하고, STT 돌리고, Gemini로 정리하고, 노션에 복붙하고. 매번 이 과정을 반복했다. 소개팅이나 미팅 후기를 블로그로 쓸 때도 마찬가지다. 기억이 생생할 때 음성으로 쭉 녹음하고, 나중에 텍스트로 옮기고, 블로그 형태로 다듬는다.

**이 중간 과정이 전부 노가다다.**

나는 이런 반복 작업을 참을 수 없는 사람이다. 자동화하기로 했다.

## 아이디어는 단순했다

기존 봇에 이미 텍스트 → 블로그 기능은 있다. 여기에 **음성 입력**만 추가하면?

```
아이폰에서 음성 녹음
  ↓
텔레그램으로 전송
  ↓
Gemini STT → 텍스트 전사
  ↓
[📋 회의록]  [📝 블로그]  ← 인라인 키보드
  ↓                ↓
노션용 마크다운    블로그 포스트 + 이미지 3장
```

버튼 하나로 회의록이든 블로그든 바로 나온다.
녹음 끝나고 텔레그램에 보내면 5분 후에 결과가 온다. 중간 과정이 사라졌다.

![개념도](/images/blog/voice-stt-telegram-2.jpg)

## Gemini STT — 이미 있는 걸 쓴다

새로운 서비스를 추가하고 싶지 않았다. 이미 이미지 생성에 쓰고 있는 **Gemini API가 오디오도 처리**한다.

멀티모달이라 텍스트, 이미지, 오디오를 동시에 이해한다. 오디오 파일 넣고 "전사해줘"라고 하면 끝이다. 추가 의존성 0개.

```python
# bot/stt.py — 핵심 부분
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

포인트:
- `types.Blob`으로 오디오 바이너리를 직접 전달한다. 파일 업로드 없이 인라인으로.
- 텔레그램 음성 메시지는 OGG Opus 포맷인데, Gemini가 네이티브로 지원한다.
- `gemini-2.5-flash`가 1순위, `gemini-2.0-flash`가 폴백. 이미지 생성이랑 같은 패턴이다.
- 기존 `google-genai` SDK 그대로 사용. 새로 설치할 거 없다.

## 텔레그램 음성 핸들러

음성 메시지를 받으려면 `filters.VOICE | filters.AUDIO` 필터를 쓴다.

```python
# bot/main.py
app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))
app.add_handler(CallbackQueryHandler(handle_voice_callback, pattern="^voice_"))
```

음성 메시지가 오면:

1. **다운로드** — `media.get_file()` → `download_as_bytearray()`
2. **Gemini STT** — 오디오 바이너리를 Gemini에 전달
3. **미리보기** — 전사 결과 300자 미리보기 + 인라인 키보드

```python
keyboard = [[
    InlineKeyboardButton("📋 회의록", callback_data="voice_minutes"),
    InlineKeyboardButton("📝 블로그", callback_data="voice_blog"),
]]
reply_markup = InlineKeyboardMarkup(keyboard)
```

버튼 두 개. 회의록이냐 블로그냐. 이게 전부다.

![인라인 키보드 선택](/images/blog/voice-stt-telegram-3.jpg)

## 회의록 모드 — 노션에 바로 복붙

"📋 회의록" 버튼을 누르면 Claude가 전사 텍스트를 구조화된 마크다운으로 바꾼다.

```markdown
## 회의록 — 2026-02-08

### 참석자
- 홍길동, 김개발

### 주요 안건
1. Q1 마케팅 전략 논의
2. 신규 기능 로드맵 확정

### 논의 내용
**1. Q1 마케팅 전략**
- SNS 광고 예산 30% 증액 제안
- 인플루언서 협업 3건 진행 예정
...

### 결정 사항
- [ ] SNS 광고 예산안 최종 검토 (김개발, 2/15까지)
- [ ] 인플루언서 리스트 작성 (홍길동, 2/12까지)

### Action Items
| 담당자 | 항목 | 기한 |
|--------|------|------|
| 김개발 | 예산안 검토 | 2/15 |
| 홍길동 | 인플루언서 리스트 | 2/12 |
```

이걸 그대로 노션에 복붙하면 깔끔하게 들어간다. 체크박스, 테이블 전부 지원된다.

회의 끝나고 녹음 파일 하나 보내면 회의록 완성. 더 이상 회의 끝나고 30분 씩 정리할 필요 없다.

## 블로그 모드 — 이미지까지 한 번에

"📝 블로그" 버튼을 누르면 기존 `/blog` 파이프라인을 탄다.

1. 나노바나나(Gemini)로 이미지 3장 생성
2. Claude가 전사 내용을 블로그 글로 재구성
3. frontmatter + 이미지 삽입된 마크다운 파일 생성
4. `draft: true`로 저장 → `/publish`로 발행

소개팅 다녀와서 걸으면서 음성 녹음 → 텔레그램에 전송 → 블로그 버튼 탭 → 5분 후 이미지 포함된 블로그 초안 완성.

이게 된다. 진짜로 된다. 내가 만들어놓고도 신기하다.

![결과 이미지](/images/blog/voice-stt-telegram-4.jpg)

## 전체 아키텍처

```
📱 iPhone
  │ 음성 녹음 / 오디오 파일
  ↓
🤖 Telegram Bot (handle_voice)
  │ 1. 오디오 다운로드
  │ 2. Gemini STT (audio → text)
  ↓
📝 전사 결과 + 인라인 키보드
  ├─ [📋 회의록] → Claude → 노션용 마크다운
  │
  └─ [📝 블로그] → 나노바나나 이미지 3장
                  → Claude → 블로그 포스트 (draft)
                  → /publish → git push → 배포
```

새로 만든 파일은 `bot/stt.py` 딱 하나. 나머지는 기존 코드에 핸들러만 추가했다.

## 코드 변경 요약

| 파일 | 변경 | 설명 |
|------|------|------|
| `bot/stt.py` | **신규** | Gemini STT 모듈 (80줄) |
| `bot/handlers.py` | 추가 | 음성 핸들러 + 콜백 핸들러 (170줄) |
| `bot/main.py` | 추가 | 핸들러 등록 (6줄) |

추가 의존성: **없음**. 이미 쓰고 있는 `google-genai`와 `python-telegram-bot`으로 전부 해결했다.

## 시리즈 진행 상황

1. [AI 비서 소개](/posts/telegram-ai-assistant-intro) ✅
2. [텔레그램 봇 구축](/posts/telegram-bot-setup) ✅
3. [OpenClaw 스타일 메모리](/posts/openclaw-style-memory) ✅
4. [나노바나나 이미지 생성](/posts/nanobanana-image-gen) ✅
5. 음성 → 회의록/블로그 자동 생성 ← **지금 이 글**

---

음성 하나로 글이 된다. 추가 비용 $0. 게으름이 또 하나의 기능을 만들었다.

결국 가장 좋은 자동화는, 중간 과정을 없애는 거다.
