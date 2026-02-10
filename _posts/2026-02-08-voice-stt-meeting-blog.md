---
title: '음성 메시지 하나로 회의록 + 블로그 자동 생성 — Gemini STT의 힘'
description: '텔레그램 봇에 음성 메시지를 보내면 Gemini가 전사하고, 회의록이나 블로그로 자동 변환한다. 아이폰에서 녹음만 하면 끝이다.'
date: 2026-02-08 00:00:00 +0900
tags: ['음성인식', 'STT', 'Gemini', '텔레그램봇', '회의록자동화', '자동화', 'Claude-Code']
categories: [ai-automation]
image:
  path: /images/blog/voice-stt-telegram-1.webp
  width: 800
  height: 800
author: wonder
twin: voice-stt-meeting-blog-en
---

## 음성 녹음 하나가 완성된 문서가 되려면 몇 단계가 필요할까?

결론부터 말하면, **텔레그램에 음성 메시지 하나 보내면 5분 후에 회의록이든 블로그든 완성본이 온다.** 추가 서비스 없이, 이미 쓰고 있던 Gemini API 하나로 전부 처리된다. 추가 비용 $0.

나는 회의가 싫은 게 아니다. 회의 끝나고 30분씩 회의록을 정리하는 그 과정이 싫다. 맥북에서 녹음하고, STT 돌리고, Gemini로 정리하고, 노션에 복붙하는 4단계 루틴. 블로그도 마찬가지다 -- 경험이 생생할 때 음성으로 쭉 녹음하고, 나중에 텍스트로 옮기고, 블로그 형태로 다듬는 그 반복.

**이 중간 과정 전부가 자동화 대상이다.** 그래서 없앴다.

## 설계 — 기존 파이프라인에 음성 입력만 추가

핵심 아이디어는 단순하다. 기존 봇에 이미 텍스트 -> 블로그 기능이 있었다. 여기에 **음성 -> 텍스트** 변환 레이어만 하나 추가하면 된다.

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

사용자 입장에서 녹음을 텔레그램에 보내면 전사 결과와 버튼 두 개가 온다. 버튼 하나 누르면 회의록이든 블로그든 완성이다. 중간 과정이 완전히 사라졌다.

![개념도](/images/blog/voice-stt-telegram-2.webp)

## Gemini STT — 새 서비스 추가 없이 해결하는 법

별도의 STT 서비스를 추가하고 싶지 않았다. 의존성이 늘어나면 관리 비용이 늘어나고, 장애 포인트도 늘어난다.

다행히 이미 이미지 생성에 쓰고 있던 **Gemini API가 오디오도 처리**한다. Gemini는 멀티모달 모델이라서 텍스트, 이미지, 오디오를 동시에 이해한다. 오디오 바이너리를 넣고 "전사해줘" 한 마디면 끝이다. 추가 의존성 0개, 추가 API 키 0개.

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

기술적으로 주목할 포인트 네 가지:

- **`types.Blob`으로 오디오 바이너리를 인라인 전달**한다. 파일 업로드 API를 별도로 호출할 필요가 없다.
- 텔레그램 음성 메시지 포맷이 **OGG Opus**인데, Gemini가 이를 네이티브로 지원한다. 포맷 변환 불필요.
- **`gemini-2.5-flash`가 1순위**, `gemini-2.0-flash`가 폴백이다. 이미지 생성과 동일한 폴백 패턴을 적용했다.
- 기존 `google-genai` SDK를 그대로 사용한다. 새로 설치할 패키지가 없다.

## 텔레그램 음성 핸들러 — 구현 상세

음성 메시지를 받으려면 `filters.VOICE | filters.AUDIO` 필터를 등록한다.

```python
# bot/main.py
app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))
app.add_handler(CallbackQueryHandler(handle_voice_callback, pattern="^voice_"))
```

음성 메시지가 도착했을 때의 처리 흐름은 세 단계다:

