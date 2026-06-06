# 사이트 아키텍처 — 도산 안창호 일대기 (architecture.md)

> **상태: 확정 v1.0 (2026-06-06) / 작성: web-architect (21)**
> 본 문서는 Phase 4b 구현 팀(frontend-developer·timeline-developer·map-developer·a11y-engineer·qa-engineer)의 **단일 진실 공급원**이다. 추측 금지 — 구현 중 본 문서에 없는 결정이 필요하면 web-architect에게 SendMessage로 질의하고, 답변과 동시에 본 문서를 보강한다.
> 입력(전부 동결본): `_workspace/03_content/`(sitemap.md v1.0·page_specs 11종·drafts 10종·citations.json·images/manifest.json), `_workspace/02_verified/`(timeline.json 172건·network.json v1.2.1-phase2·claims_register.json 305건).
> 승계 계약: sitemap.md §4(앵커=데이터 id 무변형)·00_common.md §3(마커·메타 예외)·§6.1(D등급 차단)·§8(완성 게이트)는 본 문서가 **그대로 승계**한다. 본 문서와 00_common이 어긋나면 즉시 본 문서를 정정한다.
> 합의 상태: data-engineer 스키마(§3 전체·D3·D6·제안 8건)·ui-designer 경계(§4·D-14·D-15) **합의 완료**. 본 v1.0이 4b 팀 확정 계약이다.

---

## 0. 이 문서를 읽는 법 (Phase 4b 개발자용)

- **§1 스택·§2 디렉토리**: 무엇으로 어디에 만드는가. 한 번 읽고 따른다.
- **§3 인터페이스 계약**: 네가 읽을 데이터의 정확한 모양. 구현 전 네 담당 계약을 정독하라. 소비 필드 목록이 곧 QA 대조 기준이다.
- **§4 파일 소유권**: 네가 만질 수 있는 파일. 소유 아닌 파일은 직접 수정 금지.
- **§5 함정·회피책**: file://, 데이터 누락, null 처리 등 터질 게 뻔한 것들. 구현 전 읽어야 디버깅 턴을 아낀다.
- **§6 작업 분해(WBS)·§7 결정 기록**: 누가 무슨 순서로, 그리고 왜 이렇게 정했는가.

---

## 1. 기술 스택 — 빌드 도구 없는 정적 사이트 (확정)

**확정 스택: HTML5 + CSS(커스텀 프로퍼티) + vanilla JS(ES modules) + JSON 데이터. 외부 의존은 Leaflet 1.9.x(지도) CDN만.**

| 항목 | 결정 |
|------|------|
| 마크업 | 시맨틱 HTML5. 각 페이지는 정적 골격 + JS 데이터 렌더. |
| 스타일 | 순수 CSS. 디자인 토큰은 CSS 커스텀 프로퍼티(`--`)로 `tokens.css`에 집중. 전처리기·프레임워크 없음. |
| 스크립트 | vanilla JS, **ES modules**(`<script type="module">`). 번들러·트랜스파일 없음 — 브라우저가 모듈을 직접 로드. |
| 데이터 | `site/data/*.json`을 `fetch`로 로드해 렌더. **HTML에 사실 텍스트 하드코딩 금지**(검증 DB 대조 경로 단절 방지 — site-architecture §4). |
| 외부 라이브러리 | **Leaflet 1.9.x만**(CDN). 지도 타일·마커·폴리라인. 그 외 라이브러리·프레임워크·번들러 도입 전면 금지. |
| 로컬 서빙 | `cd site && python3 -m http.server 8000` → `http://localhost:8000`. **file:// 직접 열기 금지**(§5.1). |
| 배포 | 정적 호스팅(GitHub Pages·S3·로컬 디스크) 그대로. 빌드 단계 없음 = 파일 복사가 곧 배포. |

**이유(근거 기록):** 의존성 부패 0(10년 뒤에도 열려야 하는 역사 아카이브), 어디서나 서빙, 에이전트 병렬 작업 시 빌드 충돌 0(작성한 파일이 곧 실행 결과). 상세는 site-architecture §1.

**Leaflet 도입 사유서(위험성향 3 — 유일 외부 의존):** 문제 = 활동 지도(map.html)의 인터랙티브 좌표 시각화(타일·마커·팝업·경로 폴리라인·줌/팬). vanilla로 불가한 이유 = 슬리피 맵 타일 좌표 변환·줌 레벨별 타일 페칭·드래그 패닝을 직접 구현하면 수천 줄의 검증 안 된 코드가 되고, 그 자체가 결함원. 대안 비교 = (a) 직접 구현 → 유지 비용 과다·버그 위험, (b) Mapbox/Google → API 키·과금·추적·CDN 의존 동일하나 라이선스 제약 추가, (c) Leaflet → MIT·의존성 0의 단일 파일·OSM 무료 타일·10년+ 안정 API. 제거 비용 = map.js만 영향, 다른 페이지 무관(격리됨). → Leaflet 채택 확정. 타 페이지로 전파 금지(연표는 Leaflet 불요 — §3.2).

**추가 라이브러리 도입 절차:** 그래프 라이브러리(d3 등) 포함 어떤 추가 의존도 web-architect에게 사유서(해결 문제·vanilla 불가 이유·대안 비교·제거 비용) 제출 후 합의. people.html 관계망 그래프는 **vanilla SVG/Canvas로 구현**한다(§3.3·§7 D-09) — 라이브러리 불요.

---

## 2. 디렉토리 구조 (확정 — 10페이지)

sitemap.md §1의 10페이지 구성을 반영(site-architecture 표준 9 + `organizations.html`).

```
site/
├── index.html              홈 — 도입 서사·탐색 허브·검증 통계
├── life.html               생애 — 15장(8부) + 공백과 한계
├── timeline.html           연표 — 인터랙티브 (165건 렌더)
├── map.html                활동 지도 — Leaflet (좌표 보유 113건)
├── organizations.html      조직 — 결사 10절 (org 앵커)
├── philosophy.html         사상 — 9절 + 어록 검증표
├── people.html             인물 — 관계망 그래프 + 서사 + 미확정 목록
├── archives.html           사료 — 카탈로그 + 사료 비판 + 미확인 + 채택 안 한 전승
├── gallery.html            갤러리 — 이미지 매니페스트 뷰
├── references.html         참고문헌 — 인용 일람 + 검증 방법론
├── css/
│   ├── tokens.css          디자인 토큰 (ui-designer 소유)
│   └── main.css            공통 스타일·컴포넌트 (frontend-developer 소유)
├── js/
│   ├── loader.js           공통 데이터 로더 (frontend-developer 소유 — 공유 모듈)
│   ├── layout.js           공통 헤더·내비·푸터 (frontend-developer 소유 — 공유 모듈)
│   ├── footnotes.js        [ref:ref-NNN] 각주 렌더 (frontend-developer 소유 — 공유 모듈)
│   ├── page-render.js      일반 페이지 본문 렌더 (frontend-developer 소유)
│   ├── timeline.js         연표 (timeline-developer 소유)
│   └── map.js              지도 (map-developer 소유)
├── data/
│   ├── timeline.json       165건(D 제외) + actor_refs/org_refs 파생
│   ├── network.json        nodes 81·edges 135·edges_unconfirmed 19·정규화표
│   ├── citations.json      refs 155·sources 194 (2층)
│   ├── archives.json       1차 사료 카탈로그 47건 (src-pri 앵커)
│   ├── images.json         이미지 매니페스트 80건 (gallery.json 아님 — D-22)
│   ├── meta.json           사이트 자기 집계 수치 단일 출처 (home 통계·qa 정합 — D-21)
│   └── pages/              본문 데이터
│       ├── home.json
│       ├── life.json
│       ├── timeline.json   ※ 페이지 도입문 (연표 데이터 data/timeline.json과 별개)
│       ├── map.json        ※ 페이지 도입문
│       ├── organizations.json
│       ├── philosophy.json
│       ├── people.json
│       ├── archives.json
│       ├── gallery.json    ※ 도입문
│       └── references.json ※ 방법론 절
└── assets/
    └── images/             WebP 81개 (이미 존재) + originals/ 80개 (이미 존재)
```

> **이름 충돌 주의(함정 §5.6):** `data/timeline.json`(연표 데이터)과 `data/pages/timeline.json`(연표 페이지 도입문)은 **다른 파일**이다. 경로 접두(`pages/`)로 구분. map도 동일. 로더 호출 시 전체 경로를 명시하라.

- `site/assets/images/`(WebP 81 + originals/ 80)는 **이미 존재**한다 — 재생성 금지. images.json의 `file`/`original_file`이 이 디렉토리의 파일명과 일치한다.
- 새 최상위 디렉토리·새 `js/`·`css/` 파일 추가는 web-architect 합의 사항.

---

## 3. 인터페이스 계약 (게이트 핵심)

