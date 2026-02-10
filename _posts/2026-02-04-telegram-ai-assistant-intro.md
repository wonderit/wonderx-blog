---
title: 'Claude Code + Telegram으로 24시간 AI 비서 만들기 — 시리즈 소개'
description: '맥북에 항상 켜져 있는 Claude Code를 Telegram 봇과 연동해서 개인 AI 비서를 만드는 프로젝트를 시작한다.'
date: 2026-02-04 00:00:00 +0900
tags: ['claude-code', 'telegram', 'automation', 'ai']
categories: [ai-automation]
image:
  path: /images/blog/ai-assistant-intro-1.webp
  width: 800
  height: 800
author: wonder
twin: telegram-ai-assistant-intro-en
---

## 맥북이 놀고 있었다

회사 맥북은 24시간 켜져 있다. Claude Code Max 플랜도 매달 $100씩 내고 있다.
근데 이걸 퇴근하면 그냥 방치하고 있었다.

솔직히 멍청했다.

어느 날 문득 생각이 들었다. 이 맥북, 텔레그램이랑 연결하면 **24시간 일하는 비서** 되는 거 아닌가?

OpenClaw 같은 도구도 봤다. 근데 나는 이미 Max 플랜을 쓰고 있다. 추가 비용 0원. Claude Code의 `-p` 모드만 쓰면 된다. 끝.

## 구조는 이게 전부다

```
📱 Telegram → 🐍 Python Bot (맥북) → 💻 Claude Code CLI → 결과 반환
```

별거 없다. 진짜로.

1. 텔레그램으로 메시지를 보낸다
2. 맥북의 Python 봇이 받는다
3. `claude -p "명령"`으로 Claude Code를 실행한다
4. 결과를 다시 텔레그램으로 보내준다

나는 복잡한 걸 싫어한다. 이 네 줄이 전부인 게 마음에 들었다.

## 왜 굳이 Claude Code인가

일반 API 호출이랑은 차원이 다르다. Claude Code는 **맥북 자체를 조작**한다.

- 프로젝트 빌드 & 배포
- Git 상태 확인, commit, push
- 로그 파일 읽기
- 코드 직접 수정
- 터미널 명령 실행

ChatGPT한테 "배포 좀 해줘"라고 하면 방법을 알려준다. Claude Code한테 하면 **진짜로 배포한다.**

그 차이가 전부다.

## 앞으로 쓸 것들

1. **프로젝트 세팅** — Telegram 봇 생성 & Claude Code 연동 (다음 글)
2. **대화 맥락 관리** — 히스토리 유지 & 시스템 프롬프트
3. **자동화 추가** — launchd로 자동 실행, 크론 작업
4. **기능 확장** — MCP 연동, 파일 관리, 알림

삽질 과정도 다 쓸 거다. 깔끔하게 성공하는 글은 재미없다.

## 비용

| 항목 | 비용 |
|------|------|
| Claude Max 구독 | $100/월 (기존 결제) |
| Telegram Bot API | 무료 |
| 맥북 상시 가동 | 전기세 약간 |
| **추가 비용** | **$0** |

이미 내고 있는 돈으로 비서를 하나 더 고용한 셈이다. 세상에 이런 가성비가 없다.

다음 글에서 실제 코드를 까본다.

---

결국 좋은 도구는 이미 내 손에 있었다. 나만 몰랐을 뿐.
