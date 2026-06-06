---
name: timeline-construction
description: 도산 안창호 생애(1878–1938) 연표를 구축·검증·확정할 때 반드시 사용하는 연표 구축 스킬. 음력/양력 구분 규칙(1896 태양력 도입 기준), 불확실 날짜의 precision·range 표기, 시공간 모순 전수 검사 절차, timeline.json 최종 형식과 검증 스크립트를 규정한다. "연표 다시", "연표 업데이트", "날짜 검증 보완", "타임라인 재구축", "정합성 재검사" 요청 시에도 이 절차를 재적용한다. chronology-researcher(02)가 연표 골격 수집에, timeline-analyst(13)가 최종 timeline.json 확정에 사용한다.
---

# 연표 구축

연표는 이 하네스의 등뼈다. 모든 연구원의 사건이 연표로 병합되고, 관계망(network.json)·서사(pages)·인터랙티브 연표 페이지가 모두 timeline.json을 소비한다. 연표의 날짜 오류는 단순 오타가 아니라 인과관계의 왜곡(원인이 결과보다 늦게 표시되는 등)으로 증폭되므로, 날짜의 표현 규칙과 정합성 검사를 다른 무엇보다 엄격하게 적용해야 한다.

## 1. 사건 레코드 스키마

**사건 레코드 스키마는 S02 historical-research의 스키마와 동일하다. 여기서 재정의하지 않는다 — `historical-research` 스킬의 "사건 레코드 JSON 스키마" 절을 참조하라.** 스키마 정의가 두 곳에 존재하면 한쪽만 수정되는 drift가 반드시 발생하고, drift는 병합 단계에서 데이터 유실로 나타난다. 이 스킬은 그 스키마 중 `date` 객체의 해석·검증 규칙만 심화한다.

## 2. 음력/양력 규칙

조선은 **1896년 1월 1일 태양력(건양 원년)을 도입**했다. 이 날짜가 모든 역법 판단의 분기점이다.

- **1896년 이전 날짜는 음력이 원본일 가능성이 높다.** 도산의 출생(1878)을 포함한 초년기 기록의 날짜는 별도 명시가 없으면 음력으로 의심하라. 후대 문헌이 음력 날짜를 양력 표기인 것처럼 옮긴 경우가 흔하므로, 출처가 어느 역법으로 적었는지를 먼저 확인해야 한다.
- **`calendar` 필드로 구분하라.** 원본 사료의 역법을 `calendar: "lunar"` 또는 `"solar"`로 기록한다. 이 필드의 목적은 변환이 아니라 **원본의 보존**이다 — 원본 역법 정보가 사라지면 이후 누구도 변환의 옳고 그름을 검증할 수 없다.
- **변환 시 원본 표기를 보존·병기하라.** 음력을 양력으로 변환해 표시하더라도 원본 음력 날짜를 버리지 마라. 변환값은 표시용, 원본은 검증용이다. 병기 형식: `1878년 11월 9일(음력 10월 6일)` 처럼 변환값 뒤 괄호에 원본을 남긴다. JSON에서는 `date.start`에 변환된 양력, `detail` 또는 사건 레코드의 원본 표기 주석에 음력 원본과 변환 근거를 기록하라.
- **변환 불확실 시 변환하지 마라.** 음력-양력 변환은 연도 경계(음력 11~12월은 양력 이듬해 1~2월)에서 연도까지 달라진다. 변환 근거(만세력 등)가 불확실하면 원본 역법 그대로 두고 `calendar: "lunar"`로만 표기하는 것이 잘못된 변환보다 낫다.
- **1896년 이후에도 방심하지 마라.** 민간 기록·제례 관련 날짜는 1896년 이후에도 음력을 쓰는 경우가 있다. 분기점은 "공식 역법"의 전환이지 모든 기록의 전환이 아니다.

## 3. 불확실 날짜 표기 — precision과 range

사료가 보장하는 정밀도보다 정밀하게 적는 것은 정보 추가가 아니라 오류 주입이다. "1905년경"을 "1905-01-01"로 적으면 하류 소비자는 1월 1일이라는 거짓 정밀도를 믿는다.

| 사료의 표현 | 표기 |
|------------|------|
| "1908년 9월 26일" | `start: "1908-09-26"`, `precision: "day"` |
| "1908년 9월" | `start: "1908-09-01"`, `precision: "month"` — day 자리는 채움값일 뿐임을 precision이 선언 |
| "1908년" | `start: "1908-01-01"`, `precision: "year"` |
| "1905년 봄" | `start: "1905-03-01"`, `end: "1905-05-31"`, `precision: "range"` |
| "1907년 초~1908년 사이" | `start: "1907-01-01"`, `end: "1908-12-31"`, `precision: "range"` |

- 범위의 중간값을 단일 날짜로 찍지 마라. 범위는 범위로 보존해야 정합성 검사가 올바르게 작동한다.
- 출처마다 날짜가 다르면 어느 하나를 고르지 말고 cross-validator의 채택 권고를 기다려라. 권고 전까지는 상충 양쪽을 기록하고 `disputed` 후보로 표시한다.

## 4. 정합성 검사 절차 (timeline-analyst)

검사는 표본이 아니라 전수로, 눈이 아니라 절차로 하라. 사건 수십 개의 쌍별 비교는 사람의 눈으로는 누락이 생긴다.

