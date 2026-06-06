# 접근성·SEO 감사 기록 — 도산 안창호 일대기 사이트

> 작성: a11y-engineer (Phase 4b, Task #4) / 시작: 2026-06-06
> 기준: WCAG 2.1 AA, design-system.md §2 대비표(실측 검증 완료), architecture.md §4 규칙2(접근성 수정 전권+사후 고지)
> 운영: 페이지 완성 통보 즉시 단위 감사 — 전체 완성 후 일괄 감사 금지(web-qa-protocol §2 incremental).
> 종결 조건: 전 10페이지 + 인터랙티브 컴포넌트(연표·지도·관계망 그래프) 감사 통과.
> **상태: 완결(2026-06-06). 전 10페이지 통과. 차단 2·중대 2 전건 해소 재검증 완료(§2.4). 경미 2건은 비차단 권고로 남김.**

---

## 0. 감사 체크리스트 (페이지마다 전 항목 적용)

각 항목에 WCAG 기준 번호를 인용한다. 판정은 코드 읽기가 아니라 로컬 서버(`cd site && python3 -m http.server 8000`) 실측·키보드 시연 기준.

| # | 영역 | 검사 항목 | WCAG 기준 |
|---|------|----------|-----------|
| C1 | 색 대비 | 모든 전경/배경 조합이 §2 대비표 통과 등급(본문 ≥4.5 / 큰글씨·UI ≥3.0). 표 외 조합은 check_contrast.py로 실측 | 1.4.3 |
| C2 | 색 대비 | 등급 배지·disputed·소재 상태·관계 유형의 **색 단독 의존 금지** — 텍스트 라벨/형태 병기 | 1.4.1 |
| K1 | 키보드 | 모든 인터랙티브 요소 Tab 도달 가능, 논리적 포커스 순서 | 2.1.1 / 2.4.3 |
| K2 | 키보드 | 포커스 트랩 없음(모바일 내비 오버레이·팝업은 의도적 트랩 + Esc 탈출) | 2.1.2 |
| K3 | 키보드 | 포커스 표시(focus ring) 가시 — `:focus-visible` 또는 --focus-ring | 2.4.7 |
| K4 | 키보드 | 스킵 링크("본문 바로가기") 헤더 최상단 | 2.4.1 |
| S1 | 스크린리더 | 랜드마크: `<header>`·`<nav>`·`<main>`·`<footer>` 각 1, main에 id | 1.3.1 / 4.1.2 |
| S2 | 스크린리더 | 헤딩 위계: h1 1개, 건너뛰기 없는 h2→h3 순서 | 1.3.1 / 2.4.6 |
| S3 | 스크린리더 | 모든 `<img>` 의미 있는 alt(manifest caption 기반). 장식 이미지 없음 | 1.1.1 |
| S4 | 스크린리더 | 아이콘 단독 버튼·링크에 aria-label, ⚑ 등 장식 글리프 aria-hidden | 1.1.1 / 4.1.2 |
| S5 | 스크린리더 | SVG 그래프(관계망)에 대체 텍스트(role/aria-label) + 비JS 테이블 폴백 | 1.1.1 / 1.3.1 |
| S6 | 스크린리더 | 현재 페이지 내비에 aria-current="page" | 4.1.2 |
| R1 | 반응형 | 360 / 768 / 1280px 가로 스크롤·요소 겹침 없음 | 1.4.10 |
| R2 | 반응형 | 본문 폭 --measure(42rem) 준수, 텍스트 200% 확대 가독 | 1.4.4 / 1.4.10 |
| R3 | 반응형 | 터치 타깃 ≥44×44px(모바일 내비 토글 등) | 2.5.5(AAA 참고)/AA 권장 |
| M1 | 모션 | prefers-reduced-motion 존중(tokens.css 전역 안전망 확인 + 컴포넌트 전환) | 2.3.3 |
| SEO1 | SEO | `<html lang="ko">`, 페이지별 고유 `<title>` | 3.1.1 |
| SEO2 | SEO | `<meta name="description">` 페이지별 고유 | — (SEO best practice) |
| SEO3 | SEO | Open Graph(og:title·og:description·og:type·og:url·og:image) | — |
| SEO4 | SEO | 시맨틱 마크업(article·section·time·figure/figcaption·dl) | 1.3.1 |
| SEO5 | SEO | 구조화 데이터(JSON-LD: Person/Article 등) 권장 | — |
| SEO6 | SEO·검증 | **description·OG 문구는 page_specs·본문 lede에서 발췌 — 새 사실 문장 생성 금지**(team-lead 승인 단서, 검증 평면 보호). lede·도입 서사는 지리 한정·영웅 서사 압축 위험 구간이므로 발췌 원문 대조 | 검증 윤리(프로젝트 규칙) |
| F1 | 폼/UI | 필터·토글에 접근 가능한 이름(label/aria-label), 상태(aria-pressed/expanded) | 4.1.2 |

> **SEO 기준 승인(team-lead, 2026-06-06):** lang="ko"·페이지별 고유 title/description·OG·시맨틱·JSON-LD를 감사 기준으로 승인. 단 description·OG 문구는 page_specs·lede 발췌만(새 사실 문장 금지 — 검증 평면 보호).
> **CSS 파일 규칙 확정:** site/css/에 `timeline.css`(timeline 모듈)·`map.css`(map 모듈)가 추가됨 — 모듈 접두 전용. 하드코딩 hex 검사 대상에 포함(tokens.css 외부 색 = 위반).

심각도: **차단**(법적·핵심 기능 불가) / **중대**(주요 사용자군 접근 불가) / **경미**(우회 가능·미세 개선).
직접 수정 범위(architecture.md §4 규칙2): alt·lang·aria 속성, 시맨틱 태그 교체, meta·OG 태그 추가. **JS 동작 로직 변경은 소유 개발자 회부.**

---

## 1. 사전 검증 — 대비표 실측 (대기 중 수행, 2026-06-06)

`_workspace/04_build/check_contrast.py`로 design-system.md §2 대비표 전 25조합을 tokens.css 실측 값으로 독립 계산(WCAG 2.1 SC 1.4.3 상대휘도 공식).

**결과: 전건 일치(exit 0).** 표가 주장한 모든 대비율이 실측과 소수 둘째 자리까지 재현됨. 따라서 **대비표를 신뢰 가능한 감사 기준으로 채택**한다.

핵심 경계선 항목(감사 시 주의):
- `--ink-faint / --paper-dim` = **4.74:1** — 본문 AA(4.5) 통과하나 여유 작음. 더 작은 배경 변형엔 재실측 필요.
- `--celadon / --paper` = **3.38:1**, `--celadon / --paper-dim` = **3.07:1** — **본문 크기 텍스트 절대 금지**. 큰글씨(24px+)·테두리·아이콘만. 본문엔 `--celadon-deep` 사용. → 감사 시 main.css에서 `--celadon`(또는 `--rule`)을 18px 이하 텍스트 색으로 쓴 곳 0건 확인할 것.
- `--dancheong / --ink` = **2.94:1** — 금지 조합. 단청 텍스트를 먹 배경 위에 둔 곳 0건 확인.
- `--loc-cited / --paper-dim` = **4.86:1**, `--grade-c-text / --paper-dim` = **4.86:1** — 경계선 통과. 배경이 --paper-dim보다 어두운 곳에 놓이면 불통과 위험.

재사용: 페이지 감사 중 표 외 임의 조합 발견 시 `python3 check_contrast.py --pair '#FG' '#BG'`로 즉석 판정.

---

## 2. 페이지별 감사 기록

> 페이지 완성 통보 수신 시 이 절에 누적. 각 페이지: 통보 시각 → 체크리스트 판정 → 위반(심각도·기준·수정안) → 직접 수정/회부 → 재검증.

### 2.1 timeline.html (연표) — timeline-developer 통보 2026-06-06

**감사 방법:** 로컬 서버(`python3 -m http.server`) + headless Chrome(puppeteer-core) 실측 — 키보드 Tab 전수, `<dialog>` 포커스 트랩·Esc·포커스 복귀, aria-live 갱신, 3뷰포트(360/768/1280) 가로 스크롤·터치 타깃, 색 단독 의존, 콘솔 에러. 코드 읽기만으로 판정하지 않음(Policy 3). 산출물: timeline.html·js/timeline.js·css/timeline.css.

**통과 항목(실측 근거):**
| 항목 | 결과 | 근거 |
|------|------|------|
| C1 색 대비 | 통과 | timeline.css 전 색이 tokens.css var() 참조. 활성 칩=bg-raised+rule 테두리+700(단청 면 없음). 하드코딩 hex 0(`::backdrop`은 color-mix로 --ink 파생) |
| C2 색 단독 금지 | 통과 | 등급 배지="A검증"·"B학술·기관"(문자+라벨), disputed="⚑ 기록 상충"(점선+텍스트, ⚑는 aria-hidden), 태그 칩=텍스트 |
| K1 Tab 도달·순서 | 통과 | 칩(aria-pressed)·토글·카드 제목 버튼·상세 버튼·다이얼로그 닫기 전부 네이티브 포커스 요소, 논리 순서 |
| K2 포커스 트랩 | 통과 | 네이티브 `<dialog>.showModal()` — 트랩·배경 비활성 브라우저 제공. 일반 흐름엔 트랩 없음 |
| K3 포커스 표시 | 통과 | main.css `:focus-visible{box-shadow:var(--focus-ring)}` 적용 확인(단청 2px 링, outline:none이나 box-shadow로 대체 — 가시) |
| K2/Esc | 통과 | Esc로 dialog.open=false, **포커스가 원래 카드 버튼으로 복귀**(close 이벤트 lastFocused.focus()) 실측 확인 |
| S1 랜드마크 | 통과 | header·nav·main·footer 각 1, main#app. ※단 헤더 내용 미주입 — 아래 회부 BLK-1 참조 |
| S2 헤딩 위계 | 통과 | h1 1개(도입문) → h2(시기 그룹 P1~P8, 각주) 건너뜀 없음. dialog 내 h2(제목)+h3(섹션)은 모달 별도 컨텍스트 |
| S3 이미지 alt | 해당없음 | 연표 페이지에 `<img>` 0건 |
| S4 아이콘 aria | 통과 | ⚑ aria-hidden, 닫기 버튼 aria-label="닫기" |
| F1 필터 이름·상태 | 통과 | 칩 aria-pressed 토글, 토글=label+checkbox, 그룹 role=group+aria-labelledby |
| aria-live | 통과 | #tl-status aria-live="polite" role="status", 필터 시 "사건 17건 표시 중 (기록 상충만)"로 실측 갱신 |
| R1 가로 스크롤 | 통과 | 360/768/1280 전부 docW==winW, 가로 스크롤 0 |
| R2 본문 폭 | 통과 | --measure 준수, 카드 그리드 minmax 반응 |
| M1 모션 감소 | 통과 | tokens.css 전역 dur 0 + timeline.css `.tl-chip{transition:none}` + JS matchMedia로 scrollIntoView auto. reduce 에뮬에서 JS 에러 0 |
| SEO1 lang/title | 통과 | `<html lang="ko">`, title="연표 — 도산 안창호 일대기" 고유 |
| SEO2 description | 통과 | 페이지별 고유 meta description 존재 |
| SEO4 시맨틱 | 통과 | article(카드)·section(시기 그룹)·time[datetime]·dl/dt/dd(메타)·dialog·noscript 폴백 |
| 데이터 정직성(참고) | 통과 | 잠정 마커 노출 0, D등급 누출 0(실측), range 평탄화 없음, 음력 병기 |

**위반·결함:**

- **[경미] CONT-1 / WCAG 2.5.5(AAA 참고)** — disputed 토글 체크박스 단독 18×18px(360px 뷰포트). **단, `<label>`이 체크박스+텍스트를 감싸 실측 클릭 영역 157×26px**이므로 라벨 클릭으로 조작 가능 → AA(2.5.8 최소 24×24)는 라벨 영역으로 충족, AAA(44×44) 미달. 칩 80×33·제목버튼 268×34는 전부 충족. **수정안(선택):** `.tl-toggle input{min-height:1.4rem}` 또는 라벨 세로 패딩으로 26→44px 권장. **심각도 경미 — 차단 아님.** → timeline-developer 참고 통보.
- **[참고] favicon 404** — `/favicon.ico` 404 콘솔 에러 1건. 접근성 위반 아님(사이트 공통 head, frontend-developer 소유). QA #3 콘솔 에러 게이트 대상 → frontend-developer/qa 통보.

**회부(소유 개발자 — JS 동작 로직, 직접 수정 금지 Policy 5):**

- **[차단] BLK-1 / WCAG 4.1.2·2.4.1·1.3.1 — timeline-developer 회부.** `js/timeline.js` L36이 `mountLayout`을 **import만 하고 호출하지 않음**(init 함수에 호출 없음). 결과(실측): 전역 헤더·내비 10항목·푸터가 **렌더되지 않음**(`.site-nav` 부재, header 내용 빈 상태). 파급: ① 전역 내비 부재 → 페이지 간 이동 불가 ② `aria-current="page"` 미표시(S6 위반) ③ 푸터 랜드마크 내용 공백(참고문헌·방법론 링크 부재). **기대 동작:** init()에서 `mountLayout('timeline')` 호출. **재현:** timeline.html 로컬 서버 로드 → 헤더 영역 빈칸. **추가:** timeline.html L22 마운트포인트 속성이 `data-layout-header`인데 layout.js는 `data-site-header`를 찾음(L66) → 불일치. 호출하더라도 layout.js가 기존 마운트포인트를 못 찾아 새 header를 body.prepend → header 중복 위험. **둘 다 timeline 측 정합 필요**(호출 추가 + 속성 일치 또는 frontend와 마운트포인트 규약 합의).

> ※ BLK-1의 skip 링크 부재는 timeline 단독 결함이 아니라 **layout.js(frontend-developer) 자체에 skip-link 생성 코드가 없음** — main.css는 `.skip-link` 스타일만 정의(L50). 별도 회부 BLK-2(frontend) 참조.

**timeline 자체 a11y 구현 품질은 매우 높음**(네이티브 dialog·aria-pressed·aria-live·포커스 복귀·motion-reduce·noscript 폴백 전부 구현). 차단 결함은 공통 레이아웃 미연결 1건으로, 이것만 해소되면 통과.

### 2.x layout.js 공통 결함 (전 페이지 영향) — frontend-developer 회부

- **[차단] BLK-2 / WCAG 2.4.1(Bypass Blocks) — frontend-developer 회부.** `js/layout.js` `mountHeader`가 **skip 링크 요소를 생성하지 않음**. main.css L50 `.skip-link`(off-screen→focus 노출 패턴)는 정의돼 있으나 이를 렌더하는 코드가 layout.js·어느 페이지에도 없음 → 전 10페이지에서 "본문 바로가기" 부재. **기대 동작:** mountHeader에서 헤더 최상단에 `<a class="skip-link" href="#app">본문 바로가기</a>` 주입(각 페이지 main id 또는 공통 `#app`/`#main` 규약). **재현:** 임의 페이지 로드 → 첫 Tab이 스킵 링크 아닌 브랜드/내비로. 전 페이지 공통이므로 layout.js 단일 수정으로 전체 해소.

### 2.2 map.html (활동 지도) — Task #3 완성 감지 2026-06-06 (선제 감사, Policy 6)

**감사 방법:** 로컬 서버 + headless Chrome 2모드 — (A) Leaflet 차단(오프라인 폴백 검증) / (B) Leaflet 허용. 슬라이더 키보드(화살표)·경로 버튼·aria-valuetext/live·거점 목록 키보드 동등성·3뷰포트. 산출물: map.html·js/map.js·css/map.css.

**통과 항목(실측 근거):**
| 항목 | 결과 | 근거 |
|------|------|------|
| S1/S1a 랜드마크·공통 모듈 | **통과** | map.js L580 `mountLayout('map')` **호출 확인** → 헤더 내비 렌더(.site-nav 존재), 푸터 4링크. timeline과 달리 map.html은 마운트포인트 속성도 `data-site-header`로 layout.js와 일치 |
| S6 aria-current | 통과 | 내비 "지도"에 aria-current="page" 실측 |
| 키보드 동등성(Leaflet a11y 핵심) | **통과** | 지도는 `role="application"`+aria-label로 키보드 사용자를 거점 목록으로 안내. **거점 목록(28카드·113사건)이 1급 콘텐츠**로 지도와 동일 데이터 — 마커 키보드 도달 불가를 목록이 완전 대체. Leaflet 마커도 `:focus-visible` outline(map.css L320) |
| 폴백(오프라인) | **통과** | Leaflet 차단 시 캔버스 `is-fallback` 전환 + 거점 목록·noscript 정적 안내 유지. 지도가 콘텐츠 전부가 되지 않음(interactive-viz §4) |
| 슬라이더 키보드 | **통과** | input[type=range], ArrowRight로 value 0→2, **aria-valuetext "P2 결혼과 1차 미주 (1899–1907)"로 갱신**, readout + #map-live 라이브("거점 6곳 표시 중") 동기. 거점 목록도 6곳으로 필터(시각·SR 동기) |
| 경로 버튼 | 통과 | aria-pressed false→true, is-current(단청), 캡션 텍스트 + 라이브 고지. 색 단독 아님(캡션 텍스트·pressed 병기) |
| C1 색 대비 | 통과 | map.css 전 색 var() 참조, 하드코딩 hex 0(Leaflet 구조 px만 주석 예외). 경로선 청자/현재만 단청(강조 1색) |
| aria-live | 통과 | #map-live visually-hidden + aria-live polite, 슬라이더·경로 조작 시 갱신 |
| R1 가로 스크롤 | 통과 | 360/768/1280 전부 0 |
| M1 모션 감소 | 통과 | tokens 전역 0 + map.css `.map-route-btn{transition:none}`, JS 폴백 안전 |
| SEO1 lang/title | 통과 | lang="ko", title 고유 |
| SEO6 메타 발췌 검증 | **통과** | description "113건·다섯 차례 대이동·검증 데이터만"은 map-intro/map-routes 원문 발췌, 새 사실 없음. title "한반도→미주·중국·연해주" 지리 요약은 R1~R5(인천·SF·상하이·블라디보스토크) 근거 — **압축 과장·영웅 서사 없음**([[lede-compression-risk]] 대조 통과) |
| 각주 처리 | 통과 | 경로 캡션의 [ref:] → `<sup class="footnote-ref"><a aria-label="각주 N, 출처 보기">`로 정상 치환(처음 "123"으로 보인 건 각주 1·2·3 위첨자, 누출 아님) |

**위반·결함:**

- **[경미] CONT-2 / WCAG 1.4.1 경계·design-system §6.1 위반** — 거점 카드 등급 배지가 `grade-letter`(문자 "B")만 렌더하고 **`grade-text` 라벨("학술·기관")을 누락**(map.js L272–273). `aria-label="신뢰도 B등급"`이 있어 **스크린리더는 통과**, 등급 문자 자체가 색 외 구분자라 1.4.1 엄격 위반은 아님. 그러나 design-system §6.1 "반드시 등급 문자 **+ 라벨 텍스트** 병기"와 timeline 구현("B학술·기관")과 **불일치** → 시각 일관성·색약 보강 차원에서 라벨 병기 권장. **수정안:** timeline의 `gradeBadge`처럼 `el('span',{class:'grade-text',text:GRADE_LABEL[g]})` 추가. **심각도 경미.** → map-developer 통보.
- **[참고] favicon 404** — 전 페이지 공통(BLK-2와 함께 frontend). map 고유 아님. **→ 해소(layout.js ensureFavicon SVG 데이터URI 주입, 전 10페이지 favicon 링크 존재·404 0 실측).**
- **[경미·비차단] MAP-POPUP / WCAG 2.1.1 경계 — Leaflet 마커 팝업 키보드 흐름.** Leaflet 로드 실측(마커 28개): 마커 포커스+Enter로 팝업 열림·grade-text 라벨·교차링크 href(timeline.html#evt-) 존재 확인. 그러나 팝업 열린 뒤 **포커스가 팝업 내부로 이동하지 않아**(activeTag=IMG 마커 잔류) Tab으로 팝업 내 "연표에서 보기" 도달이 어렵고 Esc로 닫히지 않음 — **Leaflet 1.9.x 기본 동작**(팝업 콘텐츠 auto-focus 안 함). **비차단 판정 근거:** 거점 목록(113 교차링크 전부 focusable, 실측)이 1급 키보드 등가 콘텐츠라 모든 사건·교차링크가 목록으로 완전 도달(interactive-viz 폴백 패턴 충족). 캔버스 aria-label도 키보드 사용자를 목록으로 안내. **권고(선택):** Leaflet 팝업 열림 시 컨테이너/closeButton 포커스 이동 + Esc 핸들러 보강. **게이트 영향 없음** — 등가 콘텐츠로 2.1.1 충족.

**map 자체 a11y 구현 품질 매우 높음** — 특히 Leaflet 페이지의 난제(지도 키보드 접근)를 "거점 목록 1급 콘텐츠"로 정공법 해결, 슬라이더 aria-valuetext·오프라인 폴백·각주 처리까지 모범. **차단급 0건.** 경미 1건(배지 라벨 일관성)만 보완하면 통과.

### 2.3 frontend 8페이지 (index·life·organizations·philosophy·people·archives·gallery·references) — Task #1 완성 2026-06-06

**감사 방법:** headless Chrome 일괄 스캔(구조·랜드마크·헤딩 위계 점프·메타·alt·SVG 대체텍스트·색 단독·3뷰포트) + people 그래프·archives Reflow 심층 실측.

**전 페이지 공통 통과(실측):**
| 항목 | 결과 |
|------|------|
| SEO1 lang/title | 8/8 `lang="ko"` + 페이지별 고유 title |
| SEO2 description | 8/8 페이지별 고유 description |
| BLK-2 skip 링크 | **해소** — 8/8 `.skip-link` 렌더 확인(frontend가 layout에 추가, main.css `.skip-target`#main 타깃). 첫 Tab=본문 바로가기 |
| S1 랜드마크 | header·main·footer 각 1(내비 nav + 푸터 nav). ※비-index 7페이지의 header 2개는 `.site-header`(전역)+`.page-header`(main 내부 페이지 타이틀 배너)로 **정상 시맨틱**(main 내부 header는 banner 랜드마크 아님) |
| S1a 공통 모듈 | 8/8 `.site-nav` 렌더, 푸터 4링크 — mountLayout 정상 호출(timeline의 BLK-1과 대조) |
| S2 헤딩 위계 | 8/8 h1 1개, **헤딩 레벨 점프 0건**(h2→h4 등 건너뜀 없음) |
| S6 aria-current | 8/8 현재 페이지 내비에 aria-current="page" |
| S3 이미지 alt | **전 이미지 alt 보유**(gallery 80 + life 13 + people 3 + archives 3 + index 1 = 100건, alt 누락 0·빈 alt 0). 장식 이미지 없음 원칙 부합 |
| C1 색 대비 | tokens var() 참조, 하드코딩 hex 외부 0(별도 grep 예정 — QA 토큰 단일성과 공유) |
| R1 가로 스크롤 | archives 외 7페이지 360/768/1280 전부 0 |
| 본문 렌더 | mainTextLen 전부 정상(life 23,633·archives 40,881 등 — 빈 화면 0) |

**위반·결함:**

- **[중대→수정 회부] NW-1 / WCAG 4.1.2·1.3.1 — people.js SVG role 충돌. frontend-developer 회부.**
  - 증상(접근성 트리 실측): people 관계망 SVG에 `role="img"`(people.js L90)인데 그 안에 `role="button" tabindex="0"` 노드 **81개**가 있음. `role="img"`는 SVG를 단일 이미지로 선언해 AT가 하위 트리를 가지치기 → **스크린리더에 노출되는 버튼 0개**(accessibility.snapshot 실측: img=버튼 0, group=버튼 81). 키보드 사용자는 81개 노드에 Tab·Enter로 도달·작동 가능(실측: Enter→상세 패널 "안창호(安昌浩)1878..." 열림)인데 **SR 사용자는 그래프를 단일 이미지로만 인지** → 포커스 가능하나 AT에서 역할·이름 미노출(4.1.2 위반).
  - **완화 요인:** 그래프 등가 콘텐츠(노드·관계 목록·미확정 D 별도 섹션)가 별도 존재해 SR 사용자도 전체 데이터 도달 가능 → **차단 아님, 중대.**
  - **수정안(검증 완료):** people.js L90 `role: 'img'` → **`role: 'group'`**. 실측 결과 group으로 변경 시 81 버튼이 "안창호(安昌浩), 인물 — 상세 보기" 등 라벨과 함께 AT에 정상 노출(aria-label은 group 이름으로 유지). role 제거도 동일 효과. **JS 렌더 로직 + frontend 동시 편집 중(main.css 변경 감지)이라 직접 수정 않고 회부.**
  - 범례·색 단독 통과: ● 인물·■ 조직(형태) + 6관계 유형 텍스트 라벨(조직소속·동지·가족·갈등·사제·후원, 갈등 동등 비중).

- **[중대→직접 수정 완료] REF-1 / WCAG 1.4.10 Reflow — archives 360px 가로 스크롤. a11y-engineer 직접 수정(§4 규칙2).**
  - 증상(실측): archives.html 360px에서 docScrollW 719 > 360, `canScroll: true`(사용자 가로 스크롤 발생). 원인: 사료 비판 문단 `<p>`의 "공식 호수 제1호~제83호 중 57개호…" 등 **숫자·기호 혼합 긴 한글 어절이 word-break:normal로 안 끊겨** 박스를 404px 초과(scrollW 674/clientW 270).
  - **직접 수정:** main.css에 `.page-section,.page-lead,.archive-card,.criticism-block { word-break: keep-all; overflow-wrap: anywhere; }` 추가(본문 텍스트 컨테이너 스코프, 헤더·컴포넌트 타이포 비변경). keep-all=한글 어절 보존·공백 줄바꿈, anywhere=불가피 시 강제.
  - **재검증(실측):** archives·life·organizations·philosophy·references·people 6페이지 360px 전부 docScrollW 360·`canScroll: false`. frontend 동시 편집과 충돌 없음(수정 잔존 확인). → frontend-developer 사후 고지 완료.

- **[경미·권장] SEO3 OG / SEO5 JSON-LD 미구현** — 8/8 페이지 `og:*` 메타 0개, JSON-LD 0개. SEO3(OG)는 team-lead 승인 기준에 포함, SEO5(JSON-LD)는 권장. SNS 공유 카드·검색 리치 결과 미지원. **수정안:** layout.js 또는 각 head에 og:title(=title)·og:description(=meta description)·og:type=article(home은 website)·og:url·og:image(대표 초상 dosan-portrait-1919) 추가. **문구는 기존 title/description 재사용(SEO6 — 새 사실 문장 금지).** 차단 아님(점진 개선). → frontend-developer 회부.

**frontend 8페이지 기반 품질 높음** — skip 링크·랜드마크·헤딩 위계·alt 100%·aria-current 전부 통과. 차단급 0건. people SVG role(중대, 1줄 수정)·OG(권장)만 보완하면 통과. Reflow는 직접 수정 완료.

### 2.4 재검증 — 전 10페이지 수정 반영 후 (2026-06-06, 게이트 종결)

수정 통보 후 headless Chrome 재실측. **전 결함 해소 확인:**

| 결함 | 소유 | 재검증 결과 |
|------|------|------------|
| **BLK-1** mountLayout 미호출 | timeline-developer | **해소** — timeline.js L662 `mountLayout('timeline')` 호출 + timeline.html L22 `data-site-header`로 정정. 실측: headerNav true·footerLinks 4·aria-current "연표". dialog 키보드(Enter 열림·Esc 닫힘·포커스 복귀) 유지 |
| **BLK-2** skip 링크 미생성 | frontend-developer | **해소** — 10/10 페이지 `.skip-link` href="#main" 렌더. 실측: 첫 Tab="본문 바로가기" → Enter → 포커스 `#main`(skip-target) 이동(WCAG 2.4.1 통과) |
| **NW-1** people SVG role 충돌 | frontend-developer | **해소** — people.js L92 `role:'group'`. 접근성 트리 실측: 노출 버튼 0→**81** ("안창호(安昌浩), 인물 — 상세 보기" 등 라벨 노출). WCAG 4.1.2 통과 |
| **REF-1** archives Reflow | a11y-engineer(직접) | **해소 유지** — main.css word-break 규칙 잔존. archives 360px canScroll false |
| **CONT-2** map 배지 라벨 누락 | map-developer | **해소** — map.js 거점 배지 "B학술·기관"(grade-text 병기). timeline과 일관 |
| **SEO3** OG 미구현 | frontend-developer | **해소** — 10/10 페이지 og:title·og:description·og:type 5종. **SEO6 검증: og:title=`<title>`, og:description=meta description 자구 동일 — 새 사실 문장 0**(검증 평면 안전) |

**전 10페이지 콘솔 에러 0**(favicon.ico 404도 layout.js ensureFavicon으로 해소 — 이제 셸 예외조차 불요, [[favicon-404-site-shell]]), pageError 0. **대비표 25조합 실측 일치(exit 0)**, 전 CSS 외부 하드코딩 hex 0(tokens.css `--on-accent #FFFFFF`는 토큰 정의처 자신, 정상). 금지 색 조합 0.

**최종 재검증(shutdown 직전, 전 10페이지 일괄 실측):** consoleErr 0 / skip-link 1개·href="#main"·#main 타깃 존재 / favicon 링크 존재 — 10/10 전부 통과. timeline·map 포함(qa-engineer가 BLK-2 미보유로 관측했던 2페이지도 layout.js 단일 주입으로 해소 확인). BLK-1·BLK-2·NW-1·CONT-2·REF-1·SEO3·favicon **전 회부 결함 해소 재검증 완료.**

**잔여(비차단·권장):** ① SEO5 JSON-LD 미구현(권장) ② og:url·og:image null(공유 카드 완성도 — 경미). 둘 다 차단·중대 아님 → 게이트 통과 판정에 영향 없음, frontend 점진 개선 권고로 남김.

**최종 판정: 전 10페이지 접근성·SEO 감사 통과.** 차단 2·중대 2·경미 2 발견 → 차단·중대 4건 전부 해소 재검증 완료. 경미 2건(JSON-LD·og 보조 태그)은 권고로 남김.

---

## 3. 회고 (감사 1회 종료 시마다 갱신 — 체크리스트 누락 점검)

**감사 #1 (timeline.html) 후 회고:**
- **누락했던 검사 유형 발견:** 페이지 단위 감사 시 "그 페이지가 공통 모듈(layout.js)을 실제로 호출/연결했는가"를 별도 항목으로 두지 않았다. timeline은 자기 컴포넌트 a11y는 완벽했으나 `mountLayout` 미호출로 헤더·내비·skip 링크가 통째로 비었다 — 컴포넌트만 보면 통과처럼 보이는 함정. **체크리스트 보강:** S1 항목에 "공통 헤더·내비·푸터가 실제 렌더되는가(랜드마크 내용 비어있지 않은가)" 하위 검사를 명시한다.
- **확인된 좋은 패턴:** 코드 읽기로 "import 있음 → 호출됨"이라 단정했다면 BLK-1을 놓쳤을 것. **로컬 서버 실측(headless Chrome)이 코드 읽기를 이긴 사례** — Policy 3(키보드 시연·실측) 준수가 결함을 잡았다. 이후 전 페이지 동일 방식 유지.
- **재사용 자산:** `/tmp/tl_audit.mjs`(puppeteer 감사 스크립트)를 페이지별로 URL·셀렉터만 바꿔 재사용. map(좌표·Leaflet)·people(SVG 그래프) 감사 시 컴포넌트 특화 검사만 추가.

**체크리스트 보강 반영(S1 하위 항목 추가):**
- S1a: 공통 헤더·내비 10항목·푸터가 비어있지 않게 렌더되는가(공통 모듈 호출 누락 검출).
- S6 재확인: aria-current="page"는 내비 렌더가 전제 — 내비 미렌더면 S6도 자동 실패로 묶어 보고.

**감사 #2~#3 (map + frontend 8페이지) 후 회고:**
- **놓칠 뻔한 검사 유형 — `documentElement.scrollWidth` 단독으로는 원인 미상.** archives Reflow는 per-element 경계 스캔(`getBoundingClientRect().right > vw`)으로는 offender 0이 나왔다(박스는 viewport 내, 자식 텍스트만 overflow). **`scrollWidth > clientWidth` 트리 하강 + 텍스트 leaf의 ws/owrap/wbreak 동시 추출**이 진짜 원인(긴 한글 어절)을 잡았다. **체크리스트 보강 R1a:** Reflow 의심 시 (1) 사용자 가로 스크롤 가능 여부(canScroll) 확인 (2) scrollW>clientW 요소를 루트→leaf로 하강해 텍스트 노드의 word-break/overflow-wrap까지 본다.
- **SVG `role="img"` + focusable 자식 = 숨은 4.1.2 함정.** 구조 스캔에서 SVG에 role·aria-label·title이 다 있어 통과처럼 보였으나, **접근성 트리 스냅샷(accessibility.snapshot)으로 버튼 노출 수를 세니 0**이었다. role 속성 존재만으로 통과 판정하면 놓친다. **체크리스트 보강 S5a:** 인터랙티브 SVG는 접근성 트리에서 자식 인터랙티브 요소가 실제 노출되는지(버튼 수) 확인 — role 존재 ≠ 올바른 role.
- **동시 편집 환경 — 직접 수정 vs 회부 판단.** CSS Reflow는 안정 구역의 추가 규칙이라 직접 수정(검증 후 잔존 확인). people SVG role은 frontend가 main.css를 동시 편집 중이고 JS 렌더 로직이라 회부. **원칙 재확인: 직접 수정은 (a) 안전·추가적이고 (b) 소유자 동시 편집과 충돌 없을 때만. 의심되면 회부**(위험성향 2).

**감사 #4 (전 10페이지 재검증·게이트 종결) 후 회고:**
- **회부 결정이 옳았다.** NW-1을 직접 안 고치고 회부한 사이 frontend가 role을 'group'으로 고쳐 푸시했다 — 같은 파일(people.js)을 내가 동시에 건드렸다면 충돌했을 것. 회부+검증된 수정안(role:'group') 제시가 개발자를 즉시 움직이게 했다(Policy 5: 수정안 동봉).
- **재검증은 "수정됐다는 통보"가 아니라 실측으로.** 소스 grep에서 people.js가 아직 role:'img'로 보였으나(편집 타이밍), 같은 순간 렌더는 'group'이었다 — **소스 한 줄이 아니라 접근성 트리 실측(버튼 81 노출)이 진실**. 통보·소스만 믿었으면 오판했다.
- **체크리스트 완결성 확인:** S1a(공통 모듈 렌더)·R1a(Reflow 트리 하강)·S5a(SVG AT 노출 수)를 이번 사이클에 모두 적용해 누락 0. 다음 감사(부분 수정·재실행)도 동일 4축(콘솔·키보드/트리·대비·반응형) 실측 유지.
