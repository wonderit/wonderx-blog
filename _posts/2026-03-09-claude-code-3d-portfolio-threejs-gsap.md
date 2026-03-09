---
title: "Claude Code로 3D 포트폴리오 사이트 만들기 — AI와 페어 프로그래밍한 후기"
description: "Three.js + GSAP로 만든 인터랙티브 CV 사이트 제작기. 빌드 도구 없이 순수 HTML/CSS/JS만으로 3D 배경, 스크롤 애니메이션, 다국어를 구현한 과정을 공개한다."
date: 2026-03-09 11:00:00 +0900
image:
  path: /images/blog/claude-code-3d-portfolio-threejs-gsap-1.webp
  width: 1280
  height: 720
tags: ['포트폴리오', 'Three.js', 'GSAP', 'ClaudeCode', '웹개발', 'GitHub Pages', '개인사이트']
categories: [tutorial]
author: wonder
---

"AI한테 포트폴리오 사이트 만들어달라고 하면 어느 수준까지 가능할까?"

솔직히 말하면 처음엔 기대를 낮게 잡았다. 레이아웃 정도 잡아주면 다행이겠지 싶었다. 결과는 달랐다. Three.js 기반 3D 배경, GSAP 스크롤 애니메이션, 한/영 실시간 전환, 반응형까지 — 대화 몇 세션 만에 실제로 배포까지 완료됐다.