1. **다운로드** -- `media.get_file()` -> `download_as_bytearray()`로 바이너리 획득
2. **Gemini STT** -- 오디오 바이너리를 Gemini에 전달해서 텍스트 전사
3. **미리보기 + 선택** -- 전사 결과 300자 미리보기와 인라인 키보드를 표시

```python
keyboard = [[
    InlineKeyboardButton("📋 회의록", callback_data="voice_minutes"),
    InlineKeyboardButton("📝 블로그", callback_data="voice_blog"),
]]
reply_markup = InlineKeyboardMarkup(keyboard)
```

인터페이스는 버튼 두 개가 전부다. 회의록이냐 블로그냐. 이 선택에 따라 후속 파이프라인이 분기된다.

![인라인 키보드 선택](/images/blog/voice-stt-telegram-3.webp)

## 회의록 모드 — 노션에 바로 복붙 가능한 구조화된 출력

"📋 회의록" 버튼을 누르면 Claude가 전사 텍스트를 구조화된 마크다운으로 변환한다. 출력 포맷은 노션 호환성을 고려해서 설계했다.

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

이걸 노션에 그대로 붙여넣으면 체크박스, 테이블 전부 깔끔하게 렌더링된다. 회의 끝나고 녹음 파일 하나 보내면 회의록이 완성된다. 30분씩 정리하던 시간이 0이 됐다.

## 블로그 모드 — 음성에서 이미지 포함 포스트까지 원스톱

"📝 블로그" 버튼을 누르면 기존 `/blog` 파이프라인을 탄다. 여기가 이 시스템의 진짜 강점이다.

1. **나노바나나**(Gemini)로 이미지 3장 자동 생성
2. Claude가 전사 내용을 기반으로 블로그 글을 재구성
3. frontmatter + 이미지가 삽입된 마크다운 파일 생성
4. `draft: true`로 저장 -> `/publish`로 발행

실전 시나리오를 하나 들어본다. 미팅을 다녀와서 걸으면서 음성 녹음을 한다. 텔레그램에 전송한다. 블로그 버튼을 탭한다. 5분 후에 이미지 3장이 포함된 블로그 초안이 완성되어 있다. 이게 실제로 동작한다. 내가 만들어놓고도 매번 놀란다.

![결과 이미지](/images/blog/voice-stt-telegram-4.webp)

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

새로 만든 파일은 `bot/stt.py` 딱 하나다. 나머지는 전부 기존 코드에 핸들러를 추가한 수준이다. 이게 가능한 이유는 처음부터 파이프라인을 모듈화해뒀기 때문이다.

## 코드 변경 요약

| 파일 | 변경 | 설명 |
|------|------|------|
| `bot/stt.py` | **신규** | Gemini STT 모듈 (80줄) |
| `bot/handlers.py` | 추가 | 음성 핸들러 + 콜백 핸들러 (170줄) |
| `bot/main.py` | 추가 | 핸들러 등록 (6줄) |

추가 의존성은 **0개**다. 이미 사용 중인 `google-genai`와 `python-telegram-bot`으로 전부 해결했다. 새 기능을 추가하는데 새 라이브러리가 필요 없다는 건, 기존 아키텍처 선택이 맞았다는 의미이기도 하다.

## 시리즈 진행 상황

1. [AI 비서 소개](/posts/telegram-ai-assistant-intro) ✅
2. [텔레그램 봇 구축](/posts/telegram-bot-setup) ✅
3. [OpenClaw 스타일 메모리](/posts/openclaw-style-memory) ✅
4. [나노바나나 이미지 생성](/posts/nanobanana-image-gen) ✅
5. 음성 → 회의록/블로그 자동 생성 ← **지금 이 글**

---

음성 하나가 완성된 글이 된다. 추가 비용 $0, 추가 의존성 0개. 가장 좋은 자동화란 결국, 중간 과정을 통째로 없애는 것이다.
