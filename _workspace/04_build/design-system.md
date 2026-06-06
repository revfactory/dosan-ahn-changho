# 디자인 시스템 — 도산 안창호 일대기 사이트

> **v2.0 (2026-06-06)** / 작성: ui-designer (Phase 4a) / 개정: dosan-redesign 팀
> 기준 스킬: `dosan-design-system` **v2 — "맑은 한지, 살아 움직이는 먹"** (컨셉·토큰·대비표·애니메이션·인터랙션·컴포넌트·사진·반응형의 상위 규범)
> 토큰 구현: `site/css/tokens.css` (이 문서의 토큰표와 1:1 동기화 — §2·§9 검증 규칙)
> 소비자: Phase 4b frontend-developer(전 페이지 스타일링·인터랙션 구현), a11y-engineer(색 대비·모션 접근성 감사), timeline/map-developer(시각화)
> 입력: `sitemap.md`·`page_specs/00~10`·`images/manifest.json`(80건)·`synthesis/*`(콘텐츠 성격) / v1 기존 산출물(main.css·timeline.css·map.css 상속)
>
> **v2 개정 범위:** 모던·세련 + 인터랙티브 + 애니메이션 배경 + **밝은 톤 유지**. v1의 정적 절제 위에 *절제된 움직임*을 더한다. **v1 토큰 값은 전부 불변**(기존 CSS 상속) — v2는 새 이름의 확장 토큰을 추가만 한다(§2.5·tokens.css §10~15). v1 결정(다크 모드 기각 등)은 §11 "v1 결정 승계"로 보존한다.

이 문서는 **frontend-developer가 픽셀 단위 추측 없이** 페이지를 구현하도록 모든 시각·모션 결정을 수치로 고정한다. "은은한 베이지"가 아니라 `--paper: #F7F3EB`, "적당한 여백"이 아니라 간격 스케일 토큰, "부드러운 등장"이 아니라 `--dur-reveal 320ms --ease-out`이다. 토큰 외부 하드코딩 색/크기/모션은 계약 위반이다.

> **v2 빠른 인덱스 (신규·갱신 절):** §1 컨셉 v2 · §2.5 v2 확장 토큰표 · §2.6 v2 WCAG 대비표(유리·배경 위 실측) · §9 애니메이션 배경 스펙 · §10 인터랙션 패턴 · §10.5 컴포넌트별 모션·표면 적용 매핑표 · §11 v1 결정 승계 · §12 v2 자기 검증.

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

## 1. 디자인 컨셉 — 맑은 한지, 살아 움직이는 먹 (v2)

### v2 컨셉 진술 (모든 토큰·모션 결정의 정박점)

> **v2의 시각 언어는 v1의 무실역행(務實力行) 절제 위에 "절제된 움직임"을 더한다. 컨셉은 "맑은 한지, 살아 움직이는 먹" — 밝은 한지 바탕의 정직과 여백은 그대로 두고, 먹이 종이에 스며들 듯 부드럽고 느리고 유기적으로 움직이는 모던한 생동감을 입힌다. 세련됨은 화려함이 아니라 깊이(depth)·반응(response)·흐름(flow)에서 온다: 다층 소프트 그림자로 깊이를, 150~280ms 마이크로 인터랙션으로 즉각적 반응을, 400~700ms 스크롤 리빌과 80~140초 배경 먹번짐으로 여유 있는 흐름을 만든다. 단, 움직임은 결코 텍스트의 주인 자리를 빼앗지 않는다 — 독서 사이트의 주인공은 텍스트이고, 모션이 시선을 본문에서 빼앗으면 실패다. 그리고 v1의 핵심 윤리는 v2에서도 협상 불가다: 등급 배지·disputed·한정 문형·공백 고지가 시각적으로 읽혀야 하고, 불확실을 분위기·연출로 덮는 것은 여전히 금지다. 애니메이션 배경은 "보이는 듯 안 보이는" 수준이어야 하며(알아채는 순간 과한 것), 화려한 모션으로 사료의 빈틈을 메우려는 유혹을 거부한다.**

**v2에서도 불변(협상 불가):** WCAG AA 대비, 등급 배지·disputed의 색 단독 의존 금지, `prefers-reduced-motion` 전면 대응, 성능 예산(첫 로드 <200KB 압축 전송), 검증 윤리의 시각화(불확실성을 분위기로 덮지 않음), **밝은 색상 톤(다크 모드 전환 금지 — §11 승계)**.

### v2 컨셉을 모션·표면으로 — 다섯 가지 v2 번역 규칙

1. **밝은 바탕은 정체성이다.** 한지 라이트 톤 유지. 다크 모드 전환 금지(v1 결정 승계 §11). 깊이는 어두운 배경이 아니라 *빛(소프트 그림자·밝은 유리)*으로 만든다.
2. **움직임은 먹의 물성으로.** 모든 애니메이션은 "먹이 번지고 종이가 숨쉬는" 은유 안 — 느리고(slow) 부드럽고(soft) 유기적(organic). 기계적 바운스·네온 글로우·고채도 파티클·무한 회전은 이 사이트의 인격이 아니다(§10.4 금지 목록).
3. **반응은 즉각, 전환은 여유.** hover/focus는 `--dur-micro`(180ms)로 즉각, 리빌·장면 전환은 `--dur-reveal`(320ms)·`--ease-out`으로 — 단 스크롤 리빌은 뷰포트 하단 ≥30% 선발동으로 사용자가 미리빌 상태를 보지 않게 한다(v2.4, 스크롤 방해 피드백).
4. **단청은 여전히 인장이다.** 강조 1색 원칙 유지(화면당 단청 ≤3곳). v2는 단청 *그라디언트 파생*(`--grad-accent` 단청→노을)을 **대형 장식 표면**(히어로 획·읽기 진행바)에 한해 허용 — **텍스트에는 단색만, 그라디언트 위 본문 텍스트 금지**.
5. **유리·깊이는 절제해서.** 유리감(`--glass`)은 *배경 위에 뜨는 패널*(스티키 헤더·필터 바·지도 컨트롤·모바일 내비)에만. 장문 본문 컨테이너에는 쓰지 않는다(blur 비용·가독성). 어두운 오버레이 금지 — 밝은 반투명 + blur만.

### v2 컨셉 2안 비교 (반성성 — 자기 평가 후 1안 선택)

v1의 "라이트 vs 다크"는 §11에 승계. v2의 분기점은 **"움직임을 어떤 물성으로 줄 것인가"**다.

| 축 | **A안 — "스며드는 먹"** (채택) | B안 — "전시장 스포트라이트" (기각) |
|----|-------------------------------|-------------------------------------|
| 배경 모션 | 한지 위 먹번짐 블롭이 80~140s로 매우 느리게 표류(CSS-only) | 스크롤 연동 패럴랙스 + 마우스 추종 글로우(JS rAF) |
| 마이크로 인터랙션 | 카드 소프트 리프트 3px + 다층 그림자, 링크 밑줄 좌→우 | 카드 3D 틸트 + 네온 테두리 펄스 |
| 정서 | 차분·학술적·은은한 생동. 텍스트가 주인공 | 극적·테크 데모적. 시선이 효과로 분산 |
| 성능 | transform/opacity만, +JS ≤15KB, CPU 페인트 0 | rAF·filter 애니메이션 → 페인트 비용·발열·번들 증가 |
| 검증 윤리 정합 | "보이는 듯 안 보이는" 절제 — 불확실을 덮지 않음 | 화려한 연출이 사료의 빈틈을 분위기로 덮을 위험(컨셉 충돌) |
| 모션 접근성 | 블롭 정지·리빌 즉시화로 reduced-motion 안전 | 패럴랙스·추종은 전정 자극·멀미 위험, 끄기 복잡 |
| 모던함의 출처 | 깊이·여백·타이포 위계·부드러운 흐름 | 효과의 양 |

