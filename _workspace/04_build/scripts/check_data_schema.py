#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_data_schema.py — site/data/*.json 산출물 스키마·무결성 재검사 (data-engineer)
================================================================================

목적
----
build_data.py가 만든 `site/data/*.json`을 **독립적으로** 다시 읽어 스키마와
무결성을 재검증한다. build의 assert와 별개의 검사기로 두는 이유: 빌드 로직이
바뀌어도 소비 계약(consumer contract)은 이 파일이 고정 기준으로 지킨다.
Phase 4b(frontend/timeline/map developer)·Phase 5(qa-engineer)가 재사용한다.

검사 항목
--------
  1. 6개 파일 존재·JSON 파싱 가능
  2. timeline: 165건, D id 0, id 유일, disputed 17, precision/calendar 보존,
     date.precision 값 유효, 시기 코드 전건
  3. network: 노드 81·엣지 135, 끊어진 엣지 0, evidence가 렌더 사건만 참조,
     edge type 6분류, unconfirmed 19 분리
  4. citations: refs 155·sources 194, refs→source 끊어진 참조 0, source id 형식
  5. images: 80건, file 실재, 시기 8구간 ≥1
  6. search-index: (type,id) 유일, url 앵커 = 데이터 id 무변형
  7. meta: 수치 ↔ 실제 파일 레코드 수 정합 (00_common §3(iii) 자기 서술 검증)
  8. 교차 파일: timeline.id ↔ search url, network.id ↔ search url 일관

종료 코드: 통과 0 / 실패 1 (CI·QA 게이트에서 사용)
실행: python3 _workspace/04_build/scripts/check_data_schema.py

