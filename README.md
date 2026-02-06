# WonderX Blog

WonderX Inc. 기술 블로그 — AI, 자동화, 그리고 개발 이야기

## 🚀 Quick Start

```bash
# 의존성 설치
npm install

# 개발 서버 실행
npm run dev

# 빌드
npm run build
```

## 📝 글 작성하기

`src/content/blog/` 폴더에 마크다운 파일을 추가하면 됩니다.

```markdown
---
title: '글 제목'
description: '글 설명'
pubDate: '2026-02-06'
tags: ['tag1', 'tag2']
---

본문 작성...
```

## 🌐 배포

`main` 브랜치에 push하면 GitHub Actions가 자동으로 빌드 & 배포합니다.

## 🔗 커스텀 도메인

`blog.wonderx.co.kr` → GitHub Pages CNAME 설정 필요

```bash
# public/CNAME 파일 생성
echo "blog.wonderx.co.kr" > public/CNAME
```

DNS에서 `blog.wonderx.co.kr` → `wonderx-inc.github.io` CNAME 레코드 추가
