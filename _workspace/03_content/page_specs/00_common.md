# 공통 명세 — 전 페이지 적용 규칙 (00_common)

> v1.0 (2026-06-06) / content-architect. 모든 페이지 명세(01~10)는 본 문서를 전제한다. 개별 명세와 충돌하면 개별 명세가 우선한다.

## 1. 데이터 소스 — 단일 진실 공급원

| 소스 | 경로 | 용도 |
|------|------|------|
| 생애 서사 | `_workspace/02_verified/synthesis/life.md` (v1.3) | life·home 본문의 사실 원천 |
| 조직 | `_workspace/02_verified/synthesis/organizations.md` (v1.1) | organizations 본문 |
| 사상 | `_workspace/02_verified/synthesis/philosophy.md` (v1.1) | philosophy 본문 |
| 인물 | `_workspace/02_verified/synthesis/people.md` (v1.3) | people 본문 |
| 사료 | `_workspace/02_verified/synthesis/sources.md` (v1.1) | archives 본문 |
| 제외 목록 | `_workspace/02_verified/synthesis/excluded.md` (v1.0) | 전 페이지 노출 금지 검사 + archives "채택하지 않은 전승" |
| 연표 | `_workspace/02_verified/timeline.json` (172건) | timeline·map·생애 장 골격 |
| 관계망 | `_workspace/02_verified/network.json` (v1.2.1, 노드 81·엣지 135·미확정 19) | people·organizations 앵커와 데이터 |
| 주장 대장 | `_workspace/02_verified/claims_register.json` (305건) | 인용 매핑(citation-manager)·등급 확인 |
| 상충 대장 | `_workspace/02_verified/conflicts.md` (66건) | disputed 각주 문안의 원천 |
| 사료 카탈로그 | `_workspace/01_research/primary-source_catalog.json` (47건) | archives 카드·소재 상태 |

**규칙: 본문의 모든 사실은 위 소스에서만 온다.** 작성자의 기억·외부 검색으로 사실을 보충하지 않는다. synthesis에 없는 사실이 필요하면 content-architect에게 질의(명세 결함)하거나 해당 내용 없이 작성한다.

## 2. 신뢰도 등급 표시 규칙 (집필·교열 공통)

| 등급 | 본문 문형 | 사이트 표시 |
|------|----------|------------|
| A·B | 단정 평서형 | 일반 본문 + [ref:] 각주 |
| C | "~로 전해진다 / ~라고 전한다 / 기록이 갈린다" 한정 문형 **유지 의무** | 일반 본문 + [ref:] 각주 (한정 문형 자체가 표시다) |
| D | **전면 사용 금지** (excluded.md 운영 규칙 ①) | archives "채택하지 않은 전승"에서 메타 주장(clm-0282~0285) 경유만 |
| disputed | conflicts.md 권고 형식 (a)통설 채택+각주 / (b)양론 병기 / (c)양립·분리 | 각주 또는 dispute_note 동반 의무 |

- synthesis 문장을 옮길 때 **한정 문형과 각주를 절대 단정형으로 윤문하지 않는다** — copy-editor의 1순위 검사 항목.
- 날짜 정밀도는 timeline.json의 precision을 초과 표기하지 않는다 (range는 range로, 연 단위는 연 단위로).
- 필수 각주 2건(synthesis가 "필수"로 지정): cfl-012 중앙총회장 판정 경위, cfl-029 가출옥 오기 판정. 해당 대목 인용 시 각주 생략 불가.
- 한정 인용 표기(원문 그대로 유지 — **비망라 골격**): "안도산전서 수록본에 따름", "전재본 기준", "차리석의 1942년 체계화에 따르면", "이광수 전기에 기록되어 있다", "일제 공판 기록에 따르면", "흥사단 전승 어록" 등. **망라 목록과 적용 규칙은 copy-editor의 `_workspace/03_content/style_guide.md` R0.4가 소유한다** — 집필 시 R0.4를 기준으로 하라. ※ 표기에는 synthesis 원형 변형이 있다(예: "흥사단 전승 어록"의 드래프트 자구는 synthesis 원형 "흥사단 어록·전기류 전승" — 둘 다 synthesis 자체에 등장하는 적법 변형). **QA·교열 검색식은 일반 명칭이 아니라 R0.4의 변형 포함 망라 목록으로 매칭하라** — 일반 명칭 단독 매칭은 누락 오탐을 낳는다.

