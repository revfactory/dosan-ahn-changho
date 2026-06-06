#!/usr/bin/env python3
"""check_links.py — 정적 사이트 링크·리소스 전수 대조.

site 디렉토리의 모든 HTML에서 href/src(및 srcset)를 추출해
로컬 파일 실존 여부를 대조하고, 끊어진 참조를 출력한다.

사용법:
    python3 check_links.py <site_dir>

종료 코드:
    0 — 끊어진 참조 없음
    1 — 끊어진 참조 존재 (또는 인자 오류)

표준 라이브러리만 사용한다. 외부 URL(http/https 등)은 존재 검사
대상이 아니며 참고용 목록으로만 출력한다.
"""

import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

# 로컬 존재 검사에서 제외하는 스킴
EXTERNAL_SCHEMES = ("http:", "https:", "//", "mailto:", "tel:", "javascript:", "data:")

# 참조를 추출할 (태그, 속성) 목록
REF_ATTRS = {
    ("a", "href"), ("link", "href"), ("script", "src"), ("img", "src"),
    ("source", "src"), ("video", "src"), ("audio", "src"),
    ("iframe", "src"), ("object", "data"), ("use", "href"),
}


class RefExtractor(HTMLParser):
    """HTML에서 href/src/srcset 참조를 수집한다."""

    def __init__(self):
        super().__init__()
        self.refs = []  # (url, tag, attr)

    def handle_starttag(self, tag, attrs):
        for attr, value in attrs:
            if value is None:
                continue
            if (tag, attr) in REF_ATTRS:
                self.refs.append((value.strip(), tag, attr))
            elif attr == "srcset":
                # "url1 1x, url2 2x" 형식 — URL 부분만 추출
                for part in value.split(","):
                    url = part.strip().split()[0] if part.strip() else ""
                    if url:
                        self.refs.append((url, tag, "srcset"))


def is_external(url: str) -> bool:
    lowered = url.lower()
    return any(lowered.startswith(s) for s in EXTERNAL_SCHEMES)


def resolve_target(url: str, html_file: Path, site_dir: Path):
    """참조 URL을 로컬 파일 경로로 해석한다. 검사 불요 시 None."""
    # 쿼리스트링·프래그먼트 제거
    parsed = urlparse(url)
    path = unquote(parsed.path)
    if not path:  # 순수 앵커(#section) 또는 빈 참조
        return None
    if path.startswith("/"):
        # 루트 상대 — site 디렉토리를 루트로 간주
        return (site_dir / path.lstrip("/")).resolve()
    return (html_file.parent / path).resolve()


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

    broken = []     # (html, url, resolved)
    externals = set()
    checked = 0

    for html_file in html_files:
        parser = RefExtractor()
        try:
            parser.feed(html_file.read_text(encoding="utf-8", errors="replace"))
        except Exception as e:  # 파싱 실패도 결함이다
            broken.append((html_file, f"<파싱 실패: {e}>", None))
            continue

        for url, tag, attr in parser.refs:
            if not url:
                continue
            if is_external(url):
                externals.add(url)
                continue
            target = resolve_target(url, html_file, site_dir)
            if target is None:
                continue
            checked += 1
            # 디렉토리 참조는 index.html로 폴백 확인
            exists = target.exists() and (
                target.is_file() or (target / "index.html").is_file()
            )
            if not exists:
                broken.append((html_file, f"<{tag} {attr}> {url}", target))

    print(f"검사: HTML {len(html_files)}개, 로컬 참조 {checked}건")

    if externals:
        print(f"\n[참고] 외부 URL {len(externals)}건 — 존재 검사 제외, 표본 확인 권장:")
        for url in sorted(externals):
            print(f"  - {url}")

    if broken:
        print(f"\n[결함] 끊어진 참조 {len(broken)}건:")
        for html_file, ref, target in broken:
            rel = html_file.relative_to(site_dir)
            print(f"  - {rel}: {ref}")
            if target is not None:
                print(f"      → 미존재 경로: {target}")
        return 1

    print("\n통과: 끊어진 로컬 참조 0건")
    return 0


if __name__ == "__main__":
    sys.exit(main())
