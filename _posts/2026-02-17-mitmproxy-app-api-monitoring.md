---
title: '매번 앱 껐다 켜기 지쳐서, 직접 API를 까봤다 — mitmproxy로 모바일 앱 트래픽 모니터링'
description: '커뮤니티 앱에서 모임이 항상 매진이라 새로고침도 안 되는데 앱을 껐다 켜야만 했다. 그래서 앱이 어떤 API를 호출하는지 직접 들여다보기로 했다. mitmproxy + iPhone 조합으로 HTTPS 트래픽을 캡처한 삽질기.'
date: 2026-02-17 22:00:00 +0900
tags: ['mitmproxy', 'API모니터링', '리버스엔지니어링', 'iOS', 'HTTPS', '네트워크분석', 'macOS']
categories: [tech]
image:
  path: /images/blog/mitmproxy-app-api-monitoring-1.webp
  width: 800
  height: 800
author: wonder
lang: ko
twin: mitmproxy-app-api-monitoring-en
---

## 앱을 껐다 켜는 게 일상이 된 순간

커뮤니티 앱을 하나 쓰고 있다. 모임에 참가 신청을 하는 앱인데, 인기 있는 모임은 올라오자마자 자리가 찬다.

문제는 이 앱에 **새로고침 버튼이 없다**는 것.

새 모임이 올라왔는지 확인하려면 앱을 완전히 종료했다가 다시 열어야 한다. 매번. 하루에도 몇 번씩. 이게 은근히 번거롭다. 알림이 오긴 하는데 알림이 올 때쯤이면 이미 마감이다.

그래서 생각했다.

> 이 앱이 서버에 어떤 요청을 보내는지 알 수 있다면, 내가 직접 주기적으로 호출하면 되지 않을까?

앱의 API 호출 패턴을 알아내기로 했다.

![동기](/images/blog/mitmproxy-app-api-monitoring-2.webp)

## 도구 선택: mitmproxy

모바일 앱의 네트워크 트래픽을 보려면 중간자 프록시(Man-in-the-Middle Proxy)가 필요하다. 대표적인 도구는 세 가지다.

| 도구 | 특징 | 가격 |
|------|------|------|
| **mitmproxy** | CLI/웹 UI, 오픈소스 | 무료 |
| **Charles Proxy** | GUI 기반, macOS 친화적 | $50 |
| **Proxyman** | 모던 UI, macOS 네이티브 | $49/yr |

나는 무료이고 CLI에서 바로 쓸 수 있는 **mitmproxy**를 선택했다.

```bash
brew install mitmproxy
```

## 처음엔 Android 에뮬레이터로 시도했다

처음에는 Android 에뮬레이터에서 해보려 했다. Android Studio에서 에뮬레이터를 띄우고, 프록시를 물리면 간단할 줄 알았다.

현실은 달랐다.

### 삽질 1: M칩 맥에서 32비트 앱이 안 돌아간다

APK를 구해서 설치하려 했는데, 이 앱이 **armeabi-v7a**(32비트 ARM) 네이티브 라이브러리만 제공하고 있었다. M칩 맥의 에뮬레이터는 **arm64-v8a만** 지원한다.

```
INSTALL_FAILED_NO_MATCHING_ABIS: Failed to extract native libraries
```

이 에러를 보고 한참 build.prop을 수정하고, setprop을 시도하고, 소스 이미지까지 뒤졌지만 결국 실패.

### 삽질 2: API 24 이미지는 x86뿐

Android 7.0 (API 24) 이하에서는 사용자 인증서를 앱이 신뢰하기 때문에, API 24 에뮬레이터를 만들어보려 했다. 그런데 Google Play가 포함된 API 24 ARM64 이미지는 **공식적으로 존재하지 않는다**.

x86 이미지를 받아봤자 M칩에서는 실행 불가:

```
PANIC: Avd's CPU Architecture 'x86' is not supported by the QEMU2 emulator on aarch64 host.
```

### 삽질 3: Google Play 이미지는 root 불가

Google Play가 포함된 에뮬레이터 이미지는 프로덕션 빌드라서 `adb root`가 안 된다. 시스템 인증서를 설치하려면 root가 필요한데, 막혀있다.

Google APIs 이미지(Play Store 없는 버전)는 root가 되지만, 그러면 앱을 Play Store에서 설치할 수 없다.

**결론: Android 에뮬레이터는 포기.**

![삽질](/images/blog/mitmproxy-app-api-monitoring-3.webp)

## iPhone + mitmproxy = 정답

실제 iPhone을 쓰기로 했다. 이게 훨씬 간단했다.

