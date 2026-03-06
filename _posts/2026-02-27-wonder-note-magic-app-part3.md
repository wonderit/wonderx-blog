---
title: "애플 워치에 마술을 올리기까지 — WonderNote 개발기 3부"
description: "손목 위에서 관객의 그림을 몰래 확인한다. Apple Watch 연동, react-native-watch-connectivity 삽질기, 그리고 2-Tier Premium 완성."
date: 2026-02-27 14:00:00 +0900
image:
  path: /images/blog/wonder-note-part3-1.webp
  width: 1280
  height: 720
tags: ['Apple Watch', 'WatchConnectivity', 'React Native', '마술앱', 'IAP', '사이드프로젝트']
categories: [side-project]
author: wonder
---

마술사에게 이상적인 Peek 방법은 뭘까.

아이폰 화면을 몰래 보는 건 한계가 있다. 관객이 돌아볼 수 있고, 옆에서 누가 볼 수도 있다. **손목시계를 흘끗 보는 건 자연스럽다.** 시간 확인하는 것처럼 보이니까.

Apple Watch에서 관객의 그림을 확인할 수 있다면 — 그게 궁극의 Peek이다.

---

## WatchConnectivity: 아이폰과 워치를 연결하는 다리

![아이폰에서 워치로 이미지를 전송하는 구조](/images/blog/wonder-note-part3-2.webp)

Apple Watch 연동의 핵심은 `WatchConnectivity` 프레임워크다. React Native에서는 `react-native-watch-connectivity` 라이브러리가 이걸 브릿지한다.

아키텍처는 세 가지 통신 채널로 나뉜다:

| 채널 | API | 용도 | 특징 |
|------|-----|------|------|
| **Message** | `sendMessage()` | 숫자 인식 결과, 설정 변경 | 실시간, Watch 화면 켜져 있어야 함 |
| **File Transfer** | `startFileTransfer()` | 캡처 이미지 전송 | 큰 데이터, 백그라운드 전달 |
| **Application Context** | `updateApplicationContext()` | 프리미엄 상태, 언어 설정 | 마지막 값만 유지, 확실한 전달 |

마술 시나리오에서 각 채널의 역할이 다르다.

관객이 그림을 그리고 삭제하면, 캡처된 이미지가 **File Transfer**로 워치에 전송된다. 파일 전송이라 약간의 지연이 있지만, 마술사가 바로 확인할 필요는 없다. 공연 흐름상 "잠깐 생각하는 척" 하는 시간이 있으니까.

```typescript
export const sendImageToWatch = async (imageUri: string): Promise<boolean> => {
    try {
        await watchModule.startFileTransfer(imageUri, {
            type: 'magic_image',
            timestamp: Date.now(),
        });
        return true;
    } catch (e) {
        return false;
    }
};
```

OCR로 숫자를 인식하면 **Message**로 즉시 전달한다. 텍스트 한 줄이라 지연이 거의 없다:

```typescript
export const sendDigitToWatch = async (digit: string): Promise<boolean> => {
    watchModule.sendMessage({
        type: 'recognized_digit',
        digit,
        timestamp: Date.now(),
    });
    return true;
};
```

프리미엄 상태와 언어 설정은 **Application Context**로 보낸다. 이 채널은 "마지막으로 보낸 값"만 워치에 유지하기 때문에, 설정처럼 최신 상태만 중요한 데이터에 적합하다.

---

## 연결 상태 관리: 워치가 항상 켜져 있진 않다

Watch 앱 개발에서 가장 까다로운 건 **연결 상태 관리**다. 워치는 항상 아이폰과 연결돼 있지 않다. 블루투스 범위를 벗어나거나, 워치의 화면이 꺼져 있거나, 비행기 모드일 수 있다.

그래서 세 가지 상태를 추적한다:

```typescript
export interface WatchState {
    isConnected: boolean;   // 페어링 + 도달 가능
    isPaired: boolean;      // 블루투스 페어링 여부
    isReachable: boolean;   // 실시간 통신 가능 여부
}
```

`isPaired`는 한 번 설정하면 거의 안 바뀐다. 중요한 건 `isReachable`. 워치 화면이 꺼지면 `false`가 되고, 다시 켜면 `true`가 된다. 이 변화를 실시간으로 추적해야 한다:

```typescript
watchModule.watchEvents.on('reachability', (reachable: boolean) => {
    callback({
        isConnected: reachable,
        isPaired: true,
        isReachable: reachable,
    });
});
```

마술 공연 중에 "워치 연결 끊김" 에러가 뜨면 참사다. 그래서 설정 화면에 Watch 연결 상태를 실시간으로 표시하고, 공연 전에 미리 확인할 수 있게 했다.

---

## react-native-iap v12 → v14 마이그레이션

![IAP 버전 마이그레이션 삽질](/images/blog/wonder-note-part3-3.webp)

Watch 연동보다 오히려 더 삽질한 게 **인앱결제 라이브러리 업그레이드**였다.

`react-native-iap`을 처음 적용할 때 v12를 설치했는데, React Native 0.81과 호환이 안 됐다. v14로 올려야 했다. 문제는 API가 완전히 바뀌었다는 거다.

