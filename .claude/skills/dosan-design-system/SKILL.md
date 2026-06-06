---
name: dosan-design-system
description: 도산 안창호 사이트 고유의 디자인 시스템 v2 — "맑은 한지, 살아 움직이는 먹" 컨셉. 한지·먹·단청 컬러 토큰(CSS 커스텀 프로퍼티), 모션·엘리베이션·라운딩 토큰, 애니메이션 배경 스펙, 마이크로 인터랙션·스크롤 리빌 패턴, 타이포 스케일, 컴포넌트 스펙, 사진 처리 톤, 반응형 브레이크포인트를 정의하는 스킬. ui-designer가 design-system.md와 tokens.css를 작성할 때, frontend-developer가 페이지를 스타일링·인터랙션 구현할 때, a11y-engineer가 색 대비·모션 접근성을 감사할 때 반드시 사용하라. "디자인 수정", "모던하게", "세련되게", "인터랙티브 요소", "애니메이션 배경", "마이크로 인터랙션", "색 바꿔", "토큰 업데이트", "타이포 보완", "대비 재검토" 같은 요청 시에도 이 스킬의 토큰·대비표·모션 규칙을 기준으로 작업하라. 임의 색상·임의 폰트·임의 애니메이션 도입 전에 반드시 이 스킬을 확인할 것.
---

# 도산 디자인 시스템 v2 (dosan-design-system)

도산 안창호 사이트의 시각 언어를 정의한다. v2 컨셉은 **"맑은 한지, 살아 움직이는 먹"** — 밝은 한지 바탕의 절제는 유지하되, 먹이 종이에 스며들 듯 부드럽게 움직이는 모던한 생동감을 더한다. v1의 "무실역행의 절제"가 정적 절제였다면, v2는 **절제된 움직임**이다: 화려함이 아니라 깊이(depth)·반응(response)·흐름(flow)으로 세련됨을 만든다. 이 스킬이 모든 색·글꼴·모션·컴포넌트의 단일 기준이며, 여기서 벗어난 임의 스타일은 시각적 일관성을 깨는 계약 위반이다.

**v2에서도 불변인 것 (협상 불가):** WCAG AA 대비, 등급 배지·disputed의 색 단독 의존 금지, `prefers-reduced-motion` 전면 대응, 성능 예산(첫 로드 <200KB 압축 전송), 검증 윤리의 시각화(불확실성을 분위기로 덮지 않는다), 밝은 색상 톤.

## 글로벌 frontend-design 스킬과의 관계

- **frontend-design:** 일반 품질 원칙 — 범용 AI 디자인 회피, 완성도, 창의적 폴리시. 그대로 따른다.
- **본 스킬:** 이 프로젝트 고유의 결정 — 컨셉, 토큰 값, 모션 규칙, 컴포넌트 스펙. 충돌 시 본 스킬이 우선한다.

## 1. 디자인 컨셉 — 맑은 한지, 살아 움직이는 먹

- **밝은 바탕은 정체성이다.** 한지 라이트 톤을 유지한다. 다크 모드 전환 금지(92% 흑백 사료 이미지의 시각 품질·장문 가독성·검증 정직성 사유 — v1 결정 승계).
- **움직임은 먹의 물성으로.** 애니메이션은 "먹이 번지고, 종이가 숨쉬는" 은유 안에서만 — 느리고(slow), 부드럽고(soft), 유기적(organic)이어야 한다. 기계적 바운스·네온 글로우·고채도 파티클은 이 사이트의 인격이 아니다.
- **깊이는 빛으로.** 그림자는 다층(soft multi-layer)으로 은은하게, 유리감(glassmorphism)은 밝은 반투명 + blur로 — 어두운 오버레이 금지.
- **반응은 즉각, 전환은 여유.** 마이크로 인터랙션(hover/focus)은 150~250ms로 즉각 반응하고, 장면 전환·리빌은 400~700ms로 여유 있게.
- **단청은 여전히 인장이다.** 강조색 남용 금지 원칙 유지 — 다만 v2는 단청의 **그라디언트 파생**(단청→노을)을 대형 표면(히어로 액센트·구분 장식)에 한해 허용한다. 텍스트에는 단색만.

## 2. 컬러 토큰 (v1 승계 + v2 확장)

`site/css/tokens.css` 기준. 모든 색은 토큰 참조로만.

