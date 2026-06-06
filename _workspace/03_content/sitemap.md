# 사이트맵·정보구조 (IA) — 도산 안창호 일대기 사이트

> **상태: 확정·동결 v1.0 (2026-06-06, team-lead 승인) / 작성: content-architect (16)**
> 10페이지 구성(organizations.html 추가)과 핵심 결정 5건(D등급 데이터 평면 차단·앵커=데이터 id 무변형 포함) team-lead 승인 완료 — 후자 2건은 Phase 4·5 계약으로 승계된다. 증분 개정은 잔여 조건부 재판정(cfl-018·032·041·052, network 대기 P-1·P-2) 도착 시에만 §10 절차로 수행한다.
> 입력(전부 동결본 기준): `_workspace/02_verified/synthesis/` 6종(life v1.3 · organizations v1.1 · philosophy v1.2〔구 v1.1 — 잔존 evt id 정정만, 내용 불변〕 · people v1.3 · sources v1.1 · excluded v1.0), `timeline.json`(172건, disputed 17, D등급 7), `network.json`(v1.2.1-phase2, 노드 81=인물 59+조직 22, 엣지 135, 미확정 19), `claims_register.json`(305건, A9/B155/C89/D52), `conflicts.md`(66건), `_workspace/01_research/primary-source_catalog.json`(47건).
> 본 문서는 Phase 3 콘텐츠 팀(narrative-writer·copy-editor·citation-manager·visual-curator)의 합의 문서다. 페이지별 상세 요구는 `page_specs/*.md`가 소유하며, 본 문서와 명세가 어긋나면 명세가 우선하고 본 문서를 즉시 개정한다.
> **변경 절차:** 명세 변경 시 변경 사유·영향 페이지를 본 문서 말미 변경 이력에 기록하고 narrative-writer·visual-curator에게 SendMessage로 즉시 통지한다. 조용한 명세 변경 금지.

## 1. 페이지 위계 — 10페이지 구성

`site-architecture` 스킬의 표준 9페이지에 **organizations.html(조직) 1페이지를 추가**한 10페이지 구성이다.

```
site/
├── index.html            홈 — 도입 서사·탐색 허브·검증 통계
├── life.html             생애 — 15개 시기 장 + 공백과 한계
├── timeline.html         연표 — 인터랙티브 (렌더 165건 = 172 − D등급 7)
├── map.html              활동 지도 — 좌표 보유 117건 내외(D 제외 후 확정) + 이동 경로
├── organizations.html    조직 — 도산이 세우고 이끈 결사 10절 (org-001~022 앵커)
├── philosophy.html       사상 — 7개 주제 + 어록 검증표
├── people.html           인물 — 관계망 그래프 + 시기별 서사 + 미확정 목록
├── archives.html         사료 — 카탈로그 47건 + 사료 비판 + 소재 미확인 + 채택하지 않은 전승
├── gallery.html          갤러리 — 사이트 전체 이미지 매니페스트 뷰
└── references.html       참고문헌 — 인용 일람 + 검증 방법론·등급 체계
```

**추가 근거 (위험성향 4 — 분량 근거 적시):** organizations.md는 21KB·10개 결사 절의 독립 synthesis 문서로, 각각 페이지를 받는 philosophy.md(15KB)·people.md(19KB)와 동급 분량이다. life.html에 합치면 단일 페이지 60KB+가 되어 시간 축 서사(life 소유)와 조직 구조 서술(organizations 소유)의 문서 소유권 구분이 깨지고, network.json의 조직 노드 22건이 앵커 목적지를 잃는다. 팀 리더 과업 지시문의 "synthesis 분량과 데이터 구조에 맞게 조정·확장 가능" 승인에 근거한다. (전역 내비 10항목의 모바일 처리 우려는 ui-designer 소관으로 이관 — Phase 4 전달 사항.)

## 2. 전역 내비게이션

