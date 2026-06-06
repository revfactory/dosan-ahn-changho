#!/usr/bin/env python3
"""Extract ALL display text from the render plane (HTML static + data JSON)."""
import json, re, os, glob
from html.parser import HTMLParser

SITE = "/Users/robin/Downloads/DOSAN/site"

class TextExtractor(HTMLParser):
    SKIP = {"script", "style", "noscript"}
    def __init__(self):
        super().__init__(); self.texts=[]; self._skip=0
        self.meta=[]
    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP: self._skip+=1
        d=dict(attrs)
        if tag=="meta" and ("name" in d or "property" in d) and "content" in d:
            self.meta.append((d.get("name") or d.get("property"), d["content"]))
        if tag=="title": self._intitle=True
    def handle_endtag(self, tag):
        if tag in self.SKIP: self._skip-=1
        if tag=="title": self._intitle=False
    def handle_data(self, data):
        if not self._skip and data.strip():
            self.texts.append((data.strip(), self.getpos()))

# 1. HTML static text + meta
html_records=[]   # (file, location, text)
for hf in sorted(glob.glob(f"{SITE}/*.html")):
    base=os.path.basename(hf)
    p=TextExtractor()
    p.feed(open(hf, encoding="utf-8").read())
    for txt,pos in p.texts:
        html_records.append((base, f"line{pos[0]}", txt))
    for name,content in p.meta:
        html_records.append((base, f"meta:{name}", content))

# 2. Page JSON display text (paragraph.text, blockquote.lines, list.items, table headers/rows, lead, heading, title)
page_records=[]   # (file, jsonpath, text)
def walk_page(o, path, recs, fname):
    if isinstance(o, dict):
        t=o.get("type")
        if t=="paragraph" and isinstance(o.get("text"),str):
            recs.append((fname, path+".text", o["text"]))
        elif t=="blockquote":
            for i,l in enumerate(o.get("lines",[])):
                if isinstance(l,str): recs.append((fname, f"{path}.lines[{i}]", l))
        elif t=="list":
            for i,it in enumerate(o.get("items",[])):
                if isinstance(it,str): recs.append((fname, f"{path}.items[{i}]", it))
        elif t=="table":
            for i,h in enumerate(o.get("headers",[])):
                if isinstance(h,str): recs.append((fname, f"{path}.headers[{i}]", h))
            for r,row in enumerate(o.get("rows",[])):
                for c,cell in enumerate(row):
                    if isinstance(cell,str): recs.append((fname, f"{path}.rows[{r}][{c}]", cell))
        for k,v in o.items():
            walk_page(v, f"{path}.{k}", recs, fname)
    elif isinstance(o, list):
        for i,v in enumerate(o):
            walk_page(v, f"{path}[{i}]", recs, fname)

for pf in sorted(glob.glob(f"{SITE}/data/pages/*.json")):
    base="pages/"+os.path.basename(pf)
    d=json.load(open(pf, encoding="utf-8"))
    if isinstance(d.get("title"),str): page_records.append((base,"title",d["title"]))
    for i,lb in enumerate(d.get("lead",[])):
        if isinstance(lb,dict) and isinstance(lb.get("text"),str):
            page_records.append((base,f"lead[{i}].text",lb["text"]))
    for si,s in enumerate(d.get("sections",[])):
        if isinstance(s.get("heading"),str): page_records.append((base,f"sections[{si}].heading",s["heading"]))
        walk_page(s.get("blocks",[]), f"sections[{si}].blocks", page_records, base)

# 3. Top-level data display fields
data_records=[]  # (file, path, text)
# timeline.json: title, summary, detail, dispute_note, place.name, place.modern_name
tl=json.load(open(f"{SITE}/data/timeline.json", encoding="utf-8"))
for e in tl["events"]:
    eid=e["id"]
    for fld in ("title","summary","detail","dispute_note"):
        if isinstance(e.get(fld),str) and e[fld].strip():
            data_records.append(("data/timeline.json", f"{eid}.{fld}", e[fld]))
    pl=e.get("place") or {}
    for fld in ("name","modern_name"):
        if isinstance(pl.get(fld),str) and pl[fld].strip():
            data_records.append(("data/timeline.json", f"{eid}.place.{fld}", pl[fld]))
# network.json: nodes summary/description/label, edges summary/description/label
nw=json.load(open(f"{SITE}/data/network.json", encoding="utf-8"))
for n in nw.get("nodes",[]):
    nid=n.get("id")
    for fld in ("label","name","summary","description","role","note"):
        if isinstance(n.get(fld),str) and n[fld].strip():
            data_records.append(("data/network.json", f"node:{nid}.{fld}", n[fld]))
for ed in nw.get("edges",[]) + nw.get("edges_unconfirmed",[]):
    eid=ed.get("id") or f"{ed.get('source')}->{ed.get('target')}"
    for fld in ("label","summary","description","note","relation"):
        if isinstance(ed.get(fld),str) and ed[fld].strip():
            data_records.append(("data/network.json", f"edge:{eid}.{fld}", ed[fld]))
# images.json: caption, title, credit, alt
im=json.load(open(f"{SITE}/data/images.json", encoding="utf-8"))
for img in im.get("images",[]):
    iid=img.get("id")
    for fld in ("title","caption","credit","alt","description"):
        if isinstance(img.get(fld),str) and img[fld].strip():
            data_records.append(("data/images.json", f"{iid}.{fld}", img[fld]))
# citations.json sources display text
ci=json.load(open(f"{SITE}/data/citations.json", encoding="utf-8"))
for sid,s in (ci.get("sources") or {}).items() if isinstance(ci.get("sources"),dict) else []:
    for fld in ("title","display","citation","note"):
        if isinstance(s.get(fld),str) and s[fld].strip():
            data_records.append(("data/citations.json", f"{sid}.{fld}", s[fld]))
if isinstance(ci.get("sources"),list):
    for s in ci["sources"]:
        sid=s.get("id")
        for fld in ("title","display","citation","note"):
            if isinstance(s.get(fld),str) and s[fld].strip():
                data_records.append(("data/citations.json", f"{sid}.{fld}", s[fld]))
# archives.json catalog display text
ar=json.load(open(f"{SITE}/data/archives.json", encoding="utf-8"))
for it in ar.get("catalog",[]):
    aid=it.get("id")
    for fld in ("title","summary","description","note","content","caption"):
        if isinstance(it.get(fld),str) and it[fld].strip():
            data_records.append(("data/archives.json", f"{aid}.{fld}", it[fld]))

out={"html":html_records,"pages":page_records,"data":data_records}
json.dump(out, open("/Users/robin/Downloads/DOSAN/_workspace/05_qa/_scratch/extracted.json","w"), ensure_ascii=False, indent=1)
print("HTML records:", len(html_records))
print("Page JSON records:", len(page_records))
print("Top-level data records:", len(data_records))
print("TOTAL text records:", len(html_records)+len(page_records)+len(data_records))
