---
name: citation-style
description: 도산 안창호 사이트의 인용·출처 표기 체계를 구축·관리할 때 반드시 사용하는 인용 스타일 스킬. 출처 ID 체계(src-{유형}-{일련번호}), 사료/논문/단행본/웹별 표기 형식, citations.json 스키마, 본문 마커 [ref:id]와 매핑의 무결성 검증 스크립트를 규정한다. "인용 다시", "출처 업데이트", "참조 무결성 재검증", "참고문헌 보완", "끊어진 각주 수정" 요청 시에도 이 절차를 재적용한다. citation-manager(19)가 단독 사용하며, content-qa(29)의 각주 검사 기준이기도 하다.
---

# 인용·출처 표기

인용 체계는 사이트의 신뢰를 기계적으로 보증하는 마지막 안전망이다. 본문의 모든 사실 진술은 `[ref:id]` 마커를 통해 출처에 연결되고, 이 연결이 단 하나라도 끊어지면 독자에게는 "근거 없는 주장"으로 보인다. 따라서 이 스킬의 목표는 아름다운 서지 형식이 아니라 **끊어진 참조 0건** — 모든 마커가 실재하는 출처에 도달하고, 모든 출처가 검증 가능한 표기를 갖는 상태다. 형식의 통일은 그 자체가 목적이 아니라, 기계 검증을 가능하게 하는 전제조건이다.

## 1. 출처 ID 체계

형식: `src-{유형}-{일련번호}` — 예: `src-pri-001`, `src-aca-014`.

| 유형 코드 | 의미 | 대상 |
|----------|------|------|
| `pri` | primary | 1차 사료 — 일기·서한·연설문·동시대 신문·신문조서·판결문 |
| `aca` | academic | 학술 논문·연구서 |
| `ins` | institutional | 공공기관 DB·기관 발간물 |
| `enc` | encyclopedia | 백과사전 표제어 |
| `web` | web | 일반 웹 자료 |

운영 규칙:

- 일련번호는 유형별 3자리 연번. 한 번 발급한 id는 출처를 삭제해도 재사용하지 마라 — 재사용된 id는 과거 버전의 마커를 엉뚱한 출처로 연결시킨다.
- 같은 출처의 다른 면(페이지)은 새 source가 아니라 같은 source id에 다른 `page_or_locator`를 가진 별도 ref다 (3절 스키마의 refs/sources 분리가 이를 위한 구조다).
- primary-source-researcher의 사료 카탈로그(`src-pri-` id)와 충돌하지 않게, 사료는 카탈로그의 id를 그대로 승계하라. 같은 사료에 두 id가 생기면 어느 쪽 메타데이터가 진본인지 알 수 없게 된다.

## 2. 표기 형식 (유형별)

참고문헌 페이지와 각주에 표시되는 문자열 형식이다. 형식을 단일하게 유지해야 하는 이유: 표기가 흔들리면 독자가 같은 출처를 다른 출처로 오인하고, 기계 대조(중복 출처 탐지)도 불가능해진다. 예외 없이 적용하라.

| 유형 | 형식 | 예 |
|------|------|-----|
| 1차 사료 | 작성자, 「사료명」, 작성연도, 소장처, 문서번호/locator. | 안창호, 「안창호 일기」, 1920, 독립기념관. |
| 신문 기사 | 「기사 제목」, 『신문명』, YYYY.MM.DD., 면수. | 「국민회 중앙총회 결성」, 『신한민보』, 1912.11.20., 1면. |
| 학술 논문 | 저자, 「논문 제목」, 『학술지명』 권(호), 발행연도, 수록면. | 홍길동, 「안창호의 대공주의 연구」, 『한국독립운동사연구』 50, 2015, 1–35쪽. |
| 단행본 | 저자, 『서명』, 출판사, 발행연도. | 이광수, 『도산 안창호』, 도산안창호선생기념사업회, 1947. |
| 웹 자료 | 작성 주체, 「문서 제목」, 사이트명, URL (접속일: YYYY-MM-DD). | 국사편찬위원회, 「안창호 신문조서」, 한국사데이터베이스, https://db.history.go.kr/... (접속일: 2026-06-06). |

- 한국어 서지 관행에 따라 논문·기사·사료는 「」, 책·신문·학술지는 『』로 감싼다.
- 웹 자료의 접속일은 필수다 — 웹 페이지는 변하고 사라지므로, 접속일이 없으면 "그 시점의 그 내용"이라는 검증 좌표가 사라진다.
- 같은 유형인데 형식 요소가 결손된 출처(저자 미상 등)는 결손 자리를 생략하되, sources 레코드의 해당 필드는 null로 명시해 결손이 의도임을 남겨라.

## 3. citations.json 스키마

산출물 `_workspace/03_content/citations.json`은 refs(본문 마커 ↔ 출처+위치)와 sources(출처 원장)의 2층 구조다. 분리하는 이유: 같은 책의 다른 페이지를 인용할 때마다 서지 정보 전체를 복제하면, 서지 수정 시 일부만 고쳐지는 불일치가 생긴다. 서지는 sources에 한 번만, 위치는 refs에 여러 번.