- 순서: **홈 · 생애 · 연표 · 지도 · 조직 · 사상 · 인물 · 사료 · 갤러리 · 참고문헌** (10항목 전부 상시 노출)
- 마크업은 공통 모듈(layout.js 또는 include 패턴) 한 곳에서만 정의 — 페이지별 복붙 금지 (site-architecture §3). 구현은 Phase 4 frontend-developer 소관이나, 콘텐츠 평면의 요구로서 모든 페이지 푸터에 참고문헌·사료 링크와 "검증 방법론" 링크(`references.html#methodology`)를 둔다.
- 페이지 골격 공통: 공통 헤더(사이트명+전역 내비) → 페이지 헤더(h1 + 한 줄 소개) → 본문 섹션들 → 공통 푸터.

## 3. 시기 체계 (전 페이지 공통 — 8대 시기)

생애 15장을 묶은 상위 8구간. life.html의 부(部) 구분, timeline.html의 시기 필터, gallery.html의 시기 분류, map.html의 시기 슬라이더가 **모두 이 하나의 체계**를 쓴다 (교차링크 정합의 기준).

| 코드 | 시기 | 연대 | life 장 |
|------|------|------|---------|
| P1 | 성장과 수학 | 1878–1899 | 1–3장 |
| P2 | 결혼과 1차 미주 | 1899–1907 | 4–5장 |
| P3 | 신민회와 망명 | 1907–1911 | 6–7장 |
| P4 | 2차 미주 — 국민회와 흥사단 | 1911–1919 | 8장 |
| P5 | 임시정부와 모색 | 1919–1924 | 9–10장 |
| P6 | 재방문과 대독립당 | 1924–1932 | 11–12장 |
| P7 | 수감과 순국 | 1932–1938 | 13–14장 |
| P8 | 사후 | 1938–1973 | 15장 |

## 4. 앵커 ID 체계 (교차링크의 좌표)

| 대상 | 앵커 형식 | 정의처 | 예 |
|------|----------|--------|-----|
| 생애 장 | `life.html#ch-{01..15}`, `#ch-gaps`(공백과 한계) | 02_life.md | `life.html#ch-06` |
| 연표 사건 | `timeline.html#{evt-id}` (timeline.json id 그대로) | 03_timeline.md | `timeline.html#evt-shin-005` |
| 조직 | `organizations.html#{org-id}` (org-001~022) | 05_organizations.md §앵커 매핑표 | `organizations.html#org-013` |
| 인물 | `people.html#{per-id}` (per-001~059) | 07_people.md | `people.html#per-005` |
| 사료 | `archives.html#{src-pri-id}` | 08_archives.md | `archives.html#src-pri-001` |
| 사상 절 | `philosophy.html#sec-{1..9}` | 06_philosophy.md | `philosophy.html#sec-7` |
| 인용 | `references.html#{source-id}` — citations.json `sources[].id`, 형식 `src-{pri\|aca\|ins\|enc\|web}-{NNN}` 5종. 본문 최종 마커는 `[ref:ref-NNN]`(`refs[].id`)이며 refs→source_id 경유로 이 앵커에 닿는다 (00_common §3 수명주기) | citation-style 스킬 | `references.html#src-aca-001` |
| 갤러리 이미지 | `gallery.html#{img-id}` (visual-curator manifest 키) | 09_gallery.md | — |

- 앵커 id는 데이터 파일의 id를 **변형 없이** 쓴다 — 변형하면 QA의 경계면 교차 비교가 끊긴다.
- 명세에 정의된 교차링크만 구현한다 (site-architecture §3). 임의 추가 링크는 명세 개정을 거친다.

## 5. 교차링크 체계 (페이지 간 — 명세 정의분)

