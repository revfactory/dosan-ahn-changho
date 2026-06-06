# DOSAN — 도산 안창호 일대기 프로젝트

## 하네스: 도산 안창호 조사·웹사이트

**목표:** 도산 안창호(1878–1938) 일대기 전수 조사·검증·분석 후 초상세 정적 웹사이트(`site/`) 제작.

**트리거:** 도산 안창호 관련 조사·분석·콘텐츠·웹사이트 작업(초기 실행, 재실행, 부분 수정, QA, 보완 포함) 요청 시 `dosan-orchestrator` 스킬을 사용하라. 단순 지식 질문은 직접 응답 가능.

**설계 문서:** 하네스 구조 전체(30 에이전트 × Role·Trait Vector·Policy, 14 스킬, Phase 파이프라인)는 `.claude/harness-blueprint.md`가 단일 진실 공급원이다. 에이전트/스킬을 수정할 때는 청사진을 함께 갱신하라.

## 하네스: 도산 안창호 소설

**목표:** 검증 DB(`_workspace/02_verified/`)를 사실 원천으로 한 대사 중심 장편소설(20~24장, 전 생애) 제작 — 유추·창작 허용, 전부 사실-허구 대장(ledger)에 기록.

**트리거:** 도산 소설 창작·수정·퇴고 작업("소설 써줘", "N장 다시", "대사 수정", "퇴고", "작가의 말") 시 `dosan-novel-orchestrator` 스킬을 사용하라. 웹사이트·조사 작업은 `dosan-orchestrator` 소관이다.

**변경 이력:**
| 날짜 | 변경 내용 | 대상 | 사유 |
|------|----------|------|------|
| 2026-06-06 | 초기 구성 (에이전트 30, 스킬 14, 오케스트레이터) | 전체 | - |
| 2026-06-06 | 디자인 시스템 v2 개정 — "맑은 한지, 살아 움직이는 먹": 모션·엘리베이션·라운딩 토큰, 애니메이션 배경(먹번짐), 마이크로 인터랙션·스크롤 리빌 패턴 추가. 밝은 톤·WCAG AA·motion-reduce·성능 예산은 불변 계약 | skills/dosan-design-system | 사용자 요청: 모던·세련 디자인, 인터랙티브 요소, 애니메이션 배경, 밝은 톤 유지 |
| 2026-06-06 | v2 실행 중 스킬 정밀화 3건 — 토큰명 v1 충돌 회피(radius-soft/card/xl·dur-micro/enter/reveal), 예산 기준 명문화(구현 자산 raw ≤15KB·토큰 별도 ≤8KB·결함 수정 안전망은 승인 상향 가능·gzip 페이지 예산 재확인 의무) | skills/dosan-design-system | 실행 중 판정 D-1·D-2·D-5 — 계약 모호성이 QA 보류를 유발한 교훈 반영 |
| 2026-06-07 | 소설 하네스 신설 — 에이전트 5(novel-director·voice-keeper·scene-writer·fiction-fact-keeper·literary-editor), 스킬 3(dosan-novel-style·fact-fiction-ledger·dosan-novel-orchestrator). 장편 20~24장·전 생애·대사 중심, 검증 DB 사실 원천 + 유추 대장 | agents 5종·skills 3종 | 사용자 요청: 대사 중심 소설, 검증 사실 기반 + 유추 허용 |
| 2026-06-07 | 디자인 v2.4 — 스크롤 방해 수정: 헤더 레이아웃 전이 금지·리빌 선발동(≥30%)·모션 절제(320ms/10px/40ms) | skills/dosan-design-system, site | 사용자 피드백: 스크롤을 방해하는 애니메이션 |
| 2026-06-07 | 디자인 v2.5 — 스크롤 리빌 전면 폐기·smooth scroll 제거(reveal.js 삭제). 콘텐츠 즉시 표시 원칙 명문화 | skills/dosan-design-system, site | 동일 피드백 2회 — 절제 조정 불충분, 진화 트리거 발동 |
