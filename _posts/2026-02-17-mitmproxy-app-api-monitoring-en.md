---
title: "Tired of Force-Quitting the App — So I Peeked at Its API with mitmproxy"
description: "A community app had no refresh button, so I had to kill and restart it every time to check for new events. I decided to intercept the app's HTTPS traffic with mitmproxy + iPhone to find the actual API endpoints."
date: 2026-02-17 22:00:00 +0900
tags: ['mitmproxy', 'API-monitoring', 'reverse-engineering', 'iOS', 'HTTPS', 'network-analysis', 'macOS']
categories: [tech]
image:
  path: /images/blog/mitmproxy-app-api-monitoring-1.webp
  width: 800
  height: 800
author: wonder
lang: en
twin: mitmproxy-app-api-monitoring
---

## When Force-Quitting Becomes a Daily Routine

I use a community app for signing up to social meetups. Popular events fill up the moment they're posted.

The problem? The app has **no refresh button**.

To check for new events, I have to fully kill the app and reopen it. Every time. Multiple times a day. Notifications exist, but by the time they arrive, the event is already full.

So I thought:

> If I could figure out what API calls the app makes, couldn't I just poll the server myself?

I decided to reverse-engineer the app's API call patterns.

![Motivation](/images/blog/mitmproxy-app-api-monitoring-2.webp)

## Tool Selection: mitmproxy

To inspect mobile app network traffic, you need a man-in-the-middle proxy. The three main options are:

| Tool | Features | Price |
|------|----------|-------|
| **mitmproxy** | CLI/Web UI, open source | Free |
| **Charles Proxy** | GUI-based, macOS-friendly | $50 |
| **Proxyman** | Modern UI, macOS native | $49/yr |

I chose **mitmproxy** because it's free and works straight from the CLI.

```bash
brew install mitmproxy
```

## First Attempt: Android Emulator

My initial plan was to use an Android emulator. Launch one in Android Studio, set up the proxy, done. Right?

Reality had other plans.

### Struggle 1: 32-bit Apps Don't Run on M-chip Macs

I got the APK and tried to install it, but the app only shipped **armeabi-v7a** (32-bit ARM) native libraries. The M-chip Mac emulator only supports **arm64-v8a**.

```
INSTALL_FAILED_NO_MATCHING_ABIS: Failed to extract native libraries
```

I spent hours modifying build.prop, trying setprop, digging through source images. All failed.

### Struggle 2: API 24 Images Are x86 Only

Android 7.0 (API 24) and below trusts user-installed certificates at the app level, so I tried creating an API 24 emulator. But a Google Play ARM64 image for API 24 **officially doesn't exist**.

Downloading the x86 image was pointless on an M-chip:

```
PANIC: Avd's CPU Architecture 'x86' is not supported by the QEMU2 emulator on aarch64 host.
```

### Struggle 3: Google Play Images Can't Be Rooted

Google Play emulator images are production builds, so `adb root` is blocked. Installing system certificates requires root, which is locked down.

Google APIs images (without Play Store) allow root, but then you can't install the app from the Play Store.

**Verdict: Gave up on Android emulator.**

![Struggles](/images/blog/mitmproxy-app-api-monitoring-3.webp)

## iPhone + mitmproxy = The Answer

I switched to using my actual iPhone. This was much simpler.

### Setup Diagram

```
iPhone (Wi-Fi Proxy)
       |
   mitmproxy (Mac, port 8080)
       |
   Actual Server
```

### Step 1: Run mitmproxy

```bash
mitmweb --listen-port 8080 --no-web-open-browser
```

`mitmweb` provides a web-based UI for viewing traffic in real time through your browser. You access it using the token printed to the console.

### Step 2: Configure iPhone Wi-Fi Proxy

1. **Settings > Wi-Fi** > tap (i) next to your network
2. **Configure Proxy > Manual**
3. Server: Mac's local IP / Port: 8080

One critical note: **the Mac and iPhone must be on the same network.** I had my Mac on Ethernet and iPhone on Wi-Fi, and they couldn't communicate. Switching the Mac to Wi-Fi immediately fixed it.

### Step 3: Install CA Certificate

To decrypt HTTPS traffic, you need to install mitmproxy's CA certificate on the iPhone.

1. Open `http://mitm.it` in iPhone Safari
2. Download the Apple certificate
3. **Settings > General > VPN & Device Management** > Install profile
4. **Settings > General > About > Certificate Trust Settings** > Enable mitmproxy

After these four steps, all HTTPS traffic from the iPhone passes through mitmproxy and gets decrypted.

### Step 4: Run the App and Capture Traffic

Open the app, tap around, and requests pour into the mitmweb UI. Filtering out noise is key.

Safe to ignore:
- `amplitude.com` - Event tracking
- `sentry.io` - Error reporting
- `firebaseinstallations.googleapis.com` - Firebase init
- `app-measurement.com` - Google Analytics

Filter these out, and the **real API server** becomes immediately visible.

## mitmweb 12.x Token Authentication Issue

Starting with mitmproxy 12.x, the web UI has **token authentication** enabled by default. The problem is that when running with `nohup` or in the background, the token isn't printed because it skips console output without a TTY.

Solution: Use Python's `pty` module to create a fake TTY and capture the token.

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

This lets you save the token to a file while keeping the mitmweb process running in the background.

## What I Got

From the captured traffic, I was able to identify the app's actual API endpoints and request patterns. With this knowledge, I can now:

1. **Poll the API periodically** to check for new events
2. Write a **notification script** that alerts me when conditions are met
3. **Automate** away the force-quit-and-reopen cycle

## Lessons Learned

- **Android emulators on M-chip Macs can't run 32-bit apps.** Use a real device instead.
- **iPhone + mitmproxy is the simplest combo.** Certificate installation is intuitive, and proxy setup is right in Wi-Fi settings.
- **Same network** is a must. Wired/wireless mixed setups may not communicate.
- mitmproxy 12.x token auth can be worked around with **the pty trick**.
- Understanding an external app's API opens up automation possibilities.

![Automation](/images/blog/mitmproxy-app-api-monitoring-4.webp)

When an annoyance repeats, it's an opportunity to automate.
