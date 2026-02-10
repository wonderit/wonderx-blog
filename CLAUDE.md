# WonderX Blog 프로젝트 메모리

Jekyll 기반 개인 블로그 (jekyll-theme-chirpy). GitHub Pages 배포.

## 구조 (Jekyll — Astro 아님!)

- `_posts/` — 블로그 포스트 (파일명: `YYYY-MM-DD-slug.md`)
- `images/blog/` — 블로그 본문 이미지
- `images/` — 기타 이미지 (썸네일 등)
- `_config.yml` — Jekyll 설정
- `_layouts/` — 레이아웃
- `_includes/` — 인클루드

⚠️ `src/content/blog/`는 사용하지 않음! (Astro 구조 아님)

## 블로그 작성 규칙

- 파일 위치: `_posts/YYYY-MM-DD-slug.md` (반드시 날짜 prefix 필요)
- frontmatter 필수 필드:
  ```yaml
  ---
  title: '제목'
  description: '설명'
  date: YYYY-MM-DD HH:MM:SS +0900
  image: /images/blog/이미지.jpg   # 썸네일/히어로 이미지
  tags: ['tag1', 'tag2']
  categories: [카테고리]
  author: wonder
  ---
  ```
- categories: youtube, social, dev-log, ai-automation, side-project, tutorial, thoughts
- image: frontmatter에 썸네일 경로 (홈 리스트에 표시됨)
- 본문 이미지: `![설명](/images/blog/파일명.jpg)` 형식으로 3장 삽입
- 이미지 파일 저장: `images/blog/` 폴더
- 말투: ~다 체, 반말, 친근하고 실용적
- 작성 후 자동 git commit + push

## 멀티 머신 작업 규칙

⚠️ **작업 시작 전 반드시 `git pull origin main`** (다른 머신에서 푸시했을 수 있음)
- 빌드 명령: `eval "$(rbenv init -)" && bundle exec jekyll b 2>&1`
- 상세 세팅: Google Drive `claudecode/projects/wonderx-blog/SETUP.md` 참조

## 다국어 구조

- 한국어 홈: `/` (layout: home), 영문 홈: `/en/` (layout: home-en)
- 포스트 기본 lang: `ko`, 영문 포스트: `lang: en` frontmatter
- `twin` frontmatter로 한↔영 포스트 교차 링크
- categories/tags/archives 레이아웃에서 `page.lang` 기준 필터링
- 페이지네이션: home.html에서 한국어 포스트만 자체 페이지네이션

## 기술 결정사항

- [2026-02-06] hero image 모바일 대응: max-width: 100%
- [2026-02-07] GA4 + Vercel Analytics 통합
- [2026-02-08] 텔레그램 봇에서 블로그 수정/배포 요청 가능
- [2026-02-08] Jekyll (chirpy theme) 기반 — Astro 아님! `_posts/` 폴더 사용
- [2026-02-10] 전체 영문 번역 완료 (13개 포스트), twin frontmatter 연결
- [2026-02-10] categories/tags/archives 다국어 필터링 적용
- [2026-02-10] 홈 페이지네이션: 한국어 포스트 기준 자체 구현 (jekyll-paginate 한계 우회)
