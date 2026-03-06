---
title: "Xcode에서 Apple Watch가 안 보일 때 — 개발자 모드와 Trust의 함정"
description: "Xcode 디바이스 목록에 Apple Watch가 나타나지 않는 문제. Developer Mode 활성화, Trust Computer 순서, 그리고 Xcode를 먼저 끄는 게 핵심이었다."
date: 2026-02-28 10:00:00 +0900
image:
  path: /images/blog/xcode-watch-fix-1.webp
  width: 1280
  height: 720
tags: ['Xcode', 'Apple Watch', 'iOS 개발', 'React Native', '트러블슈팅', 'WonderNote']
categories: [dev-log]
author: wonder
---

WonderNote에 Apple Watch 기능을 넣고, 실기기에서 테스트하려고 했다. Xcode를 열었다. 디바이스 목록에 iPhone은 보이는데, **Watch가 없다.**

Developer Mode를 켜라는 옵션조차 보이지 않았다.

이게 꽤 많은 사람들이 겪는 문제인데, 해결법이 직관적이지 않다. 나도 2시간을 날렸다.

---

## 증상

- Xcode > Window > Devices and Simulators에 **iPhone만 보이고 Watch가 없다**
- Watch에 Developer Mode 활성화 옵션이 **아예 나타나지 않는다**
- iPhone을 USB로 연결해도 Watch가 감지되지 않는다

---

## 원인: Trust 순서의 타이밍 충돌

![Xcode와 iPhone의 Trust 타이밍 충돌](/images/blog/xcode-watch-fix-2.webp)

핵심 원인은 이거다. iPhone을 Mac에 연결하면 두 가지 "Trust" 과정이 필요하다:

1. **iPhone → Mac**: "이 컴퓨터를 신뢰하시겠습니까?" (PIN 입력)
2. **Xcode → iPhone**: Xcode가 개발용으로 디바이스를 등록

문제는 **Xcode가 열려 있는 상태에서 iPhone을 연결**하면, 두 개의 Trust 요청이 거의 동시에 뜬다. iPhone에서 첫 번째 PIN을 입력하기도 전에 Xcode가 두 번째 요청을 보내고, 둘 다 제대로 처리되지 않는다.

이 상태에서는 iPhone 자체는 연결되지만, Watch 페어링 정보까지는 전달되지 않는다.

---

## 해결: 11단계 프로토콜

커뮤니티에서 공유된 해결법을 내 상황에 맞게 조정했다. 순서가 중요하다:

### 1단계: 모든 연결 해제
```
☐ iPhone을 Mac에서 USB 분리
☐ Xcode에서 iPhone 페어링 해제 (Devices 목록에서 우클릭 > Unpair)
```

### 2단계: iPhone 신뢰 초기화
```
☐ iPhone > 설정 > 개발자 > 신뢰하는 컴퓨터 초기화 (Clear Trusted Computers)
☐ iPhone > 개발자 모드 비활성화
☐ iPhone > 개발자 모드 다시 활성화 → 재시작
```

이 단계가 핵심이다. **기존의 꼬인 Trust 관계를 완전히 리셋**하는 거다.

### 3단계: Xcode 끄기 (중요!)
```
☐ Xcode를 완전히 종료 (Cmd+Q)
```

**이게 가장 중요한 단계다.** Xcode가 열려 있으면 USB 연결 시 자동으로 Trust 요청을 보내서 타이밍 충돌이 재발한다.

### 4단계: 깨끗한 연결
```
☐ iPhone을 USB로 Mac에 연결
☐ iPhone에서 "이 컴퓨터를 신뢰하시겠습니까?" → 신뢰 + PIN 입력
☐ 완전히 처리될 때까지 기다리기 (10초 정도)
```

### 5단계: Xcode 재연결
```
☐ Xcode 실행
☐ iPhone에서 앱 실행 시도 → iPhone에서 다시 Trust 팝업 → 승인
☐ 이 시점에서 Xcode가 Watch도 감지해야 함
```

### 6단계: Watch 개발자 모드
```
☐ Watch에서 개발자 모드 활성화
☐ Watch에서 앱 실행
```

---

## 왜 이렇게 복잡한가

![Apple의 보안 레이어와 개발자 경험의 충돌](/images/blog/xcode-watch-fix-3.webp)

이 문제의 근본 원인은 **Apple의 보안 모델과 개발자 경험의 충돌**이다.

iOS 16부터 Developer Mode가 별도 토글로 분리됐다. 예전에는 Xcode에 연결하면 자동으로 개발용 디바이스가 등록됐는데, 이제는 사용자가 명시적으로 활성화해야 한다. 보안 관점에서는 맞는 판단이지만, 개발자 온보딩 경험은 확실히 나빠졌다.

Watch의 경우 한 단계 더 복잡하다. Watch는 iPhone을 통해서만 Mac과 통신하기 때문에:

```
Mac ← USB → iPhone ← Bluetooth → Watch
```

이 체인에서 **iPhone-Mac 간 Trust가 깨지면 Watch는 아예 보이지 않는다.** Watch 자체에 문제가 있는 게 아니라, iPhone과 Mac의 관계가 깨진 거다.

---

## 체크리스트 정리

다시 겪을 때를 대비해서 요약한다:

```
1. ☐ iPhone USB 분리
2. ☐ Xcode에서 iPhone 페어링 해제
3. ☐ iPhone: 신뢰하는 컴퓨터 초기화
4. ☐ iPhone: 개발자 모드 끄기 → 켜기 → 재시작
5. ☐ Xcode 완전 종료
6. ☐ iPhone USB 연결 → Trust → PIN
7. ☐ Xcode 실행 → 앱 빌드 시도 → Trust 다시 승인
8. ☐ Xcode가 Watch 감지 확인
9. ☐ Watch 개발자 모드 활성화
10. ☐ Watch에서 앱 실행
```

**핵심은 5번이다.** Xcode를 먼저 끄고, iPhone Trust를 완료한 후에 Xcode를 열어라. 이 순서만 지키면 대부분 해결된다.

---

## 마치며

이 버그에 2시간을 날리고 나서 생각했다. Apple Watch 개발이 어려운 게 아니다. **Watch에 코드를 올리기 전 단계가 어려운 거다.** `react-native-watch-connectivity` API는 10줄이면 되지만, Xcode에서 Watch를 인식시키는 데 2시간이 걸렸다.

개발에서 가장 시간을 많이 잡아먹는 건 코드를 짜는 시간이 아니라, **환경을 세팅하는 시간**이다. 특히 Apple 생태계에서.

![개발 환경 세팅에 시간을 빼앗기는 개발자](/images/blog/xcode-watch-fix-4.webp)

> 📌 관련 글: **WonderNote 개발기 시리즈**
> - [1부: iOS 메모앱으로 위장한 마술앱을 만들었다](/posts/wonder-note-magic-app-part1/)
> - [2부: 68MB에서 4.55MB로](/posts/wonder-note-magic-app-part2/)
> - [3부: 애플 워치에 마술을 올리기까지](/posts/wonder-note-magic-app-part3/)
