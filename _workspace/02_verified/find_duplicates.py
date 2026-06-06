#!/usr/bin/env python3
"""중복 후보 탐지 — chronology 골격 vs 상세 연구원 레코드, 상세 연구원 간 교차.
날짜 구간 겹침(허용 오차 포함) + 텍스트/인물/장소 유사도로 후보 쌍을 점수화해 출력한다.
"""
import json, re, itertools
from datetime import date, timedelta

BASE = "/Users/robin/Downloads/DOSAN/_workspace/01_research/"
FILES = {
    "chrono": "chronology_events.json",
    "early": "early-life_events.json",
    "amer": "america_events.json",
    "shin": "shinminhoe_events.json",
    "provgov": "provisional-gov_events.json",
    "hsd": "heungsadan_events.json",
    "phil": "philosophy_events.json",
}

def parse(d):
    return date(*map(int, d.split("-")))

def span(e):
    d = e["date"]
    s = parse(d["start"])
    t = parse(d["end"]) if d.get("end") else s
    # precision에 따른 허용 오차
    pad = {"day": 3, "month": 31, "year": 366, "range": 15}[d["precision"]]
    return s - timedelta(days=pad), t + timedelta(days=pad)

def tokens(e):
    text = e["title"] + " " + e.get("summary", "")
    # 한글 2글자 이상 토큰
    return set(re.findall(r"[가-힣]{2,}", text))

def score(a, b):
    sa, ea = span(a); sb, eb = span(b)
    if ea < sb or eb < sa:
        return 0.0
    ta, tb = tokens(a), tokens(b)
    jac = len(ta & tb) / max(1, len(ta | tb))
    actors = len(set(a["actors"]) & set(b["actors"]))
    orgs = len(set(a.get("orgs", [])) & set(b.get("orgs", [])))
    place = 0
    pa, pb = a["place"]["name"] or "", b["place"]["name"] or ""
    if pa and pb and (pa in pb or pb in pa or len(set(re.findall(r"[가-힣]{2,}", pa)) & set(re.findall(r"[가-힣]{2,}", pb))) > 0):
        place = 1
    return jac * 10 + actors * 0.5 + orgs * 1.0 + place * 1.0

events = {}
for k, f in FILES.items():
    events[k] = json.load(open(BASE + f))

# 1) 골격 vs 상세
pairs = []
detail_keys = [k for k in FILES if k != "chrono"]
for c in events["chrono"]:
    for dk in detail_keys:
        for d in events[dk]:
            s = score(c, d)
            if s >= 2.0:
                pairs.append((s, c, d))

# 2) 상세 연구원 간 교차
cross = []
for ka, kb in itertools.combinations(detail_keys, 2):
    for a in events[ka]:
        for b in events[kb]:
            s = score(a, b)
            if s >= 2.0:
                cross.append((s, a, b))

def show(p, label):
    print(f"\n=== {label} ({len(p)}쌍) ===")
    for s, a, b in sorted(p, key=lambda x: -x[0]):
        print(f"[{s:5.2f}] {a['id']} {a['date']['start']}({a['date']['precision']}) {a['title'][:38]}")
        print(f"        {b['id']} {b['date']['start']}({b['date']['precision']}) {b['title'][:38]}")

show(pairs, "골격-상세 중복 후보")
show(cross, "상세 간 교차 중복 후보")
