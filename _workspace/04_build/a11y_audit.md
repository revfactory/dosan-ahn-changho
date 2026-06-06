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

---

## 4. v2 재감사 (dosan-redesign Task #3, 2026-06-06 — incremental, 진행 중)

> 컨셉 v2 "맑은 한지, 살아 움직이는 먹" — 애니메이션 배경·스크롤 리빌·카운트업·유리 표면·smooth scroll 신규 도입.
> 감사 5축(team-lead 지정): ① prefers-reduced-motion 전수 ② 애니메이션 배경 위 텍스트 대비 실측(최악 프레임) ③ 키보드·focus-visible 회귀 ④ JS 비활성 콘텐츠 가시(리빌 숨김 0) ⑤ 기존 통과(v1 §2.4) 회귀 0.
> 기준: dosan-design-system v2 §2 대비표(유리·그라디언트 조합)·§3 애니배경 규칙·§4 모션 규칙.
> 재감사 하네스: `/tmp/v2_rm_audit.mjs`(emulateMediaFeatures(reduce) 실측 — 배경 transform 변화·리빌 화면밖 숨김 수·카운트업 즉시값·scroll-behavior, +키보드 firstTab/skip/aria-current/랜드마크, +JS off 가시). check_contrast.py 재활용.

### 4.0 대기 중 토큰 레이어 선검증 (tokens.css v2 착지분, 페이지 미완 — 조기 페이지 감사 아님)

