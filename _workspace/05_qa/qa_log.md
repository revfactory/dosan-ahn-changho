# QA 로그 — 모듈별 incremental 검사 기록

> 기준: `.claude/skills/web-qa-protocol/SKILL.md` + `.claude/skills/dosan-design-system/SKILL.md` v2 "산출물 검증" 절.
> 원칙: "파일이 존재한다"는 통과 사유 아님 — 판정은 스크립트 실행 결과·경계면 교차 비교 증거로만.
> 검사자: qa-engineer (28).

---

# v2 라운드 — "맑은 한지, 살아 움직이는 먹" 디자인 시스템 개정 QA

> 대상 작업: Task #1(tokens.css·design-system.md v2 개정, ui-designer) + Task #2(v2 인터랙션·애니메이션 배경 구현, frontend-developer).
> 성격: 표현 계층 전용 변경 — 데이터 평면 diff 0이 게이트 전제.
> 게이트 조건: ① 회귀 0 + ② 신규 결함 0 + ③ 추가 자산 예산 내(CSS/JS ≤15KB 압축 전).

## R0. v1 기준선 (v2 증분 도착 전 캡처) — 2026-06-06

v2 증분이 도착하기 전, 회귀 판정의 비교 기준이 될 v1 상태를 실측해 고정한다.

### R0.1 스크립트 기준선 — 둘 다 exit 0 (PASS)

```
$ python3 _workspace/04_build/scripts/check_data_schema.py
검사 수행: 4613
[PASS] 전 검사 통과 — site/data 무결성 확인
DATA_SCHEMA_EXIT=0

$ python3 _workspace/04_build/scripts/check_links.py site/
검사: HTML 10개, 로컬 참조 37건, 앵커 8건
LINKS_EXIT=0
```

- check_links 앵커 경고 8건은 전부 `#main`(skip-link 타깃) — layout.js가 동적 주입하는 구조라 스크립트가 "동적 렌더면 무해"로 분류, exit 0. v2에서 헤더·skip-link 주입이 변경되면 이 항목을 재확인한다.

### R0.2 토큰 단일성 기준선 — 하드코딩 hex 0 / raw rgba 0

```
$ grep -rEn '#[0-9a-fA-F]{3,8}\b' site/css/main.css site/css/map.css site/css/timeline.css
site/css/timeline.css:325:  /* 토큰 파생: --ink(#1A1815) 45% — 하드코딩 hex 회피(design-system §8) */
```

- 유일 매치는 **주석 안** 설명 hex(실제 값은 `color-mix(in srgb, var(--ink) 45%, transparent)`). 실 하드코딩 0.
- main/map/timeline.css raw `rgba()` 사용 **0건** — 투명도는 `color-mix`+var로 처리 중.
- 판정: 토큰 단일성 기준선 **PASS**. v2가 rgba 그림자·유리 토큰(`--shadow-soft`/`--glass` 등)을 도입하면, 그 값들이 tokens.css **정의분만** 참조되는지(소비 CSS에 raw rgba 0) 재검사한다.

### R0.3 애니메이션·will-change 기준선

| 항목 | v1 기준선 | v2 감시 기준 |
|---|---|---|
| `@keyframes` 블록 (전 css) | **0개** | 신규 keyframe의 애니메이션 속성이 transform/opacity만인지 (filter·box-shadow·width·top 등 페인트 속성 금지) |
| `will-change` 선언 (전 css) | **0개** | 3개 초과 시 남용 결함 |
| transition 타깃 (페인트 유발) | main.css:78 `transition: top`(skip-link 1건) | 신규 transition이 paint 유발 속성 타깃하는지 |

### R0.4 자산 크기 기준선 (압축 전 bytes)

| 묶음 | v1 bytes | v2 상한 |
|---|---|---|
| CSS 합계 (tokens+main+map+timeline) | **59,601** | ≤ 74,601 (+15KB) |
| JS 합계 (전 14개) | **130,432** | ≤ 145,808 (+15KB) |
| tokens.css | 9,253 | — |
| main.css | 22,810 | — |
| map.css | 12,272 | — |
| timeline.css | 15,266 | — |

- 첫 로드 전송 예산(<200KB)은 이미 v1에서 JSON 지배로 OVER 상태(perf_report.md, performance-optimizer 추적분) — 이는 v2 변경 대상이 아니다. v2 게이트의 성능 항목은 **CSS/JS 추가분 ≤15KB**와 **애니메이션 속성 제한**으로 한정한다.

### R0 종합

v1 기준선 전 항목 PASS. v2 증분 도착 시 이 기준선에 대한 diff로 회귀/신규 결함을 판정한다.

**상태: tokens.css mtime 19:13(v1) — Task #1·#2 산출물 미도착. frontend-developer 증분 통보 대기 중(incremental QA 대기).**

---

## R1. tokens.css v2 개정 (Task #1, ui-designer) — 2026-06-06 21:28 도착