> 형식: **스키마 전체 + 소비자가 실제로 읽는 필드 + null/누락 정책 + 변경 절차.** 소비 필드 목록은 qa-engineer의 경계면 교차 비교 대조 기준이다(site-architecture §5).
> **불변 원칙(승계, sitemap §4):** 모든 데이터 id(`evt-` `per-` `org-` `src-pri-` `ref-` `src-{aca|enc|ins|pri|web}-`)는 site/data로 옮길 때 **변형 없이** 보존한다. 앵커 = id이므로 변형 시 교차링크 전멸. (결정 D-01)

### 3.0 공통 로더 계약 — `js/loader.js` (공유 모듈)

```js
// 시그니처 (변경 시 전 소비자 사전 고지 — 시그니처는 계약)
export async function loadData(path) -> Promise<object|array>
  // 성공: 파싱된 JSON 반환
  // 실패(네트워크·HTTP!=200·JSON 파싱 오류): renderLoadError(path, err) 호출 후 throw
export function renderLoadError(path, err) -> void
  // 사용자에게 보이는 에러 UI를 #app(또는 [data-load-error] 타깃)에 렌더
  // 빈 화면 금지 — "데이터를 불러오지 못했습니다: {path}" + 로컬서버 안내(§5.1) 노출
```

- 모든 데이터 로드는 이 함수를 경유한다. 직접 `fetch` 금지(에러 UI 일관성·QA 추적성).
- 경로는 페이지 기준 **상대 경로**(`data/timeline.json`, `data/pages/life.json`) — 절대 경로(`/data/...`) 금지(서브디렉토리 호스팅 호환).
- **null 정책:** 로더는 빈 객체를 반환하지 않는다 — 실패는 throw로 전파. 소비자는 호출부에서 try/catch 또는 await 실패를 처리.
- 변경 절차: frontend-developer가 시그니처 변경 시 web-architect 합의 후 timeline·map 개발자에게 사전 고지.

### 3.1 계약: `data/timeline.json` ↔ `js/timeline.js`, `js/map.js`

**스키마** (원본 timeline.json 승계 + 빌드 파생 필드):
```jsonc
{
  "meta": { "event_count": 165, "excluded_d_count": 7, "disputed_count": 17,
            "coord_count": 113, "generated": "...", "status": "..." },
  "events": [{
    "id": "evt-shin-005",                  // 무변형 — timeline.html#{id} 앵커
    "title": "신민회 결성",
    "date": { "start": "1907-04-01", "end": "1907-04-30",
              "precision": "year|month|day|range", "calendar": "solar|lunar" },
    "place": { "name": "서울", "modern_name": "...", "lat": 37.5, "lng": 126.9 },  // lat/lng null 가능
    "actors": ["안창호", "양기탁"],          // 표시명 문자열 (원본)
    "orgs": ["신민회"],                      // 표시명 문자열 (원본)
    "actor_refs": [{ "name": "안창호", "node_id": "per-001" },   // ★빌드 파생 (D3 — 확정)
                   { "name": "양기탁", "node_id": "per-017" }],   // 미해소: node_id:null
    // 동명이호(ambiguous_aliases): { "name":"우강", "node_id":null, "ambiguous":true } — 런타임 단정 차단
    "org_refs": [{ "name": "신민회", "node_id": "org-006" }],     // ★빌드 파생 (D3 — 확정)
    "summary": "...", "detail": "...",
    "sources": [{ "type":"...", "title":"...", "locator":null, "url":"..." }],  // 원본 출처(연표 카드 출처 표시용)
    "confidence": "A|B|C",                   // D 없음 (본체서 제외)
    "tags": ["조직"],                        // 7종 그대로(병합·개명 금지): 결사·이동·사상·가족·교육·언론·연설
    "disputed": false,
    "dispute_note": null,                    // disputed=true면 문자열
    "dispute": null,                         // ★disputed=true면 객체(아래) — D-16 확정
    // "dispute": { "status":"unresolved (cfl-001)",
    //   "adopted": { "start":"...","end":"...","precision":"range","basis":"..." },
    //   "variants": [{ "claim":"...","source":"...","assessment":"동률|..." }] }
    "period": "P3",                          // ★빌드 파생 — periodOf(date.start) (D-12)
    "has_geo": true                          // ★빌드 파생 — place.lat && place.lng 둘 다 non-null (D-17)
  }]
}
```

**timeline.js 소비 필드:** `id`, `title`, `date.start`, `date.end`, `date.precision`, `date.calendar`, `place.name`, `place.lat`, `place.lng`, `summary`, `sources`, `confidence`, `disputed`, `dispute_note`, `dispute`, `tags`, `period`, `has_geo`, `actor_refs[]`, `org_refs[]`. (`period`는 빌드 파생이므로 timeline은 재계산 불요 — §3.7 단일 함수로 빌드 시 산출됨.)

**map.js 소비 필드:** `id`, `title`, `date.start`, `place.name`, `place.lat`, `place.lng`, `summary`, `period`, `has_geo`. **`has_geo`=true 이벤트(D 제외 후 113건)만** 마커 렌더. 마커 팝업 → `timeline.html#{id}` 링크. (집계는 build 산출 meta.coord_count가 최종 진실 — qa는 메타 대조.)

**딥링크 계약 (03_timeline.md L18에서 이관 — D-18 확정):**
- `timeline.html#{evt-id}` → 해당 사건 카드로 스크롤·하이라이트(앵커 = id 무변형).
- `timeline.html?period=P{1..8}` → 로드 시 해당 시기 필터 상태로 진입. 다른 페이지의 "이 시기의 연표 보기" 링크가 이 형식을 만든다. timeline.js는 `location.search`의 `period` 파라미터를 파싱해 초기 필터 적용. 잘못된 값(P9 등)은 무시(전체 표시).
- 필터 3종: ① 시기 P1–P8(`period` 필드 버킷) ② 주제 태그 7종(`tags` 그대로) ③ disputed 토글(`disputed`).

**null/누락 정책:**
- `place.lat`/`lng` = null(`has_geo`=false) → map은 마커 생략(데이터 누락 아님, 좌표 미상). timeline은 "지도에서 보기" 링크 생략.
- `actor_refs[].node_id` = null → 소비자는 **평문 렌더**(앵커 없음). non-null → `people.html#{node_id}` 또는 `organizations.html#{node_id}` 링크. ★이게 핵심: **렌더 165건 기준 distinct actor 134개 중 53개·org 68개 중 25개만** 노드 매핑됨(§5.3·§7 D-03). 추측 매핑 금지 — node_id가 진실. ambiguous(예 '우강')는 node_id:null + ambiguous:true 플래그(런타임 단정 차단).
- `disputed`=true → 카드/팝업에 **`dispute_note`(한 줄 요약) + `dispute` 객체(adopted 채택안·variants 이설 목록) 동반 노출 의무**(00_common §6 disputed 표시 — conflicts.md (a)통설+각주/(b)양론병기 문형의 데이터 원천이 `dispute`다). disputed=true인데 `dispute`/`dispute_note`가 null이면 데이터 결함 → qa 리포트.
- `dispute.adopted.precision`=range → date 표시는 범위로(통설 단일값 단정 금지, 00_common §2 정밀도 초과 금지).
- `confidence`="C" → 카드에 한정 표시(요약 문형이 이미 한정형, 추가 단정 윤문 금지). D는 본체에 없어야 함(있으면 결함).

**변경 절차:** data-engineer가 web-architect 합의 후 스키마 변경 → timeline·map·qa 개발자 전원 고지 → qa 재검증.

### 3.2 계약: 연표·지도 페이지 도입문 ↔ 본문

