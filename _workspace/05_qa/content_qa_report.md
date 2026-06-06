# 콘텐츠 정확성 QA 보고서 (content-qa, Phase 5 최종 게이트)

> **★ 최종 사인오프(2026-06-06, content-qa 29): 게이트 = 무조건 통과(UNCONDITIONAL PASS).** 결함 5건 전건 해소(CQA-001~005). 차단 0·중대 0·경미 0. CQA-005 표시 텍스트 5곳(home 2·references 1·archives 2) "47건→48건" 치환 확인 — 사료 관련 "47건" 잔존 0, 표시(48)↔데이터(citations·catalog·meta 48) 정합, meta 21수치 mismatch 0, 인접 통계(305/172/165/135) 불변, build_data.py:873 주석 정정. 상세 §6·§7.

> **재검증 라운드 1 결과(2026-06-06, team-lead 수정 후): 게이트 = 조건부 통과 유지(차단 0).** 직전 4건 중 **3건 완전 해소(CQA-001·003·004)**, **1건 부분 해소·잔존(CQA-002)**. 신규 추적 결함 **CQA-005** 분리(아래 §6). 상세는 보고서 말미 **§6 재검증 라운드 1**.

- **작성:** content-qa(29) — 2026-06-06
- **스킬:** `content-accuracy-qa` 전수 대조 절차(표본 검사 금지)
- **대조 기준:** `_workspace/02_verified/`(timeline.json 172건·claims_register.json 305건·network.json·synthesis 6종) + `_workspace/03_content/`(citations.json·style_guide.md)
- **렌더 평면:** site/*.html 정적/메타 + site/data/pages/*.json blocks + site/data/{timeline,network,images,citations,archives,meta}.json 표시 필드
- **추출 규모:** 표시 텍스트 레코드 **2,303건** (HTML/메타 52 + 페이지 JSON 527 + 상위 데이터 1,724)
- **재현 스크립트:** `_workspace/05_qa/_scratch/`(extract.py, cmp_dates.py, cmp_refs.py, cmp_meta.py, cmp_dgrade.py, classify_dgrade.py, cmp_cgrade.py)

---

## 0. 게이트 판정

**조건부 통과(CONDITIONAL PASS).** 차단(블로커)급 결함 **0건**. 중대 1건·경미 3건. 어떤 결함도 검증된 사실을 거짓으로 바꾸지 않으며, 사이트 본문(life/people/organizations/philosophy)의 등급·상충·각주 규율은 무결하다. 다만 **이미지 캡션 1건이 D등급 자구를 단정 노출**(중대)하고, **자기 통계·사료 카탈로그가 1차 사료 1건을 누락 집계**(경미)하므로, 해당 2건 수정 후 재대조를 권고한다.

---

## 1. 검사 통계 (전수성 증명)

| 검사 항목 | 추출/대상 건수 | 대조 건수 | 결함 |
|----------|--------------|----------|------|
| 연표 사건 필드(날짜·장소·title·summary·detail·dispute·disputed·conf·tags·actors·orgs) | 165 사건 × 11 필드 | 165 사건 전수 | 0 |
| 끊어진 각주([ref:]→ref→source) | 마커 1,217회 / 고유 ref 155 | 양방향 전수 | 0 |
| D등급 무단 노출(excluded.md 52건 × 다중 probe) | probe 적중 199건 분류 | 52 claim 전수 | 1 |
| C등급 한정 문형 / 무출처 단정문 | 본문 단락 전수(年+단정어미+무ref+무한정) | 전수 | 0 |
| disputed 양론 병기 보존 | 17 사건 | 17 전수 | 0 |
| lede·도입·OG 메타 압축 합성 | home lede + 10 OG/desc + map 5경로 | 전수 | 0 |
| meta.json 통계 정합 | 21 수치 + 4 등급 + 3 신뢰도 | 전수 | 1 |
| 인명 한자 정규화(network hanja ↔ 본문 병기) | 56 인물 / 20 병기쌍 | 전수 | 0 |
| **합계** | | | **2 결함(+2 인접 관찰)** |

**전수성 자기검증(Policy 7):** 무작위 사건 10건을 수동 글자 단위 재대조 → 전부 verified와 완전 동일 확인(검사 스크립트가 거짓 통과시키지 않음을 입증). 연표 165건은 검증 timeline.json에서 D등급 7건만 차단한 무변형 export(날조 사건 0, 필드 불일치 0)임을 확인.

---

## 2. 결함 목록 (근거쌍 포함)

### CQA-001 [D등급 무단 노출 — 캡션 압축] 심각도: 중대(MAJOR)
- **위치:** `site/data/images.json` > `gwanghwamun-1880s.caption` (gallery/life/관련 페이지 렌더)
- **사이트 텍스트:** "1880년대 말의 광화문 일대. 안창호가 **1894년 상경**해 처음 마주한 서울의 풍경에 가깝다." (각주 마커 없음)
- **DB 레코드:** `claims_register.json` clm-0015 = "상경 시기는 1894년이다" **grade D**(cfl-003 부분해소, 〔재판정 v1.1: D 확정〕). `timeline.json` evt-early-009 = `date.start 1894-09-01 / end 1895-12-31 / precision range / disputed true`, summary "상경 시기는 출처 간 상충(1894년설 vs 1895년설)".
- **판정 근거:** 검증 DB는 상경 시기를 **disputed range(1894~1895)·D등급**으로 처리했고, 본문(life.json sec[2].blocks[1])은 정확히 "상경 시기는 1894년설과 1895년설이 갈려 1894~95년 무렵으로 적는다 [ref]"로 한정한다. 그러나 이 캡션만 "1894년 상경"으로 **단정·정밀화**했다. `style_guide.md` **R0.6**("이 두 위치 밖의 D등급 자구(캡션 포함)는 전부 회부 대상") + **R0.3**(range 단순화 금지) + **R0.5**(정밀화 금지) 위반. 표기 규칙 예외 아님. MEMORY 〔lede-compression-risk〕가 경고한 캡션 압축 패턴의 실제 발현.
- **수정 책임자:** visual-curator(20)(캡션 원안) → copy-editor(18) 교열 / data-engineer(23)(images.json 반영). 권고 자구: "안창호가 1894~95년 무렵 상경해 마주했을 무렵의 서울 풍경에 가깝다" 또는 연도 단정 삭제.

### CQA-002 [자기 통계·사료 카탈로그 불일치 — 1차 사료 1건 누락 집계] 심각도: 경미(MINOR)
- **위치:** `site/data/meta.json` `counts.primary_sources = 47`; `site/data/pages/home.json` sec[2]/sec[4] "1차 사료 카탈로그 **47건**"; `site/data/archives.json` catalog(47건, meta.count 47).
- **사이트 텍스트 vs DB:** `site/data/citations.json` sources에 `src-pri-001`~`src-pri-048` **48건** 연속 실재(누락 번호 0). `src-pri-048`(중외일보 1930-01-11자 필리핀 이주 보도)은 **ref-093이 실제 인용**하며 life.json sec[17].blocks[3]·organizations.json sec[25].blocks[2] 본문에 마커로 노출됨. 즉 인용·각주 체인은 정상(끊어진 각주 아님)이나, **archives.json catalog와 meta/home 통계가 src-pri-048을 빠뜨려 47로 집계**.
- **판정 근거:** 자기 서술 수치(meta·home "47건")가 실제 인용된 1차 사료 집합(48)과 불일치 → 사이트가 자기 데이터 규모를 1건 과소 진술. 끊어진 각주가 아니므로 차단급은 아니나, 통계 정합 게이트 위반.
- **수정 책임자:** data-engineer(23)(meta.json·archives.json catalog 재집계) / citation-manager(19)(카탈로그-인용 정합). 결정 필요: src-pri-048을 archives 카탈로그에 편입(48로 통일)할지, 또는 본문 인용을 다른 src로 대체할지 — 임의 채택 금지, 오케스트레이터 라우팅.

### CQA-003 [연표 카드 summary — D등급 세부 단정(요약 압축)] 심각도: 경미(MINOR)
- **위치:** `site/data/timeline.json` > `evt-shin-013.summary` (연표 카드 항시 렌더)
- **사이트 텍스트:** "1909년 8월 신민회가…청년학우회를 창립하였다. 설립위원장 윤치호, **총무 최남선** 등이 맡았고…"
- **DB 레코드:** claims_register clm-0111 = "청년학우회의 총무는 최남선이다" **grade D**(cfl-046 미해소, 총무원 안태국 vs 총무 최남선 병존). 동일 사건 `detail` 필드에는 병존이 명기됨("총무원 안태국…과 총무 최남선…이 병존한다").
- **판정 근거:** 본문(life.json sec[8].blocks[5])은 청년학우회 임원을 "설립위원장 윤치호"만 적고 **총무 최남선을 의도적으로 생략**(D등급 회피)했다. 그러나 연표 카드 summary는 detail의 병존을 압축하며 "총무 최남선"을 **단정**해 같은 사건의 본문 규율과 충돌. 검증 timeline.json summary와 글자 일치하므로 전사(轉寫) 오류가 아닌 **기준 DB 자체의 요약 압축**이다.
- **수정 책임자:** timeline-analyst(13)(timeline.json summary 한정 표지 보강 — "총무 최남선 등으로 전하며 임원 구성은 기록이 갈린다") → site/data 재export(data-engineer). QA는 DB 자구를 직접 고치지 않음.

### CQA-004 [연표 카드 summary — disputed 도착일 단일 표기(요약 압축)] 심각도: 경미(MINOR)
- **위치:** `site/data/timeline.json` > `evt-amer-016.summary` (연표 카드 렌더, conf=C)
- **사이트 텍스트:** "**1911년 9월 3일** 뉴욕 도착(망명 여정 종착) 직후 안창호는…"
- **DB 레코드:** claims_register clm-0131 = "뉴욕항 도착일은 1911년 9월 3일…" **grade D**(cfl-020 미해소, 공훈 9-02 vs 인명사전 9-03, range 09-02~03). 도착 사건 본체 evt-shin-028.detail은 "도착일은 출처 간 상충…①9월 2일 ②9월 3일…"로 정확히 병기.
- **판정 근거:** 후속 사건(evt-amer-016)의 summary가 도착일을 "9월 3일"로 **단일 채택**해, 도착 사건 자체의 상충 표기와 불일치. 검증 DB와 글자 일치(전사 무변형) — 기준 DB의 요약 압축.
- **수정 책임자:** timeline-analyst(13)(evt-amer-016 summary 도착일 표기를 "9월 초" 또는 evt-shin-028 참조로 완화) → data-engineer 재export.

---

## 3. 무결 확인 항목 (결함 0 — 근거)

1. **연표 날짜·장소(165 사건 전수):** date(start/end/precision/calendar)·place(name/modern_name/lat/lng) 전 필드가 verified timeline.json과 글자·값 완전 일치. 정밀도 과장·음양력 오류·환산 오류 0. 날조 사건 0. (cmp_dates.py)
2. **끊어진 각주 0:** 본문/데이터 [ref:] 마커 1,217회, 고유 ref 155건 전수가 citations.json에 정의됨(broken 0), 고아 ref 0(155 전부 사용), 모든 ref의 source_id가 실존 source(194건)로 해소(unresolved 0). meta.refs(155)와 일치. references 페이지는 citations.sources 194건 전수 렌더(references.js). (cmp_refs.py)
3. **D등급 어록 6계열 전면 미노출:** 임종 어록(clm-0226)·낙망은 청년의 죽음(0239)·밥을 먹어도(0241)·서로 사랑하면/힘은 인격과 단결(0242)·자유의 인민(0243)·점진가 가사(0244) — blockquote·큰따옴표 단정 노출 0. philosophy §8 "싣지 않은 어록" 작은따옴표 목록(R0.6 ② 허용 위치)에서만 자구 등장, 임종 어록은 자구조차 미수록. 본문 blockquote 인용 어록은 검증 2건(흥사단 약법 목적 조항 "전재본 기준"·「개조」 "안도산전서 수록본에 따름")뿐.
4. **D등급 전승 4종 메타 주장 경유 처리:** 호'도산'하와이설(0046)·이토 면담(0103)·도산 내각(0115)·오렌지 일화(0057) 모두 "두 전승이 병존…어느 쪽도 1차 사료로 확인되지 않았다 / 채택하지 않는다 / 동시대 사료에서 확인되지 않는다" 형태(archives "채택하지 않은 전승"·life 한정문). 객체 주장 단정 0.
5. **D등급 상충 기각측 각주 처리:** 1912 초대 중앙총회장(0069)·신민회 1907.4(0100)·가출옥 1933(0215)·태극서관 1905(0106)·파차파 1904(0055)·대구복심(0273)·기소 122/49명(0275/0276) 등 — "사용하지 않는다(필수 각주)"·"오기로 판정"·"통설…단정할 수 없다"·"기록이 갈린다"·"범위로 적는다" 등 한정/판정경위 동반. 단정 승격 0.
6. **D등급 미확정 관계 §7 격리:** 서재필(0259)·안중근(0260)·박용만 중재(0261)·손정도(0302)·안치호 한자(0286) — 본문 단정 0. 안치호 한자는 "두 표기가 병존해 한글로만 적는다"로 명시 회피, network.json summary만 상충 전문 병기(authorized).
7. **C등급 한정 문형 유지:** 본문 단락 중 "연도+단정어미+무ref+무한정" 0건. C 89건의 단정 승격 정황 미검출.
8. **disputed 17건 전수 양론 병기:** 17 사건 모두 dispute_note 보유, 전부 verified와 글자 일치. 단일 설 서술 0.
9. **lede/도입/OG 무압축:** home 도입 서사의 연쇄 사실(1878 출생 A / 1897 독립협회 B / 1899 점진학교 A / 1902 도미 B / 1905 공립협회 B / 1907 신민회·대성학교 / 1913 흥사단 A / **1914 국민회 중앙총회장 당선** — D등급 "1912 초대" 회피 / 1938.3.10 순국) 전수가 timeline 값과 정합. map "다섯 번의 대이동"은 R1~R5 5경로와 1:1, 경유 항로 전승은 "전해진다" 한정. 10개 OG/meta description에 지리 한정·영웅 수사·새 사실 0. 영웅 형용사·존칭 0.
10. **인명 한자 정규화:** 본문 병기 한자 20쌍이 network.json hanja와 전수 일치(불일치 0).

---

## 4. 미검 범위 / 한계 명시

- **이미지 실파일·alt 시각 검증 제외:** 캡션·credit 텍스트는 전수 대조했으나 실제 .webp 이미지의 인물 식별(사진이 도산 본인인지)은 본 콘텐츠 QA 범위 밖(visual-curator/a11y-engineer 소관). 캡션의 "~로 전해지는 사진" 한정 표기는 확인됨.
- **외부 URL 생존성 제외:** sources의 url 200/404 여부는 link/web-qa(qa-engineer) 소관. 본 보고는 ref→source **참조 무결성**만 판정.
- **D등급 probe 한계:** excluded.md 52건을 다중 키워드 probe(199 적중)로 분류했고 1건(CQA-001) 확정. probe는 고유 인명·자구·날짜 조합 기반이라 자구가 전혀 다르게 의역된 D등급 노출은 이론상 누락 가능 — 단, 사이트 본문이 검증 DB의 자구를 보존하는 구조(전사 export)이고 무작위 10건 재대조가 무변형을 입증해 누락 위험은 낮음.
- **기준 DB 내부 상충 분리:** CQA-003·004는 site 전사 오류가 아니라 검증 timeline.json summary 자체의 요약 압축이다. 사이트 결함이 아닌 "기준 DB 한정표지 보강 건"으로 분리 라우팅(timeline-analyst), site는 무변형 전사임을 명시.

---

## 5. 수정 후 재대조 지침

- CQA-001(캡션) 수정 시 images.json 해당 캡션 단건이 아니라 **gallery·life 렌더 결과 전체 캡션 47건(연도+무ref)** 재스캔 권고 — 압축 수정 과정의 인접 변형 방지.
- CQA-002 수정 시 meta.json `primary_sources`·home 통계·archives catalog **세 곳 동시 정합** 확인(한 곳만 고치면 새 불일치 발생).
- CQA-003·004 수정 시 timeline.json summary 변경 → site/data 재export 후 해당 사건 카드 + 본문 동일 사건 단락 **양쪽 재대조**.

## 반환 요약

- **결함 수:** 차단 0 / 중대 1(CQA-001) / 경미 3(CQA-002·003·004). 인접 관찰 포함 총 4건.
- **유형별:** D등급 캡션 압축 노출 1, 자기 통계 불일치 1, 연표 summary 요약 압축 2.
- **핵심 발견:** ① 본문(life/people/org/philosophy)의 등급·상충·각주 규율 무결 — 끊어진 각주 0, D등급 어록 전면 미노출, disputed 17건 양론 보존, 인명 한자 정합. ② **유일한 D등급 단정 노출은 본문이 아닌 이미지 캡션 1건**(gwanghwamun "1894년 상경") — MEMORY가 경고한 캡션 압축 패턴. ③ 1차 사료 1건(src-pri-048)이 인용은 정상이나 카탈로그·통계에서 누락 집계.
- **게이트 판정: 조건부 통과** — CQA-001(중대) 수정을 게이트 통과 조건으로, CQA-002~004(경미)는 동시 수정 권고.

---

## 6. 재검증 라운드 1 (2026-06-06, team-lead 수정·재빌드 후)

- **검증 범위:** team-lead 지시에 따라 수정 평면(captions·summaries·counts)에 한정 전수 재검 + `_scratch/` 재현 스크립트 전부 재실행(extract → cmp_dates → cmp_refs → cmp_meta → cmp_dgrade → classify). 직전 0결함 평면(본문 단락·각주·disputed·인명 한자)은 인접 변형 점검으로 무손상 확인.
- **방법 메모:** 재추출 레코드 2,304건(+1 = archives catalog src-pri-048 증분). check_data_schema·check_links는 team-lead 측 PASS, 본 절은 그 검사가 못 잡는 **사용자 표시 텍스트** 정합을 판정.

### 결함별 재검 결과

| 결함 | 직전 심각도 | 재검 결과 | 근거(재실행) |
|------|-----------|----------|------------|
| CQA-001 캡션 D 노출 | 중대 | **해소** | manifest 원천·site/data/images.json 동시 수정 확인. `gwanghwamun-1880s.caption` = "안창호가 1894~95년 무렵 상경해 처음 마주했을 서울의 풍경에 가깝다(상경 연도는 기록이 갈린다)". cmp_dgrade clm-0015 "1894년 상경" probe 적중 1→**0**. R0.3·R0.5·R0.6 위반 해소 |
| CQA-003 summary D세부 | 경미 | **해소** | `evt-shin-013.summary`에서 "총무 최남선" 제거, "설립위원장은 윤치호가 맡았고"로 정리. 02_verified↔site 글자 일치(전사 무변형). cmp_dgrade clm-0111 적중 2→**1**(잔여 1은 detail의 authorized 병기 "총무원 안태국…과 총무 최남선…이 병존한다") |
| CQA-004 summary 단정 | 경미 | **해소** | `evt-amer-016.summary` = "1911년 9월 초 뉴욕 도착(망명 여정 종착, 도착일은 9월 2일과 3일로 기록이 갈린다)…". 단정 "9월 3일" 소멸, 양설 병기. 02_verified↔site 글자 일치. clm-0131 summary 적중 소멸(잔여는 evt-shin-028.detail 상충 전문 — authorized) |
| CQA-002 1차 사료 집계 | 경미 | **부분 해소 — 잔존(CQA-005로 추적)** | 데이터·계약 계층 4곳 정합 완성: citations 48 = archives catalog 48 = archives meta.count 48(by_status confirmed 22→23) = meta.primary_sources 48. check_data_schema.py L177 `assert len(cat)==48`·build_data.py L605 동기. **그러나 사용자 표시 본문 5곳이 "47건" 잔존** → CQA-005 |

### CQA-005 [자기 통계 표시 텍스트 미동기 — "1차 사료 47건" 잔존] 심각도: 경미(MINOR), CQA-002에서 분리
- **위치(5곳, 사용자 표시 본문):**
  - `site/data/pages/home.json` > `sections[2].blocks[0].items[6]` — "1차 사료 카탈로그 47건, 사료 비판과 소재 미확인 목록"
  - `site/data/pages/home.json` > `sections[4].blocks[1].items[3]` — "1차 사료 카탈로그 **47건** — 소재 미확인 사료 목록 포함"
  - `site/data/pages/references.json` > `sections[3].blocks[0].text` — "…1차 사료 카탈로그 47건 위에서 작성되었다…"
  - `site/data/pages/archives.json` > `sections[0].blocks[0].text` — "조사에서 다룬 1차 사료는 47건이며…"
  - `site/data/pages/archives.json` > `sections[1].blocks[2].text` — "사료 47건의 카드가 유형별로 표시된다…"
- **사이트 텍스트 vs DB:** 표시 텍스트 "47건" ↔ `meta.json primary_sources 48` / `archives.json catalog 48` / `citations.json src-pri 48`. 즉 **데이터 계층(48)과 사용자 표시 자기서술(47)이 모순**.
- **판정 근거:** CQA-002 수정이 데이터·빌드 계약 계층은 48로 동기했으나, 그 수치를 **사용자에게 진술하는 페이지 본문 5곳을 함께 갱신하지 않았다.** 스키마 검사는 JSON 카운트만 보므로 PASS했지만, content-qa의 표시-텍스트 정합 기준에서는 사이트가 자기 사료 규모를 1건 과소 진술하는 통계 모순(직전 CQA-002와 동일 성질의 미해소분). archives 페이지는 "사료 47건의 카드가 표시된다"고 적으나 실제 카드는 48건 렌더되어 표시-실데이터 불일치.
- **수정 책임자:** narrative-writer(17)(home·references·archives 본문 "47건"→"48건" 5곳) → copy-editor(18) 교열 / data-engineer(23)(재export). 부수: `build_data.py:873` stale 주석(`# 47`, 값은 archives_count=48이라 동작 무영향이나 정정 권고).

### 인접 변형 무손상 확인 (수정이 0결함 평면을 건드리지 않음)
- 165 사건 필드 전수 재대조 — mismatch **0**(수정 2건은 verified↔site 글자 일치, 그 외 필드 변형 0).
- 각주 무결성 — 마커 1,217회·broken 0·orphan 0·source 미해소 0 유지(catalog 48 증분이 ref-093→src-pri-048 체인 무손상).
- disputed 17건 전수 dispute_note 보존, evt-shin-013·evt-amer-016의 disputed flag·date 불변(summary 한정표지 보강이 타 필드 미오염).

### 재검증 게이트 판정
- **조건부 통과 유지(차단 0).** 중대 0(CQA-001 해소). 경미 1 잔존(CQA-005 — 표시 텍스트 5곳 "47→48"). CQA-005는 검증된 사실을 거짓으로 바꾸지 않는 자기 통계 표시 모순이므로 차단급 아님. **CQA-005 수정 후 home·references·archives 3페이지의 통계 표시 텍스트 재스캔만으로 완전 해소 가능** — 그 시점에 무조건 통과(UNCONDITIONAL PASS) 전환 권고.

### 반환 요약 (재검증 라운드 1)
- **해소:** CQA-001(중대), CQA-003·004(경미) — 3건.
- **잔존:** CQA-005(경미, CQA-002 표시-텍스트 미동기분 분리) — home 2·references 1·archives 2 = 5곳 "1차 사료 47건".
- **게이트:** 조건부 통과(차단 0). CQA-005 표시 텍스트 5곳 "47→48" 갱신이 마지막 잔여 조건.