| 출발 → 도착 | 규칙 | 정의처 |
|------------|------|--------|
| home → 전 페이지 | 탐색 카드 9장 + 통계 박스 → 연표·참고문헌 | 01_home.md |
| life → timeline | 장별 골격 사건 앵커 링크 각 장 ≥1 | 02_life.md |
| life → organizations / people / philosophy | 조직·인물 첫 등장 시 1회 링크, 사상 주제 언급 시 해당 절 링크 | 02_life.md |
| timeline → life / map | 사건 카드에 소속 시기 장 링크 + 좌표 보유 사건 "지도에서 보기" | 03_timeline.md |
| timeline → people / organizations | 사건 카드 actors·orgs를 앵커 링크로 | 03_timeline.md |
| map → timeline | 마커 팝업 → 사건 앵커 | 04_map.md |
| organizations → life / philosophy / people / timeline | 시간 맥락·강령 사상·구성 인물·근거 사건 | 05_organizations.md |
| philosophy → life / organizations / archives | 사건 전거·강령 문서·사료 층위(한정 인용의 근거) | 06_philosophy.md |
| people → timeline / life / organizations | 관계의 근거 사건(evidence_event_ids) ≥1 / 시기 장 / 소속 조직 | 07_people.md |
| archives → timeline / references | related_event_ids → 사건 앵커, 서지 → 인용 항목 | 08_archives.md |
| gallery → 사용 페이지 | 이미지 카드에 "이 이미지가 쓰인 페이지" 역링크 의무 | 09_gallery.md |
| 전 페이지 → references | 본문 [ref:] 각주 → 인용 앵커 (citation-manager 매핑) | 00_common.md |

## 6. 신뢰도 등급·disputed 표시 정책 (사이트 전역 — 협상 불가)

excluded.md 운영 규칙과 content-accuracy-qa 검사 기준을 사이트 평면으로 옮긴 것이다. 상세 문형은 `page_specs/00_common.md`.

1. **D등급(주장 52건·연표 사건 7건) 노출 0건** — 본문·연표·지도·관계망·캡션 어디에도 쓸 수 없다. 유일 예외: archives.html "채택하지 않은 전승" 섹션에서 **메타 주장(clm-0282~0285, B등급) 경유** 서술만 허용.
2. **C등급은 한정 문형 의무** — "~로 전해진다 / 기록이 갈린다" 문형을 그대로 유지. 단정형으로 윤문 금지 (copy-editor 검사 항목).
3. **disputed 사건 17건은 표시 의무** — 연표·본문에서 인용 시 dispute_note(또는 synthesis 각주)를 동반 노출.
4. **모든 사실 문장에 [ref:] 마커 ≥1** — 마커 없는 사실 문장은 content-qa에서 결함 처리된다.
5. **금지 표현** — 평가 형용사(위대·탁월·불멸), 서사 수사(마침내), 내면 묘사, 작가 추정, 존칭(선생). synthesis 자기 감사와 동일 기준.

## 7. 사용자 여정 3종과 IA 충족 (설계 검증 기준)

**J1. 처음 방문자 (일반 대중)** — "안창호가 누구인지 30분 안에 입체적으로 알고 싶다."
경로: 홈(도입 서사+통계) → 생애(8부 15장 순독 또는 시기 점프) → 장 내 이미지·연표 앵커로 심화 → 갤러리.
충족 장치: 홈의 한 단락 도입+시기 카드, 생애 각 장 첫 문단 두괄식 요약, 장별 이미지 슬롯, 푸터의 다음 장 이동.

**J2. 연구자** — "특정 사실의 전거와 검증 상태를 확인하고 싶다. 예: 신민회 결성 시점."
경로: 연표 검색/필터 → 사건 카드(날짜 정밀도·confidence·disputed·출처) → 각주 → 참고문헌 항목 → 사료 페이지(원문 소재 상태·unlocated 목록).
충족 장치: 사건 카드의 등급·dispute_note 상시 노출, 사료 카탈로그 47건+소재 미확인 표 18건, references의 등급 방법론·독립성 경고 4건 공개.

**J3. 학생 (학습·과제)** — "사상 요약, 인물 관계, 활동 무대를 빠르게 정리하고 싶다. 유명 어록을 인용하고 싶다."
경로: 사상(7주제 구조 요약) → 인물(그래프+관계 서사) → 지도(활동 무대 시각화) → 어록 검증표.
충족 장치: 사상 페이지의 어록 검증표(인용 가능 2건 / 전승 1건 / 출전 미확인 노출 금지 목록 — "왜 유명 어록이 없는가"를 교육 콘텐츠로 전환), 인물 페이지의 갈등 관계 동등 서술, 지도의 시기 필터.

## 8. 워크스루 결과 (v1.0 확정 전 자체 점검 — 반성성 8)

여정 3종으로 IA 초안을 도상 워크스루한 결과 발견·수정한 결함 4건:

