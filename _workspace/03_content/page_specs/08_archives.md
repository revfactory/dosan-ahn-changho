# 페이지 명세 08 — 사료 (archives.html)

> v1.0 (2026-06-06) / 전제: 00_common.md

## 목적
이 사이트의 서술이 **무엇 위에 서 있는가**를 공개한다 — 1차 사료 47건의 카탈로그, 사료 비판(일제 기록·단체 기록·전기류의 한계), 소재 미확인 목록, 그리고 검증 미달로 채택하지 않은 전승. 연구자 여정(J2)의 종착점이자 사이트 신뢰성의 근거 페이지.

## 데이터 소스
- 사료 카드: `_workspace/01_research/primary-source_catalog.json` 47건 — 소비 필드: id, title, type, author, date_created, language, holder, access_url, location_status, transcription, criticism, related_event_ids, notes
- 본문: `synthesis/sources.md` §1–10 (유일 사실 원천)
- 채택하지 않은 전승: `synthesis/excluded.md` (메타 주장 clm-0282~0285 경유분만)

## 섹션 구조

| 절 | 앵커 | 내용 | 원천 | 분량(자) |
|----|------|------|------|---------|
| 1 | #intro | 도입 — 사료 지형 개관 + A등급 9건 희소 정직 공개 | sources §머리말·§10 | 300–500 |
| 2 | #catalog | **사료 카탈로그 47건** — 유형별 그룹 카드 (일기 1/서한 4/연설 4/신문 9/일제 기록 8/단체 기록 6/기타 15) + location_status 배지(confirmed/cited_only/unlocated) | catalog.json | 데이터 렌더 (카드 자체는 집필 불요) |
| 3 | #criticism | 사료 비판 — 도산일기 대필 가능성, 일제 기록 내적 비판(직인용 금지 사유), 흥사단 기록 가중 검증, 전기류 단일 전승 사슬 | sources §1·5·6·7 | 1,200–1,600 |
| 4 | #unlocated | 소재 미확인 사료 — sources §8 표 18건 그대로 ("소재 미확인도 정보다" + 막혀 있는 판정 열 포함) | sources §8 | 표 + 머리말 200–300 |
| 5 | #reliability | 출처 신뢰성 평가 — 독립성 경고 4건 + 기관 오류 사례 2건(가출옥 오기·1912 중앙총회장 기각) | sources §9 | 600–900 |
| 6 | #excluded-traditions | **채택하지 않은 전승** — 이토 회견설(clm-0282)·도산 내각설(clm-0283)·호 유래 양설(clm-0284)·오렌지 일화(clm-0285) 4건. "~라는 일화가 후대 기록에 전해지나 동시대 사료에서 확인되지 않는다" 메타 문형 한정 | excluded.md 메타 주장 | 700–1,000 |
| 7 | #archives-gaps | 공백과 한계 (USC KADA 접근 실패, 공보 결호 28개호 등) | sources §10 | 300–500 |

총 3,500–5,500자 + 데이터 렌더.

## 집필 규칙 (archives 특화 — 협상 불가)
- **#excluded-traditions는 메타 주장 4건(B등급) 경유 서술만** 허용 — 객체 주장(D)의 내용을 사실 문형으로 풀어 쓰지 않는다. 어록류 D(임종 어록 등)는 이 섹션에서도 **다루지 않는다** (전면 노출 금지 — 디렉터 지시 승계; 어록 제외 사실의 고지는 philosophy #sec-8이 소유).
- 이토 회견·도산 내각 두 전승은 **별개 전승으로 분리 서술** (병합 시 시간 모순 — life.md §6 경고 승계).
- 사료 카드의 title·holder·access_url은 catalog.json 원문 그대로 (재작성 금지).
- 일제 기록 절에서 신문조서 진술 내용 직인용 0건 — "널리 유통되는 옥중 문답"도 원본 대조 전(src-pri-017 cited_only)이므로 자구 인용 금지.

## 이미지 슬롯
| 슬롯 | 위치 | 주제 | 권장 연대 | 구분 |
|------|------|------|----------|------|
| img-arc-01 | #criticism | 도산일기 실물 (표지·내지 — 독립기념관 소장, 국가등록문화재) | 1920–21 | **필수** |
| img-arc-02 | #catalog | 집조(여권) 실물 (img-life-04 재사용 허용) | 1902 | **필수** |
| img-arc-03 | #catalog | 105인 사건 공판시말서 또는 동시대 신문 지면 | 1913 | 권장 |
| img-arc-04 | #catalog | 수형기록카드 (img-life-13 재사용 허용) | 1937 | **필수** |
| img-arc-05 | #catalog | 신한민보·독립신문·동광 지면 중 1 (타 페이지 재사용 허용) | 1909–1926 | 권장 |

필수 3 (전부 재사용 허용 — 신규 수집 부담 최소) / 권장 2.

## 교차링크
- 사료 카드 related_event_ids → `timeline.html#evt-...` 전건
- #criticism 각 사료 → 카드 앵커(#src-pri-XXX) 상호 링크
- #reliability 오류 사례 → `life.html#ch-08`(중앙총회장)·`#ch-13`(가출옥)
- #excluded-traditions → `life.html#ch-06`(이토·내각 전승의 시기 맥락), `philosophy.html#sec-8`(어록)
- 서지 → `references.html#...` (citation-manager 매핑 후)

## 완성 기준
- 사료 카드 47건 전수 렌더, location_status 배지 3종 표시 100%
- #unlocated 표 18건 = sources.md §8과 일치
- #excluded-traditions 메타 문형 위반 0건 (D 객체 주장의 사실 서술 0)
- 신문조서 진술 직인용 0건
