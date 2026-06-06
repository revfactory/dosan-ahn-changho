# 디자인 시스템 — 도산 안창호 일대기 사이트

> v1.0 (2026-06-06) / 작성: ui-designer (Phase 4a)
> 기준 스킬: `dosan-design-system` (컨셉·토큰·대비표·컴포넌트·사진·반응형의 상위 규범)
> 토큰 구현: `site/css/tokens.css` (이 문서의 토큰표와 1:1 동기화 — §2 검증 규칙)
> 소비자: Phase 4b frontend-developer(전 페이지 스타일링), a11y-engineer(색 대비 감사), timeline/map-developer(시각화)
> 입력: `sitemap.md`·`page_specs/00~10`·`images/manifest.json`(80건)·`synthesis/*`(콘텐츠 성격)

이 문서는 **frontend-developer가 픽셀 단위 추측 없이** 페이지를 구현하도록 모든 시각 결정을 수치로 고정한다. "은은한 베이지"가 아니라 `--paper: #F7F3EB`, "적당한 여백"이 아니라 간격 스케일 토큰이다. 토큰 외부 하드코딩 색/크기는 계약 위반이다.

---

## 0. 작업 계약 — 경로·네이밍

- **tokens.css 경로**: `site/css/tokens.css` — **architecture.md v0.9 §4 계약으로 확정**. CSS 디렉토리는 `site/css/`이고 `assets/`는 이미지 전용(`site/assets/images/`). 파일 분할은 `css/tokens.css`(ui-designer 단독 소유) + `css/main.css`(frontend-developer 소유, tokens 변수 소비). team-lead 지시문의 `site/assets/css/`는 채택되지 않음 — architecture.md 계약이 우선이라 `site/css/`로 동결한다.
- **클래스 네이밍 규약** (소유·확정: ui-designer / 충돌 방지 골격: web-architect 합의 — architecture.md §4가 ui-designer에 위임한 항목): 단순 케밥 케이스, BEM `__` 변형 미사용. 컴포넌트 루트는 의미 명사, 자식은 컴포넌트 스코프 안의 의미 클래스(`.event-card .card-date` — `루트__요소` 안 씀).
  - **모듈 스코프 접두** (web-architect 확정 규약 — architecture.md §4 규칙8·D-15; timeline.js·map.js·관계망 그래프·일반 페이지가 main.css 네임스페이스를 공유하므로 필수): **공통 컴포넌트는 무접두 케밥**(`.card`·`.badge`·`.grade-badge`·`.person-card`·`.quote-block`·`.data-table` 등 — 전 페이지 공유), **연표 전용 `tl-`**(`.tl-event-card`·`.tl-filter`·`.tl-period-track`), **지도 전용 `map-`**(`.map-marker-popup`·`.map-route-caption`), **people 관계망 그래프 전용 `nw-`**(`.nw-graph`·`.nw-node`·`.nw-edge`). 모듈 접두 3종(`tl-`/`map-`/`nw-`) 확정. 본 문서 §6 컴포넌트 중 모듈 전용 시각화 내부 클래스에는 해당 접두를 적용하고, 등급 배지·인용 블록·인물 카드 등 페이지 공유 컴포넌트는 무접두로 둔다.
  - **상태 클래스**: `is-`/`has-` 접두(`.is-disputed`·`.is-current`·`.has-image`).
  - **JS 훅**: 스타일과 분리해 `data-*` 속성 권장(web-architect 규약 — 클래스 오염 방지). 예: `data-period="P3"`·`data-disputed="true"`. 스타일 클래스를 JS 셀렉터로 재사용하지 않는다.
  - 유틸리티는 최소화하고 토큰 직접 참조 우선. main.css(frontend-developer 소유)·timeline.js·map.js가 본 규약을 따른다.
- **CSS 변수 참조 원칙**: 컴포넌트는 §1 시맨틱 별칭(`--bg`, `--text`, `--accent` 등)만 참조하고 원시 색(`--paper`, `--dancheong`)을 직접 쓰지 않는다 — 톤 조정 시 별칭 한 곳만 바꾸면 되도록.

---

## 1. 디자인 컨셉 — 무실역행의 절제

### 컨셉 진술 (모든 토큰 결정의 정박점)

> **이 사이트의 시각 언어는 도산의 무실역행(務實力行) 정신과, 이 사이트의 고유한 편집 윤리 — 검증 등급·상충·공백의 정직한 공개 — 를 한 몸으로 번역한다. 꾸밈없이 실질을 다하고(務實) 묵묵히 실행한다(力行)는 정신은 화면에서 "여백이 위계이고, 텍스트가 주인공이며, 강조색은 인장처럼 한 번만 찍는" 절제로 나타난다. 그리고 이 사이트가 다른 위인 사이트와 다른 점 — '확실한 것과 불확실한 것을 같은 화면에서 구분해 보여준다' — 는 시각의 핵심 과제다. 등급 배지·disputed 표시·한정 문형·공백 고지가 본문에서 시각적으로 읽혀야 하며, 동시에 본문 독해를 방해하지 않아야 한다. 화려한 효과는 도산을 말하는 것이 아니라 도산을 가리고, 불확실을 확실처럼 보이게 꾸미는 것은 이 사이트의 윤리를 배신한다.**

콘텐츠 성격 근거(synthesis 확인): life.md만 보아도 모든 사실 문장에 `[clm-]/[evt-]/[cfl-]` 근거 식별자가 붙고, C등급은 "~로 전해진다" 한정 문형을 유지하며, 상충은 양론 병기된다. 즉 **정직성이 콘텐츠의 1차 가치**이고, 디자인은 이 정직성을 가시화하되 우아하게 절제해야 한다.

### 컨셉 2안 비교 (반성성 — 자기 평가 후 1안 선택)

