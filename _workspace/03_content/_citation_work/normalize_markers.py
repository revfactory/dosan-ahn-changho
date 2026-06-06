#!/usr/bin/env python3
"""잠정 마커 정규화 — citation-manager 전용.

작성 단계 마커(style_guide R0.1: [ref:clm-/evt-/src-pri-/cfl-…])를
정식 ref id([ref:ref-NNN])로 치환하고 citations.json refs를 증분 등재한다.

해석 규칙:
  src-pri-NNN  -> 해당 사료 1건
  clm-XXXX     -> claim_source_map 상위 2건 (출처 위계: pri > aca > ins > enc > web)
  evt-…        -> event_source_map 상위 2건 (동일 위계)
  cfl-XXX      -> conflict_event_map의 관련 사건 출처 합집합 상위 2건

ref id는 (잠정 id, source_id) 쌍 단위로 발급하며 ref_assignments.json에
영구 기록한다 — 재실행 시 절대 재발급하지 않는다.

사용:
  python3 normalize_markers.py <md파일|디렉토리> ...        # 보고만 (dry-run)
  python3 normalize_markers.py --apply <md파일|디렉토리> ...  # 치환 + refs 등재
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent           # _citation_work/
CONTENT = HERE.parent                            # 03_content/
CITATIONS = CONTENT / "citations.json"
ASSIGN = HERE / "ref_assignments.json"
CLAIM_MAP = HERE / "claim_source_map.json"
EVT_MAP = HERE / "event_source_map.json"
CFL_MAP = HERE / "conflict_event_map.json"

MARKER = re.compile(r"\[ref:([^\]\s]+)\]")
HIER = {"pri": 0, "aca": 1, "ins": 2, "enc": 3, "web": 4}

# 별칭 해석 위험 케이스 (team-lead 검증, 2026-06-06 — synthesis life.md §14 정정 건):
# timeline 병합 시 merged_from 기계 별칭이 본문 의미와 다른 인접 사건을 가리키는
# 소멸 id 2건. 기계 별칭을 그대로 따르면 엉뚱한 사건의 출처가 각주에 붙으므로
# 자동 해석을 차단하고, 문장 의미 기준으로 생존 id를 직접 쓰도록 안내한다.
AMBIGUOUS_ALIAS = {
    "evt-chrono-093": "기계 별칭=evt-hsd-018(송태산장 은거), 의미 대응=evt-hsd-017"
                      "(가출옥 후 치료·순회) — 문장 의미로 판별해 생존 id로 교체할 것",
    "evt-chrono-094": "기계 별칭=evt-hsd-020(동우회 사건 피체), 의미 대응=evt-hsd-018"
                      "(송태산장 은거) — 문장 의미로 판별해 생존 id로 교체할 것",
}


def hier_key(m):
    return (HIER.get(m["source_id"].split("-")[1], 9), m["source_id"])


def clean_locator(loc):
    # 내부 작업 메모·내부 식별자(레지스터가 locator 필드에 넣은 id류)·검증 메모는
    # 표시용 locator가 아니다 — 각주에 노출될 가치가 있는 좌표만 남긴다
    if not loc or loc == "사료 카탈로그 참조(grade_reason)":
        return None
    s = loc.strip()
    _ID = r"(?:src-(?:pri|aca|ins|enc|web)-\d{3}|clm-\d+|cfl-\d+|evt-[a-z]+-\d+)"
    if re.fullmatch(rf"{_ID}(?:\s*[/·,]\s*{_ID})*", s):    # 내부 id 단독·연쇄
        return None
    if re.fullmatch(r"[a-z]{2,}\.(?:[a-z0-9-]+\.)+[a-z]{2,}", s):   # 맨 도메인
        return None
    if re.search(r"미확정|부재|불가|미확인$", s) and len(s) <= 20:   # 짧은 검증 메모
        return None
    return s


def locator_equiv(loc):
    """locator 동치 키 — 표기 변형('사전 id 696'/'id 696', 'KCI artiId ART…'/'KCI ART…',
    'levelId kc_…'/'kc_…')이 같은 좌표의 ref를 분열시키지 않도록 잡음 토큰을 걷어낸 비교 키."""
    if not loc:
        return ""
    k = loc.lower()
    for tok in ("사전", "표제어", "levelid", "kci", "arti", "art", "id", ":", "="):
        k = k.replace(tok, "")
    k = re.sub(r"\s+", "", k)
    # 꼬리 주석 변형: '제1호(1919.8.21),…소장' vs '제1호' — 괄호 이후가 부가 주석이면 동치
    m = re.match(r"^(제?\d+호|창간호)\(", k)
    if m:
        k = m.group(1)
    return k


def resolve(pid, maps):
    """잠정 id -> [{source_id, locator}] (상위 2건). 해석 불능이면 []"""
    claim_map, evt_map, cfl_map, src_ids = maps
    if pid in AMBIGUOUS_ALIAS:                       # 의미-별칭 불일치 — 자동 해석 금지
        return []
    if re.fullmatch(r"src-pri-\d{3}", pid):
        return [{"source_id": pid, "locator": None}] if pid in src_ids else []
    if pid.startswith("clm-"):
        cands = claim_map.get(pid, [])
    elif pid.startswith("evt-"):
        cands = evt_map.get(pid, [])
    elif pid.startswith("cfl-"):
        seen, cands = set(), []
        for evt in cfl_map.get(pid, []):
            for m in evt_map.get(evt, []):
                if m["source_id"] not in seen:
                    seen.add(m["source_id"])
                    cands.append(m)
    else:
        return []
    return sorted(cands, key=hier_key)[:2]


def main():
    args = sys.argv[1:]
    apply_mode = "--apply" in args
    targets = [a for a in args if a != "--apply"]
    if not targets:
        print(__doc__)
        return 2

    files = []
    for t in targets:
        p = Path(t) if Path(t).is_absolute() else CONTENT / t
        files += sorted(p.glob("*.md")) if p.is_dir() else [p]

    cit = json.loads(CITATIONS.read_text(encoding="utf-8"))
    src_ids = {s["id"] for s in cit["sources"]}
    refs = {r["id"]: r for r in cit["refs"]}
    assign = json.loads(ASSIGN.read_text(encoding="utf-8")) if ASSIGN.exists() else {}
    # 연번 하한은 발급분 + 영구 결번의 최대값 — 결번 이후 카운터가 후퇴해
    # 결번 번호를 재발급하는 사고를 막는다 (실제 발생: ref-114, 2026-06-06 교정)
    retired_file = HERE / "retired_refs.json"
    retired_max = 0
    if retired_file.exists():
        retired = json.loads(retired_file.read_text(encoding="utf-8"))["retired"]
        retired_max = max((int(i.split("-")[1]) for i in retired), default=0)
    counter = max([retired_max] + [int(i.split("-")[1]) for i in assign.values()])
    maps = (json.loads(CLAIM_MAP.read_text(encoding="utf-8")),
            json.loads(EVT_MAP.read_text(encoding="utf-8")),
            json.loads(CFL_MAP.read_text(encoding="utf-8")), src_ids)

    unresolved, converted, kept = [], 0, 0
    for f in files:
        body = f.read_text(encoding="utf-8")

        def sub(m):
            nonlocal counter, converted, kept
            pid = m.group(1)
            if re.fullmatch(r"ref-\d+", pid):      # 이미 정식 id
                kept += 1
                return m.group(0)
            picks = resolve(pid, maps)
            if not picks:
                unresolved.append((f.name, pid))
                return m.group(0)                   # 손대지 않고 통보 대상으로
            out = ""
            for p in picks:
                loc = clean_locator(p["locator"])
                # ref = (출처, 위치) 단위 — 같은 좌표는 잠정 id·locator 표기가 달라도 동일 ref로 수렴
                key = f"{p['source_id']}|{locator_equiv(loc)}"
                if key not in assign:
                    counter += 1
                    assign[key] = f"ref-{counter:03d}"
                rid = assign[key]
                refs.setdefault(rid, {"id": rid, "source_id": p["source_id"],
                                      "page_or_locator": loc})
                out += f"[ref:{rid}]"
            converted += 1
            return out

        new_body = MARKER.sub(sub, body)
        # 인접 마커 클러스터 내 동일 ref 중복 제거 (잠정 마커 2종이 같은 출처로 수렴한 경우)
        new_body = re.sub(
            r"(?:\[ref:ref-\d+\]){2,}",
            lambda m: "".join(dict.fromkeys(re.findall(r"\[ref:ref-\d+\]", m.group(0)))),
            new_body)
        if apply_mode and new_body != body:
            f.write_text(new_body, encoding="utf-8")

    if apply_mode:
        cit["refs"] = sorted(refs.values(), key=lambda r: int(r["id"].split("-")[1]))
        CITATIONS.write_text(json.dumps(cit, ensure_ascii=False, indent=2), encoding="utf-8")
        ASSIGN.write_text(json.dumps(assign, ensure_ascii=False, indent=2), encoding="utf-8")

    mode = "APPLY" if apply_mode else "DRY-RUN"
    print(f"[{mode}] 파일 {len(files)}개 | 잠정 마커 치환 {converted}건 | "
          f"정식 마커 유지 {kept}건 | refs {len(refs)}건 | 해석 불능 {len(unresolved)}건")
    for fn, pid in unresolved:
        hint = AMBIGUOUS_ALIAS.get(pid)
        if hint:
            print(f"  [AMBIGUOUS ] {fn}: [ref:{pid}] — {hint}")
        else:
            print(f"  [UNRESOLVED] {fn}: [ref:{pid}] — narrative-writer 통보 대상")
    if not apply_mode and not unresolved:
        print("dry-run 통과 — --apply로 치환·등재 실행 후 validate_citations.py를 돌려라.")
    return 1 if unresolved else 0


if __name__ == "__main__":
    sys.exit(main())
