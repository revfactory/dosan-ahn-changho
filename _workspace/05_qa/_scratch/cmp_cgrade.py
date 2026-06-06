#!/usr/bin/env python3
"""Pass 4: C-grade qualifier check. C-grade body claims must carry a limiting marker."""
import json, re
claims=json.load(open("/Users/robin/Downloads/DOSAN/_workspace/02_verified/claims_register.json"))
cgrade=[c for c in claims if c.get("grade")=="C"]
print(f"C-grade claims: {len(cgrade)}")

# Extract distinctive probe (a quoted phrase or rare name+number) from each C claim text — heuristic:
# We instead scan BODY PROSE paragraphs for declarative sentences that assert facts WITHOUT any qualifier,
# focusing on whether the page-level qualifier discipline holds. Spot-check approach + global qualifier density.
ex=json.load(open("/Users/robin/Downloads/DOSAN/_workspace/05_qa/_scratch/extracted.json"))
QUAL=["전해진다","전한다","전해지","전승","라는 설","설이","설로","병존","병기","갈린다","갈려","상충","미확인","미해소",
 "추정","범위로","무렵","로 알려","듯","로 보인","개연성","로 기록","서술","따르면","논쟁","양론","쟁점","회고",
 "확인되지 않","확인하지 못","불명","미상","미특정","로 추정","않는다","경"]

# Count paragraphs that contain a date+ a factual verb but no qualifier and no ref (worst case: unsourced bare claim)
para=[(f,loc,txt) for f,loc,txt in ex["pages"] if loc.endswith(".text")]
REF=re.compile(r"\[ref:")
bare_unsourced=[]
for f,loc,txt in para:
    has_ref=bool(REF.search(txt))
    has_qual=any(q in txt for q in QUAL)
    # a factual sentence pattern (very rough): ends with declarative 했다/이다/되었다 and has a year
    declarative=re.search(r"(\d{4}년|\d{4})", txt) and re.search(r"(했다|이다|되었다|이었다|였다)\.?\s*($|\[)", txt)
    if declarative and not has_ref and not has_qual:
        bare_unsourced.append((f,loc,txt))
print(f"\nBODY paragraphs with year + declarative verb + NO ref + NO qualifier (potential bare claims): {len(bare_unsourced)}")
for f,loc,txt in bare_unsourced[:30]:
    print(f"  {f} > {loc}")
    print(f"     {txt[:200]}")
