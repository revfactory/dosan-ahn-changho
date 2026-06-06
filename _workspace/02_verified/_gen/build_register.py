# -*- coding: utf-8 -*-
"""claims_register.json 빌더 — fact-checker
- 주장 데이터(claims_a/b/c) 병합, claim_id 부여
- sources: event_ids에 해당하는 사건 레코드 sources의 합집합(중복 제거) + 주장별 추가 출처(xs)
- 검증: JSON 유효성, claim_id 유일, grade/grade_reason 존재, event_ids 실재,
        A등급 primary 출처 포함, 전체 사건 레코드 커버리지
"""
import json, sys, os

BASE = "/Users/robin/Downloads/DOSAN/_workspace"
RESEARCH = os.path.join(BASE, "01_research")
OUT = os.path.join(BASE, "02_verified", "claims_register.json")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from claims_a import CLAIMS_A
from claims_b import CLAIMS_B
from claims_c import CLAIMS_C
from updates import UPDATES, NEW_CLAIMS

# 사건 레코드 로드
EVENT_FILES = ["chronology", "early-life", "america", "shinminhoe",
               "provisional-gov", "heungsadan", "philosophy"]
events = {}
for f in EVENT_FILES:
    for r in json.load(open(os.path.join(RESEARCH, f + "_events.json"))):
        events[r["id"]] = r
# 보완 라운드 산출 — 동일 id 존재 시 보강판으로 덮어씀 (출처 합집합이 최신 보강 기준이 되도록)
SUPPLEMENTS = ["chronology_events_supplement.json"]
for f in SUPPLEMENTS:
    p = os.path.join(RESEARCH, f)
    if os.path.exists(p):
        for r in json.load(open(p)):
            events[r["id"]] = r

all_claims = CLAIMS_A + CLAIMS_B + CLAIMS_C + NEW_CLAIMS
# 주의: 오버레이는 NEW_CLAIMS 병합 후 적용 — 신규 주장도 후속 재판정 대상이 되도록

# 재판정 오버레이 적용 (conflicts.md 채택 권고 반영 — 변경 이력은 reason에 내장)
upd_by_old = {u["old"]: u for u in UPDATES}
applied = set()
for c in all_claims:
    u = upd_by_old.get(c["text"])
    if u:
        applied.add(u["old"])
        c["g"] = u["g"]
        c["r"] = u["r"]
        if u.get("new"):
            c["text"] = u["new"]
        if u.get("ev"):
            c["ev"] = u["ev"]
unapplied = [u["old"][:50] for u in UPDATES if u["old"] not in applied]
if unapplied:
    print("경고 — 매칭 실패 오버레이:", len(unapplied))
    for x in unapplied:
        print("  MISS:", x)

register = []
errors = []
seen_texts = set()

for i, c in enumerate(all_claims, start=1):
    cid = f"clm-{i:04d}"
    evs = c["ev"]
    for e in evs:
        if e not in events:
            errors.append(f"{cid}: 존재하지 않는 event_id {e}")
    # sources 합집합 (type,title) 기준 중복 제거
    srcs, seen = [], set()
    for e in evs:
        for s in events.get(e, {}).get("sources", []):
            key = (s.get("type"), s.get("title"))
            if key not in seen:
                seen.add(key)
                srcs.append({"type": s.get("type"), "title": s.get("title"),
                             "locator": s.get("locator"), "url": s.get("url")})
    for s in c.get("xs", []):
        key = (s.get("type"), s.get("title"))
        if key not in seen:
            seen.add(key)
            srcs.append({"type": s.get("type"), "title": s.get("title"),
                         "locator": s.get("locator"), "url": s.get("url")})
    if not c.get("g") or c.get("g") not in "ABCD":
        errors.append(f"{cid}: grade 누락/비정상 — {c.get('g')}")
    if not c.get("r", "").strip():
        errors.append(f"{cid}: grade_reason 비어 있음")
    if c["g"] == "A" and not any(s["type"] == "primary" for s in srcs):
        errors.append(f"{cid}: A등급인데 primary 출처 없음")
    if c["text"] in seen_texts:
        errors.append(f"{cid}: text 중복 — {c['text'][:40]}")
    seen_texts.add(c["text"])
    register.append({"claim_id": cid, "text": c["text"], "event_ids": evs,
                     "grade": c["g"], "grade_reason": c["r"], "sources": srcs})

# 커버리지: 모든 사건 레코드가 최소 1개 주장에 등장하는가
covered = set()
for c in register:
    covered.update(c["event_ids"])
uncovered = sorted(set(events) - covered)

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(register, f, ensure_ascii=False, indent=1)

# 통계
from collections import Counter
dist = Counter(c["grade"] for c in register)
print(f"총 주장 수: {len(register)}")
print(f"등급 분포: A={dist['A']} B={dist['B']} C={dist['C']} D={dist['D']}")
print(f"검증 오류: {len(errors)}건")
for e in errors[:30]:
    print("  ERR:", e)
print(f"미커버 사건 레코드: {len(uncovered)}건")
for u in uncovered:
    print("  UNCOVERED:", u)
print(f"출력: {OUT}")