작성: data-engineer (23) / 2026-06-06
"""

import json
import os
import re
import sys
from collections import Counter

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
DATA = os.path.join(REPO_ROOT, "site", "data")
ASSETS = os.path.join(REPO_ROOT, "site", "assets", "images")

EXPECTED_D_IDS = {
    "evt-early-002", "evt-amer-009", "evt-amer-034", "evt-provgov-001",
    "evt-chrono-110", "evt-provgov-028", "evt-hsd-024",
}
EDGE_TYPES = {"family", "mentor", "comrade", "conflict", "patron", "membership"}
PERIODS = ["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8"]
PRECISIONS = {"day", "month", "year", "range"}

errors = []
checks = 0


def check(cond, msg):
    global checks
    checks += 1
    if not cond:
        errors.append(msg)


def load(name):
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        errors.append(f"파일 부재: {name}")
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:  # noqa
        errors.append(f"JSON 파싱 실패 {name}: {exc}")
        return None


def main():
    t = load("timeline.json")
    n = load("network.json")
    c = load("citations.json")
    im = load("images.json")
    a = load("archives.json")     # §3.5b
    m = load("meta.json")
    # D-23: search-index.json은 미산출이 정상 — 존재하면 보류 위반 경고
    if os.path.exists(os.path.join(DATA, "search-index.json")):
        errors.append("search-index.json 존재 — D-23 보류(미산출)인데 잔존 (정리 필요)")
    if errors:
        report()
        return

    # ---- timeline ----
    ev = t["events"]
    check(len(ev) == 165, f"timeline 165 아님: {len(ev)}")
    ids = [e["id"] for e in ev]
    check(len(set(ids)) == len(ids), "timeline id 중복")
    check(not (set(ids) & EXPECTED_D_IDS), "timeline에 D id 잔존")
    check(not any(e.get("confidence") == "D" for e in ev), "timeline D등급 잔존")
    check(sum(1 for e in ev if e.get("disputed")) == 17, "disputed 17 아님")
    for e in ev:
        check(e["date"].get("precision") in PRECISIONS,
              f"{e['id']} precision 무효: {e['date'].get('precision')}")
        check(e["date"].get("calendar") in ("solar", "lunar"),
              f"{e['id']} calendar 무효")
        check(e.get("period") in PERIODS, f"{e['id']} 시기 코드 무효")
        check("〔미확인〕" not in (e.get("title") or ""),
              f"{e['id']} 〔미확인〕 제목 잔존")
        # disputed면 dispute 구조 또는 dispute_note 동반
        if e.get("disputed"):
            check(e.get("dispute") is not None or e.get("dispute_note"),
                  f"{e['id']} disputed인데 dispute/dispute_note 부재")
        # D3 파생: actor_refs/org_refs 길이=원본, node_id 종류·실재 검증 (network 로드 후 재검사)
        if "actor_refs" in e:
            check(len(e["actor_refs"]) == len(e.get("actors", [])),
                  f"{e['id']} actor_refs 길이 불일치")
            check(len(e["org_refs"]) == len(e.get("orgs", [])),
                  f"{e['id']} org_refs 길이 불일치")

    # ---- network ----
    nodes = n["nodes"]
    edges = n["edges"]
    check(len(nodes) == 81, f"노드 81 아님: {len(nodes)}")
    check(len(edges) == 135, f"엣지 135 아님: {len(edges)}")
    check(len(n.get("edges_unconfirmed", [])) == 19, "unconfirmed 19 아님")
    nodeset = set(x["id"] for x in nodes)
    check(len(nodeset) == len(nodes), "노드 id 중복")
    render_ids = set(ids)
    for e in edges:
        check(e["source"] in nodeset, f"엣지 source 미존재: {e['source']}")
        check(e["target"] in nodeset, f"엣지 target 미존재: {e['target']}")
        check(e["type"] in EDGE_TYPES, f"엣지 type 6분류 위반: {e['type']}")
        for eid in e.get("evidence_event_ids", []):
            check(eid in render_ids,
                  f"엣지({e['source']}→{e['target']}) 비렌더 사건 참조: {eid}")
    for nd in nodes:
        check(nd.get("kind") in ("person", "org"), f"{nd['id']} kind 무효")

    # D3 파생 node_id 무결성: 비null node_id는 종류 맞고 실재해야 (끊어진 앵커 0)
    for e in ev:
        for ar in e.get("actor_refs", []):
            nid = ar.get("node_id")
            if nid is not None:
                check(nid.startswith("per-") and nid in nodeset,
                      f"{e['id']} actor_ref node_id 무효/미존재: {nid}")
        for orf in e.get("org_refs", []):
            nid = orf.get("node_id")
            if nid is not None:
                check(nid.startswith("org-") and nid in nodeset,
                      f"{e['id']} org_ref node_id 무효/미존재: {nid}")

    # ---- citations ----
    refs = c["refs"]
    sources = c["sources"]
    check(len(refs) == 155, f"refs 155 아님: {len(refs)}")
    check(len(sources) == 194, f"sources 194 아님: {len(sources)}")
    srcset = set(x["id"] for x in sources)
    check(len(srcset) == len(sources), "source id 중복")
    pat = re.compile(r"^src-(pri|aca|ins|enc|web)-\d+$")
    for sx in sources:
        check(pat.match(sx["id"]) is not None, f"source id 형식 위반: {sx['id']}")
    for r in refs:
        check(r["source_id"] in srcset,
              f"ref {r['id']} → 미존재 source: {r['source_id']}")

    # ---- images ----
    imgs = im["images"]
    check(len(imgs) == 80, f"이미지 80 아님: {len(imgs)}")
    iids = [x["id"] for x in imgs]
    check(len(set(iids)) == len(iids), "이미지 id 중복")
    for x in imgs:
        check(os.path.exists(os.path.join(ASSETS, x["file"])),
              f"이미지 파일 부재: {x['file']}")
    pcov = Counter(x.get("period") for x in imgs)
    for p in PERIODS:
        check(pcov.get(p, 0) >= 1, f"시기 {p} 이미지 0장")

    # ---- archives.json (§3.5b) ----
    cat = a["catalog"]
    check(len(cat) == 48, f"archives 48 아님: {len(cat)}")  # CQA-002: src-pri-048 증분(team-lead 2026-06-06)
    cids = [x["id"] for x in cat]
    check(len(set(cids)) == len(cids), "archives id 중복")
    apat = re.compile(r"^src-pri-\d+$")
    valid_status = {"confirmed", "cited_only", "unlocated"}
    for x in cat:
        check(apat.match(x["id"]) is not None, f"archives id 형식 위반: {x['id']}")
        check(x.get("location_status") in valid_status,
              f"{x['id']} location_status 무효: {x.get('location_status')}")
        for eid in x.get("related_event_ids", []) or []:
            check(eid in render_ids,
                  f"archives {x['id']} related_event 비렌더 참조: {eid}")

    # ---- meta 정합 (architecture.md §3.8 — 수치 ↔ 실제 레코드 수) ----
    mc = m["counts"]
    check(mc["events_rendered"] == len(ev), "meta events_rendered 불일치")
    check(mc["events_total"] == 172, "meta events_total 불일치")
    check(mc["events_excluded_d"] == 172 - len(ev), "meta events_excluded_d 불일치")
    check(mc["edges"] == len(edges), "meta edges 불일치")
    check(mc["edges_unconfirmed"] == len(n.get("edges_unconfirmed", [])),
          "meta edges_unconfirmed 불일치")
    check(mc["sources"] == len(sources), "meta sources 불일치")
    check(mc["primary_sources"] == len(cat), "meta primary_sources 불일치")
    check(mc["images"] == len(imgs), "meta images 불일치")
    check(mc["persons"] == sum(1 for x in nodes if x["kind"] == "person"),
          "meta persons 불일치")
    check(mc["orgs"] == sum(1 for x in nodes if x["kind"] == "org"),
          "meta orgs 불일치")
    check(mc["events_with_geo"] == sum(1 for e in ev if e.get("has_geo")),
          "meta events_with_geo 불일치")
    check(mc["events_disputed"] == sum(1 for e in ev if e.get("disputed")),
          "meta events_disputed 불일치")

    # ---- pages/*.json (D6) ----
    ref_re = re.compile(r"\[ref:(ref-\d+)\]")
    ref_ids = set(r["id"] for r in refs)
    expected_pages = {"home", "life", "timeline", "map", "organizations",
                      "philosophy", "people", "archives", "gallery", "references"}
    pages_dir = os.path.join(DATA, "pages")
    found_pages = set()
    block_types = {"paragraph", "blockquote", "table", "list", "slot"}
    for pid in expected_pages:
        path = os.path.join(pages_dir, pid + ".json")
        if not os.path.exists(path):
            errors.append(f"pages 파일 부재: {pid}.json")
            continue
        found_pages.add(pid)
        with open(path, encoding="utf-8") as f:
            pg = json.load(f)
        check(pg.get("page_id") == pid, f"{pid}.json page_id 불일치")
        check(bool(pg.get("title")), f"{pid}.json title 없음")
        check("sections" in pg and "lead" in pg, f"{pid}.json 구조 결함")
        # 블록 유형·앵커·마커 검사
        all_blocks = list(pg.get("lead", []))
        sec_ids = []
        for sec in pg.get("sections", []):
            sec_ids.append(sec.get("id"))
            check(sec.get("id") is not None, f"{pid} 섹션 id 없음")
            check(isinstance(sec.get("level"), int), f"{pid} 섹션 level 무효")
            all_blocks.extend(sec.get("blocks", []))
        check(len(sec_ids) == len(set(sec_ids)), f"{pid} 섹션 id 중복")
        for b in all_blocks:
            check(b.get("type") in block_types,
                  f"{pid} 블록 유형 무효: {b.get('type')}")
        # 본문 ref-NNN 마커가 전부 정의된 ref (끊어진 각주 0)
        blob = json.dumps(pg, ensure_ascii=False)
        for mk in ref_re.findall(blob):
            check(mk in ref_ids, f"{pid} 미정의 ref 마커: {mk}")
    check(found_pages == expected_pages,
          f"pages 누락: {sorted(expected_pages - found_pages)}")
    # life 장 앵커 보존 (교차링크 목적지)
    life_path = os.path.join(pages_dir, "life.json")
    if os.path.exists(life_path):
        with open(life_path, encoding="utf-8") as f:
            life = json.load(f)
        life_ids = set(sec["id"] for sec in life["sections"])
        for need in ("ch-01", "ch-15", "ch-gaps"):
            check(need in life_ids, f"life 앵커 누락: {need}")

    report()


def report():
    print("=" * 60)
    print("check_data_schema — site/data 무결성 재검사")
    print("=" * 60)
    print(f"검사 수행: {checks}")
    if errors:
        print(f"\n[FAIL] {len(errors)}건 결함:")
        for e in errors:
            print("  -", e)
        sys.exit(1)
    print("\n[PASS] 전 검사 통과 — site/data 무결성 확인")
    sys.exit(0)


if __name__ == "__main__":
    main()