```css
:root {
  /* — v1 승계 (값 불변 — 기존 대비표 유효) — */
  --paper:        #F7F3EB;  --paper-dim:    #EFE8DB;
  --ink:          #1A1815;  --ink-soft:     #4A453E;
  --dancheong:    #B5342B;  --celadon:      #6E8B74;
  --bg: var(--paper); --bg-raised: var(--paper-dim);
  --text: var(--ink); --text-muted: var(--ink-soft);
  --accent: var(--dancheong); --on-accent: #FFFFFF;

  /* — v2 확장: 표면·깊이 — */
  --paper-bright: #FDFBF7;            /* 카드 hover·유리 표면 베이스 */
  --glass:        rgba(253,251,247,.72); /* 유리 카드 — 반드시 backdrop-filter:blur(12px+)와 함께 */
  --glass-border: rgba(26,24,21,.08);
  --shadow-soft:  0 1px 2px rgba(26,24,21,.04), 0 4px 16px rgba(26,24,21,.06);
  --shadow-lift:  0 2px 4px rgba(26,24,21,.05), 0 12px 32px rgba(26,24,21,.10);

  /* — v2 확장: 그라디언트 (대형 표면·장식 전용, 텍스트 배경 금지) — */
  --grad-accent:  linear-gradient(135deg, #B5342B, #D4663A); /* 단청→노을 */
  --grad-wash:    radial-gradient(closest-side, rgba(110,139,116,.10), transparent); /* 청자 먹번짐 */
  --grad-wash-2:  radial-gradient(closest-side, rgba(181,52,43,.06), transparent);   /* 단청 먹번짐 */

  /* — v2 확장: 라운딩·모션 — */
  /* 주의: v1에 --radius-sm/md·--dur-fast/base/slow가 다른 값으로 이미 존재(불변 계약).
     이름 충돌을 피해 v2는 신규 이름을 쓴다 (ui-designer 채택, 2026-06-06). */
  --radius-soft: 8px; --radius-card: 14px; --radius-xl: 22px; --radius-pill: 999px;
  --dur-micro: 180ms; --dur-enter: 280ms; --dur-reveal: 600ms;
  --ease-out: cubic-bezier(.22,1,.36,1);      /* 리빌·등장 */
  --ease-soft: cubic-bezier(.45,.05,.55,.95); /* 배경·루프 */
}
```

### WCAG AA 대비표 (v1 표 전체 유효 — 추가 조합)

v1 대비표(ink/paper 16.0, dancheong/paper 5.4 등)는 값 불변이므로 그대로 유효하다. v2 추가 조합:

| 전경 / 배경 | 대비율 | 판정 | 용도 |
|---|---|---|---|
| `--ink` / `--paper-bright` | 16.6:1 | AAA | 유리 카드 본문 |
| `--ink` / `--glass`(블러 합성) | ≥14:1 | 통과 | 유리 표면 텍스트 — 단, 배경 애니메이션 위에서는 실측 필수 |
| `--dancheong` / `--paper-bright` | 5.6:1 | 통과 | 밝은 카드 링크 |
| 텍스트 / `--grad-accent` 위 | — | **금지** | 그라디언트 위 본문 텍스트 금지(장식·보더·아이콘만) |

- 새 조합은 실측 후 표에 추가. 애니메이션 배경 위 텍스트는 **배경의 가장 어두운 프레임 기준**으로 대비를 실측하라.

## 3. 애니메이션 배경 — "종이 위의 먹번짐"

전 페이지 공통 배경 레이어. 구현 규칙:

- **형태:** `--grad-wash`·`--grad-wash-2`의 대형 블롭 2~3개가 화면 뒤에서 80~140초 주기로 매우 느리게 표류(translate+scale). 먹이 한지에 스며드는 농담(濃淡)의 은유.
- **구현:** CSS-only(`@keyframes` + transform/opacity만). canvas·WebGL·JS rAF 금지 — 성능 예산과 단순성. `position:fixed; z-index:-1; pointer-events:none`.
- **강도 한계:** 블롭 불투명도 ≤0.10. 본문 영역 뒤에서는 텍스트 대비를 침식하지 않아야 한다(§2 실측 의무). 배경이 "보이는 듯 안 보이는" 수준이 정답 — 알아채는 순간 과한 것이다.
- **접근성:** `@media (prefers-reduced-motion: reduce)`에서 애니메이션 정지(정적 워시로 고정, 제거 아님 — 톤 유지). 깜빡임·고대비 플래시 절대 금지.
- **성능:** `will-change: transform` 블롭에만, 레이어 2~3개 한정. CPU 페인트 유발 속성(filter 애니메이션·box-shadow 애니메이션) 금지.

## 4. 인터랙션 패턴

### 4-1. 마이크로 인터랙션 (hover/focus — `--dur-micro`)
- **카드 리프트:** hover 시 `translateY(-3px)` + `--shadow-soft → --shadow-lift` + `--paper-bright` 표면. active 시 복귀.
- **링크:** 밑줄이 좌→우로 그려지는 애니메이션(background-size 기법). 색은 `--accent` 유지.
- **버튼·필터 칩:** hover 배경 전이 + `:focus-visible`에 2px `--accent` 오프셋 링(키보드 사용자에게 동일 품질의 피드백).
- **사진:** grayscale 통일 톤 유지하되, hover 시 `--dur-enter`로 grayscale(1)→grayscale(0.65) 부드러운 원톤 일부 복원 허용(원본 비변형·CSS만).