**선택: A안.** 기각 사유 — B안은 (1) JS rAF·filter 애니메이션이 성능 예산과 "transform/opacity만" 원칙을 깨고, (2) 마우스 추종·패럴랙스가 전정 자극으로 모션 접근성을 위협하며, (3) 무엇보다 *효과의 양으로 모던함을 만들려는* 방향이 "움직임이 텍스트의 주인 자리를 빼앗으면 실패"라는 v2 컨셉과 정면 충돌한다. A안은 "맑은 한지, 살아 움직이는 먹"을 CSS-only·저비용·끄기 쉬운 방식으로 구현하며, 모던함을 깊이·흐름·위계라는 *질*에서 끌어낸다. (B안의 3D 틸트는 향후 reduced-motion 분기 하에 인물 카드 1종에 한해 재검토 여지를 남긴다 — v2는 전면 채택하지 않는다.)

<details><summary>v1 컨셉 진술 (무실역행의 절제 — 정박점으로 승계, §11 참조)</summary>

> **이 사이트의 시각 언어는 도산의 무실역행(務實力行) 정신과, 이 사이트의 고유한 편집 윤리 — 검증 등급·상충·공백의 정직한 공개 — 를 한 몸으로 번역한다. 꾸밈없이 실질을 다하고(務實) 묵묵히 실행한다(力行)는 정신은 화면에서 "여백이 위계이고, 텍스트가 주인공이며, 강조색은 인장처럼 한 번만 찍는" 절제로 나타난다. 그리고 이 사이트가 다른 위인 사이트와 다른 점 — '확실한 것과 불확실한 것을 같은 화면에서 구분해 보여준다' — 는 시각의 핵심 과제다. 등급 배지·disputed 표시·한정 문형·공백 고지가 본문에서 시각적으로 읽혀야 하며, 동시에 본문 독해를 방해하지 않아야 한다. 화려한 효과는 도산을 말하는 것이 아니라 도산을 가리고, 불확실을 확실처럼 보이게 꾸미는 것은 이 사이트의 윤리를 배신한다.**

</details>

콘텐츠 성격 근거(synthesis 확인): life.md만 보아도 모든 사실 문장에 `[clm-]/[evt-]/[cfl-]` 근거 식별자가 붙고, C등급은 "~로 전해진다" 한정 문형을 유지하며, 상충은 양론 병기된다. 즉 **정직성이 콘텐츠의 1차 가치**이고, 디자인은 이 정직성을 가시화하되 우아하게 절제해야 한다.

### [v1 승계] 컨셉 2안 비교 — 라이트 vs 다크 (라이트 채택, §11 다크 모드 기각 사유)

| 축 | **A안 — "한지 위의 사료"** (채택) | B안 — "먹빛 아카이브" (기각) |
|----|-----------------------------------|------------------------------|
| 바탕 | 한지 베이지(`--paper #F7F3EB`) 라이트 모드. 종이 위에 글을 읽는 은유 | 짙은 먹빛 다크 모드. 박물관 전시 조명 은유 |
| 정서 | 차분·학술적·따뜻함. 장시간 독해 친화 | 극적·엄숙·대비 강함 |
| 이미지 정합 | 흑백/세피아 92% 사료가 밝은 한지 위에서 자연스럽게 안착(원본 톤과 충돌 적음) | 저해상 흑백 초상이 어두운 배경 위에서 경계가 흐려지고 노이즈가 도드라짐 |
| 검증 윤리 정합 | "정직한 종이 문서"의 은유 — 등급 배지·각주가 학술 문서처럼 읽힘 | 극적 연출이 "불확실을 분위기로 덮을" 위험 — 컨셉 진술과 충돌 |
| 가독성·접근성 | 밝은 바탕 위 먹 텍스트 16:1, 장문 한글 안전 | 다크 모드 장문 한글은 글레어·번짐 위험, 본문 길이(life 16,000자)에 불리 |
| 강조색 작동 | 단청 빨강이 밝은 바탕에서 "인장"처럼 명료 | 어두운 바탕에서 단청 빨강이 탁해지거나 형광처럼 떠 보임 |

**선택: A안.** 기각 사유 — B안은 (1) 80건 중 92%가 흑백/세피아 저해상 사료라는 이미지 제약상 어두운 배경에서 시각 품질이 떨어지고, (2) life 16,000자 등 장문 한글 본문에 다크 모드가 가독성상 불리하며, (3) 무엇보다 "극적 연출"이라는 정서가 **불확실을 분위기로 덮는** 방향이라 이 사이트의 검증 윤리 컨셉과 정면 충돌한다. A안은 도산의 절제 정신과 사이트의 정직성을 둘 다 자연스럽게 담는다. (다크 모드는 향후 `prefers-color-scheme` 토큰 분기로 별도 검토 가능하나 v1은 라이트 모드 단일로 확정 — 토큰을 시맨틱 별칭으로 설계해 분기 여지를 남겼다.)

### [v1 승계] 컨셉을 토큰으로 — 네 가지 번역 규칙 (v2 §1 다섯 규칙으로 확장됨)

> v2 갱신: 규칙 3 "장식 최소"는 §1 v2 규칙 2·5로 *대체* — 모션·유리·그림자가 "장식"이 아니라 깊이·흐름의 도구로 격상됐다(절제는 유지, "최소"에서 "절제된 적용"으로). 나머지 1·2·4는 그대로 유효.

1. **여백이 위계다.** 구분선·박스·그림자 대신 간격 스케일(`--sp-*`)로 위계를 만든다. 섹션 구분은 `--sp-7`/`--sp-8` 여백, 카드 분리는 `--sp-5` 패딩. 선(`--border`)과 그림자(`--shadow-*`)는 최후 수단. *(v2: 그림자가 카드 hover 부양에는 적극 쓰이되, 정적 위계는 여전히 여백 우선)*
2. **정직한 타이포.** 본문 세리프(`--font-serif`), UI 산세리프(`--font-sans`). 디스플레이 폰트 없음. 텍스트가 주인공.
3. ~~**장식 최소.**~~ → **v2 §1 규칙 2·5로 대체** (모션·유리·깊이의 절제된 적용).
4. **강조 1색 원칙.** 단청 빨강(`--accent`)은 한 화면에 1~3회. 링크·현재 위치·핵심 강조에만. 등급 배지·필터·일반 UI에는 청자/먹 계열을 쓰고 단청을 남용하지 않는다(§12 검증). *(v2: `--grad-accent` 그라디언트는 히어로 획·진행바 등 대형 장식 1~2곳에 한해 단청 사용 횟수에 포함해 카운트)*

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

## 2.5 v2 확장 토큰표 (tokens.css §10~15 — 추가만, v1 값 불변)

**v1 토큰 값 불변 계약(team-lead 지시):** main.css·timeline.css·map.css가 v1 토큰을 상속한다 — 실사용 확인: `--radius-md`(24회)·`--radius-sm`(16회)·`--dur-fast`(5회)·`--dur-base`(2회)·`--ease`(7회)·`--shadow-pop`(4회)·`--shadow-sm`(1회). 이 이름·값을 바꾸면 기존 페이지가 깨진다. 따라서 **스킬 §2가 같은 이름(`--radius-sm:8px`, `--dur-fast:180ms` 등)으로 제안한 값은 v1과 충돌하므로 신규 이름으로 채택**한다(team-lead가 부여한 "값 정밀 조정 가능하되 사유 기록" 재량 적용).

