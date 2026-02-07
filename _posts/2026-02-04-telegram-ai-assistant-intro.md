---
title: 'Claude Code + Telegram으로 24시간 AI 비서 만들기 — 시리즈 소개'
description: '맥북에 항상 켜져 있는 Claude Code를 Telegram 봇과 연동해서 개인 AI 비서를 만드는 프로젝트를 시작합니다.'
date: 2026-02-04 00:00:00 +0900
tags: ['claude-code', 'telegram', 'automation', 'ai']
categories: [ai-automation]
image: /assets/img/blog/ai-assistant-intro-1.png
author: wonderx
---

## 왜 이 프로젝트를 시작했나

회사 맥북이 항상 온라인이다. Claude Code Max 플랜도 쓰고 있다.
그렇다면 이 맥북을 **24시간 AI 비서**로 만들 수 있지 않을까?

OpenClaw 같은 도구도 있지만, 이미 Max 플랜($100/월)을 결제하고 있으니
추가 비용 없이 Claude Code의 `-p` 모드를 활용하기로 했다.

## 아키텍처

```
📱 Telegram → 🐍 Python Bot (맥북) → 💻 Claude Code CLI → 결과 반환
```

핵심은 간단하다:

1. Telegram으로 메시지를 보내면
2. 맥북의 Python 봇이 받아서
3. `claude -p "명령"` 으로 Claude Code를 실행하고
4. 결과를 다시 Telegram으로 보내준다

## Claude Code를 비서로 쓸 때의 장점

일반 API 호출과 다르게 Claude Code는 **맥북 전체를 조작**할 수 있다:

- 프로젝트 빌드 & 배포
- Git 상태 확인, commit, push
- 로그 파일 읽기
- 코드 직접 수정
- 터미널 명령 실행

단순 챗봇이 아니라 **실제로 일을 처리하는 비서**가 되는 것.

## 시리즈 예정

1. **프로젝트 세팅** — Telegram 봇 생성 & Claude Code 연동 (다음 글)
2. **대화 맥락 관리** — 히스토리 유지 & 시스템 프롬프트
3. **자동화 추가** — launchd로 자동 실행, 크론 작업
4. **기능 확장** — MCP 연동, 파일 관리, 알림

## 비용

| 항목 | 비용 |
|------|------|
| Claude Max 구독 | $100/월 (기존 결제) |
| Telegram Bot API | 무료 |
| 맥북 상시 가동 | 전기세 약간 |
| **추가 비용** | **$0** |

다음 글에서 실제 코드와 함께 세팅 과정을 공유하겠다.

---

*이 블로그는 Astro + GitHub Pages로 운영되며, WonderX Inc.의 기술 블로그입니다.*
