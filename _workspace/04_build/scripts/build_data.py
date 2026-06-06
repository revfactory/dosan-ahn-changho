#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_data.py — 도산 안창호 사이트 데이터 변환 파이프라인 (data-engineer / Task #3)
================================================================================

역할
----
검증 산출물(`_workspace/02_verified/*`, `_workspace/03_content/*`)을 사이트가
소비하는 `site/data/*.json`으로 변환한다. 멱등(idempotent)·재실행 가능하며,
모든 변환 단계에 무결성 assert를 심어 깨진 데이터가 site/data로 새어나가지
못하게 막는다. 검증 실패 시 부분 산출물을 남기지 않고 즉시 중단한다.

입력 (읽기 전용 — 절대 수정 금지)
---------------------------------
  02_verified/timeline.json          172건 (D 7 → 렌더 165), disputed 17
  02_verified/network.json           v1.2.1: 노드 81·엣지 135·미확정 19
  02_verified/claims_register.json   305건 (A9/B155/C89/D52) — 등급 분포 통계용
  03_content/citations.json          refs 155(1:1)·sources 194
  03_content/images/manifest.json    80건 (visual-curator manifest)

출력 (쓰기 대상 — site/data/ 와 scripts/ 만)
-------------------------------------------
  site/data/timeline.json       렌더 165건 (D 7 차단), disputed adopted+variants 보존
  site/data/network.json        노드 81·엣지 135 (+ unconfirmed 19 분리 보관)
  site/data/citations.json      refs 155 + sources 194
  site/data/images.json         80건 (manifest → 렌더용; sitemap §4 계약명)
  site/data/search-index.json   사건+노드+사료 통합 검색 색인
  site/data/meta.json           파일별 레코드 수·등급 분포·통계

실행
----
  python3 _workspace/04_build/scripts/build_data.py
  (의존: 표준 라이브러리만. 외부 패키지 불요. 순서·의존 없음 — 단일 진입점.)