### 구성도

```
iPhone (Wi-Fi 프록시)
       ↓
   mitmproxy (맥, port 8080)
       ↓
   실제 서버
```

### Step 1: mitmproxy 실행

```bash
mitmweb --listen-port 8080 --no-web-open-browser
```

`mitmweb`은 웹 기반 UI를 제공해서 브라우저에서 트래픽을 실시간으로 볼 수 있다. 콘솔에 출력되는 토큰을 URL에 붙여서 접속한다.

### Step 2: iPhone Wi-Fi 프록시 설정

1. **설정 > Wi-Fi** > 연결된 네트워크 옆 (i)
2. **HTTP 프록시 구성 > 수동**
3. 서버: 맥의 로컬 IP / 포트: 8080

여기서 주의할 점이 하나 있다. **맥과 iPhone이 같은 네트워크에 있어야 한다.** 나는 맥을 이더넷(랜선)으로, iPhone을 Wi-Fi로 연결했더니 서로 통신이 안 됐다. 맥도 Wi-Fi로 바꾸니까 바로 해결됐다.

### Step 3: CA 인증서 설치

HTTPS 트래픽을 복호화하려면 mitmproxy의 CA 인증서를 iPhone에 설치해야 한다.

1. iPhone Safari에서 `http://mitm.it` 접속
2. Apple 인증서 다운로드
3. **설정 > 일반 > VPN 및 기기 관리** → 프로파일 설치
4. **설정 > 일반 > 정보 > 인증서 신뢰 설정** → mitmproxy 활성화

이 4단계를 완료하면 iPhone의 모든 HTTPS 트래픽이 mitmproxy를 통과하면서 복호화된다.

### Step 4: 앱 실행 → 트래픽 캡처

앱을 열고 여기저기 탭을 누르면 mitmweb UI에 요청이 쏟아진다. 이때 노이즈가 많으니 필터링이 중요하다.

무시해도 되는 것들:
- `amplitude.com` → 이벤트 트래킹
- `sentry.io` → 에러 리포팅
- `firebaseinstallations.googleapis.com` → Firebase 초기화
- `app-measurement.com` → Google Analytics

**진짜 API 서버**는 이것들을 걸러내면 바로 보인다.

## mitmweb 12.x의 토큰 인증 이슈

mitmproxy 12.x부터 웹 UI에 **토큰 인증**이 기본 활성화되었다. 문제는 `nohup`이나 백그라운드로 실행하면 토큰이 출력되지 않는다는 것. TTY가 아니면 콘솔 출력을 건너뛰기 때문이다.

해결법: Python의 `pty` 모듈로 가짜 TTY를 만들어서 토큰을 캡처했다.

```python
import subprocess, os, pty, re

master, slave = pty.openpty()
proc = subprocess.Popen(
    ['mitmweb', '--listen-port', '8080', '--no-web-open-browser'],
    stdout=slave, stderr=slave, stdin=subprocess.DEVNULL
)
os.close(slave)

output = b''
for _ in range(100):
    data = os.read(master, 4096)
    output += data
    m = re.search(r'token=([a-f0-9]+)', output.decode())
    if m:
        print(f'Token: {m.group(1)}')
        break
```

이렇게 하면 토큰을 파일에 저장하고, mitmweb 프로세스는 백그라운드에서 계속 돌릴 수 있다.

## 얻은 것

캡처 결과, 앱이 사용하는 실제 API 엔드포인트와 요청 패턴을 알아낼 수 있었다. 이제 이걸 가지고:

1. **주기적으로 API를 호출**해서 새 모임이 올라왔는지 확인
2. 조건에 맞으면 **알림을 보내는 스크립트** 작성
3. 앱을 껐다 켜는 수고를 **자동화**

로 이어갈 수 있게 되었다.

## 교훈

- **Android 에뮬레이터는 M칩 맥에서 32비트 앱 테스트가 사실상 불가능**하다. 실제 기기가 답이다.
- **iPhone + mitmproxy 조합이 가장 간단**하다. 인증서 설치도 직관적이고, 프록시 설정도 Wi-Fi 설정에서 바로 된다.
- **같은 네트워크** 확인은 필수. 유선/무선 혼용 시 통신 안 될 수 있다.
- mitmproxy 12.x의 토큰 인증은 **pty 트릭**으로 우회 가능.
- 외부 앱의 API를 이해하면 자동화의 가능성이 열린다.

![자동화](/images/blog/mitmproxy-app-api-monitoring-4.webp)

번거로움이 반복되면, 그건 자동화의 기회다.
