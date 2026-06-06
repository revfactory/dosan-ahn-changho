---
name: dosan-novel-orchestrator
description: 도산 안창호 장편소설(대사 중심·검증 사실 기반·유추 허용) 제작의 전 과정을 지휘하는 소설 오케스트레이터. "도산 소설 써줘", "소설 작업 시작/계속/이어서", "N장 다시 써줘", "장면 수정", "대사 고쳐줘", "인물 목소리 바꿔", "다음 부 진행", "소설 퇴고", "작가의 말 갱신", "이전 원고 기반으로 개선" 등 도산 소설 관련 창작·수정·퇴고 작업(초기 실행과 모든 후속·부분 재실행 포함)이 요청되면 반드시 이 스킬을 사용하라. 웹사이트·조사 작업에는 dosan-orchestrator를 쓰고 이 스킬을 쓰지 마라.
---

# 도산 소설 오케스트레이터 (dosan-novel-orchestrator)

도산 안창호 장편소설을 제작하는 5-에이전트 하네스의 지휘 스킬이다. **확정 사양: 장편 20~24장 + 서장·종장, 전 생애(1878~1938), 대사 중심(장면의 60%+), 검증 사실 기반 + 유추 허용(전부 ledger 기록).**

**실행 모드: 하이브리드** — N1·N2는 서브 에이전트, N3·N4는 에이전트 팀(세션당 1팀 — dosan-orchestrator 팀과 동시 가동 금지).

**불변 규칙:**
- 모든 에이전트 호출에 `model: "opus"` 명시.
- 사실 기반: `_workspace/02_verified/`(timeline 172·network·claims 305·synthesis·conflicts)가 유일한 사실 원천이다. 에이전트가 새 역사 사실을 웹 검색으로 추가하지 않는다 — 부족하면 dosan-orchestrator의 조사 보완으로 회부.
- 모든 장면은 fact-fiction-ledger 스킬의 scene_ledger.json에 기록 — 대장 없는 장면은 존재할 수 없다.
- 산출 디렉토리: `novel/` (outline.md, characters/voices.md, chapters/ch{NN}.md, ledger/scene_ledger.json, afterword.md). 중간 산출물은 `novel/_workshop/`.

## Phase N0: 컨텍스트 확인

1. `novel/` 미존재 → **초기 실행** (N1부터).
2. `novel/` 존재 + 부분 수정 요청("N장 다시", "대사 수정", "장면 추가") → **부분 재실행**: 해당 장의 scene-writer 재투입 → fiction-fact-keeper 해당 장 재검 → voice-keeper 대사 감수 → literary-editor 해당 장 퇴고 → ledger·afterword 갱신.
3. `novel/` 존재 + 전면 재구상 → outline 단계(N1)부터, 기존을 `novel/_prev/`로 이동.
4. 중단 재개 → chapters/ 마지막 완성 장 다음부터 N3 재개.

## Phase N1: 작품 설계 — 서브 (novel-director)

1. `Agent(novel-director, opus)` — dosan-novel-style·fact-fiction-ledger 스킬 + 검증 DB 정독 후:
   - `novel/outline.md`: 제목 후보, 컨셉 진술(주제·정조), 부 구성(전 생애 → 4~5부), 장 목록(20~24장 + 서장·종장 — 장별: 시기·핵심 사건 앵커(evt id)·등장 인물·갈등·시점), 모티프 설계, 장당 분량.
   - 시점 전략(3인칭 도산 밀착 + 타 시점 장 지정), 1차 사실 앵커 검증(존재하는 evt id인지).
2. **게이트:** 전 장에 사실 앵커·갈등·시점 명시 + 확정 공백 구간 활용 계획 명시.

## Phase N2: 인물 목소리 바이블 — 서브 (voice-keeper)

