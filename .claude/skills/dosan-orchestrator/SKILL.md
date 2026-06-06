---
name: dosan-orchestrator
description: 도산 안창호 일대기 조사·분석·웹사이트 제작의 전 과정을 지휘하는 마스터 오케스트레이터. "도산 웹사이트 만들어줘", "안창호 조사해줘", "도산 프로젝트 시작/계속/이어서", "조사 다시 해줘", "연표만 업데이트", "콘텐츠 보완", "사이트 수정", "QA 다시 돌려줘", "이전 결과 기반으로 개선" 등 도산 안창호 관련 조사·분석·콘텐츠·웹사이트 작업(초기 실행과 모든 후속·부분 재실행 포함)이 요청되면 반드시 이 스킬을 사용하라. 단, 도산에 대한 단순 지식 질문 1~2개는 직접 답해도 된다.
---

# 도산 안창호 하네스 오케스트레이터

도산 안창호(1878–1938)의 일대기를 전수 조사·검증하고 초상세 웹사이트(`site/`)를 만드는 30-에이전트 하네스의 지휘 스킬이다. 전체 설계의 단일 진실 공급원은 `.claude/harness-blueprint.md`이며, 의문이 생기면 청사진을 먼저 읽어라.

**실행 모드: 하이브리드** — Phase 1·5는 서브 에이전트 팬아웃, Phase 2·3·4a·4b는 에이전트 팀. 팀은 세션당 1개만 활성화되므로 Phase 경계마다 산출물을 파일로 고정한 뒤 팀을 해체(`TeamDelete`)하고 다음 팀을 생성한다.

**불변 규칙:**
- 모든 `Agent` 호출과 팀원 스폰에 `model: "opus"`를 명시한다. 하네스 품질은 추론 능력에 직결된다.
- 에이전트는 반드시 `.claude/agents/{name}.md`에 정의된 30개 중에서 호출한다. 즉석 역할 프롬프트로 대체하지 마라.
- 중간 산출물은 전부 `_workspace/`에 보존한다(감사 추적). 삭제 금지.
- 상충 데이터는 삭제하지 않고 출처를 병기한다. 검증 불가 주장은 D등급으로 보존하되 사이트에 노출하지 않는다.

## Phase 0: 컨텍스트 확인 (실행 모드 판별)

작업 시작 전 반드시 실행 상태를 판별하라:

1. `_workspace/` 미존재 → **초기 실행**. Phase 1부터 전체 파이프라인 실행.
2. `_workspace/` 존재 + 사용자가 부분 수정 요청(예: "연표만 다시", "사상 페이지 보완", "지도 수정") → **부분 재실행**. 아래 부분 재실행 매트릭스에 따라 해당 Phase·에이전트만 재호출. 하류 영향(예: 연표 변경 → 데이터 변환 → 연표 페이지 → QA)을 반드시 함께 실행.
3. `_workspace/` 존재 + 사용자가 전면 재실행/새 방향 요청 → **새 실행**. 기존 `_workspace/`를 `_workspace_prev/`로 이동 후 초기 실행과 동일하게 진행.
4. `_workspace/`는 있으나 `site/`가 없거나 미완 → **중단 재개**. 각 Phase 산출물 존재 여부로 마지막 완료 Phase를 판별하고 그 다음 Phase부터 재개.

**부분 재실행 매트릭스:**
| 요청 유형 | 재호출 에이전트 | 하류 필수 실행 |
|----------|----------------|---------------|
| 특정 시기 조사 보완 | 해당 연구원 + research-director | Phase 2 해당 부분 → 3 → 4 데이터 → QA |
| 연표 수정 | timeline-analyst | data-engineer → timeline-developer → qa-engineer |
| 관계망 수정 | relation-analyst | data-engineer → frontend(인물) → qa-engineer |
| 본문 콘텐츠 수정 | narrative-writer → copy-editor → citation-manager | data-engineer → frontend-developer → content-qa |
| 디자인 변경 | ui-designer | frontend-developer → a11y-engineer → qa-engineer |
| QA만 재실행 | content-qa, qa-engineer, performance-optimizer (병렬 서브) | 발견 결함의 수정 루프 |

## Phase 1: 조사 — 실행 모드: 서브 에이전트 팬아웃

