---
title: '나노바나나로 블로그 이미지 자동 생성 — API 비용 $0의 비밀'
description: 'Google Gemini의 나노바나나 이미지 생성을 텔레그램 봇에 연동했다. 무료 API로 블로그 이미지를 자동 생성한다.'
date: 2026-02-07 00:00:00 +0900
tags: ['nanobanana', 'gemini', 'image-generation', 'telegram', 'claude-code', 'automation', 'vibe-coding']
categories: [ai-automation]
image:
  path: /images/blog/nanobanana-1.webp
  width: 800
  height: 800
author: wonder
---

## 이미지 만들기 귀찮다

텍스트만 있는 블로그는 밋밋하다. 그건 안다.
근데 매번 Canva 열어서 이미지 만드는 건 더 싫다.

나는 게으른 개발자다. "블로그 써줘" 한 마디에 이미지까지 자동으로 나오면 좋겠다.
그래서 만들었다.

## 나노바나나 vs DALL-E

이미지 생성 API를 골라야 했다. 후보는 두 개.

| 항목 | 나노바나나 (Gemini Flash) | DALL-E 3 |
|---|---|---|
| **가격** | **무료** (500장/일) | $0.04~$0.12/장 |
| **신용카드** | 불필요 | 필요 |
| **한국어** | 네이티브 지원 | 내부 번역 |
| **품질** | 블로그용 충분 | 좋음 |

**나노바나나 = Google Gemini의 이미지 생성 기능**이다. `response_modalities=["IMAGE"]`를 주면 이미지를 뱉는다.

하루 500장 무료. 블로그에 3장 넣으면 0.6% 사용. 사실상 무제한이다.
DALL-E한테 매번 돈 내가며 이미지 만들 이유가 없었다. 선택은 1초 만에 끝났다.

![개념도](/images/blog/nanobanana-2.webp)

## 구현: 10분이면 끝난다

### 1. API 키 발급

[Google AI Studio](https://aistudio.google.com/apikey)에서 무료로 발급. 신용카드 필요 없다. 이게 핵심이다.

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

포인트는 세 가지다:
- `gemini-2.0-flash-exp` 모델 사용. 무료 티어.
- `response_modalities=["IMAGE"]`가 마법의 주문이다. 이거 하나로 이미지 생성 모드가 켜진다.
- Gemini SDK는 동기 API라 `asyncio.to_thread`로 비동기 래핑했다.

### 3. 블로그용 이미지 배치 생성

한 포스트에 이미지 3장. 각각 다른 느낌으로 만든다.

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
        result = await generate_image(prompt, filename=f"{slug}-{i+1}.jpg")
        results.append(result)
    return results
```

### 4. 텔레그램 봇 연동

두 가지 방식이다.

**단독 이미지 생성 (`/image`):**
```
/image 텔레그램 봇과 AI가 대화하는 일러스트
```
→ 이미지 1장 생성, 텔레그램에 미리보기, 블로그 폴더에 저장.

**블로그 자동 생성 (`/blog`):**
```
/blog 나노바나나 이미지 생성 연동기
```
→ 이미지 3장 자동 생성 → Claude가 본문에 이미지 경로 포함 → 완성된 초안 한 방에 생성.

![결과 이미지](/images/blog/nanobanana-3.webp)

## 전체 흐름

```
텔레그램: /blog 주제
  │
  ├→ 나노바나나: 이미지 3장 생성 (무료)
  │   ├→ hero.jpg (히어로)
  │   ├→ concept.jpg (개념도)
  │   └→ result.jpg (결과)
  │
  ├→ Claude Code: 본문 작성 (이미지 경로 포함)
  │
  └→ 결과: draft 포스트 + 이미지 완성
       └→ /publish → git push → 배포
```

한 번의 명령으로 **글 + 이미지** 완성. 이게 자동화다. 진짜 자동화.

## 삽질기: AI Studio에서 Vertex AI로

위의 코드가 처음부터 깔끔하게 된 건 아니다. 삽질이 있었다. 솔직히 꽤 오래 걸렸다.

### AI Studio API 키가 막혀 있었다

처음엔 AI Studio에서 무료 API 키를 발급받았다. 그런데 이미지 생성 모델들이 전부 **quota = 0**이었다.

```
429 RESOURCE_EXHAUSTED: Quota exceeded for
GenerateContent:imageGeneration
```

`gemini-2.0-flash-exp`, `gemini-2.5-flash-image` 다 시도했다. 전부 같은 에러. Google이 무료 티어에서 이미지 생성을 제한한 거다.

무료라며? 사기 아닌가 싶었다.

### Vertex AI가 답이었다

해결책은 [Google Cloud Vertex AI](https://console.cloud.google.com/vertex-ai/studio)였다. 같은 Gemini 모델인데 GCP 프로젝트 단위로 과금되는 구조라 quota 제한이 없다.

전환은 쉬웠다:

```bash
# 1. GCP 프로젝트에서 Vertex AI API 활성화
# 2. Application Default Credentials 설정
gcloud auth application-default login

# 3. 브라우저에서 Google 계정 인증 → 완료
```

코드 변경은 딱 한 줄:

```python
# Before: AI Studio (API 키)
client = genai.Client(api_key=GEMINI_API_KEY)

# After: Vertex AI (ADC)
client = genai.Client(
    vertexai=True,
    project="my-project-id",
    location="us-central1"
)
```

`vertexai=True` 하나 추가한 거다. 모델명도 그대로. 이후 바로 동작했다.
삽질 2시간, 해결 2분. 늘 이렇다.

### 3단계 폴백 전략

최종 구조는 이렇다:

```
1순위: Vertex AI (ADC 인증) → 안정적, 과금 기반
2순위: AI Studio (API 키) → 무료지만 quota 제한
3순위: SVG 플레이스홀더 → 최후의 수단
```

뭐가 됐든 블로그 생성은 멈추지 않는다. 이미지가 안 만들어지면 SVG로 자리라도 잡아둔다. 완벽주의보다 완성이 중요하다.

## 비용 정리

| 항목 | 월간 비용 |
|---|---|
| Claude Code Max | 이미 구독 중 |
| 나노바나나 이미지 | **$0** (무료 500장/일) |
| Telegram Bot API | **$0** |
| GitHub Pages 호스팅 | **$0** |
| **합계** | **추가 비용 $0** |

OpenClaw 같은 서비스 쓰면 월 $20+ 든다. 직접 만들면 $0.
이 차이가 내가 직접 만드는 이유다.

## 시리즈 진행 상황

1. [AI 비서 소개](/posts/telegram-ai-assistant-intro) ✅
2. [텔레그램 봇 구축](/posts/telegram-bot-setup) ✅
3. [OpenClaw 스타일 메모리](/posts/openclaw-style-memory) ✅
4. 나노바나나 이미지 생성 ← **지금 이 글**
5. 예약 발행 + 전체 자동화 파이프라인 (다음 편)

텔레그램에서 한 줄 치면 이미지 포함된 블로그가 자동으로 나온다. 거의 완성이다.

---

자동화의 끝은 없다. 근데 그게 재밌다.
