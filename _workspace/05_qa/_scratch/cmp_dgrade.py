#!/usr/bin/env python3
"""Pass 3: D-grade unauthorized exposure. Search render plane for distinctive D-claim content."""
import json, re

ex=json.load(open("/Users/robin/Downloads/DOSAN/_workspace/05_qa/_scratch/extracted.json"))
# Flatten render plane into (file, loc, text). EXCLUDE archives.json catalog? No — it renders. Keep all.
plane=[]
for grp in ("html","pages","data"):
    for rec in ex[grp]:
        plane.append((grp, rec[0], rec[1], rec[2]))

# D-grade probe terms: distinctive phrases / number+name combos per claim.
# Format: claim_id -> list of probe substrings (any hit => candidate exposure, manual review).
PROBES = {
 "clm-0004": ["안태열", "안교진"],
 "clm-0009": ["8세 때", "여덟 살 때 부친", "8세에 부친"],
 "clm-0011": ["심정리"],
 "clm-0015": ["1894년 상경", "1894년에 상경", "1894년 가을 상경"],
 "clm-0028": ["18조목", "쾌재", "부재(不哉)"],
 "clm-0041": ["가장 오래된 한국 여권", "현존하는 가장 오래된"],
 "clm-0046": ["하와이 섬을 보고", "하와이를 보고 호를", "도산이라 지었다", "도산으로 지었다"],
 "clm-0055": ["1904년", "파차파 캠프"],  # 1904 only-as-設立 — manual
 "clm-0057": ["오렌지 한 개", "오렌지를 따더라도", "정성껏 따"],
 "clm-0069": ["초대 중앙총회장"],
 "clm-0087": ["안수라", "Soorah", "2016년 사망"],
 "clm-0093": ["대한인신민회"],
 "clm-0100": ["1907년 4월"],
 "clm-0103": ["이토 히로부미의 제의", "이토와 회견", "이토 히로부미와 회견", "이토와의 회견", "협조 요청을 거절"],
 "clm-0106": ["1905년 5월", "태극서관"],  # manual: 1905 only
 "clm-0111": ["청년학우회의 총무는 최남선", "총무 최남선", "최남선이 총무"],
 "clm-0114": ["약 3개월"],
 "clm-0115": ["도산 내각", "내각 조직을 제의", "내각 조직(이른바"],
 "clm-0121": ["열차로 행주", "열차편으로", "기차로 행주"],
 "clm-0124": ["1910년 여름", "1910년 6월", "1910년 7월", "1910년 8월"],  # 청도회의 manual
 "clm-0131": ["머제스틱호", "9월 3일 뉴욕"],
 "clm-0133": ["평양역에서 체포", "12월 평양역"],
 "clm-0141": ["1919년 4월경", "4월경 미국을 출발"],
 "clm-0147": ["대통령 이승만", "이승만 명의"],
 "clm-0169": ["시대일보", "1924-05-19", "1924년 5월 19일"],
 "clm-0172": ["우리 혁명운동과 임시정부 문제"],
 "clm-0175": ["1월 27일", "1927년 1월 27일"],  # 길림사건 manual
 "clm-0179": ["기초위원은 7인", "7인이며 조소앙", "기초위원 7인"],
 "clm-0182": ["난징에서 이상촌", "이상촌 부지 토지", "토지를 매수"],
 "clm-0191": ["민족전도대업"],
 "clm-0192": ["1913년 흥사단 약법", "1913년 약법에서 정식화", "4대 정신.*1913"],
 "clm-0209": ["7월 15일", "1932년 7월 15일"],  # 서대문 입감 manual
 "clm-0215": ["1933년 2월 10일", "1933년 가출옥", "2월 10일.*가출옥"],
 "clm-0226": ["죽기도 죄스럽", "갈 곳이 감옥뿐", "병이 나아봐야"],
 "clm-0229": ["3월 12일", "1938년 3월 12일"],  # 안장 manual
 "clm-0237": ["자아혁신과 민족개조"],
 "clm-0239": ["낙망은 청년의 죽음", "청년이 죽으면 민족이 죽는다"],
 "clm-0241": ["밥을 먹어도 대한의 독립", "밥을 먹어도"],
 "clm-0242": ["서로 사랑하면 살고", "서로 싸우면 죽는다", "힘은 건전한 인격", "공고한 단결에서 난다"],
 "clm-0243": ["자유의 인민이니", "노예적이 되어서는"],
 "clm-0244": ["점진가", "점진 점진 점진"],
 "clm-0247": ["대공주의", "大公主義"],
 "clm-0259": ["서재필이 안창호에게 사상적 영향", "서재필의 영향을 받아"],
 "clm-0260": ["안중근의 연설을 듣고", "안중근과 면담", "안중근의 연설을 청강"],
 "clm-0261": ["박용만 측 중재", "박용만 측을 중재", "분규에서.*중재를 시도"],
 "clm-0273": ["대구복심법원", "1913년 7월 15일 판결"],
 "clm-0275": ["기소 인원은 122명", "122명을 기소", "122명이 기소"],
 "clm-0276": ["기소 인원은 49명", "49명을 기소", "49명이 기소"],
 "clm-0286": ["安致鎬"],
 "clm-0294": ["800달러", "800불"],
 "clm-0299": ["만류를 무시", "안창호의 만류를 무시"],
 "clm-0302": ["손정도.*흥사단", "손정도가.*원동임시위원부"],
}

hits=[]
for clm, probes in PROBES.items():
    for pr in probes:
        rx=re.compile(pr) if ".*" in pr else None
        for grp,f,loc,txt in plane:
            found = rx.search(txt) if rx else (pr in txt)
            if found:
                hits.append((clm, pr, f, loc, txt))

print(f"Total candidate D-grade hits (need manual review for qualifier/context): {len(hits)}")
print()
from collections import defaultdict
byclm=defaultdict(list)
for h in hits: byclm[h[0]].append(h)
for clm in sorted(byclm):
    print(f"### {clm} — {len(byclm[clm])} hits")
    for clm_,pr,f,loc,txt in byclm[clm]:
        print(f"   [probe={pr!r}] {f} > {loc}")
        print(f"      TEXT: {txt[:240]}")
json.dump(hits, open("/Users/robin/Downloads/DOSAN/_workspace/05_qa/_scratch/dgrade_hits.json","w"), ensure_ascii=False, indent=1)