1. `Agent(subagent_type: "research-director", model: "opus")` 호출 → 조사 매트릭스(`_workspace/00_director/matrix.md`) 작성.
2. 9개 연구원을 **한 메시지에서 병렬 호출** (`run_in_background: true`, 전원 `model: "opus"`): chronology-researcher, early-life-researcher, america-researcher, shinminhoe-researcher, provisional-gov-researcher, heungsadan-researcher, philosophy-researcher, network-researcher, primary-source-researcher. 각 프롬프트에 조사 매트릭스 경로와 출력 경로(`_workspace/01_research/{agent}_*`)를 명시.
3. 전원 완료 후 research-director 재호출 → 공백 맵(`gaps.md`) 작성. 공백·출처 누락률 >10% 영역이 있으면 해당 연구원에 보완 라운드 1회 지시.
4. **게이트:** 9개 연구원 산출 파일이 모두 존재하고 events.json이 파싱 가능해야 Phase 2 진입.

## Phase 2: 검증·분석 — 실행 모드: 에이전트 팀 (5명)

1. `TeamCreate` → 팀원: fact-checker, cross-validator, timeline-analyst, relation-analyst, synthesis-editor (전원 opus).
2. `TaskCreate`로 의존성 있는 작업 할당: 주장 등급화(fact-checker) → 상충 분석(cross-validator) ⇉ 연표 확정(timeline-analyst) · 관계망 확정(relation-analyst) → 통합 편집(synthesis-editor). 팀원 간 SendMessage로 상충 후보·채택 권고를 직접 교환하게 한다.
3. 산출: `claims_register.json`, `conflicts.md`, `timeline.json`, `network.json`, `synthesis/*.md`.
4. **게이트:** timeline.json·network.json 스키마 검증 통과(스크립트 실행) + synthesis 문서에 D등급 주장 0건. 통과 후 `TeamDelete`.

## Phase 3: 콘텐츠 — 실행 모드: 에이전트 팀 (5명)