v2 토큰이 tokens.css에 착지(L170~234), main.css 모션 구현(Task #2)은 미착지(@keyframes·is-revealed·backdrop-filter 0건) 상태에서 **완성된 토큰 정의만** 정적 검증. 페이지 감사는 frontend 완성 통보 후로 유보(Policy 1).

- **회귀 0(대비표):** check_contrast.py 재실행 exit 0 — v1 §2 대비표 25조합 전건 실측 일치 유지(v2 토큰 추가가 v1 값 불변).
- **v2 §2 추가 조합 실측(check_contrast.py --pair, WCAG 1.4.3):**
  | 조합 | 실측 | 판정 | 비고 |
  |---|---|---|---|
  | `--ink`/`--paper-bright`(#1A1815/#FDFBF7) | 17.14:1 | AAA | 유리 카드 본문. 토큰 주석 17.14 정확(스펙 §2 "16.6"은 보수적 인용, 둘 다 AAA) |
  | `--dancheong`/`--paper-bright` | 5.82:1 | 본문 AA 통과 | 밝은 카드 링크(스펙 5.6↑ 여유) |
  | `--ink-soft`/`--paper-bright` | 9.19:1 | 통과 | hover 표면 위 카드 메타 |
  | 흰 텍스트/`--grad-accent` 단청끝(#B5342B) | 6.02:1 | 통과 | — |
  | 흰 텍스트/`--grad-accent` 노을끝(#D4663A) | **3.65:1** | **본문 AA 불통과** | 스펙 §2 "그라디언트 위 본문 텍스트 금지" 근거 확정. 감사 시 진행바·히어로 획 위 본문 텍스트 0건 확인(장식·보더·아이콘만 허용) |
- **유리(`--glass` rgba .72) 위 텍스트:** 애니메이션 배경 합성색에 의존 → 최악 프레임 합성 실측 필요. 배경 구현 착지 후 측정(유보).
- **reduced-motion 전역 안전망:** L232~234 `--dur-fast/base/slow: 0ms` 유지 확인. **단, 듀레이션 0은 @keyframes 배경 루프·JS 카운트업을 멈추지 못함** — 배경 `animation-play-state` 정지·리빌 즉시·카운트업 즉시값은 구현 착지 후 emulate(reduce)로 별도 실측 필수(이번 사이클 핵심 함정).

### 4.0b ui-designer §2.6·§9 감사 기준 수령 (Task #1 completed, 2026-06-06)

ui-designer가 design-system.md §2.6(유리·배경 위 실측)·§9.2(겹침 금지)·§9.3(모션)를 확정. **a11y 감사 항목으로 채택할 측정 기준(전건 check_contrast.py 재현 가능):**

- **§2.6-가 paper-bright 위:** 전건 본문 AA↑(ink 17.14·ink-soft 9.19·ink-faint 5.59·dancheong 5.82·grade-c 5.73 등). 내 선검증과 일치.
- **§2.6-나 유리(`--glass` .72) 합성:** 최악 backdrop=두 블롭 겹침 `#E6DED4` → 유리 합성색 `#F7F3ED`. 그 위 ink 16.03·ink-soft 8.59·ink-faint 5.22·dancheong 5.44·celadon-deep 5.54 — **전건 본문 AA 통과.** ★**조건부:** frontend가 `--glass-blur`(blur 12px)를 반드시 동반해야 합성 가정 성립 → **감사 시 유리 표면에 backdrop-filter:blur(≥12px) 적용 여부 실측**(blur 0이면 합성 깨짐, 회부).
- **★§2.6-다 애니메이션 배경 위 *직접* 텍스트(가장 불리한 프레임):**
  - 안전: `--ink`/#E6DED4 13.30 · `--ink-soft`/#E6DED4 7.13 · `--dancheong`/#E6DED4 4.52(경계 여유 0.02) · `--celadon-deep`/#E6DED4 4.59(경계).
  - **금지(AA 미달):** `--ink-faint`/#E6DED4 = **4.33:1** · `--grade-c-text`/#E6DED4 = **4.45:1** — 두 블롭 겹침 backdrop에서 본문 AA 미달. 단일 블롭(#E9E9DF)에선 4.72/4.85로 통과 → **겹침만 위반**.
- **채택 감사 항목(§9.2 — 겹침 금지 제약, 협상 불가):**
  1. **블롭 겹침 금지:** 청자(`bg-blob-celadon`)·단청(`bg-blob-dancheong`) 블롭이 **중앙 `--measure` 본문 컬럼 뒤에서 겹치지 않는가**(좌상↔우하 분리·표류 진폭 제한). 겹쳐 `#E6DED4` backdrop이 본문 영역에 생기면 ink-faint·C배지 미달 → **차단 회부**. → 감사: 블롭 애니메이션 전 구간(다수 시점 샘플)에서 두 블롭 bounding box가 본문 컬럼 x범위에서 동시 교차하는지 실측.
  2. **텍스트 표면 제약:** 본문·배지·미세 메타(`--ink-faint`·`grade-c` 등)는 `--paper`/`--paper-dim`/유리 위에 두고, raw 블롭 위 직접 텍스트는 큰 텍스트(`--ink`/`--ink-soft` 위계)만. → 감사: 배경(`.bg-wash`)이 `position:fixed;z-index:-1`로 본문 *뒤*에 있고 본문 컨테이너가 자체 배경(paper류)을 갖는지, ink-faint/C배지가 raw 블롭 위에 직접 노출되는 케이스 0건.
- **§9.3 채택 항목:** ① reduce에서 블롭 `animation:none` 정지(제거 아님·톤 유지) ② 배경 레이어 `aria-hidden="true"`(콘텐츠 아님) ③ transform/opacity만(filter·box-shadow 애니메이션 금지 — 페인트 플래시 0).
- **★사진 hover filter 예외(ui-designer 정정 수령, D-1b 명문화 — false-positive 방지):** 사진 hover 톤 복원 듀레이션 확정값=**`--dur-enter`(280ms)**(design-system.md §10.1, 스킬 초안의 `--dur-base`는 오기). reduce에서 `--dur-enter`=0 중화 → 즉시 톤·전이 없음(reduce 감사 기대값 동일). 이 hover `filter` 전이는 "filter 애니메이션 금지"의 **명시 예외**(D-1b): 조건 ①transition만(@keyframes 루프 아님) ②`will-change` 상시 부여 금지 ③그리드 일괄 전이 금지. **→ 페인트 플래시 0 감사 시 이 hover filter는 위반 아님**(이산·단일 요소·사용자 개시 — 연속 페인트 누적 없음. 배경 블롭의 연속 filter와 구분). 2차/사진 페이지 감사 시 위 3조건 충족만 확인.

> **상태: 토큰·대비 기준 레이어 선검증·감사 항목 확정 완료.** frontend-developer 배경+유리헤더(1차)·리빌+카운트업(2차) 통보 시 incremental 감사 착수 → 아래 절에 페이지/모듈별 누적.

### 4.1 Stage-1 감사 — 배경 + 유리헤더 (frontend 1차 증분 통보 2026-06-06)

**변경:** site/js/layout.js(배경 `.bg-wash` 주입·헤더 스크롤 토글), site/css/main.css(`.bg-wash`/`.bg-blob`/`bg-drift`·`.site-header.is-scrolled` 유리·reduce 쿼리).
**감사 방법:** 로컬 서버(:8137) + headless Chrome(`/tmp/v2_rm_audit.mjs` emulate(reduce) 실측·`/tmp/v2_bg_sample2.mjs` 렌더 합성색 채취·check_contrast.py --pair). index·life·timeline 3페이지 표본. Stage-1 감사 가능 항목 = reduce 1·5 + 키보드 회귀(reduce 4 smooth scroll·2·3 카운트업/리빌은 frontend 정정대로 3차/2차 — 미감사).

**통과 항목(실측 근거):**
| 항목 | 결과 | 근거(실측) |
|------|------|-----------|
| **reduce 1** 배경 정지 (WCAG 2.3.3·§9.3) | **통과** | NORMAL: 블롭 `bg-drift`/`bg-drift-2` 애니 가동(matrix transform 변화)·`bgMovedAfter1.5s:true`. REDUCE(emulate): 전 블롭 `animation:none`·transform `none`·`bgMovedAfter1.5s:false`. main.css L675-676 `@media reduce{.bg-blob{animation:none}}` 실측 발화 — 정적 워시 톤 유지(제거 아님). index·life·timeline 3페이지 동일 |
| **reduce 5** 유리헤더 텍스트 대비 (WCAG 1.4.3·§2.6-나) | **통과** | `.is-scrolled` = `--glass`(rgba .72)+`backdrop-filter:blur(12px)` 실측(main.css L660 — §2.6-나 전제 충족). 최악 합성 backdrop `#F7F3ED` 위 헤더 텍스트 전건 본문 AA: brand/nav `--ink` 16.03·brand-sub `--ink-soft` 8.59·is-current `--dancheong` 5.44. 블러 미지원 폴백 가정(raw `#E6DED4`)에서도 13.30/7.13/4.52 전부 통과. 헤더에 `--ink-faint`·`grade-c` 텍스트 0 |
| **§9.2 ② 렌더 합성색** (a11y 분담분 — QA GATE-A 상보) | **통과** | 본문 컬럼 중앙(x=640) 3스크롤×4위상 12샘플 실측(2회 재현): 가장 어두운 backdrop **`#EFE7DB`~`#EFE8DB`**(=사실상 `--paper-dim`, 휘도 231.8~232.5/255) — 겹침 임계 `#E6DED4`(188.4)보다 훨씬 밝음 → **본문 영역에 두 블롭 겹침 backdrop 미발생**. 그 위 §2.6-다 금지 후보조차 통과: `--ink-faint` 4.71·`--grade-c` 4.83(단일 블롭 안전역). **GATE-A 양면 잠금 확정:** QA 코드측(블롭 A 청자 좌상 top:-10%·B 단청 우하 bottom:-12%, @keyframes 표류 A=translate(4%,3%)scale≤1.06·B=translate(-3%,-4%) §9.1 진폭표 부합, 4뷰포트 768/1024/1280/1440 최악 표류에도 원 중심거리>반지름합 여유 7.2~20.6% → 원 미교차) + a11y 렌더측(합성 농담 #E6DED4 미도달 실측). qa_log.md 교차 기록. **추가 표본(QA 권장 — 좁은 --measure 페이지):** life.html(이미지·figure 차폐 후 순수 배경 레이어 채취) 4스크롤×4위상 가장 어두운 backdrop `#EFE8DB`(휘도 232.5) — index와 동일·#E6DED4 미도달. 넓은(index)·좁은(life) 본문 컬럼 양쪽 통과 확인. (※초기 life 측정에서 #7C7C7C 나온 건 grayscale 사진 픽셀 오염 — img 차폐로 해소, 배경 아님) |
| **K1~K4·S1·S6 키보드 회귀** (WCAG 2.4.1·2.4.7·1.3.1·4.1.2) | **통과·회귀 0** | 3페이지 첫 Tab=`.skip-link`("본문 바로가기" href="#main"), skip-link 보존. 랜드마크 header/nav/main/footer 유지(life의 header:2는 v1 확정 정상 — 전역+page-header 배너). aria-current 정확(홈/생애/연표). focusable 92~825. **콘솔 에러 0·pageError 0** |
| **JS 비활성 가시(부분)** | **통과(회귀 0)** | NOJS `opacityZeroTextEls:0` 3페이지 — CSS 기본 숨김(`.card{opacity:0}` 류) 0건. timeline noscript 본문 774자 유지. ※index·life는 v1부터 JS 렌더(noscript 폴백)라 NOJS bodyText 짧음 — v2 신규 회귀 아님. 리빌 정식 JS-off 감사는 2차에서 |

**리빌 메커니즘 선점 검증(2차 항목이나 1차에 reveal.js 이미 존재 — 오탐 방지차 실측):**
- main.css L676 `.is-pre-reveal{opacity:0}`는 **reveal.js가 JS로만 부여**(L57), no-JS면 미부여 → 콘텐츠 가시(폴백 안전, §4-2 준수). CSS 기본 숨김 0.
- **자연(점진) 스크롤 실측(life, 300px 간격·정착):** NORMAL·REDUCE 양 모드 `stillHidden:0`·`revealed:35` — **전 리빌 대상이 스크롤 시 정상 노출, 영구 숨김 0건**. (초기 `scrollTo(scrollHeight)` 점프-스크롤에서 33 잔류로 보였던 것은 IntersectionObserver가 프레임 점프로 교차 미등록한 **테스트 아티팩트** — 자연 스크롤에서 재현 안 됨. 오탐으로 회부하지 않음.)
- **경미 관측(비위반):** reduce에서 화면밖 리빌 대상은 스크롤 전까지 `opacity:0`(전이는 0ms 즉시). 콘텐츠 도달 가능·모션 없음이라 §9.3 "리빌 즉시 표시" 취지 충족. reveal.js의 `prefersReduced()`(L24)는 정의되나 미사용(무해). 2차 정식 감사에서 카운트업·JS-off 리빌과 함께 재확인.

**배경 레이어 §9.3 위생(실측):** `.bg-wash`가 `<body>` 첫 자식·`aria-hidden="true"`(장식·AT 비노출)·`z-index:-1`·`position:fixed`·`pointer-events:none`·블롭 2개(§9.1 2~3 한도 내). 전건 충족. (z-index·예산 게이트 정본은 QA — 접근성 부수 관측으로만 기록.)

> **★기준 거버넌스(ui-designer 확정, 재감사 시 준수):** §2.6-다 `#E6DED4`(두 블롭 풀강도 겹침 가정)는 **보수적 게이트 컷오프 — 완화 금지**. 현재 렌더가 그 안쪽(#EFE7DB)에 여유 안착했다는 사실은 "현재 통과"일 뿐, 컷오프를 느슨히 할 근거가 아니다. frontend가 향후 블롭 진폭·강도를 키워 본문 뒤 겹침이 생기면 ink-faint(4.33)·C배지(4.45)가 AA 미달하므로, **재실행/부분수정 감사 시에도 #E6DED4 기준 + 렌더 합성색 실측을 동일하게 적용**한다(블롭 위치·진폭·opacity 변경분이 있으면 §9.2 양면 잠금 재수행).

**Stage-1 위반:** **0건(차단·중대·경미 모두 0).** reduce 1·5·키보드 회귀·§9.2 렌더·배경 위생 전건 통과. → frontend-developer Stage-1 통과 통보. reduce 2·3(2차)·reduce 4 smooth scroll(3차) 대기.

> **상태: Stage-1(배경+유리헤더) 통과. 2차(리빌+카운트업)·3차(진행바+smooth scroll) 증분 통보 대기.**

### 4.2 Stage-2/3 감사 — 리빌·카운트업·진행바·smooth scroll (frontend 2·3차 증분 통보 2026-06-06)

**변경:** js/reveal.js(신규), js/layout.js(리빌 호출·진행바), js/home.js(카운트업), css/main.css(리빌·히어로·카드·링크·진행바·smooth scroll). reduce 4(smooth scroll)도 이번 반영.
**감사 방법:** 로컬 서버(:8137) + headless Chrome emulate(reduce). 카운트업 0-경유 폴링·리빌 자연스크롤(인간 모사 80px+rAF flush)·진행바 속성·smooth scroll 양모드. index·life·gallery·organizations 표본. 산출물 `/tmp/v2_stage2.mjs`·`/tmp/v2_gallery_human.mjs`·`/tmp/v2_hidden_at.mjs`.

**통과 항목(실측 근거):**
| 항목 | 결과 | 근거(실측) |
|------|------|-----------|
| **reduce 3** 카운트업 즉시 최종값 (WCAG 2.3.3·§10.2) | **통과** | home.js L41 `if(reduce) return;` — reduce면 `start()` 미진입 → `textContent='0'`(L64)에 절대 도달 안 함. emulate(reduce) 로드 직후 10회 폴링 `.stat-num`의 '0' 출현 **0회**, 최종값(165·17·305·48·59·22·135·80) 즉시. 0 깜빡임 없음. 최종값은 meta.json textContent(하드코딩 아님) |
| **reduce 4** smooth scroll 해제 (WCAG 2.3.3·§10.3) | **통과** | main.css L13 `html{scroll-behavior:smooth}` + L745 `@media reduce{html{scroll-behavior:auto}}`. emulate 실측: NORMAL html=smooth·REDUCE html=auto. CSS 미디어쿼리 정공법 |
| **진행바** (§10.3·§2.6 그라디언트 텍스트 금지) | **통과** | life에만 주입(index 부재 확인)·`aria-hidden="true"`·`textContent=""`(그라디언트 위 텍스트 0 — §2.6 준수)·`transform:scaleX(0)`(matrix(0,0,0,1,0,0))·`--grad-accent` 배경·z-index 199(헤더 하). 순수 장식 |
| **reduce 2** 리빌(life·organizations) | **통과** | life(35)·organizations(33) reduce 자연스크롤 후 영구 숨김 0. `.is-pre-reveal{opacity:0}`는 JS만 부여(no-JS 가시), reduce에서 transition 0·shift 0 즉시 |

**위반·결함:**

- **[중대 → frontend-developer 회부] REV-1 / WCAG 1.4.13·1.3.1 — gallery 리빌 영구 숨김(lazy-load 리플로우 × IO unobserve).**
  - **증상(실측):** gallery.html(`.image-card` 80개, 전부 `loading="lazy"`)에서 **인간 모사 스크롤(80px 스텝·rAF 더블 flush·40ms)** 후에도 **14개**(촘촘 스크롤+2.5s 정착 시 6개) 카드가 `opacity:0`·`is-revealed` 미부여로 **영구 숨김**. **NORMAL·REDUCE 양 모드 동일 14건** — reduce 한정 아님, 프로그램 점프 아티팩트 아님(rAF flush 인간 스크롤에서 재현). 숨은 카드는 뷰포트 위로 지나가(top<0) IO 재관찰 없음(unobserve-once).
  - **근본 원인:** ① 80 카드 전부 `loading="lazy"` → 초기 그리드 높이 0, 스크롤 중 이미지 로드되며 그리드 리플로우·카드 위치 이동 ② IO `threshold:0.08`+`rootMargin:-8%`+첫 교차 시 `unobserve`(reveal.js L35·39) → 리플로우로 카드가 콜백 프레임 사이에 트리거존을 지나치면 영구 미발화. life/organizations(카드 적고 큼)는 미발생, gallery(80 밀집 그리드)만 발현.
  - **완화 요인(차단 아닌 근거):** opacity:0이나 `visibility:visible`·`display:block` → **접근성 트리 잔존**(실측 `inAccessibilityTree:true`), 숨은 카드 img alt(예 "1935년 대전형무소 가출옥…여운형·조만식")·focusable `<a>` AT·키보드 도달 가능. no-JS면 `is-pre-reveal` 미부여로 전건 가시. **→ 시각(마우스) 사용자만 사진 ~14장 시각 손실 — 중대(주요 사용자군 시각 접근 불가), 차단 아님.**
  - **수정안(frontend 검증 권장):** (a) **폴백 리빌 패스 추가** — `scroll`(디바운스) 또는 settle 시 `getBoundingClientRect().top < innerHeight`인 잔여 `.is-pre-reveal`를 일괄 `is-revealed`(이미 지나친 요소 구제). 또는 (b) IO `unobserve` 제거하고 가시 영역 통과분 재평가, 또는 (c) 이미지에 `aspect-ratio` 박스로 치수 예약해 lazy 리플로우 제거(IO 오프셋 안정화). + reduce에서는 `is-pre-reveal` 아예 미부여(reveal.js의 미사용 `prefersReduced()` L24 의도 실현 — reduce는 즉시 가시). **JS 동작 로직이라 직접 수정 않고 회부**(Policy 5).

**추가 통과 항목(실측):**
| 항목 | 결과 | 근거 |
|------|------|------|
| **사진 hover filter D-1b 3조건** (§9.3·§10.1·§10.4 예외) | **통과(예외 정상)** | main.css L744-750: ①`transition:filter --dur-enter`(@keyframes 루프 아님) ②`will-change` 0(블롭 L611·리빌 L669에만, 사진엔 없음·L743 주석 명시) ③`.figure-img` 개별 요소 hover 전이(`.gallery-grid` 일괄 아님). `@media(hover:hover)` 가드·reduce 시 --dur-enter=0 즉시. grayscale 1→0.65 부분복원(CSS만·원본 불변). **이산·단일·사용자 개시 → 페인트 플래시 위반 아님**(ui-designer D-1b 예외 합치) |
| **CSS 기본 숨김 금지** (§4-2·§9.3) | **통과** | css 전체 content `opacity:0`은 `.is-pre-reveal`(main.css L665) **1곳뿐** — JS만 부여(reveal.js L57). 블롭 키프레임 opacity 0.9~0.92는 장식(숨김 아님). `.card{opacity:0}` 류 무조건 숨김 0 |
| **JS 비활성 — 리빌 기여 숨김 0**(axis ④) | **통과** | gallery·life·organizations·people JS-off: `.is-pre-reveal` 클래스 0건·`opacity:0` 가시요소 0건 → **v2 리빌이 no-JS 콘텐츠를 추가로 숨기지 않음**(JS 게이트 정상). |

**참고(비위반·v2 회귀 아님):** 8 frontend 페이지(index·life·gallery 등)는 **v1부터 JS 렌더 셸**(JSON 로드 후 DOM 주입)이라 JS-off 시 본문·이미지 미렌더(bodyText 짧음). noscript 정적 폴백은 interactive-viz 페이지(timeline·map)에만 존재 — **v1 §2.3에서 확정된 기존 아키텍처, v2 신규 회귀 아님**. v2 리빌 feature는 이 위에 올바르게 JS-게이트로 얹힘(위 axis④ 통과). 셸에 skip-link·`data-load-error`·고유 title/description/favicon 정적 존재. (이 아키텍처 자체에 대한 판정은 v1 게이트 소관 — v2 재감사 범위 밖.)

**Stage-2/3 종합:** reduce 3·4·진행바·리빌(비-gallery)·사진 hover 예외·CSS 기본숨김 금지·JS-off 리빌 기여 0 통과. **중대 1건(REV-1, gallery 리빌 영구 숨김) frontend 회부.** 수정 후 gallery 인간 스크롤 재검증 예정. reduce 1·5(Stage-1)는 통과 유지.

### 4.3 v2 전 10페이지 회귀 스윕 (2026-06-06)

v2 전체 착지(Task #2 completed) 후 v1 §2.4 통과 항목 회귀 0 확인:
- **대비표 회귀 0:** `check_contrast.py` exit 0 — v1+v2 대비표 전건 실측 일치 유지.
- **하드코딩 hex 회귀 0:** main/timeline/map.css tokens.css 외부 색상값 0건(timeline.css L325 hex 1건은 **주석 내 토큰 파생 설명** — 색상값 아님, v1 확정 예외).
- **10페이지 키보드·랜드마크·내비·콘솔 회귀 0:** index·life·philosophy·organizations·people·archives·gallery·references·timeline·map 전부 — 첫 Tab=skip-link(href="#main")·main 1개·전역 내비 렌더(navItems 14, timeline 22)·aria-current 정확(홈/생애/사상/조직/인물/사료/갤러리/참고문헌/연표/지도)·**콘솔 에러 0**. v1 통과 항목 전건 보존.

### 4.4 REV-1 해소 재검증 (frontend 수정 22:07 후, 2026-06-06)

frontend가 reveal.js에 **REV-1 3중 안전망** 구현(22:07): ① 양수 bottom rootMargin(64px)+threshold 0(진입 직전 선반응) ② 카드 내 이미지 `load`/`error` + scroll/resize 시 `sweepInView`(in-view 잔여 카드 보정) ③ **6000ms 최종 안전망 — 잔여 `is-pre-reveal` 전부 강제 `is-revealed`**(가시성>연출, 화면밖 미진입 포함).

**재검증(실측, 6s 안전망 통과 대기 포함):**
| 시나리오 | reduce | normal |
|---|---|---|
| 스크롤 없이 로드 → 6s 후 숨김 수 | **0** (전 77→0, revealed 82) | **0** (77→0, revealed 82) |
| 인간 스크롤 → 6s 후 숨김 수 | **0** | **0** |
| 자연 스크롤(settle) 즉시 숨김 수 | **0**(layer② 스윕이 in-view 카드 즉시 보정) | 0 |

- **gallery 80 카드 전 시나리오 영구 숨김 0** — 스크롤 안 해도 6s 안전망이 화면밖 카드까지 전부 보임 처리. 콘텐츠 영구 비가시 불가능.
- **회귀 0:** reduce 2 리빌 life·gallery·organizations 전부 0 숨김(비-gallery 미회귀). 새 scroll/resize 리스너에도 **10페이지 콘솔 에러 0**(6s 후 removeEventListener 정리 확인). 키보드·랜드마크·aria-current 회귀 0 유지.
- 잔여 미세 관측(비위반): 스크롤 안 한 화면밖 카드는 ≤6s간 opacity:0(정상 reveal-on-scroll 연출 구간) 후 안전망으로 표시 — 가시성 보장됨. 채택한 수정안 (a)(폴백 리빌 패스)와 동일 방향.

**REV-1 → 해소 재검증 완료.** 내가 회부한 수정안대로 frontend가 폴백 리빌 패스(+이미지 load 보정+6s 강제)로 해결, 실측 확인.

> **최종 판정: v2 접근성 재감사 — 전 항목 통과. 차단 0·중대 1(REV-1)→해소 재검증 완료·경미 0.**
> reduce 1~5 전수(배경 정지·리빌 즉시·카운트업 즉시·smooth scroll 해제·유리헤더 대비)·§9.2 애니배경 위 대비(index+life 렌더 + QA GATE-A 코드 양면 잠금)·사진 hover D-1b 예외·진행바(grad 텍스트 금지)·JS 비활성 가시·CSS 기본숨김 금지·10페이지 v1 회귀 0(대비표 exit 0·hex 0·키보드/랜드마크/aria-current/콘솔) 전건 실측 통과. **Task #3 종결.**

### 4.5 frontend 최종 증분(사진 hover 원톤 + D-3) 접근성 확인 (2026-06-06)

frontend 최종 증분(Task #2 완료) — 사진 hover 톤 복원·D-3 reveal.js 죽은 셀렉터 제거. 제기된 a11y 포인트 3건 실측 검증:

- **사진 hover가 `:hover`만(`:focus` 아님) — 통과(의도 정당).** WCAG 1.4.1(색 단독 의미 전달) 비해당 근거: ① 이미지 식별 정보는 **alt·figcaption(텍스트)**이 전담(실측: alt "1919년 무렵 상하이에서 촬영된 안창호의 초상…" 등·figcaption 존재), hover 톤(grayscale 1→0.65)은 **순수 장식 강조**로 정보 0 ② 키보드 포커스 가시성은 별도 `--focus-ring` 담당 — 갤러리 카드 링크 focus 시 `box-shadow:0 0 0 2px(paper)+accent ring` 실측 적용(WCAG 2.4.7). 즉 키보드 사용자는 focus 피드백을 받고, hover 톤 미적용은 정보 손실 아님. **hover-only 정당.**
- **사진 hover reduce — 통과.** filter 전이 `--dur-enter`가 reduce에서 0 즉시화(모션 없음·깜빡임 0). D-1b 예외(transform/opacity 외 filter 승인): @keyframes 루프 아님·will-change 0·개별 요소 — 페인트 위반 아님(§4.0b 기록과 일치).
- **D-3 reveal.js 죽은 셀렉터 제거 — 회귀 0.** people는 `.page-section` 8개로 정상 리빌(`.person-card` 제거 무영향). reduce 자연스크롤+6s 후 영구숨김 0, 관계망 graph `role=button` 81 노출 유지(v1 NW-1 수정 보존), no-JS `is-pre-reveal` 0(폴백 가시).

**frontend 최종 증분 접근성 결함 0.** Task #2 전 증분(1·2·3차+최종) a11y 항목 전건 통과 확인.

### 4.6 v2 재감사 회고 (Task #3 종결 후 — 체크리스트 갱신)

- **리빌 완전성은 "자연 스크롤 + 안전망 통과 시점"에 측정한다(점프·즉시 측정은 양쪽 오류원).** REV-1 추적에서 두 측정 함정: ① `scrollTo(scrollHeight)` **점프 스크롤**은 IO가 프레임 점프로 교차를 놓쳐 *과탐*(life 33 잔류 → 자연 스크롤 0, 오탐), ② 안전망(6s) **전 즉시 측정**은 *미탐* 위험. 진실은 **인간 모사 스크롤(80px·rAF 더블 flush)로 발현 + 6000ms 안전망 통과 대기 후** 측정에서 잡힌다. → 체크리스트 보강 **M2:** 스크롤 리빌은 (1)자연 스크롤 발현 (2)안전망 grace 통과 후 (3)`opacity<1` 잔류 0 + 가시 카드 수=데이터 카드 수(특히 lazy 그리드) 실측. qa-engineer 체크리스트와 동일 합의.
- **silent failure는 콘솔·no-JS·소스로 안 잡히고 "렌더 후 상태 실측"으로만 잡힌다.** REV-1은 JS 정상 동작(콘솔 0)인데 결과(가시성) 실패 — no-JS 폴백·코드 읽기·콘솔 게이트 어느 것도 못 잡고 인간 스크롤 후 `getComputedStyle().opacity` 실측만 잡았다. **렌더 결과 상태 검사가 코드/콘솔/폴백을 이긴 두 번째 사례**(v1 BLK-1에 이어). Policy 3 재확인.
- **오탐 2건을 회부 전 걸러냈다.** ① life 점프-스크롤 33 잔류(테스트 아티팩트) ② life 배경 채취 #7C7C7C(grayscale 사진 픽셀 오염 — img 차폐로 해소). 둘 다 "보수적 위반 처리" 대신 **재현 조건을 바꿔 진위 확정 후** 판정 → 거짓 차단 회부 방지. 단 §2.6-다 #E6DED4 컷오프는 ui-designer 확정대로 **완화 안 함**(현재 통과 ≠ 기준 완화). **경계선은 보수 처리, 측정 아티팩트는 진위 확정 — 둘은 다르다.**
- **회부 vs 직접수정:** v2 결함은 전부 JS 동작 로직(REV-1 1건)이라 직접 수정 0건·회부. 검증된 수정안 3종 동봉 → frontend가 폴백 패스로 채택. 수정안 동봉이 개발자를 즉시 움직이게 한 v1 패턴 유효(Policy 5).
- **체크리스트 완결성:** v2 신규 축(reduce 전수·애니배경 위 대비 실측·M2 리빌 완전성)을 5축에 통합. 재실행/부분수정 감사 시: 블롭 위치·진폭·opacity 변경 → §9.2 양면 잠금 재수행(§4.1 거버넌스), 리빌 셀렉터/lazy 그리드 변경 → M2 재실측, 유리 표면 변경 → blur 동반 + 합성색 실측.