### 표면·깊이 (Surface & Elevation)
| 토큰 | 값 | 역할 |
|------|-----|------|
| `--paper-bright` | `#FDFBF7` | 카드 hover 표면·유리 베이스. `--bg-bright` 별칭 |
| `--glass` | `rgba(253,251,247,.72)` | 유리 패널 — **반드시 `--glass-blur`(blur 12px)와 함께**. 어두운 오버레이 금지 |
| `--glass-strong` | `rgba(253,251,247,.86)` | 모바일 내비 오버레이 등 가독 우선 유리 |
| `--glass-border` | `rgba(26,24,21,.08)` | 유리 패널 1px 보더(빛 가장자리) |
| `--glass-blur` | `blur(12px)` | backdrop-filter 표준값 |
| `--shadow-soft` | `0 1px 2px /.04, 0 4px 16px /.06` | 카드 기본 부양(다층 소프트) |
| `--shadow-lift` | `0 2px 4px /.05, 0 12px 32px /.10` | 카드 hover 부양 |
| `--shadow-glass` | `0 8px 28px /.08` | 유리 패널 부유 |

### 그라디언트 (대형 표면·장식 전용 — 텍스트 배경 금지)
| 토큰 | 값 | 역할 |
|------|-----|------|
| `--grad-accent` | `linear-gradient(135deg,#B5342B,#D4663A)` | 단청→노을: 히어로 붓질 획·읽기 진행바 |
| `--grad-wash` | `radial-gradient(closest-side, rgba(110,139,116,.10), transparent)` | 청자 먹번짐(배경 블롭 A) |
| `--grad-wash-2` | `radial-gradient(closest-side, rgba(181,52,43,.06), transparent)` | 단청 먹번짐(배경 블롭 B) |
| `--grad-edge` | `linear-gradient(180deg, rgba(26,24,21,.06), transparent)` | 스티키 헤더 하단 페이드 |

### 라운딩 v2 (v1 `--radius-sm/md/lg` 불변 → 신규 이름)
| 토큰 | 값 | 역할 / v1과의 관계 |
|------|-----|------|
| `--radius-soft` | `8px` | v2 카드·입력 (스킬 §2 `radius-sm:8px` 후보를 신규 이름으로) |
| `--radius-card` | `14px` | v2 유리 패널·대형 카드 (스킬 §2 `radius-md:14px` 후보) |
| `--radius-xl` | `22px` | v2 히어로 프레임·대형 표면 (스킬 §2 `radius-lg:22px` 후보) |
| `--radius-pill` | `999px` | 칩·필터·배지 알약형 |

> **라운딩 채택 지침(frontend):** 신규 v2 컴포넌트(유리 패널·히어로·v2 카드)는 `--radius-soft/card/xl` 채택. **기존 v1 컴포넌트의 `--radius-sm/md`는 유지**(시각 일관성 위해 점진 마이그레이션은 별도 합의). 한 페이지에서 v1 4px와 v2 14px가 인접하면 v2로 통일하되, 그 변경은 이 표에 기록.

### 모션 v2 (v1 `--dur-fast/base/slow`·`--ease` 불변 → 신규 이름)
| 토큰 | 값 | 역할 |
|------|-----|------|
| `--dur-micro` | `180ms` | 마이크로 인터랙션(hover/focus) |
| `--dur-enter` | `280ms` | 표면 전이·헤더 축소·사진 톤 복원 |
| `--dur-reveal` | `320ms` | 스크롤 리빌·장면 전환 (v2.4: 600→320) |
| `--dur-count` | `800ms` | 통계 카운트업 |
| `--dur-ambient` | `110s` | 배경 블롭 표류 1주기(80~140s 중앙값) |
| `--ease-out` | `cubic-bezier(.22,1,.36,1)` | 리빌·등장(감속) |
| `--ease-soft` | `cubic-bezier(.45,.05,.55,.95)` | 배경·루프(부드러운 인아웃) |
| `--reveal-shift` | `10px` | 리빌 translateY 오프셋 (v2.4: 16→10) |
| `--reveal-stagger` | `40ms` | 카드 그룹 리빌 스태거 (v2.4: 75→40) |
| `--lift-y` | `-3px` | 카드 hover 리프트 거리 |

> `prefers-reduced-motion: reduce`에서 tokens.css가 `--dur-micro/enter/reveal/count → 0`, `--reveal-shift/--lift-y → 0`으로 자동 중화. `--dur-ambient`는 토큰이 아니라 main.css가 배경 `animation: none`으로 정지(정적 워시 톤 유지 — §9 접근성).

### 타이포·z-index v2 (v1 불변 → 추가만)
| 토큰 | 값 | 역할 |
|------|-----|------|
| `--fs-hero` | `3.052rem` | 홈 히어로 전용(데스크톱) — 모바일은 `--fs-2xl`로 강등 |
| `--ls-hero` | `-0.02em` | 히어로·섹션 제목 자간 보정(한글 대형) |
| `--z-bg` | `-1` | 애니메이션 배경 레이어(fixed; pointer-events:none) |

> **사진 처리 v2 추가:** `--img-filter-hover: grayscale(0.65) contrast(1.02)` — hover 시 원톤 일부 복원(§10-1, CSS·원본 비변형). v1 `--img-filter`(기본 흑백 통일)는 불변.

---

## 2.6 v2 WCAG AA 대비표 (유리·배경 위 조합 실측 — check_contrast.py)

§2 v1 대비표(ink/paper 16.01 등)는 값 불변이므로 전건 유효(`check_contrast.py` exit 0 재확인 완료). 아래는 v2 신규 표면(paper-bright·유리·애니메이션 배경)에 대한 **실측** 추가분. 모든 수치는 `check_contrast.py --pair`로 산출.

### (가) `--paper-bright`(#FDFBF7) 표면 위 — 카드 hover·유리 베이스
| 전경 / 배경 | 대비율 | 본문 AA | 큰글씨·UI | 용도 |
|---|---|---|---|---|
| `--ink` / `--paper-bright` | **17.14:1** | AAA | 통과 | 유리 카드·hover 카드 본문 |
| `--ink-soft` / `--paper-bright` | **9.19:1** | AAA | 통과 | 메타·캡션 |
| `--ink-faint` / `--paper-bright` | **5.59:1** | 통과 | 통과 | 비활성·플레이스홀더 |
| `--dancheong` / `--paper-bright` | **5.82:1** | 통과 | 통과 | 밝은 카드 링크 |
| `--dancheong-dim` / `--paper-bright` | **7.36:1** | 통과 | 통과 | 링크 hover |
| `--celadon-deep` / `--paper-bright` | **5.92:1** | 통과 | 통과 | 청자 본문(불가피 시) |
| `--grade-a-text` / `--paper-bright` | **7.39:1** | 통과 | 통과 | A등급 배지 |
| `--grade-c-text` / `--paper-bright` | **5.73:1** | 통과 | 통과 | C등급 배지 |

> 스킬 §2가 적은 추정치(ink/paper-bright 16.6, dancheong/paper-bright 5.6)와 실측이 다르다 → **실측값 채택**(17.14, 5.82).

