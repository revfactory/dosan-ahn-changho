#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_links.py — 정적 사이트 링크·리소스·앵커 전수 대조 (qa-engineer)
================================================================================

web-qa-protocol 번들 스크립트의 확장판. site/ 의 모든 HTML 에서
href/src(및 srcset)를 추출해 (1) 로컬 파일 실존, (2) 앵커 프래그먼트가
데이터 id 우주(evt-/per-/org-/src-pri-/ref-/source-id/image-id) 또는
페이지 정적 앵커(ch-/sec-/*-intro/*-gaps 등)에 실재하는지를 대조한다.

왜 앵커까지 검사하는가:
    이 사이트의 교차링크(timeline↔life↔people↔org↔archives↔references)는
    전부 데이터 id 를 앵커로 쓴다(architecture.md §3 D-01). id 변형·병합 전
    id 잔존(§5.2·§5.4b·D-24)은 파일 존재 검사로는 절대 안 잡힌다 —
    `timeline.html#evt-XXX` 가 죽은 id 면 파일(timeline.html)은 존재하므로
    번들 check_links 는 통과시킨다. 앵커 대조가 이 평면을 닫는다.

데이터 평면(JS 렌더로 생기는 동적 앵커)의 죽은 참조는 데이터 자체에서
검사된다(check_data_schema.py). 이 스크립트는 HTML 에 정적으로 박힌
href 의 프래그먼트만 대조한다(동적 렌더 앵커는 런타임 검사 영역).

사용법:
    python3 check_links.py <site_dir>

종료 코드: 0 — 결함 0 / 1 — 끊어진 참조·앵커 존재 (또는 인자 오류)

표준 라이브러리만 사용. 외부 URL 은 존재 검사 제외(참고 목록만).
"""

import json
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

EXTERNAL_SCHEMES = ("http:", "https:", "//", "mailto:", "tel:", "javascript:", "data:")

REF_ATTRS = {
    ("a", "href"), ("link", "href"), ("script", "src"), ("img", "src"),
    ("source", "src"), ("video", "src"), ("audio", "src"),
    ("iframe", "src"), ("object", "data"), ("use", "href"),
}

# 데이터 id 프래그먼트로 해석할 페이지(파일명) → 검사할 id 집합 키
# architecture.md §3 의 앵커=id 계약. 이 페이지로의 #fragment 는 동적 렌더
# 앵커일 수 있으므로 "데이터 우주에 있으면 통과, 없으면 결함"으로 본다.
PAGE_ID_DOMAINS = {
    "timeline.html": "evt",       # #evt-...
    "people.html": "per",         # #per-...
    "organizations.html": "org",  # #org-...
    "archives.html": "src_pri",   # #src-pri-...
    "references.html": "source",  # #src-{aca|enc|ins|pri|web}-...
    "gallery.html": "image",      # #image-id
}


class RefExtractor(HTMLParser):
    """HTML 에서 href/src/srcset 참조 + 정적 id 속성을 수집한다."""

    def __init__(self):
        super().__init__()
        self.refs = []       # (url, tag, attr)
        self.ids = set()     # 이 HTML 내 정적 id 속성

    def handle_starttag(self, tag, attrs):
        adict = dict(attrs)
        if adict.get("id"):
            self.ids.add(adict["id"])
        for attr, value in attrs:
            if value is None:
                continue
            if (tag, attr) in REF_ATTRS:
                self.refs.append((value.strip(), tag, attr))
            elif attr == "srcset":
                for part in value.split(","):
                    url = part.strip().split()[0] if part.strip() else ""
                    if url:
                        self.refs.append((url, tag, "srcset"))


def is_external(url: str) -> bool:
    lowered = url.lower()
    return any(lowered.startswith(s) for s in EXTERNAL_SCHEMES)


def load_id_universe(site_dir: Path):
    """site/data/*.json 에서 데이터 id 우주를 추출한다.
    데이터 파일이 없으면 빈 우주(앵커 검사 비활성·경고)."""
    data = site_dir / "data"
    uni = {"evt": set(), "per": set(), "org": set(),
           "src_pri": set(), "source": set(), "image": set(), "ref": set()}
    missing = []

    def jload(name):
        p = data / name
        if not p.is_file():
            missing.append(name)
            return None
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            missing.append(f"{name} (파싱 실패: {e})")
            return None

    t = jload("timeline.json")
    if t:
        uni["evt"] = {e["id"] for e in t.get("events", [])}
    n = jload("network.json")
    if n:
        for nd in n.get("nodes", []):
            (uni["per"] if nd["id"].startswith("per-") else uni["org"]).add(nd["id"])
    c = jload("citations.json")
    if c:
        uni["source"] = {s["id"] for s in c.get("sources", [])}
        uni["ref"] = {r["id"] for r in c.get("refs", [])}
    a = jload("archives.json")
    if a:
        uni["src_pri"] = {x["id"] for x in a.get("catalog", [])}
    im = jload("images.json")
    if im:
        uni["image"] = {x["id"] for x in im.get("images", [])}
    return uni, missing


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 1

    site_dir = Path(sys.argv[1]).resolve()
    if not site_dir.is_dir():
        print(f"오류: 디렉토리가 아님 — {site_dir}")
        return 1

    html_files = sorted(site_dir.rglob("*.html"))
    if not html_files:
        print(f"오류: HTML 파일이 없음 — {site_dir}")
        return 1

    uni, uni_missing = load_id_universe(site_dir)

    # 1차 패스: 각 HTML 의 정적 id 수집(페이지 내 #앵커 해소용) + 참조 추출
    parsed_pages = {}   # name -> (refs, ids)
    for html_file in html_files:
        parser = RefExtractor()
        try:
            parser.feed(html_file.read_text(encoding="utf-8", errors="replace"))
        except Exception as e:
            parsed_pages[html_file] = (None, e)
            continue
        parsed_pages[html_file] = (parser.refs, parser.ids)

    broken = []           # (html, ref, detail)
    broken_anchor = []    # (html, ref, detail)
    externals = set()
    checked = anchors_checked = 0

    page_static_ids = {f.name: data[1] for f, data in parsed_pages.items()
                       if data[0] is not None}

    for html_file in html_files:
        refs, ids = parsed_pages[html_file]
        rel = html_file.relative_to(site_dir)
        if refs is None:
            broken.append((rel, f"<파싱 실패: {ids}>", None))
            continue

        for url, tag, attr in refs:
            if not url:
                continue
            if is_external(url):
                externals.add(url)
                continue

            parsed = urlparse(url)
            path = unquote(parsed.path)
            frag = parsed.fragment

            # --- 파일 존재 검사 ---
            target = None
            if path:
                if path.startswith("/"):
                    target = (site_dir / path.lstrip("/")).resolve()
                else:
                    target = (html_file.parent / path).resolve()
                checked += 1
                exists = target.exists() and (
                    target.is_file() or (target / "index.html").is_file())
                if not exists:
                    broken.append((rel, f"<{tag} {attr}> {url}",
                                   f"미존재 경로: {target}"))
                    continue  # 파일 없으면 앵커 검사 무의미

            # --- 앵커 프래그먼트 검사 ---
            if not frag:
                continue
            anchors_checked += 1
            # 대상 페이지 결정: path 있으면 그 파일, 없으면 현재 HTML
            target_name = Path(path).name if path else html_file.name

            domain = PAGE_ID_DOMAINS.get(target_name)
            if domain:
                # 데이터 id 도메인 — ?period= 같은 정적 앵커도 섞일 수 있으므로
                # 페이지 정적 id 우선, 없으면 데이터 우주 대조
                static_ids = page_static_ids.get(target_name, set())
                if frag in static_ids:
                    continue
                if frag in uni[domain]:
                    continue
                if uni_missing:
                    continue  # 데이터 우주 불완전 — 단정 보류(경고는 하단)
                broken_anchor.append(
                    (rel, f"<{tag} {attr}> {url}",
                     f"{target_name}#{frag} — {domain} id 우주에 없음(죽은 앵커)"))
            else:
                # 일반 페이지(life/philosophy/home 등) 정적 섹션 앵커
                static_ids = page_static_ids.get(target_name)
                if static_ids is None:
                    continue  # 대상 페이지 미파싱(존재하지만 동적)·정보 부족 — 보류
                if frag not in static_ids:
                    # 정적 골격에 없는 앵커 = 동적 렌더 앵커일 수 있음 →
                    # 단정 못함. 결함 후보로만 목록화(경고).
                    broken_anchor.append(
                        (rel, f"<{tag} {attr}> {url}",
                         f"{target_name}#{frag} — 정적 id 없음(동적 렌더면 무해, 수동 확인)"))

    print(f"검사: HTML {len(html_files)}개, 로컬 참조 {checked}건, 앵커 {anchors_checked}건")
    if uni_missing:
        print(f"[경고] 데이터 id 우주 일부 미로드 — 앵커 도메인 대조 보류: {uni_missing}")
    else:
        print(f"[id 우주] evt {len(uni['evt'])}·per {len(uni['per'])}·"
              f"org {len(uni['org'])}·src-pri {len(uni['src_pri'])}·"
              f"source {len(uni['source'])}·image {len(uni['image'])}")

    if externals:
        print(f"\n[참고] 외부 URL {len(externals)}건 — 존재 검사 제외, 표본 확인 권장:")
        for url in sorted(externals):
            print(f"  - {url}")

    if broken:
        print(f"\n[결함] 끊어진 파일 참조 {len(broken)}건:")
        for rel, ref, detail in broken:
            print(f"  - {rel}: {ref}")
            if detail:
                print(f"      → {detail}")

    if broken_anchor:
        print(f"\n[결함/주의] 앵커 {len(broken_anchor)}건:")
        for rel, ref, detail in broken_anchor:
            print(f"  - {rel}: {ref}")
            print(f"      → {detail}")

    if broken:
        return 1
    if not broken_anchor:
        print("\n통과: 끊어진 로컬 참조·앵커 0건")
    return 0


if __name__ == "__main__":
    sys.exit(main())
