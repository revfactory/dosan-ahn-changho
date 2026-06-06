#!/usr/bin/env python3
"""Pass 2: Broken footnote check — [ref:id] markers in render plane vs citations.json refs/sources."""
import json, re, glob, os

# Collect all [ref:id] markers from the render plane (pages JSON text + top-level data display fields)
ex=json.load(open("/Users/robin/Downloads/DOSAN/_workspace/05_qa/_scratch/extracted.json"))
REF_RE=re.compile(r"\[ref:([a-zA-Z0-9\-]+)\]")
markers=[]  # (refid, file, loc)
for grp in ("html","pages","data"):
    for f,loc,txt in ex[grp]:
        for m in REF_RE.findall(txt):
            markers.append((m,f,loc))

# Site citations.json
ci=json.load(open("/Users/robin/Downloads/DOSAN/site/data/citations.json"))
refs=ci["refs"]   # could be dict or list
if isinstance(refs,dict):
    ref_ids=set(refs.keys())
    ref_to_source={k:(v.get("source_id") or v.get("source") or v.get("src")) for k,v in refs.items()}
elif isinstance(refs,list):
    ref_ids=set(r["id"] for r in refs)
    ref_to_source={r["id"]:(r.get("source_id") or r.get("source") or r.get("src")) for r in refs}
sources=ci["sources"]
if isinstance(sources,dict):
    source_ids=set(sources.keys())
elif isinstance(sources,list):
    source_ids=set(s["id"] for s in sources)

used_refs=set(m[0] for m in markers)

print("=== REF MARKER INTEGRITY ===")
print(f"Total [ref:] marker occurrences in render plane: {len(markers)}")
print(f"Distinct ref ids used: {len(used_refs)}")
print(f"citations.json refs defined: {len(ref_ids)}")
print(f"citations.json sources defined: {len(source_ids)}")
print()

# (a) marker used but not defined => BROKEN
broken=sorted(used_refs - ref_ids)
print(f"[A] BROKEN markers (used but undefined in refs): {len(broken)}")
for b in broken:
    locs=[f"{f}>{loc}" for r,f,loc in markers if r==b][:3]
    print(f"   {b}  e.g. {locs}")
print()

# (b) ref defined but never used => orphan
orphan=sorted(ref_ids - used_refs)
print(f"[B] ORPHAN refs (defined but never used in render plane): {len(orphan)}")
for o in orphan[:40]: print(f"   {o}")
print()

# (c) ref -> source_id resolves to a real source
unresolved=[]
for rid in sorted(used_refs & ref_ids):
    sid=ref_to_source.get(rid)
    if sid is None or sid not in source_ids:
        unresolved.append((rid,sid))
print(f"[C] refs whose source_id does NOT resolve to a real source: {len(unresolved)}")
for rid,sid in unresolved[:40]: print(f"   {rid} -> source={sid!r}")