1. `TeamCreate` → 팀원: content-architect, narrative-writer, copy-editor, citation-manager, visual-curator.
2. 흐름: content-architect가 sitemap·페이지 명세 작성 → narrative-writer 집필(`[ref:id]` 마커 의무) ⇉ visual-curator 이미지 수집 병행 → copy-editor 교열 → citation-manager 인용 매핑·무결성 검증.
3. 산출: `_workspace/03_content/` 전체 (pages/*.md, citations.json, images/manifest.json, sitemap.md).
4. **게이트:** 본문 마커↔citations.json 매핑 누락 0건 + 모든 이미지에 라이선스 메타데이터. 통과 후 `TeamDelete`.

## Phase 4a: 설계 — 실행 모드: 에이전트 팀 (3명)

1. `TeamCreate` → 팀원: web-architect, ui-designer, data-engineer.
2. 흐름: web-architect가 인터페이스 계약·파일 소유권 확정 → ui-designer가 디자인 시스템·토큰 CSS → data-engineer가 변환 스크립트로 `site/data/*.json` 생성(레코드 수·id 무결성 assert).
3. **게이트:** architecture.md에 4b 전 모듈의 계약 명시 + site/data/ 스키마 검증 통과. 통과 후 `TeamDelete`.

## Phase 4b: 구현 — 실행 모드: 에이전트 팀 (5명)

1. `TeamCreate` → 팀원: frontend-developer, timeline-developer, map-developer, a11y-engineer, qa-engineer.
2. 흐름: 세 개발자가 소유 파일 내에서 병렬 구현. **각 모듈 완성 직후** qa-engineer에 SendMessage로 QA 요청(incremental QA — 경계면 교차 비교), a11y-engineer는 페이지 단위 접근성 감사. 결함은 해당 개발자가 즉시 수정 후 재검증.
3. qa-engineer는 절대 읽기 전용으로 두지 마라 — 검증 스크립트(`check_links.py`, `check_data_schema.py`)를 직접 실행해야 한다.
4. **게이트:** 전 페이지 incremental QA 통과 + 콘솔 에러 0 + 끊어진 링크 0. 통과 후 `TeamDelete`.

## Phase 5: 최종 QA·종합 — 실행 모드: 서브 에이전트 병렬

1. 한 메시지에서 병렬 호출: content-qa(콘텐츠 전수 대조), performance-optimizer(성능 측정·최적화), qa-engineer(최종 통합 패스).
2. 결함 발견 시 수정 루프: 해당 작성자/개발자를 서브 호출로 재투입 → 수정 → 해당 QA만 재실행. 루프는 최대 3회, 이후 잔여 결함은 보고서에 명시하고 사용자 판단에 회부.
3. 완료 보고: 사이트 구조 요약, 페이지 목록, 데이터 통계(사건 수·인물 수·출처 수), 신뢰도 등급 분포, 알려진 한계(`gaps.md` 요약), 로컬 미리보기 방법(`python3 -m http.server -d site`).
4. **피드백 수집:** "결과에서 개선할 부분이 있나요? 에이전트 구성이나 워크플로우에 바꾸고 싶은 점이 있나요?" — 피드백은 하네스 진화 규칙(아래)에 따라 반영.

## 데이터 전달 프로토콜

- **파일 기반(주산출물):** `_workspace/{00_director,01_research,02_verified,03_content,04_build,05_qa}/`, 최종 산출물은 `site/`. 파일명 `{phase}_{agent}_{artifact}.{ext}` 또는 청사진 4절의 명시 경로.
- **태스크 기반(조율):** 팀 Phase에서 TaskCreate로 의존 관계 관리.
- **메시지 기반(실시간):** 팀원 간 SendMessage — 상충 회부, QA 요청, 결함 통보.
- **반환값 기반:** 서브 Phase에서 각 에이전트의 반환 요약을 게이트 판정에 사용.

## 에러 핸들링

| 상황 | 처리 |
|------|------|
| 에이전트 실패/무응답 | 1회 재시도 → 재실패 시 해당 산출 없이 진행하되 최종 보고서에 누락 명시 |
| 검색/외부 도구 실패 | 해당 에이전트가 1회 재시도 후 "소재 미확인"으로 기록하고 계속 |
| 산출 파일 스키마 불일치 | 생산 에이전트에 결함 목록과 함께 1회 재작업 지시, 재실패 시 data-engineer가 격리(D등급 분리) |
| 출처 간 상충 | 삭제 금지 — conflicts.md에 출처 병기, 채택 권고는 출처 위계 기준 |
| 팀원 교착(상호 대기) | 리더가 TaskList 확인 후 의존성 재정렬, 필요 시 작업을 직렬화 |
| Phase 게이트 불통과 | 원인 에이전트만 재투입(전체 재실행 금지), 2회 불통과 시 사용자에 보고 |

## 하네스 진화 규칙

매 실행 후 피드백을 다음 경로로 반영하고, 변경 시 `CLAUDE.md` 변경 이력과 `.claude/harness-blueprint.md`를 함께 갱신하라(청사진이 단일 진실 공급원이다):
- 결과물 품질 문제 → 해당 스킬 수정 | 역할 공백 → 에이전트 정의 수정/추가 | 순서 문제 → 본 스킬 수정 | 트리거 누락 → description 확장

## 테스트 시나리오

**정상 흐름 — 초기 전체 실행:**
"도산 안창호 일대기 웹사이트 만들어줘" → Phase 0에서 초기 실행 판별 → Phase 1 팬아웃(디렉터+9 연구원) → Phase 2 검증 팀 → Phase 3 콘텐츠 팀 → Phase 4a/4b → Phase 5 → `site/` 완성 + 완료 보고 + 피드백 요청. 기대: `_workspace/` 6개 하위 디렉토리와 `site/`가 모두 생성되고, 게이트 4개를 모두 통과.

**에러 흐름 — 연구원 1명 실패:**
Phase 1에서 america-researcher가 재시도 후에도 실패 → 나머지 8개 산출물로 Phase 2 진행, gaps.md와 최종 보고서에 "미주 활동 조사 누락" 명시 → 사용자에게 보완 라운드 제안. 기대: 파이프라인은 중단되지 않고, 누락이 침묵 속에 묻히지 않는다.

**부분 재실행 — "연표에 1907년 귀국 날짜가 틀렸어, 고쳐줘":**
Phase 0에서 부분 재실행 판별 → timeline-analyst 재호출(해당 사건 재검증) → data-engineer 변환 → timeline-developer 반영 → qa-engineer·content-qa 해당 부분 재검증. 기대: 전체 파이프라인을 다시 돌지 않는다.