- `data/pages/timeline.json`(연표 페이지 도입·안내문, drafts/03_timeline.md 출처)과 `data/pages/map.json`(지도 도입·경로 해설, drafts/04_map.md)은 §3.6 공통 페이지 스키마를 따른다.
- timeline.js/map.js는 데이터(data/timeline.json)와 도입문(data/pages/*.json) **둘 다** 로드: 도입문은 page-render 패턴으로 헤더 영역에, 데이터는 자기 렌더 로직으로.
- map.js Leaflet 사용: OSM 타일, 시기 슬라이더(P1–P8, §3.7), 경로 폴리라인(drafts/04_map.md 정의분만). 비-JS·Leaflet 로드 실패 폴백 = 좌표 보유 사건의 텍스트 목록(interactive-viz 스킬 폴백 규칙).

### 3.3 계약: `data/network.json` ↔ `js/page-render.js`(people·organizations)

**스키마** (원본 network.json 승계):
```jsonc
{
  "meta": { "version": "v1.2.1-phase2", "counts": { "nodes":81,"edges":135,"edges_unconfirmed":19 },
    "place_normalization": [   // ★network.meta에 실재(4건, cfl-036~039) — D-20 정정으로 계약 포함
      { "standard":"암화리", "variants":["화암리"], "status":"잠정 채택(cfl-038)", "note":"..." },
      { "standard":null, "variants":["심정리(민백)","노남리(인명사전)"], "status":"미해소(cfl-037)", "note":"..." }
    ] },
  "name_normalization": { "Ahn Chang-ho": "per-001", ... },   // 293 별칭→node_id
  "ambiguous_aliases": { "우강": { "node_ids":["per-017","per-034"], "note":"..." } },
  "nodes": [{
    "id": "per-001|org-001",         // 무변형 — people.html#{per-id} / organizations.html#{org-id} 앵커
    "kind": "person|org",            // ★빌드 파생 — id 접두(per-/org-)로 산출 (D-19). 페이지 분기용
    "name": "안창호", "hanja": "安昌浩",
    "alt_names": ["도산","島山",...],
    "birth": "1878-11-09", "death": "1938-03-10",   // 문자열, precision 다양(연/연-월/연-월-일)
    "role": "...", "summary": "..."
  }],                                 // per 59 + org 22 = 81
  "edges": [{
    "source": "per-001", "target": "per-002",
    "type": "family|comrade|conflict|mentor|membership|patron",  // 6분류 (데이터 실측: mentor 3건 — teacher_student 아님)
    "period": { "from": "1878", "to": null },         // to null 가능
    "evidence_event_ids": ["evt-early-001", ...],     // timeline.html#{evt} 링크 (근거 사건)
    "description": "...", "period_note": "...",        // period_note 없을 수 있음
    "org_relation": "predecessor|subsidiary|affiliate|organ"  // 조직-조직 보조 필드, 없을 수 있음
  }],
  "edges_unconfirmed": [{ ... "grade":"D", "unconfirmed_reason":"...", "evidence_pending":[...] }]  // 19건
}
```

**people.html(`kind`=person 노드 + per 관련 edge) / organizations.html(`kind`=org 노드 + org 관련 edge) 소비:**
- 노드: `id`(앵커), `kind`(페이지 분기), `name`, `hanja`, `alt_names`, `birth`, `death`, `role`, `summary`.
- 엣지(관계망 그래프·서사): `source`, `target`, `type`, `period`, `evidence_event_ids`, `description`, `org_relation`.
- `evidence_event_ids[]` → 각각 `timeline.html#{evt-id}` 링크(관계의 근거 사건, 07_people.md 의무 ≥1).
- 인명 정규화: 본문/검색에서 별칭 표시 시 `name_normalization`으로 canonical 노드 해소. `ambiguous_aliases`는 동명이호 경고 표시.
- **`place_normalization`(network.meta, 4건)은 계약에 포함**(D-20 정정 — 2026-06-06): 지명 상충(cfl-036~039)의 `{standard, variants[], status, note}`. map 마커·본문 지명 표기 시 `standard`(있으면) 채택하되, `status`가 "미해소"이거나 variants가 실질 상충이면 **variants 병기**(00_common §6 disputed 표기와 동형). data-engineer가 site/data/network.json에 동봉(동봉 확정). ※ 최초 D-20은 web-architect가 network **top-level**만 검색해 "부재"로 오판한 것 — data-engineer 회신으로 `network.meta.place_normalization` 실재 확인·정정. timeline.json엔 없음(network.meta에만).

**null/누락 정책:**
- `period.to`=null → "현재까지/미상"이 아니라 **종결 미기재**(period_note 참조). UI는 "from~" 형태로 표시, "~현재" 금지.
- `period_note` 없음 → 추가 주석 없이 period만 표시.
- `org_relation` 없음 → 일반 type만 표시.
- **edges_unconfirmed(19, D등급) 그래프 본체 렌더 절대 금지**(00_common §6.1 D 차단). people.html "미확정 관계" **별도 목록 섹션**에서만 노출(per-id 기준 필터, `unconfirmed_reason` 동반). 그래프 노드·엣지에 섞지 마라. (결정 D-04)
- org 노드는 **lat/lng 없음** — organizations는 지도 연결 안 함(timeline 경유만).

**변경 절차:** §3.1과 동일(data-engineer 주도, web-architect 합의, people·org·qa 고지).

### 3.4 계약: `data/citations.json` ↔ `js/footnotes.js` (각주 렌더 — 전 페이지 공유)

**스키마** (2층 — 00_common §3 승계):
```jsonc
{
  "refs": [{ "id": "ref-001", "source_id": "src-ins-001", "page_or_locator": null }],  // 155건
  "sources": [{ "id": "src-aca-001", "type":"academic|encyclopedia|institutional|primary|web",
                "author":"이광수", "title":"도산 안창호",
                "publisher":"...", "year":1947, "url":"...", "accessed":"2026-06-06" }]    // 194건
}
```

**각주 렌더 계약 (footnotes.js — ★전 페이지 공통, 게이트 핵심):**
- 본문 텍스트의 마커 형식은 **`[ref:ref-NNN]`** 으로 확정. drafts 실측 = 1,211개 마커 전부 이미 `ref-NNN` 정규화 완료(00_common §3 수명주기 2단계 완료). Phase 4 렌더러 입력 = `ref-NNN`. 잠정 마커(clm-/evt-/src-pri-/cfl-)는 본문에 없어야 함(있으면 정규화 누락 결함 → qa 리포트). (결정 D-05)
- **렌더 경로:** 본문 `[ref:ref-NNN]` → `refs[]`에서 `id==ref-NNN` 조회 → `source_id` 획득 → `sources[]`에서 해당 id 조회 → 각주 번호 + `references.html#{source_id}` 앵커 링크 생성.
- **렌더 규약:**
  1. 페이지 본문 렌더 후 footnotes.js가 텍스트 노드의 `[ref:ref-NNN]`을 스캔.
  2. 각 마커를 위첨자 각주 번호(`<sup><a href="references.html#{source_id}">N</a></sup>`)로 치환. 페이지 내 등장 순서로 번호 부여.
  3. 같은 ref-NNN이 한 페이지에 여러 번 → 같은 번호 재사용(번호 중복 부여 금지).
  4. 페이지 하단에 각주 목록 섹션 생성(번호 → sources 서지 약식 + references.html 앵커 링크).
- **null/누락 정책:**
  - `ref-NNN`이 refs[]에 없음 → **끊어진 각주**. 빈 화면 금지 — 마커를 `[ref:ref-NNN ⚠]`로 가시화하고 console.warn, qa-engineer가 검출(00_common §8-3). 조용히 삼키지 마라.
  - `source_id`가 sources[]에 없음 → 동일 처리(끊어진 출처).
  - `page_or_locator`=null → 각주에 페이지/위치 표기 생략.
- **메타 예외(승계, 00_common §3):** 편집 메타 서술 구역(`*-intro`·`*-gaps` 앵커, `methodology`·`grades`·`citations`·`colophon`, 각 페이지 도입문, 데이터 집계 자기 서술)은 마커 없어도 정상 — footnotes.js는 마커가 **있을 때만** 렌더하므로 추가 처리 불요. qa의 "사실 문장 마커 100%" 검사가 이 예외를 적용(렌더러는 무관).
- **변경 절차:** 각주 마커 형식은 citation-manager·content-qa와 공유 규칙. 형식 변경 시 web-architect+citation-manager 합의, frontend(footnotes.js 소유)·전 페이지·qa 고지.

### 3.5 계약: `data/images.json` ↔ gallery·전 페이지 이미지 슬롯

**스키마** (manifest.json 승계, image_root만 정규화):
```jsonc
{
  "version":"...", "image_root":"assets/images/", "originals_root":"assets/images/originals/",
  "stats": { "total":80, "by_period":{...}, "by_license":{...} },
  "unfilled_slots": [{ "slot":"img-phil-02", "page":"philosophy", "status":"...", "reason":"..." }],
  "images": [{
    "id":"dosan-portrait-1919",       // 무변형 — gallery.html#{id} 앵커
    "file":"1919_dosan_portrait_shanghai.webp",   // assets/images/{file}
    "original_file":"...jpg",          // assets/images/originals/{original_file}
    "title":"...", "date":"1919", "date_precision":"circa|exact|year",
    "depicted":["안창호"], "place":"상하이", "period":"P5",   // period = P1–P8
    "type":"portrait|document|newspaper|place|group", 
    "source_org":"...", "source_url":"...", "license":"...", "license_evidence":"...",
    "caption":"...",                   // 표시 캡션 (사실 캡션 — content-qa 대조 대상)
    "credit":"출처: ...",
    "slots":["img-home-01"],           // 이 이미지가 채우는 슬롯 id
    "used_pages":["gallery","home","life"],   // 사용 페이지 (역링크 원천)
    "notes":"..."
  }]
}
```

**소비:**
- **gallery.html**: `images[]` 전체 렌더. 카드 = 이미지(`image_root`+`file`) + `title` + `caption` + `credit` + `license` + `period` 배지 + `used_pages` 역링크(09_gallery.md 의무). 앵커 `gallery.html#{id}`.
- **각 페이지(home·life·organizations·philosophy·people·archives)**: `slots[]` 또는 `used_pages[]`로 필터해 자기 페이지 슬롯 이미지 소비. 슬롯 id(`img-{page}-NN`)는 page_specs 슬롯 표 기준.
- **이미지 경로:** `image_root`(`assets/images/`) + `file`. 페이지 기준 상대 경로(절대 경로 금지). 원본은 `originals_root` + `original_file`.
- **null/누락 정책:**
  - `unfilled_slots`의 슬롯(img-phil-02 등) → 해당 페이지는 그 슬롯을 **빈 채로 두되 레이아웃 깨짐 없이 생략**. 필수 슬롯 미충족은 명세 개정 합의 기록 존재(00_common §8-8). 권장 슬롯 미충족은 허용.
  - 캡션 4요소(사실 캡션·연대·출처·라이선스)는 manifest에 있음 — 표시 의무. 캡션 사실 주장도 content-qa 대조 대상.
- **변경 절차:** images.json 스키마 변경은 data-engineer 주도(visual-curator 매니페스트가 상류). gallery·해당 페이지·qa 고지.

### 3.5b 계약: `data/archives.json` ↔ archives.html (사료 카탈로그)

> 자기 검토(§9)에서 발견한 누락분 추가. archives.html은 본문(pages/archives.json) **외에** 사료 카탈로그 데이터를 별도 렌더한다. 출처는 `_workspace/01_research/primary-source_catalog.json`(47건, **루트가 배열**). data-engineer가 `site/data/archives.json`으로 변환.

**스키마** (catalog 승계):
```jsonc
{
  "meta": { "count": 47, "by_status": { "confirmed":22,"cited_only":14,"unlocated":11 } },
  "catalog": [{
    "id": "src-pri-001",              // 무변형 — archives.html#{src-pri-NNN} 앵커 (sitemap §4)
    "title": "도산 안창호 일기 (1920–1921, ...)",
    "type": "diary|letter|speech|newspaper|interrogation|verdict|org_record|etc",
    "author": "...", "date_created": "...", "language": "ko-hanja",
    "holder": "독립기념관 ...", "access_url": "...",
    "location_status": "confirmed|cited_only|unlocated",   // 배지
    "transcription": null, "modern_translation": null,     // null 가능
    "criticism": { "external": "...", "internal": "..." },  // 사료 비판 (외적·내적)
    "related_event_ids": ["evt-..."],   // 45/47 보유 — timeline.html#{evt} 링크
    "notes": "..."
  }]
}
```
**archives.html 소비 필드:** `id`(앵커), `title`, `type`(유형별 그룹), `author`, `date_created`, `language`, `holder`, `access_url`, `location_status`(배지), `criticism.external`/`internal`, `related_event_ids`(→timeline 링크), `notes`, `transcription`/`modern_translation`(있으면 표시).

**★ related_event_ids 해소 의무 (D-24 — 교차평면 끊어진 앵커 차단, 최우선):**
- 실측 경고: 카탈로그 원본의 `related_event_ids`는 **병합 전(pre-merge) id를 다수 포함**한다 — 47건 중 57개 참조가 site/data/timeline.json(렌더 165)에 그대로는 없다. 그중 **55개는 timeline의 `merged_from` 맵으로 생존 id에 해소되고**, **2개(src-pri-003→evt-amer-034, src-pri-036→evt-hsd-024)는 D등급 제외분으로 해소**된다. 무해소 죽은 id는 0.
- **빌드 의무:** data-engineer가 timeline의 `merged_from`(병합 전 id → 생존 id) 맵으로 archives `related_event_ids`를 **생존 id로 치환**하고, 치환 후 (a) 렌더 165에 있으면 링크 유지, (b) D 제외분으로 해소되면 **링크 제거**(평문). 즉 site/data/archives.json의 `related_event_ids`는 **이미 해소·필터된 렌더 가능한 id만** 담는다(소비자는 추가 해소 불요).
- network 엣지의 `evidence_event_ids`는 실측 클린(D·죽은 id 참조 0 — relation-analyst가 이미 생존 id로 해소). archives만 이 처리가 필요하다.
- 검증: qa는 archives·network·people의 모든 evt 참조가 렌더 165 집합의 부분집합인지 전수 대조(끊어진 교차평면 앵커 0).

**null/누락 정책:** `transcription`/`modern_translation`=null → 해당 표시 생략. `related_event_ids` 없음(2건) 또는 해소 후 비면 → "근거 사건 링크 없음", 끊어진 링크 아님. `title`·`holder`·`access_url`은 **원문 그대로**(08_archives.md 재작성 금지). 신문조서 진술 직인용 0건(08 spec 제약 — 데이터엔 무관, 본문 제약).
**변경 절차:** §3.1과 동일(data-engineer 주도, archives·qa 고지).

### 3.6 계약: `data/pages/*.json` ↔ `js/page-render.js` (일반 페이지 본문)

> drafts/*.md(10종)를 data-engineer가 구조화 JSON으로 변환. **본문 표현 = `blocks`(타입별 객체배열) 확정**(D6 — data-engineer 실측 후 blocks 채택, html 평문은 기각: 드래프트 헤딩에 명시 앵커 71개·표·슬롯 구조가 있어 평문화 시 바인딩 불가). 3불변 준수: (a) text 내 `[ref:ref-NNN]` 마커 **원형 보존**(변환이 건드리지 않음), (b) md 교차링크 `[텍스트](page.html#anchor)` 원형 보존, (c) 섹션 `id`=앵커 무변형. 파일 단위 = `pages/{page_id}.json` 1파일.

**스키마 (blocks 확정 — data-engineer 실측 블록 유형):**
```jsonc
{
  "page_id": "life",
  "title": "생애",
  "lead": "페이지 헤더 한 줄 소개 (page_specs 정의)",
  "sections": [{
    "id": "ch-06",                     // 무변형 — life.html#{id} 앵커 (드래프트 {#ch-06} 그대로). 앵커 없는 헤딩만 slug 파생
    "heading": "제6장 ...",
    "level": 2,                        // h2/h3 ...
    "blocks": [                        // 6유형(코드펜스·인라인이미지 없음 — 실측)
      { "type":"paragraph", "text":"...본문...[ref:ref-002]...[표시](timeline.html#evt-shin-005)..." },
      { "type":"blockquote", "lines":["...","..."] },           // 인용(각주 동반)
      { "type":"table", "headers":["...","..."], "rows":[["",""]] },  // philosophy 어록표·archives·people
      { "type":"list", "ordered":false, "items":["...","..."] },
      { "type":"slot", "slot_id":"img-life-06" }                // <!-- slot: img-... --> → images.json 매핑
    ]
  }]
}
```

**page-render.js 소비 필드:** `page_id`, `title`, `lead`, `sections[].id`(앵커), `sections[].heading`, `sections[].level`, `sections[].blocks[]`(유형별: paragraph.text / blockquote.lines / table.headers·rows / list.ordered·items / slot.slot_id). `paragraph.text`·`blockquote.lines`·`table` 셀 내 `[ref:ref-NNN]`은 page-render 렌더 후 footnotes.js가 각주 치환. md 교차링크 `[텍스트](page.html#anchor)`는 `<a>`로 변환. `slot.slot_id`는 images.json `slots[]`로 이미지 조회.

**null/누락 정책:**
- 섹션 `id`는 sitemap §4 앵커 체계 준수(`ch-NN`·`sec-N`·`*-intro`·`*-gaps` 등). 예약 앵커명(메타 예외) 재사용 금지(00_common §3).
- 본문에 잠정 마커(clm-/evt-/cfl-)가 남아 있으면 정규화 누락 결함 → qa 리포트(footnotes.js는 ref-NNN만 처리).

**변경 절차:** 페이지 JSON 공통 스키마 변경은 web-architect+data-engineer 합의, frontend(page-render 소유)·qa 고지.

### 3.7 시기(P1–P8) 산출 규칙 (전 페이지 공통 — 계산 계약)

sitemap §3·00_common §5의 8대 시기는 **데이터에 명시 필드가 없는 경우 date.start로 계산**한다(timeline 이벤트엔 시기 필드 없음; images엔 `period` 필드 있음 = 그대로 사용).

| 코드 | 시기 | 경계(start 기준) |
|------|------|------------------|
| P1 | 성장과 수학 | 1878 ≤ y ≤ 1899 |
| P2 | 결혼과 1차 미주 | 1899 < y ≤ 1907 |
| P3 | 신민회와 망명 | 1907 < y ≤ 1911 |
| P4 | 2차 미주·국민회·흥사단 | 1911 < y ≤ 1919 |
| P5 | 임시정부와 모색 | 1919 < y ≤ 1924 |
| P6 | 재방문과 대독립당 | 1924 < y ≤ 1932 |
| P7 | 수감과 순국 | 1932 < y ≤ 1938 |
| P8 | 사후 | y > 1938 |

- **시기 산출의 단일 권위 = data-engineer의 빌드 시 `periodOf(date.start)`** (D-12·D-17). 그 결과를 timeline.json 각 이벤트의 `period` 필드에 박는다(§3.1). timeline 필터·map 슬라이더는 **이 `period` 필드를 읽기만** 하고 재계산하지 않는다 — 경계 부등호(1899·1907·1911·1919·1924·1932)가 한 곳(빌드 스크립트)에만 존재해야 정합이 깨지지 않는다.
- 런타임에서 시기 계산이 필요한 곳(있다면)은 동일 경계의 공통 유틸 `periodOf`를 쓰되, 진실은 빌드 산출 `period`. 두 결과가 다르면 빌드 스크립트가 진실(qa 대조).
- images.json은 `period` 필드를 그대로 신뢰(visual-curator 분류). gallery 시기 분류·페이지 필터는 이 필드 사용.

### 3.8 계약: `data/meta.json` ↔ home 통계 박스 + qa 데이터 정합 검사 (D-21 — 신설 승인)

> data-engineer 제안 채택. 01_home.md L10이 "검증 통계 수치는 **데이터 파일 메타에서만** 가져온다(집계 재계산 금지)"를 요구하고, 00_common §3(iii)가 데이터 집계 자기 서술은 [ref:] 정박 대상이 아니라 사이트 JSON이 근거라고 규정한다. → 이 수치들의 **단일 출처**로 `data/meta.json`을 신설한다(사이트 자신의 집계를 한 파일에 모아 home과 qa가 같은 출처를 본다).

**스키마:**
```jsonc
{
  "counts": { "events_total":172, "events_rendered":165, "events_excluded_d":7,
              "events_disputed":17, "events_with_geo":113,
              "persons":59, "orgs":22, "edges":135, "edges_unconfirmed":19,
              "claims":305, "sources":194, "primary_sources":47, "images":80 },
  "claim_grades": { "A":9, "B":155, "C":89, "D":52 },     // claims_register 집계(실측 확인)
  "timeline_confidence": { "A":8, "B":106, "C":51 },       // 렌더분(D 제외) 집계(실측 확인)
  "timeline_tags": { "결사":112, "이동":37, "사상":33, "가족":28, "교육":22, "언론":17, "연설":1 },  // ★렌더분(D 제외) 실측
  "images_by_period": { "P1":8, ... }, "generated": "..."
}
```
> **★중요(D-21 단서):** 모든 수치는 **빌드 시 site/data 실제 레코드에서 집계**한다 — 명세·드래프트에 적힌 수치를 베껴 넣지 마라. 예: 03_timeline.md 등 일부 명세의 태그 수치(결사114·이동38·사상35·가족31)는 **D 포함 또는 동결 전 집계**라 렌더분(D 제외) 실측(결사112·이동37·사상33·가족28)과 다르다. meta.json은 **렌더되는 데이터의 실측치**가 진실이다(00_common §3(iii) "사이트 자신의 JSON이 근거"). home 통계·qa 정합 검사는 이 실측 meta를 본다.

**home 소비:** 통계 박스 수치를 meta.json에서만 바인딩(하드코딩·재집계 금지). **qa 소비:** 데이터 정합 검사 = meta.json 수치 ↔ 각 데이터 파일 실제 레코드 수 전수 대조(00_common §8-3). 불일치 = 결함.
**null/누락 정책:** 모든 수치는 빌드 시 데이터 파일에서 집계. 수기 입력 금지(산출 스크립트가 진실). **변경 절차:** §3.1과 동일.

### 3.9 파일명·신규 산출 확정

- **이미지 데이터 파일명 = `data/images.json` 확정**(team-lead 지시문의 `gallery.json` 아님). 근거: sitemap §4 앵커표·09_gallery.md·00_common §1·site-architecture §2가 모두 `images.json`. (결정 D-22 — CSS 경로 D-14와 동일한 충돌 해소 원리: 계약 다수·스킬 일치 우선.)
- **`data/search-index.json` = 선택·보류(미승인)**. data-engineer 제안이나 명세가 전역 검색을 명시 요구하지 않는다(J2의 "연표 검색/필터"는 timeline 내부 필터=§3.1 딥링크·태그·시기로 충족). 전역 검색 UI가 실제 필요해지면 frontend-developer가 web-architect에 요청 → 승인 시 계약 추가(site-architecture §2 신규 파일 절차). 지금은 산출 강제·금지 아님(만들어도 소비처 미정이면 미사용). (결정 D-23)

---

## 4. 파일 소유권 규칙 (충돌 0 보장)

동시 수정 충돌은 사후 머지가 아니라 **사전 소유권**으로 막는다(site-architecture §6). 모든 `site/` 파일에 단일 소유자.

| 파일/디렉토리 | 소유자 | 비고 |
|---------------|--------|------|
| `index.html`, `life.html`, `organizations.html`, `philosophy.html`, `people.html`, `archives.html`, `gallery.html`, `references.html` | **frontend-developer** | 일반 8페이지 |
| `timeline.html`, `js/timeline.js` | **timeline-developer** | |
| `map.html`, `js/map.js` | **map-developer** | |
| `css/tokens.css` | **ui-designer** | 디자인 토큰 단독 소유 |
| `css/main.css` | **frontend-developer** | tokens.css 변수 소비, 공통 컴포넌트 클래스 |
| `js/loader.js` | **frontend-developer** | ★공유 모듈 — 시그니처 변경 전 고지 |
| `js/layout.js` | **frontend-developer** | ★공유 모듈 — 헤더·내비·푸터 |
| `js/footnotes.js` | **frontend-developer** | ★공유 모듈 — 각주 렌더(전 페이지 사용) |
| `js/page-render.js` | **frontend-developer** | 일반 페이지 본문 렌더 |
| `data/*.json`, `data/pages/*.json` | **data-engineer** | 전 데이터 파일 |
| `assets/images/**` | (visual-curator 산출, 이미 존재) | 재생성·이동 금지 |

**규칙:**
1. 소유 아닌 파일 수정 필요 시 → 소유자에게 SendMessage 요청. **직접 수정 금지.**
2. **예외(a11y-engineer):** 접근성 위반 수정에 한해 모든 파일 수정 가능. 단, 수정 내역을 소유자에게 **사후 고지 의무**(어느 파일·무엇·왜).
3. **공유 모듈(loader.js·layout.js·footnotes.js·page-render.js) 시그니처 변경:** 시그니처는 계약(§3.0·§3.4·§3.6). 변경 시 **전 소비자(timeline·map·전 페이지·qa)에게 사전 고지** + web-architect 확인. timeline/map은 이 4개 공유 모듈을 **import만** 하고 수정하지 않는다.
4. **공유 데이터(data/*.json):** data-engineer 단독 쓰기. 소비자(frontend·timeline·map)는 읽기만. 스키마 변경은 §3 각 계약의 변경 절차.
5. **css/tokens.css:** ui-designer 단독. 다른 개발자는 변수 참조만(하드코딩 색/폰트 금지). 새 토큰 필요 시 ui-designer에 요청.
6. **HTML 골격 ↔ JS 렌더 경계:** 각 페이지 HTML(정적 골격: head·헤더 마운트포인트·`<main id="...">`·푸터 마운트포인트·script 태그)은 페이지 소유자가 작성. 본문 콘텐츠는 JS가 data/에서 렌더. 헤더·푸터는 layout.js가 모든 페이지에 공통 주입(복붙 금지 — sitemap §2).
7. **CSS 경로 = `site/css/` 확정**(`site/assets/css/` 아님 — assets/는 이미지 전용). site-architecture §2·dosan-design-system 스킬·기존 커밋(`site/css/tokens.css`) 3중 일치. (결정 D-14)
8. **CSS 클래스 네이밍 규약**(ui-designer 합의, design-system.md가 세부 소유): 공통 컴포넌트는 무접두 케밥(`.card`·`.badge`·`.grade-badge`), **모듈 전용 클래스는 접두 의무** — 연표 `tl-`(`.tl-event-card`), 지도 `map-`(`.map-marker-popup`), **people 관계망 그래프 `nw-`**(`.nw-node`·`.nw-edge`·`.nw-graph`). 상태 클래스 `is-`/`has-`(`.is-active`·`.is-disputed`), JS 훅은 `data-*` 속성. 이유: timeline.js·map.js·페이지 그래프가 같은 main.css 네임스페이스를 공유 → 접두가 CSS 평면의 소유권 충돌을 사전 차단. ※ `nw-` 그래프 클래스는 people.html 소유자(frontend-developer)가 main.css에 작성(그래프는 vanilla SVG, D-09).

**충돌 0 검증:** 위 표가 site/ 전체를 커버한다(html 10 + css 2 + js 6 + data + assets). 동일 파일 2인 소유 0건. 공유 모듈은 단일 소유(frontend) + 시그니처 고지 프로토콜로 동시 수정 차단. CSS는 단일 main.css 네임스페이스를 모듈 접두 규약(규칙 8)으로 분할.

---

## 5. 예측 가능한 함정과 회피책 (주도성 — 구현 전 필독)

### 5.1 file:// CORS 함정 (최우선)
브라우저는 `file://`로 연 페이지의 `fetch`를 CORS로 차단 → **데이터 전부 로드 실패**. 이건 코드 버그가 아니다. HTML 더블클릭 금지.
- **회피:** `cd site && python3 -m http.server 8000` → `http://localhost:8000`. QA·스크린샷·동작 확인 전부 이 전제.
- **로더 에러 UI(renderLoadError)에 이 안내를 포함**: "데이터 로드 실패. 로컬 서버로 여세요: `python3 -m http.server`". file://에서 빈 화면 보고 코드 수정하지 마라.

### 5.2 데이터 id 변형 = 앵커 전멸
site/data로 옮길 때 id를 prettify·재번호·소문자화하면 교차링크(timeline↔life↔people↔org↔references)가 전부 끊긴다. **무변형 보존**(§3 D-01). qa가 끊어진 앵커 전수 검출.

### 5.3 actors/orgs ≠ node_id (최다 통합 버그 후보)
timeline `actors`/`orgs`는 표시명 **문자열**이다(per-id 아님). 실측(렌더 165건 기준): distinct actor 134개 중 53개, org 68개 중 25개만 노드 매핑. **추측 매핑·문자열을 id로 사용 금지.**
- **회피:** data-engineer가 빌드 시 `actor_refs`/`org_refs` 파생 필드 생성(§3.1). `node_id`=null이면 평문, non-null이면 앵커. timeline-developer는 이 파생 필드만 신뢰.

### 5.4 D등급·edges_unconfirmed 무단 노출
- timeline: D등급 7건은 data/timeline.json **본체에서 제외**되어야 함(렌더할 데이터가 없어야 정상). 만약 본체에 있으면 데이터 결함 → qa 리포트, 렌더 금지.
- network: edges_unconfirmed 19건은 **그래프 본체 렌더 금지**, people "미확정 관계" 목록 전용(§3.3). 그래프 노드/엣지 배열에 섞으면 00_common §6.1 위반.
- D등급 어록: archives "채택하지 않은 전승"에서 메타 주장(clm-0282~0285, B등급) 경유만(00_common §6.1 유일 예외).

### 5.4b 병합 전 id 참조 = 교차평면 끊어진 앵커 (archives 최다 위험)
archives 카탈로그의 `related_event_ids`는 병합 전 id를 다수 포함 → site/data/timeline.json(렌더 165)에 그대로는 없다(57개 중 55개 merged_from 해소·2개 D 제외). 그대로 링크하면 **57개 끊어진 앵커**.
- **회피:** data-engineer가 빌드 시 timeline `merged_from` 맵으로 생존 id 치환 + D 제외분 링크 제거(§3.5b D-24). site/data/archives.json엔 렌더 가능한 id만. network 엣지는 이미 클린(처리 불요).

### 5.5 끊어진 각주 = 빈 화면 금지
ref-NNN이 refs/sources에 없거나 source_id 미존재 → 조용히 삼키지 말고 가시화(`[ref:ref-NNN ⚠]`)+console.warn(§3.4). 빈 각주·삼킨 에러는 qa가 못 잡는 결함.

### 5.6 timeline.json 이름 충돌
`data/timeline.json`(연표 데이터) ≠ `data/pages/timeline.json`(연표 페이지 도입문). 로더 호출 시 전체 경로 명시(§2). map도 동일.

### 5.7 ES module + http.server MIME
`<script type="module">`는 서버가 `.js`를 `text/javascript`로 서빙해야 동작. `python3 -m http.server`는 .js MIME을 올바로 준다(검증됨). 그래도 모듈 import 경로는 상대 경로(`./loader.js`)로.

### 5.8 데이터 파일 크기
timeline.json(원본 495KB)·claims_register는 크다. site/data/timeline.json은 D 제외 165건이라 더 작지만, detail 필드 포함 시 여전히 큼. 페이지 최초 로드 성능 = performance-optimizer 검사 대상(번들 없으니 gzip은 호스팅 의존). 본 단계는 분할 강제 안 함 — 단일 fetch 유지(단순성 우선), 성능 예산 초과 시 performance-optimizer가 분할 제안.

### 5.9 Leaflet CDN 의존
map.html만 Leaflet CDN 로드(`<link>`+`<script>`). CDN 실패 시 map만 영향 → §3.2 텍스트 목록 폴백. 다른 페이지로 전파 금지(연표는 Leaflet 불요).

---

## 6. 작업 분해(WBS)와 의존 순서 (Phase 4b)

> 의존 순서 = 무엇이 무엇을 막는가. 병렬 가능 구간을 명시해 5인 팀이 대기 없이 작업.

### 단계 0 — 선행(Phase 4a 잔여, 4b 착수 전 완료 필요)
| # | 작업 | 소유 | 산출 | 막는 작업 |
|---|------|------|------|----------|
| W0.1 | data/*.json 변환(§3 계약대로) | data-engineer | data/{timeline,network,citations,archives,images}.json + pages/*.json | W2.*, W3.*, W4.* 전부 |
| W0.2 | tokens.css + design-system.md | ui-designer | css/tokens.css | W1.2(main.css) |

### 단계 1 — 공유 기반(frontend-developer, 다른 페이지보다 선행)
| # | 작업 | 산출 | 의존 | 막는 작업 |
|---|------|------|------|----------|
| W1.1 | loader.js + renderLoadError | js/loader.js | W0.1 | 전 렌더 작업 |
| W1.2 | layout.js(헤더·내비 10·푸터) + main.css | js/layout.js, css/main.css | W0.2 | 전 페이지 HTML |
| W1.3 | footnotes.js(각주 렌더 §3.4) | js/footnotes.js | W0.1, W1.1 | 본문 있는 전 페이지 |
| W1.4 | page-render.js + periodOf 유틸(§3.7) | js/page-render.js | W1.1 | 일반 8페이지·timeline·map 시기 |

### 단계 2 — 페이지 구현(병렬 — 소유권으로 충돌 0)
| # | 작업 | 소유 | 의존 |
|---|------|------|------|
| W2.1 | index.html(홈: 도입·탐색카드·통계박스) | frontend-developer | W1.1–1.4 |
| W2.2 | life.html(15장·공백) | frontend-developer | W1.* |
| W2.3 | organizations.html(10절·org 앵커) | frontend-developer | W1.* |
| W2.4 | philosophy.html(9절·어록 검증표) | frontend-developer | W1.* |
| W2.5 | people.html(관계망 그래프 vanilla + 서사 + 미확정 목록) | frontend-developer | W1.*, W0.1(network) |
| W2.6 | archives.html(카탈로그·비판·미확인·채택안한전승) | frontend-developer | W1.* |
| W2.7 | gallery.html(매니페스트 뷰·역링크) | frontend-developer | W1.*, W0.1(images) |
| W2.8 | references.html(인용 일람·방법론) | frontend-developer | W1.*, W0.1(citations) |
| W3.1 | timeline.html + timeline.js(인터랙티브 연표·시기 필터·disputed 표시·폴백) | timeline-developer | W1.1–1.4, W0.1(timeline) |
| W4.1 | map.html + map.js(Leaflet·마커·경로·시기 슬라이더·폴백) | map-developer | W1.1–1.4, W0.1(timeline) |

> frontend의 8페이지(W2.1–2.8)는 공유 기반(W1.*) 완료 후 서로 독립 — 순차/병렬 자유. timeline(W3)·map(W4)은 frontend 페이지와 완전 병렬(소유 파일 분리). 단 셋 다 W1.* 공유 모듈에 의존하므로 W1.*가 임계 경로.

### 단계 5 — QA·접근성·성능(구현과 인터리브 + 최종 게이트)
| # | 작업 | 소유 | 의존 |
|---|------|------|------|
| W5.1 | 모듈 완성 직후 incremental QA(web-qa-protocol) | qa-engineer | 각 모듈 완성 즉시 |
| W5.2 | 접근성 감사(키보드·대비·alt·aria, motion-reduce) | a11y-engineer | 각 페이지 완성 후 |
| W5.3 | 성능 측정(번들·이미지·로드) | performance-optimizer | 페이지 완성 후 |
| W5.4 | 최종 게이트(00_common §8 8항 + 경계면 교차·끊어진 앵커/각주 전수) | qa-engineer | 전체 완성 |

**임계 경로:** W0.1(data) → W1.1(loader) → W1.3/W1.4(footnotes·page-render) → 페이지들 → W5.4(최종 게이트). W0.2(tokens)는 W1.2와만 직렬, 나머지와 병렬.

---

## 7. 결정 기록 (결정 / 이유 / 기각한 대안)

| # | 결정 | 이유 | 기각한 대안 |
|---|------|------|------------|
| D-01 | 데이터 id 무변형 보존(evt/per/org/src-pri/ref/src-*) | 앵커=id(sitemap §4 승계). 변형 시 교차링크·QA 경계 비교 전멸 | id prettify/재번호 — 끊어진 앵커 양산 |
| D-02 | timeline 본체에서 D등급 7건 물리 제외(165건 출력) | 00_common §6.1 D 노출 0. 데이터에 없으면 렌더 사고 원천 차단 | 플래그만 달고 본체 유지 — 실수로 렌더될 위험 |
| D-03 | actors/orgs를 빌드 시 actor_refs/org_refs(name+node_id\|null, ambiguous 플래그)로 해소 | actors는 표시명 문자열·렌더 165 기준 53/134 actor·25/68 org만 노드 매핑. 런타임 매핑은 로직 중복+추측 위험. 빌드 해소가 단일 진실+QA 대조 용이. data-engineer 검증 동의(cross-kind 오해소 0) | 런타임에 timeline.js가 name_normalization 직접 로드 — 매핑 로직 timeline/map 중복, 미매핑 처리 누락 위험 |
| D-04 | edges_unconfirmed(19, D) 그래프 본체 제외, people "미확정 목록" 전용 | 00_common §6.1 + network 스킬 §5(삭제 금지·본체 제외). 그래프에 섞으면 D 노출 | 그래프에 점선으로 표시 — D등급 시각 노출, 정책 위반 |
| D-05 | 본문 마커 형식 = [ref:ref-NNN] 확정 | drafts 실측 1,211개 전부 ref-NNN 정규화 완료(00_common §3 2단계 완료). 렌더러 입력 단순화 | 잠정 마커(clm-/evt-) 런타임 해석 — 정규화 단계 무력화·매핑 추측 |
| D-06 | 각주 렌더는 footnotes.js 단일 공유 모듈(전 페이지) | 각주 로직 페이지별 복붙 시 불일치=통합 버그. 렌더 경로(ref→source_id→앵커) 단일화로 QA 대조 일관 | 페이지별 각주 렌더 — 복붙 불일치, 끊어진 각주 처리 제각각 |
| D-07 | 헤더·내비·푸터 = layout.js 단일 주입 | sitemap §2·site-architecture §3. 복붙 내비는 페이지 추가 시 한 곳 누락 | 페이지별 HTML에 내비 하드코딩 — 10페이지 동기화 불가 |
| D-08 | ES modules(번들러 없음) | 빌드 0 원칙. 브라우저 직접 로드, http.server가 MIME 정상 제공 | webpack/rollup — 빌드 의존 부패·에이전트 빌드 충돌(스택 원칙 위배) |
| D-09 | people 관계망 그래프 = vanilla SVG/Canvas(라이브러리 금지) | 의존성 최소주의(위험성향 3). 노드 81·엣지 135는 vanilla로 충분. d3는 큰 의존+학습비용 | d3.js/cytoscape — 추가 외부 의존(Leaflet 외 금지 원칙 위배), 사유서 미통과 |
| D-10 | Leaflet만 외부 의존 허용(map.js 격리) | 슬리피 맵 직접 구현 비현실적. MIT·의존성0·OSM 무료. map만 영향 | Mapbox/Google(API키·과금·추적), 직접 구현(수천 줄 미검증 코드) |
| D-11 | 데이터 경로=페이지 기준 상대(`data/...`), 모듈 import도 상대 | 서브디렉토리 호스팅(GitHub Pages 프로젝트 페이지) 호환 | 절대 경로 `/data/` — 루트 호스팅에만 동작 |
| D-12 | 시기(P1–P8)는 date.start로 단일 함수 periodOf 계산 | timeline 필터·map 슬라이더가 다른 경계 쓰면 교차 정합 깨짐. 단일 유틸로 통일 | 페이지별 경계 하드코딩 — 시기 경계 불일치 |
| D-13 | 단일 fetch 유지(데이터 분할 강제 안 함) | 단순성 우선. 성능 예산 초과 시에만 performance-optimizer 분할 제안 | 선제 분할(lazy chunk) — 미증명 최적화, 복잡도 증가 |
| D-14 | CSS 경로 = `site/css/` (assets/css 아님) | site-architecture §2·dosan-design-system 스킬·기존 커밋 3중 일치. team-lead 지시문의 assets/css는 단발 표기로 판단·통일 | `site/assets/css/` — 두 스킬·기존 레이아웃과 불일치, 4b 탐색 비용 증가 |
| D-15 | CSS 클래스 = 무접두 케밥(공통) + 모듈 접두(`tl-`/`map-`/`nw-`) + `is-`/`has-`(상태) | 단일 main.css 네임스페이스를 다개발자 공유 → 접두로 충돌 사전 차단(CSS 평면 소유권). ui-designer 합의(`nw-`=people 그래프 추가) | BEM 전면(`.c-card__title`) — 정적 사이트엔 과한 형식. 무규약 — 클래스 충돌 위험 |
| D-16 | disputed 이벤트에 `dispute{status,adopted{...},variants[]}` 객체 노출(dispute_note와 함께) | 실측 17건 전부 보유. conflicts.md (a)통설+각주/(b)양론병기 문형의 데이터 원천. dispute_note(한 줄)만으로는 양론 병기 불가 | dispute_note만 노출 — 이설(variants) 소실, 연구자 여정(J2) 검증 깊이 부족 |
| D-17 | `has_geo`(place.lat&&lng) 빌드 파생 + map은 이 필드로 필터 | 좌표 유무 판정 로직을 빌드 1곳에 고정. map이 매번 null 체크하면 로직 분산 | map이 런타임 null 체크 — 판정 분산, qa 대조 기준 불명 |
| D-18 | timeline 딥링크 = `#evt-id` + `?period=PN` (03_timeline.md L18 이관) | 명세가 형식 고정·구현 계약을 architecture.md로 명시 이관. 타 페이지 "이 시기 연표" 링크의 목적지 | 구현 자유 — 페이지마다 다른 쿼리 형식, 링크 깨짐 |
| D-19 | network 노드에 `kind`(person/org) 빌드 파생 | id 접두로 산출, people/org 페이지 분기를 데이터 평면에서 1회 해소. data-engineer 제안 채택 | 소비자가 id 접두 매번 파싱 — 분기 로직 중복 |
| D-20 | ~~제외~~ **정정: `place_normalization`(network.meta, 4건) 계약 포함**(지명 상충 cfl-036~039, variants 병기) | data-engineer 회신으로 `network.meta.place_normalization` 실재 확인. 최초 "부재" 판정은 web-architect가 network top-level만 검색한 오판 — 정정. map·본문 지명 표기의 데이터 원천 | (기각) 제외 유지 — 실재 데이터 누락, 지명 상충 병기 불가 |
| D-21 | `data/meta.json` 신설 — 사이트 자기 집계 수치 단일 출처 | 01_home L10(수치는 데이터 메타에서만)+00_common §3(iii)(자기 서술 수치는 사이트 JSON 근거). home·qa가 같은 출처. data-engineer 제안 채택 | 페이지별 수치 하드코딩 — 재계산 불일치, qa 정합 검사 기준 부재 |
| D-22 | 이미지 데이터 파일명 = `images.json`(gallery.json 아님) | sitemap §4·09_gallery.md·00_common §1·site-architecture §2 4중 일치. team-lead 지시문 gallery.json은 소수 | gallery.json — 계약 4종과 불일치, 앵커표와 어긋남 |
| D-23 | `search-index.json` 보류(미승인, 금지도 아님) | 명세가 전역 검색 미요구. timeline 내부 필터로 J2 충족. 소비처 확정 시 §2 절차로 승인 | 지금 계약에 강제 — 미사용 산출물·소비처 미정 스코프 크리프 |
| D-24 | archives `related_event_ids`를 빌드 시 merged_from 해소+D제외 필터 후 저장 | 실측 57개 참조가 병합 전 id(55 merged_from 해소·2 D제외). 그대로 링크 시 57 끊어진 앵커. network 엣지는 이미 클린 | 소비자(archives.js)가 런타임 해소 — merge 맵 로딩 중복, 미해소 시 깨진 링크. 원본 그대로 링크 — 57 끊어진 앵커 |

---

## 9. 자기 검토 — "4b 개발자가 이 문서만으로 구현 가능한가" (반성성)

초안 v0.9를 4b 개발자 시점으로 1회 자기 검토한 결과.

**발견·수정한 결함:**
| # | 발견 | 수정 |
|---|------|------|
| 1 | archives.html의 사료 카탈로그 데이터 계약 누락 — 08_archives.md는 `01_research/primary-source_catalog.json`(47건)을 소비하나 §3 계약에 없었다. `src-pri-NNN` 앵커의 출처이기도 하다. | §3.5b 신설(archives.json 계약), §2 데이터 목록·W0.1에 추가 |
| 2 | timeline/map의 "지도에서 보기"·시기 필터가 데이터 명시 필드 없이 동작해야 함 — 산출 규칙 모호 | §3.7 periodOf 단일 함수 계약 명시(경계연도 부등호 확정), D-12 |
| 3 | `data/timeline.json`(데이터)과 `data/pages/timeline.json`(도입문) 이름 충돌 가능 | §2·§5.6 경로 접두 구분 명시 |
| 4 | 끊어진 각주·미매핑 actor 처리 시 "빈 화면 vs 가시화" 모호 | §3.4·§5.5(각주 가시화+warn), §5.3(node_id null=평문) 명문화 |

**확인한 구현 가능성:** timeline·map·각 페이지 개발자가 (a) 자기 데이터의 정확한 필드·null 정책(§3), (b) 자기 소유 파일(§4), (c) 공유 모듈 시그니처(§3.0·§3.4·§3.6), (d) 작업 순서·의존(§6), (e) 함정 회피(§5)를 본 문서만으로 알 수 있다.

**미확정 항목 — 전건 해소(2026-06-06):**
- ~~§3.1 actor_refs/org_refs 파생 위치(D3)~~ **해소** — data-engineer가 period·has_geo·kind를 빌드 파생하는 방식과 일관되게 actor_refs/org_refs도 **빌드 시 파생** 확정(§3.1). node_id=null→평문, non-null→앵커.
- ~~§3.6 pages/*.json blocks vs html(D6)~~ **해소·확정 = blocks** — data-engineer 실측 후 blocks(6유형: paragraph/blockquote/table/list/slot/heading) 채택, html 평문 기각(드래프트 앵커 71·표·슬롯 구조 보존 불가). 3불변(ref-NNN·md링크·id 무변형) 충족. page-render.js는 이 blocks 스키마(§3.6)로 파싱.
- ~~§4 ui-designer 경계~~ **해소** — CSS 경로 `site/css/`(D-14)·클래스 네이밍(D-15). 토큰·컴포넌트 세부는 design-system.md 소유.
- **data-engineer 제안 반영분(2026-06-06):** dispute 객체(D-16)·has_geo(D-17)·딥링크(D-18)·kind(D-19)·**place_normalization 포함(D-20 정정)**·meta.json(D-21)·images.json 파일명(D-22)·search-index 보류(D-23)·actor_refs ambiguous 플래그(D-03).
- → **전 미확정 해소 완료. 본 문서 v1.0 승격.** 4b 팀 확정 고지 대상.

**v1.0 잔여 권고(블로커 아님):**
- page-render.js는 data-engineer의 §3.6 표현 선택(blocks|html) 통지를 받은 뒤 본문 파싱 구현. 그 전까지 골격·로더·footnotes는 선행 가능.
- meta.json·images.json 산출은 data-engineer 진행 중(Task #3) — qa는 meta 수치 ↔ 데이터 정합 검사를 게이트에 포함.

## 10. Phase 4b 인계 고지 (5개발자 진입점)

> 이 문서가 4b 팀(별도 팀)의 인계 수단이다. 각자 자기 섹션부터 읽고, 막히면 web-architect에 질의(추측 금지).

**공통(전원 먼저):** §1 스택 / §2 디렉토리 / §5 함정(특히 §5.1 file:// — 미리보기는 반드시 `cd site && python3 -m http.server 8000`) / §6 WBS·의존순서.

| 개발자 | 진입 계약 | 소유 파일 | 선행 의존 |
|--------|----------|----------|----------|
| **frontend-developer** | §3.0 로더·§3.4 각주·§3.5 images·§3.5b archives·§3.6 pages·§3.8 meta·§4 소유권 | 일반 8 html, main.css, loader/layout/footnotes/page-render.js, people 그래프(vanilla SVG `nw-`) | W0.1 data, W0.2 tokens.css |
| **timeline-developer** | §3.1 timeline·§3.2 도입문·§3.7 시기(`period` 읽기)·딥링크(§3.1) | timeline.html, timeline.js (`tl-` 클래스) | W1.1–1.4 공유모듈, data/timeline.json |
| **map-developer** | §3.1(map 소비분: `has_geo`·좌표)·§3.2·interactive-viz 폴백 | map.html, map.js (`map-` 클래스, Leaflet CDN) | W1.1–1.4, data/timeline.json |
| **a11y-engineer** | §4 규칙2(접근성 예외=전 파일 수정권+사후 고지)·design-system.md 대비표 | (감사·수정 전권, 소유자 고지) | 각 페이지 완성 후 |
| **qa-engineer** | §3 전 계약의 "소비 필드"=경계 비교 기준·00_common §8 게이트·§3.4 끊어진 각주·§3.5b·§5.4b 교차평면 앵커 | web-qa-protocol 스크립트 | 모듈 완성 직후 incremental |

**4b 전원 불변 3계명(위반=통합 버그):**
1. **데이터 id 무변형**(앵커=id). HTML에 사실 텍스트 하드코딩 금지 — 전부 `data/`에서 fetch.
2. **D등급·edges_unconfirmed 노출 0**(§5.4). 끊어진 각주·미매핑 actor는 가시화(빈 화면 금지, §5.5·§5.3).
3. **공유 모듈 시그니처는 계약**(§3.0·§3.4·§3.6) — 변경 시 전 소비자 사전 고지. 소유 아닌 파일 직접 수정 금지(§4).

**데이터 준비 상태:** data-engineer가 D1–D7+D8·D16–D24 기준 site/data/*.json 구현·검증 완료(Task #3). frontend는 §3.6 표현(blocks|html) data-engineer 통지 수령 후 page-render 본문 파싱 구현. 그 전 골격·로더·layout·footnotes·tokens 연결은 선행 가능.

## 변경 이력
| 일자 | 버전 | 변경 | 사유 |
|------|------|------|------|
| 2026-06-06 | v0.9 | 최초 초안 — 스택·디렉토리·인터페이스 계약 7종·소유권·함정 9·WBS·결정 13 | - |
| 2026-06-06 | v0.9 | 자기검토 보강 — archives.json 계약(§3.5b) 추가, periodOf(§3.7) 명시, coord 113 정정 | 누락·모호 항목 4건 수정 |
| 2026-06-06 | v0.9 | ui-designer 경계 확정 — CSS 경로 site/css/(D-14), 클래스 네이밍 규약(D-15·§4 규칙 7·8) | team-lead 지시문 vs 스킬 경로 충돌 해소(스킬·기존 커밋 기준) |
| 2026-06-06 | **v1.0** | data-engineer 합의 반영·전 미확정 해소 — dispute 객체(D-16)·has_geo(D-17)·딥링크(D-18)·kind(D-19)·place_normalization 제외(D-20)·meta.json(D-21)·images.json 파일명(D-22)·search-index 보류(D-23). D3(actor_refs 빌드 파생)·D6(pages blocks\|html 택1) 확정. **4b 팀 확정 계약** | data-engineer 3건 회부 + 제안 스키마 합의 |
| 2026-06-06 | v1.0 | archives related_event_ids 교차평면 결함 차단(D-24·§3.5b·§5.4b) — 빌드 시 merged_from 해소+D제외 필터 의무 | 실측 57개 병합 전 id 참조 발견(끊어진 앵커 위험) |
| 2026-06-06 | v1.0 | nw- 그래프 접두 추가(§4 규칙8·D-15) + §10 4b 인계 고지 신설(5개발자 진입점·불변 3계명) | ui-designer nw- 합의 + 4b 핸드오프 |
| 2026-06-06 | v1.0 | **team-lead v1.0 확정 승인** — 오버라이드 2건(site/css/ D-14·images.json D-22) 스킬·기존 커밋 정합 기준 유지 승인. 잔여 쟁점 0, 4b 인계 확정 | team-lead 종결 승인 |
| 2026-06-06 | v1.0 | **data-engineer 검증 회신 반영(7건 전건 동의)** — ① D-20 정정: place_normalization은 network.meta에 실재(4건) → 계약 포함(web-architect 최초 top-level만 검색한 오판 정정) ② actor/org 매핑 수치를 렌더 165 기준으로 정정(53/134·25/68) + ambiguous 플래그(D-03) ③ D6 blocks 확정(6유형 스키마 §3.6) ④ coord 113 = 117−D좌표4 reconcile 확인 | data-engineer 실측 검증·정정 2건 |
| 2026-06-06 | v1.0 | **team-lead 회부 계약 텍스트 정정 2건(해체 전 최종)** — ① §3.3 edge type enum `teacher_student`→`mentor` 정정(데이터 실측 6유형: membership·comrade·family·conflict·mentor·patron, 사제 3건. 오기 시 4b가 mentor 필터 누락) ② D-20 place_normalization 실재 계약 포함 재확인 | team-lead 회부 — 4b 필터 누락 차단 |

> **변경 이력 추가 (team-lead, 2026-06-06, D-25):** §2·§4·D-15 개정 — 모듈별 CSS 파일 공식 채택: `site/css/timeline.css`(tl- 전용, timeline-developer 소유)·`site/css/map.css`(map- 전용, map-developer 소유). 근거: §4 충돌 0 원칙(2인 소유 0)이 main.css 단일 네임스페이스보다 우선. 조건: 모듈 접두 클래스만 수록, tokens.css 변수 참조 의무(하드코딩 hex 금지), 링크 순서 tokens→main→모듈. main.css는 frontend-developer 단독 소유 유지(nw- 포함 무접두 공통). qa-engineer 거버넌스 회부에 대한 team-lead 판정(web-architect 해체 후 계약 해석 권한 대행).

> **변경 이력 추가 (team-lead, 2026-06-06, Phase 5 수정 라운드 1):** §3.5b archives 카탈로그 47→48 — CQA-002 정정(src-pri-048 중외일보 1930-01-11, Phase 3 인용 체계 선등재분의 카탈로그 증분 이행). build_data.py·check_data_schema.py 계약 assert 동기 갱신. 부수: CQA-001(이미지 캡션 상경 연도 한정 문형), CQA-003·004(timeline summary 2건 한정표지 보강 — 02_verified changelog_phase5 기록).