| 축 | **A안 — "한지 위의 사료"** (채택) | B안 — "먹빛 아카이브" (기각) |
|----|-----------------------------------|------------------------------|
| 바탕 | 한지 베이지(`--paper #F7F3EB`) 라이트 모드. 종이 위에 글을 읽는 은유 | 짙은 먹빛 다크 모드. 박물관 전시 조명 은유 |
| 정서 | 차분·학술적·따뜻함. 장시간 독해 친화 | 극적·엄숙·대비 강함 |
| 이미지 정합 | 흑백/세피아 92% 사료가 밝은 한지 위에서 자연스럽게 안착(원본 톤과 충돌 적음) | 저해상 흑백 초상이 어두운 배경 위에서 경계가 흐려지고 노이즈가 도드라짐 |
| 검증 윤리 정합 | "정직한 종이 문서"의 은유 — 등급 배지·각주가 학술 문서처럼 읽힘 | 극적 연출이 "불확실을 분위기로 덮을" 위험 — 컨셉 진술과 충돌 |
| 가독성·접근성 | 밝은 바탕 위 먹 텍스트 16:1, 장문 한글 안전 | 다크 모드 장문 한글은 글레어·번짐 위험, 본문 길이(life 16,000자)에 불리 |
| 강조색 작동 | 단청 빨강이 밝은 바탕에서 "인장"처럼 명료 | 어두운 바탕에서 단청 빨강이 탁해지거나 형광처럼 떠 보임 |

**선택: A안.** 기각 사유 — B안은 (1) 80건 중 92%가 흑백/세피아 저해상 사료라는 이미지 제약상 어두운 배경에서 시각 품질이 떨어지고, (2) life 16,000자 등 장문 한글 본문에 다크 모드가 가독성상 불리하며, (3) 무엇보다 "극적 연출"이라는 정서가 **불확실을 분위기로 덮는** 방향이라 이 사이트의 검증 윤리 컨셉과 정면 충돌한다. A안은 도산의 절제 정신과 사이트의 정직성을 둘 다 자연스럽게 담는다. (다크 모드는 향후 `prefers-color-scheme` 토큰 분기로 별도 검토 가능하나 v1은 라이트 모드 단일로 확정 — 토큰을 시맨틱 별칭으로 설계해 분기 여지를 남겼다.)

### 컨셉을 토큰으로 — 네 가지 번역 규칙

1. **여백이 위계다.** 구분선·박스·그림자 대신 간격 스케일(`--sp-*`)로 위계를 만든다. 섹션 구분은 `--sp-7`/`--sp-8` 여백, 카드 분리는 `--sp-5` 패딩. 선(`--border`)과 그림자(`--shadow-*`)는 최후 수단.
2. **정직한 타이포.** 본문 세리프(`--font-serif`), UI 산세리프(`--font-sans`). 디스플레이 폰트 없음. 텍스트가 주인공.
3. **장식 최소.** 그라디언트·글로우·과한 애니메이션 금지. 모션은 의미(시간 흐름·경로 이동) 전달 시에만(`--dur-slow`). 그림자는 팝업에만(`--shadow-pop`).
4. **강조 1색 원칙.** 단청 빨강(`--accent`)은 한 화면에 1~2회. 링크·현재 위치·핵심 강조에만. 등급 배지·필터·일반 UI에는 청자/먹 계열을 쓰고 단청을 남용하지 않는다(§2 검증 4항).

---

## 2. 컬러 토큰과 WCAG AA 대비 검증표

### 토큰표 (tokens.css §1~3과 동기화)

| 토큰 | 값 | 역할 |
|------|-----|------|
| `--paper` | `#F7F3EB` | 기본 배경(한지) |
| `--paper-dim` | `#EFE8DB` | 카드·인용 블록 배경 |
| `--paper-edge` | `#E2D9C7` | 구분선·테두리(`--border`) |
| `--ink` | `#1A1815` | 본문 텍스트(`--text`) |
| `--ink-soft` | `#4A453E` | 보조 텍스트(`--text-muted`) |
| `--ink-faint` | `#6B655B` | 비활성·플레이스홀더(`--text-faint`) — 큰/UI 텍스트 권장 |
| `--dancheong` | `#B5342B` | 강조·링크·현재 위치(`--accent`) |
| `--dancheong-dim` | `#9A2C24` | hover/active(`--accent-hover`) |
| `--celadon` | `#6E8B74` | 비텍스트 UI·큰 제목 보조·테두리(`--rule`) |
| `--celadon-deep` | `#4E6854` | 청자색 본문 텍스트 불가피 시(`--rule-text`) |
| `--on-accent` | `#FFFFFF` | 단청 배경 위 텍스트 |
| `--grade-a-text` | `#2F5D3A` | A등급 배지 글자 |
| `--grade-b-text` | `#4A453E` | B등급 배지 글자(먹 보조) |
| `--grade-c-text` | `#8A5A00` | C등급(한정) 배지 글자(황토) |
| `--loc-confirmed` | `#4E6854` | 사료 소재 확인 |
| `--loc-cited` | `#8A5A00` | 인용만 확인(cited_only) |
| `--loc-unlocated` | `#6B655B` | 소재 미확인 |

### WCAG AA 대비표 (실측 — WebAIM 공식, 본 문서 작성 시 계산기로 검증)

