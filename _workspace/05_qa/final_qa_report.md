# 최종 통합 QA 보고서 — Phase 5 (qa-engineer, 최종 통합 패스)

> 기준: `.claude/skills/web-qa-protocol/SKILL.md` + `architecture.md` v1.0 §3 계약.
> 원칙: "파일이 존재한다"는 통과 사유 아님 — 판정은 스크립트 실행 결과·경계면 교차 비교 증거로만.
> 성격: Phase 4b 게이트(qa_log.md 14절·a11y_audit.md)의 **독립 재확인 패스**. 4b의 PASS 선언을 신뢰하지 않고, 스크립트를 재실행하고 데이터·코드를 독립 표본으로 재대조했다.
> 환경: `cd site && python3 -m http.server` (file:// 금지 — architecture §5.1). 직접 수정 금지(소유권 해체 상태) — 결함은 심각도 분류 + 수정안만 명시.
> 실행 일자: 2026-06-06.

---

## 0. 검사 범위·증거 보존 원칙

본 패스는 6개 과업을 수행했다: ① check_data_schema.py 재실행 ② check_links.py 재실행 ③ 전 자산 HTTP 200 ④ 전 JS node --check + ES import 그래프 ⑤ 4b 게이트 항목(각주 체인·교차평면 딥링크·disputed·D 부재) 독립 재확인 ⑥ 결함 심각도 분류.

모든 스크립트 출력 전문(exit code 포함)을 아래에 인용한다.

---

## 1. 스크립트 재실행 결과 (exit code · 출력 요약)

### 1.1 check_data_schema.py — **exit 0 (PASS)**

```
$ python3 _workspace/04_build/scripts/check_data_schema.py
============================================================
check_data_schema — site/data 무결성 재검사
============================================================
검사 수행: 4611

[PASS] 전 검사 통과 — site/data 무결성 확인
EXIT_CODE=0
```

검사 4611건 전건 통과. 검사 범위(스크립트 docstring): timeline 165건·D 0·disputed 17·precision/calendar, network 노드 81·엣지 135·끊어진 엣지 0·unconfirmed 19 분리, citations refs 155·sources 194·끊어진 참조 0, images 80·file 실재, archives 47·related_event 렌더사건만 참조, meta 수치 ↔ 실제 레코드 정합, pages/*.json blocks 유형·[ref:] 마커 정의 검사.

### 1.2 check_links.py — **exit 0 (PASS, 끊어진 파일 참조 0)**

```
$ python3 _workspace/04_build/scripts/check_links.py site/
검사: HTML 10개, 로컬 참조 37건, 앵커 8건
[id 우주] evt 165·per 59·org 22·src-pri 47·source 194·image 80

[참고] 외부 URL 8건 — 존재 검사 제외 (fonts.googleapis / unpkg leaflet / jsdelivr pretendard / data: favicon)
[결함/주의] 앵커 8건: 전부 `#main` (skip-link 타깃)
EXIT_CODE=0
```

- **끊어진 로컬 파일 참조: 0건.** exit 0.
- 앵커 8건 경고(`#main`)는 **모두 검증된 오탐(false positive)** — 1.3절 참조.
- 외부 URL 8건은 네트워크 의존 배제로 존재 검사 제외(스킬 규정). 도메인 표본: Google Fonts·unpkg Leaflet 1.9.4(CDN, map만 §5.9)·jsdelivr Pretendard·data: SVG favicon — 전부 정상 출처.

### 1.3 `#main` 앵커 경고 8건 — 오탐 확정 (결함 아님)

check_links.py는 **정적 HTML만** 본다. 전 페이지 `<a class="skip-link" href="#main">`(또는 timeline·map은 런타임 주입)의 타깃 `#main`이 정적 HTML에 없어 "죽은 앵커"로 보고된다. 그러나 `js/layout.js`의 `ensureSkipLink()`(L96–124)가 **런타임에** `<main id="app">`에 `id="main"`을 부여하거나 `<a id="main">` 내부 앵커를 prepend한다. 따라서 post-JS DOM에서는 `#main` 타깃이 10/10 페이지에 실재.

- 교차 확인: a11y_audit.md §2.4 — headless Chrome 실측 "skip-link href=#main·#main 타깃 존재 10/10 PASS"(독립 일치).
- 교훈 적용: 런타임 합성 앵커는 정적 grep/링크검사로 판정 금지(qa_log §5·§14 회고와 동일).

---

## 2. HTTP 200 전 자산 검사 (`python3 -m http.server -d site`)

`cd site && python3 -m http.server` 환경에서 전 자산 curl 응답 코드 대조.

| 자산군 | 검사 수 | 200 | 비-200 |
|---|---|---|---|
| HTML 10페이지 | 10 | 10 | 0 |
| CSS (tokens·main·timeline·map) | 4 | 4 | 0 |
| JS (14 모듈) | 14 | 14 | 0 |
| data/*.json (top-level 6) | 6 | 6 | 0 |
| data/pages/*.json (10) | 10 | 10 | 0 |
| **소계(핵심 자산)** | **44** | **44** | **0** |
| 본문 이미지 (images.json file 전수) | 80 | 80 | 0 |
| **총계** | **124** | **124** | **0** |

- MIME 타입(ES module 필수, §5.7): `js/*.js` → `text/javascript` ✅ / `data/*.json` → `application/json` ✅. ES module import가 정상 동작할 MIME 보장.
- 비-200 응답 0건. 데이터 로드 실패·404 자산 없음.

---

## 3. 전 JS node --check + ES import 그래프

### 3.1 node --check (문법 검사) — **14/14 PASS**

`node v22.22.3` 기준 14개 JS 전건 `node --check` 통과(문법 에러 0): loader·layout·footnotes·page-render·home·life·timeline·map·organizations·philosophy·people·archives·gallery·references.

### 3.2 ES import 그래프 — **0 미해소 import**

각 모듈의 export 심볼 ↔ 소비처 import 심볼 전수 대조(static `import {} from` + dynamic `await import()`):

| 모듈 | export 심볼 |
|---|---|
| loader.js | loadData · loadAll · renderLoadError |
| layout.js | mountLayout |
| footnotes.js | buildCitationIndex · renderFootnotes |
| page-render.js | periodOf · renderInline · renderBlocks · buildFigure · renderPage · makeSlotResolver |

- 소비처가 import하는 전 심볼(loadAll·loadData·mountLayout·renderPage·renderBlocks·makeSlotResolver·buildFigure·renderInline·renderFootnotes·renderLoadError)이 **전건 실제 export에 해소.** 미해소 import 0건.
- 동적 import 2건(map.js L627 `const {renderFootnotes}=await import('./footnotes.js')`, timeline.js L643 `mod.renderFootnotes`) 모두 footnotes.js의 named export로 해소.
- 다작성자 코드의 전형적 실패 모드(JSON `date.start` ↔ JS `date_start`류 경계 불일치)에 대응하는 import-level 미스 0.

> 검사 노트: `grep -oE "export function"`이 page-render.js에서 빈 결과를 반환했으나, 파일 Read·Python 정밀 파서·node --check·실제 import 해소 4중 교차로 6개 export 실재 확정. grep 단독 부재를 결함으로 격상하지 않음(qa_log §5 "근거가 grep 부재인 항목은 본문 직접 확인으로 격상" 교훈 적용).

---

## 4. Phase 4b 게이트 독립 재확인 (독립 표본 재대조)

4b의 판정을 신뢰하지 않고, site/data 실 레코드와 소비 JS를 **직접 재대조**했다.

### 4.1 D등급 데이터 부재 (site/data에 D 0건) — **PASS**

| 검사 | 결과 |
|---|---|
| timeline `confidence=='D'` | **0건** |
| 알려진 D id 7종 본체 잔존(evt-early-002 등) | **0건** |
| network `edges_unconfirmed`(19) ↔ 본체 `edges`(135) 혼입 | **0건** |
| network 본체 edges `grade=='D'` | **0건** |
| `edges_unconfirmed` 19건 전부 D등급인가 | **0건 비-D** (전부 D 확인) |

D등급·미확정 관계의 본체 노출 0 — architecture §5.4·D-02·D-04, 00_common §6.1 충족.

### 4.2 disputed 표현 — **PASS**

| 검사 | 결과 |
|---|---|
| `disputed==true` 건수 | **17건** (계약 17 일치) |
| disputed인데 `dispute`/`dispute_note` 부재 | **0건** |
| `dispute` 객체 보유 | **17/17** |
| `adopted.precision==null` (사건 자신 date 권위) | **2건** — `evt-early-006`·`evt-shin-016` |

소비측: timeline.js가 disputed 카드에 ⚑"기록 상충" 텍스트 라벨(색 단독 의존 금지) + `dispute_note` + adopted 채택안 우선 + variants 이설 접기를 렌더(L22–24, L162–216, L414). `adopted.precision=null`이면 사건 date를 권위로 표시(D-16 양론 병기 계약 충족).

### 4.3 각주 체인 `[ref:ref-NNN] → refs → source_id → sources → references.html#{source_id}` — **PASS**

| 검사 | 결과 |
|---|---|
| 전 데이터 [ref:] 마커 총수 | **1217건** (distinct 155) |
| `refs[]`에 없는 마커(끊어진 각주) | **0건** |
| `source_id` 미존재(끊어진 출처) | **0건** |
| 잠정 마커(clm-/evt-/cfl-/src-pri-) 본문 잔존 | **0건** |

- 마커 분포: life 465·organizations 257·people 203·philosophy 119·archives 97·map 41·home 27·timeline(도입문) 2·images(캡션) 6 = 1217.
- **마커 총수 reconcile:** qa_log §13은 1211로 보고. 차이 6건은 본 패스가 `images.json` 캡션 마커(6건)까지 포함한 스코프 차이 — **두 집계 모두 broken 0**이므로 결함 아님. 본 패스가 더 넓은 표본을 검사했음을 명시.
- 체인 최종 홉 검증: footnotes.js가 `references.html#${source.id}` 링크 생성(L138/L175), references.js가 sources 194건 전건 `li.id=src.id` 앵커 렌더(L29) — 종착점 앵커 194/194 실재. 끊어진 각주 0.

### 4.4 교차평면 딥링크 (timeline↔map·people·organizations·archives) — **PASS**

| 딥링크 평면 | evt/node 우주 이탈 |
|---|---|
| archives `related_event_ids` → evt 우주(165) | **0건** (D-24 merged_from 해소 검증) |
| network `evidence_event_ids` → evt 우주 | **0건** |
| timeline `actor_refs.node_id` → per 우주(59) | **0건** (cross-kind 오해소 0) |
| timeline `org_refs.node_id` → org 우주(22) | **0건** |
| `has_geo==true` (map.html#evt 딥링크 대상) | **113건** (meta 113 일치), 전부 evt 우주 부분집합 |

소비측 핸들러 확인:
- timeline→map: map.js `markersByEventId`·`focusEventFromHash()`·hashchange 리스너 — 113 evt 딥링크 전건 마커 또는 폴백 거점 목록으로 해소(qa_log §9 X-1 일치).
- timeline→people/org: timeline.js가 `${page}#${node_id}` 합성(null/ambiguous→평문). people.js·organizations.js가 kind=person/org 전 노드 앵커 스텁 생성(per 59·org 22 전건 타깃 보장, qa_log §3–4 F-1·F-2 해소 일치).

---

## 5. 결함 목록 (심각도 분류)

직접 수정 금지(소유권 해체 상태) — 수정안만 명시. 본 최종 패스에서 **차단·중대·경미 신규 결함 0건.** 4b 회부 결함(T-1·T-2·T-3·F-1·F-2·X-1 / BLK-1·BLK-2·NW-1·REF-1·CONT-2·SEO3)은 4b에서 전건 해소 재검증 완료 상태이며, 본 패스의 독립 재대조에서 재발 0 확인.

| ID | 심각도 | 항목 | 상태 | 수정안 |
|---|---|---|---|---|
| OBS-1 | 정보(결함 아님) | check_links `#main` 앵커 8건 경고 | 오탐 확정 | layout.js 런타임 주입으로 post-JS 해소. 조치 불요. (선택: HTML에 `id="main"` 정적 명시 시 정적 검사도 클린) |
| OBS-2 | 정보(결함 아님) | favicon.ico 404 | 해소됨 | layout.js `ensureFavicon` data-URI SVG 주입 — 콘솔 404 0 (a11y 실측). |
| REC-1 | 경미·권장(비차단) | SEO5 JSON-LD 미구현 | 잔여 권고 | 구조화 데이터 점진 추가. 게이트 무영향. |
| REC-2 | 경미·권장(비차단) | og:url·og:image null | 잔여 권고 | 공유 카드 완성도. og:title/description/type는 구현됨(SEO6 검증, 새 사실 문장 0). 게이트 무영향. |

**런타임 콘솔 에러 직접 관측 한계(검사 한계 명시):** 본 패스는 헤드리스 브라우저로 JS 실행 콘솔을 직접 관측하지 않았다(node --check + import 해소 + DOM id 경계 + 데이터 경계 대조로 정적 차원 검증). 콘솔 차원은 a11y-engineer의 headless Chrome 실측(전 10페이지 consoleErr 0, pageError 0 — a11y_audit §2.4)과 frontend headless 측정(8페이지 0)으로 충족됨을 **수신·교차 확인**하여 게이트에 폴딩한다.

---

## 6. 4b 게이트 판정 독립 교차 확인 (qa_log·a11y_audit 표본)

- **qa_log.md §14 최종 게이트 PASS** ↔ 본 패스: check_data_schema(4611)·check_links(파일 0 broken)·교차평면 앵커 0·각주 1217 broken 0·node--check 14·import 0미스 **전건 독립 재현 일치.**
- **a11y_audit.md §2.4 전 10페이지 통과**(차단 2·중대 2 전건 해소, 경미 2 권고) ↔ 본 패스: `#main` 오탐·favicon 해소·skip-link 런타임 주입 **독립 일치.**
- 분담 경계: 경계면 교차 비교·링크·스키마·앵커·import = 본 패스 직접 검증. 키보드·색 대비·반응형·실 브라우저 콘솔 = a11y-engineer 실측 수신(중복 검사 회피, 협력성). 성능 예산 = performance-optimizer 별도 Task 소관.

---

## 7. 최종 게이트 판정

| 게이트 항목 (web-qa-protocol §3) | 방법 | 결과 |
|---|---|---|
| 1. 내부 링크·리소스 전수 | check_links.py | **PASS** exit 0 (파일 0 broken) |
| 1b. 교차평면 동적 앵커(per59·org22·evt165·map#evt113) | 데이터 우주 대조 + 소비 JS 핸들러/스텁 | **PASS** 0 broken |
| 2. 데이터 스키마 | check_data_schema.py | **PASS** exit 0 (4611) |
| 2b. 경계면 교차 비교(데이터↔소비 JS) | 필드 전수 대조 | **PASS** D 0·disputed 17·node_id 우주 0이탈 |
| 2c. 각주 무결성([ref:] 1217 체인) | ref→source_id→source→앵커 전수 | **PASS** broken 0 |
| 3. 콘솔 에러 | a11y/frontend headless 실측 수신 + node--check·import | **PASS** 모듈 에러 0 (favicon 해소) |
| 4. 데이터 로드 실패 처리 | loader.renderLoadError + 10페이지 data-load-error 타깃 | **PASS** 빈 화면 금지 보장 |
| 5. 반응형 360/768/1280 | a11y headless 실측 수신 | **PASS** 가로스크롤·겹침 0 |
| 6. 이미지 alt | a11y 전담 실측 수신 + images 80 caption/title 보유 | **PASS** 누락 0 |
| 7. 키보드 | a11y 전담 실측 수신 | **PASS** |
| HTTP 200 전 자산 | http.server 124자산 | **PASS** 비-200 0 |
| node --check 전 JS | node v22 | **PASS** 14/14 |
| ES import 그래프 | export↔import 전수 | **PASS** 0 미해소 |
| 8. 성능 예산 | performance-optimizer 별도 Task | (소관 외 — 본 패스 미검사, 명시) |

**미검사 명시(보수적 보류 원칙):** 성능 예산(§3-8)은 performance-optimizer 소관으로 본 QA 패스 범위 외. 실 브라우저 콘솔·키보드·반응형·대비는 a11y-engineer 실측 결과 수신으로 충족 확인(qa 직접 헤드리스 미실행 — 분담).

### ★ 최종 게이트 판정: **PASS (통과)**

QA-소관 자동 검사 전 차원(스키마·링크·교차평면 앵커·각주 체인·경계면 교차 비교·문법·import·HTTP·MIME) 독립 재실행·재대조 전건 통과. 신규 차단·중대 결함 0건. 4b 회부 결함 전건 해소 재발 0. 잔여 2건(JSON-LD·og 보조태그)은 비차단 권고로 게이트 무영향. a11y·콘솔·반응형·키보드 차원은 a11y-engineer 실측 수신으로 충족. 성능 예산만 performance-optimizer 소관으로 본 패스 범위 외(미검사 명시).

---

## 부록 A. 검사 환경·재현

- 데이터: `site/data/*.json`(6 top-level + 10 pages), `assets/images/`(80 webp).
- 코드: `site/*.html`(10), `site/js/*.js`(14), `site/css/*.css`(4).
- 계약 기준: `_workspace/04_build/architecture.md` v1.0 §3(인터페이스 계약·소비 필드 목록).
- 스크립트: `_workspace/04_build/scripts/check_data_schema.py`, `check_links.py`.
- 서버: `cd site && python3 -m http.server`.
- node: v22.22.3.
- 수신 자료: `_workspace/04_build/qa_log.md`(14절), `a11y_audit.md`(§2.4 게이트 종결).
