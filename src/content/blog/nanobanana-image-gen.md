---
title: '나노바나나로 블로그 이미지 자동 생성 — API 비용 $0의 비밀'
description: 'Google Gemini의 나노바나나 이미지 생성을 텔레그램 봇에 연동했다. 무료 API로 블로그 포스트마다 이미지 3장을 자동 생성한다.'
pubDate: '2026-02-07'
tags: ['nanobanana', 'gemini', 'image-generation', 'telegram', 'claude-code', 'automation', 'vibe-coding']
category: 'ai-automation'
draft: false
---

## 블로그에 이미지가 필요하다

텍스트만 있는 블로그는 밋밋하다. 근데 매번 Canva 열어서 이미지 만드는 건 귀찮다.

개발자는 게을러야 한다. **"블로그 써줘"** 한 마디에 이미지까지 자동으로 생성되면 얼마나 좋을까.

## 나노바나나 vs ChatGPT(DALL-E)

이미지 생성 API를 골라야 한다. 후보는 두 개:

| 항목 | 나노바나나 (Gemini Flash) | DALL-E 3 |
|---|---|---|
| **가격** | **무료** (500장/일) | $0.04~$0.12/장 |
| **신용카드** | 불필요 | 필요 |
| **한국어** | 네이티브 지원 | 내부 번역 |
| **품질** | 블로그용 충분 | 좋음 |

**나노바나나 = Google Gemini의 이미지 생성 기능**이다. Gemini 2.0 Flash 모델에 `response_modalities=["IMAGE"]`를 주면 이미지를 생성한다.

핵심은 **무료 500장/일**. 블로그에 3장 넣으면 0.6% 사용이다. 사실상 무제한.

## 구현: 10분 만에 끝나는 연동

### 1. API 키 발급

[Google AI Studio](https://aistudio.google.com/apikey)에서 무료로 발급. 신용카드 불필요.

### 2. 이미지 생성 모듈

```python
# bot/image_gen.py — 핵심 부분만
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

    # 이미지 추출 → 파일 저장
    for part in response.candidates[0].content.parts:
        if part.inline_data:
            save_path.write_bytes(part.inline_data.data)

    return {"path": str(save_path), "blog_path": f"/images/blog/{filename}"}
```

**포인트:**
- `gemini-2.0-flash-exp` 모델 사용 (무료 티어)
- `response_modalities=["IMAGE"]`가 핵심 — 이걸로 이미지 생성 모드 활성화
- Gemini SDK는 동기 API라 `asyncio.to_thread`로 비동기 래핑

### 3. 블로그용 이미지 배치 생성

한 포스트에 이미지 3장이 필요하다. 각각 다른 스타일로:

```python
async def generate_blog_images(topic: str, count: int = 3) -> list:
    prompts = [
        # 1. 히어로: 다크 배경, 추상적
        f"Hero illustration about: {topic}. Dark background, vibrant accents.",
        # 2. 개념도: 밝은 배경, 구조
        f"Conceptual diagram about: {topic}. Isometric view, connections.",
        # 3. 결과물: 개발자 워크스페이스
        f"Developer workspace showing: {topic}. Multiple screens, cozy.",
    ]

    results = []
    for i, prompt in enumerate(prompts):
        result = await generate_image(prompt, filename=f"{slug}-{i+1}.png")
        results.append(result)
    return results
```

### 4. 텔레그램 봇 연동

두 가지 방식으로 사용 가능:

**단독 이미지 생성 (`/image`):**
```
/image 텔레그램 봇과 AI가 대화하는 일러스트
```
→ 이미지 1장 생성, 텔레그램에 미리보기 전송, 블로그 이미지 폴더에 저장.

**블로그 자동 생성 (`/blog`):**
```
/blog 나노바나나 이미지 생성 연동기
```
→ 이미지 3장 자동 생성 → Claude가 본문 작성할 때 이미지 경로 포함 → 완성된 초안 한 번에 생성.

## 흐름 정리

```
텔레그램: /blog 주제
  │
  ├→ 나노바나나: 이미지 3장 생성 (무료)
  │   ├→ hero.png (히어로)
  │   ├→ concept.png (개념도)
  │   └→ result.png (결과)
  │
  ├→ Claude Code: 본문 작성 (이미지 경로 포함)
  │
  └→ 결과: draft 포스트 + 이미지 완성
       └→ /publish → git push → 배포
```

한 번의 명령으로 **글 + 이미지** 완성. 진짜 게으른 블로깅이다.

## 비용 정리

| 항목 | 월간 비용 |
|---|---|
| Claude Code Max | 이미 구독 중 |
| 나노바나나 이미지 | **$0** (무료 500장/일) |
| Telegram Bot API | **$0** |
| GitHub Pages 호스팅 | **$0** |
| **합계** | **추가 비용 $0** |

OpenClaw 같은 서비스 쓰면 월 $20+인데, 직접 만들면 $0이다.

## 다음 편 예고

시리즈가 꽤 쌓였다:

1. [AI 비서 소개](/blog/telegram-ai-assistant-intro) ✅
2. [텔레그램 봇 구축](/blog/telegram-bot-setup) ✅
3. [OpenClaw 스타일 메모리](/blog/openclaw-style-memory) ✅
4. 나노바나나 이미지 생성 ← **지금 이 글**
5. 예약 발행 + 전체 자동화 파이프라인 (다음 편)

텔레그램에서 한 줄 치면 이미지 포함된 블로그가 자동으로 발행되는 시스템. 거의 완성이다.