| 전경 / 배경 | 대비율 | 본문 AA (≥4.5) | 큰글씨·UI AA (≥3.0) | 용도 |
|---|---|---|---|---|
| `--ink` / `--paper` | **16.01:1** | 통과(AAA) | 통과 | 본문 기본 |
| `--ink` / `--paper-dim` | **14.54:1** | 통과(AAA) | 통과 | 카드 본문 |
| `--ink-soft` / `--paper` | **8.58:1** | 통과(AAA) | 통과 | 캡션·메타 |
| `--ink-soft` / `--paper-dim` | **7.79:1** | 통과(AAA) | 통과 | 카드 내 메타 |
| `--ink-faint` / `--paper` | **5.22:1** | 통과 | 통과 | 비활성·플레이스홀더 |
| `--ink-faint` / `--paper-dim` | **4.74:1** | 통과 | 통과 | 카드 내 미확인 라벨 |
| `--dancheong` / `--paper` | **5.44:1** | 통과 | 통과 | 링크·강조 |
| `--dancheong` / `--paper-dim` | **4.94:1** | 통과 | 통과 | 카드 내 링크 |
| `--dancheong-dim` / `--paper` | **6.88:1** | 통과 | 통과 | 링크 hover |
| `#FFFFFF` / `--dancheong` | **6.02:1** | 통과 | 통과 | 강조 버튼 |
| `#FFFFFF` / `--dancheong-dim` | **7.61:1** | 통과 | 통과 | 버튼 hover |
| `--celadon` / `--paper` | **3.38:1** | **불통과** | 통과 | 큰 제목(24px+)·테두리·아이콘만 |
| `--celadon` / `--paper-dim` | **3.07:1** | **불통과** | 통과 | 카드 테두리·비텍스트만 |
| `--celadon-deep` / `--paper` | **5.53:1** | 통과 | 통과 | 청자색 본문 텍스트(불가피 시) |
| `--celadon-deep` / `--paper-dim` | **5.02:1** | 통과 | 통과 | 카드 내 청자 텍스트 |
| `--grade-a-text` / `--paper-dim` | **6.27:1** | 통과 | 통과 | A등급 배지(카드 위) |
| `--grade-a-text` / `--paper` | **6.91:1** | 통과 | 통과 | A등급 배지(본문 위) |
| `--grade-c-text` / `--paper-dim` | **4.86:1** | 통과 | 통과 | C등급 배지(카드 위) |
| `--grade-c-text` / `--paper` | **5.36:1** | 통과 | 통과 | C등급 배지(본문 위) |
| `--loc-confirmed` / `--paper-dim` | **5.02:1** | 통과 | 통과 | 소재 확인 배지 |
| `--loc-cited` / `--paper-dim` | **4.86:1** | 통과 | 통과 | cited_only 배지 |
| `--loc-unlocated` / `--paper-dim` | **4.74:1** | 통과 | 통과 | 소재 미확인 배지 |
| `--dancheong` / `--ink` | 2.94:1 | **불통과** | **불통과** | **금지 조합** |

**규칙 (a11y-engineer 감사 기준):**
- 표의 모든 "통과" 조합만 사용 가능. 표에 없는 조합은 미검증 — 도입 전 실측 후 표를 갱신하라.
- `--celadon`은 **본문 크기 텍스트 절대 금지** — 18.66px bold 또는 24px+ 큰 텍스트, 테두리·아이콘·비텍스트 UI만. 청자색을 본문 글자로 써야 하면 `--celadon-deep`(`--rule-text`)을 쓴다.
- **금지 조합**: `--dancheong` 텍스트를 `--ink` 계열 어두운 배경 위에 두지 마라(2.94:1). 단청은 한지 위에서만 강조로 작동한다.
- **등급/소재 배지는 색 단독 의존 금지** — 항상 라벨 텍스트("A등급", "기록 상충", "소재 미확인")를 병기한다(색각 이상 대응, §6 컴포넌트 스펙).

---

## 3. 타이포그래피

### 폰트 스택 (tokens.css §4)
- `--font-serif: "Noto Serif KR", "Nanum Myeongjo", serif` — 제목·본문(읽는 것)
- `--font-sans: "Pretendard", "Apple SD Gothic Neo", system-ui, sans-serif` — UI·메타·캡션(조작하는 것)
- `--font-mono` — id·좌표·날짜 raw 표기

**폰트 로드 규칙:** Google Fonts(Noto Serif KR) + Pretendard CDN을 `display=swap`으로 로드하고 시스템 폰트 폴백을 항상 유지한다. 폰트 로드 실패가 빈 텍스트가 되어서는 안 된다. **폰트 가용성 확인은 Phase 4b 구현 시 수행** — CDN 응답 미확인 상태이므로 위 폴백 스택(`Nanum Myeongjo`/`Apple SD Gothic Neo`/system)을 항상 둔다.

### 크기 스케일 (1.25배 모듈러 — 임의 px 금지)
| 토큰 | 값 | 용도 | 글꼴 | 행간 |
|------|-----|------|------|------|
| `--fs-3xl` | 3.052rem | 홈 히어로 사이트명(데스크톱, 단일) | serif | `--lh-tight` |
| `--fs-2xl` | 2.441rem | h1 페이지 제목 | serif | `--lh-tight` |
| `--fs-xl` | 1.953rem | h2 섹션 | serif | `--lh-tight` |
| `--fs-lg` | 1.563rem | h3 | serif | `--lh-tight` |
| `--fs-md` | 1.25rem | h4 소제목·카드 제목 | serif | `--lh-snug` |
| `--fs-base` | 1rem (root 18px) | 본문 | serif | `--lh-body` (1.8) |
| `--fs-sm` | 0.8rem | 캡션·크레딧·UI 라벨·날짜 | sans | `--lh-snug` |
| `--fs-xs` | 0.694rem | 배지·미세 메타 | sans | `--lh-snug` |