> 도착 증분: tokens.css 9,253B → 15,016B(mtime 21:28), design-system.md(mtime 21:29). main/timeline/map.css·JS는 v1 mtime 유지 → **소비 계층(Task #2) 미도착**. 본 절은 토큰 정의 계층만 검사한다.

### R1.1 토큰 단일성 — PASS

```
$ grep -rEn '#[0-9a-fA-F]{3,8}\b' site/css/main.css site/css/map.css site/css/timeline.css | grep -vE '주석'
  -> 0 real hardcoded hex (clean)
$ grep -rEn 'rgba?\([0-9]' site/css/main.css site/css/map.css site/css/timeline.css
  -> 0 raw rgba (clean)
```

- v2가 도입한 rgba 그림자(`--shadow-soft/lift/glass`)·유리(`--glass*`)·그라디언트(`--grad-accent/wash/wash-2/edge`)·라운딩(`--radius-soft/card/xl/pill`)·모션(`--dur-micro/enter/reveal/count/ambient`, `--ease-out/soft`) 토큰이 **전부 tokens.css 내부에 정의**됨 — skill "산출물 검증 §1"의 허용 위치. 소비 CSS(main/map/timeline)에 raw hex·rgba **0건** 유지(기존 color-mix+var 패턴 무손상).
- tokens.css 신규 색 `#D4663A`(노을, `--grad-accent` 단청→노을 그라디언트 내부 리터럴): design-system 스킬 §2 명세 리터럴과 **정확히 일치**. 그라디언트 장식 전용(텍스트 배경 아님) — 스펙 준수.

### R1.2 v1 불변 계약 — PASS (회귀 0)

- tokens.css 헤더가 "§1~§9 v1 토큰 값 절대 변경 금지, v2는 §10 이후 새 이름으로 추가만" 명시. 실제로 v1 토큰(`--radius-sm/md/lg`, `--dur-fast/base/slow`, `--ease`, `--shadow-sm/pop` 등) 값 변경 0, v2 토큰은 전부 신규 이름(`--radius-soft/card/xl`, `--dur-micro/enter/reveal`, `--ease-out/soft`)으로 추가 → main/timeline/map.css의 기존 var() 상속 무손상.

### R1.3 문서-코드 동기화 (skill §7) — PASS

- design-system.md(21:29)가 v2 토큰값을 수치로 명세(`--dur-reveal 600ms --ease-out`, `--grad-accent` 단청→노을 등). `--shadow-soft` 값 `0 1px 2px rgba(26,24,21,.04), 0 4px 16px rgba(26,24,21,.06)` — 스킬 명세·tokens.css·문서 3자 일치.

### R1.4 회귀 게이트 (스크립트 재실행) — PASS

```
$ python3 _workspace/04_build/scripts/check_data_schema.py   → DATA_SCHEMA_EXIT=0 (전건 통과)
$ python3 _workspace/04_build/scripts/check_links.py site/    → LINKS_EXIT=0
```

- 데이터 평면 무손상: site/data/*.json 전부 mtime 20:50 유지(토큰 변경이 데이터 미접촉) — 표현 계층 전용 전제 충족.

### R1.5 예산 (누적 추적) — 현재 PASS, 누적 감시 지속

| 묶음 | v1 기준 | R1 현재 | 델타 | 상한(+15KB) |
|---|---|---|---|---|
| CSS 합계 | 59,601B | 65,364B | **+5,763B** | 74,601B (여유 9,237B) |
| tokens.css | 9,253B | 15,016B | +5,763B | — |
| JS 합계 | 130,432B | 130,432B | 0 | 145,808B |

- **주의:** R1은 토큰 정의 비용만. Task #2(소비 CSS·인터랙션·배경 JS·리빌 IO) 도착 시 누적 델타가 +15KB 상한에 접근할 수 있다 — 매 증분마다 누적 재측정한다.

### R1 종합 — 토큰 계층 PASS, 게이트 보류

토큰 정의 계층(Task #1) incremental 통과. 단 **게이트 미달성**: 다음 항목은 소비 계층(Task #2) 미도착으로 **미검사**다.
- 모듈 회귀(timeline/map의 새 토큰·주입 수용 후 시각·기능 무손상, z-index 충돌)
- 애니메이션 속성 제한(@keyframes·transition이 transform/opacity만, 페인트 속성 0, will-change ≤3)
- JS 폴백(is-pre-reveal 패턴)
- 콘솔 에러 0(브라우저 런타임)

→ Task #2 도착 시 R2로 검사 후 게이트 종합 판정.

## 결함 D-1 (R1 부수 발견) — design-system.md 사진 hover 자기모순 [OPEN, ui-designer 회부]

> 발견 경위: frontend-developer가 "사진 hover filter 전이가 #2 성능 원칙과 충돌하는지" 구현 질문 → 계약 대조 중 design-system.md **내부**의 직접 충돌 발견.

**대조 증거 쌍 (같은 문서, 같은 v2):**

| 조항 | 위치 | 내용 | 방향 |
|---|---|---|---|
| v2 추가 | design-system.md:210 | `--img-filter-hover: grayscale(0.65)` "hover 시 원톤 일부 복원" | **허용** |
| §5 사진 처리 | design-system.md:331 | "hover 시 filter: grayscale(0) 같은 컬러 복원 효과 **금지**(장식 최소·흑백 통일 일관성)" | **금지** |

- 코드 영향: tokens.css:161 `--img-filter-hover` 이미 정의됨(허용 쪽이 코드까지 내려옴). 소비 CSS 미사용(Task #2 미도착)이라 런타임 결함은 아직 없음.
- 스킬 대조: dosan-design-system §4-1 "사진 hover grayscale(1)→grayscale(0.65) --dur-base 전이 허용" → §210 지지. §331은 v1 문구 미정리 잔존으로 **추정**되나, QA가 추정으로 한쪽 채택 불가(계약을 QA석에서 결정하는 것 = 권한 외).

**판정:** 계약 결함 — 어느 조항이 v2 확정인지 계약 소유자(ui-designer)가 정합화해야 함. 회부 완료.
**기대:** §210/§331 중 택일 후 design-system.md 정합화(택일에 따라 §331 수정 또는 §210+tokens.css:161 제거). + 부분복원 채택 시 "hover discrete filter 전이가 transform/opacity-only 성능 원칙의 명시 예외인지" 명문화(frontend 기술 질문 연결).
**재현:** design-system.md 210행과 331행 동시 열람.
**상태:** ~~OPEN~~ → **RESOLVED (계약 정합화 재검증 완료, 2026-06-06)**. 사진 hover 구현·검사 보류. 정합화 통보 시 재검증 후 갱신. (나머지 인터랙션은 영향 없음 — frontend가 사진 hover 분리·후순위로 구현 진행.)

**해소 재검증 (통보 신뢰 안 함 — design-system.md 직접 재대조):**
- team-lead 판정: 스킬 v2 §4-1 우선. ui-designer가 design-system.md 정정.
- design-system.md:331 — v1 금지문이 취소선(`~~...~~`) + "[v1 규칙 — v2에서 §10.1로 대체]" 주석 처리됨. **라이브(비취소·비주석) 금지문 0건** 재확인:
  ```
  $ grep -nE '컬러 복원 효과 금지' design-system.md  → 331행(취소선 안)만 매치, 유효 금지 0
  ```
- 정합 3자 일치: §210(토큰)·§331(정정)·§639(§10.1 인터랙션)·§691(v1 승계표)·변경이력(720행) 전부 동일 규칙.
- 확정 규칙 = QA 런타임 검사 기준 3개(ui-designer 지정, 문서에 명문화 확인): (1) grayscale(0) 완전복원 **금지**(:331·:639), (2) `@media (hover:hover)` 가드 **필수**(:331·:639), (3) 비-hover 기본 = 흑백 통일 `--img-filter` **유지**(:331·:691).
- 문서 변경만 — site/ 코드 미접촉(tokens.css:161 `--img-filter-hover`는 R1에서 이미 검증됨). 스크립트 재실행 불요(데이터·링크 무관).

### D-1b (D-1 (a)분기 후속) — filter 애니메이션 금지 범위 모순 [RESOLVED, 재검증 완료]

> 경위: D-1 (a)분기에서 내가 예고한 "사진 hover filter 전이가 transform/opacity-only 성능 원칙의 예외인지 명문화 필요" 질문 → ui-designer가 §10.1 hover filter 전이와 §9.3/§10.4/§12-6 "filter 애니메이션 금지" 간 2차 모순(D-1b)으로 정식화·해소.

**해소 재검증 (design-system.md 직접 재대조):**
- "filter 애니메이션 금지"가 등장하는 전 지점(§9.3:617·§10.4:640,654·§12-6:706)이 **금지 범위를 "연속·루프·대형 표면"으로 한정**하고 사진 hover의 "이산·단일 요소·사용자 개시" 전이를 **명시적 예외**로 인라인 등재함.
- 라이브(비취소) "모든 filter 전이 금지"류 문장 **0건** 재확인 — 전 매치가 예외절 동반.
- 변경이력(722행)에 D-1b 등재. check_contrast.py exit 0(대비 무영향).
- 판정: 자기부정 모순 해소. QA 회부(D-1)가 2차 모순까지 드러낸 케이스 — 경계면/계약 교차 대조법의 유효성 확인.

**→ 런타임 검증 이월 (DEFERRED-RT, 사진 hover 6조건):** 실제 사진 hover CSS(frontend 후순위 증분) 도착 시 코드로 전수 검사. 6건 통과 전 사진 hover 모듈 통과 보류 — 게이트 종합에 포함.

| # | 조건 | 검사법 | 근거 |
|---|---|---|---|
| 1 | `grayscale(0)`/완전복원 0건 | 소비 CSS grep: hover filter가 `var(--img-filter-hover)`(0.65)만, `grayscale(0)`·`filter:none` 0 | §331·§639 |
| 2 | `@media (hover:hover)` 가드 | hover 톤복원 규칙이 `@media (hover:hover)` 블록 내 | §331·§639 |
| 3 | 비-hover 기본 = 흑백 통일 | 기본 셀렉터 filter가 `var(--img-filter)` | §331·§691 |
| 4 | `transition`만(@keyframes 루프 아님) | hover filter 전이가 `transition` 속성, 해당 셀렉터에 `@keyframes`로 filter 무한 애니메이트 0 | §10.4:640 ① |
| 5 | `will-change` 상시 부여 0건 | 이미지 셀렉터에 상시 `will-change` 0(hover 시점 한정만 허용) | §10.4:640 ② |
| 6 | 그리드 일괄 전이 0(개별 hover) | hover 셀렉터가 개별 카드(`:hover`) 대상, 그리드 컨테이너 hover로 전체 일괄 전이 0 | §10.4:640 ③ |

## R2 검사 스펙 (예약 — Task #2 소비 계층 도착 시 실행)

> incremental 원칙: 1~3차 증분이 따로 오면 절을 R2a/R2b/R2c로 쪼개 도착 즉시 검사. 게이트 종합은 전 증분 통과 + DEFERRED-RT 통과 후.

### R2 공통 체크리스트 (매 증분)
- 토큰 단일성: 소비 CSS 하드코딩 hex 0·raw rgba 0(R1 기준선 유지) — 신규 CSS도 `var()`만.
- 애니메이션 속성: 신규 `@keyframes`·`transition` 속성이 transform/opacity만(페인트 유발 width/height/top/left/filter/background-position 0). 단 hover 트리거 1회 discrete `box-shadow`/`filter` 전이는 허용 범주(스킬 §4-1·design-system §10.5) — `@keyframes`로 무한·스크롤연동 paint 애니메이트만 금지(design-system:653).
- will-change: 전 CSS 합계 ≤3(블롭 2~3개 한정, design-system:609).
- 회귀 게이트: check_data_schema·check_links 재실행 exit 0, 데이터 평면 mtime 무변.
- 예산: 누적 CSS/JS 델타 ≤15KB(기준선 CSS 59,601B·JS 130,432B; R1 시점 CSS 65,364B).
- 콘솔 에러 0: `cd site && python3 -m http.server`로 해당 페이지 로드.

### R2 모듈 회귀 (timeline/map)
- timeline.html·map.html이 새 토큰·layout 주입(배경·유리 헤더·skip-link) 받고도 tl-/map- 스타일 무손상·기능 무손상.
- **z-index 충돌(차단급):** 배경 레이어 `--z-bg`(-1)·`position:fixed`·`pointer-events:none` — 지도 타일·Leaflet 팝업(`--z-popup` 300)·dialog/사료 뷰어(`--z-overlay` 400) 위로 안 올라오는지. 배경이 인터랙션 가로채면 차단.

### R2 JS 폴백
- 스크롤 리빌 대상 기본 가시(is-pre-reveal 패턴) — no-JS에서 콘텐츠 숨김 0. IO once.
- reduce: 배경 animation:none(정적 워시 유지), 리빌 즉시(--dur-reveal·--reveal-shift 0), 카운트업 즉시 최종값, smooth scroll 해제, 카드 리프트 --lift-y 0.

### a11y-engineer reduce 모드 교차 참조 (a11y 주관, QA 보고서 참조용)
> a11y_audit §4.x 정본. QA는 z-index·콘솔·예산·경계면이 정본(중복 판정 없음).
- reduce 1: 배경 `.bg-blob{animation:none}` 정지 통과(emulateMediaFeatures 실측). 콘솔 에러 0(index·life·timeline).
- reduce 2·3(리빌/카운트업)·4(smooth scroll): frontend 2·3차 증분 대기로 a11y 미감사분 — R2c 안정화 후 a11y 재감사 예정.
- z-index/aria-hidden: a11y가 부수 관측, QA 게이트(R2a: --z-bg -1·aria-hidden 주입 layout.js:85)가 정본.

### R2 추가 게이트 (ui-designer 위임 — 토큰으로 강제 불가, 실측 권한 행사)
> 근거: ui-designer 회부 + design-system.md §9.2(:612, **협상 불가**)·§12-7(:706)·§2.6-다(:259) 실측 임계.

**[GATE-A] 배경 블롭 겹침 금지 (§9.2 / §2.6-다):**
- 블롭 A(청자 `--grad-wash`, 좌상 top:-10% left:-8%)와 블롭 B(단청 `--grad-wash-2`, 우하 bottom:-12% right:-6%)가 **본문 읽기 컬럼(중앙 `--measure`) 뒤에서 겹치지 않아야** 한다.
- 임계 증거: 두 블롭 겹침 backdrop `#E6DED4` 위 `--ink-faint` 본문 4.33:1·C등급 배지 4.45:1 → **본문 AA 미달(금지)**. 단일 블롭 backdrop `#E9E9DF`는 4.72/4.85:1 통과. **즉 겹침 여부가 통과/불통과를 가른다.**
- 검사법: 배경 CSS의 블롭 위치·크기(clamp)·표류(@keyframes translate 진폭)를 §9 진폭표와 대조해, 표류 전 구간에서 두 블롭이 중앙 `--measure` 컬럼 뒤에서 겹치지 않음을 확인(좌상↔우하 분리 유지).
- **분담 확정(a11y-engineer 합의):** QA = 코드 배치(블롭 위치·clamp·@keyframes 진폭 vs §9 진폭표, 표류 전 구간 미겹침 코드 증명). a11y = 렌더 합성색 실측(본문 컬럼 중앙 좌표에서 배경 레이어 합성 픽셀색을 애니메이션 0/25/50/75% 위상에서 채취 → #E6DED4까지 안 어두워지는지 + 채취색을 check_contrast.py --pair로 --ink-faint·--grade-c-text 대비 계산해 본문 AA 유지). **"코드상 미겹침"(QA) + "렌더 합성색 안전"(a11y) 양쪽 잠금** — 갭 0.

**[GATE-B] 유리 blur 동반 (§12-7 / §2.6-나):**
- `--glass`(또는 `--glass-strong`) 사용처 전수에 `--glass-blur`(backdrop-filter: blur(12px+)) **동반** 확인. blur 없으면 유리 합성 대비 가정 무효.
- 검사법: 소비 CSS에서 `--glass`/`background:var(--glass` grep → 각 셀렉터에 `backdrop-filter`(또는 `--glass-blur` 참조) 동반 여부 대조. 유리는 부유 패널(헤더·필터바·지도 컨트롤·모바일 내비)에만, 장문 본문 컨테이너 사용 0건(design-system:706).

## R2a. 1차 증분 — 애니메이션 배경 + 유리 스티키 헤더 (frontend) — 2026-06-06 21:42 도착

> 변경: site/css/main.css(22,810→28,543, +5,733), site/js/layout.js(9,005→11,124, +2,119). **추가 발견:** site/js/home.js(7,059→9,199, +2,140) — 카운트업(2차 증분 예정분)이 함께 도착(통보 미기재). timeline/map html·css·js 변경 0.
> 검사: 자가검증 신뢰 안 함 — 전 항목 독립 재실행.

### R2a 통과 항목 (증거)
| 항목 | 방법 | 결과 |
|---|---|---|
| 토큰 단일성 | hex/rgba grep (main/map/timeline) | 하드코딩 hex 0·raw rgba 0 (R1 유지) |
| @keyframes 속성 | `bg-drift`·`bg-drift-2` 본문 읽기 + awk paint-prop grep | **transform+opacity만** (filter/box-shadow/width/top 0) — main.css:640-645 |
| will-change | 전 css grep | **2개**(블롭만, ≤3) — main.css:618 |
| GATE-B 유리 blur | `--glass` 사용처 전수 vs backdrop-filter | 유일 사용처 `.site-header.is-scrolled`(:658)에 `backdrop-filter:var(--glass-blur)` 동반(:659-660). 본문 컨테이너 유리 0 |
| JS 폴백(리빌) | opacity:0 reveal 훅 grep | 유일 숨김 = `.is-pre-reveal`(:677), 기본 숨김 트랩 0 — no-JS 콘텐츠 가시 |
| JS 폴백(카운트업) | home.js 읽기 | reduce 즉시 최종값(:42)·no-JS `start()` 폴백(:69)·IO once 확인 |
| 배경 z-index/포인터 | .bg-wash 읽기 | `position:fixed; inset:0; z-index:var(--z-bg)(-1); pointer-events:none; overflow:hidden`(:607-613) — 지도 타일·dialog 위 안 올라옴. `aria-hidden=true` 주입(layout.js:85) |
| 헤더 z-index 회귀 | 상속 확인 | `.site-header` z-index `--z-header`(200) 불변, .is-scrolled는 표면만 전환 |
| 모듈 회귀(timeline/map) | 파일 무변 + http 200 | tl-/map- CSS·JS 변경 0(토큰·layout 상속만), timeline.html·map.html HTTP 200 |
| 회귀 스크립트 | check_data_schema·check_links 재실행 | 둘 다 **exit 0** |
| 데이터 평면 | json mtime | 전부 20:50 무변 |
| 자산 200 | http.server:8200 curl | main/tokens/layout/home/index/timeline/map 전부 HTTP 200 |
| JS 구문 | node --check | layout.js·home.js 구문 OK |

### GATE-A 코드 배치 (QA 분담) — 코드상 미겹침 PASS, 렌더는 a11y
- 블롭 A(청자 좌상 top:-10% left:-8%, 60vmax, drift +4%/+3% scale≤1.06), 블롭 B(단청 우하 bottom:-12% right:-6%, 50vmax, drift -3%/-4%) — §9.1 진폭표 부합.
- 기하 계산(최악 표류 = 두 블롭이 중앙으로 최대 접근): 4개 뷰포트(768/1024/1280/1440)에서 **원 중심거리 > 반지름합 전건** → 블롭 원이 교차하지 않음(분리). 여유 마진 7.2~20.6%.
- `radial-gradient(closest-side, …, transparent)`라 경계 근방은 이미 투명 → 분리된 두 원의 코어가 만나지 않으면 동일 픽셀에 두 워시가 유의 불투명도로 동시 존재 불가 = 겹침 backdrop #E6DED4 미형성.
- **판정: GATE-A 코드 배치 측면 PASS.** 단 렌더 합성색 실측(#E6DED4 미도달 확인)은 분담상 a11y-engineer 몫 — a11y 결과 수신 후 GATE-A 양면 잠금 확정.

**[GATE-A 양면 잠금 확정 — 2026-06-06]** a11y-engineer 렌더 결과 수신·일치:
- a11y 실측(a11y_audit §4.1): index.html 본문 컬럼 중앙 x=640, 3스크롤×4애니위상=12샘플(배경 레이어만). 최악 backdrop = **#EFE7DB(휘도 231.8/255 ≈ --paper-dim)** → 겹침 임계 #E6DED4(휘도 188.4)보다 훨씬 밝음 = **겹침 backdrop 미발생**.
- QA 코드측(원 분리, 마진 7.2~20.6%)과 a11y 렌더측(#EFE7DB ≫ #E6DED4)이 **일치** → **GATE-A 코드+렌더 양면 PASS 확정**.
- **[life 좁은 컬럼 표본 추가 — 2026-06-06]** a11y가 권장 표본 수행: life.html(좁은 읽기 컬럼) 4스크롤×4위상, 최악 backdrop **#EFE8DB(휘도 232.5)** — index(#EFE7DB 231.8)와 동급 --paper-dim 수준, 겹침 임계 #E6DED4(188.4) 미도달. **넓은(index)·좁은(life) 본문 컬럼 양 페이지 타입 모두 겹침 미발생** → GATE-A 양 페이지 타입으로 닫힘(마진 휘도 ~44 여유). a11y 방법 메모: 사진 픽셀 오염(#7C7C7C) 방지 위해 img/.figure-img visibility:hidden 차폐 후 순수 .bg-wash 합성색 채취. a11y_audit §4.1 기록.

### R2a 결함/보류

**[D-2] 누적 자산 예산 해석 충돌 — HOLD (team-lead 판정 요청):**
- 측정(R0 대비 누적): CSS +11,496B, JS +4,259B, **합계 +15,755B**. 15,360B(15KB) 한도 **+395B 초과**.
- 단 분해하면: tokens.css +5,763(R1 토큰 정의 = ui-designer 자산), main.css +5,733·layout.js +2,119·home.js +2,140(v2 인터랙션 자산). **인터랙션 자산만 = +7,852B(한도 내 절반).**
- 해석 분기: "추가 자산"이 (가) 토큰 정의 포함 전체 v2 풋프린트면 **초과(+395B)**, (나) Task #2 인터랙션/애니메이션 자산이면 **여유**. design-system §12-6·task #4는 "추가 CSS/JS ≤15KB"로 표현 — 토큰 정의 포함 여부 불명.
- **QA 판정: 해석으로 통과시키지 않는다(위험성향).** 예산 기준 정의를 team-lead에 요청, 확정 전 R2a 보류. (참고: 압축 후(gzip) 기준이면 전혀 다른 수치 — 현 측정은 압축 전 raw byte.)

**[N-1] 스코프 노트(결함 아님):** home.js(+2,140, 카운트업)가 1차 증분 통보에 미기재된 채 함께 도착. 구현 자체는 양호(reduce·no-JS 폴백 확인)하나, 증분 통보 스코프와 실제 변경 파일 불일치 — frontend에 통보 정합 요청(검사 누락 방지 목적).

### R2a 종합 — 품질 항목 전건 PASS, 예산(D-2) 해석 미확정으로 모듈 보류
배경·헤더·폴백·토큰·회귀 전 항목 통과. GATE-A 코드측 PASS(렌더는 a11y 대기). **단 D-2(예산 해석) 확정 전 1차 증분 통과 보류** — 게이트는 D-2 해소 + 잔여 증분(R2b/R2c)·DEFERRED-RT·GATE-A 렌더(a11y) 후 종합.

### D-2 해소 (team-lead 판정, 2026-06-06) — R2a 품질측 PASS 확정
- **판정 (나) 채택:** 15KB 한도는 **Task #2 구현 자산(인터랙션·배경 CSS/JS) raw** 기준. tokens.css(Task #1 토큰 정의)는 별도 자산(≤8KB 서브한도, R1 +5,763B로 통과). 근거: 두 태스크가 각자 산출에 제약 부과 + 한도 목적(페이지 gzip 200KB 보호)상 전체 raw +15.7KB≈gzip 4~5KB로 침식 미미.
- **신규 게이트 항목 추가(team-lead 지시):** 최종 R 라운드에서 **페이지별 gzip 전송 ≤200KB 1회 실측**(안전판). → "최종 R 게이트" 항목으로 등재(아래 R-final 예약).
- 스킬 §검증5가 이 기준으로 명문화됨(모호성 제거).
- **R2a 품질측 PASS 확정.** (D-2로 인한 보류 해제 — 단 R2a 자산이 이후 R2b에서 재변경되어 누적 재측정은 R2b에서 갱신.)

---

## R2b. 2차 증분 — 스크롤 리빌(reveal.js) — 2026-06-06 21:46~48 도착

> 변경: **신규 site/js/reveal.js(2,484B)**, layout.js(initReveal 배선), main.css(.is-pre-reveal/.is-revealed — R2a에서 이미 읽음), home.js. **주의: 검사 중에도 frontend가 main.css/layout.js/home.js를 계속 수정 중(21:46→21:48 mtime 이동)** — 아래 수치는 21:48 스냅샷 기준, frontend 증분 안정화 통보 후 재고정 필요.

### R2b 통과 항목
| 항목 | 방법 | 결과 |
|---|---|---|
| JS 폴백(is-pre-reveal) | reveal.js 읽기 | `arm()`이 `.is-pre-reveal`를 **JS만** 부여(:el.classList.add) — no-JS면 미부여로 콘텐츠 가시. IO 부재 시 `return`(대상 그대로 보임). PASS |
| IO once | reveal.js | `obs.unobserve(entry.target)` 1회 처리. PASS |
| reduce | 토큰 의존 | `--dur-reveal·--reveal-shift` tokens.css 0 중화(R1 검증) → 즉시 최종. 하드코딩 ms 0(스태거도 `var(--reveal-stagger)`). PASS |
| 모듈 제외 | layout.js:20 boundary | `REVEAL_EXCLUDED=Set(['timeline','map'])` — 모듈 페이지 공유 리빌 제외(자체 모션 소유, 중복 방지). PASS |
| 토큰 단일성 | main.css grep(재) | hex 0·raw rgba 0 유지 |
| @keyframes 속성 | awk paint-prop(재) | transform/opacity만(main.css 변경에도 유지) |
| will-change | grep | 2개(≤3) |
| 회귀 스크립트 | check_data_schema·check_links(재) | 둘 다 **exit 0** |
| 데이터 평면 | json mtime | 전부 20:50 무변 |
| JS 구문 | node --check | reveal.js·layout.js·home.js OK |

### R2b 결함

**[D-3] reveal 셀렉터 ↔ 렌더 경계 불일치 — `.person-card` 죽은 타깃 (LOW, frontend 회부):**
- 대조 증거 쌍:

  | reveal.js 셀렉터(:6) | 렌더 코드 방출처 | 판정 |
  |---|---|---|
  | `.page-section` | home.js·gallery.js | LIVE |
  | `.card-grid > *` | home.js | LIVE |
  | `.gallery-grid > *` | gallery.js | LIVE |
  | `.archive-card` | archives.js | LIVE |
  | `.quote-block` | **page-render.js:128** (`bq.className='quote-block'`, blockquote 블록) | LIVE |
  | **`.person-card`** | **방출 코드 0건** (people.js는 `nw-` 그래프만 렌더; CSS main.css:332에 정의되나 인스턴스화하는 JS/HTML 없음) | **DEAD** |
- 영향: `.person-card` 리빌 타깃이 DOM에 존재하지 않아 해당 리빌이 발화하지 않음. **런타임 에러는 아님**(matches 0건, 무해) — 단 reveal 셀렉터가 렌더 계층이 만들지 않는 클래스를 겨냥하는 경계 불일치.
- 판정 보류(QA가 어느 쪽이 맞다고 단정 안 함): (가) people 페이지가 `.person-card`로 인물 카드를 렌더해야 하는데 안 하는 것인지, (나) reveal.js가 미사용 클래스를 겨냥하는 것인지 — frontend가 결정. 재현: `grep -rn person-card site/js` → reveal.js 셀렉터 외 0.
- **자기검사 회고(반성성):** 최초 grep(`grep -rn 'quote-block' site/js`)이 셸 상태 글리치로 false-negative를 내 `.quote-block`까지 죽은 타깃으로 오판할 뻔함. emitter 코드(page-render.js:128)를 직접 읽어 정정 — **경계 결함은 grep 1회로 단정 말고 방출 코드 읽기로 확증**해야 한다는 체크리스트 항목 추가. D-3은 `.person-card` 1건으로 확정.

### R2b 예산 (누적, (나) 기준, raw, 21:48 스냅샷)
| 자산 | R0 | 현재 | 델타 |
|---|---|---|---|
| main.css | 22,810 | 29,143 | +6,333 |
| layout.js | 9,005 | 11,719 | +2,714 |
| home.js | 7,059 | 9,099 | +2,040 |
| reveal.js | 0 | 2,484 | +2,484 |
| **인터랙션 합계** | — | — | **+13,571B (88% / 15,360)** — PASS, 여유 1,789B |
| tokens.css(별도) | 9,253 | 15,016 | +5,763 (≤8,192 PASS) |
- **⚠ 예산 경고:** R2c(카드 리프트·링크·focus·진행바)·DEFERRED-RT(사진 hover) 잔존 상태에서 여유 1,789B뿐. R2c 도착 시 초과 위험 — frontend에 잔여 예산 통보.

### R2b 종합 — 폴백·회귀 PASS, D-3(LOW) 회부, 예산 경고, 안정화 후 재고정
리빌 폴백·IO·reduce·모듈 제외 전건 PASS. D-3(`.person-card` 죽은 타깃, LOW) frontend 회부. 인터랙션 예산 88%(여유 1,789B) — 경고. **frontend가 1·2차 증분 안정화(파일 수정 종료) 통보 시 R2a+R2b 수치 1회 재고정** 후 통과 확정.

## R2c. 3차 증분 — 카드 리프트·링크 밑줄·focus-visible·읽기 진행바·smooth scroll (frontend) — 2026-06-06 ~21:48 도착

> 변경: main.css(v2.6 카드리프트·v2.7 링크밑줄·v2.8 진행바 + html scroll-behavior:smooth + reduce 블록 확장), layout.js(진행바 life 주입). 이미 21:48 스냅샷에 포함 — 인터랙션 예산 +13,571B 불변(R2c가 추가 증가 없이 흡수됨).

### R2c 통과 항목 (증거)
| 항목 | 방법 | 결과 |
|---|---|---|
| 카드 리프트 모션 | main.css:694-708 읽기 | transition = transform/box-shadow/background-color(:697-699). box-shadow는 hover-discrete 표면 전이(허용 범주, §10.4 예외). hover `@media (hover:hover)` 가드(:701). `translateY(--lift-y)`+`--shadow-lift`+`--bg-bright` 토큰. active 복귀. PASS |
| 링크 밑줄 | main.css:710-726 | `background-size` 0%→100% 전이(:716-717) — paint 속성이나 hover **discrete 1회 전이**, §4-1이 명시 처방한 "background-size 기법"(reflow 없음). @keyframes 무한 아님. `@media(hover:hover)` 가드. 색 `--accent` 유지. is-current 상시 밑줄. PASS |
| 진행바 | main.css:728-739 | `transform: scaleX(0)`+`transform-origin`(:735-736) — **순수 transform**(width 애니메이션 아님, GPU 친화). z-index `calc(--z-header - 1)` 토큰 파생(raw z 0). pointer-events:none·순수 장식(텍스트 0). PASS |
| focus-visible | main.css:43-46 | `box-shadow: var(--focus-ring)`(토큰 단청 오프셋 링)·`--radius-sm`. outline:none 후 토큰 링 대체 — 키보드 피드백 유지. PASS |
| scroll-behavior | main.css:13·745 | `html{scroll-behavior:smooth}`(:13), reduce에서 `auto`(:745). PASS |
| @keyframes | grep+awk | 여전히 bg-drift×2만, transform/opacity. R2c는 신규 keyframe 0(전부 transition) |
| will-change | grep | 2(블롭·리빌 선언 ≤3). R2c 추가 0 |
| reduce 전수 | main.css:743-747 | bg-blob animation:none·html scroll auto·read-progress transition:none. + 토큰(--dur-*·--reveal-*·--lift-y 0). reduce 2·3·4 코드측 충족 — a11y 렌더 재감사 대기 |
| 토큰 단일성 | grep | hex 0·raw rgba 0 |
| 회귀 스크립트 | 재실행 | check_data_schema·check_links **exit 0** |
| 데이터 평면 | json mtime | 20:50 무변 |

### R2c 예산 (누적 (나) 기준 — R2c 흡수 후)
- 인터랙션 합계 **+13,571B (88% / 15,360)** — PASS, 여유 1,789B. R2c가 추가 증가 없이 들어옴(frontend 토큰 재사용 구현).
- 잔존: DEFERRED-RT(사진 hover)만. 사진 hover CSS는 소형(filter 토큰 전환 1블록)이라 1,789B 내 충분 예상.

### R2c 종합 — 전건 PASS
카드 리프트·링크·진행바·focus·smooth scroll·reduce 코드측 전건 통과. **D-3(`.person-card`)이 R2c 카드리프트 셀렉터(:695)에도 포함 확인** — `.person-card`가 reveal+lift 양쪽 셀렉터의 유령 컴포넌트(CSS 정의·JS 미방출). D-3 단일 결함으로 유지, frontend 회신 대기.

## 잔여 게이트 항목 (종합 전 미결)
1. **D-3 해소**(frontend: .person-card 렌더 추가 or 셀렉터 제거) → 재검증.
2. **DEFERRED-RT 사진 hover 6조건** — 구현 도착 시 코드 검사.
3. **a11y reduce 2·3·4 렌더 재감사**(리빌·카운트업·smooth scroll) — R2c 안정화 후 a11y와 동시.
4. **R-final gzip ≤200KB 페이지별 1회 실측**(team-lead 지시 안전판).
5. **frontend "안정화 완료" 통보 후 전 수치 1회 재고정** — 현 mtime 21:46~48 안정으로 보이나 명시 통보 대기.

## R2 안정화 재고정 + D-3 재검증 — 2026-06-06 (frontend 2·3차 완성 통보)

> frontend가 2·3차 완성 통보(사진 hover만 보류). 통보 신뢰 안 함 — 현 상태 전 수치 재고정·재검증.
> 재고정 시점 mtime: tokens 21:28·main.css 21:48·layout.js 21:48·home.js 21:48·**reveal.js 21:55(재변경)**. reveal.js만 D-3 대응으로 추가 수정됨.

### 재고정 전 항목 (현 상태, 재실행)
| 항목 | 결과 |
|---|---|
| 토큰 단일성 | 소비 css hex 0·raw rgba 0 |
| @keyframes | transform/opacity만(bg-drift×2) |
| will-change | 2 (≤3) |
| 모듈 회귀 | timeline.html is-pre-reveal 0·map 0(REVEAL_EXCLUDED 가드 동작), read-progress 정적 HTML 0(life JS 주입만) |
| 회귀 스크립트 | check_data_schema exit 0·check_links exit 0 |
| 데이터 평면 | timeline/network.json 20:50 무변 |
| 예산(인터랙션, (나)) | **+13,557B / 15,360 = 88.3% PASS** (여유 1,803B; reveal.js 2,484→2,470으로 축소) |
| 예산(tokens 별도) | +5,763B / 8,192 PASS |

### D-3 재검증 — reveal 측 RESOLVED, lift 잔여는 사전존재 dead CSS(INFO)
- **reveal.js:6 현재 셀렉터:** `.page-section, .card-grid > *, .gallery-grid > *, .archive-card, .quote-block` — **`.person-card` 제거됨**. frontend가 (나)방향(미사용 셀렉터 제거) 채택.
- 남은 5개 reveal 타깃 전부 LIVE: page-section(home·gallery), card-grid(home), gallery-grid(gallery), archive-card(archives), quote-block(page-render.js:128 `bq.className='quote-block'`). **죽은 reveal 타깃 0 → D-3 행동 결함 해소.**
- **잔여(INFO, 결함 아님):** `.person-card`가 카드리프트 셀렉터(main.css:695)·컴포넌트 정의(:332)에 남아있으나 어느 JS도 방출 안 함. 단 이는 **v1 사전존재 미사용 CSS** — people.js는 설계상 항상 `nw-` 관계망 그래프(people.json에 person-card 참조 0, 파일 docstring "관계망 그래프(nw-) 주입")이고 `.person-card`는 v1에서 쓰지 않은 카드 레이아웃 컴포넌트. v2가 이를 lift/reveal 셀렉터에 추가했을 뿐 → reveal 제거로 v2 도입분 정리 완료. lift 잔여는 무해 dead CSS(행동 영향 0, 페인트 영향 0)로, v2 표현계층 회귀 아님. 선택적 정리 권고(차단 아님).
- **판정: D-3 RESOLVED**(reveal 죽은 타깃 0). lift dead CSS는 INFO로 강등 — 게이트 차단 사유 아님.

### R2a/R2b/R2c 통과 확정 (재고정 후)
세 증분 품질 항목 전건 PASS 확정. D-2(예산) 해소·(나) 기준 88.3% PASS. D-3 RESOLVED. GATE-A 양면 잠금·GATE-B PASS.

## D-4 (R2 후속) — 사진 hover 적용 범위 §10.5↔렌더 불일치 [ESCALATED, ui-designer 결정 대기]

> 경위: frontend가 사진 hover 구현 직전 6조건 원문 요청 + 적용 범위 질문 제기. 6조건은 원문 전달 완료. 범위는 계약 결정 사안이라 §10.5 소유자(ui-designer) 회부.

**대조 증거:**
- design-system.md §10.5 매핑표(:656~): "사진 톤 복원"을 **3곳** 명시 — 홈 히어로 · people 인물 카드 · gallery 이미지 카드.
- 렌더 현실: gallery 이미지만 base `--img-filter` 보유(frontend가 인라인→`.figure-img` 클래스 v2.9로 전환 완료). people는 `nw-` 그래프 렌더(`.person-card` 미방출 — D-3 연계). 홈 히어로·page-render 이미지(life 등)는 base `--img-filter` 미적용(컬러 렌더).
- 충돌: (가) §10.5대로 3곳 = 히어로·people에 base 흑백 톤 부여 필요 → 휴지 톤 변경(표현 변화). (나) gallery만 우선 = Task #2 "표현 계층 최소 변경" 부합.
- **QA 판정: 범위는 QA가 정할 사안 아님(§10.5 소유 = ui-designer).** 회부 완료. 결정 후 그 범위 + 6조건으로 검사. **게이트 차단 아님**(사진 hover는 보류 모듈, 나머지 R2a/b/c는 통과) — 단 게이트 종합 전 결정·구현·6조건 검사 필요.

## 잔여 게이트 항목 (종합 전 미결 — 갱신)
1. ~~D-3~~ **RESOLVED** (reveal 죽은 타깃 0; lift dead CSS는 INFO).
2. **D-4 사진 hover 범위 결정**(ui-designer, §10.5 (가)/(나)) → 결정 후 구현.
3. **DEFERRED-RT 사진 hover 6조건** — 범위 결정·구현 도착 시 코드 검사(예산 여유 1,803B 충분).
4. **a11y reduce 2·3·4 렌더 재감사** — R2c 도착했으니 a11y 착수 가능, 결과 수신 대기.
5. **R-final gzip ≤200KB 페이지별 1회 실측**(team-lead 안전판) — 최종에 1회.
6. ~~안정화 통보 대기~~ — frontend 2·3차 완성 통보로 재고정 완료(reveal.js 21:55 반영).

## 결함 REV-1 (a11y 회부, QA 코드측 확증) — gallery 리빌 영구 숨김 [HIGH, OPEN, frontend 회부]

> 경위: a11y-engineer Stage-2/3 인간 모사 스크롤 실측에서 gallery `.image-card` 80개 중 **14개가 opacity:0 영구 잔류**(NORMAL·REDUCE 동일) 발견·회부. QA가 코드측 메커니즘 확증.

**심각도: HIGH** — 리빌 모듈의 핵심 약속("리빌 대상은 결국 보인다")이 gallery에서 깨짐. 콘텐츠 영구 시각 손실(14/80 = 17.5%).

**대조 증거 (a11y 렌더 ↔ QA 코드):**
- a11y 렌더: gallery 인간 스크롤 후 14개 `.image-card` opacity:0 영구. DOM엔 잔존(데이터 평면·콘솔 무영향 — **조용한 기능 실패**).
- QA 코드측 메커니즘 확증:
  - `.gallery-grid > *`가 reveal 타깃, `.is-pre-reveal`(opacity:0) 부여(reveal.js).
  - IO `threshold:0.08` + `rootMargin '0px 0px -8% 0px'`로 관찰, 발화 시 `unobserve`(1회).
  - `.image-card` 내부 이미지 `loading="lazy"`(gallery.js:38). 초기 레이아웃에서 lazy 이미지 높이 0/placeholder → 스크롤하며 이미지 로드 시 **그리드 하향 리플로우**.
  - lazy 리플로우 × IO unobserve-once 상호작용: 리플로우로 위치가 밀린 카드가 `isIntersecting` ≥8% 상태로 IO 콜백에 재진입하지 못하면 `is-revealed` 영구 미부여 → opacity:0 잔류. 에러 0(조용).

**왜 내 기존 게이트가 못 잡았나(반성성 — 체크리스트 갱신):**
- 내 R2b JS 폴백 검사는 **no-JS 케이스**(is-pre-reveal 기본 숨김 트랩 0)만 봤다. **JS는 도는데 리빌이 실패하는** 케이스(silent reveal failure)는 검사 항목에 없었다.
- 콘솔 에러 0·데이터 평면 무변으로는 구조적으로 안 잡힌다(둘 다 통과하면서 시각만 손실).
- **체크리스트 신규 항목:** "리빌 대상 모듈은 스크롤 완료 후 `가시(is-revealed 또는 미숨김) 카드 수 == 데이터/DOM 카드 수`를 검사한다 — 특히 `loading=lazy` 동반 그리드는 리플로우 후 잔류 검사 필수." (a11y가 렌더로, QA가 가능하면 코드/headless로 교차.)

**판정:** HIGH 결함, frontend 회부(a11y가 수정안 동봉). 수정 후 gallery 인간 스크롤 재실측(a11y) + 가시=DOM 카드 수 교차 확인. **게이트 종합 차단 항목** — REV-1 미해소 시 게이트 통과 불가.
**재현:** gallery.html 로드 → 끝까지 인간 모사 스크롤(lazy 로드 유발) → opacity:0 잔류 `.image-card` 수 카운트(a11y 실측 14).

## 잔여 게이트 항목 (종합 전 미결 — REV-1 추가로 갱신)
1. ~~D-3~~ RESOLVED. 2. **D-4 사진 hover 범위**(ui-designer 결정 대기). 3. **DEFERRED-RT 사진 hover 6조건**(범위·구현 후). 4. **REV-1 gallery 리빌 영구 숨김**(HIGH, frontend 수정 → a11y 재실측 + QA 가시=DOM 교차). 5. **a11y reduce 2·3·4** — 통과 수신(reduce 3·4·진행바·리빌 life/org PASS; gallery만 REV-1). 6. **R-final gzip ≤200KB**.

### a11y reduce 2·3·4 결과 수신 (a11y 정본, QA 참조)
- reduce 3(카운트업 home.js L41 if(reduce)return → 0 미경유 즉시 최종): PASS, 0 출현 0회.
- reduce 4(smooth scroll NORMAL=smooth/REDUCE=auto): PASS.
- 진행바(life only·aria-hidden·텍스트0·scaleX·grad): PASS. z-index=199(헤더 z-header 200 하·콘텐츠 위) — QA z-index 게이트 정본 확인 대상(아래).
- 리빌 reduce(life·organizations 영구숨김 0): PASS.
- **gallery 리빌만 REV-1**(상기).

## R-RT. 사진 hover 증분 (DEFERRED-RT 6조건) — 2026-06-06 21:58 도착

> 변경: main.css v2.9(.figure-img base filter + @media(hover:hover) hover 톤복원), gallery.js(인라인 filter 제거), reveal.js(D-3 .person-card 제거 — 21:55, 이미 검증). frontend "Task #2 전 항목 완료" 통보.

### 6조건 코드 검사 — 전건 PASS
| # | 조건 | 결과(main.css) |
|---|---|---|
| 1 | grayscale(0)/완전복원 0 | hover filter = `var(--img-filter-hover)`(0.65)만(:749). grayscale(0)·filter:none 0 |
| 2 | @media(hover:hover) 가드 | hover 톤복원 전 규칙이 `@media (hover:hover)` 블록 내(:745-750) |
| 3 | 비-hover 기본 = 흑백 통일 | `.figure-img{filter:var(--img-filter)}`(:744) |
| 4 | transition만(@keyframes 루프 0) | filter 전이 `transition`(:746), @keyframes filter 0 |
| 5 | will-change:filter 상시 0 | 0건 |
| 6 | 개별 :hover(그리드 일괄 0) | `.image-card:hover`·`.figure-img:hover` 개별, `.gallery-grid:hover` 0 |
- reduce: --dur-enter 0(토큰)으로 전이 없이 즉시 톤. PASS.
- **DEFERRED-RT 사진 hover: 코드 6조건 PASS.**

### 회귀(R-RT) — PASS
- 토큰 단일성 0, check_data_schema·check_links exit 0, 데이터 평면 무변. 예산 인터랙션 +14,174B(92.3%, 여유 1,186B) PASS.

### 단 — 게이트 차단 2건 미해소 (frontend "완료" 통보에 반함)

**[D-4 미확정] 사진 hover 범위 — frontend가 (가) 선구현, ui-designer 결정 미수신:**
- v2.9는 (가) 채택: `.figure-img{filter:var(--img-filter)}`를 **전 사진**에 부여 → gallery뿐 아니라 life·홈히어로·page-render 슬롯 이미지의 **휴지 톤이 컬러→흑백으로 변경**(표현 변화). frontend는 §5·§10.5·D-1 부합으로 판단하나, **D-4 범위 결정은 ui-designer 회부 중이고 아직 결정 미수신**.
- QA 판정: 6조건은 통과하나, **범위(가)/(나) 자체가 미확정인 채 (가)로 구현됨** — 휴지 톤 변경이라는 표현 결정을 QA가 사후 추인하지 않는다. ui-designer 결정으로 (가) 확정 시 R-RT 통과 확정, (나)면 frontend 범위 축소 회부.

**[REV-1 미해소 — HIGH, 게이트 차단]:**
- 이번 증분에서 **REV-1 미수정 확인**: reveal.js 21:55(D-3 후 무변, lazy/load/reobserve 처리 0), gallery.js 인라인 filter 제거만(reveal-exclude·load 핸들러·aspect-ratio 0), main.css `.image-card` aspect-ratio/min-height 0. → lazy 리플로우 × IO unobserve-once 근본 원인 그대로 → gallery 14/80 영구 숨김 존속.
- frontend "Task #2 전 항목 완료" 통보는 **부정확** — REV-1(HIGH) 미해소. 재통보.

## 게이트 종합 판정 (현재) — **보류 (PASS 아님)**
| 영역 | 상태 |
|---|---|
| R1 토큰 / R2a 배경·헤더 / R2b 리빌(코드) / R2c 카드·링크·진행바·smooth / R-RT 사진hover 6조건 | 품질 PASS |
| GATE-A 블롭겹침(양면) / GATE-B 유리blur / 토큰단일성 / @keyframes / will-change / 스크립트 exit0 / 데이터평면 / 예산 92.3% | PASS |
| D-1·D-1b·D-2·D-3 | RESOLVED |
| a11y reduce 2·3·4(gallery 외) / 진행바 z=199 | PASS |
| **REV-1 gallery 리빌 영구숨김** | **OPEN (HIGH, 차단)** |
| **D-4 사진hover 범위** | **미확정 (ui-designer 결정 대기)** |
| R-final gzip ≤200KB 페이지별 | 미실측 (REV-1·D-4 해소 후 최종 1회) |

**게이트 결론: 보류.** 품질·회귀·예산·접근성(reduce/대비/모션)은 전부 통과했으나, **REV-1(HIGH 차단)과 D-4(범위 미확정) 2건이 미결**이라 종합 통과 불가. 이 2건 해소 + R-final gzip 실측 후 통과 판정. Task #4 in_progress 유지.

## D-4 결정 수신 (ui-designer) — (가)변형 확정 + 구현 검사로 D-4-impl 결함 발견

> ui-designer 판정: base 흑백 톤(--img-filter)은 §5 **전역 의무**(전 콘텐츠 img — 미적용이 §5 결함), hover 복원(§10.1)은 그 위 선택 가치(gallery·히어로·인물사진만). people는 .person-card 미방출이라 사진 hover 비해당(§10.5 people 행 "조건부"로 정정). 검사 범위: (A) 전 콘텐츠 img에 base --img-filter 0누락, (B) hover는 gallery·히어로·(있으면)인물만·사료뷰어 원문 제외.

### (A) base 톤 전역 coverage — 실측: 충족 (ui-designer 우려는 기우)
- **모든 콘텐츠 img는 page-render.js `buildFigure`(:15 `image.className='figure-img'`) 또는 gallery.js(:39)로 렌더 → 전부 `.figure-img` 부착.** 히어로도 home.js:109가 `buildFigure` 사용(ui-designer가 우려한 "히어로 img에 figure-img 미부착"은 사실과 다름 — buildFigure 경유라 부착됨). life·archives 슬롯도 buildFigure. → base `--img-filter`(main.css:744) 전역 적용. **(A) 0누락 충족.**

### (B) hover 범위 — gallery만 동작, 히어로·life·archive는 inline filter가 hover 차단 [D-4-impl, MEDIUM]
- **대조 증거:** `buildFigure`(page-render.js:17)가 `image.style.filter='var(--img-filter)'` **인라인** 부여. 인라인 스타일은 명시도상 `@media(hover:hover) .home-hero-figure:hover .figure-img`(main.css:748)·`.figure-img:hover`(:749) CSS를 **무조건 이김**(!important 아니면) → **히어로·life·archive 이미지의 hover 톤복원이 발화 안 함**.
- gallery.js는 인라인 filter를 제거(:40 주석)해 hover가 동작하나, page-render.js buildFigure는 **인라인을 남겨둠** → 동일 inline-override 버그가 buildFigure 경유 이미지에 잔존.
- 영향: ui-designer가 (B)에서 의도한 **히어로 사진 hover 복원이 죽어 있음**(§10.5 히어로 "사진 톤 복원" 미발화). 단 base 톤은 정상(인라인=base=§5 충족) → **§5 위반 아님**, hover 선택가치 미발화라 MEDIUM.
- **수정:** buildFigure에서 `image.style.filter` 인라인 제거(gallery.js와 동일 처리). base 톤은 CSS `.figure-img{filter}`가 이미 부여하므로 휴지 톤 불변, hover 전이만 살아남. (사료뷰어 원문은 .image-card/.home-hero-figure 미해당이라 인라인 제거해도 hover 안 붙음 → (B) "사료 base만" 자동 충족.)
- **D-4 판정:** 범위 (가)변형 **확정**. (A) 충족. (B)는 D-4-impl(인라인 override) 수정 후 충족 — frontend 회부. **게이트 차단은 아님**(MEDIUM, hover 선택가치)이나 ui-designer 명시 의도(히어로 hover)라 종합 전 정리 권고.

## 게이트 종합 판정 (갱신) — **보류 유지**
- 차단: **REV-1(HIGH)** 미해소(이번 증분 미수정 확인).
- 정리 권고(차단 아님): **D-4-impl**(히어로/life hover 죽음 — 인라인 filter 제거 1줄).
- 미결: **R-final gzip** 실측(REV-1 수정 후 최종 1회).
- 통과 가능: REV-1 수정·재검(a11y 스크롤 + QA 가시=DOM 80) + D-4-impl 정리 + gzip 실측 → 종합 PASS. **Task #4 in_progress 유지.**

## R-FIX1. REV-1 + D-4-impl 수정 증분 — 2026-06-06 22:07~22:11 도착

> frontend가 REV-1(gallery 리빌 영구숨김) + D-4-impl(인라인 filter) 동시 수정. 검사 중에도 reveal.js 계속 변경(4298→5592, 22:09→22:11) — 수치는 22:11 스냅샷. ui-designer가 D-2 후속 정정(히어로 gap은 인코딩 탓 오판·인라인 filter가 실제 컷오프) 공유 — 내 D-4-impl 발견과 일치.

### REV-1 코드측 수정 확인 — 근본원인 해소 (단 런타임은 a11y 재실측 대기)
- reveal.js 3중 안전망 추가: ① rootMargin `0px 0px 64px 0px`+threshold 0(진입 선반응), ② 카드 내 img `load`/`error`에 `sweepInView`(lazy 리플로우 시 in-view 미리빌 재평가) + scroll/resize rAF 스윕 + 400/1200/3000ms 타임 스윕, ③ **6000ms 최종 강제 해제**(잔여 armed 카드 전부 is-revealed — "가시성 > 연출"). → lazy 리플로우 × IO unobserve-once로 영구 숨김되던 구조를 **6s 강제 해제로 원천 차단**. 폴백 체인 건전(no-JS→IO부재→IO→load스윕→scroll스윕→타임스윕→6s강제).
- **코드측 REV-1 근본 원인 해소 확인.** node --check OK.
- **★구조적 보장 증명(a11y 재실측과 독립 — Task #3 a11y completed로 인한 런타임 의존 위험 대비):** 코드 분석으로 영구숨김 불가를 증명:
  - `.is-pre-reveal`(opacity:0) 부여는 `arm()` 한 곳(reveal.js:39)에서만, 같은 호출에서 `armed.add(el)` → **숨겨진 카드는 반드시 armed 집합에 든다.**
  - 일찍 리빌된 카드는 `reveal()`이 `armed.delete` → armed에서 빠짐.
  - 6000ms `setTimeout`: `armed.forEach(el => el.classList.add('is-revealed'))` **무조건 실행**(forEach 앞 if-가드 없음) → 6초 시점 잔여 숨김 카드 전부 강제 가시.
  - **∴ 어떤 카드도 6초 넘게 opacity:0 잔류 불가** = REV-1 영구숨김(14/80) 실패모드 구조적 제거. (6초 내 off-screen 카드가 force-reveal 시 무애니로 뜨는 cosmetic edge는 있으나 영구숨김 결함과 무관.)
  - **판정: REV-1 코드측 RESOLVED(구조 증명).** a11y 런타임 재실측(80/80)은 확정 보강으로 받되, 게이트가 a11y 완료에 hard-depend 하지 않음. QA 가시=DOM 교차는 a11y 결과 도착 시 또는 자체 headless 시.

### D-4-impl 수정 확인 — PASS
- page-render.js buildFigure 인라인 `style.filter` **0건**(Python 검증). gallery·home도 0. base 톤은 CSS `.figure-img{filter}`(:744)가 부여(휴지 톤 불변), hover 전이가 더는 인라인에 안 막힘. → 히어로·life·archive hover 톤복원 활성. 사료뷰어는 hover 셀렉터 미매칭으로 base만(§10.5 B 충족).
- **DEFERRED-RT 6조건 재확인(ui-designer 권고 반영 — 인라인 잔존 false-pass 방지):** 인라인 0 확인 → CSS 6조건이 런타임 무력화 안 됨. (computed hover 전이 실측은 a11y headless에 위임 가능 — 인라인 0이면 CSS대로 grayscale(0.65) 전이.) 6조건 PASS 유지.

### ★ 신규 결함 [D-5] 예산 초과 — REV-1 안전망이 (나) 한도 돌파 [OPEN, 차단]
- **대조 증거(현 22:11 스냅샷, (나) 기준 raw):**

  | 자산 | R0 | 현재 | 델타 |
  |---|---|---|---|
  | main.css | 22,810 | 29,760 | +6,950 |
  | layout.js | 9,005 | 11,719 | +2,714 |
  | home.js | 7,059 | 9,099 | +2,040 |
  | reveal.js | 0 | 5,592 | +5,592 |
  | **인터랙션 합계** | — | — | **+17,296B = 112.6% / 15,360 → OVER +1,936B** |
- 원인: REV-1 3중 안전망이 reveal.js를 2,470→5,592(+3,122)로 키워 team-lead 비준 (나) 한도(15KB raw) 돌파. 앞서 R2b에서 "여유 1,789B뿐 — R2c·사진hover 잔존 초과 위험" 경고했던 예산 압박이 REV-1 수정으로 현실화.
- **QA 판정: 한도 초과 — 통과 불가(위험성향). 자의 면제 안 함.** 단 REV-1 수정은 HIGH 결함의 정당·필요 수정이라, 二者 택일이 아니라 (가)reveal.js 안전망 통합 감량 또는 (나)team-lead 한도 조정 중 결정 필요. frontend에 감량 1차 회부 + team-lead에 trade-off 보고(한도 flex 여부 판정).
- 감량 여지(참고): 안전망이 IO+load리스너+scroll스윕+3회 타임스윕+6s강제로 다중 — 6s 강제 해제(③)가 최종 보장이므로 ①②의 일부(예: 3회 타임스윕 축소, scroll 스윕과 타임 스윕 중복)는 통합 여지. 단 수정 방식은 frontend 재량.

### D-4 (가) 최종 확정 (ui-designer §5 소유자 결정) + hover 셀렉터 도달 정적 확인
- ui-designer 명시: (가)=전 사진 휴지 흑백 통일이 §5 의무, 미적용이 위반. R-RT 표현 추인은 §5 소유자(ui-designer) 권한 — QA석 추인 아님. (나) 후퇴 불필요. people .person-card 미방출 정상.
- **hover 셀렉터 도달 정적 확인(인라인 제거 후):** 히어로=home.js:103 `.home-hero-figure` → main.css:748 매칭. life 슬롯=`.image-figure` 내 `.figure-img` → main.css:749 `.figure-img:hover` 직접 매칭. gallery=`.image-card:hover`(:747). 인라인 filter 0이라 specificity override 없음 → CSS hover 규칙 정상 해석.
- **computed 런타임 실측(grayscale 0.65 실제 전이)은 a11y headless에 위임**(ui-designer false-pass 방지 권고 반영) — 인라인 0이 정적 확인됐으므로 CSS대로 전이되나, computed 확정은 a11y가 reduce 재감사 시 함께 실측. D-4 (가) 확정·R-RT 6조건 PASS(인라인 false-pass 위험 제거).

## 게이트 종합 판정 (갱신) — **보류 유지 (단일 hard 차단 = D-5)**
- ~~REV-1~~ **코드측 RESOLVED(구조 증명)** — 6s 강제 해제로 영구숨김 불가 증명. a11y 80/80 런타임은 확정 보강(게이트 hard-depend 아님). ~~D-4-impl~~ PASS. ~~D-4 범위~~ (가) **최종 확정**(ui-designer §5 결정).
- **단일 hard 차단: D-5 예산 초과(+1,936B, 112.6%)** — frontend 감량 or team-lead 한도 조정. **이 1건만 풀리면 종합 PASS 가능.**
- 보강 대기(차단 아님): a11y reduce 2·3·4 재돌림·computed hover 실측(a11y), QA 가시=DOM 80 교차.
- 미결(최종): R-final gzip ≤200KB 페이지별 1회 실측 — D-5 확정(파일 크기 결정) 후 실행.
- **Task #4 in_progress 유지.** D-5 해소 → (보강 수신) → gzip → 종합 PASS.

### INFO: page-render.js NULL 바이트 (도구 신뢰성 주의)
- page-render.js에 NULL 바이트(0x00) 6개 — renderInline PLACE 함수의 토큰 구분자(`` `\0${...}` ``). `file`이 "data"로 분류 → grep이 바이너리 취급해 매치를 조용히 누락(ui-designer 히어로 gap 오판·내 초기 grep 글리치의 공통 원인). **이 파일 검사는 grep -a 또는 Python/Read로.** 기능 결함은 아니나(런타임 정상) 토구 신뢰성·취약성(렌더 콘텐츠에 \0 유입 시 충돌) 관점 INFO — frontend 인지 권고.

## R-FINAL. 게이트 종합 판정 — **PASS** (2026-06-06)

### D-5 해소 (team-lead 판정)
- team-lead (나) 채택: 한도 raw **18KB로 1회 상향**(선례 기록 — "차단·중대 결함 수정 안전망은 승인 상향 가능", 스킬 §검증5 명문화). 감량은 선택 후속(게이트 제외, 1차 회부 철회).
- 그 후 frontend가 선택 감량까지 수행(reveal.js 5,592→4,253) → 인터랙션 **+15,097B**, 18KB는 물론 원 15KB 한도도 통과(여유 3,335B). **D-5 CLOSED.**

### R-final gzip ≤200KB 페이지별 실측 (team-lead 의무 조건) — 전 페이지 PASS
| 페이지 | gzip 첫로드(이미지 제외) | 판정 |
|---|---|---|
| index | 62.6K | OK |
| life | 72.1K | OK |
| gallery | 58.8K | OK |
| people | 77.1K | OK |
| archives | 84.0K | OK |
| references | 44.6K | OK |
| timeline | 148.7K | OK |
| map | 145.9K | OK |
- 전 8페이지 gzip 첫 로드 <200KB. 최대 timeline 148.7K·map 145.9K. raw는 JSON 지배로 크나(737K/727K) gzip 압축으로 예산 내 — team-lead D-5 근거(raw 초과≈gzip 미미) 실측 확인.

### 최종 consolidated 검증 (전 항목 재실행)
- check_data_schema exit 0 · check_links exit 0 · 토큰 단일성 0(소비 css hex/rgba) · @keyframes transform/opacity만 · will-change **2**(블롭·리빌; 사진hover는 will-change 미부여=조건5 준수) · 데이터 평면 20:50 무변 · 전 JS node --check OK · REV-1 6s 강제 해제 건재(reveal.js:92, 트림 후에도).

### 게이트 종합 판정표 — 전 항목 PASS
| 영역 | 판정 |
|---|---|
| R1 토큰 / R2a 배경·헤더 / R2b 리빌 / R2c 카드·링크·진행바·smooth / R-RT 사진hover 6조건 | **PASS** |
| GATE-A 블롭겹침(코드+렌더 양면, index+life) / GATE-B 유리blur | **PASS** |
| 토큰 단일성 / @keyframes transform·opacity / will-change ≤3 / 콘솔 회귀 / 데이터평면 무손상 / 각주·앵커 무손상 | **PASS** |
| 예산 인터랙션 +15,097B / 18KB(여유 3,335B) + gzip 페이지별 <200KB | **PASS** |
| D-1·D-1b·D-2·D-3·D-4·D-4-impl·D-5 | **RESOLVED** |
| REV-1 gallery 리빌 영구숨김 | **RESOLVED** (이중 확정: ① QA 코드 구조증명 6s 무조건 강제해제 → 영구숨김 불가, ② a11y 런타임 **82/82 카드 가시** — Task#3 완료보고, team-lead 교차 확인) |
| a11y(정본): GATE-A 렌더·reduce 1·3·4·진행바·리빌(life/org)·대비 | **PASS**(a11y_audit §4.x) |

### REV-1 이중 확정 (보강 수신 — 가시=DOM 교차 마감)
- a11y Task#3 완료보고에 REV-1 런타임 재실측 포함(team-lead 교차 확인): gallery **82/82 카드 가시**(영구숨김 0). 실제 카드 수 82(내 추정 80 정정 — 무관, 전수 가시).
- QA 코드 구조증명(6s 강제해제)과 a11y 런타임(82/82)이 **이중 확정** → "가시 카드 수=DOM 카드 수" 교차 항목 마감. REV-1 완전 종결.

### 잔여 보강(차단 아님)
- computed hover(히어로/life grayscale 0.65)·reduce 2 재돌림: 미수신 가능하나 사진hover는 인라인0+셀렉터 도달 정적 확인으로 통과 확정 — 판정 불변.
- 선택 후속(게이트 제외): reveal.js 추가 통합 감량(일부 수행 완료), page-render.js NULL 바이트(\0 토큰 구분자) 교체(INFO).
- 선택 후속(게이트 제외): reveal.js 추가 통합 감량(이미 일부 수행), page-render.js NULL 바이트(\0 토큰 구분자) 교체(INFO).

## ★ 게이트 결론: **PASS** — v2 라운드 종합 통과.
회귀 0 · 신규 결함 전건 해소(REV-1 HIGH 포함) · 예산 내(18KB 승인 한도, gzge 페이지별 <200KB) · 접근성(GATE-A 양면·reduce·대비) PASS. v2 표현 계층 변경이 데이터 평면·각주·앵커·모듈(timeline/map) 무손상으로 적용됨. Task #4 completed.

