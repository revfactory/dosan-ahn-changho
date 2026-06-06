#!/usr/bin/env python3
"""인용 무결성 검증 — citation-style 스킬 §4 검사 4종 + 스키마 검사.

검사 항목:
  [ERROR] 고아 마커        — 본문 [ref:id]가 refs에 없음 (끊어진 각주)
  [ERROR] 미사용 ref       — refs에 있는데 본문 마커가 없음 (참고문헌 부풀림)
  [ERROR] 끊어진 source    — ref.source_id가 sources에 없음
  [ERROR] ref/source 중복 id, id 형식 위반, 유형 코드-type 불일치
  [ERROR] url 있는데 accessed 없음 / url·publisher(소장처) 모두 없음
  [WARN ] 출처 없는 문단    — 사실 진술로 보이는 문단(>80자)에 마커 0건
                             (오탐 가능 — 기계 검출 후 사람이 판별. 검사 비활성화 금지)
  [META ] 메타 서술 예외 위치의 무마커 문단 — 00_common.md §3 예외(4곳+도입문).
          결함이 아니나 출력은 유지: 메타 서술 안의 정박 가능 사실은 사람이 판별.

실행: python3 validate_citations.py [스캔 디렉토리]   (기본 pages/ — drafts/ 지정 가능)
종료 코드: ERROR 있으면 1, 없으면 0. 로그는 _citation_work/last_validation.log 보존.
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent          # _workspace/03_content/
CITATIONS = HERE / "citations.json"
LOG = HERE / "_citation_work" / "last_validation.log"

# 작성 단계 잠정 마커(style_guide R0.1) — 끊어진 참조와 구분해 '정규화 대기'로 표시
PROVISIONAL = re.compile(r"(?:clm|cfl)-\d+$|evt-[a-z]+-\d+$|src-pri-\d{3}$")

SRC_ID = re.compile(r"src-(pri|aca|ins|enc|web)-\d{3}$")
REF_ID = re.compile(r"ref-\d+$")
TYPE_CODE = {"primary": "pri", "academic": "aca", "institutional": "ins",
             "encyclopedia": "enc", "web": "web"}
MARKER = re.compile(r"\[ref:([^\]\s]+)\]")

# 문단 검사에서 건너뛰는 비본문 블록 (제목·표·인용·이미지·주석·구분선·코드)
SKIP_PARA = re.compile(r"^(#|\||>|!\[|<!--|---|```|:::|\{)")

# 편집 메타 서술 [ref:] 예외 (00_common.md §3 — content-architect 패턴 확장 승인 2026-06-06,
# content-qa 게이트와 공유 규칙): 앵커 패턴 `*-intro`·`*-gaps` 전체 + 명명 4종
# (methodology·grades·citations·colophon) + 각 페이지 도입문(H1 직후 ~ 첫 섹션 전).
# 해당 위치의 무마커 문단은 WARN이 아니라 META로 재분류한다 — 억제가 아니라 재분류이며,
# §3 단서(메타 안의 도산-사실·정박 가능 사실은 마커 의무)는 사람이 META 행을 훑어 판별한다.
# 데이터 집계 자기 서술(165건/305건 등)은 [ref:] 대상이 아니라 content-qa 데이터 정합 검사 대상.
META_ANCHORS = {"methodology", "grades", "citations", "colophon", "intro"}
HEADING_ANCHOR = re.compile(r"\{#([A-Za-z0-9_-]+)\}")


def paragraph_zones(body):
    """(문단 번호, 문단, 메타 여부) 순회 — 섹션 앵커·도입문 구역 추적."""
    in_intro, anchor = False, None
    for i, para in enumerate(body.split("\n\n")):
        p = para.strip()
        head = p.splitlines()[0] if p else ""
        if head.startswith("#"):
            level = len(head) - len(head.lstrip("#"))
            m = HEADING_ANCHOR.search(head)
            anchor = m.group(1) if m else None
            in_intro = (level == 1)          # H1 직후 = 도입문 구역, ##/###부터 해제
            continue
        a = anchor or ""
        meta = in_intro or a in META_ANCHORS or a.endswith(("-intro", "-gaps"))
        yield i, p, meta


def main() -> int:
    lines = []

    def out(msg=""):
        print(msg)
        lines.append(msg)

    errors, warns, metas = [], [], []

    cit = json.loads(CITATIONS.read_text(encoding="utf-8"))
    refs, sources = cit.get("refs", []), cit.get("sources", [])
    ref_ids = [r["id"] for r in refs]
    src_ids = [s["id"] for s in sources]
    ref_set, src_set = set(ref_ids), set(src_ids)

    # --- sources 스키마 ---
    if len(src_ids) != len(src_set):
        dups = sorted({i for i in src_ids if src_ids.count(i) > 1})
        errors.append(f"sources 중복 id: {dups}")
    for s in sources:
        sid = s["id"]
        if not SRC_ID.fullmatch(sid):
            errors.append(f"{sid}: source id 형식 위반 (src-{{유형}}-{{3자리}})")
        elif TYPE_CODE.get(s.get("type")) != sid.split("-")[1]:
            errors.append(f"{sid}: type '{s.get('type')}'와 id 유형 코드 불일치")
        if s.get("url") and not s.get("accessed"):
            errors.append(f"{sid}: url 있는데 accessed 없음")
        if not s.get("url") and not s.get("publisher"):
            errors.append(f"{sid}: url 없는 출처에 소장처(publisher)도 없음")
        if not (s.get("title") or "").strip():
            errors.append(f"{sid}: title 결손")

    # --- refs 무결성 ---
    if len(ref_ids) != len(ref_set):
        dups = sorted({i for i in ref_ids if ref_ids.count(i) > 1})
        errors.append(f"refs 중복 id: {dups}")
    for r in refs:
        if not REF_ID.fullmatch(r["id"]):
            errors.append(f"{r['id']}: ref id 형식 위반 (ref-{{일련번호}})")
        if r["source_id"] not in src_set:
            errors.append(f"{r['id']}: source_id {r['source_id']} 미존재 (끊어진 source)")

    # --- 본문 마커 전수 스캔 ---
    scan_dir = sys.argv[1] if len(sys.argv) > 1 else "pages"
    pages = sorted(HERE.glob(f"{scan_dir.rstrip('/')}/*.md"))
    used = set()
    for path in pages:
        body = path.read_text(encoding="utf-8")
        for m in MARKER.findall(body):
            used.add(m)
            if m not in ref_set:
                if PROVISIONAL.fullmatch(m):
                    errors.append(f"{path.name}: 잠정 마커 [ref:{m}] — 정규화 대기 (최종 게이트 불가)")
                else:
                    errors.append(f"{path.name}: 고아 마커 [ref:{m}]")
        # 잘못 적힌 마커 형태( [ref: id] 공백, [Ref:], (ref:) )도 잡는다
        for bad in re.findall(r"\[\s*[Rr]ef\s*:\s+[^\]]+\]|\([Rr]ef:[^)]+\)", body):
            errors.append(f"{path.name}: 마커 형식 위반 {bad!r}")
        # 출처 없는 문단 (메타 서술 예외 위치는 META로 재분류 — 00_common.md §3)
        for i, p, meta in paragraph_zones(body):
            if p and not SKIP_PARA.match(p) and "[ref:" not in p and len(p) > 80:
                if meta:
                    metas.append(f"{path.name}: 문단 {i + 1} 메타 서술(예외 위치) — "
                                 f"정박 가능 사실 포함 여부 확인 — {p[:40]}…")
                else:
                    warns.append(f"{path.name}: 문단 {i + 1} 출처 마커 없음 (확인 요망) — {p[:40]}…")

    # --- 이미지 매니페스트 캡션 마커 (manifest.json — 독자 노출 텍스트라 동일 게이트) ---
    manifest = HERE / "images" / "manifest.json"
    if manifest.exists():
        mbody = manifest.read_text(encoding="utf-8")
        for m in MARKER.findall(mbody):
            used.add(m)
            if m not in ref_set:
                if PROVISIONAL.fullmatch(m):
                    errors.append(f"manifest.json: 잠정 마커 [ref:{m}] — 정규화 대기 (최종 게이트 불가)")
                else:
                    errors.append(f"manifest.json: 고아 마커 [ref:{m}]")

    for unused in sorted(ref_set - used):
        errors.append(f"미사용 ref: {unused} (본문 마커 없음)")

    # --- 결과 ---
    out(f"검증 시각: {datetime.now().isoformat(timespec='seconds')}")
    out(f"페이지 {len(pages)}개 | 마커 {len(used)}종 | refs {len(ref_set)}건 | "
        f"sources {len(src_set)}건")
    if not pages:
        out("[알림] pages/*.md 미존재 — 본문 미작성 단계의 사전 검증으로 간주")
    out(f"ERROR {len(errors)}건 | WARN {len(warns)}건 | META {len(metas)}건")
    for e in errors:
        out(f"  [ERROR] {e}")
    for w in warns:
        out(f"  [WARN ] {w}")
    for m in metas:
        out(f"  [META ] {m}")
    if not errors:
        out("끊어진 참조 0건 — 통과" + (" (본문 스캔 전 — 최종 판정 아님)" if not pages else ""))

    LOG.parent.mkdir(parents=True, exist_ok=True)
    LOG.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
