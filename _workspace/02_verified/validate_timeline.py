#!/usr/bin/env python3
"""timeline.json 전수 검증 스크립트 (timeline-analyst).

검사 항목 (timeline-construction S05 §4·§5):
 1. 스키마: 필수 필드, 날짜 형식(YYYY-MM-DD), precision/calendar 허용값, range는 end 필수
 2. 무결성: id 유일, meta.event_count 일치, 입력 263건 전수 계정(생존 ∪ merged_from), 출처 ≥1
 3. 시간: start <= end, 실존 달력 날짜, 생애 골격(출생 1878-11-09 ~ 순국 1938-03-10) — 사후 사건은 추서·이장·가족·단체 존속만 허용
 4. disputed: disputed=true ↔ dispute_note·dispute(adopted/variants) 존재
 5. 음양력: 1896 이전 사건의 calendar 의식적 판정 목록 출력(리뷰), lunar는 원본 병기 주석 확인
 6. 시공간: 안창호 본인의 정밀(span<=3일) 사건 쌍 전수 — 당대 교통수단 이동 가능성 검사
 7. geo_missing: 좌표 없는 사건 목록 (이동 경로 검사에서 제외된 건 보고)
종료 코드: 오류 1건이라도 있으면 1.
"""
import json, re, sys, itertools, math
from datetime import date, timedelta

PATH = "/Users/robin/Downloads/DOSAN/_workspace/02_verified/timeline.json"
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
BIRTH, DEATH = date(1878, 11, 9), date(1938, 3, 10)

data = json.load(open(PATH))
events = data["events"]
errors, warns = [], []

def parse(s):
    try:
        return date(*map(int, s.split("-")))
    except ValueError:
        return None

# ---------- 1·2·3·4: 스키마·무결성·시간·disputed ----------
ids = [e.get("id") for e in events]
if data["meta"]["event_count"] != len(events):
    errors.append("meta.event_count 불일치")
if len(ids) != len(set(ids)):
    errors.append("중복 id 존재")

alias = [m for e in events for m in e.get("merged_from", [])]
if len(alias) != len(set(alias)):
    errors.append("merged_from 중복 등재")
if set(ids) & set(alias):
    errors.append("생존 id가 merged_from에 동시 존재")
added = set(data["meta"].get("analyst_added_ids", []))
if added - set(ids):
    errors.append(f"meta.analyst_added_ids가 events에 없음: {added - set(ids)}")
if data["meta"].get("input_event_count") and len(ids) - len(added) + len(alias) != data["meta"]["input_event_count"]:
    errors.append(f"입력 사건 계정 불일치: 생존 {len(ids)} - 신규 {len(added)} + 병합 {len(alias)} != {data['meta']['input_event_count']}")

for e in events:
    eid = e.get("id", "?")
    d = e.get("date", {})
    if not e.get("id") or not e.get("title"):
        errors.append(f"{eid}: 필수 필드(id/title) 누락"); continue
    for k in ("summary", "place", "actors"):
        if k not in e:
            errors.append(f"{eid}: 필수 필드 {k} 누락")
    s, t = d.get("start"), d.get("end")
    if not s or not DATE_RE.match(s):
        errors.append(f"{eid}: start 형식 오류 ({s})")
    elif parse(s) is None:
        errors.append(f"{eid}: start 실존하지 않는 날짜 ({s})")
    if t is not None:
        if not DATE_RE.match(t):
            errors.append(f"{eid}: end 형식 오류 ({t})")
        elif parse(t) is None:
            errors.append(f"{eid}: end 실존하지 않는 날짜 ({t})")
        elif s and DATE_RE.match(s) and t < s:
            errors.append(f"{eid}: start > end")
    if d.get("precision") not in ("day", "month", "year", "range"):
        errors.append(f"{eid}: precision 허용값 위반 ({d.get('precision')})")
    if d.get("precision") == "range" and not t:
        errors.append(f"{eid}: precision=range인데 end 누락")
    if d.get("calendar") not in ("solar", "lunar"):
        errors.append(f"{eid}: calendar 허용값 위반 ({d.get('calendar')})")
    if not e.get("sources"):
        errors.append(f"{eid}: 출처 없음")
    else:
        for srn in e["sources"]:
            if not srn.get("type") or not srn.get("title"):
                errors.append(f"{eid}: source에 type/title 누락")
    if e.get("disputed"):
        if not e.get("dispute_note"):
            errors.append(f"{eid}: disputed인데 dispute_note 없음")
        dis = e.get("dispute") or {}
        if not dis.get("adopted") or not dis.get("variants"):
            errors.append(f"{eid}: disputed인데 dispute.adopted/variants 구조 없음")

# 생애 골격: 사후(1938-03-10 이후 시작) 사건 점검 — 허용 태그/제목 패턴 외 보고
POSTHUMOUS_OK = ("추서", "이장", "합장", "재판", "생애", "출생", "존속", "재건", "거주", "하우스")
for e in events:
    s = parse(e["date"]["start"]) if DATE_RE.match(e["date"]["start"] or "") else None
    if not s:
        continue
    # year/month/range의 start는 채움값이므로 day 정밀도만 출생 이전 위반으로 판정
    if s < BIRTH and e["date"]["precision"] == "day" and "안창호" in e.get("actors", []) \
            and "출생" not in e["title"] and "생애" not in e["title"]:
        errors.append(f"{e['id']}: 출생 이전 시작인데 안창호가 actor ({s})")
    if s > DEATH and "안창호" in e.get("actors", []):
        if not any(k in e["title"] for k in POSTHUMOUS_OK):
            errors.append(f"{e['id']}: 순국 이후 시작인데 사후 사건 패턴 아님 ({s}, {e['title'][:30]})")