### (나) 유리 표면(`--glass`) 위 — 합성색 실측
유리 `rgba(253,251,247,.72)`는 backdrop 위에 합성된다. **최악 backdrop = 애니메이션 배경의 가장 어두운 프레임 위.** 두 블롭(`--grad-wash` 청자@.10, `--grad-wash-2` 단청@.06)이 **동시에 겹친** 최악 backdrop은 `#E6DED4`, 그 위 유리 합성 표면은 **`#F7F3ED`**(=사실상 `--paper`). 이 최악 합성색 기준 실측:

| 전경 / 유리 합성색(최악 #F7F3ED) | 대비율 | 본문 AA | 용도 |
|---|---|---|---|
| `--ink` / glass(최악) | **16.03:1** | AAA | 유리 패널 제목·본문 |
| `--ink-soft` / glass(최악) | **8.59:1** | AAA | 유리 패널 메타 |
| `--ink-faint` / glass(최악) | **5.22:1** | 통과 | 유리 패널 비활성 텍스트 |
| `--dancheong` / glass(최악) | **5.44:1** | 통과 | 유리 패널 링크·현재 내비 |
| `--celadon-deep` / glass(최악) | **5.54:1** | 통과 | 유리 패널 청자 텍스트 |

> 유리 패널 위 텍스트는 **전건 본문 AA 통과**. 단 frontend는 유리에 `--glass-blur`(blur 12px)를 반드시 동반해 backdrop을 평활화해야 한다(blur 없으면 합성 가정이 깨짐 — §10.3·§9).

### (다) 애니메이션 배경 위 **직접** 본문 텍스트 — 제약 발견(중요)
유리 없이 본문 텍스트가 애니메이션 배경 위에 직접 놓이는 경우, **가장 불리한 프레임 기준** 실측:

| 전경 / backdrop | 대비율 | 본문 AA | 판정 |
|---|---|---|---|
| `--ink` / 배경 최악(두 블롭 겹침 #E6DED4) | 13.30:1 | 통과 | 안전 |
| `--ink-soft` / 배경 최악 #E6DED4 | 7.13:1 | 통과 | 안전 |
| `--dancheong` / 배경 최악 #E6DED4 | 4.52:1 | 통과 | 경계(여유 0.02) |
| `--celadon-deep` / 배경 최악 #E6DED4 | 4.59:1 | 통과 | 경계 |
| **`--ink-faint` / 배경 최악 #E6DED4** | **4.33:1** | **불통과** | ⚠ **금지** |
| **`--grade-c-text` / 배경 최악 #E6DED4** | **4.45:1** | **불통과** | ⚠ **금지** |
| `--ink-faint` / 배경 **단일 블롭** 최악 #E9E9DF | 4.72:1 | 통과 | 안전(겹침만 위반) |
| `--grade-c-text` / 배경 단일 블롭 최악 #E9E9DF | 4.85:1 | 통과 | 안전(겹침만 위반) |

> **AA 미달 2건은 채택하지 않는다("예쁘지만 미달" 예외 없음).** 두 블롭이 겹치면 backdrop이 `#E6DED4`까지 어두워져 `--ink-faint` 본문(4.33:1)·C등급 배지(4.45:1)가 본문 AA 미달. **그러나 단일 블롭이면 둘 다 통과**(4.72/4.85:1). 따라서 미달을 막는 **설계 제약(§9에 명문화)**: ① 두 블롭(청자·단청)은 **본문 읽기 컬럼 뒤에서 서로 겹치지 않게** 배치(좌상/우하 분리), ② 본문·배지·미세 메타는 원칙적으로 `--paper`/`--paper-dim`/유리 표면 위에 놓고 raw 블롭 위 직접 배치는 큰 텍스트(`--ink`/`--ink-soft`)에 한정. 이 두 제약으로 모든 사용 조합이 AA를 통과한다. a11y-engineer는 ①②를 감사 항목으로 쓴다.

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

### v2 타이포 추가 (위계 강화 — 큰 대비가 모던함의 핵심)
- **홈 히어로**: `--fs-hero`(3.052rem, 데스크톱) — `--fs-3xl`과 같은 값이나 **히어로 전용 시맨틱 토큰**으로 분리(모바일에서 `--fs-2xl`로 강등하는 분기 지점). 모바일(<640px) 히어로는 `--fs-2xl` 적용.
- **히어로·섹션 제목 자간**: `letter-spacing: var(--ls-hero)`(-0.02em) 허용 — 한글 대형 타이포 시각 보정. 본문(`--fs-base`)에는 적용 금지.
- **숫자 통계**: `font-variant-numeric: tabular-nums` — 카운트업(§10.2) 시 자릿수 흔들림 방지. `.stat-num`에 적용.

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
- ~~hover 시 `filter: grayscale(0)` 같은 컬러 복원 효과 금지(장식 최소 원칙 + 흑백 통일의 일관성 훼손).~~ **[v1 규칙 — v2에서 §10.1로 대체]** v2는 스킬 §4-1에 따라 **hover 시 원톤 *일부* 복원을 허용**한다: `filter: var(--img-filter) → var(--img-filter-hover)`(grayscale 1→**0.65**, 완전 복원 `grayscale(0)`은 여전히 금지), `--dur-enter`(280ms), `@media (hover:hover)`에서만(터치 기기 고정 톤), CSS·원본 비변형. 기본 비-hover 상태는 흑백 통일 톤 유지 → §210 v2 추가·§639 §10.1과 정합. (team-lead D-1 판정: 스킬 v2 §4-1 우선)

### 캡션·크레딧·alt (manifest.json 사용 — 임의 작성 금지)
- 모든 `<img>`에 `<figcaption>`: manifest의 `caption`(사실 캡션+연대) + `credit`(출처) 그대로. 임의 작성·윤문 금지.
- 모든 `<img>`에 의미 있는 `alt` 필수 — manifest `caption` 기반. **이 사이트에 장식 이미지는 없다. 모든 이미지가 사료다.**
- **★base 흑백 통일 톤은 사이트 전역 의무 — 갤러리 한정 아님 (D-2 결정, 2026-06-06):** "모든 이미지가 사료"이므로 `--img-filter`(흑백 통일) 적용 대상은 **전 페이지의 모든 콘텐츠 `<img>`**(히어로·life 본문 이미지·인물 사진·갤러리 전부)다. 이는 v2 hover 기능이 아니라 §5(v1 승계 §11) 통일 톤 원칙의 정상 적용이라, "표현 계층 최소 변경" 범위를 넘는 표현 변경이 아니라 **미적용 상태가 §5 위반**이다. 구현 수단: 콘텐츠 이미지에 공유 클래스 `.figure-img` 부여(main.css가 `--img-filter` 부여) — 인라인 `style="filter:…"` 대신 클래스로(hover 전이 성립 조건). 사료 뷰어 원문 이미지에도 base 톤은 적용하되 **hover 복원은 제외**(원문=해석 혼동 방지).
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

> **§8은 v1 정적 검증으로 유효.** v2 모션·배경·유리에 대한 검증은 §12로 확장한다(중복 항목은 §12가 상위).

---

## 9. 애니메이션 배경 — "종이 위의 먹번짐" (v2 신규)

전 페이지 공통 배경 레이어. main.css가 1회 정의하고 전 페이지가 공유한다(frontend 소유). **CSS-only — canvas·WebGL·JS rAF 금지**(성능 예산·단순성).

### 9.1 시각 스펙 (frontend가 픽셀 추측 없이 구현)
| 항목 | 결정 |
|------|------|
| 레이어 컨테이너 | `position: fixed; inset: 0; z-index: var(--z-bg)(-1); pointer-events: none; overflow: hidden` |
| 블롭 수 | **2~3개** (기본 2개 권장 — 청자 1 + 단청 1; 3개째는 청자 보조 가능) |
| 블롭 A (청자) | `--grad-wash`, 크기 **viewport의 55~70%**(`clamp(380px, 60vmax, 900px)`), **좌상단 영역**(top:-10%; left:-8%) |
| 블롭 B (단청) | `--grad-wash-2`, 크기 **45~60%**(`clamp(320px, 50vmax, 760px)`), **우하단 영역**(bottom:-12%; right:-6%) |
| 블롭 C (선택, 청자 보조) | `--grad-wash`, 30~40%, 우상단 — 본문 컬럼 뒤를 피해 배치 |
| 불투명도 한계 | 블롭 자체 그라디언트 내 alpha ≤0.10(청자)·≤0.06(단청). 추가 opacity 곱 금지 |
| 모션 | `transform: translate()+scale()` + 미세 `opacity` 만. **주기 `--dur-ambient`(80~140s, 기본 110s)**, `--ease-soft`, `animation-iteration-count: infinite`, `alternate` |
| 표류 진폭 | translate ±3~6%(vmax 기준), scale 1.0↔1.08 이내 — "보이는 듯 안 보이는" 수준 |
| will-change | `transform` (블롭 요소에만, 2~3개 한정) |

### 9.2 겹침 금지 제약 (§2.6-다 대비 미달 방지 — 협상 불가)
- **블롭 A(청자)와 블롭 B(단청)는 본문 읽기 컬럼(중앙 `--measure`) 뒤에서 겹치지 않아야 한다.** 좌상↔우하로 분리 배치하고 표류 진폭을 진폭표 내로 제한해 겹침 backdrop(`#E6DED4`)이 본문 영역에 생기지 않게 한다. (겹치면 `--ink-faint`·C배지 본문 AA 미달 — §2.6-다)
- 본문·배지·미세 메타 텍스트는 `--paper`/`--paper-dim`/유리 표면 위에 둔다. raw 블롭 위 직접 텍스트는 큰 텍스트(`--ink`/`--ink-soft` 위계)만.

### 9.3 접근성·성능
- `@media (prefers-reduced-motion: reduce)`: 블롭 `animation: none`으로 **정지**(제거 아님 — 정적 워시 톤 유지). 깜빡임·고대비 플래시 절대 금지.
- 페인트 비용 유발 속성(`filter`·`box-shadow`의 **연속·루프 애니메이션**) 금지 — 배경·루프는 transform/opacity만. DevTools 페인트 플래시 0이어야 한다. (예외: 사진 hover 톤 복원의 *이산적·단일 요소·사용자 개시* `filter` 전이는 허용 — §10.1.)
- 배경 레이어 마크업은 콘텐츠가 아니므로 `aria-hidden="true"`.

```html
<!-- main.css가 스타일. 전 페이지 <body> 직속 첫 요소로 1회 -->
<div class="bg-wash" aria-hidden="true">
  <span class="bg-blob bg-blob-celadon"></span>
  <span class="bg-blob bg-blob-dancheong"></span>
</div>
```
- 클래스 `.bg-wash`/`.bg-blob`는 전 페이지 공유 → **무접두**(§0 규약). 블롭 색은 `background: var(--grad-wash)` 등 토큰 참조.

---

## 10. 인터랙션 패턴 (v2 신규)

각 패턴은 토큰·지속시간·이징을 수치로 고정한다. 적용 컴포넌트는 §10.5 매핑표가 단일 출처.

### 10.1 마이크로 인터랙션 (hover/focus — `--dur-micro` 180ms)
- **카드 리프트:** hover 시 `transform: translateY(var(--lift-y))`(-3px) + 그림자 `--shadow-soft → --shadow-lift` + 표면 `--bg → --bg-bright`. transition `transform/box-shadow/background-color --dur-micro --ease-out`. active(`:active`) 시 복귀(translateY 0). reduced-motion: `--lift-y`=0이라 이동 없음(그림자·표면 전이만).
- **링크 밑줄(좌→우):** `background-image: linear-gradient(currentColor,currentColor)` + `background-size: 0% 1px → 100% 1px` hover 전이(`--dur-micro --ease-out`), `background-position: 0 100%`, `background-repeat:no-repeat`. 색은 `--accent` 유지. (밑줄 애니메이션은 transform 아닌 background-size — 페인트 저렴, 텍스트 reflow 없음)
- **버튼·필터 칩:** hover 배경 전이(`--dur-micro`). `:focus-visible`에 `--focus-ring`(v1 단청 오프셋 링) — 키보드 사용자에게 동일 품질 피드백. 칩은 `--radius-pill`.
- **사진 톤 복원:** hover 시 `filter: var(--img-filter) → var(--img-filter-hover)`(grayscale 1→0.65), transition `--dur-enter`(280ms). 원본 비변형·CSS만. **단 hover 가능 기기에서만**(`@media (hover:hover)`) — 터치 기기 고정 톤.
  - **base 톤과 hover 복원은 별개 책임 (D-2):** base `--img-filter`는 전 이미지 의무(§5·위), hover 복원은 그 위에 얹는 v2 인터랙션이다. hover 복원은 **base 톤이 적용된 콘텐츠 이미지 중 단독으로 주목되는 단위**(갤러리 카드·홈 히어로 프레임·인물 사진처럼 사용자가 한 장씩 보는 이미지)에 적용한다. base 톤만 있고 hover 복원이 없어도 §5 위반 아님(복원은 선택적 가치, 통일 톤이 본체).
  - **성능 원칙과의 관계(명문화 — D-1 연계):** 이 `filter` 전이는 §9.3·§10.4·§12-6의 "filter 애니메이션 금지"의 **명시적 예외**다. 그 금지는 *연속·루프·대형 표면*(배경 블롭처럼 전 뷰포트에서 끊임없이 도는 filter)을 겨냥한다 — 시간당 GPU/CPU 페인트가 누적되기 때문. 사진 톤 복원은 (1) **이산적**(hover 진입/이탈 1회), (2) **단일·경계 있는 요소**(이미지 한 장, 전 뷰포트 아님), (3) **사용자 개시**(자동 재생 아님)라 누적 페인트가 없다. 따라서 허용. **단 조건:** ① `transition`만(절대 `@keyframes` 무한 루프 금지), ② `will-change` 상시 부여 금지(hover 시점에만 필요하면), ③ 동시 hover 다수 카드에서 한꺼번에 전이되지 않도록 그리드 카드 개별 hover만(전체 일괄 전이 금지). a11y: reduced-motion에서 `--dur-enter`=0이라 전이 없이 즉시 톤만 바뀐다(깜빡임 없음).

### 10.2 스크롤 리빌 (`--dur-reveal` 600ms, `--ease-out`)
- IntersectionObserver로 섹션·카드에 `is-revealed` 토글: fade(opacity 0→1) + `translateY(var(--reveal-shift))`(16px→0). 카드 그룹은 `--reveal-stagger`(75ms) 순차 지연.
- **1회만:** 관찰 후 `observer.unobserve` — 재스크롤 재생 금지(독서 방해).
- **JS 실패 폴백(필수):** 리빌 대상은 **기본 상태 "보임"**. JS가 먼저 `is-pre-reveal`(opacity:0; transform:translateY(16px))을 부여한 뒤 관찰하는 구조. no-JS면 `is-pre-reveal`이 안 붙어 콘텐츠가 그대로 보인다. **CSS에서 `.card{opacity:0}` 같은 기본 숨김 금지.**
- **카운트업:** 홈 통계 숫자 0→값(`--dur-count` 800ms). `tabular-nums` 적용. reduced-motion: 즉시 최종값(JS가 미디어쿼리 감지).

### 10.3 내비게이션·구조
- **스티키 헤더:** 스크롤 시 `--glass` + `--glass-blur` + `--glass-border` 하단 1px(또는 `--grad-edge` 페이드)로 전환. 높이 축소 전이 `--dur-enter`. 상단(스크롤 0)에서는 불투명 `--bg` 무그림자. `--z-header`(200, v1). 유리 위 내비 텍스트 대비는 §2.6-나 통과(blur 12px 필수).
- **읽기 진행 바(life 페이지):** 상단 고정 3px `--grad-accent` 바, 스크롤 비율로 `width`(또는 `transform: scaleX`) 진행. 장문 독서 보조. `--z-header` 바로 아래. reduced-motion에서도 위치 표시는 유지(전이만 즉시).
- **앵커 스무스 스크롤:** `html { scroll-behavior: smooth }`. reduced-motion: `auto`(main.css 미디어쿼리).

### 10.4 모션 금지 목록 (협상 불가)
무한 회전·바운스 루프(배경 블롭의 느린 표류는 예외 — 회전 아님), 텍스트 글자 단위 애니메이션, 자동 재생 캐러셀, hover 없이 스스로 움직이는 카드(배경 외), 100ms 미만 플래시, 마우스 추종·스크롤 패럴랙스(§1 B안 기각), `filter`/`box-shadow`의 **연속·루프** 애니메이션(페인트 비용 — 단 사진 hover 톤 복원의 이산 `filter` 전이는 §10.1 예외). **이유: 독서 사이트의 주인공은 텍스트다.**

### 10.5 컴포넌트별 모션·표면 적용 매핑표 (frontend 단일 구현 출처)
어느 페이지 어느 요소에 어떤 모션·표면을 적용하는지 픽셀 추측 없이 명시한다. "모션 없음"은 의도적 결정이다.

| 페이지 / 요소 | 표면(반경·그림자) | hover 마이크로 | 리빌 | 비고 |
|---|---|---|---|---|
| **전 페이지** 배경 | `.bg-wash` 블롭 2~3 | — | — | §9, reduced-motion 정지 |
| **전 페이지** 스티키 헤더 | `--glass`+blur, `--grad-edge` | 내비 링크 밑줄 좌→우 | — | §10.3, 스크롤 시 유리 전환 |
| **전 페이지** 모바일 내비 오버레이 | `--glass-strong`+blur, `--z-overlay` | 항목 hover 배경 | fade-in | 가독 우선 strong 유리 |
| **홈** 히어로 | 타이포 중심, `--grad-accent` 붓질 획 1개, `--radius-xl` 프레임 | 사진 톤 복원 | 진입 시 fade+shift 1회 | `--fs-hero`, 풀블리드 금지(§5). 히어로 `<img>`는 공유 `buildFigure()`가 `.figure-img` 부여 → base 톤·hover 복원 자동 성립(D-2 구현 확인) |
| **life·archives** 본문 삽화 | `.image-figure`/`.figure-img`, `.page-section`에서 max 30rem | 사진 톤 복원(D-2 광의 채택) | 슬롯 리빌 동반 | `buildFigure()` 공유 — 본문 사료 삽화도 단독 주목 이미지라 §5 base + §10.1 hover 일관 적용. 사료 뷰어 원문 `<img>`는 0건이라 충돌 없음 |
| **홈** 탐색 카드(9) | `--bg-raised`→`--bg-bright`, `--radius-card`, `--shadow-soft→lift` | 카드 리프트 | 그룹 스태거 75ms | §6.9 |
| **홈** 통계 박스 | `--bg-raised`, `--radius-card` | — | 카운트업 800ms | §6.10, `tabular-nums` |
| **life** 읽기 진행 바 | `--grad-accent` 3px | — | — | §10.3 |
| **life** 장(章) 섹션 | 본문 폭, 표면 없음 | — | 섹션 fade+shift 1회 | 본문 컨테이너에 유리 금지 |
| **life** 인용 블록 | `--bg-raised`, 좌 `--bw-accent` 청자 | — | 리빌 동반 | §6.5, 모션 절제 |
| **timeline** 사건 카드 | `--bg-raised`→`--bg-bright`, `--radius-card`, `--shadow-soft→lift` | 카드 리프트 | 진입 카드 스태거 | §6.3, timeline.js 바인딩 |
| **timeline** 필터 칩 | `--radius-pill`, hover 배경 | 칩 hover·focus-ring | — | 활성 칩만 `--accent` |
| **map** 마커 팝업 | `--bg`, `--shadow-pop`(v1 유지), `--radius-md` | — | 등장 fade `--dur-enter` | §6.11b, 팝업은 v1 그림자 |
| **map** 지도 컨트롤 패널 | `--glass`+blur, `--radius-card`, `--shadow-glass` | 버튼 hover | — | 배경 위 부유 패널 |
| **people** 인물 카드 | `--bg-raised`→`--bg-bright`, `--radius-card`, `--shadow-soft→lift` | 카드 리프트 + 사진 톤 복원 | 그룹 스태거 | §6.4 — **조건부(D-2): `.person-card`가 DOM에 방출될 때만.** 현재 people는 `nw-` 관계망 그래프로 렌더하고 `.person-card` 미방출 → 사진 hover 복원 대상 아님. 향후 인물 카드 도입 시 base 톤+hover 복원 자동 적용(`.figure-img` 부여) |
| **people** 관계망 노드 | SVG, `--rule` 테두리 | 노드 hover 강조(반경·`--accent` 테두리) | — | §6.11, reduced-motion 무관(hover만). 노드 썸네일 사진 없음(SVG 노드) → 사진 톤 복원 비해당 |
| **gallery** 이미지 카드 | `--bg-raised`, `--radius-card`, `--shadow-soft→lift` | 카드 리프트 + 사진 톤 복원 | 그룹 스태거 | §6.12, `loading=lazy` |
| **사료 뷰어** 단 | `--bg`/`--bg-raised` 구분 | — | — | §6.6, 모션 없음(해석=원문 혼동 방지) |
| **등급/disputed/소재 배지** | `--radius-pill`(grade)·점선(disputed) | — | — | §6.1·6.2·6.7, 모션 없음 |

> **절제 게이트:** 한 화면에서 동시 재생 모션 ≤3종(배경 제외), 단청(그라디언트 포함) ≤3곳. §12-6 검증.

---

## 11. v1 결정 승계 (삭제 금지 — v2가 명시적으로 유지하는 v1 결정)

| v1 결정 | 상태 | 사유 요지 |
|---|---|---|
| **다크 모드 기각** | **v2 유지** | (1) 80건 중 92%가 흑백/세피아 저해상 사료 → 어두운 배경에서 노이즈·경계 흐림, (2) life 16,000자 장문 한글 다크 모드 가독성 불리, (3) "극적 연출"이 불확실을 분위기로 덮어 검증 윤리와 충돌. v2 "밝은 톤 유지"가 이 결정을 명시 재확인. 깊이는 어두운 배경이 아닌 *빛(소프트 그림자·밝은 유리)*으로 만든다. |
| **시맨틱 별칭 우선 참조** | v2 유지 | 컴포넌트는 `--bg`/`--text`/`--accent` 등 별칭만, 원시색 직접 참조 금지. v2도 `--bg-bright` 별칭 추가로 동일 원칙. |
| **강조 1색(단청 절제)** | v2 유지·확장 | 화면당 단청 ≤3곳. v2는 `--grad-accent`를 대형 장식 1~2곳에 허용하되 단청 카운트에 포함. |
| **본문 폭 `--measure` 42rem** | v2 유지 | 한 줄 35~45자. 넓은 화면 본문 신장 금지. 유리·배경이 본문 폭을 바꾸지 않는다. |
| **흑백 통일 사진 톤** | v2 유지+hover | `--img-filter` 기본 흑백 통일 불변. v2는 hover 시 `--img-filter-hover`(grayscale 0.65) 일부 복원만 추가(터치 기기 제외). |
| **색 단독 의존 금지** | v2 유지 | 등급·disputed·소재·관계·노드 전부 텍스트 라벨/형태 병기. 유리·모션이 이 라벨을 가리거나 대체하지 않는다. |
| **경로·네이밍 계약**(`site/css/`, 케밥, `tl-`/`map-`/`nw-` 접두, `data-*` JS 훅) | v2 유지 | §0 그대로. v2 신규 공유 클래스(`.bg-wash`·`.bg-blob`·`.is-revealed`·`.is-pre-reveal`)는 무접두, 상태는 `is-` 접두 규약 준수. |
| **모듈 전용 시각화 frontend 소유(vanilla SVG)** | v2 유지 | 관계망 그래프 라이브러리 없음(D-09). v2 모션도 CSS·소량 JS(IntersectionObserver)로만. |

---

## 12. v2 산출물 자기 검증 (§8 정적 검증 + v2 모션·배경·유리)

1. **v1 토큰 불변:** tokens.css §1~9 v1 토큰 값·이름 무변경. `check_contrast.py` exit 0(v1 대비표 전건 일치) 재확인 완료. main.css·timeline.css·map.css의 `--radius-sm/md`·`--dur-*`·`--shadow-*` 참조가 그대로 동작.
2. **토큰 단일성:** `site/css/` 하드코딩 hex/rgba grep → tokens.css 외 0건(유리·그림자·그라디언트 rgba도 tokens.css §10~11에 정의).
3. **대비 전수:** 사용 조합이 §2(v1)·§2.6(v2) 대비표에 있고 통과. **애니메이션 배경 위 텍스트는 §2.6-다 미달 2건(`--ink-faint`·`--grade-c` 본문) 위반 0건** — §9.2 겹침 금지·표면 우선 배치로 회피했는지 a11y 감사.
4. **모션 접근성:** `prefers-reduced-motion: reduce`에서 ① 배경 블롭 `animation:none` 정지(톤 유지), ② 리빌 즉시 표시(`--dur-reveal`·`--reveal-shift` 0), ③ 카운트업 즉시 최종값, ④ smooth scroll 해제, ⑤ 카드 리프트 이동(`--lift-y`) 0 — 전수 확인.
5. **JS 폴백:** JS 비활성에서 모든 콘텐츠 가시(리빌 숨김 0건 — `is-pre-reveal`은 JS만 부여). 배경은 CSS-only라 그대로 동작.
6. **성능·절제:** 연속·루프 애니메이션은 transform/opacity만(DevTools 페인트 플래시 0). 사진 hover 톤 복원의 이산 `filter` 전이는 §10.1 예외(단일 요소·사용자 개시·1회, 일괄 전이·`@keyframes` 루프 금지). 추가 CSS/JS ≤15KB(압축 전), 첫 로드 <200KB 유지. 한 화면 동시 모션 ≤3종(배경 제외)·단청(그라디언트 포함) ≤3곳.
7. **유리 조건:** `--glass` 사용처에 `--glass-blur`(blur 12px+) 동반 확인(blur 없으면 §2.6-나 대비 가정 무효). 유리는 부유 패널에만, 장문 본문 컨테이너 사용 0건.
8. **문서-코드 동기화:** §2.5 v2 토큰표 ↔ tokens.css §10~15 값 일치 대조.

---

## 변경 이력

| 일자 | 변경 | 사유 |
|------|------|------|
| 2026-06-06 | v1.0 최초 작성 — 컨셉(A안 채택·B안 기각)·토큰표·대비표(신규 9조합 실측)·타이포·컴포넌트 14종·경계 상황·사진 처리·반응형 | Phase 4a 디자인 시스템 확정 |
| 2026-06-06 | **경로·네이밍 계약 확정** — architecture.md v0.9 §4 확인 후: tokens.css 경로를 `site/css/tokens.css`로 동결(team-lead 지시문 `site/assets/css/` 미채택, `assets/`는 이미지 전용 확인). 파일을 `site/css/`로 이동. 클래스 케밥 규약은 architecture.md가 ui-designer에 위임한 항목이라 본 문서 §0 규약을 표준 확정. §0·머리말·§8 경로 기재 정정 | architecture.md CSS 디렉토리 계약(`css/`)이 지시문보다 우선 — 단일 진실 공급원 정합 |
| 2026-06-06 | **모듈 스코프 접두 규약 반영** (web-architect 회신) — §0 네이밍에 모듈 접두(연표 `tl-`·지도 `map-`·공통 무접두) + JS 훅 `data-*` 권장 추가. §6.3 연표 카드 `event-card`→`tl-event-card`(공유 `.grade-badge`·`.ref-link`는 무접두 유지), §6.11b 지도 마커 팝업·경로 캡션 절 신설(`map-` 접두) | main.css 단일 네임스페이스에서 timeline.js·map.js·일반 페이지 클래스 충돌 사전 차단(CSS 평면 파일 소유권) |
| 2026-06-06 | **`nw-` 접두 확정** (web-architect §4 규칙8·D-15 확정 회신) — 관계망 그래프 모듈 접두 `nw-` 확정(제안→확정), §0 모듈 접두 3종(`tl-`/`map-`/`nw-`) 등재. §6.11 관계망 그래프를 "frontend 소유 vanilla SVG"로 명시하고 그래프 시각 토큰(노드 형태·크기 스케일 8~16px·엣지 패턴·선두께 `--bw-hair`/`--bw-accent`·색)을 frontend가 nw- 클래스에 적용하도록 구체화. **design-system.md v1.0 동결 — Phase 4b 인계 준비 완료** | 그래프=vanilla SVG·frontend 소유(D-09) 확정에 따른 소유·접두 정합 |
| 2026-06-06 | **v2.0 개정 — "맑은 한지, 살아 움직이는 먹"** (dosan-redesign 팀). 컨셉 진술 v2 신규(§1)·v2 2안 비교(A안 "스며드는 먹" 채택, B안 "전시장 스포트라이트" 기각). §2.5 v2 확장 토큰표(표면·유리·그림자·그라디언트·라운딩·모션·타이포·z) 신설. §2.6 v2 WCAG 대비표(paper-bright·유리 합성색·애니메이션 배경 위 텍스트 **실측** — check_contrast.py). §9 애니메이션 배경 시각 스펙(블롭 2~3·크기·위치·주기·진폭·겹침 금지). §10 인터랙션 패턴(마이크로·리빌·내비)+§10.5 컴포넌트별 모션·표면 매핑표. §11 v1 결정 승계(다크 모드 기각 등 보존). §12 v2 자기 검증. **v1 토큰 값·이름 전부 불변**(main/timeline/map.css 상속) — v2는 tokens.css §10~15에 신규 이름으로 추가만. | 사용자 요청: 모던·세련+인터랙티브+애니메이션 배경+밝은 톤 유지. 스킬 dosan-design-system v2 전면 개정 반영 |
| 2026-06-06 | **D-1 해소 — 사진 hover 자기모순 정정** (team-lead 판정: 스킬 v2 §4-1 우선). §5 사진 처리의 v1 잔존문 "hover 컬러 복원 효과 금지"를 취소선+"[v1 규칙 — v2에서 §10.1로 대체]" 주석화. v2는 hover 시 원톤 *일부* 복원(grayscale 1→0.65, 완전복원 grayscale(0)은 계속 금지, --dur-enter 280ms, `@media (hover:hover)`만, CSS·원본 비변형) 허용. §2.5 v2 추가(§210)·§10.1(§639)·§11 승계표와 정합 확인. | §5(v1)과 §10.1·스킬 §4-1 간 hover 정책 충돌(D-1) 해소. 기본 비-hover 흑백 통일은 유지되므로 사료 일관성 원칙 위배 아님 |
| 2026-06-06 | **D-2 결정 — 사진 톤 적용 범위 (qa-engineer 회부, §10.5 소유자 판정)**. frontend이 §10.5 3곳(히어로·people·gallery) 중 gallery에만 base 톤 적용된 현실을 짚어 (가)전체 vs (나)gallery한정 분기 회부. **판정: (가) 변형 — 단 base 톤과 hover 복원을 분리.** ① base `--img-filter` 흑백 통일은 §5(v1 승계) 전역 의무 — "모든 이미지가 사료"이므로 히어로·life·인물·갤러리 전 콘텐츠 `<img>`에 `.figure-img` 부여(미적용은 §5 위반, Task #2 범위 밖 아님). ② hover 복원은 base 톤 위 단독 주목 이미지(갤러리·히어로·인물 사진)에만 얹는 선택 가치. ③ people 인물 카드는 현재 `.person-card` 미방출(nw- 그래프 렌더)이라 hover 복원 비해당 — §10.5 people 행을 "조건부(방출 시)"로 정정, 인물 카드 신설은 별건(D-2가 강제 안 함). §5·§10.1·§10.5(히어로·people 행) 정합. | §10.5 명세(3곳)와 구현(gallery만) 괴리. base 톤(의무)과 hover(선택)를 분리해 §5 일관성은 지키되 Task #2 범위 과확장 방지 |
| 2026-06-06 | **D-2b — hover 복원 광의 범위 확정 + 구현 사실 정정** (frontend 투명 공유 회신 후). frontend가 hover 복원을 §10.5 3행이 아니라 `.figure-img` 전반(공유 `buildFigure()` 경유 — 히어로·life·archives 본문 삽화 포함)에 적용했음을 확인. **이를 정식 채택**: 본문 사료 삽화도 독자가 한 장씩 주목하는 사료라 gallery·히어로와 동질 → §5 base + §10.1 hover 일관 적용이 옳다. 좁히면 셀렉터 복잡·독서 경험 비일관만 생긴다. §10.5에 "life·archives 본문 삽화" 행 추가. **D-2 구현 사실 정정:** 직전 D-2에서 "히어로 img에 `.figure-img` 미부착"이라 적었으나, page-render.js가 비-UTF-8이라 grep이 조용히 건너뛴 탓의 오판이었다 — 실제 `buildFigure()`(page-render.js:220)가 전 콘텐츠 img에 `.figure-img` 부여, 히어로 포함 base 톤·hover 자동 성립. **잔여 버그 1건 별도 회부:** buildFigure:221이 `image.style.filter='var(--img-filter)'` 인라인 설정 → 인라인이 `.figure-img:hover` 클래스 규칙을 specificity로 눌러 hover 복원이 gallery(인라인 제거함) 외에서 무력화될 소지(frontend에 통보). 사료 뷰어 원문 img 0건 확인(hover 제외 대상 없음). | §10.5 명세(3행)와 구현(광의)의 정합 — 구현이 더 일관적이라 명세를 구현에 맞춤. 비-UTF-8 파일 grep 누락으로 인한 D-2 사실오류 정정 |
| 2026-06-06 | **D-1b 해소 — filter 애니메이션 금지의 범위 명문화** (qa-engineer 회부 후속). §10.1 사진 hover `filter` 전이가 §9.3·§10.4·§12-6의 "filter 애니메이션 금지"와 충돌하던 것을, 금지 범위를 *연속·루프·대형 표면*으로 한정하고 사진 hover의 *이산·단일 요소·사용자 개시* 전이를 **명시적 예외**로 등재해 해소. 예외 조건 3개(transition만·`@keyframes` 루프 금지·일괄 전이 금지·will-change 상시 부여 금지) 명문화. 4개 조항(§10.1·§9.3·§10.4·§12-6) 동시 정합화. | 성능 원칙이 *연속 페인트*를 겨냥했음에도 문구가 모든 filter 전이를 포괄해, team-lead가 인가한 사진 hover(D-1)를 자기부정하던 2차 모순(D-1b) 해소 |
| 2026-06-06 | **토큰 충돌 해소 결정 기록** — 스킬 §2가 `--radius-sm:8px`·`--radius-md:14px`·`--dur-fast:180ms`·`--dur-base:280ms`·`--dur-slow:600ms`·`--ease-out`·`--ease-soft`를 *기존 v1 이름으로* 제안했으나, v1 동명 토큰을 main/timeline/map.css가 실사용 중(radius-md 24회·radius-sm 16회·dur-fast 5회·ease 7회 등)이라 그대로 덮으면 기존 페이지가 깨진다. team-lead "v1 값 불변" 지시 우선 → 스킬 제안값을 **신규 이름**(`--radius-soft/card/xl`, `--dur-micro/enter/reveal`, `--ease-out/--ease-soft`는 신규라 충돌 없음)으로 채택. 영향: 신규 v2 컴포넌트만 v2 라운딩/모션 사용, 기존 v1 컴포넌트는 v1 토큰 유지(점진 마이그레이션은 별도 합의). | v1 불변 계약 ↔ 스킬 동명 재정의 충돌. team-lead 부여 "값 정밀 조정 가능하되 사유 기록" 재량 적용 |


---
**v2.4 (2026-06-07, team-lead):** 스크롤 방해 사용자 피드백 반영 — ① 스티키 헤더의 padding-block 전이 제거(레이아웃 점프 원인, 표면 전환만 유지) ② 리빌 선발동(rootMargin 하단 35%)·duration 320ms·shift 10px·stagger 40ms. 스킬 §4-2·§4-3 동기 개정.

**v2.5 (2026-06-07, team-lead):** 스크롤 리빌 전면 폐기 + smooth scroll 제거 — 동일 피드백 2회("스크롤 방해"). v2.4 절제 조정으로 불충분 판정. 콘텐츠 즉시 표시 원칙 확립. 잔존 모션: ambient 배경·hover·카운트업·진행 바(전부 스크롤 비연동). reveal.js 삭제.

**v2.6 (2026-06-07, team-lead):** 헤더 내비 깜빡임 피드백 — 스티키 헤더 backdrop-filter 제거(애니메이션 배경 위 블러 재계산 아티팩트), 불투명 --paper-bright 표면으로 교체(대비 16.6:1 AAA). 토글 히스테리시스(진입 24px/해제 4px). 규칙화: 움직이는 배경 위 고정 표면에 blur 금지.
