#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
recheck_polish.py — 퇴고(polish) 후 사실 평면 incremental 재검 보조 도구.
fiction-fact-keeper 소유.

용법:
  1) 퇴고 전 스냅샷 기록:   python3 recheck_polish.py --snap
       → novel/_workshop/_snap/chapters_pre_polish.sha256 + .factplane.json 생성
  2) 퇴고 후 변경 진단:     python3 recheck_polish.py
       → 해시 변경 장 식별 + 각 장의 '사실 평면 토큰'(연도·날짜·인명·지명) 추가/삭제 diff.
       → 표현만 바뀐 장(사실 토큰 불변)은 [무사통과 후보], 사실 토큰 변동 장은 [전수 재검 필요]로 분류.

이 도구는 판정을 대신하지 않는다 — 변동 후보를 좁혀 keeper가 의미 검사할 대상을 가린다.
사실 평면 토큰: 4자리 연도, YYYY-MM(-DD), 검증 DB(network.json)의 인물·조직 표시명.
"""
import json
import os
import re
import sys
import hashlib
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
CHAP = os.path.abspath(os.path.join(HERE, "..", "chapters"))
SNAP = os.path.join(HERE, "_snap")
HASH_FILE = os.path.join(SNAP, "chapters_pre_polish.sha256")
FACT_FILE = os.path.join(SNAP, "chapters_pre_polish.factplane.json")
VER = os.path.abspath(os.path.join(HERE, "..", "..", "_workspace", "02_verified"))

YEAR = re.compile(r"(?<!\d)(18[789]\d|19[0-3]\d)(?!\d)")          # 1878~1939
DATE = re.compile(r"\b(18[789]\d|19[0-3]\d)[-.년]\s?\d{1,2}")     # 연-월


def person_names():
    """network.json에서 인물·조직 표시명을 모은다(사실 평면 토큰 후보)."""
    names = set()
    p = os.path.join(VER, "network.json")
    if not os.path.exists(p):
        return names
    net = json.load(open(p, encoding="utf-8"))
    nodes = net.get("nodes", net if isinstance(net, list) else [])
    for n in nodes:
        for k in ("label", "name", "display", "표시명", "id"):
            v = n.get(k) if isinstance(n, dict) else None
            if isinstance(v, str) and len(v) >= 2 and not v.startswith(("per-", "org-", "node-")):
                names.add(v)
    return names


def chapter_files():
    return sorted(f for f in os.listdir(CHAP) if re.match(r"ch\d+\.md$", f))


def factplane_tokens(text, names):
    toks = Counter()
    for y in YEAR.findall(text):
        toks["year:" + y] += 1
    for d in DATE.findall(text):
        toks["date:" + d] += 1
    for nm in names:
        c = text.count(nm)
        if c:
            toks["name:" + nm] = c
    return toks


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def do_snap():
    os.makedirs(SNAP, exist_ok=True)
    names = person_names()
    lines, fact = [], {}
    for fn in chapter_files():
        p = os.path.join(CHAP, fn)
        lines.append(f"{sha(p)}  novel/chapters/{fn}")
        fact[fn] = dict(factplane_tokens(open(p, encoding="utf-8").read(), names))
    open(HASH_FILE, "w").write("\n".join(sorted(lines)) + "\n")
    json.dump(fact, open(FACT_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"스냅샷 기록: {len(fact)}개 장 (해시 + 사실평면 토큰). names={len(names)}")


def do_diff():
    if not (os.path.exists(HASH_FILE) and os.path.exists(FACT_FILE)):
        print("스냅샷 없음 — 먼저 --snap 실행"); sys.exit(2)
    old_hash = {}
    for line in open(HASH_FILE):
        line = line.strip()
        if not line:
            continue
        h, p = line.split(None, 1)
        old_hash[os.path.basename(p)] = h
    old_fact = json.load(open(FACT_FILE, encoding="utf-8"))
    names = person_names()

    changed, factplane_changed = [], []
    print("=== 퇴고 후 incremental 진단 ===")
    for fn in chapter_files():
        p = os.path.join(CHAP, fn)
        if sha(p) == old_hash.get(fn):
            continue
        changed.append(fn)
        new_t = factplane_tokens(open(p, encoding="utf-8").read(), names)
        old_t = Counter(old_fact.get(fn, {}))
        added = {k: v for k, v in new_t.items() if v != old_t.get(k, 0)}
        removed = {k: old_t[k] for k in old_t if k not in new_t}
        delta = {k: (old_t.get(k, 0), new_t.get(k, 0))
                 for k in set(added) | set(removed)}
        if delta:
            factplane_changed.append(fn)
            print(f"\n[전수 재검 필요] {fn} — 사실평면 토큰 변동:")
            for k, (o, n) in sorted(delta.items()):
                print(f"    {k}: {o} → {n}")
        else:
            print(f"[무사통과 후보] {fn} — 본문 변경(표현)·사실평면 토큰 불변")

    print("\n--- 요약 ---")
    print(f"변경 장 {len(changed)}: {', '.join(changed) or '없음'}")
    print(f"사실평면 변동 장 {len(factplane_changed)}: "
          f"{', '.join(factplane_changed) or '없음 — 전 장 표현 수정으로 추정(keeper 확인 권고)'}")
    print("\n주의: 토큰 불변이라도 인물 동선·관계 해석 변경은 토큰으로 안 잡힐 수 있음 — "
          "변경 장은 keeper가 본문을 직접 의미 검사할 것.")


def main():
    if "--snap" in sys.argv:
        do_snap()
    else:
        do_diff()


if __name__ == "__main__":
    main()
