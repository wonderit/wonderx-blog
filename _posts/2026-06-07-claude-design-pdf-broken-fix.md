---
title: "Claude Design 슬라이드, PDF로 추출하면 깨지는 이유 — 원인 분석과 복붙 가능 예방 프롬프트"
description: "임원 보고 전날 밤, Claude Design으로 만든 슬라이드를 PDF로 추출했더니 색상 블록이 텍스트를 덮고 배경 그리드가 전면 노출됐다. background-clip:text, box-shadow, mask-image — PDF 렌더러가 무시하는 CSS 목록과 처음부터 막는 예방 프롬프트를 정리했다."
date: 2026-06-07 23:00:00 +0900
image:
  path: /images/blog/claude-design-pdf-fix-hero.webp
  width: 1280
  height: 720
tags: ['Claude', 'Claude-Design', 'PDF', '슬라이드', '프레젠테이션', 'CSS', 'AI툴', 'PPT', '프롬프트엔지니어링']
categories: [dev-log]
author: wonder
---

요즘 파워포인트 안 열고 Claude.ai Design으로 프레젠테이션을 만드는 사람이 많아졌다. HTML/CSS 기반이라 디자인 자유도가 높고, AI가 레이아웃까지 즉석에서 잡아주니 PT 제작 시간이 확 줄어든다.

그런데 함정이 있다.

**"완성된 슬라이드를 PDF로 추출하면 왜 이렇게 깨지죠?"**

임원 보고 전날 밤이었다. PDF를 열었더니 이런 일이 벌어져 있었다.

- 보라색 직사각형 블록이 제목 텍스트를 통째로 덮고 있다
- 버튼 뒤에 시안 색상 덩어리가 뭉텅이로 붙어 있다
- 장식용 배경 그리드가 전 슬라이드에 그대로 노출돼 있다
- eyebrow 앞에 있어야 할 장식 pill이 흔적도 없이 사라져 있다

원인을 직접 분석해서 수정했다. 같은 상황 겪지 않도록 원인과 예방 프롬프트를 공개한다.

![브라우저 정상 렌더링 vs PDF 추출 후 깨진 슬라이드 비교](/images/blog/claude-design-pdf-fix-hero.webp)

---

## 왜 PDF에서 깨지는가 — 렌더러 간극의 문제

Claude Design이 생성하는 슬라이드는 브라우저 기반이다. Chrome, Safari 등 최신 브라우저는 CSS 최신 스펙을 대부분 지원한다. 문제는 **PDF 변환 시 사용하는 렌더러가 10년 전 수준의 CSS만 처리한다**는 점이다. 이 간극에서 모든 문제가 발생한다.

실제로 겪은 케이스 4가지다.

---

### 문제 1 — 그라데이션 텍스트가 색상 블록으로 둔갑

원인은 `background-clip: text`다. 이 기법은 배경 그라데이션을 텍스트 형태로 잘라내서 컬러를 입힌다. 이때 텍스트 자체는 `color: transparent`로 투명하게 처리된다.

PDF 렌더러가 `background-clip: text`를 무시하면 어떻게 되나. **투명한 텍스트 자리에 배경 박스만 남는다.** 보라 그라데이션 제목이 보라색 직사각형 블록으로 둔갑하는 이유가 이것이다.

```css
/* Claude Design이 생성하는 코드 (브라우저에선 정상) */
.hero-title {
  background: linear-gradient(135deg, #7c3aed, #a855f7);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent; /* PDF에서 텍스트가 그냥 투명해진다 */
}
```

---

### 문제 2 — box-shadow가 색상 덩어리로 변신

Claude Design은 버튼이나 카드에 컬러 `rgba` box-shadow를 즐겨 쓴다. `box-shadow: 0 6px 20px rgba(61, 214, 224, 0.30)` 같은 식으로.

PDF 렌더러는 blur 값을 무시하고 단색 solid 블록으로 처리한다. 반투명 시안 그림자가 시안 색상 덩어리로 굳어서 버튼 뒤에 붙는다.

---

### 문제 3 — 배경 그리드가 전면 노출

장식용 그리드 배경에 `mask-image`로 "가장자리만 보이고 중앙은 투명"하게 처리하는 패턴이 있다. 브라우저에서는 자연스럽게 페이드아웃된 그리드가 보인다.