# ---------- 5: 음양력 (1896 이전 — 의식적 판정 리뷰) ----------
pre1896 = [e for e in events if e["date"]["start"] < "1896-01-01"]
lunar_issues = []
for e in pre1896:
    if e["date"]["calendar"] == "lunar":
        body = (e.get("detail") or "") + (e.get("summary") or "")
        if "음력" not in body:
            errors.append(f"{e['id']}: calendar=lunar인데 원본 음력 병기 주석 없음")
print(f"[리뷰] 1896-01-01 이전 사건 {len(pre1896)}건의 calendar 판정:")
for e in pre1896:
    print(f"  {e['id']:<18} {e['date']['start']} {e['date']['precision']:<6} {e['date']['calendar']:<6} {e['title'][:36]}")

# ---------- 6: 시공간 모순 전수 검사 ----------
# 지명 -> 좌표 분류 (키워드 우선순위 순서 평가)
REGION = [
    ("샌프란시스코|상항", (37.77, -122.42)), ("로스앤젤레스|하이랜드|할리우드|파노라마", (34.05, -118.24)),
    ("리버사이드|파차파|헤멧", (33.95, -117.40)), ("뉴욕", (40.71, -74.01)),
    ("캘리포니아|미국 서부|미주", (36.0, -119.0)), ("멕시코|유카탄", (20.97, -89.62)),
    ("하와이|호놀룰루", (21.31, -157.86)), ("마닐라|필리핀", (14.60, 120.98)),
    ("도쿄|동경", (35.68, 139.69)), ("상하이|상해", (31.23, 121.47)),
    ("난징|남경", (32.06, 118.80)), ("베이징|북경|북평", (39.90, 116.40)),
    ("청도|칭다오", (36.07, 120.38)), ("위해위|웨이하이", (37.51, 122.12)),
    ("길림|지린", (43.84, 126.55)), ("밀산|봉밀산|만주|북중국", (45.55, 131.85)),
    ("블라디보스토크|해삼위|연해주|시베리아", (43.12, 131.89)),
    ("페테르부르크|베를린|런던|유럽", (52.52, 13.40)),
    ("평양|평안|강서|대동|선천|안악|진남포|대보산|송태산장", (39.03, 125.75)),
    ("인천|제물포", (37.46, 126.71)), ("대전", (36.33, 127.43)),
    ("한성|서울|경성|용산|종로|서대문|망우리|도산공원|행주|고양|제중원|혜화|삼선평|경기", (37.57, 126.98)),
    ("위해|한반도", (37.5, 127.0)),
]
def locate(e):
    p = e.get("place") or {}
    if p.get("lat") is not None and p.get("lng") is not None:
        return (p["lat"], p["lng"])
    name = (p.get("name") or "") + " " + (p.get("modern_name") or "")
    for pat, coord in REGION:
        if re.search(pat, name):
            return coord
    return None

def km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2-la1)/2)**2 + math.cos(la1)*math.cos(la2)*math.sin((lo2-lo1)/2)**2
    return 6371 * 2 * math.asin(math.sqrt(h))

# 당대 교통: 평균 800km/일(기선·철도), 300km 미만은 1일 내 이동 가능
def days_needed(dist):
    return 0 if dist < 300 else max(1, math.ceil(dist / 800))

# 안창호 본인 + 정밀 시간창 사건만 쌍별 비교 — month/year의 start와 넓은 range는
# 채움값/'그 안의 어느 시점'이므로 겹침이 곧 모순이 아님. 정밀 = day 또는 span<=3일 range.
# '부재 중' 사건(본인이 현장에 없는 선출 등)은 본인 이동 검사에서 제외.
geo_missing, tight = [], []
for e in events:
    if "안창호" not in e.get("actors", []):
        continue
    body = e["title"] + (e.get("summary") or "")
    if "부재 중" in body or "부재중" in body:
        continue
    prec = e["date"]["precision"]
    if prec not in ("day", "range"):
        continue
    s = parse(e["date"]["start"]); t = parse(e["date"]["end"]) if e["date"].get("end") else s
    if not s or s > DEATH:
        continue
    if prec == "range" and (t - s).days > 3:
        continue
    loc = locate(e)
    if loc is None:
        geo_missing.append(e["id"]); continue
    tight.append((e["id"], s, t, loc, e["title"][:30]))

tight.sort(key=lambda x: x[1])
conflicts = 0
for (id1, s1, t1, l1, ti1), (id2, s2, t2, l2, ti2) in itertools.combinations(tight, 2):
    gap = (s2 - t1).days if s2 > t1 else 0
    if gap > 30:
        continue
    dist = km(l1, l2)
    need = days_needed(dist)
    if gap < need:
        conflicts += 1
        errors.append(f"시공간 모순: {id1}({t1},{ti1}) -> {id2}({s2},{ti2}) 거리 {dist:.0f}km 필요 {need}일 실제 {gap}일")

print(f"\n[시공간] 정밀 사건 {len(tight)}건 쌍별 전수 검사 — 모순 {conflicts}건")
if geo_missing:
    print(f"[geo_missing] 좌표/지역 분류 불가로 이동 검사 제외 {len(geo_missing)}건: {geo_missing}")

# ---------- 결과 ----------
print(f"\n검사 대상 {len(events)}건 / disputed {sum(1 for e in events if e.get('disputed'))}건")
print(f"오류 {len(errors)}건, 경고 {len(warns)}건")
for x in errors:
    print(" [오류]", x)
for x in warns:
    print(" [경고]", x)
sys.exit(1 if errors else 0)
