#!/usr/bin/env python3
"""Classify each D-grade hit: AUTHORIZED (qualified/non-adopted/disputed) vs SUSPECT (bare assertion)."""
import json
hits=json.load(open("/Users/robin/Downloads/DOSAN/_workspace/05_qa/_scratch/dgrade_hits.json"))

# Authorized-framing markers anywhere in the surrounding text => OK
QUALIFIERS = ["전해진다","전한다","전해지","전승","라는 설","설과","설이","설로","병존","병기","갈린다","갈림","갈려","상충",
 "미확인","미해소","채택하지 않","싣지 않","사용하지 않","쓸 수 없","오기로 판정","기각","판정 불가","단정하지 않",
 "단정 서술 금지","미특정","미상","범위로","로 추정","추정","논쟁","양론","쟁점","회고","미확정","불명","않는다",
 "보류","대조 미완","대조 전","로 기록","서술이 있","서술한다","서술로","로 보는","계열은","따르면","따름","따른 것",
 "확인되지 않","확인이 안","확인하지 못","특정하지 못","적지 않는다","의 의심","의심","개연성","으로 본다","논의된다",
 "라고 한","듯","무렵","로 알려"]
# Fields that are pure metadata (not asserted-as-fact body) — title/place.name of a disputed event is structural
def classify(text):
    return "AUTHORIZED" if any(q in text for q in QUALIFIERS) else "SUSPECT"

suspects=[]
for clm,pr,f,loc,txt in hits:
    if classify(txt)=="SUSPECT":
        suspects.append((clm,pr,f,loc,txt))

print(f"Total hits: {len(hits)} | SUSPECT (no qualifier in same text unit): {len(suspects)}")
print()
for clm,pr,f,loc,txt in suspects:
    print(f"### {clm} [probe={pr!r}]")
    print(f"   {f} > {loc}")
    print(f"   {txt[:280]}")
    print()