```json
{
  "refs": [
    {
      "id": "ref-{일련번호}",          // 본문 마커 [ref:id]가 참조하는 id. 전역 유일
      "source_id": "src-aca-014",     // sources 배열에 실재해야 하는 출처 id
      "page_or_locator": "23–25쪽"    // 출처 내 위치 — 면수, 문서번호, URL 단편 등. 전체 인용이면 null
    }
  ],
  "sources": [
    {
      "id": "src-aca-014",            // 1절 ID 체계
      "type": "primary|academic|institutional|encyclopedia|web",
      "author": "저자 또는 작성 주체",  // 미상이면 null
      "title": "제목",
      "publisher": "출판사·발행처·소장처",
      "year": 2015,                   // 발행·작성 연도. 미상이면 null
      "url": "접근 URL 또는 null",
      "accessed": "YYYY-MM-DD"        // url이 있으면 필수, 없으면 null
    }
  ]
}
```

## 4. 본문 마커 ↔ 매핑 무결성 검증 절차

무결성은 눈이 아니라 스크립트로 검증하라. 페이지 수십 개의 마커 수백 개를 눈으로 대조하면 반드시 누락이 생기고, 한 번 통과한 뒤에도 본문 수정마다 다시 깨질 수 있으므로 재실행 가능해야 한다.

검사 항목 4종:

1. **고아 마커:** 본문에 있는 `[ref:id]`가 refs에 없음 → 끊어진 각주가 된다.
2. **미사용 ref:** refs에 있는데 본문 어디에도 마커가 없음 → 참고문헌이 부풀려진다.
3. **끊어진 source:** ref의 `source_id`가 sources에 없음 → 각주가 빈 서지를 가리킨다.
4. **출처 없는 문단:** 사실 진술 문단에 마커가 하나도 없음 → narrative-writer에 직설 통보 대상.

```python
import json, re, glob, sys

cit = json.load(open("_workspace/03_content/citations.json"))
ref_ids = {r["id"] for r in cit["refs"]}
src_ids = {s["id"] for s in cit["sources"]}
errors = []

# refs 무결성
dup = len(cit["refs"]) != len(ref_ids)
if dup: errors.append("refs: 중복 id 존재")
for r in cit["refs"]:
    if r["source_id"] not in src_ids:
        errors.append(f"{r['id']}: source_id {r['source_id']} 미존재 (끊어진 source)")

# 본문 마커 전수 스캔
used = set()
for path in glob.glob("_workspace/03_content/pages/*.md"):
    body = open(path, encoding="utf-8").read()
    for m in re.findall(r"\[ref:([^\]]+)\]", body):
        used.add(m)
        if m not in ref_ids:
            errors.append(f"{path}: 고아 마커 [ref:{m}]")
    # 출처 없는 문단 (제목·빈 줄 제외, 마커 없는 본문 문단)
    for i, para in enumerate(body.split("\n\n")):
        p = para.strip()
        if p and not p.startswith("#") and "[ref:" not in p and len(p) > 80:
            errors.append(f"{path}: 문단 {i+1} 출처 마커 없음 (확인 요망)")

for unused in ref_ids - used:
    errors.append(f"미사용 ref: {unused}")

print(f"마커 {len(used)}종, refs {len(ref_ids)}건, sources {len(src_ids)}건, 문제 {len(errors)}건")
for e in errors: print(" -", e)
sys.exit(1 if errors else 0)
```

"출처 없는 문단" 검사는 짧은 연결 문단 등 오탐이 있을 수 있으므로, 기계 검출 후 사람이 사실 진술 문단인지 판별해 처리하라 — 오탐을 이유로 검사 자체를 끄지는 마라.

## 5. 참고문헌 페이지 데이터

`references_page.md`는 sources를 유형별(1차 사료 → 학술 → 기관 → 백과 → 웹)로 묶고, 각 유형 내에서 저자 가나다순으로 정렬해 2절 형식으로 렌더링한 것이다. 직접 손으로 쓰지 말고 citations.json에서 생성하라 — 손으로 쓰면 citations.json과 참고문헌 페이지가 서로 다른 두 진실이 된다.

## 산출물 검증

확정 전 다음을 모두 통과해야 한다.

1. 4절 검증 스크립트 실행 결과 끊어진 참조(고아 마커·끊어진 source) 0건 — 실행 로그를 보존하라.
2. 미사용 ref 0건, 또는 사용 예정 사유가 기록되어 있는가.
3. 모든 source가 1절 ID 체계를 따르고, 사료 출처는 primary-source 카탈로그의 id를 승계했는가.
4. `url`이 있는 모든 source에 `accessed`가 있는가.
5. references_page.md가 citations.json에서 생성되었고, sources 수와 표기 건수가 일치하는가.
6. 본문 수정이 발생한 뒤에는 반드시 스크립트를 재실행했는가 — 무결성은 한 번의 통과가 아니라 마지막 수정 이후의 통과만 유효하다.
