---
title: "gstack으로 5분만에 개발 자동화 완벽 구축!"
description: "Claude Code + gstack + gbrain Supabase 마이그레이션, makers-log 자동화 시스템 구축 기록."
date: 2026-05-08 22:00:00 +0900
image: /images/blog/makers-log-2026-05-08.png
tags: ['메이커스로그', '데일리로그', 'Claude-Code', '클로드코드', 'gstack', 'gbrain', '자동화']
categories: [daily-log]
author: wonder
---

## 2026년 5월 8일 작업 요약

오늘은 코드 커밋보다 **개발 환경 자동화**에 집중한 날이다. 집 맥북을 새로 세팅하면서 회사 맥과 동일한 Claude Code + gstack 환경을 구축했다.

### 🔨 개발·인프라

- `primeet-*` 레포 전체를 `~/workplace/primeet/` 아래로 정리
- `bun` 설치 → gstack 셋업 (`bash ~/.claude/skills/gstack/setup`)
- `/setup-gbrain` 실행 — 집 맥에 gbrain 로컬 PGLite 엔진 구성
- `/sync-gbrain` 실행 — gstack-artifacts GitHub 레포와 아티팩트 동기화

### 🧠 gbrain Supabase 마이그레이션

가장 큰 작업이었다. 기존에 로컬 PGLite로 돌리던 gbrain을 **Supabase PostgreSQL**로 이전했다.

- `gbrain migrate --to supabase` → 회사 맥 데이터(29 pages) 확인
- 기존 데이터 보존 선택 → `gbrain init --supabase --url` 로 config만 전환
- 이제 집 맥 ↔ 회사 맥이 **같은 Supabase DB**를 바라봄
- `gbrain embed --stale` → OpenAI API로 82 chunks 임베딩 완료

### ⚙️ Claude Code 자동화

- `SessionEnd` 훅 추가 → 세션 종료 시 `gbrain sync` 자동 실행
- 기존 `SessionStart` 훅(gstack-session-update)과 함께 **세션 시작/종료 양방향 싱크** 완성
- 매 대화가 끝나면 자동으로 gbrain에 저장되고, 다음 세션에서 바로 이어받는 구조

### 📋 makers-log 자동화 시스템

이 메이커스로그 자체를 자동으로 만드는 시스템을 구축했다.

- `~/bin/makers-log` Python 스크립트 작성
  - 오늘 날짜 git 커밋 자동 수집 (전 레포 대상)
  - 커밋을 개발/기획콘텐츠/인사이트로 자동 분류
  - GPT-4o-mini로 키워드 후킹 제목 자동 생성
  - DALL-E 3로 썸네일 자동 생성
  - Jekyll 블로그 초안 자동 생성 (`_posts/`)
  - 텔레그램 봇으로 일일 요약 발송
- cron 등록: **매일 밤 10시** 자동 실행
- `--dry-run`, `--date` 플래그 지원

### 🔐 iCloud Secrets 관리

- `iCloud/secrets/api-keys.sh` 생성 (chmod 600)
- OpenAI API 키 등 시크릿 한 곳에 관리
- `~/.zshrc`에 자동 source 추가 → 셸 시작 시 환경변수 자동 로드
- 회사 맥에서도 iCloud 동기화로 동일하게 사용 가능

---

## 오늘의 인사이트

> "자동화는 처음 만들 때가 제일 힘들다. 하지만 한번 만들어두면 매일 조금씩 나한테 시간을 돌려준다."

makers-log 시스템을 만들면서 느낀 것 — Claude Code로 반복 작업을 자동화하는 건 단순히 편리함이 아니라, **기록의 지속성**을 만드는 일이다. 오늘 어떤 커밋을 했는지, 어떤 생각을 했는지를 자동으로 정리해주는 시스템이 생겼다.

---

> *이 글은 Claude Code + makers-log 스크립트로 자동 생성된 초안에 내용을 보강했습니다.*