| # | 발견 | 수정 |
|---|------|------|
| 1 | 갤러리 이미지가 막다른 경로 — 맥락(어느 시기·어느 페이지)으로 돌아갈 길이 없었다 | 이미지 카드에 시기 코드(P1–P8)와 사용 페이지 역링크 의무화 (09_gallery.md) |
| 2 | timeline → map 단방향 누락 — 지도에서 연표로는 가는데 역방향이 없었다 | 좌표 보유 사건(117건) 카드에 "지도에서 보기" 링크 추가 (03_timeline.md) |
| 3 | J3에서 어록을 찾는 학생이 D등급 어록("낙망은 청년의 죽음" 등)을 사이트 외부에서 가져와 인용할 위험 — 사이트가 침묵하면 외부 오류가 이긴다 | philosophy §8 어록 검증표를 사이트에 그대로 노출 — 출전 미확인 어록 목록과 사유를 명시 (06_philosophy.md) |
| 4 | references.html이 각주 경유로만 도달하는 준고아 페이지였다 | 전역 내비 상시 노출 + 전 페이지 푸터 링크 + 홈 통계 박스에서 직링크 (01_home.md, §2) |

도달성 검증: 10페이지 전부 전역 내비에서 1클릭 도달 — 고아 페이지 0. 모든 앵커 대상(사건 165 렌더분·인물 59·조직 22·사료 47)은 데이터 파일 id 기반이라 끊어진 앵커는 Phase 5 QA 스크립트로 전수 검출 가능.

## 9. 페이지 명세 목록과 산출물 경로

| 명세 | 페이지 | 본문 산출(narrative-writer) | 분량 가이드(공백 포함 한글) |
|------|--------|---------------------------|------------------------|
| `page_specs/00_common.md` | 전 페이지 공통 규칙 | — | — |
| `page_specs/01_home.md` | index.html | `drafts/01_home.md` | 1,000–1,500자 |
| `page_specs/02_life.md` | life.html | `drafts/02_life.md` | 12,000–16,000자 |
| `page_specs/03_timeline.md` | timeline.html | `drafts/03_timeline.md` (도입·안내문만) | 400–700자 |
| `page_specs/04_map.md` | map.html | `drafts/04_map.md` (도입·경로 해설만) | 600–1,000자 |
| `page_specs/05_organizations.md` | organizations.html | `drafts/05_organizations.md` | 6,000–8,500자 |
| `page_specs/06_philosophy.md` | philosophy.html | `drafts/06_philosophy.md` | 5,000–7,000자 |
| `page_specs/07_people.md` | people.html | `drafts/07_people.md` | 5,000–7,000자 |
| `page_specs/08_archives.md` | archives.html | `drafts/08_archives.md` | 3,500–5,500자 |
| `page_specs/09_gallery.md` | gallery.html | `drafts/09_gallery.md` (도입만) | 200–400자 |
| `page_specs/10_references.md` | references.html | `drafts/10_references.md` (방법론 절만) | 1,200–2,000자 |

- 본문 초고는 `_workspace/03_content/drafts/`에 markdown으로 작성하고, Phase 4 data-engineer가 `site/data/pages/*.json`으로 변환한다 (site-architecture §4 — HTML 하드코딩 금지의 상류 공정).
- 이미지: visual-curator가 `page_specs/*` 이미지 슬롯 표 기준으로 수집, visual-sourcing 스킬 스키마의 manifest에 슬롯 id를 매핑. 사이트 전체 필수 슬롯 21 + 권장 33–43 (집계 기준표는 09_gallery.md §3 — 수집 라운드 1 확정 반영: img-phil-02 권장 강등). 수집 결과 80건: `_workspace/03_content/images/manifest.json`.
- 인용: citation-manager가 [ref:] 마커를 citations.json으로 매핑 (citation-style 스킬). 작성 단계 마커에는 synthesis 근거 식별자(clm-/evt-/src-pri-/cfl-)를 그대로 쓴다 — 매핑·정규화는 citation-manager 소관.

## 10. 동결·증분 관리

