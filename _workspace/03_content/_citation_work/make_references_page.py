#!/usr/bin/env python3
"""references_page.md 생성 — citations.json에서 기계 생성 (수기 작성 금지, 스킬 §5).

유형별 묶음(1차 사료 -> 학술 -> 기관 -> 백과 -> 웹), 유형 내 저자(없으면 제목) 가나다순.
표기 형식은 citation-style 스킬 §2를 유형별로 단일 적용한다.

사용: python3 make_references_page.py [--used-only]
  --used-only: refs가 실제 참조하는 source만 수록 (최종 게이트용)
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONTENT = HERE.parent
CITATIONS = CONTENT / "citations.json"
OUT = CONTENT / "references_page.md"

TYPE_ORDER = ["primary", "academic", "institutional", "encyclopedia", "web"]
TYPE_HEAD = {"primary": "1차 사료", "academic": "학술 논문·단행본",
             "institutional": "공공기관·단체 DB 및 발간물",
             "encyclopedia": "백과사전", "web": "일반 웹 자료"}
# academic 중 단행본 — 「」 대신 『』 (서명 표기)
BOOK_IDS = {"src-aca-001", "src-aca-003"}


def quote_title(s, book=False):
    t = s["title"]
    if any(b in t for b in "「」『』"):   # 원제 자체에 낫표 포함 — 재포장 금지
        return t
    return f"『{t}』" if book else f"「{t}」"


def render(s):
    parts = []
    if s["author"]:
        parts.append(s["author"])
    book = s["id"] in BOOK_IDS
    parts.append(quote_title(s, book))
    if s["type"] == "primary":
        if s["year"]:
            parts.append(str(s["year"]))
        if s["publisher"]:
            parts.append(s["publisher"])
    elif s["type"] == "academic":
        if s["publisher"]:
            parts.append(s["publisher"])
        if s["year"]:
            parts.append(str(s["year"]))
    else:  # institutional / encyclopedia / web
        if s["publisher"]:
            parts.append(s["publisher"])
        if s["year"]:
            parts.append(str(s["year"]))
    line = ", ".join(parts)
    if s["url"]:
        line += f", {s['url']} (접속일: {s['accessed']})"
    return line + "."


def main():
    used_only = "--used-only" in sys.argv
    cit = json.loads(CITATIONS.read_text(encoding="utf-8"))
    sources = cit["sources"]
    if used_only:
        used = {r["source_id"] for r in cit["refs"]}
        sources = [s for s in sources if s["id"] in used]

    lines = ["# 참고문헌", "",
             f"> citations.json에서 기계 생성됨 (생성 스크립트: _citation_work/make_references_page.py). "
             f"수기 편집 금지 — 수정은 citations.json에서.", ""]
    total = 0
    for t in TYPE_ORDER:
        group = sorted((s for s in sources if s["type"] == t),
                       key=lambda s: (s["author"] or s["title"]))
        if not group:
            continue
        lines += [f"## {TYPE_HEAD[t]} ({len(group)}건)", ""]
        for s in group:
            lines.append(f"- <a id=\"{s['id']}\"></a>{render(s)}")
            total += 1
        lines.append("")
    lines.append(f"<!-- 총 {total}건 | 모드: {'used-only' if used_only else '전체 원장'} -->")
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"references_page.md 생성 — {total}건 ({'used-only' if used_only else '전체'})")


if __name__ == "__main__":
    sys.exit(main())
