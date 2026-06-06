#!/usr/bin/env python3
"""ref 발급 키 체계 보정 마이그레이션 (2026-06-06, 1회성 — 감사 목적 보존).

배경: 초기 발급 키가 locator 원문 표기를 그대로 써서 동치 좌표가 ref로 분열됐다
(예: src-ins-002의 'id 696'/'사전 id 696' → ref-002/ref-003 이중 발급,
locator 필드에 내부 id가 든 'src-pri-001' → ref-074/ref-076 분열).

처리: clean_locator·locator_equiv(normalize_markers.py 신판) 기준으로 동치 그룹을
구성하고, 그룹 대표 = 최소 번호 ref. 흡수된 ref 번호는 영구 결번(재사용 금지,
citation-style §1) — retired_refs.json에 기록. 본문(정규화 완료 페이지)의 흡수
마커는 대표로 치환 후 인접 중복 제거.
"""
import json
import re
from pathlib import Path

from normalize_markers import clean_locator, locator_equiv

HERE = Path(__file__).resolve().parent
CONTENT = HERE.parent
CITATIONS = CONTENT / "citations.json"
ASSIGN = HERE / "ref_assignments.json"
RETIRED = HERE / "retired_refs.json"

# 정규화 진행 평면 전체 — 치환 맵은 ref-NNN만 다루므로 잠정 마커·JSON 텍스트에도 안전
NORMALIZED_PAGES = sorted((CONTENT / "drafts").glob("*.md")) + \
    [CONTENT / "images" / "manifest.json"]


def main():
    cit = json.loads(CITATIONS.read_text(encoding="utf-8"))
    refs = {r["id"]: r for r in cit["refs"]}
    assign = json.loads(ASSIGN.read_text(encoding="utf-8"))

    # 1) 구 키 -> 신 키 재계산, 동치 그룹화
    groups = {}  # new_key -> [(rid, display_loc)]
    for old_key, rid in assign.items():
        src_id = old_key.split("|", 1)[0]
        disp = clean_locator(refs[rid].get("page_or_locator"))
        new_key = f"{src_id}|{locator_equiv(disp)}"
        groups.setdefault(new_key, []).append((rid, disp, src_id))

    new_assign, new_refs, replace, retired = {}, {}, {}, []
    for key, members in groups.items():
        members.sort(key=lambda t: int(t[0].split("-")[1]))
        rep, _, src_id = members[0]
        # 표시 locator: 그룹 내 비None 중 최단 표기
        locs = [d for _, d, _ in members if d]
        disp = min(locs, key=len) if locs else None
        new_assign[key] = rep
        new_refs[rep] = {"id": rep, "source_id": src_id, "page_or_locator": disp}
        for rid, _, _ in members[1:]:
            replace[rid] = rep
            retired.append(rid)

    # 2) citations.json refs 재작성 (결번 제거)
    cit["refs"] = sorted(new_refs.values(), key=lambda r: int(r["id"].split("-")[1]))
    CITATIONS.write_text(json.dumps(cit, ensure_ascii=False, indent=2), encoding="utf-8")
    ASSIGN.write_text(json.dumps(new_assign, ensure_ascii=False, indent=2), encoding="utf-8")
    # 결번은 누적 병합 — 덮어쓰면 과거 결번 기록이 유실되어 번호 재발급 위험이 생긴다
    prev = set()
    if RETIRED.exists():
        prev = set(json.loads(RETIRED.read_text(encoding="utf-8"))["retired"])
    RETIRED.write_text(json.dumps(
        {"retired": sorted(prev | set(retired), key=lambda r: int(r.split("-")[1])),
         "reason": "locator 동치 병합(누적) — 번호 영구 결번, 재사용 금지"},
        ensure_ascii=False, indent=2), encoding="utf-8")

    # 3) 정규화 완료 페이지의 흡수 마커 치환 + 인접 중복 제거
    pat = re.compile(r"\[ref:(ref-\d+)\]")
    for page in NORMALIZED_PAGES:
        body = page.read_text(encoding="utf-8")
        body = pat.sub(lambda m: f"[ref:{replace.get(m.group(1), m.group(1))}]", body)
        body = re.sub(r"(?:\[ref:ref-\d+\]){2,}",
                      lambda m: "".join(dict.fromkeys(re.findall(r"\[ref:ref-\d+\]", m.group(0)))),
                      body)
        page.write_text(body, encoding="utf-8")

    print(f"동치 그룹 {len(groups)}개 | refs {len(refs)} -> {len(new_refs)}건 | "
          f"결번 {len(retired)}건: {sorted(retired, key=lambda r: int(r.split('-')[1]))}")


if __name__ == "__main__":
    main()
