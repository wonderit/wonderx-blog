# WonderX Blog 프로젝트 메모리

Astro 기반 개인 블로그. GitHub Pages 배포.

## 구조

- `src/content/blog/` — 마크다운 블로그 포스트
- `public/images/blog/` — 블로그 이미지
- `src/components/` — Astro 컴포넌트
- `src/layouts/` — 레이아웃

## 블로그 작성 규칙

- frontmatter: title, description, pubDate, tags, category, heroImage
- category: ai-automation, side-project, dev-log, social, tutorial
- heroImage: frontmatter에만 (본문에 삽입하지 않음)
- 본문 이미지: 3장 (과정/개념/결과)
- 말투: ~다 체, 반말, 친근하고 실용적
- draft: false (바로 발행)
- 작성 후 자동 git commit + push

## 기술 결정사항

- [2026-02-06] hero image 모바일 대응: max-width: 100%
- [2026-02-07] GA4 + Vercel Analytics 통합
- [2026-02-08] 텔레그램 봇에서 블로그 수정/배포 요청 가능
