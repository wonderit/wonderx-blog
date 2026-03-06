---
title: "M3 Mac에서 FLUX 돌려서 이미지 생성 비용을 0원으로 만들었다"
description: "stable-diffusion-cpp는 CPU만 쓰고 10분 걸렸다. mflux로 갈아타니 58초. 텔레그램 봇에 붙여서 Gemini API 비용을 완전히 없앴다."
date: 2026-03-01 10:00:00 +0900
image:
  path: /images/blog/flux-local-m3-1.webp
  width: 1280
  height: 720
tags: ['FLUX', 'mflux', 'Apple Silicon', 'MLX', '이미지생성', '비용최적화', '텔레그램봇']
categories: [dev-log]
author: wonder
---

블로그 이미지 하나 생성하는 데 Gemini API로 $0.02~$0.134가 든다. 포스트 하나에 이미지 4장이면 최대 $0.54. 한 달에 20편 쓰면 $10.8.

별거 아닌 것 같지만, 로컬에서 공짜로 돌릴 수 있는데 굳이 돈을 낼 이유가 있을까?

M3 Pro 36GB MacBook이 있다. FLUX.1 schnell이면 충분히 돌아갈 스펙이다. 해보자.

---

## 첫 번째 시도: stable-diffusion-cpp — 10분짜리 재앙

![stable-diffusion-cpp가 CPU만 사용하는 문제](/images/blog/flux-local-m3-2.webp)

처음 시도한 건 `stable-diffusion-cpp-python`이다. FLUX GGUF 모델을 지원하고, Python 바인딩이 있어서 기존 봇 코드에 바로 붙일 수 있을 것 같았다.

모델을 다운받았다. `flux1-schnell-Q4_0.gguf` — 4비트 양자화로 약 6GB.

```python
from stable_diffusion_cpp import StableDiffusion

sd = StableDiffusion(
    diffusion_model_path="flux1-schnell-Q4_0.gguf",
    clip_l_path="clip_l.safetensors",
    t5xxl_path="t5xxl_fp16.safetensors",
    vae_path="ae.safetensors",
)
output = sd.txt_to_img(prompt="a cat sitting on a desk", width=1024, height=576)
```

코드는 깔끔했다. 문제는 **실행 시간**이었다.

```
1024x576, 4 steps → 567초 (9분 27초)
```

**거의 10분.** 블로그 이미지 하나에 10분이면 4장에 40분이다. Gemini API는 5초면 끝나는 걸.

왜 이렇게 느릴까. Activity Monitor를 열어봤다. **CPU 사용률 800%, GPU 사용률 0%.** Metal.framework이 링크돼 있긴 한데, 실제 연산은 전부 CPU에서 돌고 있었다.

`stable-diffusion-cpp`의 Metal 지원이 FLUX 모델에서는 제대로 작동하지 않는 것이다. 이건 아무리 최적화해도 답이 없다.

---

## mflux를 발견하다

방향을 틀었다. Apple Silicon에서 GPU를 제대로 쓰는 방법이 필요했다.

찾은 게 **mflux**다. Apple의 MLX 프레임워크 위에서 돌아가는 FLUX 전용 추론 엔진이다.

MLX가 핵심이다. Apple이 직접 만든 머신러닝 프레임워크로, Metal GPU를 네이티브로 활용한다. PyTorch의 MPS 백엔드보다 훨씬 효율적이고, Apple Silicon의 Unified Memory를 최대한 활용하도록 설계됐다.

```bash
pip install mflux
```

설치는 한 줄이다. 모델은? HuggingFace에서 자동으로 다운받는다. 단, `black-forest-labs/FLUX.1-schnell`이 **gated repo**라서 HuggingFace 토큰으로 access 승인을 받아야 한다.

```bash
huggingface-cli login
# 토큰 입력 후
mflux-generate --model schnell --prompt "a cat on a desk" --width 1024 --height 576 --steps 4 --quantize 4
```

결과:

```
1024x576, 4 steps, Q4 → 57.4초
```

**10배 빨라졌다.** 567초에서 57초로. CPU 대신 GPU를 제대로 쓰니까 이런 차이가 난다.

---

## 벤치마크: 어디까지 빨라지나

![mflux 벤치마크 결과 — 해상도별 생성 시간](/images/blog/flux-local-m3-3.webp)

M3 Pro 36GB에서 mflux의 성능을 체계적으로 측정했다. 모든 테스트는 4비트 양자화(`--quantize 4`).