2월 19일 하루 동안 커밋 3개가 연달아 올라갔다:

```
b5cdb05 fix: correct react-native-watch-connectivity version to ^1.1.0
ffff8b3 fix: upgrade react-native-iap v12→v14 for RN 0.81 compatibility
95421b3 fix: add react-native-worklets peer dep & clean build for iOS
```

세 커밋이 말해주는 건 — **의존성 지옥**이다.

`react-native-iap` v14가 `react-native-worklets`를 peer dependency로 요구하는데, 이걸 명시적으로 설치하지 않으면 iOS 빌드가 터진다. `react-native-watch-connectivity`는 정확히 `^1.1.0`이어야 하는데, 다른 버전을 설치하면 런타임에서 크래시.

React Native 생태계의 고질적인 문제다. 라이브러리 A가 B를 요구하고, B가 C를 요구하는데, C가 A와 충돌한다. 이걸 해결하려면 `package.json`과 `package-lock.json`을 뚫어져라 보면서 버전을 맞춰야 한다.

---

## 2-Tier Premium: Standard vs Pro

V2.2에서 최종적으로 완성한 Premium 구조다. 무료 → Standard → Pro 3단계.

| 기능 | Free | Standard | Pro |
|------|:----:|:--------:|:---:|
| 기본 Peek (5회/일) | ✅ | ✅ | ✅ |
| 무제한 Peek | ❌ | ✅ | ✅ |
| 히스토리 (3개/24시간) | ✅ | ✅ | ✅ |
| 무제한 히스토리 | ❌ | ✅ | ✅ |
| OCR 숫자 인식 | ❌ | ✅ | ✅ |
| Apple Watch 연동 | ❌ | ❌ | ✅ |
| Watch 자동 숨김 | ❌ | ❌ | ✅ |

핵심 차별화는 **Watch 연동은 Pro 전용**이라는 것이다. Apple Watch가 있는 마술사라면 Pro를 안 살 이유가 없다. 그리고 Watch가 없는 사람은 Standard만으로 충분하다.

무료 사용자가 제한에 걸리면 `PremiumPrompt` 모달이 뜬다:

```typescript
interface PremiumPromptProps {
    visible: boolean;
    variant: 'peek' | 'history';  // 어디서 제한에 걸렸는지
    onUpgrade: () => void;
    onDismiss: () => void;
    standardPrice?: string | null;
}
```

"Peek 5회를 다 썼습니다" 또는 "히스토리가 가득 찼습니다" — 상황에 맞는 메시지를 보여주고 업그레이드를 유도한다. 가격은 App Store에서 실시간으로 가져온다.

---

## 3부를 마치며: 손목 위의 마술

![Apple Watch에서 관객의 그림을 확인하는 마술사](/images/blog/wonder-note-part3-4.webp)

WonderNote 개발기를 정리하면 이렇다:

| 버전 | 날짜 | 핵심 | 코드 변경량 |
|------|------|------|-----------|
| V1.0 | 2/6 | MVP — 위장 UX + 비밀 캡처 | +3,338줄 |
| V1.1 | 2/16 | 폴리싱 — 삭제 대화상자, strict 모드 | (V2.0에 포함) |
| V2.0 | 2/16 | Premium — IAP, OCR, Watch | +9,100줄 |
| V2.2 | 2/25 | 2-Tier Gating — Standard/Pro | +1,666줄 |

1월 20일 Expo 프로젝트 초기화부터 2월 25일 V2.2 완성까지, 약 5주. 이 기간 동안 실제 집중 개발 시간은 아마 5~6일 정도다. 나머지는 아이디어를 다듬고, 공연에서 테스트하고, 피드백을 반영하는 시간이었다.

사이드 프로젝트에서 배운 것:

1. **MVP는 빠르게, 제품화는 천천히.** Claude Code로 하루 만에 MVP를 찍고, 나머지 시간은 실전 피드백 기반으로 다듬었다
2. **번들 사이즈는 처음부터 관리하라.** 68MB까지 불어난 걸 4.55MB로 줄이는 건 가능하지만, 처음부터 안 넣었으면 더 좋았다
3. **React Native 의존성은 지뢰밭이다.** 라이브러리 버전 하나가 전체 빌드를 무너뜨린다. `package-lock.json`은 친구다
4. **Watch 연동은 생각보다 간단하고, 생각보다 까다롭다.** API는 세 줄이면 되지만, 연결 상태 관리와 에러 핸들링이 진짜 일이다

다음 포스트에서는 이 과정에서 만난 가장 짜증나는 버그 — **Xcode에서 Apple Watch가 안 보이는 문제**를 어떻게 해결했는지 다룬다.

> 📌 **WonderNote 개발기 시리즈**
> - [1부: iOS 메모앱으로 위장한 마술앱을 만들었다](/posts/wonder-note-magic-app-part1/)
> - [2부: 68MB에서 4.55MB로](/posts/wonder-note-magic-app-part2/)
> - **3부: 애플 워치에 마술을 올리기까지** ← 지금 읽는 글