PDF 렌더러는 `mask-image` 미지원이다. 마스크 없이 그리드 전체가 슬라이드를 뒤덮는다.

---

### 문제 4 — 글로우 장식과 pill이 색상 블록으로 변신

`filter: blur()`가 적용된 `radial-gradient` 장식 div는 PDF에서 blur가 무시되어 선명한 원형 블록으로 렌더링된다. eyebrow 앞 장식 pill은 `::before { content: none }`으로 설정돼 있으면 PDF에서 아예 사라진다.

![PDF 렌더러가 무시하는 CSS 속성 — 개발자 야근 버전](/images/blog/claude-design-pdf-fix-dev.webp)

---

## PDF 렌더러가 지원 안 하는 CSS 요약

| CSS 속성 | 브라우저 결과 | PDF 결과 |
|---------|------------|---------|
| `background-clip: text` | 그라데이션 텍스트 | 색상 직사각형 블록 |
| `box-shadow` (컬러 rgba) | 반투명 그림자 | 단색 블록 |
| `filter: blur()` | 부드러운 글로우 | 선명한 색상 덩어리 |
| `mask-image` | 부분 표시 | 전체 노출 |
| `backdrop-filter: blur()` | 유리 효과 | 일반 배경색만 표시 |

---

## 복붙 가능한 예방 프롬프트 — 처음부터 PDF-safe하게

슬라이드 생성 요청에 아래 프롬프트를 함께 넣으면 된다. 처음부터 PDF-safe한 슬라이드가 나온다.

```
슬라이드를 PDF로 추출했을 때도 깨지지 않도록 아래 CSS 규칙을 반드시 지켜서 만들어줘.

PDF-safe 규칙:
① 그라데이션/컬러 텍스트: background-clip:text 금지 → color:#색상코드 직접 사용
② 그림자: box-shadow에 컬러 rgba 금지 → 검정 rgba(0,0,0,.N) 또는 box-shadow 제거
③ 장식 글로우: filter:blur() 적용 div 금지 → display:none 또는 opacity:0으로 처리
④ 배경 그리드: mask-image 금지 → 필요 시 opacity로만 조절
⑤ ::before/::after 장식: content:none 금지 → 실제 content 또는 아예 제거
⑥ backdrop-filter:blur() 대신 배경색+opacity 조합으로 대체
```

---

## 이미 만든 슬라이드 사후 수정 프롬프트

완성 후에야 문제를 발견했다면 이걸 Claude에 붙여넣으면 된다.

```
현재 슬라이드를 PDF로 추출했을 때 깨지는 요소를 전수 수정해줘.

수정 항목:
① .grad-text, .cy-text 등 background-clip:text 클래스 → color 직접 지정으로 교체
② 인라인 style에서 background-clip:text 패턴 전수 검색 후 동일 교체
③ 컬러 rgba box-shadow(시안, 보라 등) → 제거 또는 rgba(0,0,0,.07)로 교체
④ filter:blur()가 적용된 장식용 position:absolute div → display:none
⑤ mask-image가 적용된 배경 그리드 div → display:none 또는 background-image:none
⑥ eyebrow::before { content:none } → content:"" + pill 스타일 복원
   (width:28px; height:4px; background:주색상; border-radius:9999px; margin-right:12px)

텍스트 내용, 폰트, 레이아웃은 유지. 전체 슬라이드 일괄 적용.
```

![예방 프롬프트 적용 후 깔끔하게 추출된 PDF 슬라이드](/images/blog/claude-design-pdf-fix-result.webp)

---

## 마무리

Claude Design은 실제로 강력한 슬라이드 제작 도구다. AI가 레이아웃을 잡고, 색상 체계를 설계하고, 텍스트까지 구조화해주니 예전 방식과 비교가 안 된다.

다만 PDF export는 아직 브라우저 렌더링 수준이 아니다. 위 6가지 규칙을 처음부터 지키면 **PDF 깨짐의 90% 이상을 예방**할 수 있다. 이미 완성한 슬라이드라면 사후 수정 프롬프트를 그대로 붙여넣으면 한 번에 전체 수정이 된다.

> "AI가 슬라이드를 만들어주는 시대, 이제는 PDF 깨짐까지 AI가 예방해준다."

임원 보고 전날 밤에 이 프롬프트를 알았더라면 좋았을 텐데.