| 해상도 | Steps | 시간 | 파일 크기 | 용도 |
|--------|:-----:|-----:|----------:|------|
| 256x256 | 2 | **11.9초** | ~50KB | 테스트/썸네일 |
| 1024x576 | 2 | **33.7초** | ~400KB | 빠른 초안 |
| 1024x576 | 4 | **57.4초** | ~544KB | 히어로 이미지 (16:9) |
| 1024x680 | 4 | **~66초** | ~600KB | 본문 이미지 (3:2) |

FLUX.1 schnell은 "schnell"(독일어로 "빠른")이라는 이름답게 2~4 steps면 충분하다. 일반적인 Stable Diffusion이 20~50 steps 필요한 것과 비교하면 압도적으로 적은 step 수다.

4 steps면 블로그 이미지로 충분한 품질이 나온다. 2 steps도 쓸 만하지만, 디테일이 조금 부족할 때가 있다.

### Gemini API와 비교

| 항목 | mflux 로컬 | Imagen Fast | Gemini 3 Pro |
|------|:----------:|:-----------:|:------------:|
| 시간/장 | ~58초 | ~5초 | ~8초 |
| 비용/장 | **$0** | $0.02 | $0.134 |
| 4장 비용 | **$0** | $0.08 | $0.536 |
| 월 80장 | **$0** | $1.60 | $10.72 |
| 품질 | A | B+ | A- |

속도는 Gemini API가 압도적이다. 하지만 비용이 0이라는 게 결정적이다. 블로그 이미지는 실시간으로 필요한 게 아니다. 글을 쓰는 동안 백그라운드에서 4장 생성하면 되니까, 58초x4 = 4분 정도는 충분히 기다릴 수 있다.

그리고 **품질이 더 좋다.** FLUX.1은 텍스트 렌더링, 복잡한 구도, 사실적인 조명에서 Imagen보다 일관되게 나은 결과를 보여준다.

---

## 텔레그램 봇에 통합하기

로컬에서 돌아가는 걸 확인했으니, 기존 텔레그램 봇의 이미지 파이프라인에 붙여야 한다.

아키텍처는 간단하다:

```
요청 → mflux 로컬 시도 → 성공 → WebP 변환 → 반환
                        → 실패/타임아웃 → Gemini API 폴백
```

핵심은 **비동기 서브프로세스**로 mflux CLI를 호출하는 것이다. mflux가 Python 라이브러리가 아니라 CLI 도구이기 때문에, `asyncio.create_subprocess_exec`로 감싸야 한다.

```python
MFLUX_BIN = Path.home() / "anaconda3/envs/wonderx-bot/bin/mflux-generate"
MFLUX_TIMEOUT = 90  # 초

async def _try_flux_local(prompt, width=1024, height=576):
    output_path = Path(tempfile.mktemp(suffix=".png"))
    cmd = [
        str(MFLUX_BIN),
        "--model", "schnell",
        "--prompt", prompt,
        "--width", str(width),
        "--height", str(height),
        "--steps", "4",
        "--quantize", "4",
        "--output", str(output_path),
    ]
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await asyncio.wait_for(proc.wait(), timeout=MFLUX_TIMEOUT)
        if proc.returncode == 0 and output_path.exists():
            return output_path.read_bytes()
    except asyncio.TimeoutError:
        proc.kill()
        return None
    finally:
        output_path.unlink(missing_ok=True)
    return None
```

타임아웃이 중요하다. mflux가 간혹 모델 로딩에서 멈추거나, 메모리 부족으로 느려질 수 있다. 90초면 1024x680 4steps 기준으로 충분한 여유다. 타임아웃이 걸리면 프로세스를 kill하고 Gemini API로 폴백한다.

### 자동 감지

```python
USE_LOCAL_FLUX = MFLUX_BIN.exists()
```

mflux 바이너리가 있으면 자동으로 로컬 생성을 시도한다. conda 환경이 없는 다른 머신에서는 자동으로 Gemini API만 사용한다. 설정 파일 수정 없이 환경에 맞게 동작하는 구조다.

---

## 삽질 기록: 넘어야 했던 장애물들

![삽질의 여정 — stable-diffusion-cpp에서 mflux까지](/images/blog/flux-local-m3-4.webp)

순탄하지 않았다. 시간순으로 정리하면:

### 1. stable-diffusion-cpp의 Metal 함정

