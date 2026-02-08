---
title: '지킬에서 Astro로 갈아탄 이유 — 바퀴를 다시 발명하지 말라'
description: '블로그 템플릿을 Astro로 마이그레이션했다. 페이지뷰, 광고, 사이드 메뉴까지 이미 잘 만들어진 기능을 가져다 쓰는 게 답이다.'
date: 2026-02-08 01:00:00 +0900
tags: ['astro', 'jekyll', 'migration', 'goatcounter', 'adsense', 'blog', 'dont-reinvent-wheel']
categories: [dev]
image: /assets/img/blog/astro-migration-1.png
author: wonder
---

## 템플릿을 갈아탔다

블로그를 지킬(Jekyll)에서 Astro로 옮겼다. 정확히는 Astro 기반 블로그 템플릿을 찾아서 마이그레이션했다.

원래 쓰던 지킬 템플릿도 괜찮았다. 근데 블로그를 운영하면서 필요한 게 계속 생긴다.

- 페이지뷰 카운터
- 광고 (AdSense)
- 좌측 사이드바 메뉴
- 관련 글 추천
- 이전/다음 글 네비게이션
- 인기 글 보기

이걸 하나씩 직접 구현하려니 시간이 너무 오래 걸린다. **그래서 이미 다 만들어진 템플릿을 찾았다.**

## 왜 Astro인가

Astro 템플릿을 고른 이유는 간단하다.

1. **필요한 기능이 이미 있다** — 페이지뷰, 사이드바, 네비게이션, 관련 글
2. **빠르다** — Static Site Generation + Island Architecture
3. **확장하기 쉽다** — 컴포넌트 기반, MDX 지원
4. **Goatcounter 연동 가능** — 페이지뷰 카운터를 실시간으로 표시

특히 페이지뷰는 중요했다. 블로그를 쓰면서 "이 글은 얼마나 많은 사람이 봤을까?"를 알고 싶었다. Goatcounter를 쓰면 서버 없이도 페이지뷰를 추적할 수 있다.

![Astro 블로그 구조](/assets/img/blog/astro-migration-2.png)

## 마이그레이션 과정

1. **템플릿 선정** — GitHub에서 Astro 블로그 템플릿 검색 → 마음에 드는 거 Fork
2. **기존 글 이동** — 지킬 `_posts/` → Astro `src/content/posts/` (frontmatter 약간 수정)
3. **Goatcounter 연동** — 스크립트 추가 + API로 페이지뷰 가져오기
4. **AdSense 추가** — `<head>`에 메타 태그 + 스크립트
5. **사이드바 커스터마이징** — 메뉴 구조 조정
6. **GitHub Pages 배포** — `astro build` → `gh-pages` 브랜치

총 소요 시간: **2시간**. 처음부터 만들었으면 며칠은 걸렸을 것이다.

## Goatcounter — 페이지뷰 추적

Goatcounter는 Google Analytics의 심플한 대안이다.

- **프라이버시 친화적** — GDPR 걱정 없음
- **무료** — 월 10만 페이지뷰까지
- **API 제공** — 페이지뷰 수를 블로그에 직접 표시 가능

블로그에 페이지뷰 카운터를 넣으려면:

1. Goatcounter 계정 생성 (`wonderx.goatcounter.com`)
2. 스크립트 추가:
```html
<script data-goatcounter="https://wonderx.goatcounter.com/count"
        async src="//gc.zgo.at/count.js"></script>
```
3. API로 페이지뷰 가져오기:
```javascript
fetch('https://wonderx.goatcounter.com/api/v0/stats/total')
  .then(res => res.json())
  .then(data => console.log(data.total_hits))
```

Astro 템플릿에는 이미 Goatcounter 연동 코드가 포함되어 있었다. 설정 파일에 URL만 넣으면 끝.

![페이지뷰 표시](/assets/img/blog/astro-migration-3.png)

## AdSense — 광고 추가

블로그에 광고를 넣으려면 AdSense가 편하다.

1. AdSense 계정 생성
2. 사이트 등록 + 심사 대기
3. 승인되면 `<head>`에 스크립트 추가
4. `ads.txt` 파일을 루트에 배치

Astro에서는 `public/ads.txt`에 파일 넣으면 자동으로 배포된다. `src/layouts/BaseLayout.astro`의 `<head>` 섹션에 AdSense 스크립트를 추가했다.

## 사이드바 메뉴

좌측 사이드바가 있는 템플릿을 골랐다. 모바일에서는 햄버거 메뉴로 전환되고, 데스크톱에서는 고정 사이드바로 표시된다.

메뉴 구조:
- Home
- Categories
- Tags
- Archives
- About

기존 지킬 템플릿에는 사이드바가 없었다. 직접 만들려면 CSS + JavaScript로 반응형 메뉴를 구현해야 하는데, 이미 잘 만들어진 걸 쓰는 게 훨씬 빠르다.

## 바퀴를 다시 발명하지 말라

내가 팀원들에게 자주 하는 말이 있다.

**"굳이 바퀴를 다시 발명하려고 하지 말자."**

이미 잘 만들어진 기능이 있으면 가져다 쓰면 된다. 직접 만들어서 시간 쓰는 것보다, 그 시간에 더 중요한 비즈니스 로직을 짜는 게 낫다.

물론 학습 목적이면 다르다. 하지만 실무에서는 효율이 우선이다. 기본 함수를 다시 만드느라 시간 쓰지 말고, 이미 검증된 라이브러리를 쓰자.

블로그도 마찬가지다. 페이지뷰 카운터, 사이드바, 광고 연동을 직접 만들 수도 있다. 하지만 이미 누군가 잘 만들어놓은 템플릿이 있다면? **그냥 쓰면 된다.**

## 남은 작업 — 크랩버튼

아직 못한 게 하나 있다. **크랩 버튼**.

블로그 글을 읽다가 "이 글 별로네" 싶으면 크랩(게) 이모지를 누를 수 있게 하려고 한다. 나중에 추가할 예정.

## 정리

- 지킬 → Astro 마이그레이션 완료
- Goatcounter로 페이지뷰 추적
- AdSense 광고 연동
- 사이드바 + 이전/다음 글 네비게이션 추가
- 총 소요 시간: 2시간

이미 잘 만들어진 바퀴를 가져다 쓰자. 그게 효율적이다.

![최종 블로그 모습](/assets/img/blog/astro-migration-4.png)
