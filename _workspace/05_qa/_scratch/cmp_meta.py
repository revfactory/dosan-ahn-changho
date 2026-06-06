#!/usr/bin/env python3
"""Pass 7: meta.json statistics vs actual site/data records."""
import json
meta=json.load(open("/Users/robin/Downloads/DOSAN/site/data/meta.json"))
c=meta["counts"]; cg=meta["claim_grades"]; tc=meta["timeline_confidence"]

tl=json.load(open("/Users/robin/Downloads/DOSAN/site/data/timeline.json"))
nw=json.load(open("/Users/robin/Downloads/DOSAN/site/data/network.json"))
im=json.load(open("/Users/robin/Downloads/DOSAN/site/data/images.json"))
ci=json.load(open("/Users/robin/Downloads/DOSAN/site/data/citations.json"))
vtl=json.load(open("/Users/robin/Downloads/DOSAN/_workspace/02_verified/timeline.json"))
claims=json.load(open("/Users/robin/Downloads/DOSAN/_workspace/02_verified/claims_register.json"))

from collections import Counter
ev=tl["events"]
nodes=nw["nodes"]; edges=nw["edges"]; edges_unc=nw["edges_unconfirmed"]
imgs=im["images"]
sources=ci["sources"]; refs=ci["refs"]

def chk(label, claimed, actual):
    ok = "OK" if claimed==actual else "MISMATCH"
    print(f"  [{ok}] {label}: meta={claimed} actual={actual}")
    return claimed==actual

print("=== meta.counts vs actual ===")
results=[]
results.append(chk("events_total (verified)", c["events_total"], len(vtl["events"])))
results.append(chk("events_rendered (site timeline)", c["events_rendered"], len(ev)))
results.append(chk("events_excluded_d", c["events_excluded_d"], len(vtl["events"])-len(ev)))
results.append(chk("events_disputed (site)", c["events_disputed"], sum(1 for e in ev if e.get("disputed"))))
results.append(chk("events_with_geo", c["events_with_geo"], sum(1 for e in ev if e.get("has_geo") or (e.get("place",{}).get("lat") is not None))))
persons=sum(1 for n in nodes if n.get("kind")=="person")
orgs=sum(1 for n in nodes if n.get("kind")=="org")
results.append(chk("persons", c["persons"], persons))
results.append(chk("orgs", c["orgs"], orgs))
results.append(chk("edges", c["edges"], len(edges)))
results.append(chk("edges_unconfirmed", c["edges_unconfirmed"], len(edges_unc)))
results.append(chk("claims", c["claims"], len(claims)))
results.append(chk("sources", c["sources"], len(sources) if not isinstance(sources,list) else len(sources)))
prim=0
if isinstance(sources,dict):
    prim=sum(1 for s in sources.values() if (s.get("id") or "").startswith("src-pri") or s.get("type")=="primary")
results.append(chk("primary_sources (src-pri count)", c["primary_sources"], sum(1 for k in (sources.keys() if isinstance(sources,dict) else [s['id'] for s in sources]) if k.startswith("src-pri"))))
results.append(chk("images", c["images"], len(imgs)))
results.append(chk("refs (top-level)", meta["refs"], len(refs)))

print()
print("=== claim_grades vs claims_register ===")
gc=Counter(cl.get("grade") for cl in claims)
for g in ("A","B","C","D"):
    results.append(chk(f"grade {g}", cg[g], gc[g]))

print()
print("=== timeline_confidence vs VERIFIED timeline (172) ===")
vc=Counter(e.get("confidence") for e in vtl["events"])
print("  verified confidence dist:", dict(vc))
print("  NOTE: meta timeline_confidence A8/B106/C51 sums to 165 (rendered, D excluded)")
sc=Counter(e.get("confidence") for e in ev)
print("  site (rendered) confidence dist:", dict(sc))
for g in ("A","B","C"):
    results.append(chk(f"timeline_confidence {g} (rendered)", tc[g], sc.get(g,0)))

print()
print(f"TOTAL meta checks: {len(results)} | MISMATCHES: {sum(1 for r in results if not r)}")
