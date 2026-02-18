---
title: '나노바나나로 블로그 이미지 자동 생성 — API 비용 $0의 비밀'
description: 'Google Gemini의 나노바나나 이미지 생성을 텔레그램 봇에 연동했다. 무료 API로 블로그 이미지를 자동 생성한다.'
date: 2026-02-07 00:00:00 +0900
tags: ['Gemini', 'AI이미지생성', '텔레그램봇', 'Claude-Code', '자동화', '바이브코딩', '나노바나나']
categories: [tech]
image:
  path: /images/blog/nanobanana-1.webp
  width: 800
  height: 800
author: wonder
twin: nanobanana-image-gen-en
---

## 블로그 이미지, 정말 매번 직접 만들어야 하나?

결론부터 말한다. **Google Gemini의 나노바나나 이미지 생성 API를 쓰면 하루 500장까지 무료**다. 블로그 포스트 하나에 이미지 3장 넣어도 일일 쿼터의 0.6%밖에 안 쓴다. DALL-E처럼 건당 과금? 필요 없다.

나는 텍스트만 있는 블로그가 밋밋하다는 걸 안다. 그렇다고 매번 Canva를 열어서 이미지를 만들고 싶지도 않다. 나는 게으른 개발자다 -- "블로그 써줘" 한 마디에 이미지까지 자동으로 나와야 진짜 자동화 아닌가? 그래서 직접 만들었다.

## 나노바나나 vs DALL-E — 비교하면 답이 나온다

이미지 생성 API를 선택해야 했다. 후보는 두 개였고, 비교표를 만들어보니 고민할 것도 없었다.

| 항목 | 나노바나나 (Gemini Flash) | DALL-E 3 |
|---|---|---|
| **가격** | **무료** (500장/일) | $0.04~$0.12/장 |
| **신용카드** | 불필요 | 필요 |
| **한국어 프롬프트** | 네이티브 지원 | 내부 번역 거침 |
| **블로그용 품질** | 충분 | 좋음 |

**나노바나나**란 Google Gemini에 내장된 이미지 생성 기능이다. API 호출 시 `response_modalities=["IMAGE"]` 파라미터 하나를 추가하면 텍스트 대신 이미지를 반환한다. 이게 전부다.

하루 500장 무료라는 건 사실상 개인 블로거에게 무제한이다. 하루에 블로그 166개를 쓰지 않는 이상. DALL-E에 매번 $0.04~$0.12를 내면서 이미지를 만들 이유가 사라졌다. 선택은 1초면 충분했다.

![개념도](/images/blog/nanobanana-2.webp)

## 구현 — 코드 10분이면 끝나는 구조

### 1. API 키 발급

