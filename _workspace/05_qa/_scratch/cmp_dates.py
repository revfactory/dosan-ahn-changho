#!/usr/bin/env python3
"""Pass 1: Full date/place/title/summary/detail comparison site vs verified timeline."""
import json
V=json.load(open("/Users/robin/Downloads/DOSAN/_workspace/02_verified/timeline.json"))["events"]
S=json.load(open("/Users/robin/Downloads/DOSAN/site/data/timeline.json"))["events"]
vd={e["id"]:e for e in V}
sd={e["id"]:e for e in S}

defects=[]
compared=0
for sid,se in sd.items():
    ve=vd.get(sid)
    if ve is None:
        defects.append(("FABRICATED-EVENT", sid, "site only, not in verified DB", "")); continue
    compared+=1
    # date object full compare
    sdate=se.get("date") or {}; vdate=ve.get("date") or {}
    for k in ("start","end","precision","calendar"):
        if sdate.get(k)!=vdate.get(k):
            defects.append(("DATE", sid, f"date.{k} site={sdate.get(k)!r}", f"verified={vdate.get(k)!r}"))
    # place
    sp=se.get("place") or {}; vp=ve.get("place") or {}
    for k in ("name","modern_name","lat","lng"):
        if sp.get(k)!=vp.get(k):
            defects.append(("PLACE", sid, f"place.{k} site={sp.get(k)!r}", f"verified={vp.get(k)!r}"))
    # title/summary/detail/dispute fields — exact compare
    for k in ("title","summary","detail","dispute_note","disputed","confidence","tags","actors","orgs"):
        if se.get(k)!=ve.get(k):
            defects.append(("FIELD:"+k, sid, f"site={str(se.get(k))[:120]!r}", f"verified={str(ve.get(k))[:120]!r}"))
print(f"Compared events: {compared}")
print(f"Total field-level mismatches: {len(defects)}")
from collections import Counter
print("By type:", dict(Counter(d[0] for d in defects)))
print()
for d in defects:
    print(" | ".join(str(x) for x in d))
json.dump(defects, open("/Users/robin/Downloads/DOSAN/_workspace/05_qa/_scratch/date_defects.json","w"), ensure_ascii=False, indent=1)
