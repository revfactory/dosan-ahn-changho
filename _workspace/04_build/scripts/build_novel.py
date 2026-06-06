#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_novel.py — 소설 『사람을 모으는 사람』 장별 분할 빌드 (멱등)
==============================================================================
입력 : novel/chapters/ch00.md ~ ch22.md, ch99.md (24유닛) + novel/afterword.md
출력 : site/data/novel/index.json            (목차 + 작품 메타)
       site/data/novel/ch{NN}.json           (장별 {id,title,part,html})
       site/data/novel/afterword.json         (작가의 말)

설계 근거(architecture.md):
  - md→html 은 표준 라이브러리만으로(외부 pip 금지). 본문 마크다운은 단순하다
    (#·## 헤딩, 문단, ---, *강조*, > 인용, - 목록) — 미니 변환기를 직접 작성하고
    HTML 이스케이프를 안전 처리한다.
  - 분할 이유: 단일 novel.json(~330KB)은 페이지 gzip 예산 압박 → 장별 lazy 로드.
  - id 무변형 원칙(§3 D-01)과 같은 정신으로, 파일 stem(ch00..ch99) 을 그대로 장 id 로 쓴다.

assert : 24유닛 + afterword = 25 파일, 자수 합계 ≈ 원본.

소유 : frontend-developer (신규 빌드 스크립트). 멱등 — 반복 실행해도 동일 산출.
==============================================================================
"""
import html
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── 경로 ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]                  # .../DOSAN
NOVEL_DIR = REPO_ROOT / "novel"
CHAPTERS_DIR = NOVEL_DIR / "chapters"
AFTERWORD = NOVEL_DIR / "afterword.md"
OUT_DIR = REPO_ROOT / "site" / "data" / "novel"

# ── 작품 메타 (outline.md 채택안 / team-lead 지시문 부제) ──────────────────────
WORK_TITLE = "사람을 모으는 사람"
WORK_SUBTITLE = "도산 안창호"

# 부 구성 — outline.md §1 (서장·5부·종장). 각 부에 속한 장 stem 목록.
#   key: part 코드, name: 표제, units: 이 부에 속한 파일 stem(순서대로)
PARTS = [
    {"part": "prologue", "name": "서장", "units": ["ch00"]},
    {"part": "p1", "name": "1부 — 빈 들에 우물을 파다", "units": ["ch01", "ch02", "ch03", "ch04"]},
    {"part": "p2", "name": "2부 — 아메리카, 그리고 비밀결사", "units": ["ch05", "ch06", "ch07", "ch08", "ch09"]},
    {"part": "p3", "name": "3부 — 임시정부의 봄과 결렬", "units": ["ch10", "ch11", "ch12", "ch13", "ch14", "ch15"]},
    {"part": "p4", "name": "4부 — 다시 모으려는 손", "units": ["ch16", "ch17", "ch18", "ch19"]},
    {"part": "p5", "name": "5부 — 모은 것이 흩어질 때", "units": ["ch20", "ch21", "ch22"]},
    {"part": "epilogue", "name": "종장", "units": ["ch99"]},
]


# ── 미니 마크다운 → HTML 변환기 (stdlib only, 이스케이프 안전) ─────────────────
def render_inline(text):
    """문단 내부 인라인 변환. 먼저 전부 escape 한 뒤 굵게/기울임만 복원.
    소설 본문에는 링크가 없다(검증 평면 외부) → 링크 변환 비활성(추측 방지)."""
    s = html.escape(text, quote=False)
    # **굵게** → <strong> (afterword 에서 사용)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    # *기울임* → <em> (afterword 인라인·일부 본문 단어 강조)
    s = re.sub(r"(?<![*])\*(?!\s)([^*\n]+?)(?<!\s)\*(?![*])", r"<em>\1</em>", s)
    return s


def md_to_html(md_text, drop_first_heading=True):
    """소설 마크다운(단순 문법)을 본문 HTML 문자열로 변환한다.

    지원 블록:
      # 제목         → drop_first_heading=True 면 본문에서 제거(JSON title 로 분리)
      ## 소제목       → <h2 class="nv-subhead">
      > 인용          → <blockquote class="nv-aside"> (연속 줄 병합)
      ---            → <hr class="nv-rule">
      * (단독)        → <hr class="nv-scene"> (장면 전환 구분)
      *...* (전체 줄) → <p class="nv-emph"> (편지·내면 — 기울임 문단)
      - 항목          → <ul class="nv-list"><li>
      그 외 문단       → <p>

    변환되지 않은(미지원) 마크업은 unhandled 리스트로 수집해 보고한다.
    반환: (html_str, unhandled_markup_list)
    """
    lines = md_text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    out = []
    unhandled = []
    i = 0
    first_heading_dropped = False

    def flush_blockquote(buf):
        if not buf:
            return
        inner = "<br>".join(render_inline(b) for b in buf)
        out.append(f'<blockquote class="nv-aside"><p>{inner}</p></blockquote>')

    def flush_list(buf):
        if not buf:
            return
        items = "".join(f"<li>{render_inline(b)}</li>" for b in buf)
        out.append(f'<ul class="nv-list">{items}</ul>')

    while i < len(lines):
        raw = lines[i]
        line = raw.strip()

        # 빈 줄 — 블록 구분
        if line == "":
            i += 1
            continue

        # 제목 (# ...)
        if line.startswith("# "):
            if drop_first_heading and not first_heading_dropped:
                first_heading_dropped = True
                i += 1
                continue
            # 본문 중 추가 h1 은 비정상 — h2 로 강등하고 보고
            unhandled.append(f"본문 내 추가 h1: {line[:40]}")
            out.append(f'<h2 class="nv-subhead">{render_inline(line[2:].strip())}</h2>')
            i += 1
            continue

        # 소제목 (## ...)
        if line.startswith("## "):
            out.append(f'<h2 class="nv-subhead">{render_inline(line[3:].strip())}</h2>')
            i += 1
            continue
        if line.startswith("### "):
            out.append(f'<h3 class="nv-subhead-sm">{render_inline(line[4:].strip())}</h3>')
            i += 1
            continue
        # ## 보다 깊은(미지원) 헤딩 보고
        if re.match(r"^#{4,}\s", line):
            unhandled.append(f"미지원 헤딩 깊이: {line[:40]}")
            out.append(f'<h3 class="nv-subhead-sm">{render_inline(line.lstrip("# ").strip())}</h3>')
            i += 1
            continue

        # 수평선 (---)
        if re.match(r"^-{3,}$", line):
            out.append('<hr class="nv-rule">')
            i += 1
            continue

        # 장면 전환 (단독 *) — 별표 하나만 있는 줄
        if line == "*":
            out.append('<hr class="nv-scene" aria-hidden="true">')
            i += 1
            continue

        # 전체 줄 기울임 문단 (*...* — 편지·내면). 별표로 시작하고 별표로 끝나며 내부에 별표 없음.
        m_emph = re.match(r"^\*([^*]+)\*$", line)
        if m_emph:
            out.append(f'<p class="nv-emph">{render_inline(m_emph.group(1).strip())}</p>')
            i += 1
            continue

        # 인용 (> ...) — 연속 줄 병합
        if line.startswith(">"):
            buf = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                buf.append(re.sub(r"^>\s?", "", lines[i].strip()))
                i += 1
            flush_blockquote(buf)
            continue

        # 목록 (- ...) — 연속 줄 병합
        if re.match(r"^[-*+]\s+", line):
            buf = []
            while i < len(lines) and re.match(r"^[-*+]\s+", lines[i].strip()):
                buf.append(re.sub(r"^[-*+]\s+", "", lines[i].strip()))
                i += 1
            flush_list(buf)
            continue

        # 일반 문단 (한 줄 = 한 문단; 소설은 문단 사이 빈 줄 사용)
        out.append(f"<p>{render_inline(line)}</p>")
        i += 1

    return "\n".join(out), unhandled


def extract_title(md_text):
    """첫 '# ...' 라인을 장 제목으로 추출(# 제거). 없으면 빈 문자열."""
    for line in md_text.replace("\r\n", "\n").split("\n"):
        s = line.strip()
        if s.startswith("# "):
            return s[2:].strip()
    return ""


def count_chars(md_text, drop_heading=True):
    """본문 자수 — 공백·개행·마크다운 기호 제외한 한글/문자 수(원본 대조용 근사)."""
    text = md_text
    if drop_heading:
        text = re.sub(r"^#\s.*$", "", text, count=1, flags=re.MULTILINE)
    # 마크다운 기호·공백 제거 후 글자 수
    text = re.sub(r"[#>*\-_`\[\]()|~=]", "", text)
    text = re.sub(r"\s+", "", text)
    return len(text)


def afterword_tagline(md_text):
    """작가의 말 첫 본문 단락에서 한 줄 소개를 발췌한다(새 사실 생성 금지 — 원문 발췌).
    blockquote(>)·heading·hr 을 건너뛴 첫 일반 문단의 첫 문장."""
    for line in md_text.replace("\r\n", "\n").split("\n"):
        s = line.strip()
        if not s or s.startswith(("#", ">", "-", "*", "|")) or re.match(r"^-{3,}$", s):
            continue
        # 첫 문장(마침표 기준) — 인라인 마크업 제거
        plain = re.sub(r"\*\*?([^*]+)\*\*?", r"\1", s)
        sentence = re.split(r"(?<=[.다])\s", plain, maxsplit=1)[0]
        return sentence.strip()
    return ""


def main():
    errors = []
    all_unhandled = []
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # 입력 파일 수집 (순서 = PARTS 의 units 순서)
    ordered_units = [u for part in PARTS for u in part["units"]]
    part_of = {u: part["part"] for part in PARTS for u in part["units"]}

    generated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    toc = []
    total_chars = 0
    written = 0

    # ── 장별 처리 ────────────────────────────────────────────────────────────
    order = 0
    for stem in ordered_units:
        src = CHAPTERS_DIR / f"{stem}.md"
        if not src.exists():
            errors.append(f"누락: {src.relative_to(REPO_ROOT)}")
            continue
        md = src.read_text(encoding="utf-8")
        title = extract_title(md)
        if not title:
            errors.append(f"제목 없음(첫 # 라인 부재): {stem}")
        body_html, unhandled = md_to_html(md, drop_first_heading=True)
        if unhandled:
            all_unhandled.extend(f"{stem}: {u}" for u in unhandled)
        chars = count_chars(md)
        total_chars += chars

        chapter = {
            "id": stem,
            "title": title,
            "part": part_of[stem],
            "html": body_html,
        }
        (OUT_DIR / f"{stem}.json").write_text(
            json.dumps(chapter, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        written += 1

        toc.append({"id": stem, "title": title, "part": part_of[stem], "order": order, "chars": chars})
        order += 1

    # ── 작가의 말 ────────────────────────────────────────────────────────────
    tagline = ""
    if not AFTERWORD.exists():
        errors.append(f"누락: {AFTERWORD.relative_to(REPO_ROOT)}")
    else:
        amd = AFTERWORD.read_text(encoding="utf-8")
        a_title = extract_title(amd) or "작가의 말"
        a_html, a_unhandled = md_to_html(amd, drop_first_heading=True)
        if a_unhandled:
            all_unhandled.extend(f"afterword: {u}" for u in a_unhandled)
        a_chars = count_chars(amd)
        total_chars += a_chars
        tagline = afterword_tagline(amd)

        afterword_obj = {
            "id": "afterword",
            "title": a_title,
            "part": "afterword",
            "html": a_html,
        }
        (OUT_DIR / "afterword.json").write_text(
            json.dumps(afterword_obj, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        written += 1
        # 목차 마지막 항목으로 작가의 말
        toc.append({"id": "afterword", "title": a_title, "part": "afterword", "order": order, "chars": a_chars})

    # ── index.json (목차 + 작품 메타) ─────────────────────────────────────────
    index = {
        "work": {
            "title": WORK_TITLE,
            "subtitle": WORK_SUBTITLE,
            "tagline": tagline,
            "unit_count": len(ordered_units),         # 24 (서장+22+종장)
            "total_chars": total_chars,
        },
        "parts": [
            {
                "part": p["part"],
                "name": p["name"],
                "chapters": [u for u in p["units"]],
            }
            for p in PARTS
        ]
        + [{"part": "afterword", "name": "작가의 말", "chapters": ["afterword"]}],
        "toc": toc,
        "generated": generated,
    }
    (OUT_DIR / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # ── assert: 24유닛 + afterword = 25 파일 ──────────────────────────────────
    expected_files = len(ordered_units) + 1  # 24 + afterword
    json_files = sorted(p.name for p in OUT_DIR.glob("ch*.json")) + (
        ["afterword.json"] if (OUT_DIR / "afterword.json").exists() else []
    )
    chapter_json_count = len(list(OUT_DIR.glob("ch*.json")))
    actual_chapter_files = chapter_json_count + (1 if (OUT_DIR / "afterword.json").exists() else 0)

    print("=" * 70)
    print(f"build_novel.py — 산출 디렉토리: {OUT_DIR.relative_to(REPO_ROOT)}")
    print("=" * 70)
    print(f"작품      : 『{WORK_TITLE}』 (부제: {WORK_SUBTITLE})")
    print(f"한 줄 소개 : {tagline}")
    print(f"장 파일    : {chapter_json_count} (ch*.json) + afterword.json = {actual_chapter_files}")
    print(f"기대 파일  : {expected_files} (24유닛 + 작가의 말)")
    print(f"자수 합계  : {total_chars:,} (본문, 기호·공백 제외 근사)")
    print(f"index.json : work + parts {len(index['parts'])}개 + toc {len(toc)}개")

    if all_unhandled:
        print("-" * 70)
        print("변환 누락 마크업(보고):")
        for u in all_unhandled:
            print(f"  - {u}")

    # 검증
    if actual_chapter_files != expected_files:
        errors.append(
            f"파일 수 불일치: 산출 {actual_chapter_files} ≠ 기대 {expected_files}"
        )
    if len(toc) != expected_files:
        errors.append(f"toc 항목 수 불일치: {len(toc)} ≠ {expected_files}")

    print("=" * 70)
    if errors:
        print("FAIL — 다음 오류:")
        for e in errors:
            print(f"  ✗ {e}")
        sys.exit(1)
    print("PASS — 25파일(24유닛 + 작가의 말) 산출·목차 정합 확인.")
    sys.exit(0)


if __name__ == "__main__":
    main()