`otool -L`로 확인하면 Metal.framework이 링크돼 있다. 그래서 "GPU 쓰겠지"라고 생각했는데, FLUX 모델에서는 실제로 Metal compute를 사용하지 않았다. 라이브러리가 Metal을 "지원한다"와 특정 모델에서 "실제로 사용한다"는 다른 이야기다.

### 2. HuggingFace Gated Repo 403

mflux를 처음 실행하면 모델을 HuggingFace에서 다운받는다. 그런데 FLUX.1 schnell은 gated repo라서, HuggingFace 계정으로 로그인하고 access를 신청해야 한다. 승인은 즉시 되지만, 토큰 없이 실행하면 403 에러가 나온다.

```bash
# 이렇게 하면 403
mflux-generate --model schnell --prompt "test"

# 먼저 로그인해야 함
huggingface-cli login
# 그 다음 실행하면 모델 다운로드 시작
```

### 3. 최초 실행 시 모델 다운로드 시간

schnell 모델(4비트 양자화)의 첫 다운로드에 약 10분이 걸린다. 이후에는 캐시돼서 즉시 로드된다. 첫 실행이 느리다고 당황하지 말 것.

### 4. 해상도 제약

mflux는 width와 height가 각각 **64의 배수**여야 한다. 1280x720처럼 Gemini API에서 쓰던 크기를 그대로 넣으면 에러가 난다. 1024x576(16:9)이나 1024x680(3:2 근사)으로 맞춰야 한다.

---

## 비용 시뮬레이션: 연간 절감 효과

내 블로그 기준으로 계산해보자.

| 항목 | 수치 |
|------|-----:|
| 월 포스트 수 | ~20편 |
| 포스트당 이미지 | 4장 |
| 월 이미지 수 | 80장 |
| 연 이미지 수 | 960장 |

| 시나리오 | 이미지당 비용 | 월 비용 | 연 비용 |
|---------|:-----------:|-------:|-------:|
| Gemini 3 Pro만 | $0.134 | $10.72 | **$128.64** |
| Imagen Fast만 | $0.02 | $1.60 | **$19.20** |
| mflux 로컬 | $0 | $0 | **$0** |
| mflux + Gemini 폴백 (10%) | ~$0.002 | ~$0.16 | **~$1.92** |

mflux 로컬을 1순위로 쓰고, 실패 시에만 Gemini API로 폴백하면 연간 비용이 $2 미만이다. 전기세를 고려해도 무시할 수 있는 수준이다.

물론 이건 M3 Pro가 있으니까 가능한 이야기다. Apple Silicon Mac이 없으면 Gemini API가 여전히 최선이다.

---

## 최종 아키텍처

정리하면 현재 이미지 생성 파이프라인은 이렇다:

```
[텔레그램 /image 또는 /blog 명령]
        ↓
[프롬프트 → Gemini AI 영어 프롬프트로 변환]
        ↓
[mflux 로컬 생성 시도]
   ├─ 성공 → PNG → WebP 변환 (quality=85) → 완료
   └─ 실패/타임아웃(90초) → Gemini API 폴백
        ├─ Imagen 4.0 Fast ($0.02)
        ├─ Gemini 3 Pro Image ($0.134)
        └─ ... (체인 폴백)
```

mflux 바이너리가 있으면 자동으로 1순위, 없으면 Gemini API만 사용. 어떤 이미지가 Gemini API로 생성됐는지 명시적으로 보고해서, 나중에 FLUX로 재생성할 수 있게 했다.

---

## 마치며

**stable-diffusion-cpp에서 mflux로 갈아탄 게 핵심이다.** 같은 FLUX.1 schnell 모델인데, 추론 엔진이 다르니까 567초가 57초로 줄었다. Metal GPU를 제대로 쓰느냐 마느냐의 차이다.

M3 Pro 36GB면 1024x576 이미지 하나에 약 1분. 블로그 포스트 하나 쓰는 동안 이미지 4장이 백그라운드에서 완성된다. API 비용은 0원.

로컬 AI가 실용적인 수준에 올라왔다는 걸 체감한 작업이었다. 2년 전에는 "로컬에서 이미지 생성? 클라우드 API 쓰세요"가 정답이었다. 지금은 Apple Silicon 하나면 충분하다.

> 📌 관련 글: [AI 이미지 생성 비용을 6.7배 줄인 방법](/posts/gemini-image-cost-optimization/) — Gemini API 내에서의 비용 최적화. 이번 글은 API 자체를 없앤 이야기다.
