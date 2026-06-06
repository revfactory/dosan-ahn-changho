# 페이지 명세 10 — 참고문헌 (references.html)

> v1.0 (2026-06-06) / 전제: 00_common.md. **citation-manager의 1차 작업 명세** — 인용 일람의 데이터 구조는 citation-style 스킬이 소유한다.

## 목적
전 페이지 각주([ref:])의 종착점이자 검증 방법론의 공개 지면. "이 사이트는 무엇을 근거로, 어떤 기준으로 썼는가"에 대한 완결 답변.

## 데이터 소스
- 인용 일람: citation-manager가 작성하는 `citations.json` (claims_register.json 305건 + primary-source_catalog.json 47건 + synthesis 인용 학술 문헌에서 도출 — 출처 ID 체계 src-{유형}-{일련번호}, citation-style 스킬 준수)
- 방법론 본문: `synthesis/life.md` 편집 원칙, `conflicts.md` 머리말·통계, `synthesis/excluded.md` 운영 규칙, fact-verification 스킬의 등급 기준 요지

## 섹션 구조

| 절 | 앵커 | 내용 | 분량(자) |
|----|------|------|---------|
| 1 | #methodology | **검증 방법론** — 주장 단위 검증·독립 출처 2개 원칙·등급 기준(A/B/C/D 정의와 분포 9/155/89/52)·상충 처리 3형식(채택/병기/분리)·D등급 비노출 원칙·공백 공개 원칙 | 800–1,300 |
| 2 | #grades | 등급별 본문 문형 안내 — "단정형은 A·B", "'전해진다'는 C", "각주의 '기록이 갈린다'는 미해소 상충" (독자용 읽기 안내) | 400–700 |
| 3 | #citations | **인용 일람** (데이터 렌더) — 유형별 그룹: 1차 사료 / 학술 논저 / 기관 DB·사전 / 신문·잡지 / 단체 기록 / 웹. **각 항목 앵커 = citations.json `sources[].id`** (`src-{pri|aca|ins|enc|web}-{NNN}` — citation-manager의 references_page.md가 source 단위 앵커 194건을 깐다) | 데이터 렌더 |
| 4 | #colophon | 제작 정보 — 데이터 규모(주장 305·사건 172 중 수록 165·관계 135·사료 47), 버전, 입력 동결일 | 150–300 |

narrative-writer 분량: §1·2·4 = 1,200–2,000자. §3은 citation-manager 데이터.

## 집필·구성 규칙
- §1은 fact-verification 절차의 **독자용 요약**이다 — 내부 파일명(claims_register.json 등)이 아니라 개념(주장 대장·상충 대장)으로 서술.
- 독립성 경고(민백 다항목·동일 저자·단일 전승 사슬·단체 기록)는 archives #reliability가 소유 — 여기서는 링크만.
- 인용 항목 표기 형식(사료/논문/단행본/웹별)은 citation-style 스킬 §표기 형식을 따른다 — 본 명세는 형식을 재정의하지 않는다.
- 전 페이지 마커의 해석 경로: 최종 마커 `[ref:ref-NNN]`(`refs[].id`) → refs에서 `source_id` 조회 → §3의 `#src-…` 앵커 (00_common §3 마커 수명주기 참조). 매핑 무결성(끊어진 마커 0)은 citation-manager의 validate_citations.py + Phase 5 content-qa가 이중 검사.

## 이미지 슬롯
없음.

## 교차링크
- #methodology → `archives.html#reliability`(독립성 경고), `archives.html#unlocated`(미확인 사료), `archives.html#excluded-traditions`(채택하지 않은 전승), `philosophy.html#sec-8`(어록 검증)
- #citations 1차 사료 항목 → `archives.html#src-pri-...` (해당 사료 카드)
- 전 페이지 푸터 → #methodology (sitemap §2)

## 완성 기준
- citations.json `sources[]` 전 항목 렌더, 항목 앵커 = `sources[].id` 100%
- 전 사이트 [ref:] 마커의 해석 실패(끊어진 인용) 0건
- 등급 분포 수치가 claims_register.json과 일치
- §1에 D등급 비노출 원칙·공백 공개 원칙 명시 존재