- 본 IA는 02_verified 동결본 기준이다. 잔여 조건부 상충 4건(cfl-018·032·041·052)과 network 대기 목록(P-1 조소앙 출생일, P-2 임치정 명단)의 재판정이 도착하면 **영향 페이지 명세만 증분 개정**하고 변경 이력에 기록, 영향 팀원에게 통지한다.
- timeline.json 메타의 잔여 증분 1건(evt-amer-023, cfl-064 관련)도 동일 절차.

## 변경 이력

| 일자 | 버전 | 변경 | 영향 | 통지 |
|------|------|------|------|------|
| 2026-06-06 | v1.0 | 최초 확정 — 10페이지 IA + 명세 11종 | 전체 | team-lead·narrative-writer·visual-curator |
| 2026-06-06 | v1.0 | team-lead 승인·동결 — 10페이지 구성 및 핵심 결정 5건 승인, D등급 차단·앵커 무변형은 Phase 4·5 계약 승계 | 상태 표기만 (내용 변경 없음) | — |
| 2026-06-06 | v1.0 | narrative-writer 소스 제약 피드백 회신 — 01_home(히어로 어록 금지)·02_life(공백 추정 서사 금지, 분량 게이트보다 우선) 문구 명문화. 요구 변경 없음(암묵 규칙의 클래리피케이션 — 동결 범위 내) | 01_home·02_life | narrative-writer |
| 2026-06-06 | v1.0 | copy-editor 요청 반영 — 00_common §2 한정 인용 표기를 "3종"에서 비망라 골격(6종 예시)으로 정정, 망라 목록은 style_guide.md R0.4 소유 명시. 누락 위험 제거 목적의 결함 수정 | 00_common | copy-editor·narrative-writer |
| 2026-06-06 | v1.0 | narrative-writer 확인 요청 3건 처리 — ① 02_life 조직 링크를 닫힌 기준으로 정정(05 명세 앵커 매핑 준거, org-002 링크 금지, 동우회→org-019) ② #ch-gaps→archives#unlocated 링크 의무 추가 ③ 00_common §3·§8에 편집 메타 서술 [ref:] 예외(허용 4곳 한정) 신설 | 00_common·02_life | narrative-writer·citation-manager |
| 2026-06-06 | v1.0 | narrative-writer 결함 보고 반영 — 06_philosophy 교차링크의 소멸 id evt-phil-002를 생존 id evt-early-019로 정정 + evt-phil 생존 3건(007·009·010) 주의 문구 추가. 전 명세 evt id 전수 스캔(범위 표기 확장 포함) 결과 동종 결함 추가 0건 확인 | 06_philosophy | narrative-writer |
| 2026-06-06 | v1.0 | citation-manager 정밀화 2건 반영 — ① 00_common §3에 마커 수명주기 2단계 명문화(집필 clm-/evt-/src-pri-/cfl- → normalize_markers.py 정규화 → 최종 [ref:ref-NNN], Phase 4 입력은 ref-NNN) ② 앵커 키 = sources[].id(src-{pri\|aca\|ins\|enc\|web}-{NNN}) 특정, sitemap §4 가공 예시 src-news-001을 실재 코드로 교체, 10_references 해석 경로·완성 기준 연동 수정. narrative-writer·copy-editor 기합의 흐름의 명문화 — 집필 단계 작업 방식 변경 없음 | 00_common·10_references·sitemap §4 | citation-manager |
| 2026-06-06 | v1.0 | citation-manager 검사 구현 확인에 따른 보강 — 00_common §3에 예약 앵커명 재사용 금지 신설(intro·ch-gaps·archives-gaps·methodology·grades — validate_citations.py 전역 [META] 매칭의 오분류 방지). 검사 구현은 명세 조정 불요 확인(재분류 방식, content-qa와 동일 의미론) | 00_common | citation-manager·narrative-writer |
| 2026-06-06 | v1.0 | visual-curator 수집 라운드 1 판정 5건 — ① img-phil-02(동광) 필수→권장 강등(자유 라이선스 미발견, 재검토 조건 명기) ② img-phil-03 대체 승인(진관사 독립신문 제30호, "육대사 게재호 아님" 캡션 의무) ③ img-ppl-01 정본=1963 이혜련 단독(연대 명기 의무), ppl-02 정본=1917 가족사진 ④ img-home-01 해상도 기준 현실화(550×696 — Phase 4 ui-designer 전달) ⑤ img-life-12 대체 승인(한국독립당 창립 선언 문서 1930). 집계 필수 22→21·권장 32–42→33–43 | 01_home·02_life·06_philosophy·07_people·09_gallery·sitemap §9 | visual-curator |
| 2026-06-06 | v1.0 | visual-curator sources.md §4 경로 점검 결과 반영 — img-phil-02 재검토 조건 구체화(국편 ma_014 원문 존재 확인, 블로커는 이용조건 — 표준화/개별 허가 시 필수 복귀), img-phil-05(서우) 미충족 확정 주석(ma_003 동일 사유). 신한민보 창간호 PD본의 org-03/life-05 활용 승인(공립신보 지령 승계 캡션은 clm-0064 정박) | 06_philosophy | visual-curator |
| 2026-06-06 | v1.0 | org-011(서북학회) 원천 예외 사후 정합화 — 05 명세가 org-011 앵커를 요구했으나 organizations.md에 서북학회 절이 없음(명세 결함, narrative-writer 발견). 드래프트의 해결(전용 소절 + life.md §6 clm-0104〔B〕 + people.md §7 한계 문장)을 검증 후 표준으로 명세화. "유일 사실 원천" 조항에 예외 명시 — 드래프트 재작업 불요 | 05_organizations | narrative-writer |
| 2026-06-06 | v1.0 | 한정 표기 변형 자구 주의 추가 — 00_common §2에 synthesis 원형 변형 안내("흥사단 전승 어록" ↔ 드래프트 자구 "흥사단 어록·전기류 전승") + QA·교열 검색식은 R0.4 변형 포함 망라 목록 기준 명시. R0.4 변형 등재는 copy-editor에 요청(R0.4 소유권 존중 — 직접 수정 안 함) | 00_common | copy-editor·narrative-writer |
| 2026-06-06 | v1.0 | org-019 링크 문구 정정 — 02_life "#ch-14·15에서"가 '각 1회'로 오독 가능(narrative-writer 질의). 의도는 첫 등장 1회 규칙 우선(ⓐ) — 드래프트 처리 적합 판정, "첫 등장(#ch-14) 1회만·#ch-15 무링크"로 명문화. 드래프트 수정 불요 | 02_life | narrative-writer |
| 2026-06-06 | v1.0 | §3 메타 예외 패턴 3종으로 확장 승인 — citation-manager 실집필 검출 14건 근거. (i) 앵커 패턴 `*-intro`·`*-gaps`+명명 4종(구판 "4곳 한정"이 명세 자신의 #org-gaps·#people-gaps보다 좁았던 결함 해소) (ii) 섹션 안내문(도산-사실 포함 시 마커 의무 단서) (iii) 데이터 집계 자기 서술(자기 인용 순환 금지 — content-qa 데이터 정합 검사로 대체). 예약 앵커명 규칙 패턴 연동 개정, §8 게이트 3항 연동. 14건 META 재분류 승인 — 드래프트 수정 불요 | 00_common | citation-manager·narrative-writer |
| 2026-06-06 | v1.0 | 입력 대장 갱신 — philosophy.md v1.1→v1.2 (synthesis-editor의 잔존 evt id 전수 정정, narrative-writer 경유 인지). 내용·구조 불변의 id 위생 개정이라 명세 영향 0 — 06 명세·드래프트 모두 처음부터 생존 id 기준이었음을 narrative-writer 재검증으로 확인. 기록 정확성 목적의 갱신만 수행 | sitemap 머리말 | — (영향 작업 없음) |
| 2026-06-06 | v1.0 | §3 확장 건 완전 종결 — citation-manager 판정 확정 접수(화이트리스트 갱신 완료, WARN 14건 전건 §3 적합·마커 추가 0: 기계 META 2 + 사람 판별 12, 도산-사실 내장 0 확인). 구현 주석 반영: (i) 패턴에 무접두 `intro` 포함 명문화(구판 archives #intro 흡수 — 검사기 구현과 명세 정합 완성) | 00_common | team-lead(종결 보고)·citation-manager |