### 4-2. 스크롤 리빌 (`--dur-reveal`, `--ease-out`)
- IntersectionObserver로 섹션·카드에 `is-revealed` 클래스 토글 — fade + `translateY(16px)` 등장, 카드 그룹은 60~90ms 스태거.
- **1회만**: 재스크롤 시 재생 금지(독서 방해). observer는 once 처리.
- **JS 실패 폴백:** 리빌 대상은 기본 상태가 "보임"이어야 한다 — JS가 `is-pre-reveal`을 부여한 뒤 관찰하는 구조(no-JS에서 콘텐츠가 숨겨지면 안 된다).
- 홈 통계 숫자는 카운트업(0→값, 800ms) 허용 — `prefers-reduced-motion`에서는 즉시 최종값.

### 4-3. 내비게이션·구조
- 헤더: 스크롤 시 `--glass` + blur로 전환되는 스티키 헤더(높이 축소 전이 `--dur-enter`).
- 생애(life) 페이지: 상단 얇은 **읽기 진행 바**(`--grad-accent`, 3px) 허용 — 장문 독서 보조라는 의미가 있다.
- 페이지 내 앵커 이동은 `scroll-behavior: smooth`(reduced-motion 시 auto).

### 4-4. 모션 금지 목록
무한 회전·바운스 루프, 텍스트 글자 단위 애니메이션, 자동 재생 캐러셀, hover 없이 스스로 움직이는 카드, 100ms 미만 플래시. 이유: 독서 사이트의 주인공은 텍스트다 — 움직임이 시선을 텍스트에서 빼앗으면 실패다.

## 5. 타이포그래피 (v1 승계 + 위계 강화)

v1 스케일(--fs-sm~--fs-2xl, 1.25배)·세리프 본문·산세리프 UI·`--measure: 42rem`·행간 규칙 전부 승계. v2 추가:

- `--fs-hero: 3.052rem` — 홈 히어로 전용(데스크톱), 모바일에서는 `--fs-2xl`로 강등. 큰 위계 대비가 모던함의 핵심이다.
- 히어로·섹션 제목에 `letter-spacing: -0.02em` 허용(한글 대형 타이포의 시각 보정).
- 숫자 통계는 `font-variant-numeric: tabular-nums`(카운트업 시 흔들림 방지).

## 6. 컴포넌트 스펙 (v1 승계 + v2 표면 갱신)

- **연표 카드·인용 블록·사료 뷰어·인물 카드:** v1 구조 스펙 승계(disputed 단청 점선+라벨, 관계 유형 텍스트 라벨, 3단 사료 뷰어 등). 표면만 v2로: `--radius-card`, `--shadow-soft`, hover 리프트.
- **등급 배지(A/B/C):** 라벨 텍스트 병기 불변. `--radius-pill`, 톤은 기존 등급색 유지.
- **유리 카드(`--glass`):** 애니메이션 배경 위에 뜨는 패널(스티키 헤더·필터 바·지도 컨트롤)에만 사용 — 본문 장문 컨테이너에는 쓰지 않는다(blur 비용·가독성).
- **히어로(홈):** 풀블리드 사진 금지 유지(저해상 제약). 대신 타이포 중심 히어로 + `--grad-accent` 장식 획(붓질 모티프) + 배경 먹번짐 — 사진은 프레임형 보조.

## 7. 사진 처리·반응형 (v1 전면 승계)

흑백 통일 톤(CSS filter)·figcaption 캡션/크레딧 의무·alt 전수·모바일 우선 브레이크포인트(640/1024)·`--measure` 본문 폭·3뷰포트 검증 — v1 규칙 그대로. hover 원톤 복원(§4-1)만 추가.

## 산출물 검증

1. **토큰 단일성:** `site/css/` 전체 하드코딩 hex grep — tokens.css 외 0건(rgba 그림자·유리 토큰도 tokens.css에 정의).
2. **대비 검증:** 사용 조합 전수가 §2 대비표(v1+v2)에 있고 통과하는지. 애니메이션 배경 위 텍스트는 가장 불리한 프레임으로 실측.
3. **모션 접근성:** `prefers-reduced-motion: reduce`에서 배경 정지·리빌 즉시 표시·카운트업 즉시·smooth scroll 해제를 전수 확인.
4. **JS 폴백:** JS 비활성 상태에서 모든 콘텐츠 가시(리빌 숨김 0건), 배경은 CSS-only라 그대로 동작.
5. **성능:** 애니메이션은 transform/opacity만(DevTools 페인트 플래시 0). 예산 기준(D-2·D-5 판정, 2026-06-06): **구현 자산(인터랙션·배경 CSS/JS, 토큰 정의 제외) raw ≤15KB** + 토큰 정의 자산 별도 ≤8KB. 단 **차단·중대 결함 수정에 필요한 안전망 코드는 team-lead 승인으로 한도 상향 가능**(v2 실행에서 REV-1 수정으로 18KB 승인 선례) — 이 경우 페이지별 gzip 전송 200KB 예산 재확인이 의무다. 측정은 압축 전(raw) byte.
6. **절제 확인:** 한 화면에 동시 재생 모션 3종 이하(배경 제외), 단청 강조 3곳 이하 — 모던함은 양이 아니라 질이다.
7. **문서-코드 동기화:** design-system.md ↔ tokens.css 값 일치 대조.