**규칙:**
- 본문 폭 `--measure: 42rem` (한 줄 35~45자) 초과 금지 — 모든 뷰포트에서. 넓은 화면 본문 신장은 가독성 결함.
- 본문 행간 `--lh-body: 1.8` (한글 장문). 제목 `--lh-tight: 1.3`.
- 한자 병기는 본문과 **같은 글꼴·크기**로 괄호 안에 — `안창호(安昌浩)`. 한자만 작게 줄이지 않는다.
- 한글 이탤릭 금지(가짜 기울임). 강조는 굵기(font-weight)나 `--accent` 색으로.

---

## 4. 레이아웃·그리드·반응형

### 모바일 우선 브레이크포인트 (tokens.css는 미디어쿼리 비포함 — 컴포넌트 CSS에서 사용)
```css
/* 기본 = 모바일 (360px+) — 단일 컬럼 */
@media (min-width: 640px)  { /* 태블릿: 2단 카드 그리드 */ }
@media (min-width: 1024px) { /* 데스크톱: 본문 + 사이드 내비/목차 */ }
```
- **모바일 우선** 필수 — 기본 CSS가 360px에서 동작하고 확장은 추가만. 검증 뷰포트 3종: **360 / 768 / 1280px**.
- 폭 토큰: 본문 `--measure`(42rem), 카드 그리드 `--measure-wide`(60rem), 페이지 셸 `--measure-full`(75rem).
- 카드 그리드: 모바일 1열 → 640px 2열 → 1024px 2~3열(`repeat(auto-fill, minmax(16rem, 1fr))` 권장).

### 페이지 골격 (sitemap §2 — 전 페이지 공통)
```
공통 헤더(사이트명 + 전역 내비 10항목)
  → 페이지 헤더(h1 + 한 줄 소개)
    → 본문 섹션들 (본문 폭 --measure 중앙 정렬)
      → 공통 푸터 (참고문헌·사료·검증 방법론 링크)
```

### 전역 내비 10항목 모바일 처리 (sitemap §1이 ui-designer에 명시 이관한 결정)
- **데스크톱(1024px+)**: 10항목 가로 1줄 노출. 항목 간격 `--sp-4`, 산세리프 `--fs-sm`. 현재 페이지는 `--accent` 색 + `aria-current="page"` + 하단 2px 단청 보더(색 단독 의존 금지).
- **태블릿(640~1023px)**: 10항목을 2줄 가로 배치 또는 가로 스크롤 허용. 폰트 `--fs-sm` 유지.
- **모바일(<640px)**: 햄버거 토글 → 세로 목록 오버레이(`--z-overlay`). 토글 버튼 최소 44×44px 터치 타깃. 오버레이 배경 `--paper`, 항목 `--text`, 현재 항목 `--accent`. `aria-expanded` 토글, ESC 닫힘, 포커스 트랩은 a11y-engineer와 협의. 비JS 폴백: `<details>` 요소로 토글하거나 앵커 점프 메뉴 상시 노출.
- 내비 마크업은 공통 모듈 한 곳에서만 정의(sitemap §2). 푸터에 참고문헌·사료·`references.html#methodology` 링크 의무.

---

## 5. 사진 처리

### 통일 톤 (CSS filter — 원본 비변형)
- 시대 사진은 **흑백 통일 톤**으로 처리해 출처가 제각각인 80건의 시각 일관성을 만든다. 원본이 세피아·변색이어도 동일 필터.
- 처리는 CSS `filter: var(--img-filter)`(= `grayscale(1) contrast(1.02)`)로 — 원본 파일 비변형이라 사료 원본성 보존, 정책 변경 시 토큰 한 줄 수정.
- 한지 배경과의 조화를 위해 미세 따뜻함이 필요하면 `--img-filter-warm`(`grayscale(0.92) sepia(0.08)`)을 대안 토큰으로 둔다 — **기본은 `--img-filter`**, 갤러리에서 톤 비교 후 frontend-developer가 택일.
- hover 시 `filter: grayscale(0)` 같은 컬러 복원 효과 금지(장식 최소 원칙 + 흑백 통일의 일관성 훼손).

### 캡션·크레딧·alt (manifest.json 사용 — 임의 작성 금지)
- 모든 `<img>`에 `<figcaption>`: manifest의 `caption`(사실 캡션+연대) + `credit`(출처) 그대로. 임의 작성·윤문 금지.
- 모든 `<img>`에 의미 있는 `alt` 필수 — manifest `caption` 기반. **이 사이트에 장식 이미지는 없다. 모든 이미지가 사료다.**
- 라이선스 표기: `credit` 외에 manifest `license`를 갤러리 카드 메타에 노출(예: "Public Domain").

### 해상도 제약 (visual-curator 인계 + manifest 실측)
- **manifest.json에는 dimensions/width/height 필드가 없다** — 해상도는 일부 이미지 `notes`에만 자연어로 있다(예: dosan-portrait-1919 `550×696`, 1920s 초상 `160×215`·`120×156`). 따라서 CSS는 **고정 px 크기를 박지 말고** 컨테이너 기준 `max-width: 100%; height: auto`로 두고, 작은 원본이 확대되어 깨지지 않게 슬롯 최대 표시폭을 제한한다.
- **type별 권장 표시 크기**(manifest type 분포: portrait 24·group_photo 18·place 15·photo 9·document 7·newspaper 5·artifact 1·artwork 1):
  - `portrait`(저해상 다수, 최고 550×696): 소형 카드/썸네일 **최대 표시폭 280px**. 인물 카드·연표 썸네일·인물 페이지 단독 초상.
  - `group_photo`·`place`·`photo`: 본문 인라인 **최대 360~480px**(원본 해상도 허용 범위 내).
  - `document`·`newspaper`: 사료 뷰어/문서 카드에서 **최대 480px**, 확대 보기(클릭→`--z-overlay`)는 고해상 스캔(12건)에 한정.
