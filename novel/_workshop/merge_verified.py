#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
merge_verified.py — 작가 분산 ledger(ledger_a/b.json)를 정본 scene_ledger.json에 병합하고
keeper가 PASS 판정한 장면에 verified=true를 기록한다.

verified 판정은 PASS_FILE(novel/_workshop/passed.txt — keeper가 관리하는 PASS 장 목록)으로 통제.
- passed.txt: 한 줄당 'chXX'(장 전체 PASS) 또는 'chXX-sY'(개별 장면 PASS).
- BLOCKED 목록(차단·회부)은 어떤 경우에도 verified=false 강제.

이 스크립트는 verified=true를 keeper의 명시적 PASS 목록에서만 켠다 — 작가 ledger의 verified 값은 무시.
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.abspath(os.path.join(HERE, "..", "ledger"))
PASS_FILE = os.path.join(HERE, "passed.txt")

# keeper가 verified를 절대 켜지 않는 장면(차단·회부 중)
BLOCKED = set()
# 전 회부·차단 해소(2026-06-07):
#   ch10-s1(시공간 §3-2) — 권고안 B 최종 채택·재검 PASS(2026-06-07, polish팀):
#                          시베리아 구간을 도산 단독 내면 추정장면으로 전환(동승 인물 완전 제거),
#                          송종익 약법 문답은 ch10-s4(1913 캘리포니아 창립 전야)에만 존치.
#                          ledger_b.json이 B 기준이며 본문 ch10.md도 B(도산 단독)와 정합.
#   ch10-s3(생몰)·ch08-s3(id)·ch09-s2(type) — 작가 수정 완료, 재검 PASS.


def load_passed():
    """passed.txt에서 PASS 장/장면 목록 로드. 주석(#)·빈 줄 무시."""
    ch_pass, scene_pass = set(), set()
    if not os.path.exists(PASS_FILE):
        return ch_pass, scene_pass
    for line in open(PASS_FILE, encoding="utf-8"):
        tok = line.split("#")[0].strip()
        if not tok:
            continue
        if re.fullmatch(r"ch\d+", tok):
            ch_pass.add(tok)
        elif re.fullmatch(r"ch\d+-s\d+", tok):
            scene_pass.add(tok)
    return ch_pass, scene_pass


def main():
    recs = {}
    for fn in ["ledger_a.json", "ledger_b.json"]:
        p = os.path.join(LEDGER, fn)
        if not os.path.exists(p):
            continue
        data = json.load(open(p, encoding="utf-8"))
        scenes = data.get("scenes", data) if isinstance(data, dict) else data
        for r in scenes:
            if r.get("scene_id"):
                recs[r["scene_id"]] = r

    ch_pass, scene_pass = load_passed()
    for sid, r in recs.items():
        ch = sid.split("-")[0]
        passed = (ch in ch_pass) or (sid in scene_pass)
        r["verified"] = bool(passed) and sid not in BLOCKED

    payload = {
        "meta": {
            "owner": "fiction-fact-keeper",
            "note": ("정본. verified=true는 keeper의 PASS 목록(passed.txt)에서만 기록 "
                     "— 기계검사 + 의미검사 PASS 전제. 차단/회부 장면은 verified=false."),
            "verified_count": sum(1 for r in recs.values() if r.get("verified")),
            "total": len(recs),
            "blocked": sorted(BLOCKED),
        },
        "scenes": [recs[s] for s in sorted(recs)],
    }
    out = os.path.join(LEDGER, "scene_ledger.json")
    json.dump(payload, open(out, "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print(f"정본 기록: {out}")
    print(f"  장면 {payload['meta']['total']} | verified {payload['meta']['verified_count']} | "
          f"차단·회부 {len(BLOCKED)}")


if __name__ == "__main__":
    main()