완성된 사이트: **[cv.wonderx.co.kr](https://cv.wonderx.co.kr)**
GitHub: [github.com/wonderit/wonderx-cv](https://github.com/wonderit/wonderx-cv)

이 포스팅은 그 과정을 낱낱이 공개한다. 어디서 막혔고, Claude Code가 뭘 잘했고, 어떤 트러블슈팅이 있었는지까지.

---

## 왜 직접 만들었나 — 기존 포트폴리오 툴의 한계

Notion, Linktree, Cargo 같은 도구들이 있다. 빠르고 편하다. 근데 커스터마이징의 벽이 존재한다. AI 연구자/CTO로서 단순 이력 나열 말고, 내 전문성이 시각적으로 드러나는 사이트를 원했다.

요구사항을 정리해보니 이랬다:

| 요구사항 | 기존 툴 | 직접 제작 |
|---------|--------|---------|
| 3D 인터랙티브 배경 | ❌ | ✅ Three.js |
| 스크롤 기반 애니메이션 | △ 제한적 | ✅ GSAP ScrollTrigger |
| 한/영 실시간 전환 | △ 일부만 | ✅ 커스텀 i18n |
| 논문 목록 + 인용수 | ❌ | ✅ 구조화 직접 설계 |
| 커스텀 도메인 + GA4 | △ 유료 | ✅ GitHub Pages 무료 |

직접 만들기로 결정. 문제는 시간이다. Three.js 풀로 짜면 며칠이다. 여기서 Claude Code가 들어온다.

---

## 기술 스택 — 빌드 도구 없이 CDN만으로

의도적인 선택이었다. Vite, Webpack 같은 번들러를 쓰면 강력하지만 프로젝트 구조가 복잡해진다. 목표는 "유지보수 제로에 가까운 정적 사이트"였다.

```
index.html (단일 파일 기반)
├── Three.js r128 (CDN)
├── GSAP 3.12.5 + ScrollTrigger (CDN)
├── Space Grotesk (Google Fonts)
└── Noto Sans KR (Google Fonts)
```

빌드 스텝이 없다는 건 GitHub Pages에 `git push` 하나로 배포된다는 뜻이다. CI/CD 설정도 불필요.

> 단순함이 최고의 아키텍처다. 복잡한 도구가 필요 없을 때는 쓰지 않는 것이 맞다.

![디자인 컨셉과 기술 스택 구성](/images/blog/claude-code-3d-portfolio-threejs-gsap-2.webp)

---

## 디자인 컨셉 — x.ai 스타일 모노크롬

레퍼런스는 명확했다. x.ai 웹사이트의 다크 모노크롬 미학. 화려한 컬러 없이 거의 블랙 배경에 실버/화이트 계열만 사용한다.

```css
--bg-primary: #080808;      /* 거의 블랙 */
--accent: #c0c0c0;          /* 실버 */
--accent-bright: #ffffff;   /* 하이라이트 화이트 */
--text-primary: #f0f0f0;    /* 본문 */
--text-secondary: #999999;  /* 부제목/설명 */
```

색상 외에 디테일로 분위기를 만들었다:

- **스캔라인 오버레이**: CRT 모니터의 미세한 줄무늬 효과. CSS `repeating-linear-gradient`로 구현
- **글리치 효과**: 이름 텍스트에 적용. `@keyframes`로 미세한 포지션 쉬프트
- **HUD 코너**: 프로필 사진 프레임의 게임 HUD 스타일 모서리 마커
- **홀로그래픽 카드**: 마우스 호버 시 빛이 스치는 `backdrop-filter: blur()` 반투명 카드

세 가지 효과의 조합이 "AI 연구자의 사이트"라는 정체성을 만든다.

---

## 핵심: Three.js 3D 배경 구현

가장 공들인 부분이다. 단순한 파티클 배경이 아니라 **AI 카메라 렌즈/눈 모티프**를 설계했다.

### 렌즈 구조 설계

```
동심원 토러스 링 3겹 (외부 → 중간 → 내부)
       ↓
중앙 동공 (펄스 애니메이션)
       ↓
6개 조리개 블레이드 라인
       ↓
4개 크로스헤어 라인
       ↓
12개 궤도 데이터 노드 (전문 분야 라벨)
```

각 궤도 노드에는 실제 전문 분야 키워드가 HTML 라벨로 표시된다:

```
AI Safety · Vision AI · Privacy ML · Deep Learning
Nanophotonics · Full-Stack · 3D Pose · Encryption
GAN Design · Biomedical · Segmentation · Edge AI
```

### 3D → 2D 좌표 프로젝션

Three.js의 3D 노드 위치를 브라우저 화면의 2D 좌표로 변환해서 HTML `<span>` 라벨을 붙이는 게 핵심 트릭이다.

```javascript
// Three.js 월드 좌표 → 스크린 좌표 변환
node.getWorldPosition(worldPos);
worldPos.project(camera);

var sx = (worldPos.x * 0.5 + 0.5) * window.innerWidth;
var sy = (-worldPos.y * 0.5 + 0.5) * window.innerHeight;

// 궤도 중심에서 바깥 방향으로 라벨 오프셋
var cx = window.innerWidth / 2;
var cy = window.innerHeight / 2;
var dx = sx - cx;
var dy = sy - cy;
var invDist = 1 / (Math.sqrt(dx * dx + dy * dy) || 1);

lbl.style.left = (sx + dx * invDist * LABEL_OFFSET) + 'px';
lbl.style.top  = (sy + dy * invDist * LABEL_OFFSET) + 'px';
```

`getWorldPosition()` + `project(camera)` 조합이 포인트다. 단순히 스크린 좌표만 쓰면 노드와 라벨이 겹친다. 중심에서 바깥 방향 벡터를 계산해서 오프셋을 주면 라벨이 항상 노드 바깥쪽에 위치한다.

![Three.js 3D 씬 — AI 렌즈 모티프와 파티클 네트워크](/images/blog/claude-code-3d-portfolio-threejs-gsap-3.webp)

### 파티클 네트워크

100개의 은색 파티클이 3D 공간에서 떠다니며, 일정 거리 내의 파티클끼리 연결선을 생성한다. 뉴럴 네트워크를 시각화한 느낌이다. 커스텀 GLSL 셰이더로 파티클 렌더링:

```glsl
// Fragment Shader — 파티클 원형 클리핑
void main() {
  float dist = length(gl_PointCoord - vec2(0.5));
  if (dist > 0.5) discard;
  gl_FragColor = vColor * (1.0 - dist * 2.0);
}
```

### 스크롤 반응 패럴랙스

```javascript
window.addEventListener('scroll', function() {
  var progress = window.scrollY / (document.body.scrollHeight - window.innerHeight);
  camera.position.y = -progress * 3;
  camera.position.z = 5 + progress * 2;
  glowOrb.position.y = 2 - progress * 4;
});
```

카메라가 스크롤에 따라 Y축/Z축으로 이동하며 씬이 살아있다는 느낌을 준다. 마우스 움직임에 따른 미세 회전도 추가해서 3D감을 강화했다.

---

## GSAP 애니메이션 시스템

Three.js가 배경을 맡았다면, GSAP은 컨텐츠 레이어를 책임진다. ScrollTrigger(스크롤 위치에 따라 애니메이션을 트리거하는 GSAP 플러그인)를 핵심으로 활용했다.

### Hero 텍스트 순차 등장

```javascript
var heroEls   = ['.hero-greeting', '.hero-name', '.hero-title-bar',
                 '.hero-tagline', '.hero-actions'];
var delays    = [0.3, 0.6, 1.0, 1.3, 1.6];

heroEls.forEach(function(sel, i) {
  gsap.to(sel, {
    opacity: 1, y: 0,
    duration: 0.8,
    delay: delays[i],
    ease: 'power3.out'
  });
});
```

각 요소가 0.3초 간격으로 아래에서 위로 페이드인. 단순한데 효과가 좋다.

### 섹션별 ScrollTrigger

```javascript
gsap.utils.toArray('.timeline-card').forEach(function(card, i) {
  gsap.from(card, {
    scrollTrigger: { trigger: card, start: 'top 80%' },
    x: i % 2 === 0 ? -60 : 60,  // 좌우 교차 슬라이드인
    opacity: 0,
    duration: 0.7,
    delay: i * 0.1
  });
});
```

타임라인 카드가 좌우 교차로 슬라이드인하는 연출. 경력, 세미나 섹션에 동일 패턴 적용.

![GSAP 스크롤 애니메이션과 섹션 레이아웃](/images/blog/claude-code-3d-portfolio-threejs-gsap-4.webp)

---

## i18n — 85개 번역 키로 한/영 전환

```html
<h2 data-i18n="about_title">About</h2>
<p data-i18n="about_desc">내용...</p>
```

```javascript
function applyLang(lang) {
  document.querySelectorAll('[data-i18n]').forEach(function(el) {
    var key = el.dataset.i18n;
    if (translations[lang] && translations[lang][key]) {
      el.textContent = translations[lang][key];
    }
  });
  localStorage.setItem('lang', lang);
  currentLang = lang;
}
```

`data-i18n` 어트리뷰트에 번역 키를 박아두고, 언어 전환 시 전체 DOM을 스캔해서 텍스트를 교체한다. `localStorage`로 설정이 유지된다. 85개 이상의 번역 키 — 논문 제목, 세미나 제목까지 전부 한/영 이중화.

페이지 리로드 없이 실시간 전환이다.

---

## Claude Code와의 실제 개발 과정

### 워크플로우

```
자연어 요구사항 전달
       ↓
Claude가 코드 생성/수정 (전체 파일 단위)
       ↓
preview 도구로 스크린샷 + 콘솔 에러 체크
       ↓
"좀 더 가까이", "점 없애도 될 것 같은데" 피드백
       ↓
git push (Claude가 직접 실행)
```

대화형 개발이라 "디자인 → 피드백 → 수정" 사이클이 매우 빠르다. Three.js 코드를 처음부터 짜는 게 아니라, "AI 카메라 렌즈 느낌의 3D 배경 만들어줘"라고 하면 전체 씬을 생성해준다.

### Claude Code가 잘한 것

| 작업 | 평가 |
|-----|------|
| Three.js 3D 씬 전체 설계 | ⭐⭐⭐⭐⭐ 완성도 높음 |
| GSAP ScrollTrigger 연동 | ⭐⭐⭐⭐⭐ 섹션별 패턴 완벽 |
| i18n 시스템 (85+ 키) | ⭐⭐⭐⭐⭐ 구조 깔끔 |
| 논문 11편 + 인용수 구조화 | ⭐⭐⭐⭐⭐ 반복 작업 탁월 |
| 3D→2D 라벨 프로젝션 | ⭐⭐⭐⭐ 수학 계산 정확 |
| 반응형 CSS | ⭐⭐⭐⭐ 미세 조정 필요 |
| git 커밋/푸시 자동화 | ⭐⭐⭐⭐⭐ |

### 트러블슈팅 3선

**① Hero 텍스트가 안 보이는 문제**

초기에 GSAP `timeline.from()` 체이닝을 썼더니 `requestAnimationFrame` 타이밍 이슈로 텍스트가 invisible 상태로 고정됐다. 해결책: `gsap.to()`를 각 요소별로 개별 호출 + `opacity: 0` 초기 CSS 명시.

**② 라벨-노드 겹침 문제**

3D 노드 위치에 그대로 라벨을 붙이면 텍스트가 원 위에 겹친다. 위에서 설명한 "궤도 중심 기준 바깥 방향 벡터 오프셋" 로직으로 해결. 원의 중심에서 노드 방향으로 단위벡터를 구하고 `LABEL_OFFSET` 픽셀만큼 밀어낸다.

**③ 성능 최적화**

애니메이션 루프에서 `window.innerWidth` 같은 레이아웃 값을 매 프레임 읽으면 Layout Thrashing이 발생한다. 화면 크기를 변수에 캐싱하고, resize 이벤트에서만 업데이트하도록 변경했다.

![Claude Code와의 대화형 개발 과정](/images/blog/claude-code-3d-portfolio-threejs-gsap-5.webp)

---

## 배포 — GitHub Pages + 커스텀 도메인

```
GitHub Repo (wonderit/wonderx-cv)
       ↓
GitHub Pages (자동 배포)
       ↓
CNAME: cv.wonderx.co.kr
```

`CNAME` 파일에 도메인 한 줄, DNS에 GitHub Pages IP 추가. 15분 내 HTTPS 인증서 자동 발급. 추가 비용 없다.

```bash
# GitHub Pages 설정
echo "cv.wonderx.co.kr" > CNAME
git add CNAME && git commit -m "add custom domain"
git push origin main
```

Google Analytics (G-HH3NWMYSQL)도 `<head>`에 스크립트 두 줄로 끝.

---

## 결론 — 이 방법이 맞는 사람은?

솔직하게 정리하면 이렇다.

**이 방법이 맞는 경우:**
- 포트폴리오 사이트에 독창적인 비주얼을 원하는 개발자
- 빠르게 프로토타입하고 싶은데 Three.js 깊이 공부할 시간이 없는 경우
- GitHub Pages 배포로 유지비 0원이 목표인 경우

**이 방법이 안 맞는 경우:**
- 비개발자가 혼자 유지보수해야 하는 경우 (코드 기반이라 진입장벽 있음)
- SEO가 최우선인 경우 (SPA 구조라 SSR 기반 Next.js가 유리)
- 콘텐츠가 자주 바뀌는 경우 (CMS가 더 편함)

Claude Code의 핵심 가치는 **복잡한 라이브러리를 자연어로 제어**할 수 있다는 거다. Three.js 공식 문서를 3일 읽을 시간에, 원하는 씬을 대화로 만들고 코드를 이해하면서 익히는 방식이 훨씬 효율적이다. "개발자는 게을러야 한다"는 말의 현대적 해석이 여기 있다.

결과물은 직접 확인해보길: **[cv.wonderx.co.kr](https://cv.wonderx.co.kr)**

---

**🖼️ 로컬 이미지 생성 설정 (FLUX.1 Schnell / 35GB RAM Optimized)**
- **Model**: Flux.1 [schnell] (GGUF 8-bit)
- **Settings**: 4 Steps | CFG 3.5 | Sampler: Euler
- **Style**: 테크 블로거
- **Mac Efficiency**: 35GB RAM 활용을 위해 Text Encoder를 'Full'로 설정 권장.

**[Hero Image Prompt (16:9)]**
`Dark tech portfolio website on a sleek monitor, Three.js 3D particle network with silver orbiting nodes and camera lens motif, monochrome dark aesthetic, deep space black background with subtle CRT scanline overlay, ambient cool blue-white glow, professional studio lighting, 8k ultra detail, sharp modern typography, the text "Claude Code × 3D Portfolio" glowing in silver` --ar 16:9

**[Body Image 2 Prompt (3:2)]**
`Minimalist dark web design system on dual monitors, CSS color palette swatches in monochrome silver and white against deep black, holographic card with frosted glass blur effect, HUD corner markers, glitch text effect, professional tech studio lighting, cool blue-grey palette, 8k resolution` --ar 3:2

**[Body Image 3 Prompt (3:2)]**
`Three.js 3D scene with glowing concentric torus rings representing AI camera lens, 12 orbiting data nodes with HTML labels floating in 3D space, silver particle network connecting nodes like neural pathways, dark void background, cool cyan accent lighting, technical schematic aesthetic, ultra sharp 8k` --ar 3:2

**[Body Image 4 Prompt (3:2)]**
`GSAP scroll animation timeline visualization, website sections with staggered card animations sliding in from alternating sides, dark mode UI with silver accents, smooth motion blur trails, professional UX design interface, vertical scroll progress indicator, clean developer tool aesthetic, 8k` --ar 3:2

**[Body Image 5 Prompt (3:2)]**
`AI developer coding session with Claude Code CLI on terminal, dark monitor showing conversation history with AI assistant, Three.js code snippets visible, dual screen setup, ambient cool studio lighting, professional developer workspace, subtle blue screen glow, ultra detailed 8k photography style` --ar 3:2