- **히어로 풀블리드 금지** (visual-curator 명시): img-home-01은 550×696이 최고 해상도. 홈 히어로는 **프레임형/분할형** 레이아웃으로 — 초상을 우측 프레임(최대 280~320px)에 두고 좌측에 사이트명+정의. 전면 배경 확대(`background-size: cover`) 금지.
- 시기 띠 배경(img-home-02~04)은 저해상 이미지의 전면 배경 사용을 피하고, **장식적 배경 대신 작은 썸네일 카드 + 시기 라벨** 구성을 권장(저해상 풀블리드는 노이즈가 두드러진다).

---

## 6. 컴포넌트 스펙

각 컴포넌트는 **HTML 구조 예시 + 적용 토큰**을 병기한다. frontend-developer는 이 구조를 복사해 쓰고, 클래스명은 §0 케밥 규약을 따른다. 색은 시맨틱 별칭만 참조한다.

### 6.1 등급 배지 (grade-badge) — A/B/C 신뢰도

색 단독 의존 금지 — **반드시 등급 문자 + 라벨 텍스트** 병기. 연표·인물·조직·사료 카드 공통.

```html
<span class="grade-badge is-grade-a" aria-label="신뢰도 A등급">
  <span class="grade-letter">A</span><span class="grade-text">검증</span>
</span>
```
- 칩 배경 `--grade-badge-bg`(=`--paper`), 테두리 `--bw-hair solid --grade-badge-border`, 반경 `--radius-sm`, 패딩 `--sp-1 --sp-2`, 글꼴 `--font-sans --fs-xs`.
- A: 글자 `--grade-a-text`(#2F5D3A). B: `--grade-b-text`(`--ink-soft`). C: `--grade-c-text`(#8A5A00).
- **C등급 배지는 "한정" 라벨**을 둘 수 있으나, 본질적 표시는 본문의 한정 문형("~로 전해진다")이다(00_common §2). 배지는 보조.
- D등급 배지는 **존재하지 않는다** — D는 site/data로 내보내지 않음(timeline.json D 7건 필터, sitemap §6).

### 6.2 disputed 마크 — "기록 상충"

색만으로 구분 금지(스킬 §4). **단청 점선 테두리 + 명시 라벨 + dispute_note 동반**.

```html
<article class="tl-event-card is-disputed" data-disputed="true">
  <span class="disputed-flag" aria-label="기록이 상충하는 사건">⚑ 기록 상충</span>
  ...카드 본문...
  <p class="dispute-note">결성 시점은 1907년 4월(통설)과 ~ 기록이 갈린다. [ref:cfl-015]</p>
</article>
```
- `.is-disputed` 카드: `border: 1px dashed var(--disputed)` (=단청 점선), 그 외 카드는 실선/무테. `.is-disputed`·`.disputed-flag`·`.dispute-note`는 연표·인물·조직·사료 카드 공통 상태이므로 **무접두 공유 클래스**(JS는 `data-disputed` 훅).
- `.disputed-flag`: `--font-sans --fs-xs`, 글자 `--dancheong`, 아이콘(⚑/△) + 텍스트.
- `.dispute-note`: `--text-muted --fs-sm`, 카드 하단. dispute_note 또는 synthesis 각주 노출 의무(sitemap §6, disputed 17건 전건).

### 6.3 연표 사건 카드 (tl-event-card)

데이터 바인딩(timeline.json, timeline.js 소유) — 문안 작성 불요. precision 반영 날짜 표기. **모듈 전용이므로 `tl-` 접두**(web-architect 규약); 내부의 `.grade-badge`·`.ref-link`는 공유 컴포넌트라 무접두.

```html
<article class="tl-event-card" id="evt-shin-005" data-period="P3">
  <time class="card-date" datetime="1907-04">1907-04</time>   <!-- precision: month -->
  <h3 class="card-title">신민회 결성</h3>
  <p class="card-summary">…timeline.json summary 원문 그대로…</p>
  <dl class="card-meta">
    <div><dt>장소</dt><dd>서울 <span class="place-modern">(현 서울)</span></dd></div>
  </dl>
  <div class="card-tags">
    <span class="grade-badge is-grade-b">…</span>
    <a class="actor-link" href="people.html#per-017">양기탁</a>
    <a class="org-link" href="organizations.html#org-006">신민회</a>
  </div>
  <div class="card-links">
    <a href="life.html#ch-06">이 시기 생애 보기</a>
    <a href="map.html#evt-shin-005">지도에서 보기</a>   <!-- 좌표 보유 시만 -->
    <a class="ref-link" href="references.html#src-aca-001">[출처]</a>
  </div>
</article>
```
- 카드 배경 `--bg-raised`, 패딩 `--sp-5`, 반경 `--radius-md`, 카드 간 간격 `--sp-4`. 그림자 없음(여백으로 분리).
- `.card-date`: `--font-mono`(또는 sans) `--fs-sm` `--text-muted`. precision 표기: day→YYYY-MM-DD, month→YYYY-MM, year→YYYY, range→"YYYY-MM~YYYY-MM"(03_timeline §2). **range를 단일 일자로 평탄화 금지.**
- `.card-title`: serif `--fs-md` `--text`. `.card-summary`: serif `--fs-base` `--text`, `--lh-snug`.
- 링크는 모두 `--accent`. 한 카드 안에 단청 링크가 많아도, 단청은 "강조 1색"이지 "링크 금지색"이 아니다 — 다만 카드 컨테이너 자체에는 단청을 칠하지 않는다(§2 검증 4항: 화면당 단청 면적 절제).

### 6.4 인물 카드 (person-card)

```html
<article class="person-card has-image" id="per-005">
  <figure class="person-photo">
    <img src="…" alt="…manifest caption…" style="filter:var(--img-filter)">
  </figure>
  <div class="person-body">
    <h3 class="person-name">이혜련<span class="hanja">(李惠鍊)</span></h3>
    <p class="person-life">1884–1969</p>
    <p class="relation-label">관계: 가족</p>     <!-- 텍스트 라벨 — 색 코딩만 금지 -->
    <p class="person-summary">독립운동가, 2008 건국훈장 애족장. …</p>
  </div>
</article>
```
- 사진 없으면 `.person-card` (`.has-image` 미부착) → **이니셜 플레이스홀더**(§7 경계 상황).
- `.person-name` serif `--fs-md`, 한자 병기 동일 크기. `.relation-label`은 **텍스트 라벨**(관계 유형 6종: 가족/스승/동지/갈등/조직소속/후원) — 색상 코딩만으로 표현 금지(스킬 §4).
- 사진 표시폭 portrait 기준 최대 280px(§5).

### 6.5 인용 블록 (quote-block) — 사료 원문

philosophy §8 허용분 + 동시대 게재본만(06_philosophy 규칙). 한글 이탤릭 금지.

```html
<blockquote class="quote-block">
  <p class="quote-text">…원문 인용…</p>
  <footer class="quote-source">— 안도산전서 수록본에 따름 [ref:src-pri-006]</footer>
</blockquote>
```
- 배경 `--bg-raised`, **좌측 보더 `--bw-accent`(3px) `--rule`(청자)**, 패딩 `--sp-5`, 본문 폭 내.
- `.quote-text` serif `--fs-md` `--text`, 이탤릭 금지. `.quote-source` sans `--fs-sm` `--text-muted` 하단.

### 6.6 사료 뷰어 (source-viewer) — 원문·전사·현대어 3단

무엇이 원문이고 무엇이 해석인지 시각 구분(스킬 §4, archives). 각 단 라벨 명시.

```html
<section class="source-viewer">
  <div class="sv-pane sv-original">
    <h4 class="sv-label">원문 이미지</h4>
    <figure><img src="…" alt="…" style="filter:var(--img-filter)"><figcaption>…</figcaption></figure>
  </div>
  <div class="sv-pane sv-transcription">
    <h4 class="sv-label">전사(轉寫)</h4><p>…</p>
  </div>
  <div class="sv-pane sv-modern">
    <h4 class="sv-label">현대어 풀이</h4><p>…</p>
  </div>
</section>
```
- 모바일 세로 스택, 768px+ 가로 3단 또는 원문 좌/텍스트 우 2단. 각 `.sv-label`은 sans `--fs-sm` `--text-muted`, 위에 `--rule` 1px 상단 보더로 단 구분.
- "원문"과 "해석(현대어)"의 시각 구분: 현대어 단 배경 `--bg`(밝게), 전사 단 `--bg-raised`. **해석을 원문처럼 보이게 하지 않는다**(컨셉 — 불확실/해석을 확실처럼 꾸미지 않음).

### 6.7 사료 소재 상태 배지 (loc-badge) — confirmed/cited_only/unlocated

```html
<span class="loc-badge is-loc-unlocated">소재 미확인</span>
```
- confirmed → `--loc-confirmed`(청자딥) "소재 확인" / cited_only → `--loc-cited`(황토) "인용만 확인" / unlocated → `--loc-unlocated`(흐린 먹) "소재 미확인".
- 색 단독 금지 — 라벨 텍스트 필수. 칩 스타일은 grade-badge와 동일(배경 `--paper`, 테두리 `--border`, `--fs-xs`).

### 6.8 채택하지 않은 전승 블록 (excluded-tradition) — archives #excluded-traditions

D등급 객체 주장을 사실 문형으로 풀지 않음(메타 문형만, 08_archives 규칙). 시각적으로 **본문과 구분**해 "이것은 채택되지 않은 전승"임을 알린다.

```html
<div class="excluded-tradition">
  <p class="et-flag">채택하지 않은 전승</p>
  <p>…"~라는 일화가 후대 기록에 전해지나 동시대 사료에서 확인되지 않는다" [ref:clm-0282]</p>
</div>
```
- 배경 `--bg-raised`, 좌측 보더 `--bw-accent` `--rule-text`(청자딥 — 단청 아님; 강조색 절제), `.et-flag`는 sans `--fs-sm` `--text-muted` 굵게. 인용 형식(blockquote) 사용 금지(어록 자구 비노출).

### 6.9 탐색 카드·시기 카드 (nav-card / period-card) — 홈

```html
<a class="nav-card" href="timeline.html">
  <h3 class="nav-card-title">연표</h3>
  <p class="nav-card-desc">사건 165건의 인터랙티브 연표</p>
</a>
```
- 9장 그리드: 모바일 1열 → 640px 2열 → 1024px 3열. 카드 배경 `--bg-raised`, 패딩 `--sp-5`, 반경 `--radius-md`. hover 시 보더 `--rule` 또는 미세 `--shadow-sm`(택1, 둘 다 금지).
- 데이터 규모 수치(165 등)는 **데이터 파일 메타에서 바인딩**(01_home — 집계 재계산 금지). 시기 카드(P1–P8)는 `life.html#ch-XX` 직링크.

### 6.10 검증 통계 박스 (stats-box) — 홈

```html
<div class="stats-box">
  <div class="stat"><span class="stat-num">305</span><span class="stat-label">검증 주장</span></div>
  <div class="stat"><span class="stat-num">17</span><span class="stat-label">기록 상충</span></div>
  ...
  <a class="stats-link" href="references.html#methodology">검증 방법론 보기</a>
</div>
```
- `.stat-num` serif `--fs-xl` `--text`, `.stat-label` sans `--fs-sm` `--text-muted`. 단청은 통계 박스에 쓰지 않고 methodology 링크에만(강조 1색).

### 6.11 관계망 그래프 범례·폴백 (people #graph) — frontend 소유 vanilla SVG, `nw-` 접두 확정

관계망 그래프는 people.html 전용 시각화로 **frontend-developer가 main.css·vanilla SVG로 구현**한다(라이브러리 없음 — architecture.md D-09). 모듈 전용 클래스는 **`nw-` 접두 확정**(architecture.md §4 규칙8·D-15): `.nw-graph`(루트)·`.nw-node`·`.nw-edge`·`.nw-edge-legend`·`.nw-detail-panel` 등. ui-designer는 아래 **시각 토큰**을 제시하고, frontend가 이 토큰으로 nw- 클래스를 칠한다.
- **노드 형태**(색 단독 금지): 인물 = 원, 조직 = 사각(또는 둥근 사각). 노드 크기 스케일 — 기본 반지름 8px, 연결 차수 강조 시 최대 16px(2배 이내, 과장 금지). 노드 채움 `--bg-raised`, 테두리 `--rule`(청자) `--bw-hair`, 라벨 sans `--fs-xs` `--text`.
- **엣지 6종**(membership/comrade/family/conflict/mentor/patron) 범례 — **conflict는 comrade와 동등 시각 비중**(회색·숨김 금지, 07_people). 선 색은 청자/먹 계열(`--rule`/`--ink-faint`), 유형 구분은 **패턴(실선/점선/파선) + 범례 텍스트 라벨**으로(색 단독 의존 금지). 선 두께 `--bw-hair`(1px) 기본, "현재 선택" 엣지만 `--bw-accent`(3px) + `--accent`(단청 1색).
- **상세 패널**(`.nw-detail-panel`): evidence_event_ids → `timeline.html#evt-…` 링크(`--accent`). 패널 배경 `--bg-raised`, `--shadow-pop` 허용(부유 패널), `--z-popup`.
- **비JS 폴백**: 노드·관계 목록 테이블(interactive-viz 스킬). 테이블 스타일은 §6.13 데이터 테이블(공유 무접두 `.data-table`) 따름.

### 6.11b 지도 마커 팝업·경로 캡션 (map) — map.js 소유, `map-` 접두

```html
<div class="map-marker-popup" id="evt-shin-019">
  <h4 class="card-title">…제목…</h4>
  <time class="card-date">1910-XX</time>
  <p class="card-summary">…summary 1~2문장…</p>
  <span class="grade-badge is-grade-b">…</span>   <!-- 공유 컴포넌트 무접두 -->
  <a class="ref-link" href="timeline.html#evt-shin-019">연표에서 보기</a>
</div>
<figcaption class="map-route-caption">R3 망명 대장정 (1910–1911) …근거 사건 좌표만 연결… [ref:…]</figcaption>
```
- 팝업: `--bg` 배경, `--shadow-pop`(팝업만 그림자 허용), 반경 `--radius-md`, 패딩 `--sp-4`, `--z-popup`. 등급 배지·disputed 규칙은 연표와 동일(04_map §2).
- 경로 폴리라인 색: 청자/먹 계열, "현재 선택 경로"만 단청. 경로 캡션은 sans `--fs-sm` `--text-muted`. 모션은 의미 있는 이동에만 `--dur-slow`.

### 6.12 갤러리 그리드·이미지 카드 (gallery)

```html
<figure class="image-card" id="dosan-portrait-1919">
  <img src="…" alt="…" style="filter:var(--img-filter)" loading="lazy">
  <figcaption>
    <p class="img-caption">…manifest caption…</p>
    <p class="img-meta"><span class="img-date">1919</span> · <span class="img-period">P5</span>
       · <span class="img-license">Public Domain</span></p>
    <p class="img-backlinks">이 이미지가 쓰인 곳:
       <a href="life.html#ch-09">생애 9장</a></p>
  </figcaption>
</figure>
```
- 그리드 `repeat(auto-fill, minmax(15rem, 1fr))`, 간격 `--sp-4`. 시기(P1–P8)·유형(사진/문서) 필터는 산세리프 칩 버튼.
- 캡션 4요소(사실·연대·출처·라이선스) 모두 manifest에서. `loading="lazy"`. 역링크 의무(09_gallery 워크스루 #1).

### 6.13 데이터 테이블 (data-table) — 미확정 관계·소재 미확인·어록 검증표 등

```html
<table class="data-table">
  <thead><tr><th>인물</th><th>통설 관계</th><th>미확정 사유</th></tr></thead>
  <tbody><tr><td>…</td><td>…</td><td>…</td></tr></tbody>
</table>
```
- 헤더 `--bg-raised` `--text-muted` sans, 셀 구분은 가로선 `--border` 1px만(세로선 없음 — 여백 위계). 셀 패딩 `--sp-3`. 모바일에서 가로 스크롤(`overflow-x:auto`) 허용.

### 6.14 각주·참조 링크 (ref-link / footnote)

```html
<a class="ref-link" href="references.html#src-aca-001" aria-label="출처 보기">[출처]</a>
```
- `[ref:ref-NNN]` 마커(정규화 후)가 references 앵커로. `--accent` `--fs-sm`, 본문 흐름 방해 최소(위첨자 또는 인라인 `[출처]`). references 페이지 항목은 §6.13 테이블 또는 정의 리스트.

---

## 7. 경계 상황 스타일 (명세 밖 상황 — 구현 팀 임의 판단 차단, 선제 정의)

| 상황 | 스타일 결정 |
|------|------------|
| **데이터 없음** (필터 결과 0건, 빈 섹션) | `.empty-state`: 중앙 `--text-muted --fs-base`, "해당 조건의 사건이 없습니다" 류 안내 1줄. 빈 박스·스피너 잔류 금지. |
| **제목 2줄 초과** | 카드 제목은 `--lh-snug`로 자연 줄바꿈 허용(말줄임 `…` 금지 — 사건명 잘림은 검증 텍스트 훼손). 단 그리드 높이는 `align-items:start`로 카드별 가변 허용. |
| **disputed 사건** | §6.2 — 점선 단청 테두리 + "기록 상충" 라벨 + dispute_note. 색 단독 금지. |
| **미확인/추정 날짜** | precision이 year/range면 §6.3 표기 규칙대로 축약 표기. 〔미확인〕 제목 사건은 D필터로 제외됨(잔존 시 데이터 결함 — 표시하지 말고 보고). |
| **이미지 결손** (`.has-image` 미부착) | 인물: 이니셜 플레이스홀더 — `--img-placeholder-bg`(=`--paper-dim`) 바탕, 중앙에 이름 첫 글자 serif `--fs-xl` `--text-faint`. 일반 슬롯: 빈 프레임 대신 캡션만 노출하거나 슬롯 생략(필수 슬롯 미충족은 명세 개정 사항 — 임의 더미 이미지 금지). |
| **권장 슬롯 미충족** (img-phil-02 등 5건) | 슬롯 자리를 빈 박스로 남기지 말고 해당 figure를 렌더하지 않는다(레이아웃 자연 수축). 필수 슬롯은 21/21 충족(manifest 확인). |
| **긴 url·id 표기** | `--font-mono` `--fs-sm`, `overflow-wrap:anywhere`로 컨테이너 넘침 방지. |
| **C등급 한정 문형** | 별도 시각 박스 없음 — 본문 한정 문형 자체가 표시(00_common §2). C 배지는 보조. 단정형 윤문 금지는 콘텐츠 규칙이나, 디자인은 한정 문형을 굵기·색으로 과장하지 않는다(중립 유지). |

---

## 8. 산출물 자기 검증 (스킬 §검증 + a11y-engineer 인계 기준)

1. **토큰 단일성**: `site/css/` 전체에서 `#[0-9A-Fa-f]{3,6}` 하드코딩 hex grep → tokens.css 외부(특히 main.css) 발견 시 토큰 참조로 교체. (Phase 4b 구현 후 검사)
2. **대비 검증**: 사용 중인 모든 전경/배경 조합이 §2 대비표에 있고 용도 등급 통과. 표에 없는 조합 발견 시 실측 후 표 갱신. ← **본 v1에서 신규 등급/소재 색 9조합 실측·등재 완료(전부 AA 통과).**
3. **금지 조합 검사**: `--dancheong` 텍스트가 `--ink` 배경 위에, `--celadon`이 본문 크기 텍스트에 쓰인 곳 0건.
4. **컨셉 정합(단청 절제)**: 화면당 단청색 사용 ≤2곳 권장. 카드 컨테이너·배지·필터에 단청 면적 칠하기 금지. 강조 3곳+면 절제 위반 의심.
5. **문서·코드 동기화**: 본 문서 토큰표 ↔ tokens.css 실제 값 일치. 토큰 변경 시 양쪽 + §변경 이력 갱신.
6. **색 단독 의존 금지**: 등급·disputed·소재·관계 유형·노드 종류 모두 텍스트 라벨/형태 병기(색각 이상 대응).

---

## 변경 이력

| 일자 | 변경 | 사유 |
|------|------|------|
| 2026-06-06 | v1.0 최초 작성 — 컨셉(A안 채택·B안 기각)·토큰표·대비표(신규 9조합 실측)·타이포·컴포넌트 14종·경계 상황·사진 처리·반응형 | Phase 4a 디자인 시스템 확정 |
| 2026-06-06 | **경로·네이밍 계약 확정** — architecture.md v0.9 §4 확인 후: tokens.css 경로를 `site/css/tokens.css`로 동결(team-lead 지시문 `site/assets/css/` 미채택, `assets/`는 이미지 전용 확인). 파일을 `site/css/`로 이동. 클래스 케밥 규약은 architecture.md가 ui-designer에 위임한 항목이라 본 문서 §0 규약을 표준 확정. §0·머리말·§8 경로 기재 정정 | architecture.md CSS 디렉토리 계약(`css/`)이 지시문보다 우선 — 단일 진실 공급원 정합 |
| 2026-06-06 | **모듈 스코프 접두 규약 반영** (web-architect 회신) — §0 네이밍에 모듈 접두(연표 `tl-`·지도 `map-`·공통 무접두) + JS 훅 `data-*` 권장 추가. §6.3 연표 카드 `event-card`→`tl-event-card`(공유 `.grade-badge`·`.ref-link`는 무접두 유지), §6.11b 지도 마커 팝업·경로 캡션 절 신설(`map-` 접두) | main.css 단일 네임스페이스에서 timeline.js·map.js·일반 페이지 클래스 충돌 사전 차단(CSS 평면 파일 소유권) |
| 2026-06-06 | **`nw-` 접두 확정** (web-architect §4 규칙8·D-15 확정 회신) — 관계망 그래프 모듈 접두 `nw-` 확정(제안→확정), §0 모듈 접두 3종(`tl-`/`map-`/`nw-`) 등재. §6.11 관계망 그래프를 "frontend 소유 vanilla SVG"로 명시하고 그래프 시각 토큰(노드 형태·크기 스케일 8~16px·엣지 패턴·선두께 `--bw-hair`/`--bw-accent`·색)을 frontend가 nw- 클래스에 적용하도록 구체화. **design-system.md v1.0 동결 — Phase 4b 인계 준비 완료** | 그래프=vanilla SVG·frontend 소유(D-09) 확정에 따른 소유·접두 정합 |