1. `Agent(voice-keeper, opus)` — outline의 등장 인물 전원(주요 12~18명)의 목소리 시트를 `novel/characters/voices.md`로 작성. 도산은 연설문·서한·신문조서 원문(philosophy.md·sources.md·카탈로그)에 정박. 호칭 관계표(시기별 변화 포함) 작성.
2. **게이트:** 주요 인물 전원 시트 + 근거 출전 명시 + 호칭표 완성.

## Phase N3: 집필 — 팀 (4명: scene-writer-a, scene-writer-b, fiction-fact-keeper, voice-keeper)

1. `TeamCreate(dosan-novel)` — scene-writer 2명이 **부 단위로 분담**(a: 1·3부…, b: 2·4부… — 인접 부를 서로 다른 작가가 쓰지 않게 교차 배치 금지, 부 단위 연속성 우선). 각자 dosan-novel-style + outline + voices를 절대 기준으로 집필.
2. **장 단위 incremental 검증:** 장 탈고 즉시 ① fiction-fact-keeper에 SendMessage(원고+장면 대장) → 반사실 검사·대장 확정, ② voice-keeper에 대사 감수 요청 → 시트 위반 회부. 결함은 작가가 즉시 수정 후 재검.
3. 작가 간 경계 동기화: 부 경계 장(이어지는 장)은 선행 부 작가가 마지막 장 요약+감정 상태를 SendMessage로 인계.
4. **게이트:** 전 장 keeper PASS(verified=true) + voice 위반 0 + 대사 비율 ≥60%.

## Phase N4: 퇴고·통합 — 팀 재구성 (literary-editor + fiction-fact-keeper)

1. N3 팀 해체 → `TeamCreate(dosan-novel-polish)` — literary-editor가 전권 퇴고: 문체 통일(두 작가의 결 맞춤), 리듬, 장 전환, 모티프 일관성, 제목 확정. 수정이 사실 평면을 건드리면 keeper 재검(해당 장만).
2. keeper가 ledger 최종 전수 검증 → `novel/afterword.md`(작가의 말 — ledger 집계 기반 사실/각색/창작 공개) 생성.
3. **게이트:** dosan-novel-style 산출물 검증 6항 전부 + ledger 전 장면 verified + afterword 수치 일치.

## Phase N5: 완료 보고

장 수·총 분량·대사 비율, 사실 앵커 수·유추/창작 요소 수·채택 전승 목록, 작가의 말 요약, 파일 위치. 피드백 질문(장면·인물·문체 방향).

## 데이터 전달

파일 기반(novel/ + _workshop/) + 팀 Phase는 태스크·메시지 병용. 장 원고 파일명 `chapters/ch{NN}.md`(서장 ch00, 종장 ch99).

## 에러 핸들링

| 상황 | 처리 |
|------|------|
| keeper 반사실 차단 | 작가 수정 의무 — 우회 금지. 3회 반복 시 novel-director 재소환(장면 설계 자체 결함) |
| 작가 간 문체 격차 | N4에서 literary-editor가 통일 — N3에서 막지 않는다(속도 우선) |
| 검증 DB에 없는 사실 필요 | 창작(ledger 기록)으로 해결 가능하면 창작, 역사 사실이 꼭 필요하면 사용자에게 조사 보완 제안 |
| 장 분량 미달/초과 ±40% | literary-editor가 N4에서 조정 지시 |

## 테스트 시나리오

**정상:** "도산 소설 써줘" → N0 초기 판별 → N1 outline(24장) → N2 voices(15명) → N3 집필+검증 루프 → N4 퇴고+작가의 말 → novel/ 완성 보고.
**부분:** "7장 국민대표회의 장면, 신채호 대사를 더 날카롭게" → N0 부분 판별 → scene-writer 해당 장만 재집필(voices의 신채호 시트 범위 내) → keeper·voice 재검 → editor 해당 장 퇴고 → ledger 갱신. 전체 재실행 없음.
**차단:** 작가가 1924년 상하이에서 도산-이승만 대면 장면 작성 → keeper가 시공간 위반(도산 미주 체류) 차단 → 장면을 서신 교환으로 재설계 또는 시기 이동.
