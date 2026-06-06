#!/usr/bin/env python3
# measure_perf.py — performance-optimizer 첫 로드 실측 (측정 전용)
# 각 페이지가 실제 첫 로드에 가져오는 자산만 합산한다(디렉토리 총량 아님).
#   = HTML + (head의 CSS link) + (진입 module의 import 전이 폐쇄 JS) + (초기 fetch JSON)
# 이미지 제외. 외부 CDN(폰트/Leaflet/Pretendard)은 별도 집계(예산은 동일출처 자산 기준).
import os, re, json, sys

SITE = os.path.join(os.path.dirname(__file__), "..", "..", "site")
SITE = os.path.abspath(SITE)

def size(rel):
    p = os.path.join(SITE, rel)
    try:
        return os.path.getsize(p)
    except OSError:
        return None

def kb(n):
    return f"{n/1024:.1f}"

# --- 진입 JS의 import 전이 폐쇄(상대 경로 ./ 만) ---
IMPORT_RE = re.compile(r"""import\s+(?:.+?\s+from\s+)?['"](\./[^'"]+)['"]""")
def js_closure(entry_rel):
    seen, stack = set(), [entry_rel]
    while stack:
        cur = stack.pop()
        if cur in seen: continue
        seen.add(cur)
        p = os.path.join(SITE, cur)
        try:
            src = open(p, encoding="utf-8").read()
        except OSError:
            continue
        base = os.path.dirname(cur)
        for m in IMPORT_RE.finditer(src):
            dep = os.path.normpath(os.path.join(base, m.group(1))).replace(os.sep, "/")
            stack.append(dep)
    return sorted(seen)

# --- HTML에서 head CSS link(상대) + 진입 module + classic script ---
def html_assets(html_rel):
    p = os.path.join(SITE, html_rel)
    src = open(p, encoding="utf-8").read()
    css_local, css_cdn = [], []
    for m in re.finditer(r'<link[^>]+rel=["\']stylesheet["\'][^>]*>', src):
        tag = m.group(0)
        href = re.search(r'href=["\']([^"\']+)["\']', tag)
        if not href: continue
        h = href.group(1)
        (css_cdn if h.startswith("http") else css_local).append(h)
    modules = re.findall(r'<script[^>]+type=["\']module["\'][^>]*src=["\']([^"\']+)["\']', src)
    classics = re.findall(r'<script(?![^>]*type=["\']module)[^>]*src=["\']([^"\']+)["\']', src)
    return css_local, css_cdn, modules, classics

# --- 각 페이지의 초기 fetch JSON (코드 분석으로 확정한 목록) ---
FETCH = {
    "index.html":         ["data/pages/home.json","data/meta.json","data/images.json","data/citations.json"],
    "life.html":          ["data/pages/life.json","data/images.json","data/citations.json"],
    "philosophy.html":    ["data/pages/philosophy.json","data/images.json","data/citations.json"],
    "organizations.html": ["data/pages/organizations.json","data/images.json","data/citations.json","data/network.json"],
    "people.html":        ["data/pages/people.json","data/network.json","data/images.json","data/citations.json"],
    "archives.html":      ["data/pages/archives.json","data/archives.json","data/images.json","data/citations.json"],
    "references.html":    ["data/pages/references.json","data/citations.json"],
    "gallery.html":       ["data/pages/gallery.json","data/images.json","data/citations.json"],
    "timeline.html":      ["data/timeline.json","data/pages/timeline.json","data/citations.json"],
    "map.html":           ["data/timeline.json","data/pages/map.json","data/citations.json","data/network.json"],
}

PAGES = ["index.html","life.html","timeline.html","map.html","organizations.html",
         "philosophy.html","people.html","archives.html","gallery.html","references.html"]

BUDGET = 200*1024
rows = []
for page in PAGES:
    css_local, css_cdn, modules, classics = html_assets(page)
    html_b = size(page)
    css_b = sum(size(c) or 0 for c in css_local)
    js_files = set()
    for mod in modules:
        if mod.startswith("http"): continue
        for f in js_closure(mod.lstrip("/")):
            js_files.add(f)
    js_b = sum(size(f) or 0 for f in js_files)
    json_b = sum(size(j) or 0 for j in FETCH[page])
    total = html_b + css_b + js_b + json_b
    # 요청 수: HTML(1) + local css + js closure + json + cdn css + classic script
    req = 1 + len(css_local) + len(js_files) + len(FETCH[page]) + len(css_cdn) + len([c for c in classics if c.startswith("http")])
    rows.append({
        "page": page, "html": html_b, "css": css_b, "js": js_b, "json": json_b,
        "total": total, "req": req, "css_cdn": css_cdn, "classics": classics,
        "json_files": [(j, size(j)) for j in FETCH[page]],
        "js_files": sorted(js_files),
    })

print(f"{'page':<20}{'HTML':>8}{'CSS':>9}{'JS':>9}{'JSON':>10}{'TOTAL':>10}  {'req':>4}  budget")
print("-"*84)
for r in rows:
    status = "OK" if r["total"] < BUDGET else "OVER"
    print(f"{r['page']:<20}{kb(r['html']):>7}K{kb(r['css']):>8}K{kb(r['js']):>8}K{kb(r['json']):>9}K{kb(r['total']):>9}K  {r['req']:>4}  {status}")

print("\n=== JSON breakdown per page (이미지 제외 예산의 지배 요인) ===")
for r in rows:
    print(f"\n[{r['page']}] total {kb(r['total'])}K / req {r['req']}")
    for j, s in r["json_files"]:
        flag = " <<150K초과" if (s or 0) > 150*1024 else ""
        print(f"    {kb(s or 0):>8}K  {j}{flag}")

print("\n=== 외부 CDN (동일출처 예산 외, 별도 평가) ===")
seen=set()
for r in rows:
    for c in r["css_cdn"]:
        if c not in seen: print("  CSS:", c); seen.add(c)
    for c in r["classics"]:
        if c.startswith("http") and c not in seen: print("  JS :", c); seen.add(c)

# meta.json 통계용
print("\n=== 큰 JSON 단독 크기 ===")
for j in ["data/timeline.json","data/network.json","data/citations.json","data/images.json","data/archives.json"]:
    print(f"  {kb(size(j) or 0):>8}K  {j}")
