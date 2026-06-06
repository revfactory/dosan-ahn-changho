# QA 검증 로그 — Phase 4b incremental QA (qa-engineer)

> 기준: web-qa-protocol 스킬 + architecture.md v1.0 §3 계약. "파일 존재 ≠ 통과" — 판정은 스크립트 실행·경계면 교차 비교 증거로만.
> 환경: `cd site && python3 -m http.server` (file:// 금지 — §5.1). 게이트: 전 페이지 QA 통과 + 콘솔 에러 0 + 끊어진 링크 0.

---

## 0. 검증 도구·기준선 (2026-06-06, 모듈 착수 전)

### 도구 준비
| 스크립트 | 위치 | 상태 |
|---|---|---|
| check_data_schema.py | `_workspace/04_build/scripts/` (data-engineer 작성) | 재사용 — §3 계약 인코딩 완료 |
| check_links.py | `_workspace/04_build/scripts/` (qa-engineer 작성, 번들판 확장) | 신규 — 파일 존재 + **앵커 프래그먼트 데이터 id 우주 대조** |

번들 `check_links.py`(skill)는 href/src 파일 존재만 검사. 이 사이트의 교차링크는 전부 데이터 id 앵커(§5.2·D-24)이므로, 죽은 id 앵커(`timeline.html#evt-XXX`)는 파일 존재 검사로 안 잡힌다 → 앵커 프래그먼트를 데이터 id 우주에 대조하는 확장판 작성.

### 데이터 평면 기준선 (consumer JS 가 읽을 ground truth)
`python3 _workspace/04_build/scripts/check_data_schema.py` → **PASS (검사 4611건, exit 0)**

id 우주 (앵커 대조 기준):
- evt 165 · per 59 · org 22 · src-pri 47 · source 194 · ref 155 · image 80
- 교차평면 evt 참조: archives `related_event_ids` 죽은 id **0건**, network `evidence_event_ids` 죽은 id **0건** → D-24 (병합 전 id 해소) 데이터 평면 충족 확인.

### 모듈 상태 (착수 전)
- `site/data/*.json`(데이터 13파일) + `css/tokens.css`: **존재·검증 통과.**
- `*.html`(10) · `js/*.js`(6) · `css/main.css`: **미존재** — frontend/timeline/map 미착수. 소비 JS 경계면 교차 비교는 모듈 도착 후 시작.
- site/ 변경 감시 모니터 가동(모듈 도착 즉시 incremental QA 트리거).

**판정: 데이터 평면 통과 / HTML·JS 평면 미검사(모듈 미도착 — 보류, 결함 아님).**

---

## 1. 공유 모듈 + timeline/map 골격 1차 검사 (2026-06-06)

도착분: `js/loader.js`·`js/layout.js`·`js/footnotes.js`(frontend 공유), `timeline.html`·`map.html`(골격). 미도착: `timeline.js`·`map.js`·`page-render.js`·`css/main.css`·`css/timeline.css`.

### 1.1 통과 — 공유 모듈 경계면 교차 비교

**loader.js ↔ §3.0 계약: 통과.** `loadData(path)` 성공 시 파싱 JSON 반환, 실패(network/HTTP!=200/parse) 시 `renderLoadError` 호출 후 throw — 빈 객체 미반환(null 정책 준수). `renderLoadError`는 `[data-load-error]`→`#app`→`main`→body 순 타깃에 알림+로컬서버 안내(§5.1) 노출, console.error 로그(§5.5). XSS 방어 textContent 주입. `loadAll` 병렬 헬퍼는 계약 외 추가지만 loadData 경유라 무해.

**footnotes.js ↔ §3.4 계약 + citations.json: 통과.** 렌더 경로(ref→source_id→source) 정확. 끊어진 각주/출처 → `[ref:ref-NNN ⚠]` 가시화 + console.warn(§5.5 빈 화면 금지 준수). 번호 중복 재사용·하단 목록·백링크 정상.
경계면 필드 대조:
| footnotes.js 읽는 필드 | citations.json 존재 | 판정 |
|---|---|---|
| refs.id / .source_id / .page_or_locator | 155/155 전건 | 통과 |
| sources.id/.author/.title/.publisher/.year/.url | 194/194 전건 | 통과 |
모든 소비 필드 100% 존재. 빈 문자열 가능 필드(author 등)는 `if(src.x)` 방어 — 정상.

### 1.2 결함 — 경계면 불일치 (소유 개발자 회부)

**[T-1] timeline.html ↔ layout.js 마운트포인트 속성 불일치 (소유: timeline-developer / frontend-developer)**
- 증거 쌍: layout.js L66/L115 `document.querySelector('[data-site-header]')` / `[data-site-footer]` ↔ timeline.html L22/L76 `<header ... data-layout-header>` / `<footer ... data-layout-footer>`.
- map.html L25/L102 은 `data-site-header`/`data-site-footer` 로 **정상**(대조군).
- 기대: layout.js가 timeline.html의 마운트포인트에 헤더·푸터 주입.
- 실제: 속성명 불일치로 querySelector miss → layout.js가 body에 **새 헤더/푸터를 별도 생성**, timeline의 빈 `data-layout-header`/`data-layout-footer` 엘리먼트는 고아로 잔존 → 헤더 중복·위치 오류.
- 재현: timeline.js가 mountLayout 호출하도록 완성된 뒤 `python3 -m http.server`로 timeline.html 열기 → 헤더 2개 확인.
- 판정: **보류**(수정 후 재검). 한쪽을 맞추면 됨 — 계약(layout.js §사용법 L12)이 `data-site-header`/`data-site-footer`를 명시하므로 timeline.html이 그쪽으로 정정하는 것이 계약 정합.

**[T-2] timeline.html이 계약에 없는 `css/timeline.css` 링크 (소유: timeline-developer)**
- 증거: timeline.html L18 `<link rel="stylesheet" href="css/timeline.css">` ↔ architecture §2 디렉토리·§4 소유권표·D-15: css 파일은 `tokens.css`(ui-designer)·`main.css`(frontend) **2개뿐**. 연표 `tl-` 클래스는 main.css에 작성(단일 네임스페이스, D-15).
- 실제: `site/css/timeline.css` 미존재 → 404(check_links.py 검출). 신규 최상위 css 파일은 §2 web-architect 합의 사항.
- 판정: **보류**. 두 경로 중 택1 — (a) `tl-` 스타일을 main.css에 넣고 이 링크 제거(계약 정합), (b) 새 css 파일이 정말 필요하면 web-architect 합의 후 §2·§4 계약 추가. 임의 신설 금지.

### 1.3 미도착(결함 아님 — check_links.py 검출분 중)
`css/main.css`·`life.html`·`archives.html`·`references.html`·`js/timeline.js`·`js/map.js` 404는 해당 모듈 미완성(frontend·timeline·map 진행 중). 모듈 도착 시 자동 해소 — 재검 대상.

**현 판정: 공유 모듈(loader·footnotes) 통과 / timeline·map 골격 보류(T-1·T-2 회부) / 미도착분 대기.**

---

## 2. 본체 모듈 도착 — 경계면 교차 비교 본검사 (2026-06-06)

도착분: `timeline.js`·`map.js`(본체) + frontend 페이지 `life/philosophy/organizations/references`.html + .js + `page-render.js`. CSS는 `tokens.css`·`main.css`(nw- 보유)·`timeline.css`(tl- 93개) 존재, `map.css` 미존재(참조됨).

### 2.1 통과 — 데이터 경계면 교차 비교 (스크립트·필드 대조 증거)

**timeline.js ↔ data/timeline.json: 통과.** 소비 필드 전수 대조:
| timeline.js 읽는 필드 | timeline.json 존재 | 판정 |
|---|---|---|
| id·title·date·place·summary·detail·sources·confidence·disputed·dispute_note·tags·period·has_geo·actor_refs·org_refs | 165/165 | 통과 |
| dispute(객체) | 22/165 (disputed 17 전건 보유) | 통과 — `if(disputed && dispute)` 게이트 |
| date.{start,end,precision,calendar} | 165/165 | 통과 |
| dispute.status / adopted.{precision,start,end,basis,claim} / variants[].{claim,source,assessment} | disputed 17 전건; adopted.precision=null 2건은 claim 보유 | 통과 — `if(ad.precision) else ad.claim` 분기 정확(D-16) |
| actor_refs[].{node_id,name} (457엔트리, null 101) | 비null node_id 전건 per-/org- 유효·network 실재 | 통과 — null→평문, 유효→앵커. cross-kind 오해소 0 |
| sources[].{url,title,locator,type} | 572/572 | 통과 |
- 딥링크 `?period=PN`·`#evt-id` 파싱·숨은 카드 필터 해제 후 스크롤 — 계약(§3.1 D-18) 준수. ambiguous 플래그 데이터상 0건이나 `if(node_id && !ambiguous)` 가드로 안전.

**map.js ↔ data/timeline.json: 통과.**
| map.js 읽는 필드 | 존재 | 판정 |
|---|---|---|
| has_geo·place.{lat,lng,name}·date.start·id·title·confidence·period | 165/165 (lat/lng 113 non-null) | 통과 |
- has_geo=true ⟺ lat/lng numeric **113 = 113** (meta.json events_with_geo·timeline meta.geo_count 일치) — 마커 누락 0. has_geo-true-but-non-numeric 0건.
- 경로 R1~R5 waypoint(지명 부분일치)가 geo place 이름에 전건 해소(R1 1점=선없음 처리, R2~R5 폴리라인). 미해소 0.
- map.js DOM id 쿼리(#map-canvas 등) ↔ map.html id 전건 일치(#map-places-empty는 map.js 동적 생성 — 정상). pages/map.json `map-intro`·`map-routes` 섹션 실재.

**page-render.js ↔ images.json + pages/*.json: 통과.**
- buildFigure 소비 `img.src`(★) 80/80 존재(data-engineer가 `assets/images/{file}` 선계산 — §3.5 경로 계약 충족). caption/title/date/period/license/credit/id/slots 전건.
- blocks 6유형(paragraph/blockquote/table/list/slot) 렌더, [ref:] 마커 원형 보존(footnotes 후처리), md링크 `<a>` 변환, slot→images.json `slots[]` 조회. 3불변 준수.

**ES 모듈 의존 그래프: 통과.** node --check 전 10개 JS 문법 0에러. 크로스모듈 named import(loadData·loadAll·mountLayout·renderPage·makeSlotResolver·renderFootnotes·renderInline 등) **전건 실제 export에 해소 — 미해소 import 0**(다작성자 코드의 흔한 실패 모드 부재).

### 2.2 결함 — 재확인·확대 (소유 개발자 회부)

**[T-1 확대] layout.js 마운트포인트 ↔ timeline.html·map.html 속성 불일치 — 헤더 중복 (소유: timeline-developer·map-developer)**
- 증거 매트릭스: layout.js L66/L115 `[data-site-header]`/`[data-site-footer]` 쿼리.
  | 페이지 | 마운트 속성 | layout.js와 일치 |
  |---|---|---|
  | life·philosophy·organizations·references (frontend) | `data-site-header/footer` | ✅ |
  | timeline | `data-layout-header/footer` | ❌ |
  | map | `data-layout-header/footer` | ❌ |
- 실제: timeline·map 에서 layout.js 마운트포인트 미발견 → body 에 새 헤더/푸터 별도 생성, 빈 `data-layout-*` 고아 잔류. map.js `ensureFallbackChrome`(L546)도 `[data-site-header]` 쿼리라 폴백도 미스.
- 판정: **보류.** 다수 정합(frontend 4페이지 + layout.js 사용법 주석)은 `data-site-*` → timeline·map 이 `data-layout-*`→`data-site-*` 정정해야. 동일 결함 2페이지.

**[T-3] map.html 이 참조하는 `css/map.css` 미존재 — 404 (소유: map-developer)**
- 증거: map.html L18 `<link href="css/map.css">` ↔ `site/css/map.css` 미존재(ls 확인, check_links.py 검출).
- 판정: **보류.** map.css 작성 또는 링크 제거(클래스를 다른 css 로). ※ T-2(아래 CSS 아키텍처)와 연동 — 어느 css 에 둘지 결정 필요.

**[T-2 격상 → CSS 아키텍처 이탈] 모듈별 CSS 파일(timeline.css·map.css) vs 단일 main.css 계약 (team-lead/web-architect 판정 필요)**
- 증거: 구현팀이 `css/timeline.css`(실존, tl- 93) 사용 + `css/map.css`(참조) 도입. main.css 엔 nw- 만. ↔ architecture §2 디렉토리·§4 소유권표·D-15: css = `tokens.css`+`main.css` **2개만**, `tl-`/`map-` 클래스는 main.css 단일 네임스페이스.
- 성격: 런타임 버그는 아님(별도 파일 로드 정상)이나 **확정 계약(§2·§4·D-15)에서 집단 이탈.** §2 신규 최상위 파일은 web-architect 합의 사항.
- 판정: **team-lead/web-architect 판정 회부.** (a) 계약대로 tl-/map- 를 main.css 로 흡수하고 별도 파일 제거, 또는 (b) 모듈별 css 를 공식 채택해 §2·§4·D-15 갱신. QA 는 결정 후 그 기준으로 재검. 이 항목은 경계면 결함이 아니라 거버넌스 항목이므로 QA 단독 보류가 아닌 판정 요청.

### 2.3 미도착(결함 아님)
timeline.html→archives.html·references.html 링크는 references.html 도착으로 일부 해소 중. index/archives/gallery/people.html 미도착. 도착 시 재검.

**현 판정: timeline.js·map.js·page-render 데이터 경계면 통과 / T-1(헤더 중복, 2페이지)·T-3(map.css 404) 보류 회부 / T-2(CSS 아키텍처) team-lead 판정 회부 / frontend 8페이지 일부 미도착.**

---

## 3. frontend 페이지 + people 그래프 — 교차평면 앵커 전수 검사 (2026-06-06)

도착분: index(home.js)·life·organizations·philosophy·references·people·archives·gallery .html + js. CSS map.css 해소(T-3 closed). 끊어진 파일 참조: timeline.html→archives.html 1건(곧 해소 중).

### 3.1 통과
- **people.js ↔ network.json: 통과(D-04 핵심).** 그래프는 `network.edges`(확정 135)만 사용, `edges_unconfirmed`(19 D) 그래프 본체 절대 미투입(L78 명시). 엣지 6유형(membership·comrade·family·conflict·mentor·patron) 전건 EDGE_LABELS 커버 — **mentor 포함 확인**(데이터 실측 membership63·comrade48·family10·conflict8·mentor3·patron3). vanilla SVG(D-09), 접근 폴백 테이블, evidence→timeline.html#evt 링크. node--check 통과.
- **slot 해소: 통과.** pages/*.json slot_id 전건 images.json `slots[]` 해소(미해소 img-life-10 1건은 images.json `unfilled_slots` 등재분 — page-render가 생략 처리, §3.5 정상. 결함 아님).
- frontend 페이지 JS(life·org·philosophy·references·people·home) loadAll 패턴·mountLayout 호출·import 해소 0미스·node--check 전건 통과.

### 3.2 결함 — 교차평면 앵커 (최고 심각도, 소유: frontend-developer ± data-engineer)

**[F-2] people.html 에 per-NNN 앵커가 전무 — 59개 인물 앵커 전멸 (D-01·§5.2 위반, 최우선)**
- 증거 쌍: 계약 architecture L192 `"id":"per-001" // 무변형 — people.html#{per-id} 앵커`. ↔ 실측: `pages/people.json` 섹션 id = [graph·family·mentors·comrades·conflicts·patrons·unconfirmed·people-gaps] (per-NNN **0개/8섹션**). people.js 그래프 노드는 `data-node-id`만 부여하고 `id="per-NNN"` 앵커 타깃을 **어디에도 생성하지 않음**(L118 등은 class/layout용 n.id, 앵커 아님).
- 영향: timeline.js actor_refs 링크(`people.html#per-NNN`, 매핑된 53인물)·people.js 그래프 "상세 위치로 이동" 링크·network 경유 per 링크가 **전부 죽은 앵커**(per 59개 전건 무타깃). 클릭 시 아무 데도 안 감.
- 대조: organizations 는 pages/organizations.json 섹션이 org-NNN(22개)이라 page-render가 sec.id로 앵커 생성 → org 앵커 작동(org-002 제외). people 는 동형 구조가 없음.
- 기대: people.html#per-NNN 이 해당 인물로 스크롤(timeline↔people 교차링크 D-01).
- 수정 방향(택1, frontend ± data-engineer 협의): (a) people.js 가 그래프 노드 또는 인물 로스터에 `id="per-NNN"` 앵커 타깃 emit, (b) pages/people.json 에 per-NNN 인물 섹션 추가(org 페이지와 동형) → page-render가 앵커 생성. 데이터 구조 결정 필요.
- 판정: **보류(최우선).**

**[F-1] organizations.html#org-002(구세학당) 앵커 부재 — 1개 죽은 앵커 (소유: frontend-developer ± data-engineer)**
- 증거 쌍: timeline org_refs(+people 그래프)가 `organizations.html#org-002` 링크 생성 ↔ org-002(구세학당, network node 실재)가 pages/organizations.json 섹션에 **없음**(org 노드 22개 중 21개만 섹션 보유).
- 영향: 구세학당 관련 사건의 조직 링크가 죽은 앵커.
- 수정 방향: pages/organizations.json 에 org-002 섹션 추가, 또는 org-002 가 페이지에 없다면 timeline/people 의 해당 링크를 평문화. 데이터 결정 필요.
- 판정: **보류.**

### 3.3 절차 위반 — 결함 미해소 상태 Task 종결
**[T-1 재발] timeline.js 헤더 미주입 결함 미수정 + Task #2 completed 종결.** timeline.js 현재도 mountLayout import·호출 0건, timeline.html 마운트 속성 `data-layout-*`(layout.js 는 `data-site-*` 쿼리) — 회부한 T-1 미수정 상태로 Task #2 가 completed 됐다. timeline.html 은 여전히 헤더·내비·푸터 미렌더. → timeline-developer 재회부, team-lead 에 절차 보고.

**현 판정: people.js network 경계·slot 해소 통과 / F-2(per 앵커 59 전멸)·F-1(org-002 앵커)·T-1(timeline 헤더, 미수정 종결) 보류 회부 / T-2(CSS) team-lead 판정 대기 / archives·gallery 도착분 검사 진행.**

---

## 4. 결함 재검증 + 전체 사이트 게이트 (2026-06-06)

전 10페이지·전 JS 도착. 회부 결함 재검 결과:

### 4.1 결함 재검증 — 전건 해소 확인
| ID | 결함 | 수정 확인 증거 | 판정 |
|---|---|---|---|
| T-1 | timeline 헤더 미주입 | timeline.js L36 `import {mountLayout}` + L685 `mountLayout('timeline')` 호출; timeline.html `data-site-header/footer` 정정 → layout.js 정합 | **통과** |
| T-3 | css/map.css 404 | check_links.py 끊어진 파일 참조 0건(exit 0) | **통과** |
| F-1 | organizations.html#org-002 죽은 앵커 | organizations.js 가 network 로드(L16) + kind=org 노드 중 페이지 미존재분 앵커 스텁 생성(org-002 포함) → org 22개 전건 앵커 해소 | **통과** |
| F-2 | people.html per 앵커 59 전멸 | people.js L205-219 가 kind=person 전 노드의 앵커 스텁(`<span id="per-NNN">`) 생성 + hashchange 자동 상세표시 → per 59개 전건 앵커 해소. org/person 소유 분리(중복 0) | **통과** |

### 4.2 전체 사이트 게이트 (현 상태)
| 검사 | 결과 |
|---|---|
| check_links.py site/ (파일 참조 + 정적 앵커) | **exit 0** — 끊어진 참조 0, 끊어진 정적 앵커 0 (HTML 10·로컬참조 37·앵커 8) |
| check_data_schema.py | **exit 0** — 검사 4611건 PASS |
| 교차평면 동적 앵커(per/org/evt) | 데이터 평면 전수 대조 0 죽은 앵커 + 소비 JS 가 전 노드 앵커 스텁 보장(F-1·F-2 수정) |
| node --check 전 JS(11개) | 0 문법 에러 |
| ES 모듈 import 그래프 | 0 미해소 import |
| 런타임 데이터 로드(http) | 데이터 6 + pages 10 전건 HTTP 200·JSON 파싱 OK; .js MIME=text/javascript(§5.7) |
| 데이터 로드 실패 처리(§3#4) | renderLoadError prepend(빈 화면 금지), 전 10페이지 `<main>` 타깃 보유 — 구조 보장 |
| img alt | JS 렌더 img alt 설정(buildFigure caption||title, gallery/map/timeline) — 정적 img alt 누락 0 |
| 소비 경계면(데이터↔JS) | timeline·map·page-render·footnotes·home·archives·gallery·people·organizations 전건 필드 대조 통과 |

**미완(런타임 한계):** 헤드리스 브라우저(puppeteer/jsdom) 미설치 — 실제 JS 실행 콘솔 에러는 직접 관측 불가. node--check(파싱)+import해소+DOM id 경계+필드 경계 대조로 대체 검증. a11y-engineer 의 브라우저 기반 감사와 분담 필요(키보드·실제 콘솔).

**미판정(거버넌스):** T-2 CSS 아키텍처(모듈별 css vs 단일 main.css) — team-lead 판정 대기. 결정 전까지 보류.

**현 판정: 회부 결함(T-1·T-3·F-1·F-2) 전건 재검 통과 / 링크·앵커·스키마·문법·import 게이트 통과 / T-2 거버넌스 판정 대기 / 실 브라우저 콘솔·키보드는 a11y-engineer 분담.**

---

## 5. 후속 변경 회귀 재검 + 검사 절차 회고 (2026-06-06)

timeline.js·map.js 후속 변경(T-2 관련 추정) 회귀 재검:
- timeline.js: mountLayout('timeline') 1건·deeplink period 처리 5건·actor/org 앵커 링크 `${page}#${node_id}`(L523, null/ambiguous→평문) 유지 — 회귀 없음. node--check OK.
- map.js: has_geo===true 필터·mountLayout('map') 유지. node--check OK.
- import 그래프 0미스, check_links exit 0, check_data_schema exit 0 — 게이트 유지.

### 회고 — 검사 절차의 구멍 (반성성, 체크리스트 갱신)
- **함정: 동적 링크의 literal grep 오탐.** timeline.js actor 앵커가 `${page}#${r.node_id}` 템플릿이라 `people.html#` literal grep 이 0건을 반환 → 회귀로 오인할 뻔. **교훈: 동적으로 합성되는 링크/앵커는 literal 문자열 grep 으로 존재 판정 금지. 반드시 함수 본문(refsLine 등)을 직접 읽어 합성 로직을 확인**하거나, 합성 변수(`${page}`)까지 포함해 grep. → 보고 전 "근거가 grep 부재"인 항목은 코드 본문 직접 확인으로 격상 후 판정.
- **함정: check_links.py 는 정적 HTML href 만 검사 — JS 런타임 합성 앵커(per/org/evt)는 사각.** 이 사이트는 교차링크 대부분이 런타임 합성이라, check_links 통과만으로 앵커 건전성 판정 불가. → 데이터 평면 전수 대조(노드/이벤트 id 우주 vs 소비 JS 가 만드는 앵커 타깃)를 **항상 병행.** F-2(per 59 전멸)는 정확히 이 사각에서 검출됨(check_links 는 exit 0 이었음).
- **추가 체크리스트 항목:** "소비 JS 가 #앵커를 합성하는가? 그렇다면 그 타깃이 페이지에 실제 존재하는가(섹션 id 또는 JS 앵커 스텁)?"를 모듈별 필수 항목으로 등재.

**최종 보류 사유(미충족 2):** ① T-2 CSS 아키텍처 거버넌스 판정(team-lead) ② 실 브라우저 콘솔 에러 0·키보드 도달(a11y-engineer 분담) — 헤드리스 브라우저 미설치로 qa 직접 관측 불가. 두 건 해소 시 최종 게이트 종합.

---

## 6. T-2 거버넌스 판정 수신·반영 (2026-06-06)

team-lead 결정: 모듈별 CSS 파일(timeline.css·map.css) **공식 채택**. 접두 전용·tokens 변수 참조·링크 순서 tokens→main→모듈. → check_links·경계면 우주에 반영(모듈 css 정상 산출물로 인정).

검증 결과 — 결정 정합 확인:
| 항목 | 결과 |
|---|---|
| css 4종(tokens·main·timeline·map) 존재 | ✅ map.css 12KB 도착 |
| 링크 순서 tokens→main→모듈 | ✅ timeline.html·map.html L16-18 정합 |
| 접두 규율 | ✅ timeline.css tl- 91·0 stray / map.css map- 73, 비-map 은 `.leaflet-*`(라이브러리 override, map 한정 — 허용) |
| 토큰 규율(하드코딩 색 금지) | ✅ 전 모듈 css raw hex **0건**. timeline.css `#1A1815` 1건은 주석 내 토큰값 표기(실 CSS 아님) — 위반 아님 |
| check_links | exit 0 |

→ **T-2 종결(통과).** 회고: `#1A1815` 도 주석 내부였음 — grep 매치를 본문(주석/문맥) 확인으로 격상해야 오탐 방지(5절 회고 재확인).

**잔여 게이트 미충족 1건:** 실 브라우저 콘솔 에러 0·키보드 도달(a11y-engineer 분담). favicon.ico 404 셸 소관·콘솔 게이트 제외(프로젝트 합의). a11y 결과 수신 시 최종 게이트 종합.

**현 게이트 판정: 경계면·링크·정적/동적 앵커·스키마·문법·import·CSS(T-2 포함) 전 항목 통과 / 실 브라우저 콘솔·키보드만 a11y-engineer 분담 대기.**

---

## 7. D-25 계약 개정 반영·전 결함 종결 재확인 (2026-06-06)

team-lead 가 architecture.md L610 에 **D-25** 기록(§2·§4·D-15 개정): 모듈별 CSS 공식 채택 — timeline.css(tl- 전용, timeline-dev 소유)·map.css(map- 전용, map-dev 소유), 접두 전용·tokens 변수 의무·하드코딩 hex 금지·링크 순서 tokens→main→모듈·main.css frontend 단독(nw- 포함).

D-25 규율 재검증 — 전건 정합:
| 파일 | 접두 selector | stray | raw hex(실 CSS) | var(--) |
|---|---|---|---|---|
| timeline.css | tl- 82 | 0 | 0 | 247 |
| map.css | map- 67 | 0 (`.leaflet-*` override 허용) | 0 | 177 |
| main.css | tl-0·map-0·nw-32 | — | — | (frontend 단독) |

**메시지 교차 정정(중요):** team-lead 가 "T-1 수정 대기·T-3 파일 생성 시 해소"라 했으나, 실측상 **둘 다 이미 해소**됨(메시지 교차):
- T-1: timeline.js L36 import + L662 `mountLayout('timeline')` 호출, timeline.html `data-site-header/footer`(L22/76) → **수정 완료·통과**(timeline-developer 추가 작업 불요).
- T-3: site/css/map.css 실존(12KB) → **해소·통과**.

→ **회부 결함(T-1·T-2·T-3·F-1·F-2) 전건 종결.** check_links exit 0, check_data_schema exit 0.

**최종 게이트 잔여 1건:** 실 브라우저 콘솔 에러 0·키보드 도달(a11y-engineer 분담, 헤드리스 미설치로 qa 직접 관측 불가). favicon 404 셸 소관 제외. a11y 결과 수신 시 종합.

---

## 8. a11y 감사(_workspace/04_build/a11y_audit.md) 수신·게이트 종합 (2026-06-06)

a11y-engineer 가 headless Chrome(puppeteer) 실측 체계 보유 — 콘솔 에러·키보드 차원을 실측. 그 결과를 게이트에 폴딩.

**상호 교차 확인(독립 일치 — 판정 강화):**
- a11y BLK-1 = qa T-1 (timeline mountLayout 미호출 + data-layout-* vs data-site-* 불일치). 독립 발견·동일 결함, 현재 둘 다 fixed 확인(timeline.js mountLayout('timeline') 1건).
- a11y 콘솔 실측: timeline·map 양 페이지 콘솔 에러 = **favicon 404 1건뿐**(접근성 위반 아님, 셸 소관, 콘솔 게이트 제외 — 프로젝트 합의 일치).
- map: Leaflet 차단/허용 2모드 실측 0 차단, 거점 목록 1급 폴백 통과.

**a11y 미해소(게이트 영향) — 내 게이트 판정에 반영:**
- **BLK-2(frontend): skip-link 부재.** layout.js 가 skip-link 미생성. 실측: 정적 HTML skip-link 보유 = 8/10 페이지, **timeline.html·map.html 만 0**(skip-link=0). frontend 8페이지는 정적 추가했으나 timeline·map 미추가 → a11y 차원 불일치. a11y 소관(접근성)이나, "콘솔/키보드 게이트" 미충족 사유로 종합에 포함. a11y 에 관측 공유(중복 채널 회피, 재라우팅 안 함).
- **a11y 감사 범위: 현재 timeline·map 2페이지만.** 나머지 8페이지(index·life·org·philosophy·people·archives·gallery·references) 콘솔/키보드 **미감사** → 사이트 전역 "콘솔 에러 0" 아직 미선언 가능.

**게이트 종합 판정(정직):**
- **QA 자동 검사 차원: PASS** — 경계면 교차 비교·링크·정적/동적 앵커·스키마(4611)·문법·import·CSS(D-25) 전 항목 통과, 회부 결함(T-1·T-2·T-3·F-1·F-2) 전건 종결.
- **콘솔 에러 0 차원: 부분 통과** — a11y 실측 2페이지는 favicon 외 0건. 잔여 8페이지 a11y 콘솔 실측 대기.
- **키보드/접근성 차원: a11y 소관, BLK-2(skip-link) + 8페이지 감사 잔여.**
→ **최종 사이트 게이트: 보류.** QA 단독 책임 영역(경계면·링크·스키마)은 전건 통과 선언 가능. 사이트 전체 게이트는 a11y 의 (a) 잔여 8페이지 콘솔/키보드 실측 (b) BLK-2 skip-link 해소 후 종합.

---

## 9. 교차평면 결함 재확인 + 신규 게이트 항목 (2026-06-06)

team-lead 정리 2건 처리. 스캔 경로 라이브 확인: site/ realpath=`/Users/robin/Downloads/DOSAN/site`, timeline.js mtime 20:01 — 캐시·사본 아님(라이브 디스크).

**① T-1 종결 재확정.** 라이브 기준 timeline.js L662 `mountLayout('timeline')` 호출·timeline.html L22 `data-site-header` 정합. **통과 확정.** (3회째 회부는 늦게 도착한 이전 메시지 — 현재 결함 아님. timeline-developer 에 통과 확정 회신.)

**[X-1] timeline.html → map.html#evt-NNN 113건 딥링크 — 검증 통과 (소유: map-developer, §3.1).**
- 증거 쌍: timeline.js L225/L452 가 has_geo 사건마다 `map.html#${ev.id}` "지도에서 보기" 링크 생성(has_geo=113건 → 113 링크) ↔ map.js 가 수신 측 핸들러 보유:
  · L389/L403: `markersByEventId` — placeGroups 의 **모든 사건 id → 거점 마커** 매핑(같은 좌표=같은 거점). 113 evt-id 전건 커버.
  · L556-588 `focusEventFromHash()`: evt-id 형식 검증 → 시기필터 전체해제(딥링크 우선) → (지도) flyTo+openPopup+live, (폴백) 거점목록 카드 scrollIntoView+하이라이트+live, (미존재) 무해 console.warn.
  · L602 초기 hash 처리 + L603 hashchange 리스너.
- 폴백 모드(Leaflet 차단)에서도 거점 목록 카드로 스크롤 — 동등 동선 보장.
- 판정: **통과.** 113 딥링크 전건 마커 또는 목록 카드로 해소(끊어진 앵커 0). frontend 검출은 이전 스냅샷 기준(현재 map.js 에 핸들러 구현 완료).
- 게이트 체크리스트 등재: "timeline↔map evt 딥링크(map.html#evt) 수신 핸들러 존재·전건 해소" — 현 상태 통과.

→ **교차평면 딥링크(timeline→map evt 113·timeline→people per·timeline→org·archives/people→timeline evt) 전 평면 해소 확인.** check_links exit 0(정적), 동적 딥링크는 소비 JS 핸들러+데이터 우주 대조로 전건 통과.

---

## 10. timeline 모듈 완성 통보 — 정식 incremental QA (2026-06-06)

timeline-developer 정식 완성 통보 수신. 자가검증 주장을 데이터로 독립 재현·검증.

**자가검증 주장 데이터 재현(독립 확인):**
- 소비 필드 전건 데이터 실재(post-refactor 재확인, 팬텀 0). node --check OK.
- disputed 17건 전건 dispute객체+note 보유. adopted.precision=null = **evt-early-006·evt-shin-016 정확히 2건**(주장 일치).
- 필터 카운트 데이터 재현: P3=26·P3+결사=20·P8+결사=2 (자가검증 주장과 전건 일치).
- timeline.css D-25 정합(tl-82·stray0·raw hex0).

**개발자 설계 판단 질의 검토 — 승인:**
질의: "timeline sources 에 source_id 가 없어 references 앵커 매핑 불가 → url/title/type/locator 만 표시(추측 매핑 안 함)."
검증: timeline source 572엔트리 필드 = {type,title,locator,url}뿐, **source_id/id/ref 0건**. citations.sources 와 URL 일치는 141/155 이나 title 일치 2/237 — URL 매칭은 fuzzy·lossy 휴리스틱이라 강제 시 §5.2/D-01 "추측 매핑" 위반. → **직접 표시가 계약 정합. 설계 판단 승인**(references 앵커 강제 안 한 것이 옳음).

**판정: timeline 모듈 QA-소관 차원 전건 통과(통과).** 경계면·딥링크·날짜정직성(데이터 재현)·dispute·CSS·문법·import·source 설계 모두 통과. T-1(헤더) 기수정 확인. 잔여는 모듈 무관 공통 항목 — 콘솔(favicon만, 셸 제외)·skip-link(BLK-2)는 a11y 소관·전 페이지 공통.

---

## 11. map 모듈 완성 통보 — 정식 incremental QA (2026-06-06)

map-developer 정식 완성 통보. 자가검증 카운트를 데이터로 독립 재현·검증(존재 확인 아님).

**개발자 명시 질의 — map.js 소비(place.lat/lng·has_geo·period) ↔ timeline.json 실 필드 일치: 확인.**
| map.js 소비 | 데이터 | 판정 |
|---|---|---|
| has_geo & place.lat/lng numeric | 113 events | 통과 |
| id·title·date(start)·place.name·summary·period·confidence | geo 113 전건 존재 | 통과 |

**자가검증 카운트 데이터 재현(전건 일치):**
- 거점(distinct coord 마커): **28** (주장 일치).
- 시기별 거점: P1=5·P3=11·P7=3·P8=1 (주장 전건 일치).
- confidence==D 누출: **0** (D-exclusion 클린).
- map.json 각주: [ref:] 마커 41(distinct 18), 끊어진 각주 **0** (citations.refs 전건 해소).
- node --check OK. map.css D-25 정합(map-68·stray0·raw hex0).
- 딥링크 X-1(map.html#evt 113) 핸들러·경로 R1~R5 waypoint 해소·mountLayout('map')·폴백(Leaflet 차단→거점목록)은 9·11절에서 검증 완료(유지).

**판정: map 모듈 QA-소관 차원 전건 통과(통과).** 회부 결함 0. 잔여 모듈 무관 공통(favicon 콘솔·skip-link BLK-2)은 a11y 소관.

**3개 구현 모듈(timeline·map·frontend) incremental QA 전건 통과.** 사이트 전역 게이트 잔여 = a11y 콘솔(8페이지)·키보드·BLK-2 뿐. 그 수신 후 최종 종합.

---

## 12. T-1 수정 재검증 (timeline-developer 수정 통보, 2026-06-06)

라이브 디스크 재검(이전 상태 신뢰 안 함 — timeline.js 라인 재배치 확인: mountLayout L685→L662, 편집 발생):
- timeline.html L22 `data-site-header`·L76 `data-site-footer` ↔ layout.js L119/L168 쿼리 정합. (data-layout-* 잔존 0.)
- timeline.js L36 `import {mountLayout}` + L662 `mountLayout('timeline')` — **init() 최상단(L658→661 try→662), 데이터 로드(L671)보다 먼저** 호출(셸 우선 → 로드 실패 시에도 내비 가능 셸 안에서 에러 UI). try/catch(L661-663)로 격리.
- 회귀 가드: core 렌더 참조(tl-event-card·buildCard·disputed·renderLead·allEvents) 유지, node --check OK. 연표 본체 회귀 없음.
- layout.js 가 `[data-site-header]`/`[data-site-footer]` 쿼리(L119/168) — 수정이 올바른 속성 타깃.

→ **T-1 재검증 통과(종결).** 근본 원인(공유 모듈 마운트 속성 추측)은 [[read-shared-module-contract-not-guess]] 교훈과 일치 — 개발자도 "소스 확인 없이 추측" 자인. 회부→수정→재검 사이클 완결.

---

## 13. frontend 8페이지+공유모듈 완성 통보 — 정식 incremental QA (2026-06-06)

frontend-developer 정식 완성 통보(8페이지 + loader/layout/footnotes/page-render + main.css). 자가검증 주장을 데이터 평면 전수 재현(존재 확인 아님 — 실제 체인 재현).

**자가검증 데이터 재현 — 전건 일치:**
| 주장 | 독립 재현 결과 |
|---|---|
| 각주 무결성(끊어진 각주 0) | [ref:] 마커 **1211건 전수** 스캔(전 page JSON + network + archives) → broken ref 0·broken source 0. ref→source_id→source 체인 전건 해소 |
| meta.json 정합(하드코딩 0) | home 통계 9수치 전건 실제 레코드 수 일치(165·17·59·22·135·19·194·47·80) |
| alt 100건 누락 0 | images 80건 전건 caption/title(alt 소스) 보유 — 누락 0 |
| 교차앵커(F-1·F-2) 해소 | people.js·organizations.js network 앵커 스텁 — 앞서 검증 완료(2·3절) |
| check_links/schema | exit 0 / exit 0 (4611) |

**개발자 재지적 X-1(map.html#evt 113) — stale 정정:** frontend 가 끊어진 앵커로 재지적했으나, map.js 에 수신 핸들러(markersByEventId·focusEventFromHash·hashchange) **이미 구현·검증 완료**(9·11절 X-1 통과). frontend 검출은 수정 전 스냅샷. → map 결함 아님, frontend 에 stale 정정 회신.

**판정: frontend 모듈 QA-소관 차원 전건 통과(통과).** 회부 결함 0.

### ★ 콘솔 차원 게이트 진전 — 전 10페이지 측정 완료
frontend headless Chrome 실측: 8페이지(index·life·org·philosophy·people·archives·gallery·references) 콘솔 에러 0·pageerror 0·로드에러 0. a11y 실측: timeline·map = favicon 404 외 0. → **전 10페이지 콘솔 측정 완료, 모듈 에러 0**(favicon 404만, 셸 소관·게이트 제외). 게이트 "콘솔 에러 0(전 페이지)" 항목 **충족.**

### 게이트 종합 갱신
- QA 자동 검사(경계면·링크·앵커·스키마·문법·import·CSS): **PASS.**
- 콘솔 에러 0(전 10페이지, favicon 제외): **PASS**(frontend 8 + a11y 2 측정 종합).
- 회부 결함(T-1·T-2·T-3·F-1·F-2·X-1): 전건 종결.
- **잔여(a11y 소관):** BLK-1 a11y측 재측정 클리어(코드는 수정됨), BLK-2(skip-link timeline·map 2페이지), 8페이지 키보드 실측 — a11y 결과 수신 후 최종.

---

## 14. a11y 감사 완료 수신 — 최종 사이트 게이트 종합 (2026-06-06)

a11y Task #4 completed. a11y_audit.md §2.4(전 10페이지 재검증) 수신·교차 확인.

**a11y 최종 결과(§2.4 — headless Chrome 재실측):** 차단 2·중대 2·경미 2 발견 → **차단·중대 4건 전건 해소 재검증 완료.** 잔여 경미 2건(JSON-LD·og 보조태그)은 비차단 권고.
- BLK-1(timeline mountLayout)=내 T-1 → 해소(a11y 독립 재측정 일치).
- BLK-2(skip-link) → 해소(10/10 페이지).
- NW-1(people SVG role 충돌, a11y 신규 검출) → 해소.
- REF-1(archives reflow)·CONT-2(map 배지 라벨)·SEO3(OG) → 해소.

**★ 정적 grep vs 런타임 불일치 — 라이브 재확인으로 해소(오탐 방지):**
내 정적 grep 은 timeline·map skip-link=0, 전 페이지 og:=0 으로 나왔으나, **layout.js 가 mountLayout 에서 런타임 주입**함을 소스 확인:
- L91-122: skip-link 전 페이지 단일 주입(정적 보유 8페이지는 dedupe, timeline·map 은 JS 주입) → post-JS DOM 10/10.
- L69-87: og:title/type/locale/site_name/description 런타임 주입(정적 OG 있으면 dedupe) → 10/10.
- people.js L92 role:'group'·L123 role:'button' 확인(NW-1).
→ a11y 의 headless(post-JS) 측정이 정답, 내 정적 grep 이 사각. [[dosan-runtime-synthesized-anchors]] 교훈 재적용 — 런타임 주입 요소는 정적 grep 판정 금지.

### ★ 최종 사이트 게이트 종합 (web-qa-protocol §3 체크리스트)
| # | 항목 | 방법 | 결과 |
|---|------|------|------|
| 1 | 내부 링크·리소스 전수 | check_links.py | **PASS** exit 0 (정적 앵커 0 broken) |
| 1b | 교차평면 동적 앵커(per59·org22·evt165·map#evt113) | 데이터 우주 대조 + 소비 JS 핸들러/스텁 | **PASS** 0 broken |
| 2 | 데이터 스키마 | check_data_schema.py | **PASS** exit 0 (4611) |
| 2b | 경계면 교차 비교(14 JS↔데이터) | 필드 전수 대조 | **PASS** 팬텀 0 |
| 2c | 각주 무결성([ref:] 1211 체인) | ref→source_id→source 전수 | **PASS** broken 0 |
| 3 | 콘솔 에러 | frontend 8 + a11y 2 headless 실측 | **PASS** 모듈 에러 0 (favicon 셸 제외) |
| 4 | 데이터 로드 실패 처리 | loader.renderLoadError prepend·10페이지 main | **PASS** 빈 화면 금지 보장 |
| 5 | 반응형 360/768/1280 | a11y headless 실측 | **PASS** 가로스크롤·겹침 0 |
| 6 | 이미지 alt | a11y 전담 실측 | **PASS** 100건 누락 0 |
| 7 | 키보드 | a11y 전담 실측(전 페이지·dialog·슬라이더·그래프) | **PASS** |
| — | CSS D-25·문법·import·meta 정합 | qa | **PASS** |

**회부 결함 전건 종결:** T-1·T-2·T-3·F-1·F-2·X-1(qa) + BLK-1·BLK-2·NW-1·REF-1·CONT-2·SEO3(a11y). 잔여 비차단 권고 2건(JSON-LD·og 보조태그)은 게이트 판정 무영향.

**★ 최종 게이트 판정: PASS.** 게이트 기준(전 페이지 QA 통과 + 콘솔 에러 0 + 끊어진 링크 0) 전건 충족. QA 자동 검사 차원 + a11y 브라우저 실측 차원 종합 통과. 미검사 항목 0(성능 예산은 performance-optimizer 소관 — 별도 Task).

---
