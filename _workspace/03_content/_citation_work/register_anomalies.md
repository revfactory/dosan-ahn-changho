# claims_register.json 이상 기록 (Phase 5 content-qa 인계)

- 관리: citation-manager (19)
- 기준: claims_register.json (2026-06-06 17:08 판) — team-lead 지시: 원천 수정 금지, 기록만
- 소비자: content-qa (29) — 전수 대조 시 아래 항목을 결함으로 재검출해도 신규 결함이 아님

## A-1. clm-0271 — sources 배열이 주장 내용과 무관

- 주장: 『도산안창호전집』(2000) 전14권 권별 구성 (1–3권 시문·서한 / 4권 일기 / …)
- 이상: `sources`에 「국가유산청 국가등록문화유산 '도산 안창호 일기'」 1건만 등재 — 전집 구성과 무관한 출처. `grade_reason`은 "src-pri-026 confirmed — 전집 권별 구성은 직접 확인"으로 정상 근거를 명시.
- 추정 원인: sources 배열 작성 시 인접 claim(clm-0157 계열, 도산일기 문화재 등록)의 출처 복사 오류.
- 인용 체계 처리: grade_reason 보충 매핑으로 clm-0271 → src-pri-026 연결 완료 (claim_source_map.json). 각주 동작에는 영향 없음.
- 권고: content-qa가 clm-0271 인용 개소 검수 시 src-pri-026(전집) 기준으로 대조할 것.

## 배경 패턴 (참고 — 결함 아님)

grade_reason에 사료 카탈로그 id를 인용하면서 sources 배열에는 누락한 claim이 33건
(특히 '소재 미확인' 메타 주장 — clm-0267~0270 등). 검증자가 사료 대조 근거를
grade_reason에만 기록한 패턴으로, 전량 보충 매핑(`사료 카탈로그 참조(grade_reason)`
locator)으로 흡수했다. 명백한 출처-주장 불일치는 위 A-1 1건뿐이다.

## 변경 이력

| 일자 | 내용 |
|------|------|
| 2026-06-06 | 목록 신설 — A-1(clm-0271) 등재, team-lead 지시 |