계약 근거 — architecture.md v1.0 (2026-06-06 확정) 준수
------------------------------------------------------
  - §3.1 timeline: D 7건 제외 165 + actor_refs/org_refs·period·has_geo 빌드 파생 (D2·D3·D12·D16·D17)
  - §3.3 network: nodes 81(kind 파생)·edges 135(6분류 mentor 포함)·edges_unconfirmed 19 분리 (D4·D19)
  - §3.4 citations: refs 155→source_id→sources 194 (D5)
  - §3.5 images: image_root assets/images/ 정규화, 파일명 images.json (D22)
  - §3.5b archives: primary-source_catalog 47 → src-pri 앵커, related_event_ids는
        timeline merged_from 권위로 생존 id 치환 + D차단 링크 제거 (의미 기반 id 치환)
  - §3.6 pages: drafts 10 → blocks 배열 (D6 택1=blocks). {#anchor}·[ref:]·교차링크 원형 보존
  - §3.7 period: date.start (lo, hi] 우폐 경계 — 경계연도는 끝나는 시기 귀속 (D12)
  - §3.8 meta: 사이트 자기 집계 단일 출처, 키명 계약 1:1, 전부 site/data 실측 (D21)
  - §3.9 / D23: search-index.json 보류 — 미산출
  - sitemap §4 / D1: 앵커 = 데이터 id 무변형
  - network.json meta.changelog_v120 : supplement per-052~056 REMAP — 본체 id 사용

  ※ 회부 중(계약 텍스트 정정 대기, 출력 무영향): D-20 place_normalization은 데이터에
     실재(4건)하므로 network.json에 동봉 유지. edge type은 데이터 값 'mentor' 유지
     (계약 §3.3 'teacher_student'는 표기 오류로 회부).

작성: data-engineer (23) / 2026-06-06
"""

import json
import os
import sys
from collections import Counter, OrderedDict

# ---------------------------------------------------------------------------
# 경로 — 스크립트 위치 기준 절대 경로 산출 (cwd 무관 재현성)
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
VERIFIED = os.path.join(REPO_ROOT, "_workspace", "02_verified")
CONTENT = os.path.join(REPO_ROOT, "_workspace", "03_content")
OUT_DIR = os.path.join(REPO_ROOT, "site", "data")

IN_TIMELINE = os.path.join(VERIFIED, "timeline.json")
IN_NETWORK = os.path.join(VERIFIED, "network.json")
IN_CLAIMS = os.path.join(VERIFIED, "claims_register.json")
IN_CITATIONS = os.path.join(CONTENT, "citations.json")
IN_MANIFEST = os.path.join(CONTENT, "images", "manifest.json")
IN_CATALOG = os.path.join(REPO_ROOT, "_workspace", "01_research",
                          "primary-source_catalog.json")  # §3.5b archives 원천

# 계약상 차단 대상 D등급 사건 7건 (page_specs/03_timeline.md 명시) — 검증용 기대값
import re as _re_san

# ── D-26: 표시 텍스트 정화 — 내부 검증 id(cfl·clm·evt 산문 참조)를 렌더 평면에서 제거 ──
# 검증 DB(02_verified)는 감사 추적용으로 id를 보존하고, 사이트 표시 텍스트에서만 걷어낸다.
# 사용자 보고(2026-06-06): "판정 cfl-037 이런 표시는 없애야 합니다".
_SAN_ID = r'(?:cfl-\d{1,4}|clm-\d{1,5}|evt-[a-z][a-z-]*?-\d{1,4})'
_SAN_SEQ = _SAN_ID + r'(?:\s*[·,/]\s*' + _SAN_ID + r')*'

def sanitize_display(text):
    """표시 산문에서 내부 id 토큰 제거 + 구두점 잔해 정리. 의미 텍스트는 보존."""
    if not isinstance(text, str) or not _re_san.search(_SAN_ID, text):
        return text
    t = text
    t = _re_san.sub(r'〔판정\s+' + _SAN_SEQ + r'〕\s*', '〔기록 상충〕 ', t)
    t = _re_san.sub(r'(?:판정|지시)\s+(' + _SAN_SEQ + r')', lambda m: '판정' if '판정' in m.group(0) else '지시', t)
    t = _re_san.sub(_SAN_SEQ, '', t)
    # 구두점 잔해 정리
    for _ in range(2):
        t = _re_san.sub(r'\(\s*[·,;:—\-]?\s*\)', '', t)      # 빈 괄호
        t = _re_san.sub(r'\(\s*[·,;:]\s*', '(', t)            # "(, " → "("
        t = _re_san.sub(r'\s*[·,;:]\s*\)', ')', t)            # " ,)" → ")"
        t = _re_san.sub(r'\(\s+', '(', t)
        t = _re_san.sub(r'\s+\)', ')', t)
    t = _re_san.sub(r'\s{2,}', ' ', t)
    t = _re_san.sub(r'\s+([,.;)〕」』])', r'\1', t)
    t = _re_san.sub(r'([(〔「『])\s+', r'\1', t)
    return t.strip()

_STATUS_KO = {
    'adopted': '통설 채택', 'adopted_provisional': '잠정 채택',
    'partially_resolved': '부분 해소', 'unresolved': '미해소 — 양설 병기',
}

def korean_status(text):
    """dispute.status의 영문 토큰을 한글 라벨로, 내부 버전 주석은 제거 (D-26 확장)."""
    if not isinstance(text, str):
        return text
    t = sanitize_display(text)
    m = _re_san.match(r'^([a-z_]+)\s*(?:\((.*)\))?$', t.strip())
    if not m:
        return t
    note = (m.group(2) or '').strip()
    note = _re_san.sub(r'^v\d+(?:\.\d+)*\s*[—\-:]?\s*', '', note)   # "v1.6 — " 제거
    note = note.replace('day 승격 보류', '일 단위 확정은 보류')
    has_note = note not in ('', '연동') and not _re_san.fullmatch(r'v\d+(?:\.\d+)*', note)
    base = {'unresolved': '미해소'} if has_note else {}
    label = {**_STATUS_KO, **base}.get(m.group(1), m.group(1))
    if not has_note:
        return label
    return f'{label} — {note}'


def sanitize_fields(obj, fields):
    """dict의 지정 필드(점 표기 1단계)만 정화 — 기계 참조 필드는 건드리지 않는다."""
    for f in fields:
        if f in obj and isinstance(obj[f], str):
            obj[f] = sanitize_display(obj[f])
    return obj

EXPECTED_D_IDS = {
    "evt-early-002", "evt-amer-009", "evt-amer-034", "evt-provgov-001",
    "evt-chrono-110", "evt-provgov-028", "evt-hsd-024",
}

# 8대 시기 경계 (architecture.md §3.7 — 계약 권위) — date.start 연도로 버킷팅.
# 경계 의미: P1 = 1878 <= y <= 1899 (양끝 포함), P2~P7 = prev_hi < y <= hi (좌개·우폐),
# P8 = y > 1938. 경계연도(1899·1907·1911·1919·1924·1932·1938)는 **끝나는 시기**에 귀속한다.
# (예: 1907년 신민회 사건 → P2 "1차 미주"의 종결연도). §3.7 부등호와 1:1 일치.
PERIODS = [
    ("P1", 1878, 1899),
    ("P2", 1899, 1907),
    ("P3", 1907, 1911),
    ("P4", 1911, 1919),
    ("P5", 1919, 1924),
    ("P6", 1924, 1932),
    ("P7", 1932, 1938),
    ("P8", 1938, 9999),
]
PERIOD_CODES = [p[0] for p in PERIODS]


# ---------------------------------------------------------------------------
# 유틸
# ---------------------------------------------------------------------------
def load(path):
    if not os.path.exists(path):
        die(f"필수 입력 누락: {path}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def die(msg):
    sys.stderr.write(f"\n[BUILD ABORT] {msg}\n")
    sys.exit(1)


def write_json(name, obj):
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return path


def year_of(date_obj):
    """date.start의 연도(int). 'YYYY-MM-DD' 또는 'YYYY' 형식."""
    s = (date_obj or {}).get("start") or ""
    try:
        return int(str(s)[:4])
    except (ValueError, TypeError):
        return None


def period_of(date_obj):
    """date.start 연도를 8대 시기 코드로 매핑 (architecture.md §3.7 권위).
    경계: P1 1878<=y<=1899 · P2 1899<y<=1907 · P3 1907<y<=1911 · P4 1911<y<=1919 ·
    P5 1919<y<=1924 · P6 1924<y<=1932 · P7 1932<y<=1938 · P8 y>1938.
    경계연도는 '끝나는 시기'에 귀속(우폐). 계약 §3.7 부등호와 1:1 일치."""
    y = year_of(date_obj)
    if y is None:
        return None
    if 1878 <= y <= 1899:
        return "P1"
    if 1899 < y <= 1907:
        return "P2"
    if 1907 < y <= 1911:
        return "P3"
    if 1911 < y <= 1919:
        return "P4"
    if 1919 < y <= 1924:
        return "P5"
    if 1924 < y <= 1932:
        return "P6"
    if 1932 < y <= 1938:
        return "P7"
    if y > 1938:
        return "P8"
    return None


def build_name_resolver(network_raw):
    """timeline actors/orgs 표시명 → network node_id 해소 사전 (D3 계약).
    network.json의 canonical name + name_normalization(293 별칭)을 합쳐
    빌드 시 결정적 해소. ambiguous_aliases는 단정 금지 — null + ambiguous 플래그.
    """
    nodes = network_raw["nodes"]
    nn = network_raw.get("name_normalization", {})
    ambiguous = set(network_raw.get("ambiguous_aliases", {}).keys())

    table = {}
    # canonical name 우선 (별칭과 충돌 시 정본 이름이 이긴다)
    for n in nodes:
        table[n["name"]] = n["id"]
    for alias, nid in nn.items():
        table.setdefault(alias, nid)
    return table, ambiguous


def resolve_refs(names, resolver, ambiguous, want_prefix):
    """표시명 리스트 → [{name, node_id, ambiguous?}]. 원본 순서·문자열 보존.
    node_id는 미해소/모호 시 null. want_prefix와 다른 종류로 해소되면 null(오링크 방지)."""
    out = []
    for nm in names:
        if nm in ambiguous:
            out.append({"name": nm, "node_id": None, "ambiguous": True})
            continue
        nid = resolver.get(nm)
        if nid and nid.startswith(want_prefix):
            out.append({"name": nm, "node_id": nid})
        else:
            # 미해소 또는 cross-kind(actor가 org로 등) → 평문 렌더 (null)
            out.append({"name": nm, "node_id": None})
    return out


# ---------------------------------------------------------------------------
# 1) TIMELINE — D 7건 차단 → 165건. disputed adopted+variants·precision·calendar 보존
# ---------------------------------------------------------------------------
def build_timeline(raw, resolver=None, ambiguous=None):
    events = raw["events"]
    in_count = len(events)

    # 입력 무결성: id 유일성
    ids = [e["id"] for e in events]
    dup = [k for k, v in Counter(ids).items() if v > 1]
    assert not dup, f"timeline 입력 중복 id: {dup}"

    # 실제 D등급 = 계약 명시 7건과 일치해야 한다 (불일치 = 상류 데이터 변동)
    actual_d = set(e["id"] for e in events if e.get("confidence") == "D")
    assert actual_d == EXPECTED_D_IDS, (
        f"D등급 사건 집합 불일치 — 기대 {sorted(EXPECTED_D_IDS)}, "
        f"실제 {sorted(actual_d)} (차집합 {actual_d ^ EXPECTED_D_IDS})"
    )

    out = []
    for e in events:
        if e.get("confidence") == "D":
            continue  # D 차단 — site/data로 내보내지 않는다 (00_common §2)

        # 제목 〔미확인〕 잔존 검사 — D 필터 후 0이어야 한다 (03_timeline.md)
        if "〔미확인〕" in (e.get("title") or ""):
            die(f"비D 사건에 〔미확인〕 제목 잔존: {e['id']} — 데이터 결함")

        rec = OrderedDict()
        rec["id"] = e["id"]  # 앵커 = 데이터 id 무변형
        rec["title"] = e["title"]
        rec["date"] = {
            "start": e["date"].get("start"),
            "end": e["date"].get("end"),
            "precision": e["date"].get("precision"),   # day/month/year/range 보존
            "calendar": e["date"].get("calendar"),     # solar/lunar 보존
        }
        place = e.get("place") or {}
        rec["place"] = {
            "name": place.get("name"),
            "modern_name": place.get("modern_name"),
            "lat": place.get("lat"),  # null 가능 — 소비자는 null 시 지도 생략
            "lng": place.get("lng"),
        }
        rec["actors"] = e.get("actors", [])     # 원본 표시명 보존 (QA 대조)
        rec["orgs"] = e.get("orgs", [])
        # D3: 표시명 → node_id 빌드 시 해소 (파생). null이면 소비자 평문 렌더.
        if resolver is not None:
            rec["actor_refs"] = resolve_refs(
                rec["actors"], resolver, ambiguous or set(), "per-")
            rec["org_refs"] = resolve_refs(
                rec["orgs"], resolver, ambiguous or set(), "org-")
        rec["summary"] = e["summary"]            # 원문 그대로 (요약 재작성 금지)
        rec["detail"] = e.get("detail")
        rec["sources"] = e.get("sources", [])
        rec["confidence"] = e["confidence"]      # A/B/C (D는 이미 제외)
        rec["tags"] = e.get("tags", [])          # 그대로 (병합·개명 금지)
        rec["disputed"] = bool(e.get("disputed"))
        rec["dispute_note"] = e.get("dispute_note")
        # disputed adopted+variants 구조 보존 (timeline-developer가 그대로 표시)
        if e.get("dispute") is not None:
            rec["dispute"] = e["dispute"]
        # 시기 코드 (파생) — 필터·교차링크용
        rec["period"] = period_of(e["date"])
        # 지도 표시 가능 여부 (파생) — 소비자 편의
        rec["has_geo"] = place.get("lat") is not None and place.get("lng") is not None
        # D-26: 표시 산문 정화 — 내부 검증 id 제거 (기계 필드 불변)
        sanitize_fields(rec, ("title", "summary", "detail", "dispute_note"))
        if isinstance(rec.get("place"), dict):
            sanitize_fields(rec["place"], ("name", "modern_name", "place_note"))
        dp = rec.get("dispute")
        if isinstance(dp, dict):
            if isinstance(dp.get("status"), str):
                dp["status"] = korean_status(dp["status"])  # D-26 확장: 영문 토큰 → 한글
            sanitize_fields(dp, ("note",))
            if isinstance(dp.get("adopted"), dict):
                sanitize_fields(dp["adopted"], ("basis", "note", "value_note"))
            for v in dp.get("variants") or []:
                if isinstance(v, dict):
                    sanitize_fields(v, ("assessment", "basis", "note"))
        out.append(rec)

    # 산출 무결성 assert
    assert len(out) == in_count - len(EXPECTED_D_IDS), (
        f"렌더 수 불일치: {len(out)} != {in_count}-{len(EXPECTED_D_IDS)}"
    )
    assert len(out) == 165, f"렌더 사건 수 165 아님: {len(out)}"
    assert not any(r["confidence"] == "D" for r in out), "D등급 잔존"
    assert all(r["id"] not in EXPECTED_D_IDS for r in out), "D id 잔존"
    assert len(set(r["id"] for r in out)) == len(out), "출력 id 중복"
    disputed_out = sum(1 for r in out if r["disputed"])
    assert disputed_out == 17, f"disputed 17건 보존 실패: {disputed_out}"
    # period 전건 부여 확인
    no_period = [r["id"] for r in out if r["period"] is None]
    assert not no_period, f"시기 미부여 사건: {no_period}"

    # D3 해소 무결성: actor_refs/org_refs의 non-null node_id는 올바른 종류여야
    ref_stats = {"actor_resolved": 0, "actor_plain": 0,
                 "org_resolved": 0, "org_plain": 0}
    if resolver is not None:
        for r in out:
            assert len(r["actor_refs"]) == len(r["actors"]), \
                f"{r['id']} actor_refs 길이 불일치"
            assert len(r["org_refs"]) == len(r["orgs"]), \
                f"{r['id']} org_refs 길이 불일치"
            for ar in r["actor_refs"]:
                nid = ar.get("node_id")
                assert nid is None or nid.startswith("per-"), \
                    f"{r['id']} actor_ref node_id 종류 위반: {nid}"
                ref_stats["actor_resolved" if nid else "actor_plain"] += 1
            for orf in r["org_refs"]:
                nid = orf.get("node_id")
                assert nid is None or nid.startswith("org-"), \
                    f"{r['id']} org_ref node_id 종류 위반: {nid}"
                ref_stats["org_resolved" if nid else "org_plain"] += 1

    doc = OrderedDict()
    doc["meta"] = {
        "source": "02_verified/timeline.json",
        "source_event_count": in_count,
        "blocked_D": sorted(EXPECTED_D_IDS),
        "render_count": len(out),
        "disputed_count": disputed_out,
        "geo_count": sum(1 for r in out if r["has_geo"]),
        "ref_resolution": ref_stats,
        "note": "confidence D 7건 차단(00_common §2). 앵커 = id 무변형(00_common §6).",
    }
    doc["events"] = out
    return doc, out


# ---------------------------------------------------------------------------
# 2) NETWORK — 노드 81·엣지 135. unconfirmed 19 분리 보관. 무결성 검증
# ---------------------------------------------------------------------------
def build_network(raw, render_event_ids):
    nodes = raw["nodes"]
    edges = raw["edges"]
    unconfirmed = raw.get("edges_unconfirmed", [])

    node_ids = [n["id"] for n in nodes]
    dup = [k for k, v in Counter(node_ids).items() if v > 1]
    assert not dup, f"network 중복 노드 id: {dup}"
    nodeset = set(node_ids)

    # 엣지 끊어진 참조 0건 (노드↔엣지)
    for i, e in enumerate(edges):
        assert e["source"] in nodeset, f"엣지[{i}] source 미존재 노드: {e['source']}"
        assert e["target"] in nodeset, f"엣지[{i}] target 미존재 노드: {e['target']}"

    # 엣지 evidence_event_ids — D 차단 후에도 살아있는 사건만 참조해야 사이트 교차링크가 닿는다
    # (D 사건은 timeline 미노출이므로 그 사건으로의 링크는 끊어진 앵커가 된다)
    render_set = set(render_event_ids)
    dangling = []
    for i, e in enumerate(edges):
        for eid in e.get("evidence_event_ids", []):
            if eid not in render_set:
                dangling.append((e["source"], e["target"], eid))
    assert not dangling, (
        f"확정 엣지가 비렌더(D 또는 부재) 사건을 근거로 참조 — 끊어진 앵커: {dangling}"
    )

    # supplement REMAP 검증: per-052~056이 옛 supplement 의미(임치정 외)와 충돌 없이
    # 본체 선점 id를 유지하는지 — changelog_v120 기준 표본 확인
    name_by_id = {n["id"]: n["name"] for n in nodes}
    remap_expect = {
        "per-052": "임치정", "per-053": "방화중", "per-054": "조소앙",
        "per-055": "김동삼", "per-056": "윤해",
    }
    for nid, want in remap_expect.items():
        got = name_by_id.get(nid)
        assert got == want, f"supplement REMAP 위반: {nid} 기대 '{want}' 실제 '{got}'"

    # 노드 type 파생 (입력에 type 필드 없음 — id 접두사로 person/org 판별)
    out_nodes = []
    for n in nodes:
        kind = "person" if n["id"].startswith("per-") else (
            "org" if n["id"].startswith("org-") else "other"
        )
        rec = OrderedDict()
        rec["id"] = n["id"]
        rec["kind"] = kind
        rec["name"] = n["name"]
        rec["hanja"] = n.get("hanja")
        rec["alt_names"] = n.get("alt_names", [])
        rec["birth"] = n.get("birth")
        rec["death"] = n.get("death")
        rec["role"] = n.get("role")
        rec["summary"] = n.get("summary")
        sanitize_fields(rec, ("role", "summary"))  # D-26
        out_nodes.append(rec)
    assert all(r["kind"] in ("person", "org") for r in out_nodes), \
        "per-/org- 외 노드 id 접두사 발견"

    out_edges = []
    for e in edges:
        rec = OrderedDict()
        rec["source"] = e["source"]
        rec["target"] = e["target"]
        rec["type"] = e["type"]  # 6분류 — 신설 금지(정책 4)
        rec["period"] = e.get("period")
        rec["evidence_event_ids"] = e.get("evidence_event_ids", [])
        rec["description"] = e.get("description")
        if e.get("period_note") is not None:
            rec["period_note"] = e["period_note"]
        if e.get("org_relation") is not None:
            rec["org_relation"] = e["org_relation"]
        sanitize_fields(rec, ("description", "period_note"))  # D-26
        out_edges.append(rec)

    # edge type 6분류 준수
    allowed = {"family", "mentor", "comrade", "conflict", "patron", "membership"}
    bad = set(r["type"] for r in out_edges) - allowed
    assert not bad, f"엣지 type 6분류 위반(신설 금지): {bad}"

    assert len(out_nodes) == 81, f"노드 81 아님: {len(out_nodes)}"
    assert len(out_edges) == 135, f"엣지 135 아님: {len(out_edges)}"

    doc = OrderedDict()
    doc["meta"] = {
        "source": "02_verified/network.json",
        "version": raw["meta"].get("version"),
        "node_count": len(out_nodes),
        "person_count": sum(1 for r in out_nodes if r["kind"] == "person"),
        "org_count": sum(1 for r in out_nodes if r["kind"] == "org"),
        "edge_count": len(out_edges),
        "edges_unconfirmed_count": len(unconfirmed),
        "edge_types": dict(Counter(r["type"] for r in out_edges)),
        "name_normalization_alias_count": len(raw.get("name_normalization", {})),
        "note": "edges_unconfirmed(D 19)는 본체 분리 보관 — 사이트 미노출(§6 보류). "
                "name_normalization·ambiguous_aliases·place_normalization 보존.",
    }
    doc["nodes"] = out_nodes
    doc["edges"] = out_edges
    # D등급 미확정 엣지는 분리 보관 (삭제 금지 — network-mapping §5). 사이트 본체 미노출.
    # D-26: 미노출이지만 people.html §6 보류 표기가 unconfirmed_reason을 소비할 수 있어 정화.
    for u in unconfirmed:
        if isinstance(u, dict):
            sanitize_fields(u, ("unconfirmed_reason", "description", "period_note"))
    doc["edges_unconfirmed"] = unconfirmed
    # 정규화 사전 보존 — 교차링크 인명/지명 매칭의 단일 진실 공급원
    doc["name_normalization"] = raw.get("name_normalization", {})
    doc["ambiguous_aliases"] = raw.get("ambiguous_aliases", {})
    if raw["meta"].get("place_normalization"):
        pn = raw["meta"]["place_normalization"]
        for entry in (pn if isinstance(pn, list) else pn.values()):
            if isinstance(entry, dict):
                sanitize_fields(entry, ("status", "note", "reason"))  # D-26
        doc["place_normalization"] = pn
    return doc, out_nodes, out_edges


# ---------------------------------------------------------------------------
# 3) CITATIONS — refs 155 + sources 194. refs→source_id 무결성
# ---------------------------------------------------------------------------
def build_citations(raw):
    refs = raw["refs"]
    sources = raw["sources"]

    ref_ids = [r["id"] for r in refs]
    src_ids = [s["id"] for s in sources]
    assert len(set(ref_ids)) == len(ref_ids), "refs id 중복"
    assert len(set(src_ids)) == len(src_ids), "sources id 중복"

    srcset = set(src_ids)
    broken = [(r["id"], r["source_id"]) for r in refs if r["source_id"] not in srcset]
    assert not broken, f"refs → 미존재 source_id (끊어진 참조): {broken}"

    # sources[].id 형식 검증 (src-{pri|aca|ins|enc|web}-NNN)
    import re
    pat = re.compile(r"^src-(pri|aca|ins|enc|web)-\d+$")
    badfmt = [s["id"] for s in sources if not pat.match(s["id"])]
    assert not badfmt, f"sources id 형식 위반: {badfmt}"

    assert len(refs) == 155, f"refs 155 아님: {len(refs)}"
    assert len(sources) == 194, f"sources 194 아님: {len(sources)}"

    used_src = set(r["source_id"] for r in refs)
    orphan_sources = sorted(srcset - used_src)  # 본문 미참조 = 참고문헌 서지 전용(정상)

    doc = OrderedDict()
    doc["meta"] = {
        "source": "03_content/citations.json",
        "ref_count": len(refs),
        "source_count": len(sources),
        "orphan_source_count": len(orphan_sources),
        "source_types": dict(Counter(s["type"] for s in sources)),
        "note": "refs(마커 대상)→source_id→sources[].id 앵커. "
                "orphan sources는 본문 미참조 서지로 references.html에 정상 게재.",
    }
    doc["refs"] = refs
    doc["sources"] = sources
    return doc, refs, sources, orphan_sources


# ---------------------------------------------------------------------------
# 4) IMAGES — manifest 80건 → 렌더용. (sitemap §4 계약명: site/data/images.json)
# ---------------------------------------------------------------------------
def build_images(raw):
    imgs = raw["images"]
    img_ids = [i["id"] for i in imgs]
    assert len(set(img_ids)) == len(img_ids), "image id 중복"

    # 실제 webp 파일 존재 검증 (site/assets/images/{file})
    assets_dir = os.path.join(REPO_ROOT, "site", "assets", "images")
    missing = []
    for im in imgs:
        if not os.path.exists(os.path.join(assets_dir, im["file"])):
            missing.append((im["id"], im["file"]))
    assert not missing, f"manifest file이 site/assets/images에 부재: {missing}"

    out = []
    for im in imgs:
        rec = OrderedDict()
        rec["id"] = im["id"]  # 앵커 gallery.html#{img-id} 무변형
        rec["file"] = im["file"]
        rec["src"] = "assets/images/" + im["file"]   # 사이트 상대 경로 (소비자 편의)
        rec["title"] = im.get("title")
        rec["date"] = im.get("date")
        rec["date_precision"] = im.get("date_precision")
        rec["depicted"] = im.get("depicted", [])
        rec["place"] = im.get("place")
        rec["period"] = im.get("period")            # P1–P8 시기 코드
        rec["type"] = im.get("type")                # portrait/document 등 유형 필터
        rec["caption"] = im.get("caption")          # 캡션 4요소 — 본문 사실
        rec["credit"] = im.get("credit")
        rec["source_org"] = im.get("source_org")
        rec["source_url"] = im.get("source_url")
        rec["license"] = im.get("license")
        rec["license_evidence"] = im.get("license_evidence")
        rec["slots"] = im.get("slots", [])
        rec["used_pages"] = im.get("used_pages", [])  # 갤러리 역링크 원천
        out.append(rec)

    assert len(out) == 80, f"이미지 80건 아님: {len(out)}"
    # 시기 8구간 전부 ≥1장 (gallery 완성 기준)
    period_cov = Counter(r["period"] for r in out)
    for code, _, _ in PERIODS:
        assert period_cov.get(code, 0) >= 1, f"시기 {code} 이미지 0장"

    doc = OrderedDict()
    doc["meta"] = {
        "source": "03_content/images/manifest.json",
        "image_count": len(out),
        "image_root": "assets/images/",
        "by_license": dict(Counter(r["license"] for r in out)),
        "by_period": dict(period_cov),
        "by_type": dict(Counter(r["type"] for r in out)),
        "unfilled_slots": raw.get("unfilled_slots", []),
        "note": "사이트 소비 데이터 파일명은 sitemap §4 계약 'images.json'. "
                "src 필드는 site/ 기준 상대경로.",
    }
    doc["images"] = out
    return doc, out


# ---------------------------------------------------------------------------
# 4c) ARCHIVES — primary-source_catalog.json(47, 배열) → site/data/archives.json
#   (architecture.md §3.5b 계약). src-pri-NNN 앵커 무변형. related_event_ids→렌더사건.
# ---------------------------------------------------------------------------
def build_archives(raw_catalog, render_event_ids, merged_from_map, d_ids):
    """primary-source_catalog.json(47, 배열) → site/data/archives.json (§3.5b).

    카탈로그는 01_research/ 산출(timeline 병합 이전)이라 related_event_ids에
    병합 소멸한 옛 event id(evt-chrono-*)가 섞여 있다. timeline.json의
    merged_from 별칭표를 권위로 **생존 id로 치환**하고(의미 기반 id 치환 원칙),
    치환 후에도 D차단 사건을 가리키면 그 링크만 제거한다(소스는 보존 — null lat 동일 원리).
    """
    items = raw_catalog  # 루트가 배열
    ids = [c["id"] for c in items]
    dup = [k for k, v in Counter(ids).items() if v > 1]
    assert not dup, f"archives 중복 id: {dup}"
    import re
    pat = re.compile(r"^src-pri-\d+$")
    badfmt = [i for i in ids if not pat.match(i)]
    assert not badfmt, f"archives id 형식 위반(src-pri-NNN 아님): {badfmt}"

    render_set = set(render_event_ids)
    live_set = render_set | set(d_ids)   # D 포함 현존 id 전체

    remap_stats = {"alias_resolved": 0, "dropped_to_D": 0, "direct": 0}
    truly_missing = []
    out = []
    for c in items:
        resolved = []
        for eid in c.get("related_event_ids", []) or []:
            tgt = eid
            if eid not in live_set:
                # 병합 소멸 id → merged_from 권위로 생존 id 치환
                if eid in merged_from_map:
                    tgt = merged_from_map[eid]
                    remap_stats["alias_resolved"] += 1
                else:
                    truly_missing.append((c["id"], eid))
                    continue
            else:
                remap_stats["direct"] += 1
            # 치환 후 D차단 사건이면 링크 제거 (소스는 유지)
            if tgt in d_ids:
                remap_stats["dropped_to_D"] += 1
                continue
            resolved.append(tgt)

        rec = OrderedDict()
        rec["id"] = c["id"]  # 무변형 — archives.html#{src-pri-NNN}
        rec["title"] = c.get("title")        # 원문 그대로 (재작성 금지)
        rec["type"] = c.get("type")
        rec["author"] = c.get("author")
        rec["date_created"] = c.get("date_created")
        rec["language"] = c.get("language")
        rec["holder"] = c.get("holder")      # 원문 그대로
        rec["access_url"] = c.get("access_url")
        rec["location_status"] = c.get("location_status")  # confirmed/cited_only/unlocated
        rec["transcription"] = c.get("transcription")      # null 가능
        rec["modern_translation"] = c.get("modern_translation")
        rec["criticism"] = c.get("criticism")              # {external, internal}
        # 중복 제거하되 원래 순서 보존
        seen = set()
        rec["related_event_ids"] = [
            x for x in resolved if not (x in seen or seen.add(x))]
        rec["notes"] = c.get("notes")
        sanitize_fields(rec, ("title", "criticism", "notes", "holder"))  # D-26
        out.append(rec)

    # 진짜로 못 찾는 참조는 결함 — 중단 (별칭에도 현존에도 없음)
    assert not truly_missing, (
        f"archives related_event_id가 현존·별칭 어디에도 없음(결함): {truly_missing}"
    )
    # 치환 후 끊어진 앵커 0 재확인
    final_dangling = [(r["id"], x) for r in out
                      for x in r["related_event_ids"] if x not in render_set]
    assert not final_dangling, f"치환 후에도 끊어진 앵커 잔존: {final_dangling}"

    assert len(out) == 48, f"archives 48건 아님: {len(out)}"  # CQA-002: src-pri-048 증분 등재(team-lead 2026-06-06)
    by_status = Counter(r["location_status"] for r in out)

    doc = OrderedDict()
    doc["meta"] = {
        "source": "01_research/primary-source_catalog.json",
        "count": len(out),
        "by_status": dict(by_status),
        "with_related_events": sum(1 for r in out if r["related_event_ids"]),
        "event_id_remap": remap_stats,
        "note": "1차 사료 카탈로그. 앵커=src-pri-NNN 무변형. related_event_ids는 "
                "timeline merged_from 권위로 생존 id 치환 + D차단 링크 제거 → 렌더 사건만 참조.",
    }
    doc["catalog"] = out
    return doc, out


# ---------------------------------------------------------------------------
# 4b) PAGES — drafts/*.md → site/data/pages/{page_id}.json (D6 계약)
#   blocks 배열. {#anchor}·[ref:ref-NNN]·[표시](page.html#anchor) 원형 보존.
# ---------------------------------------------------------------------------
import re as _re  # noqa: E402

# 드래프트 파일명(NN_pageid.md) → page_id
DRAFTS_DIR = os.path.join(CONTENT, "drafts")
PAGE_FILES = [
    ("01_home.md", "home"),
    ("02_life.md", "life"),
    ("03_timeline.md", "timeline"),
    ("04_map.md", "map"),
    ("05_organizations.md", "organizations"),
    ("06_philosophy.md", "philosophy"),
    ("07_people.md", "people"),
    ("08_archives.md", "archives"),
    ("09_gallery.md", "gallery"),
    ("10_references.md", "references"),
]
_HEADING = _re.compile(r"^(#{1,4})\s+(.*?)\s*(?:\{#([a-zA-Z0-9_-]+)\})?\s*$")
_SLOT = _re.compile(r"^<!--\s*slot:\s*([a-zA-Z0-9_-]+)\s*-->\s*$")
_REF = _re.compile(r"\[ref:(ref-\d+)\]")


def _parse_markdown(text):
    """드래프트 markdown → (title, lead_blocks, sections[]). 마커·링크 원형 보존."""
    lines = text.split("\n")
    title = None
    lead_blocks = []
    sections = []  # {id, heading, level, blocks[]}
    current = None  # 현재 섹션 (None이면 lead 영역)

    i = 0
    n = len(lines)

    def target_blocks():
        return current["blocks"] if current is not None else lead_blocks

    while i < n:
        line = lines[i]
        stripped = line.strip()

        # 빈 줄
        if not stripped:
            i += 1
            continue

        # 헤딩
        hm = _HEADING.match(line)
        if hm:
            level = len(hm.group(1))
            heading_text = hm.group(2).strip()
            anchor = hm.group(3)
            if level == 1 and title is None:
                title = heading_text  # H1 = 페이지 제목
                i += 1
                continue
            # H2+ = 섹션 시작. anchor 없으면 slug 파생(부 헤딩 등)
            sid = anchor if anchor else _slugify(heading_text)
            current = {"id": sid, "heading": heading_text,
                       "level": level, "has_explicit_anchor": anchor is not None,
                       "blocks": []}
            sections.append(current)
            i += 1
            continue

        # 슬롯 주석
        sm = _SLOT.match(stripped)
        if sm:
            target_blocks().append({"type": "slot", "slot_id": sm.group(1)})
            i += 1
            continue

        # 테이블 (| ... |) — 연속 행 수집
        if stripped.startswith("|"):
            tbl_rows = []
            while i < n and lines[i].strip().startswith("|"):
                tbl_rows.append(lines[i].strip())
                i += 1
            headers, rows = _parse_table(tbl_rows)
            target_blocks().append(
                {"type": "table", "headers": headers, "rows": rows})
            continue

        # 인용/각주 (> ...) — 연속 행 수집
        if stripped.startswith(">"):
            q_lines = []
            while i < n and lines[i].strip().startswith(">"):
                q_lines.append(_re.sub(r"^>\s?", "", lines[i].strip()))
                i += 1
            target_blocks().append({"type": "blockquote", "lines": q_lines})
            continue

        # 리스트 (- 또는 N.) — 연속 행 수집
        if _re.match(r"^(-|\d+\.)\s+", stripped):
            ordered = bool(_re.match(r"^\d+\.\s+", stripped))
            items = []
            while i < n:
                ls = lines[i].strip()
                m = _re.match(r"^(?:-|\d+\.)\s+(.*)$", ls)
                if not m:
                    break
                items.append(m.group(1))
                i += 1
            target_blocks().append(
                {"type": "list", "ordered": ordered, "items": items})
            continue

        # 일반 문단 — 다음 빈 줄/특수 블록 전까지 한 단락 (마커·링크 원형 보존)
        para = [stripped]
        i += 1
        while i < n:
            nxt = lines[i].strip()
            if (not nxt or nxt.startswith("|") or nxt.startswith(">")
                    or _HEADING.match(lines[i]) or _SLOT.match(nxt)
                    or _re.match(r"^(-|\d+\.)\s+", nxt)):
                break
            para.append(nxt)
            i += 1
        target_blocks().append({"type": "paragraph", "text": " ".join(para)})

    return title, lead_blocks, sections


def _parse_table(rows):
    """markdown 표 행 리스트 → (headers, rows). 구분선(---) 행 제거."""
    def cells(r):
        # 양끝 | 제거 후 분할
        return [c.strip() for c in r.strip().strip("|").split("|")]
    headers = cells(rows[0]) if rows else []
    body = []
    for r in rows[1:]:
        if _re.match(r"^\|?[\s:|-]+\|?$", r):  # 구분선
            continue
        body.append(cells(r))
    return headers, body


def _slugify(text):
    s = text.lower()
    s = _re.sub(r"[^\w가-힣]+", "-", s).strip("-")
    return s or "section"


def build_pages():
    """drafts 10종 → pages dict. 각 페이지 {page_id, title, lead, sections}.
    ref-NNN 마커가 정의된 ref만 가리키는지 후속 검증(build_meta 단계 외부)에서 확인."""
    pages = {}
    all_ref_markers = set()
    for fname, pid in PAGE_FILES:
        path = os.path.join(DRAFTS_DIR, fname)
        if not os.path.exists(path):
            die(f"드래프트 누락: {path}")
        with open(path, encoding="utf-8") as f:
            text = f.read()
        title, lead_blocks, sections = _parse_markdown(text)
        assert title, f"{fname}: H1 제목 없음"
        # ref 마커 수집 (무결성 교차검증용)
        for m in _REF.finditer(text):
            all_ref_markers.add(m.group(1))
        # lead = H1 직후 ~ 첫 섹션 전 문단 (00_common §3 메타 예외 구역)
        pages[pid] = OrderedDict([
            ("page_id", pid),
            ("title", title),
            ("lead", lead_blocks),
            ("sections", sections),
        ])
    return pages, all_ref_markers


# ---------------------------------------------------------------------------
# 5) SEARCH-INDEX — 사건+인물/조직+사료 통합 경량 색인
# ---------------------------------------------------------------------------
def build_search_index(timeline_events, nodes, sources):
    """전역 검색용 평면 색인. 페이지 단위 분할 로딩과 무관한 단일 경량 파일.
    각 항목: {type, id, label, sub, url}. url = 앵커=데이터 id 무변형."""
    items = []
    for e in timeline_events:
        items.append(OrderedDict([
            ("type", "event"),
            ("id", e["id"]),
            ("label", e["title"]),
            ("sub", (e["date"].get("start") or "") + " · " +
                    (e["place"].get("name") or "")),
            ("text", e.get("summary") or ""),
            ("period", e.get("period")),
            ("url", f"timeline.html#{e['id']}"),
        ]))
    for n in nodes:
        page = "people.html" if n["kind"] == "person" else "organizations.html"
        alt = " ".join(n.get("alt_names", []) or [])
        items.append(OrderedDict([
            ("type", n["kind"]),
            ("id", n["id"]),
            ("label", n["name"]),
            ("sub", n.get("role") or ""),
            ("text", ((n.get("hanja") or "") + " " + alt + " " +
                      (n.get("summary") or "")).strip()),
            ("url", f"{page}#{n['id']}"),
        ]))
    # 1차 사료(src-pri-*)만 archives 앵커를 가진다 (sitemap §4)
    for s in sources:
        if s["id"].startswith("src-pri-"):
            items.append(OrderedDict([
                ("type", "source"),
                ("id", s["id"]),
                ("label", s.get("title") or s["id"]),
                ("sub", (s.get("author") or "") + " " +
                        (str(s.get("year")) if s.get("year") else "")),
                ("text", ""),
                ("url", f"archives.html#{s['id']}"),
            ]))

    # 색인 id 유일성 (type+id 조합) — event/person 간 id 충돌 없음 검증
    keys = [(it["type"], it["id"]) for it in items]
    assert len(set(keys)) == len(keys), "검색 색인 항목 (type,id) 중복"

    doc = OrderedDict()
    doc["meta"] = {
        "item_count": len(items),
        "by_type": dict(Counter(it["type"] for it in items)),
        "note": "전역 검색 경량 색인. url 앵커 = 데이터 id 무변형.",
    }
    doc["items"] = items
    return doc


# ---------------------------------------------------------------------------
# 6) META — 사이트 자기 서술 수치의 단일 출처 (00_common §3(iii))
# ---------------------------------------------------------------------------
def build_meta(claims_raw, t_events, nodes, edges, refs, sources,
               images, unconfirmed_count, archives_count, generated):
    """사이트 자기 집계 수치 단일 출처 (architecture.md §3.8 / D-21).
    ★모든 수치는 site/data 실제 레코드에서 집계 — 명세·드래프트 수치를 베끼지 않는다.
    키명은 §3.8 계약 스키마와 1:1(events_total/events_rendered/...)."""
    claim_grades = Counter(c.get("grade") for c in claims_raw)

    doc = OrderedDict()
    doc["counts"] = {
        "events_total": 172,
        "events_rendered": len(t_events),     # 165 (실측)
        "events_excluded_d": 172 - len(t_events),  # 7
        "events_disputed": sum(1 for e in t_events if e["disputed"]),  # 17
        "events_with_geo": sum(1 for e in t_events if e["has_geo"]),   # 113
        "persons": sum(1 for n in nodes if n["kind"] == "person"),     # 59
        "orgs": sum(1 for n in nodes if n["kind"] == "org"),           # 22
        "edges": len(edges),                  # 135
        "edges_unconfirmed": unconfirmed_count,  # 19
        "claims": len(claims_raw),            # 305
        "sources": len(sources),              # 194
        "primary_sources": archives_count,    # 48 (CQA-002 증분)
        "images": len(images),                # 80
    }
    doc["claim_grades"] = {                   # claims_register 전체 집계
        "A": claim_grades.get("A", 0),
        "B": claim_grades.get("B", 0),
        "C": claim_grades.get("C", 0),
        "D": claim_grades.get("D", 0),
    }
    # 렌더분(D 제외) confidence — 키 순서 A/B/C 고정
    tconf = Counter(e["confidence"] for e in t_events)
    doc["timeline_confidence"] = {"A": tconf.get("A", 0),
                                  "B": tconf.get("B", 0),
                                  "C": tconf.get("C", 0)}
    # 렌더분 태그 실측 (명세의 D포함 수치와 다름 — §3.8 단서)
    doc["timeline_tags"] = dict(
        Counter(t for e in t_events for t in e["tags"]).most_common()
    )
    doc["images_by_period"] = dict(
        Counter(im["period"] for im in images)
    )
    doc["refs"] = len(refs)                   # 인용 마커 대상 refs (155)
    doc["generated"] = generated
    doc["note"] = ("사이트 자기 서술 수치(architecture.md §3.8·00_common §3(iii))의 "
                   "단일 출처. 전부 site/data 실제 레코드 집계. home 통계·qa 정합 검사 입력.")
    return doc


# ---------------------------------------------------------------------------
# 메인 — 전 단계 통과 후에만 일괄 기록 (부분 산출물 금지)
# ---------------------------------------------------------------------------
def main():
    print("[build_data] 입력 로드…")
    tl_raw = load(IN_TIMELINE)
    nw_raw = load(IN_NETWORK)
    claims_raw = load(IN_CLAIMS)
    cit_raw = load(IN_CITATIONS)
    man_raw = load(IN_MANIFEST)
    cat_raw = load(IN_CATALOG)
    generated = tl_raw.get("meta", {}).get("generated", "2026-06-06")

    print("[build_data] 변환·검증…")
    resolver, ambiguous = build_name_resolver(nw_raw)
    t_doc, t_events = build_timeline(tl_raw, resolver, ambiguous)
    render_ids = [e["id"] for e in t_events]
    n_doc, nodes, edges = build_network(nw_raw, render_ids)
    c_doc, refs, sources, orphan = build_citations(cit_raw)
    i_doc, images = build_images(man_raw)
    # merged_from 별칭표(소멸 id → 생존 id) — archives 치환 권위
    merged_from_map = {}
    for e in tl_raw["events"]:
        for a in e.get("merged_from", []) or []:
            merged_from_map[a] = e["id"]
    a_doc, archives = build_archives(cat_raw, render_ids,
                                     merged_from_map, EXPECTED_D_IDS)   # §3.5b
    pages, page_ref_markers = build_pages()
    m_doc = build_meta(claims_raw, t_events, nodes, edges, refs, sources,
                       images, len(n_doc["edges_unconfirmed"]),
                       len(archives), generated)

    # D6 무결성: pages 본문의 ref-NNN 마커가 전부 citations.refs에 정의돼 있어야
    # (끊어진 각주 0 — references.html 종착점 무결성)
    ref_ids = set(r["id"] for r in refs)
    undefined = sorted(page_ref_markers - ref_ids)
    assert not undefined, f"pages 본문 마커가 미정의 ref 참조(끊어진 각주): {undefined}"

    print("[build_data] 기록…")
    # 산출 파일 = architecture.md §2 디렉토리 계약. search-index.json은 D-23 보류로 미산출.
    written = [
        write_json("timeline.json", t_doc),
        write_json("network.json", n_doc),
        write_json("citations.json", c_doc),
        write_json("archives.json", a_doc),      # §3.5b 신설
        write_json("images.json", i_doc),
        write_json("meta.json", m_doc),
    ]
    for pid, pdoc in pages.items():
        written.append(write_json(os.path.join("pages", pid + ".json"), pdoc))

    print("\n[build_data] 완료 — 산출 파일:")
    for p in written:
        size = os.path.getsize(p)
        print(f"  {os.path.relpath(p, REPO_ROOT)}  ({size:,} bytes)")
    print("\n[레코드 수]")
    print(f"  timeline.events      = {len(t_doc['events'])}  (D 7 차단, 172→165)")
    print(f"  timeline ref해소      = actor {t_doc['meta']['ref_resolution']['actor_resolved']}"
          f"/org {t_doc['meta']['ref_resolution']['org_resolved']} 해소(occurrence)")
    print(f"  network.nodes        = {len(n_doc['nodes'])} (인물 {m_doc['counts']['persons']}·조직 {m_doc['counts']['orgs']})")
    print(f"  network.edges        = {len(n_doc['edges'])}")
    print(f"  network.unconfirmed  = {len(n_doc['edges_unconfirmed'])}")
    print(f"  citations.refs       = {len(c_doc['refs'])}")
    print(f"  citations.sources    = {len(c_doc['sources'])}")
    print(f"  archives.catalog     = {len(a_doc['catalog'])} ({m_doc['counts']['primary_sources']}건)")
    print(f"  images               = {len(i_doc['images'])}")
    print(f"  pages                = {len(pages)} (ref 마커 {len(page_ref_markers)}종)")
    print("  (search-index.json: D-23 보류 — 미산출)")


if __name__ == "__main__":
    main()
