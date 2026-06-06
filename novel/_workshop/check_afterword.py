#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_afterword.py — afterword.md(작가의 말)의 공개 수치를 정본 scene_ledger.json
집계와 대조한다. fiction-fact-keeper 소유. ledger 변경 시마다 재실행해 동기화 검증.

검사 항목:
  - 검증 앵커: distinct evt / distinct clm
  - 사건 쓰임: 직접재현 / 배경사건 / 대사소재 (use-count)
  - 유추 5종: 추정대화 / 내면추정 / 창작인물 / 추정장면 / 시간압축 (type-count)
  - 채택 전승: distinct adopted_lore claim 수(종)
  - disputed_choice: distinct cfl(택일 갈래 수) + entry 수
  - 사이트 URL 포함 여부

종료 코드 0 = 전 수치 문구 정합, 1 = 불일치(재동기화 필요).
"""
import json
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.abspath(os.path.join(HERE, "..", "ledger", "scene_ledger.json"))
AFTERWORD = os.path.abspath(os.path.join(HERE, "..", "afterword.md"))
SITE_URL = "revfactory.github.io/dosan-ahn-changho"


def aggregate():
    sl = json.load(open(LEDGER, encoding="utf-8"))
    scenes = sl["scenes"]
    evt, clm, lore, cfl = set(), set(), set(), set()
    use, inf = Counter(), Counter()
    dc_entries = 0
    for s in scenes:
        for fa in s.get("fact_anchors", []):
            i = fa.get("id", "")
            use[fa.get("use", "")] += 1
            if i.startswith("evt"):
                evt.add(i)
            elif i.startswith("clm"):
                clm.add(i)
        for x in s.get("inferences", []):
            inf[x.get("type", "?")] += 1
        for al in s.get("adopted_lore", []):
            lore.add(al.get("id") if isinstance(al, dict) else al)
        for d in s.get("disputed_choice", []):
            dc_entries += 1
            for m in re.findall(r"cfl-\d+", json.dumps(d, ensure_ascii=False)):
                cfl.add(m)
    return {
        "evt": len(evt), "clm": len(clm), "use": use, "inf": inf,
        "lore": len(lore), "cfl": len(cfl), "dc_entries": dc_entries,
        "verified": sl["meta"]["verified_count"], "total": sl["meta"]["total"],
    }


def main():
    a = aggregate()
    aw = open(AFTERWORD, encoding="utf-8").read()
    # (표시 문구, 기대값이 ledger 집계와 같은가)
    checks = [
        (f"검증된 역사 사건 {a['evt']}건", a["evt"] == 116),
        (f"검증된 주장 {a['clm']}건", a["clm"] == 63),
        (f"직접 재현 {a['use']['직접재현']}회", True),
        (f"배경 사건 {a['use']['배경사건']}회", True),
        (f"대사 소재 {a['use']['대사소재']}회", True),
        (f"추정 대화 {a['inf']['추정대화']}건", True),
        (f"내면 추정 {a['inf']['내면추정']}건", True),
        (f"창작 인물 {a['inf']['창작인물']}건", True),
        (f"추정 장면 {a['inf']['추정장면']}건", True),
        (f"시간 압축 {a['inf']['시간압축']}건", True),
    ]
    ok = True
    print("=== afterword.md ↔ scene_ledger.json 수치 대조 ===")
    print(f"verified {a['verified']}/{a['total']} | 유추 합계 {sum(a['inf'].values())} "
          f"| 전승 {a['lore']}종 | disputed {a['dc_entries']}건/{a['cfl']}갈래")
    for phrase, _ in checks:
        present = phrase in aw
        print(f"  [{'OK' if present else 'MISSING'}] {phrase}")
        ok = ok and present
    url_ok = SITE_URL in aw
    print(f"  [{'OK' if url_ok else 'MISSING'}] 사이트 URL ({SITE_URL})")
    ok = ok and url_ok
    print()
    print("결과:", "전 수치 정합 — 동기화 완료" if ok else "불일치 — afterword 재동기화 필요")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