1. **스키마 검사:** 모든 레코드가 S02 스키마를 따르는가 — 필수 필드, 날짜 형식(YYYY-MM-DD), precision·calendar 허용값.
2. **시간 모순 검사:** `start > end`인 레코드, 생몰(1878-11-09~1938-03-10) 범위를 벗어나는 사건, 알려진 선후관계(예: 도미 이전에 미주 활동 불가)의 역전.
3. **공간 모순 검사:** 시간상 겹치거나 인접한 사건 쌍의 장소 간 이동이 당대 교통수단으로 물리적으로 가능한가. 같은 날 평양과 LA는 불가능하다. 태평양 횡단은 주 단위, 대륙 횡단 철도는 일 단위의 시간이 필요했다 — 인접 사건의 장소가 멀면 사이 간격을 검사하라.
4. **음양력 변환 검사:** `calendar: "lunar"`인 1896년 이전 사건의 변환값이 원본 병기와 함께 기록되어 있는가, 변환 근거가 있는가.
5. **해소 불가 모순 처리:** 검사로 드러났으나 출처상 해소할 수 없는 모순은 한쪽을 삭제하지 말고 양쪽을 보존하며 `disputed: true`를 부여하라. 모순의 존재를 표시하는 것이 분석의 결과물이지, 모순을 감추는 것이 아니다.

## 5. timeline.json 최종 형식과 검증 스크립트

최종 산출물 `_workspace/02_verified/timeline.json`은 다음 래퍼 구조를 가진다. `events` 배열의 원소는 S02 사건 레코드이며, 검증 단계에서 두 필드가 추가될 수 있다.

```json
{
  "meta": {
    "generated": "YYYY-MM-DD",            // 확정 일자
    "event_count": 0,                     // events 배열 길이와 일치해야 함 (무결성 자가 선언)
    "source_files": ["chronology_events.json", "..."]  // 병합된 입력 파일 목록 (감사 추적)
  },
  "events": [
    {
      "...": "S02 사건 레코드 전 필드",
      "disputed": false,                  // (검증 단계 추가) 해소 불가 상충 여부
      "dispute_note": null                // disputed=true일 때 상충 내용·출처 요약
    }
  ]
}
```

검증 스크립트 예시 — 형식 오류 0건을 직접 실행으로 확인하라. "스키마를 지켰을 것"이라는 믿음은 검사가 아니다.

```python
import json, re, sys

DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
data = json.load(open("_workspace/02_verified/timeline.json"))
events, errors = data["events"], []
ids = [e.get("id") for e in events]

if data["meta"]["event_count"] != len(events):
    errors.append("meta.event_count 불일치")
if len(ids) != len(set(ids)):
    errors.append("중복 id 존재")

for e in events:
    d = e.get("date", {})
    if not e.get("id") or not e.get("title"):
        errors.append(f"{e.get('id')}: 필수 필드 누락"); continue
    if d.get("start") and not DATE.match(d["start"]):
        errors.append(f"{e['id']}: start 형식 오류")
    if d.get("precision") not in ("day", "month", "year", "range"):
        errors.append(f"{e['id']}: precision 허용값 위반")
    if d.get("calendar") not in ("solar", "lunar"):
        errors.append(f"{e['id']}: calendar 허용값 위반")
    if d.get("end") and d.get("start") and d["end"] < d["start"]:
        errors.append(f"{e['id']}: start > end")
    if not e.get("sources"):
        errors.append(f"{e['id']}: 출처 없음")
    if e.get("disputed") and not e.get("dispute_note"):
        errors.append(f"{e['id']}: disputed인데 dispute_note 없음")

print(f"{len(events)}건 검사, 오류 {len(errors)}건")
for err in errors: print(" -", err)
sys.exit(1 if errors else 0)
```

시공간 모순(4절 2·3항)은 위 형식 검사와 별도로 사건을 시간순 정렬한 뒤 인접 쌍의 장소·간격을 검사하는 절차를 추가 실행하라.

### 재구축 시 (연표 다시/업데이트)

기존 timeline.json이 존재하면 처음부터 다시 만들지 말고 증분 갱신하라 — 사건 id는 network.json의 `evidence_event_ids`와 citations가 참조하는 외래 키이므로, id가 바뀌면 하류 산출물의 참조가 일괄 끊어진다. 사건 추가는 새 id로, 수정은 id 유지, 삭제는 금지(부적격 사건은 `disputed` 또는 D등급 분리로). 갱신 후 반드시 검증 스크립트를 재실행하고 `meta.generated`를 갱신하라.

## 산출물 검증

확정 전 다음을 모두 통과해야 한다.

1. 검증 스크립트 실행 결과 형식 오류 0건 — 실행 로그를 보고서에 첨부하라.
2. 1896년 이전 사건 전수에 대해 `calendar` 필드가 의식적으로 판정되었는가 — 기본값으로 `solar`가 들어간 레코드가 없는가.
3. 음력→양력 변환 사건에 원본 표기 병기가 보존되어 있는가.
4. `disputed: true` 사건마다 `dispute_note`에 상충 출처가 요약되어 있고, conflicts.md와 상호 참조되는가.
5. `meta.source_files`의 모든 입력 파일이 실제 병합에 반영되었는가 — 입력 사건 수 합계와 병합·중복제거 후 수의 차이를 설명할 수 있는가.
6. 시간순 정렬 시 알려진 생애 골격(출생 1878 → 도미 1902 → 귀국 1907 → 망명 1910 → 상하이 1919 → 피체 1932 → 순국 1938)과 모순되는 사건이 없는가.