[Google AI Studio](https://aistudio.google.com/apikey)에서 무료로 발급받는다. 신용카드 등록이 필요 없다. 이게 DALL-E 대비 가장 큰 진입장벽 차이다.

### 2. 이미지 생성 모듈 — 핵심 코드

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

여기서 주목할 포인트가 세 가지 있다:

- **`gemini-2.0-flash-exp` 모델**을 사용한다. 무료 티어에서 이미지 생성이 가능한 모델이다.
- **`response_modalities=["IMAGE"]`**가 핵심 파라미터다. 이 한 줄이 Gemini를 텍스트 모델에서 이미지 생성 모델로 전환시킨다.
- Gemini SDK가 동기(synchronous) API만 제공하기 때문에 **`asyncio.to_thread`로 비동기 래핑**했다. 텔레그램 봇이 비동기 기반이라 이 처리가 필수다.

### 3. 블로그용 이미지 배치 생성

한 포스트에 이미지 3장을 넣는데, 각각 다른 용도로 생성한다.

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

### 4. 텔레그램 봇 연동 — 두 가지 모드

**단독 이미지 생성 (`/image`):**
```
/image 텔레그램 봇과 AI가 대화하는 일러스트
```
이미지 1장을 생성해서 텔레그램에 미리보기로 보여주고, 동시에 블로그 폴더에 저장한다.

**블로그 자동 생성 (`/blog`):**
```
/blog 나노바나나 이미지 생성 연동기
```
이미지 3장 자동 생성 -> Claude가 이미지 경로를 본문에 포함해서 글을 작성 -> 완성된 초안이 한 번에 나온다.

![결과 이미지](/images/blog/nanobanana-3.webp)

## 전체 파이프라인 — 명령어 하나로 끝

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

한 번의 텔레그램 명령으로 **글 + 이미지** 완성. 중간에 사람이 개입하는 단계가 없다. 이게 자동화의 핵심이다 -- 중간 과정을 없애는 것.

## 삽질 기록 — AI Studio에서 Vertex AI로 우회한 이유

위의 코드가 처음부터 깔끔하게 동작한 건 아니다. 실제로는 상당한 삽질이 있었다. 이 과정을 기록해두는 게 누군가에게는 2시간을 아껴줄 수 있다.

### AI Studio API 키의 함정 — quota = 0

처음에 AI Studio에서 무료 API 키를 발급받았다. 문서에는 분명 무료로 이미지 생성이 가능하다고 되어 있었다. 그런데 실제로 호출하면?

```
429 RESOURCE_EXHAUSTED: Quota exceeded for
GenerateContent:imageGeneration
```

`gemini-2.0-flash-exp`, `gemini-2.5-flash-image` 전부 동일한 에러였다. 원인을 파보니 Google이 무료 티어에서 이미지 생성 쿼터를 0으로 설정해둔 것이다. 문서와 실제 동작이 다른 전형적인 케이스다.

### Vertex AI로 전환 — 같은 모델, 다른 인프라

해결책은 [Google Cloud Vertex AI](https://console.cloud.google.com/vertex-ai/studio)였다. 동일한 Gemini 모델이지만 GCP 프로젝트 단위로 과금되는 구조라서 쿼터 제한이 없다.

전환 과정은 의외로 간단했다:

```bash
# 1. GCP 프로젝트에서 Vertex AI API 활성화
# 2. Application Default Credentials 설정
gcloud auth application-default login

# 3. 브라우저에서 Google 계정 인증 → 완료
```

코드 변경은 정확히 한 줄이다:

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

`vertexai=True` 파라미터 하나를 추가한 것이 전부다. 모델명도 동일하다. 이후 즉시 동작했다. 삽질 2시간, 해결 2분. 개발이란 대체로 이렇다.

### 3단계 폴백 전략 — 서비스는 멈추면 안 된다

최종적으로 설계한 폴백 구조다:

```
1순위: Vertex AI (ADC 인증) → 안정적, 과금 기반
2순위: AI Studio (API 키) → 무료지만 quota 제한 가능성
3순위: SVG 플레이스홀더 → 최후의 수단
```

어떤 상황에서든 블로그 생성 파이프라인은 멈추지 않는다. 이미지가 생성 안 되면 SVG 플레이스홀더로 자리라도 잡아둔다. 완벽주의보다 완성이 중요하다 -- 이건 프로덕션 환경에서 배운 철학이다.

## 비용 분석 — 직접 만들면 추가 비용 $0

| 항목 | 월간 비용 |
|---|---|
| Claude Code Max | 이미 구독 중 |
| 나노바나나 이미지 | **$0** (무료 500장/일) |
| Telegram Bot API | **$0** |
| GitHub Pages 호스팅 | **$0** |
| **합계** | **추가 비용 $0** |

외부 블로그 이미지 서비스를 쓰면 월 $20 이상 든다. 직접 만들면 $0. 물론 구현에 시간이 들었지만, 한번 만들어두면 이후 수백 장의 이미지를 무료로 생성할 수 있다. ROI(투자 대비 수익률)로 따지면 압도적이다.

## 시리즈 진행 상황

1. [AI 비서 소개](/posts/telegram-ai-assistant-intro) ✅
2. [텔레그램 봇 구축](/posts/telegram-bot-setup) ✅
3. [OpenClaw 스타일 메모리](/posts/openclaw-style-memory) ✅
4. 나노바나나 이미지 생성 ← **지금 이 글**
5. 예약 발행 + 전체 자동화 파이프라인 (다음 편)

텔레그램에서 한 줄 치면 이미지 포함된 블로그 포스트가 자동으로 나온다. 전체 파이프라인의 마지막 퍼즐 조각이 거의 맞춰지고 있다.

---

자동화의 끝은 없다. 하지만 이미지 생성만큼은, 더 이상 손댈 게 없을 만큼 완성됐다.
