# 페이지 명세 03 — 연표 (timeline.html)

> v1.0 (2026-06-06) / 전제: 00_common.md. 구현은 Phase 4 timeline-developer(interactive-viz 스킬) 소관 — 본 명세는 **콘텐츠·데이터 요구**만 정의한다.

## 목적
검증 사건 165건의 인터랙티브 탐색. 연구자 여정(J2)의 진입점 — 사건마다 날짜 정밀도·신뢰도·disputed·출처를 그대로 노출하는 것이 핵심 가치다.

## 데이터 소스
- `timeline.json` (172건) → **렌더 대상 165건 = confidence D 7건 제외** (evt-early-002, evt-amer-009, evt-amer-034, evt-provgov-001, evt-chrono-110, evt-provgov-028, evt-hsd-024). 제외는 Phase 4 데이터 변환 단계 필터 — D 사건은 site/data로 내보내지 않는다.
- 소비 필드: id, title, date{start,end,precision,calendar}, place{name,modern_name,lat,lng}, actors, orgs, summary, detail, sources, confidence, tags, disputed, dispute_note

## 화면·콘텐츠 요구
1. **도입문** (narrative-writer, 400–700자): 연표의 범위(1878–1973)·등급 표시 의미·disputed 표시 의미·D등급 7건 제외 사실 명시("검증 미달 7건은 수록하지 않았다" + archives 링크). 비JS 환경 안내 1문장.
2. **사건 카드** (데이터 바인딩 — 문안 작성 불요): 제목 / 날짜(precision 반영 표기: day→YYYY-MM-DD, month→YYYY-MM, year→YYYY, range→"YYYY-MM~YYYY-MM") / summary / 장소 / 등급 배지(A·B·C) / disputed 마크+dispute_note / 출처 목록 / actors·orgs 앵커 링크.
   - 〔미확인〕이 제목에 붙은 사건은 D 필터로 전부 제외됨 — 잔존 시 데이터 결함으로 보고.
   - title·summary는 timeline.json 원문 그대로 (요약 재작성 금지 — 검증 텍스트 변형은 QA 대조를 끊는다).
3. **필터**: ① 시기 P1–P8 (sitemap §3 경계로 date.start 버킷) ② 주제 태그 7종 — 결사(114)·이동(38)·사상(35)·가족(31)·교육(22)·언론(17)·연설(1), timeline.json tags **그대로** (태그 병합·개명 금지 — 데이터 변경은 월권) ③ disputed만 보기 토글.
4. **딥링크**: `timeline.html#evt-{id}` (사건 직행), `timeline.html?period=P3` (시기 필터 상태) — 다른 페이지의 "이 시기의 연표 보기" 링크 형식. 구현 계약은 Phase 4 architecture.md로 이관하되 형식은 본 명세가 고정한다.

## 분량
도입문 400–700자만. 나머지는 데이터 렌더.

## 이미지 슬롯
없음 (필수 0). 사건 카드 썸네일은 Phase 4 선택 사항 — 콘텐츠 요구 아님.

## 교차링크
- 사건 카드 → `life.html#ch-XX` (소속 시기 장 — date 기반 자동 매핑)
- 사건 카드 actors → `people.html#per-...`, orgs → `organizations.html#org-...` (network.json 노드 보유분만 — name_normalization으로 매칭, 미보유 인명은 텍스트)
- 좌표 보유 사건(117건) → `map.html#evt-...` "지도에서 보기" (워크스루 수정 #2)
- 출처 → `references.html#...` (citation-manager 매핑 후)

## 완성 기준
- 렌더 사건 수 = 165 (D 7건 잔존 0)
- disputed 17건 전건 마크+dispute_note 노출
- date 표기가 precision 초과 0건 (range를 단일 일자로 평탄화 금지)
- 도입문에 D 제외 고지·archives 링크 존재
