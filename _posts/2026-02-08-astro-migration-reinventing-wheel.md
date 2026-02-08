---
title: 'Astro에서 다시 Jekyll로 — 바퀴를 다시 발명하지 말라'
description: 'Astro로 Chirpy 스타일 블로그를 직접 만들다가 안 되는 게 너무 많아서, 결국 진짜 Chirpy(Jekyll) 테마로 돌아왔다. 이미 잘 만들어진 건 그냥 쓰자.'
date: 2026-02-08 01:00:00 +0900
tags: ['astro', 'jekyll', 'chirpy', 'migration', 'goatcounter', 'adsense', 'blog', 'dont-reinvent-wheel']
categories: [dev]
image: /images/blog/astro-migration-1.jpg
author: wonder
---

## 처음에는 Astro였다

이 블로그는 원래 **Astro v5**로 만들었다.

직접 컴포넌트를 짜고, 레이아웃을 만들고, 스타일을 입혔다. SEO도 넣고, Giscus 댓글도 붙이고, GoatCounter 페이지뷰도 연동했다.

꽤 잘 돌아가고 있었다.

## 벤치마크를 발견했다

그러다 [otzslayer.github.io](https://otzslayer.github.io/) 블로그를 봤다. **Chirpy 테마** 기반의 Jekyll 블로그.

한눈에 봐도 완성도가 달랐다.

- 좌측 고정 사이드바 (프로필, 네비게이션, 소셜 링크)
- 우측 패널 (최근 업데이트, 트렌딩 태그)
- 페이지뷰 카운터가 각 글마다 표시
- 광고(AdSense)가 자연스럽게 배치
- 다크/라이트 모드 토글
- 검색, TOC, 관련 글 추천까지

"이거 내 블로그에도 넣고 싶다."

## Astro에서 Chirpy 스타일을 직접 만들었다

처음에는 **Astro 안에서** Chirpy 스타일을 재현하려고 했다.

Claude Code한테 시켰다. 결과물:

- `Sidebar.astro` — 좌측 사이드바 (프로필, 네비게이션, 소셜 아이콘)
- `RightPanel.astro` — 우측 패널 (최근 업데이트, 트렌딩 태그, 광고)
- `SearchBar.astro` — 클라이언트 사이드 검색
- `global.css` 1,235줄 전면 재작성
- Categories, Tags, Archives 페이지 신규 생성

빌드도 성공했고, 48페이지가 생성됐다. 커밋하고 푸시했다.

## 그런데 안 되는 게 너무 많았다

배포하고 보니 **빠진 게 한두 개가 아니었다.**

- ❌ 페이지뷰가 각 글에 안 보임
- ❌ 우측 사이드바가 포스트 페이지에서 안 나옴
- ❌ 광고 배치가 제대로 안 됨
- ❌ 좋아요/리액션 기능 없음
- ❌ 검색이 불안정
- ❌ 다크 모드 전환 시 깨지는 스타일

Chirpy 테마가 수년간 다듬어온 기능들을 **하루 만에 Astro 컴포넌트로 재현하는 건 불가능**했다.

## 결국 진짜 Chirpy로 갔다

고민했다.

> "계속 Astro에서 하나씩 고칠까, 아니면 그냥 Chirpy 테마를 쓸까?"

답은 명확했다. **이미 잘 만들어진 걸 쓰자.**

`cotes2020/jekyll-theme-chirpy`를 포크해서 기존 레포를 통째로 대체했다.

### 마이그레이션 과정

1. **Chirpy 테마 클론** → 기존 Astro 파일 전부 삭제
2. **_config.yml 설정** — 한국어, GA4, GoatCounter, Giscus 댓글, 아바타
3. **블로그 글 10개 마이그레이션** — frontmatter 변환 (`pubDate` → `date`, `heroImage` → `image`, `category` → `categories`)
4. **이미지 경로 변경** — `public/images/blog/` → `assets/img/blog/`
5. **내부 링크 수정** — `/blog/slug` → `/posts/slug/`
6. **AdSense 설정** — 사이드바 + 인아티클 광고
7. **GitHub Actions 배포** — Ruby 3.3 + Jekyll 빌드

빌드 시간: **0.8초**. 배포까지 총 **50초**.

## Chirpy가 제공하는 것들

테마를 쓰니까 이 모든 게 **그냥 됐다:**

- ✅ 좌측 사이드바 (프로필, 네비게이션, 다크/라이트 토글)
- ✅ 우측 패널 (최근 업데이트, 트렌딩 태그)
- ✅ GoatCounter 페이지뷰 (각 글마다 자동 표시)
- ✅ Giscus 댓글 + 리액션
- ✅ 검색 (Simple-Jekyll-Search)
- ✅ TOC (Table of Contents)
- ✅ 관련 글 추천
- ✅ 이전/다음 글 네비게이션
- ✅ AdSense 광고 (사이드바 + 인아티클)
- ✅ 한국어 로케일 기본 제공
- ✅ PWA 지원
- ✅ SEO 최적화 (og:image, twitter:card 등)

**직접 만들면 며칠, 테마를 쓰면 2시간.**

## 바퀴를 다시 발명하지 말라

개발자들이 자주 빠지는 함정이 있다.

**"이 정도는 직접 만들 수 있는데?"**

맞다. 만들 수 있다. 근데 **만들어야 하는가?**

Astro에서 Chirpy 스타일을 재현하려다 깨달았다. 레이아웃만 비슷하게 만드는 건 쉽다. 근데 **세부 기능까지 완성도 있게 동작하게 만드는 건** 전혀 다른 문제다.

페이지뷰 연동, 다크 모드 전환, 검색 인덱싱, 광고 배치 최적화, 반응형 사이드바... 이런 걸 하나하나 직접 구현하느라 시간 쓸 바에, **이미 수년간 다듬어진 테마를 쓰는 게 낫다.**

> **Don't reinvent the wheel.**

완벽한 커스텀보다 잘 돌아가는 기성품이 낫다. 그 시간에 **글을 한 편 더 쓰자.**

---

*P.S. Astro가 나쁜 건 아니다. 좋은 프레임워크다. 다만 블로그처럼 이미 잘 만들어진 솔루션이 있는 영역에서는, 처음부터 만들 이유가 없다는 것.*
