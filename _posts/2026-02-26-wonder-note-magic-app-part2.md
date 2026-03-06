---
title: "68MB에서 4.55MB로 — WonderNote 개발기 2부"
description: "번들 사이즈 93% 다이어트, TypeScript strict 모드 전환, 그리고 인앱결제와 OCR까지. 마술앱이 프리미엄 제품이 되기까지."
date: 2026-02-26 14:00:00 +0900
image:
  path: /images/blog/wonder-note-part2-1.webp
  width: 1280
  height: 720
tags: ['React Native', 'Expo', '번들최적화', 'TypeScript', 'IAP', 'OCR', '사이드프로젝트']
categories: [side-project]
author: wonder
---

MVP를 들고 마술을 해봤다. 작동은 했다. 하지만 두 가지가 마음에 걸렸다.

첫째, **앱 크기가 68MB였다.** 메모앱을 위장하는 앱이 68MB라니. iOS 기본 메모앱은 몇 MB나 될까. 관객이 앱스토어에서 다운받을 때 "메모앱이 왜 이렇게 커?"라고 생각할 수 있다.

둘째, **코드가 엉망이었다.** TypeScript인데 `any`가 130개 넘게 있었다. Claude Code가 빠르게 짠 대가였다. 동작은 하지만, 새 기능을 추가하려면 어디서 터질지 모르는 지뢰밭이었다.

1부에서 만든 MVP를 제품으로 만드는 작업이 시작됐다.

---

## 68MB → 4.55MB: 번들 다이어트

![번들 사이즈 93% 감소 — 68MB에서 4.55MB로](/images/blog/wonder-note-part2-2.webp)

68MB의 원인을 추적했다. 범인은 의외로 단순했다. **쓰지도 않는 패키지들이 13개나 설치되어 있었다.**

Expo 프로젝트를 초기화하면 기본 템플릿에 이것저것 포함된다. 탭 네비게이션, 웹 지원, Tailwind CSS 같은 것들. WonderNote에는 하나도 필요 없는 것들이었다.

제거한 패키지 목록:

```
- nativewind (4.2.1)        → Tailwind CSS 바인딩, 한 줄도 안 씀
- tailwindcss (3.4.19)       → 위에 딸려온 놈
- expo-av                    → 오디오/비디오, 필요 없음
- expo-haptics               → 진동인데 Vibration API로 대체 가능
- react-native-device-info   → 디바이스 정보, 안 씀
- react-native-web           → 웹 지원, 필요 없음
- react-dom                  → 웹 렌더러, 같이 제거
- @react-navigation/bottom-tabs → 탭 네비게이션, 안 씀
- @react-navigation/elements → 위에 딸려온 놈
- expo-symbols               → SF Symbols, lucide로 대체
- @expo/vector-icons         → 아이콘, lucide로 통일
- expo-web-browser           → 웹 브라우저, 안 씀
```

13개 패키지를 삭제하고, Expo 템플릿에서 남은 14개의 미사용 컴포넌트도 정리했다. `hello-wave.tsx`, `parallax-scroll-view.tsx`, `themed-text.tsx` 같은 기본 템플릿 잔존물들.

결과:

| 항목 | Before | After | 감소율 |
|------|--------|-------|--------|
| 번들 크기 | 68MB | 4.55MB | **93.3%** |
| 모듈 수 | - | 2,773개 | - |
| 미사용 패키지 | 13개 | 0개 | 100% |
| 미사용 컴포넌트 | 14개 | 0개 | 100% |

**93% 감소.** 4.55MB면 진짜 메모앱 수준이다. 위장에 한 발 더 가까워졌다.

---

## TypeScript Strict 모드: any 130개 전멸

MVP에서는 속도가 우선이라 TypeScript를 느슨하게 썼다. `any`가 130개 넘게 있었다. 이걸 하나씩 잡기 시작했다.

주요 타입 정의를 `types/index.ts`에 중앙화했다:

```typescript
export interface PathData {
    d: string;
    color: string;
    width: number;
    tool: 'pen' | 'eraser';
}

export interface HistoryEntry {
    id: string;
    imageUri: string;
    timestamp: number;
    svgPaths: PathData[];
}

export type PremiumTier = 'free' | 'standard' | 'pro';
```

AsyncStorage 키도 상수로 중앙화했다. 문자열 키를 직접 쓰면 오타 한 번으로 데이터가 증발한다:

```typescript
export const STORAGE_KEYS = {
    HISTORY: 'wonder_history',
    SETTINGS: 'wonder_settings',
    PREMIUM_TIER: 'premium_tier',
    ONBOARDING_DONE: 'onboarding_done',
    // ...
};
```

strict 모드 전환 후 컴파일 에러 0개를 확인했다. 130개 넘는 `any`를 모두 명시적 타입으로 교체하는 데 걸린 시간? Claude Code 도움으로 약 2시간.

---

## V1.1: 공연에서 발견한 치명적 버그 수정

1부에서 언급한 **삭제 확인 대화상자** 문제. iOS Notes는 메모를 삭제할 때 항상 "메모를 삭제하시겠습니까?"를 물어본다. 내 앱은 바로 삭제됐다. 이건 위장의 관점에서 치명적이다.

수정한 플로우:

```
[Before] 쓰레기통 탭 → 즉시 삭제 + 캡처
[After]  쓰레기통 탭 → 캡처 → "삭제하시겠습니까?" 대화상자 → 삭제
```

캡처 타이밍이 중요하다. 대화상자가 뜨면 캔버스 위에 Alert가 덮이기 때문에, **대화상자를 띄우기 전에 캡처해야 한다.** 취소를 누르면? 캡처한 이미지를 조용히 삭제한다.

V1.1에서 고친 것들을 정리하면:

| 수정 사항 | 위험도 | 소요 시간 |
|----------|--------|----------|
| 삭제 확인 대화상자 | CRITICAL | 4시간 |
| 캡처 타이밍 순서 수정 | HIGH | 2시간 |
| i18n 런타임 반영 버그 | MEDIUM | 1시간 |
| 히스토리 50개 제한 (메모리 관리) | MEDIUM | 1시간 |
| SVG 렌더러 컴포넌트 분리 (DRY) | LOW | 2시간 |

---

![인앱결제 3-Tier 구조](/images/blog/wonder-note-part2-3.webp)

## Premium 모델: 무료 마술사 vs 프로 마술사

앱이 안정되자 수익화를 고민했다. 마술앱의 특성상 **무료로 기본 트릭을 제공하고, 고급 기능은 유료**로 가는 게 자연스럽다.

3개 상품으로 구성했다:

| 상품 | ID | 포지션 |
|------|-----|--------|
| Standard | `com.wondernote.standard` | 기본 프리미엄 (OCR, 확장 히스토리) |
| Pro Full | `com.wondernote.pro_full` | 풀 패키지 (Watch + 모든 기능) |
| Upgrade to Pro | `com.wondernote.upgrade_to_pro` | Standard → Pro 업그레이드 |

`react-native-iap`을 적용했는데, 이게 간단하지 않았다. v12에서 v14로 올리면서 API가 완전히 바뀌었다. `purchaseUpdatedListener`, `finishTransaction` 같은 핵심 API의 시그니처가 달라져서 마이그레이션에만 하루를 썼다.

무료 사용자의 제한:

```typescript
const FREE_PEEK_LIMIT = 5;       // Peek 5회
const FREE_HISTORY_LIMIT = 3;     // 히스토리 3개
const HISTORY_EXPIRY_MS = 24 * 60 * 60 * 1000;  // 24시간 후 만료
```

이 정도면 공연 1~2회는 무료로 할 수 있다. 진지하게 마술을 하는 사람이라면 자연스럽게 프리미엄으로 넘어올 거라는 계산이다.

---

## OCR: 숫자를 읽는 마술

Premium 기능 중 하나로 **숫자 인식(OCR)**을 넣었다. 관객이 숫자를 쓰면 AI가 인식해서 마술사에게 알려주는 트릭이다.

TFLite MNIST 모델을 사용했다:

```typescript
// 28x28 그레이스케일 이미지 → 0~9 분류
const output = await model.run([input]);
const predictions = output[0]; // [10] 확률 배열

// 신뢰도 80% 이상만 인식 성공
if (maxConf >= CONFIDENCE_THRESHOLD) {
    return { digit: maxIdx.toString(), confidence: maxConf, success: true };
}
```

`react-native-fast-tflite`로 모델을 로드하고, 캡처한 이미지를 28x28로 리사이즈해서 추론한다. 신뢰도 80% 이상이면 성공.

다만 V2.0 출시 시점에서 OCR은 **비활성화** 상태로 출시했다. 이미지 전처리 파이프라인(리사이즈 + 그레이스케일 변환)이 아직 불안정했기 때문이다. 코드는 다 있지만 실전에서 쓰기엔 이르다는 판단이었다.

```typescript
// OCR disabled for v2.1 launch (planned for v2.2)
// import { recognizeDigit, loadOcrModel } from '../services/ocr';
const loadOcrModel = () => {};
```

미완성 기능을 주석 처리하고 출시하는 게 맞다. **작동하지 않는 기능을 켜두는 것보다 없는 게 낫다.**

---

## 2부를 마치며: 제품이 되는 순간

![MVP에서 제품으로](/images/blog/wonder-note-part2-4.webp)

V1.0에서 V2.0까지의 변경량:

```
57 files changed, 9,100 insertions(+), 2,214 deletions(-)
```

MVP의 2.7배가 넘는 코드가 추가됐다. 하지만 체감상 가장 큰 변화는 코드량이 아니라 **"이걸 진짜 출시할 수 있겠다"는 확신**이었다.

68MB짜리 프로토타입은 친구 앞에서만 쓸 수 있었다. 4.55MB짜리 제품은 앱스토어에 올려도 부끄럽지 않았다.

다음 편에서는 WonderNote의 궁극적 Peek 수단 — **Apple Watch 연동**과 그 과정에서 만난 삽질의 기록을 다룬다.

> 📌 **WonderNote 개발기 시리즈**
> - [1부: iOS 메모앱으로 위장한 마술앱을 만들었다](/posts/wonder-note-magic-app-part1/)
> - **2부: 68MB에서 4.55MB로** ← 지금 읽는 글
> - [3부: 애플 워치에 마술을 올리기까지](/posts/wonder-note-magic-app-part3/)
