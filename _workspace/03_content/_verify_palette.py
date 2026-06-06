#!/usr/bin/env python3
# 한정 문형 팔레트 변주 자가 검증 (copy-editor, Phase 5)
# 사용: python3 _verify_palette.py
import re, json, sys, glob, os

WS = os.path.dirname(os.path.abspath(__file__))  # 03_content
ROOT = os.path.dirname(WS)  # _workspace

# 전승류(C등급) 팔레트 — 표면형 -> 정규 클래스. '추정된다'는 추론류(금지 교차) 별도 추적.
PALETTE = {
    "전해진다": "전해진다", "전해지며": "전해진다", "전해지나": "전해진다", "전해지고": "전해진다",
    "했다고 한다": "한다", "였다고 한다": "한다", "되었다고 한다": "한다",
    "것이었다고 한다": "한다", "다고 한다": "한다", "다고 하며": "한다", "다고 하나": "한다",
    "기록되어 있다": "기록되어", "기록되어 있으나": "기록되어", "기록되어 있으며": "기록되어",
    "라는 기록이 있다": "기록이있다",
    "알려져 있다": "알려져", "알려져 있으며": "알려져", "알려져 있으나": "알려져", "알려진": "알려져_관형",
    "기록에 따르면": "문두",
    "라고 적는다": "적는다", "라고 적은": "적는다",
}
# '알려진'(관형, 예: '18조목으로 알려진')은 한정 보유로 카운트하되 회전 대상에서 제외할 수 있어 클래스 분리
FORMS = sorted(PALETTE.keys(), key=len, reverse=True)

def scan(text):
    """순서대로 (pos, canon, surface) 추출 — 최장일치 비중첩."""
    out = []
    pos = 0
    while pos < len(text):
        best = None
        for fm in FORMS:
            if text.startswith(fm, pos):
                best = fm
                break
        if best:
            out.append((pos, PALETTE[best], best))
            pos += len(best)
        else:
            pos += 1
    return out

def count_markers(text):
    return len(re.findall(r"\[ref:[^\]]+\]", text))

def check_adjacency(text, occ):
    viol = []
    for a, b in zip(occ, occ[1:]):
        if a[1] == b[1] and a[1] != "알려져_관형":
            between = text[a[0] + len(a[2]): b[0]]
            nsent = between.count("다.")
            if nsent <= 1:
                viol.append((a[2], b[2], nsent,
                             text[a[0]-15:b[0]+10].replace("\n", " ")))
    return viol

def check_para(text):
    over = []
    for pi, p in enumerate(text.split("\n\n")):
        from collections import Counter
        c = Counter()
        pp = 0
        while pp < len(p):
            b = None
            for fm in FORMS:
                if p.startswith(fm, pp):
                    b = fm
                    break
            if b:
                if PALETTE[b] != "알려져_관형":
                    c[PALETTE[b]] += 1
                pp += len(b)
            else:
                pp += 1
        for k, v in c.items():
            if v > 2:
                over.append((pi, k, v, p[:50].replace("\n", " ")))
    return over

def md_files():
    return sorted(glob.glob(os.path.join(WS, "drafts", "*.md")))

def report():
    total_occ = 0
    total_orig = 0
    from collections import Counter
    dist = Counter()
    all_adj = []
    all_para = []
    estim = 0
    print("=== 파일별 ===")
    for f in md_files():
        t = open(f, encoding="utf-8").read()
        occ = scan(t)
        # 전승류만 카운트(관형 '알려진' 제외)
        cocc = [o for o in occ if o[1] != "알려져_관형"]
        total_occ += len(cocc)
        for o in cocc:
            dist[o[1]] += 1
        orig = sum(1 for o in cocc if o[1] == "전해진다")
        total_orig += orig
        estim += len(re.findall(r"추정된다", t))
        adj = check_adjacency(t, occ)
        para = check_para(t)
        all_adj += [(os.path.basename(f),)+v for v in adj]
        all_para += [(os.path.basename(f),)+v for v in para]
        n_jh = len(re.findall(r"전해진다", t))
        print(f"  {os.path.basename(f):24} 전승형:{len(cocc):3}  전해진다:{n_jh:2}  추정된다:{len(re.findall(r'추정된다', t))}")
    print("\n=== 전체 팔레트 분포(드래프트) ===")
    for k, v in dist.most_common():
        print(f"  {k:12} {v:4}  ({v*100//max(total_occ,1)}%)")
    print(f"  TOTAL 전승형 출현: {total_occ}")
    print(f"  '전해진다' 원형 비율: {total_orig*100/max(total_occ,1):.1f}%  (목표 ≤25%)")
    print(f"  '추정된다' 신규(전체): {estim}")
    print(f"\n=== 위반 ===")
    print(f"  인접 문장 동일형: {len(all_adj)}")
    for v in all_adj:
        print("   ", v)
    print(f"  문단 내 동일형 >2: {len(all_para)}")
    for v in all_para:
        print("   ", v)
    print(f"\n=== 마커 총수 ===")
    tot = 0
    for f in md_files():
        tot += count_markers(open(f, encoding="utf-8").read())
    tl = count_markers(open(os.path.join(ROOT, "02_verified", "timeline.json"), encoding="utf-8").read())
    mf = count_markers(open(os.path.join(WS, "images", "manifest.json"), encoding="utf-8").read())
    print(f"  drafts:{tot}  timeline:{tl}  manifest:{mf}  TOTAL:{tot+tl+mf}")

if __name__ == "__main__":
    report()