## 3. 인용 마커 [ref:]

- 모든 사실 문장 끝에 `[ref:{id}]` ≥1. id는 synthesis의 근거 식별자(clm-/evt-/src-pri-/cfl-)를 그대로 쓴다.
- synthesis에서 문장을 가져올 때 그 문장에 달린 식별자를 **전부 승계**한다 — 누락은 content-qa 결함.
- **예외 — 편집 메타 서술 (패턴 3종, 2026-06-06 확장 — citation-manager 실집필 검출 14건 근거)**: 사이트·검증 체계 자신에 대한 기술은 도산에 대한 사실 주장이 아니므로 [ref:] 의무에서 제외한다. 구판의 "4곳 한정" 열거는 명세 자신이 정의한 앵커(#org-gaps·#people-gaps 등)보다 좁았던 결함 — 다음 3패턴으로 대체한다.
  - **(i) 앵커 화이트리스트**: `*-intro`·`*-gaps` 패턴 전체(**무접두 `intro` 포함** — 구판 archives #intro 흡수, 검사기 구현과 일치) + 명명 4종(`methodology`·`grades`·`citations`·`colophon`) + 각 페이지 도입문(H1 직후~첫 섹션 전 구역). 패턴 확장의 통제는 아래 예약 앵커명 규칙이 담당 — 신규 `*-intro`/`*-gaps` 앵커는 명세 개정 없이 만들 수 없다.
  - **(ii) 섹션 안내문**: 해당 섹션의 표시 규약·이용법·수록 기준만 기술하는 첫 문단. **단 안내문이라도 도산-사실(인명·날짜·사건·조직)을 포함하면 마커 의무** — "표시 규약 설명"과 "사실 서술"의 경계는 §3 단서가 가른다.
  - **(iii) 데이터 집계 자기 서술**: 사이트 자신의 데이터 규모 수치(사건 165/172, 인물 59·조직 22, 주장 305, 등급 분포 A 9/B 155 등)는 [ref:] 정박 대상이 아니다 — 근거가 외부 출처가 아니라 사이트 자신의 JSON이고, 자기 인용(claims_register를 출처 등재)은 순환이라 금지. 검증 경로는 content-qa의 **데이터 정합 검사**(수치 ↔ 데이터 파일 메타 전수 대조)다. 01_home "수치는 데이터 파일 메타에서만" 조항과 연동.
  - **공통 단서 (불변)**: 메타 서술 안에서도 개별 정박이 가능한 도산-사실(예: 공보 결호 28개호 → clm-0281, 1973 도산공원 합장 → clm-0234)은 마커 의무 유지. 검사 출력은 [META] 재분류하되 유지 — 사람 판별 원칙 불변. 이 예외는 citation-manager 무결성 검사·content-qa 게이트와 공유된 규칙이다.
- **예약 앵커명 — 재사용 금지 (패턴 연동 개정)**: `*-intro`·`*-gaps` **패턴 전체**와 명명 4종(`methodology`·`grades`·`citations`·`colophon`)은 메타 예외 전용 예약이다. 일반 사실 섹션의 앵커로 쓰지 마라 — validate_citations.py가 패턴 매칭으로 [META] 분류하므로, 재사용하면 사실 섹션이 마커 검사에서 빠진다. 신규 섹션 앵커는 명세의 앵커 표 또는 `sec-N` 형식만 사용하며, 새 `*-intro`/`*-gaps` 앵커 신설은 명세 개정 사항이다.
- **마커 수명주기 — 2단계 (citation-manager 합의 확정)**: ① **집필·교열 단계** — 위 잠정 마커(clm-/evt-/src-pri-/cfl-)를 쓴다(본 문서의 모든 [ref:] 규칙은 이 단계 기준). ② **정규화 단계** — 페이지별 교열 완료 후 citation-manager의 normalize_markers.py가 잠정 마커를 최종 형태 `[ref:ref-NNN]`(citations.json `refs[].id`)으로 기계 치환한다. **Phase 4 렌더러의 입력은 ref-NNN 마커다.** 작성자·교열자는 ref-NNN을 수기로 만들지 않는다 — 정규화는 citation-manager 도구 전담이며, 작성자는 매핑을 추측하지 않는다.
- citations.json은 2층 구조다 — `refs[]`(마커 대상: 출처+인용 위치)와 `sources[]`(서지 원장, id 형식 `src-{pri|aca|ins|enc|web}-{NNN}` 5종). 렌더 경로: `[ref:ref-NNN]` → refs에서 source_id 조회 → `references.html#src-…` 앵커. 스키마 상세는 citation-style 스킬 소유.

## 4. 표기·어조 (historical-writing 스킬 준수)

- 호칭: "안창호" 기본, 문맥상 "도산" 허용. 존칭(선생) 금지.
- 인명 표기는 network.json `name_normalization`(293 별칭), 지명은 timeline.json `meta.place_normalization` 기준.
- 금지: 평가 형용사(위대·탁월·불멸), 서사 수사(마침내·드디어), 내면 묘사(느꼈다·결심했다), 작가 추정(했을 것이다).
- 갈등·실패는 성취와 동일 비중·동일 어조 (우상화 금지).
- 두괄식: 모든 장·절의 첫 문장이 해당 단위의 핵심 사실을 요약한다.

## 5. 시기 체계 (8대 시기 P1–P8)

sitemap.md §3의 표가 기준이다. 시기 명칭·연대 경계를 페이지마다 다르게 쓰지 않는다.

## 6. 앵커·교차링크

- 앵커 형식은 sitemap.md §4. 데이터 id를 변형하지 않는다.
- 초고 단계 교차링크 표기: `[표시 텍스트](페이지.html#앵커)` markdown 링크. data-engineer가 변환 시 보존한다.
- 명세에 정의된 링크만 구현 — 임의 추가는 명세 개정 요청을 거친다.

## 7. 이미지 슬롯 공통 규칙 (visual-curator)

- 슬롯 id: `img-{page}-{NN}` (예: img-life-04). 명세의 슬롯 표 = 수집 범위 산정의 기준.
- **필수 슬롯**은 빈 채로 출시 불가 — 수집 실패 시 content-architect에 통지해 명세 수정(슬롯 강등·대체)을 받는다. **권장 슬롯**은 미충족 허용.
- 전 이미지 visual-sourcing 스킬 판별 절차(퍼블릭 도메인/자유 라이선스 검증) 통과 후 manifest 등재. 연출 사진·AI 생성 이미지 금지.
- 사진이 존재하지 않는 연대(1878–1902 유년·수학기)는 **장소·문서·신문 지면 이미지로 대체**한다 — 인물 사진을 무리하게 찾지 않는다.
- 캡션 필수 4요소: ① 한 줄 사실 캡션(무엇·언제·어디 — 단정은 검증 가능 범위만) ② 연대 ③ 출처·소장처 ④ 라이선스. 캡션의 사실 주장도 content-qa 대조 대상 — 검증 불가 단정(예: "최초의" 강주장) 금지.
- 동일 이미지의 다중 페이지 사용 허용 (manifest에 사용 페이지 목록 기록 — gallery 역링크의 원천).

## 8. 완성 기준 — 전 페이지 공통 게이트 (정량)

1. D등급 주장·사건·어록 노출 **0건** (excluded.md 전수 대조)
2. C등급 문장 한정 문형 동반 **100%**
3. 사실 문장 [ref:] 마커 부착 **100%** (§3 편집 메타 서술 예외 — 패턴 3종 — 제외. 집계 수치는 content-qa 데이터 정합 검사로 대체)
4. disputed 인용 개소 각주 동반 **100%**
5. 분량 가이드 **±20%** 이내
6. 명세 정의 교차링크 충족률 **100%**, 끊어진 앵커 0
7. 금지 표현·존칭 검색 결과 **0건**
8. 필수 이미지 슬롯 충족 100% (또는 명세 개정 합의 기록 존재)

## 9. 질의 프로토콜

명세로 판단이 안 서는 지점은 추측하지 말고 content-architect에게 SendMessage로 질의한다. 답변과 동시에 해당 명세를 보강한다 — 반복 질의는 명세 결함이다.
