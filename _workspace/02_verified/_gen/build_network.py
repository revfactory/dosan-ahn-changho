#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_network.py — relation-analyst (14)
network_nodes_edges.json(Round 1) → network.json(확정본) 정규화 변환.

처리 내용:
1. evidence 전환 연결: evidence_pending → timeline.json 사건 id (merged_from 별칭 해소 포함)
2. 매칭 불능 엣지 → edges_unconfirmed(D등급) 강등 (삭제 금지). v1.1: 표적 보완 라운드(evt-chrono-102~108)로 5건 재승격, 잔존 13건
3. 보류 노드 2건(임치정·방화중) 승격 + 근거 엣지 9건 추가
4. 인명 정규화: per-001에 산옹·山翁·安昌鎬 추가, 장이욱 별칭, 동명이호 '우강' 구분 유지
5. cross-validator(conflicts.md) 채택 권고 반영: cfl-001/005/006/012/016/030/041/046
6. org-org 엣지 11건: type=comrade 유지(스킬 6분류 준수) + org_relation 보조 필드 부여
"""
import json, copy, sys, os

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
SRC = os.path.join(BASE, '..', '01_research', 'network_nodes_edges.json')
TIMELINE = os.path.join(BASE, 'timeline.json')
OUT = os.path.join(BASE, 'network.json')

with open(SRC) as f:
    net = json.load(f)
with open(TIMELINE) as f:
    tl = json.load(f)

# ---- 사건 id 별칭 맵 (timeline.json merged_from 기준) ----
alias = {}
tl_events = {}
for e in tl['events']:
    alias[e['id']] = e['id']
    tl_events[e['id']] = e
    for m in e.get('merged_from', []):
        alias[m] = e['id']

def ev(*ids):
    """별칭 해소 + 중복 제거(순서 유지)"""
    out = []
    for i in ids:
        r = alias[i]  # KeyError = 존재하지 않는 id → 빌드 실패가 맞다
        if r not in out:
            out.append(r)
    return out

# =====================================================================
# 1. 노드 편집
# =====================================================================
nodes = copy.deepcopy(net['nodes'])
nmap = {n['id']: n for n in nodes}

# per-001 안창호 — gaps.md §2-1 조건 ⑤
nmap['per-001']['alt_names'] += ['산옹', '山翁', '安昌鎬']
nmap['per-001']['summary'] += " 필명 '산옹(山翁)'으로 『동광』에 기고했고(evt-phil-010), 집조(여권)에는 '安昌鎬'로 표기되었다(src-pri-024)."

# per-003 안치호 — 한자 표기 상충 (network 安致鎬 / evt-early-001 detail 安致昊)
nmap['per-003']['alt_names'] += ['安致昊']
nmap['per-003']['summary'] += (" [표기 상충: 한자가 安致鎬(network 수집)와 安致昊(evt-early-001)로 갈림 — "
                               "fact-checker 판정 D(clm-0286) + cross-validator 판정 확정(cfl-066, conflicts.md v1.11): "
                               "미해소 — 양표기 병기. 본문 한자 병기 규칙은 '安致昊/安致鎬(기록마다 다름)'. "
                               "확정 사료(족보 원본·새문안교회 명부)는 전부 unlocated — 발굴 시 재판정. "
                               "이중 구조 유의(clm-0305 B): 형 안치호·여동생 안신호의 '존재' 자체는 기관 가계 서술로 B등급 — "
                               "한정 문형은 한자 '표기'에만 적용하면 된다.]")

# per-044 장리욱 — evt-hsd-021 표기 '장이욱'
nmap['per-044']['alt_names'] += ['장이욱']

# org-012 대한인국민회 — cfl-012 채택 권고 반영 (1912 총회장 오류 정정) + 국민회(1909) 포괄
nmap['org-012']['birth'] = '1909-02'
nmap['org-012']['summary'] = (
    "공립협회와 합성협회가 통합한 국민회(1909-02)가 대한인국민회(1910)로 개칭·발전한 조직(단순 개칭 — 한 노드 유지, 스킬 §3). "
    "도산은 1912년 중앙총회 결성에 참가했으나 총회장 선거에서는 윤병구가 당선되었고, 1914-11 당선·1915-06-23 취임으로 "
    "중앙총회장이 되어 해외 한인의 무형정부를 표방하는 체제를 정비했다(cfl-012 채택 권고 — '초대 중앙총회장 안창호' 표현 사용 금지)."
)

# org-018 동우구락부 — cfl-030 채택 권고 (1923-01-16 창립대회 기준)
nmap['org-018']['birth'] = '1923-01-16'
nmap['org-018']['summary'] = (
    "평양에서 대성학교 출신 상공인(김동원 등)을 중심으로 도산의 실력양성론을 지도이념으로 결성된 단체. "
    "결성 시점은 1923-01-16 창립대회 기준 잠정 채택(cfl-030), 1922-07은 준비 모임 단계로 병기. 1926년 수양동맹회와 통합했다."
)

# 승격 노드 2건 — gaps.md §2-1 조건 ④ (Round 1 보류 → 사건 레코드 확인으로 승격)
nodes.append({
    "id": "per-052", "name": "임치정", "hanja": "林蚩正",
    "alt_names": ["춘곡", "春谷"],
    "birth": "1880-09-26", "death": "1932-01-09",
    "role": "공립협회 창립 발기인·105인 사건 유죄 6인",
    "summary": ("평남 용강 출신. 1905년 샌프란시스코에서 안창호 등과 공립협회를 창립하고(evt-amer-010) 공립신보 간행에 참여했다. "
                "귀국 후 신민회에서 활동하다(evt-shin-005) 105인 사건 유죄 6인에 포함되어 옥고를 치렀다"
                "(cfl-041 잠정 채택 명단 — 판결문 전사 src-pri-016 도착 시 최종 확정). "
                "[승격 판정: Round 1 노드 보류 → 사건 레코드 7건 확인으로 승격. 생몰·한자는 위키백과·민백 105인 사건 항목 교차.]")
})
# 조소앙 — cross-validator cfl-051 회부 이행을 위한 정규화 중 발굴 추가
# (관계 엣지에 상충 주석을 남기려면 노드·엣지가 있어야 함. 근거: evt-provgov-015/026)
nodes.append({
    "id": "per-054", "name": "조소앙", "hanja": "趙素昂",
    "alt_names": ["소앙", "素昂", "趙素昻", "조용은", "趙鏞殷"],
    "birth": "1887", "death": "1958-09-10",
    "role": "삼균주의 이론가·한국독립당 창당 발기인·임시정부 외무부장",
    "summary": ("본명 조용은(趙鏞殷). 1922년 시사책진회와 1930년 한국독립당 창당에서 도산과 협력했다. "
                "사망일은 1958-09-10(민백 「조소앙」 원문 day 명시 + 위키 일치 — fact-checker 직접 확인, B 근거). "
                "출생은 연 단위(1887) 유지 — 04-10(민백, 음력 개연)/05-02(위키, 양력 환산 개연)의 환산 쌍일 가능성이 있으나 "
                "검증 전 단정 금지(timeline-analyst 음양력 환산 검증 대기). "
                "[추가 판정: cross-validator cfl-051 회부(한독당 당의·당강 기초위원 상충 주석 요청) 이행을 위해 "
                "근거 사건 2건(evt-provgov-015/026) 기반으로 정규화 중 추가.]")
})
nodes.append({
    "id": "per-053", "name": "방화중", "hanja": None,
    "alt_names": [],
    "birth": None, "death": None,
    "role": "공립협회 창립 발기인·국민회 멕시코 파견원",
    "summary": ("1905년 공립협회 창립 발기인(evt-amer-010). 1909년 국민회 북미지방총회가 황사용과 함께 멕시코에 특파하여 "
                "메리다지방회 창립을 도왔다(evt-amer-013 detail). 2014년 건국훈장 애족장 추서. 한자·생몰 미확인 — 보완 조사 대상. "
                "[승격 판정: Round 1 노드 보류 → 사건 레코드 3건 확인으로 승격.]")
})

# =====================================================================
# 2. 엣지 변환 테이블 — 인덱스는 원본 edges[] 순서
#    (evidence, from, to) + 선택: note(period_note), desc(교체), desc_add(추가), retype, org_relation
# =====================================================================
E = {}  # idx -> transform dict

E[0]  = dict(ev=ev('evt-early-001','evt-early-003','evt-early-004'), f='1878', t=None,
             note="부친 별세 시점은 1885–1890 범위 상충 미해소(cfl-001) — to 미기재 유지.")
E[1]  = dict(ev=ev('evt-early-001'), f='1878', t=None)
E[2]  = dict(ev=ev('evt-early-001'), f='1884', t='1938',
             note="근거는 출생 레코드의 가계 등재(1878) — from(안신호 출생 1884) 이전의 기록 사건 허용. 김구 혼담(1900년대 초) 레코드는 미생산 — 추가 조사 필요.")
E[3]  = dict(ev=ev('evt-early-022','evt-amer-002'), f='1902', t='1938')
E[4]  = dict(ev=ev('evt-early-013','evt-early-022'), f='1896', t=None,
             desc="장인-사위 관계. 1896년 약혼(cfl-005 잠정 채택, 1897설 병기)으로 맺어져 1902년 혼인으로 확정. 이석관 몰년 미상으로 period.to 비움.")
E[5]  = dict(ev=ev('evt-amer-030'), f='1905', t='1938')
E[6]  = dict(ev=ev('evt-amer-032'), f='1912', t='1938')
E[7]  = dict(ev=ev('evt-amer-033'), f='1915', t='1938')
E[8]  = dict(ev=ev('evt-amer-034'), f='1917', t='1938')
E[9]  = dict(ev=ev('evt-amer-035'), f='1926', t='1938')
E[10] = dict(ev=ev('evt-early-007','evt-early-008','evt-early-015'), f=None, t='1899')
E[11] = dict(ev=ev('evt-early-010','evt-early-011','evt-early-022'), f='1894', t='1902')
E[12] = dict(ev=ev('evt-hsd-021'), f=None, t='1938', retype='comrade',
             note="입단·사사 시기 미확인으로 from 비움.",
             desc=("동지 관계. 사제 관계로 전해지나(장리욱의 도산 사사 서술·전기 「도산의 인격과 생애」 저술) 확보된 근거 사건은 "
                   "동우회 사건 공동 수감·옥중 동거(evt-hsd-021, 장이욱 회고)로 동지 관계까지만 입증 — mentor 재분류는 입단문답·사사 기록 확보 후 재판정(스킬 §2: 근거 사건이 보여주는 것만 분류)."))
E[13] = dict(ev=ev('evt-hsd-025'), f=None, t='1936',
             note=("1919년 상하이 비서 합류설은 사건 레코드 미생산으로 from 비움(추가 조사 필요). "
                   "근거 사건(1938 망우리 안장·유언)은 유상규 사망(1936) 이후의 사후 기록 사건 — 관계를 소급 입증."))
E[14] = dict(ev=ev('evt-shin-005','evt-shin-012','evt-shin-013'), f='1907', t='1911')
E[15] = dict(ev=ev('evt-shin-005','evt-shin-010','evt-shin-011','evt-shin-013'), f='1907', t='1930',
             desc_add=" 1907-07 교육진흥론 연설 감화 사건 자체는 레코드 미생산 — 추가 조사 필요.")
E[16] = dict(ev=ev('evt-shin-005','evt-shin-017'), f='1907', t='1938')
E[17] = dict(ev=ev('evt-shin-005','evt-shin-021','evt-shin-022'), f='1907', t='1910',
             desc_add=" 청도회의 시기는 1910-05~09 범위(cfl-016 — 4월 단정 금지).")
E[19] = dict(ev=ev('evt-shin-005','evt-shin-009','evt-shin-017','evt-shin-021','evt-shin-022','evt-shin-023'), f='1907', t='1917')
E[21] = dict(ev=ev('evt-shin-005','evt-shin-010','evt-shin-013'), f='1907', t='1920',
             desc="동지 관계. 도산 국내 사업의 실무 책임자 — 신민회 평남 총감·태극서관 총무·청년학우회 임원(직제 표기는 총무/총무원 상충 — cfl-046 병기).")
E[22] = dict(ev=ev('evt-shin-005'), f='1907', t='1914')
E[23] = dict(ev=ev('evt-shin-005','evt-shin-009','evt-shin-017','evt-provgov-010'), f='1907', t='1921')
E[24] = dict(ev=ev('evt-provgov-010','evt-provgov-013'), f='1919', t='1921',
             desc=("갈등 관계(임정기). 임정 운영·이념(사회주의 노선, 위임통치 문제, 정부 개조론)을 둘러싼 내각 갈등 국면에서 노선을 달리했고, "
                   "이동휘의 국무총리 사임(1921-01-24, evt-provgov-013 detail)에 이어 도산도 사퇴했다. 협력과 병존한 복합 관계."))
E[25] = dict(ev=ev('evt-shin-005','evt-provgov-026'), f='1907', t='1938')
E[26] = dict(ev=ev('evt-shin-019','evt-shin-021','evt-shin-023'), f='1910', t='1911',
             desc_add=" 청도회의 시기는 1910-05~09 범위(cfl-016).")
E[27] = dict(ev=ev('evt-shin-021'), f='1910', t='1911')
E[28] = dict(ev=ev('evt-shin-005','evt-shin-017','evt-shin-021'), f='1907', t='1910')
E[29] = dict(ev=ev('evt-shin-021'), f='1910', t='1910',
             desc_add=" [인명 유의: 105인 유죄 6인 명단의 유동열 포함설은 기각 권고(cfl-041 — 옥관빈 포함 명단 채택).]")
E[30] = dict(ev=ev('evt-provgov-015','evt-provgov-026','evt-phil-012'), f='1919', t='1938',
             note="from(1919)은 경무국장 발탁 통설(백범일지) 기준 — 해당 사건 레코드 미생산으로 최조기 근거 사건은 1922(시사책진회). 추가 조사 필요.")
E[31] = dict(ev=ev('evt-shin-005'), f='1907', t='1911',
             note="청년학우회 평남 조직 결성(1909~10) 협력은 레코드에 최광옥 미거명 — 근거 사건은 신민회 창건(1907)뿐.")
E[32] = dict(ev=ev('evt-amer-010','evt-chrono-024','evt-shin-021','evt-shin-022','evt-shin-023'), f='1905', t='1938',
             note="1903년 한인친목회 단계의 교류설은 레코드 미정박 — from은 공립협회 창립(1905) 기준.")
E[33] = dict(ev=ev('evt-amer-010','evt-chrono-024','evt-amer-017'), f='1905', t=None,
             note="1903년 친목회 단계 교류설 미정박 — from은 공립협회 창립(1905) 기준. 임준기 후기 행적 미확인으로 to 비움.")
E[34] = dict(ev=ev('evt-amer-010','evt-amer-011'), f='1905', t='1907')
E[35] = dict(ev=ev('evt-amer-010','evt-shin-023'), f='1905', t='1930')
E[36] = dict(ev=ev('evt-amer-005'), f='1903', t='1928',
             desc="동지 관계. 1903년 상항친목회 공동 결성(evt-amer-005)이 최초 근거. 1910년대 국민회 행정·언론(북미지방총회장·신한민보 주필) 협력의 개별 사건은 추가 발굴 필요.")
E[37] = dict(ev=ev('evt-hsd-001','evt-hsd-002','evt-chrono-102','evt-amer-017'), f='1912', t='1938',
             note="1906년 도미 직후 교류 개시설은 레코드 미정박 — from은 약법 초안 제시(1912) 기준.")
E[40] = dict(ev=ev('evt-amer-023','evt-provgov-003','evt-provgov-010'), f='1918', t='1920',
             desc_add=" 1918-11 파리강화회의 대표 선출(도산 주재 전체회의에서 이승만 선출, evt-amer-023)로 from을 1918로 확장.")
E[41] = dict(ev=ev('evt-provgov-009','evt-provgov-013'), f='1919', t='1925',
             note="1923~25 국면(국민대표회의·탄핵)은 이승만 거명 레코드 미정박 — to(1925, 탄핵)는 통설 기준. cross-validator/fact-checker 검증 대상(디렉터 §1-2).")
E[42] = dict(ev=ev('evt-provgov-003','evt-provgov-013'), f='1919', t='1922',
             note="to(1922)는 김규식 구미위원장기 종료 통설 기준 — 근거 사건 범위는 1919~1921.")
E[44] = dict(ev=ev('evt-provgov-014','evt-hsd-025'), f='1921', t='1938',
             desc="동지 관계. 1921년 국민대표회 소집 운동 협력(evt-provgov-014)에서 1938년 장례 참석(evt-hsd-025)까지 이어졌다.",
             note="1919년 임정 초기 협력(외무차장)설은 레코드 미생산 — from은 1921 기준. 1932 이후 옥바라지 레코드도 미생산(추가 조사 필요).")
E[46] = dict(ev=ev('evt-shin-005','evt-shin-009'), f='1907', t='1925',
             note="임정·독립신문 국면(1919~)의 공동 사건은 레코드 미정박 — 근거 범위는 1907~08(신민회·서북학회).")
E[47] = dict(ev=ev('evt-shin-012','evt-shin-013','evt-hsd-004','evt-provgov-026'), f='1908', t='1938')
E[48] = dict(ev=ev('evt-provgov-008','evt-hsd-004','evt-chrono-106','evt-hsd-006','evt-hsd-009'), f='1919', t='1937',
             desc=("동지 관계. 독립신문 사장(1919, evt-provgov-008), 흥사단 원동위원부 입단(1920, evt-hsd-004), "
                   "도산의 사명을 받은 수양동맹회 결성(1922, evt-hsd-006 — '안창호로부터 흥사단 국내 조직 결성의 사명을 받고 귀국')으로 국내 수양운동의 대행자 역할을 했다."),
             note="첫 접점은 1907년 도쿄 태극학회 연설 청강(evt-shin-003) — 일방향 감화라 동지 관계 근거에서 제외(스킬 §4).")
E[50] = dict(ev=ev('evt-provgov-008','evt-hsd-009','evt-phil-010'), f='1919', t='1938',
             desc="동지 관계. 1919년 독립신문 창간 참여(evt-provgov-008)부터 동광 편집·'산옹' 기고 게재(evt-phil-010)까지 협력. 흥사단 입단 연도(1920년경)는 미정박 — 추가 조사 필요.")
E[51] = dict(ev=ev('evt-hsd-004'), f='1920', t='1932',
             note="1919년 4~5월 도산 상하이행 수행설(도산일기 src-pri-001 관련)은 사건 레코드 미생산 — from은 원동위원부 조직(1920) 기준.")
E[53] = dict(ev=ev('evt-hsd-001','evt-hsd-019'), f='1913', t='1938',
             desc=("동지 관계. 흥사단 창립위원(8도 대표 중 충청도 대표, evt-hsd-001 detail)으로 시작해 동우회 사건 공동 연루(evt-hsd-019)까지. "
                   "[fact-checker 판정 B(clm-0287): 상충 불성립 — 8도 대표 명단에 조병옥 명시(국편+민백), 창립위원 참여가 곧 가입 기점. "
                   "Round 1 '입단 연도 미발견'은 모순이 아니라 정보 부재. 1차 기록(창립 회의록) 미대조로 B 상한.]"))
E[55] = dict(ev=ev('evt-shin-013'), f='1909', t='1910',
             desc="동지 관계(청년학우회기 국한). 직책은 총무(민백)/총무원(위키) 표기 상충 — cfl-046 병기. 이후 최남선의 행로와는 무관하게 시기를 좁게 잡았다.")
E[56] = dict(ev=ev('evt-provgov-026','evt-provgov-029'), f='1930', t='1932',
             note="1920년대 원동위원부·교민단 협력설은 레코드에 이유필 미거명 — from은 한국독립당 공동 창당(1930) 기준. 추가 조사 필요.")
E[57] = dict(ev=ev('evt-early-014','evt-early-015','evt-early-016','evt-early-017','evt-early-018'), f='1897', t='1898',
             desc_add=" 가입 연도는 1897 채택(cfl-006), 쾌재정 연설은 1898 채택(cfl-007).")
E[58] = dict(ev=ev('evt-early-010','evt-early-011','evt-early-012'), f='1894', t='1897',
             note="입학 연도는 1894~95 범위(cfl-003), 졸업은 1896~97 범위(cfl-004) — 단년 단정 금지 권고에 따라 기간은 최대 범위로 둠.")
E[59] = dict(ev=ev('evt-early-019','evt-early-021'), f='1899', t='1902')
E[60] = dict(ev=ev('evt-amer-005'), f='1903', t='1905')
E[61] = dict(ev=ev('evt-amer-010','evt-amer-011','evt-shin-006'), f='1905', t='1909')
E[62] = dict(ev=ev('evt-shin-001','evt-shin-005','evt-shin-017','evt-shin-019'), f='1907', t='1911',
             note="evt-shin-001(1906-11 미주 구상·취지서 작성)은 결성 준비 사건 — from(1907 창건) 이전 허용(cfl-044: 구상·초안설 채택).")
E[63] = dict(ev=ev('evt-shin-012'), f='1908', t='1910')
E[64] = dict(ev=ev('evt-shin-010'), f='1908', t='1911')
E[65] = dict(ev=ev('evt-shin-011'), f='1908', t='1911')
E[66] = dict(ev=ev('evt-shin-013'), f='1909', t='1910')
E[67] = dict(ev=ev('evt-shin-009'), f='1908', t='1910')
E[68] = dict(ev=ev('evt-amer-016','evt-amer-018','evt-tla-001','evt-amer-020','evt-amer-021','evt-amer-024'), f='1911', t='1919',
             desc=("회원·간부(1911 재정착 후 활동 재개) → 제1차 대표원의회 참가(1912-11-08, 총회장 선거에서는 윤병구 당선, evt-amer-018) → "
                   "중앙총회 정식 출범 선포식 참가(1912-11-20, evt-tla-001) → "
                   "중앙총회장 당선(1914-11)·취임(1915-06-23) → 1919 상하이행으로 직책 종료. "
                   "cfl-012 채택 권고 반영 — '1912년 초대 중앙총회장' 서술 금지. cfl-013 분리(11-08 대표원의회/11-20 선포식) 반영."))
E[69] = dict(ev=ev('evt-hsd-001','evt-hsd-002','evt-hsd-003'), f='1913', t='1938')
E[70] = dict(ev=ev('evt-provgov-003','evt-provgov-004','evt-provgov-011','evt-provgov-013'), f='1919', t='1921')
E[71] = dict(ev=ev('evt-provgov-008'), f='1919', t='1921')
E[72] = dict(ev=ev('evt-amer-017'), f='1912', t=None)
E[73] = dict(ev=ev('evt-hsd-009','evt-hsd-010','evt-hsd-020'), f='1926', t='1937',
             desc=("국내 운동 조직의 지도자 — 동광 창간 참여(1926, evt-hsd-009), 동우회 개칭 국면 지도(1929, evt-hsd-010), "
                   "동우회 사건 핵심 관련자 검거·기소(1937, evt-hsd-020)가 근거. to는 동우회 강제 해산(1937, evt-hsd-026) 기준."))
E[74] = dict(ev=ev('evt-provgov-020'), f='1924', t='1926')
E[75] = dict(ev=ev('evt-provgov-026'), f='1930', t='1932',
             desc_add=" 당의·당강 기초위원 명단(6인/7인·조소앙 포함 여부)은 미해소 양론 병기(cfl-051).")
# --- org-org 11건: type=comrade 유지(스킬 6분류 — 신설 금지), org_relation 보조 필드 ---
E[76] = dict(ev=ev('evt-amer-005','evt-amer-010'), f='1905', t='1905', org='predecessor',
             note="evt-amer-005(1903)는 전신 조직(친목회) 결성 사건 — 전환 시점(1905) 이전 허용.")
E[77] = dict(ev=ev('evt-amer-013','evt-amer-015'), f='1909', t='1910', org='predecessor',
             note=("전환 과정 엣지 — to(1910)는 공립협회 존속이 아니라 승계 '완료' 시점(대한인국민회 개칭 1910-05, evt-amer-015) 기준. "
                   "공립협회 해산(1909-02)으로 국민회 북미지방총회로 개편된 뒤 1910-05 개칭으로 전신-후신 전환이 종결된다 — "
                   "to를 1909-02로 줄이면 근거 사건 evt-amer-015(1910-05)가 period 밖이 되어 정합 위반. "
                   "[team-lead 동결 전 점검(WARN [9+]) 회신: 유지 근거 문서화]"))
E[78] = dict(ev=ev('evt-hsd-001'), f='1913', t=None, org='predecessor')
E[79] = dict(ev=ev('evt-hsd-008'), f='1926', t='1926', org='predecessor')
E[80] = dict(ev=ev('evt-hsd-008'), f='1926', t='1926', org='predecessor')
E[81] = dict(ev=ev('evt-hsd-008','evt-hsd-010','evt-hsd-019'), f='1926', t='1937', org='affiliate')
E[82] = dict(ev=ev('evt-shin-012'), f='1908', t='1911', org='subsidiary')
E[83] = dict(ev=ev('evt-shin-013'), f='1909', t='1910', org='subsidiary')
E[84] = dict(ev=ev('evt-shin-010'), f='1908', t='1911', org='subsidiary')
E[85] = dict(ev=ev('evt-shin-011'), f='1908', t='1911', org='subsidiary')
E[86] = dict(ev=ev('evt-provgov-008'), f='1919', t='1926', org='organ')
# --- 인물-조직 membership ---
E[87] = dict(ev=ev('evt-shin-012'), f='1908', t='1911')
E[88] = dict(ev=ev('evt-shin-013'), f='1909', t='1910')
E[89] = dict(ev=ev('evt-shin-005','evt-shin-010','evt-shin-029'), f='1907', t='1911')
E[90] = dict(ev=ev('evt-shin-005','evt-shin-017','evt-shin-024','evt-shin-029'), f='1907', t='1911')
E[91] = dict(ev=ev('evt-shin-005','evt-shin-021','evt-shin-022'), f='1907', t='1910')
E[92] = dict(ev=ev('evt-shin-005','evt-shin-017'), f='1907', t='1910')
E[93] = dict(ev=ev('evt-shin-005','evt-shin-010','evt-shin-029'), f='1907', t='1911')
E[94] = dict(ev=ev('evt-shin-005'), f='1907', t='1911')
E[95] = dict(ev=ev('evt-shin-005','evt-shin-017'), f='1907', t='1910')
E[96] = dict(ev=ev('evt-shin-005'), f='1907', t='1910')
E[97] = dict(ev=ev('evt-shin-005','evt-shin-017'), f='1907', t='1910')
E[98] = dict(ev=ev('evt-shin-005','evt-shin-024'), f='1907', t='1911')
E[99] = dict(ev=ev('evt-provgov-026','evt-provgov-029'), f='1919', t='1945',
             note="from(1919, 경무국장 임명)은 통설 기준 — 사건 레코드 미생산. 근거 사건 범위는 1930~32. 추가 조사 필요.")
E[100] = dict(ev=ev('evt-provgov-010','evt-provgov-013'), f='1919', t='1921')
E[101] = dict(ev=ev('evt-provgov-003','evt-provgov-009','evt-provgov-010'), f='1919', t='1925',
              note="to(1925, 탄핵 면직)는 통설 기준 — 탄핵 사건 레코드 미생산. 추가 조사 필요.")
E[103] = dict(ev=ev('evt-provgov-003','evt-provgov-013'), f='1919', t='1922',
              note="to(1922)는 통설 기준 — 근거 사건 범위는 1919~1921.")
E[106] = dict(ev=ev('evt-shin-012'), f='1908', t='1912')
E[107] = dict(ev=ev('evt-provgov-026'), f='1919', t='1945',
              note="from(1919, 상하이 합류·독립신문 참여)은 통설 기준 — 해당 레코드에 차리석 미거명. 근거 사건은 1930(한국독립당 창당). 추가 조사 필요.")
E[108] = dict(ev=ev('evt-amer-010'), f='1905', t='1909')
E[109] = dict(ev=ev('evt-amer-010'), f='1905', t='1909',
              desc="창립 회원. to(1909)는 공립협회의 국민회 통합(조직 종료) 기준.")
E[110] = dict(ev=ev('evt-amer-010','evt-amer-011'), f='1905', t='1907')
E[111] = dict(ev=ev('evt-amer-010'), f='1905', t='1909')
E[112] = dict(ev=ev('evt-amer-019'), f='1913', t='1928',
              note="1910년대 초 북미지방총회장·신한민보 주필 취임 시점은 레코드 미정박 — from은 헤멧 밸리 사건 대응(1913) 기준.")
E[114] = dict(ev=ev('evt-hsd-001','evt-hsd-002'), f='1913', t='1956')
E[115] = dict(ev=ev('evt-hsd-004','evt-chrono-106'), f='1920', t='1937')
E[116] = dict(ev=ev('evt-hsd-006'), f='1922', t='1926')
E[117] = dict(ev=ev('evt-hsd-008','evt-hsd-010','evt-hsd-019'), f='1926', t='1937')
E[118] = dict(ev=ev('evt-hsd-009','evt-hsd-010'), f='1926', t='1979',
              note="입단 연도(1920년경)는 레코드 미정박(Round 1 보완 표기) — from은 동광 창간 참여(1926, evt-hsd-009) 기준. 원동위원부 조직 레코드(evt-hsd-004)에 주요한 미거명.")
E[119] = dict(ev=ev('evt-hsd-009','evt-hsd-010','evt-hsd-019'), f='1926', t='1937')
E[123] = dict(ev=ev('evt-hsd-008','evt-hsd-019'), f='1926', t='1937')
E[124] = dict(ev=ev('evt-hsd-007'), f='1923', t='1926',
              note="결성 시점은 1923-01-16 창립대회 기준 잠정 채택(cfl-030) — 1922-07 준비 모임 단계부터 주도 병기.")
E[125] = dict(ev=ev('evt-shin-013'), f='1909', t='1910',
              desc="청년학우회 임원(총무/총무원 직제 표기 상충 — cfl-046 병기)·기관지 『소년』 발행.")
E[128] = dict(ev=ev('evt-early-014'), f='1896', t='1898',
              note=("독립협회 창립(1896) 사건 레코드는 본 조사 범위(도산 중심) 밖 — 근거는 도산 가입 레코드(evt-early-014)의 "
                    "'서재필 등이 이끄는 독립협회' 서술(간접). from(1896)은 통설 기준. "
                    "fact-checker 판정 B(clm-0288) — 간접 근거 채택 적합. 단 서재필→안창호 개인 영향은 별개의 D(clm-0259, 미확정 보관)."))

# --- 재승격 5건 (v1.1 — 표적 보완 라운드 evt-chrono-102~108 정박) ---
E[18] = dict(ev=ev('evt-chrono-105','evt-provgov-016','evt-provgov-018'), f='1923', t='1923',
             desc=("갈등 관계(국민대표회의). 임시정부 개조를 주장한 안창호 중심 개조파와 새 지도기관 창조를 주장한 신채호 등 "
                   "창조파가 정면 대립했다(evt-chrono-105 — 표적 보완 라운드 발굴로 D 보관에서 재승격). 동지→갈등의 시기 분리 엣지."),
             note=("Round 1의 from(1919, 위임통치 비난 국면)은 신채호 거명 레코드가 여전히 부재해 1923(국민대표회의)으로 축소 — "
                   "1919 국면 레코드 발굴 시 재확장. [v1.1 재승격]"))
E[20] = dict(ev=ev('evt-chrono-104'), f='1911', t='1917',
             desc=("후원 관계(도산→이갑). 병상의 이갑을 신한민보 주필로 초청해 도미를 주선했으나 미국 상륙 불허로 무산되었다"
                   "(evt-chrono-104 — 표적 보완 라운드 발굴로 재승격). 치료비 송금의 구체 액수·경로는 여전히 미확인 — 추가 조사 대상."),
             note="to(1917)는 이갑 사망 기준(공지의 종결 사실 규약). [v1.1 재승격]")
E[38] = dict(ev=ev('evt-chrono-103'), f='1919', t='1938',
             desc=("후원 관계(송종익→도산·도산 계열 운동). 도산의 1919년 상하이행 이후 송종익이 미주 흥사단 운영 실무와 "
                   "국민회 재무를 맡아 임시정부 자금 모집·송금을 담당했다(evt-chrono-103 — 표적 보완 라운드 발굴로 재승격)."),
             note="to(1938)는 도산 사망 기준. [v1.1 재승격]")
E[43] = dict(ev=ev('evt-chrono-105'), f='1923', t='1923',
             desc=("갈등 관계(1923 국한). 국민대표회의에서 창조파(김규식 합류) 대 개조파(안창호)로 대립했다"
                   "(evt-chrono-105 — 표적 보완 라운드 발굴로 재승격). 회의 결렬 후에도 인간 관계가 단절됐다는 근거는 없어 시기를 좁게 잡았다."))
E[49] = dict(ev=ev('evt-chrono-108'), f='1922', t='1938',
             desc=("갈등(사상적 긴장) 관계. 이광수의 「민족개조론」 발표(1922-05, 개벽 — evt-chrono-108, 표적 보완 라운드 발굴로 재승격)가 "
                   "흥사단 노선을 반영했다는 평가 속에 안창호 사상과의 동일시 논쟁을 일으켰다. 개인적 결별이 아니라 사상 해석의 긴장이며, "
                   "동우회 사건 후 이광수의 전향으로 노선이 최종 분기했다. 동지 엣지와 병존하는 복합 관계."),
             note="to(1938)는 도산 사망 기준 — 1922 이후 긴장 지속의 개별 사건은 미정박. [v1.1 재승격]")

# --- 강등 잔존: idx -> 사유 (+참고 사건 related) ---
DEMOTE = {
    39:  ("박용만이 등장하는 사건 레코드 0건 — 신한민보 주필·국민회 협력 레코드 발굴 필요. "
          "[v1.1: 표적 보완 라운드(2026-06-06)에서도 미발굴 — 신한민보 원지면 등 미주 신문 사료 발굴 필요.]", []),
    45:  ("손정도가 등장하는 사건 레코드 0건 — 임시의정원 의장 재임·흥사단 원동위원부 참여 레코드 발굴 필요. "
          "[v1.1: 표적 보완 라운드에서 evt-chrono-110(원동위원부 참여) 발굴되었으나 confidence D·〔미확인〕 — "
          "heungsadan 검증 인계 중, 검증 통과 시 재승격 후보.]", ['evt-chrono-110']),
    52:  ("조만식이 등장하는 사건 레코드 0건 — 1907 연설 감화·1932 이후 옥바라지(조만식·여운형·이광수) 레코드 미생산. "
          "조만식은 시드 인물이므로 1순위 발굴 대상. [v1.1: 표적 보완 라운드에서도 미발굴.]", []),
    54:  ("도산-김동원의 직접 상호작용 레코드 부재 — 대성학교 교사진 레코드(evt-shin-012)에 김동원 미거명, "
          "동우구락부·수양동우회 사건들은 도산과의 상호작용을 보여주지 않음(공동 등장 불충분 — 스킬 §4).",
          ['evt-hsd-007', 'evt-hsd-008']),
    102: ("임정 사건 레코드에 박은식 미등장 — 제2대 임시대통령 취임(1925-03) 레코드 미생산.", []),
    104: ("여운형의 임정 직책(외무부 차장) 사건 레코드 부재. evt-provgov-014는 국민대표회 소집 운동 사건으로 직책 근거가 아님.",
          ['evt-provgov-014']),
    105: ("손정도 임시의정원 의장 재임 레코드 0건. [v1.1: 표적 보완 라운드 evt-chrono-110은 원동위원부 참여 건이며 D·미확인 — 의장 재임 근거 아님.]", []),
    113: ("박용만의 신한민보 주필(1911)·하와이지방총회 활동 레코드 0건. [v1.1: 표적 보완 라운드에서도 미발굴.]", []),
    120: ("장리욱의 흥사단 입단 레코드 부재, 동우회 사건 검거자 레코드(evt-hsd-019)에도 미거명. "
          "공동 수감 레코드(evt-hsd-021)는 도산과의 관계(동지 엣지)만 입증.", ['evt-hsd-021']),
    121: ("유상규의 흥사단 원동지부 입단(1919~20) 레코드 부재 — 원동위원부 조직 레코드(evt-hsd-004)에 미거명.",
          ['evt-hsd-004']),
    122: ("정인과의 임정 외무총장대리 차장 임명(1919-09) 레코드 부재(provisional-gov 영역 미생산).", []),
    126: ("청년학우회 레코드(evt-shin-013)에 최광옥 미거명 — 평남 조직 결성 레코드 미생산.", ['evt-shin-013']),
    127: ("흥사단 원동위원부 레코드(evt-hsd-004)에 이유필 미거명 — 입단 레코드 발굴 필요.", ['evt-hsd-004']),
}

src_edges = net['edges']
assert len(src_edges) == 129
covered = set(E.keys()) | set(DEMOTE.keys())
missing = [i for i in range(129) if i not in covered]
assert not missing, f"변환 테이블 누락 인덱스: {missing}"
assert not (set(E.keys()) & set(DEMOTE.keys()))

edges = []
unconfirmed = []

for i, src in enumerate(src_edges):
    e = copy.deepcopy(src)
    if i in DEMOTE:
        reason, related = DEMOTE[i]
        e['grade'] = 'D'
        e['unconfirmed_reason'] = reason
        if related:
            e['related_event_ids'] = related
        e['demoted_from'] = 'edges (Round 1)'
        unconfirmed.append(e)
        continue
    tr = E[i]
    e['evidence_event_ids'] = tr['ev']
    e['period'] = {'from': tr['f'], 'to': tr['t']}
    if tr.get('retype'):
        e['type'] = tr['retype']
    if tr.get('desc'):
        e['description'] = tr['desc']
    if tr.get('desc_add'):
        e['description'] += tr['desc_add']
    if tr.get('note'):
        e['period_note'] = tr['note']
    if tr.get('org'):
        e['org_relation'] = tr['org']
    e.pop('evidence_pending', None)  # 감사 추적은 01_research 원본에 보존
    edges.append(e)

# --- 기존 미확정 3건 — gaps.md §2-1 조건 ④ 판정 결과 주석 갱신 ---
for u in net['edges_unconfirmed']:
    u = copy.deepcopy(u)
    u['grade'] = 'D'
    tgt = (u['source'], u['target'])
    if tgt == ('per-014', 'per-001'):  # 서재필→안창호
        u['unconfirmed_reason'] += " [Phase 2 판정: 보류 유지 — 263건 사건 레코드에 직접 교류 사건 없음 확인. 사상적 영향(일방향)만으로 유형 부여 불가.]"
    elif tgt == ('per-001', 'per-028'):  # 안창호-안중근
        u['related_event_ids'] = ['evt-shin-014']
        u['unconfirmed_reason'] += (" [Phase 2 판정: 보류 유지 — evt-shin-014(1909 연루 체포)는 일제의 의심이지 상호작용이 아님. "
                                    "1909 구금 기간·횟수 상충은 cfl-035. primary-source 증분(안중근 공판·105인 기록 역추적) 결과 대기.]")
    elif tgt == ('per-001', 'per-035'):  # 안창호-박용만
        u['unconfirmed_reason'] += " [Phase 2 판정: 보류 유지 — 1915 하와이 분규 중재 레코드 미생산 확인(america 영역).]"
    unconfirmed.append(u)

# --- 승격 노드·정규화 중 확인된 근거 기반 추가 엣지 9건 ---
ADD = [
    dict(source='per-001', target='per-052', type='comrade',
         period={'from': '1905', 'to': '1911'},
         evidence_event_ids=ev('evt-amer-010','evt-shin-005'),
         description="동지 관계. 공립협회 공동 창립(1905)과 신민회 창건(1907)을 함께했다. 도산 망명(1910~11)과 임치정 투옥(105인 사건) 이후의 직접 교류는 미확인."),
    dict(source='per-052', target='org-005', type='membership',
         period={'from': '1905', 'to': '1909'},
         evidence_event_ids=ev('evt-amer-010'),
         description="창립 발기인. 공립신보 간행 참여."),
    dict(source='per-052', target='org-006', type='membership',
         period={'from': '1907', 'to': '1911'},
         evidence_event_ids=ev('evt-shin-005','evt-shin-029','evt-shin-030','evt-shin-031','evt-shin-032'),
         period_note="105인 사건 재판 레코드(1912~15)는 회원 활동(to=1911 와해)을 소급 입증하는 사후 기록 사건.",
         description="회원. 105인 사건 유죄 6인에 포함(cfl-041 잠정 채택 명단 — 판결문 전사 도착 시 최종 확정)되어 옥고."),
    dict(source='per-001', target='per-053', type='comrade',
         period={'from': '1905', 'to': None},
         evidence_event_ids=ev('evt-amer-010'),
         description="동지 관계. 공립협회 공동 창립(1905)이 근거. 이후 개별 교류 사건 미수집 — 추가 조사 필요."),
    dict(source='per-053', target='org-005', type='membership',
         period={'from': '1905', 'to': '1909'},
         evidence_event_ids=ev('evt-amer-010','evt-amer-013'),
         description="창립 발기인."),
    dict(source='per-053', target='org-012', type='membership',
         period={'from': '1909', 'to': None},
         evidence_event_ids=ev('evt-amer-013'),
         description="국민회 북미지방총회 파견원 — 1909-04 황사용과 멕시코 특파, 메리다지방회 창립 지원(evt-amer-013 detail). 이후 활동 종료 시점 미확인."),
    dict(source='per-046', target='org-013', type='membership',
         period={'from': '1920', 'to': None},
         evidence_event_ids=ev('evt-hsd-004'),
         description="흥사단 원동임시위원부 조직 참여 단우(evt-hsd-004). 1930년대 친일 전향 이후 관계 종료 시점 미확인 — to 비움. [정규화 중 발굴 추가 — 강등된 임정 membership(레코드 부재)을 대체하는 근거 기반 엣지.]"),
    dict(source='per-049', target='org-019', type='membership',
         period={'from': '1926', 'to': '1937'},
         evidence_event_ids=ev('evt-hsd-008','evt-hsd-019'),
         description="수양동우회 통합 주역(1926)·동우회 사건 피검(1937). [정규화 중 발굴 추가.]"),
    dict(source='per-048', target='org-013', type='membership',
         period={'from': '1913', 'to': None},
         evidence_event_ids=ev('evt-hsd-001'),
         description="흥사단 창립위원(8도 대표 중 충청도 대표, evt-hsd-001 detail). fact-checker 판정 B(clm-0287) — 상충 불성립, 창립위원 참여가 가입 기점. [정규화 중 발굴 추가.]"),
    dict(source='per-001', target='per-054', type='comrade',
         period={'from': '1922', 'to': '1932'},
         evidence_event_ids=ev('evt-provgov-015','evt-provgov-026'),
         description=("동지 관계. 시사책진회 공동 조직(1922, evt-provgov-015)과 한국독립당 공동 창당(1930, evt-provgov-026). "
                      "to(1932)는 도산 피체 기준. [근거 주석(cfl-051, 미해소): 한독당 당의·당강 기초위원 명단은 "
                      "6인(조소앙 불포함, 민백 「한국독립당」) / 7인(조소앙 포함) / '조소앙 기초'(민백 「조소앙」) 3설 상충 — "
                      "민백 내부 항목 간 상충으로 양론 병기, 차리석 1942 문서 도착 시 재판정. 대공주의/삼균주의 논쟁(cfl-057)과 직결.]")),
    dict(source='per-054', target='org-021', type='membership',
         period={'from': '1930', 'to': None},
         evidence_event_ids=ev('evt-provgov-026'),
         period_note="이후 한독당 내 활동·이탈(1948)은 본 조사 범위(도산 생애) 밖 — to 비움.",
         description="창당 발기인. 당의·당강 기초 관여 범위는 미해소 상충(cfl-051) — 단정 서술 금지."),
]
edges += ADD

# =====================================================================
# 2b. 최종 증분 병합 — network_nodes_supplement.json (v1.2, 동결 전 마지막 증분)
#     주의: supplement의 per-052~056은 본 빌드가 이미 임치정(per-052)·방화중(per-053)·조소앙(per-054)에
#     선점 발급했으므로 신규 id로 재발급해 병합한다 (team-lead 지시).
# =====================================================================
SUPP = os.path.join(BASE, '..', '01_research', 'network_nodes_supplement.json')
with open(SUPP) as f:
    supp = json.load(f)

REMAP = {  # supplement id -> 확정 id
    'per-052': 'per-055',  # 김동삼
    'per-053': 'per-056',  # 윤해
    'per-054': 'per-057',  # 박현환
    'per-055': 'per-058',  # 오영선
    'per-056': 'per-059',  # 김희선
    'org-022': 'org-022',  # 충돌 없음
}

for n in supp['nodes']:
    n = copy.deepcopy(n)
    old_id = n['id']
    n['id'] = REMAP[old_id]
    if n['id'] != old_id:
        n['summary'] += f" [id 재발급: supplement {old_id} → {n['id']} — 본체 선점 id(임치정·방화중·조소앙) 충돌 회피.]"
    nodes.append(n)
    nmap[n['id']] = n

def remap_st(e):
    e['source'] = REMAP.get(e['source'], e['source'])
    e['target'] = REMAP.get(e['target'], e['target'])
    return e

for se in supp['edges']:
    e = remap_st(copy.deepcopy(se))
    e['evidence_event_ids'] = ev(*e['evidence_event_ids'])  # 별칭(chrono-035/068, phil-011) 해소 + 중복 제거
    # 판정 ①: 박현환→수양동우회 membership — evt-hsd-019 actors에 박현환 미거명 → 본체 기준(레코드 거명 의무) 일관 적용, D 강등
    if e['source'] == 'per-057' and e['target'] == 'org-019':
        e['grade'] = 'D'
        e['unconfirmed_reason'] = ("evt-hsd-019 actors에 박현환 미등재 — 복심 판결 서술(민백 「수양동우회」)은 사건 레코드 미정박. "
                                   "검거자 명단 보강(heungsadan 인계) 시 승격. "
                                   "[relation-analyst 판정: 최광옥·이유필 강등과 동일 규칙(레코드 거명 의무) 일관 적용 — 공급자 자인 사항.]")
        e['demoted_from'] = 'supplement edges (v1.2)'
        unconfirmed.append(e)
        continue
    # 판정 ②: org-022→org-014 patron — org-org patron 승인 (6분류 내 유형, 재정 후원 목적 조직의 피후원 기관 관계)
    if e['source'] == 'org-022' and e['target'] == 'org-014':
        e['description'] += (" [relation-analyst 판정: org-org patron 승인 — patron은 스킬 6분류 내 유형이며 재정 지원 관계 정의에 부합. "
                             "근거 사건은 조직 결성·계기(evt-chrono-109, evt-provgov-022)로 후원 '목적'을 정박하며, "
                             "실제 전달 규모·시기의 1차 근거는 미확인(원 서술 유지) — fact-checker 등급화 대상.]")
    # 판정 ③: 김희선 comrade — 1910 한정·1922 귀순 주석 원문 유지 (검증: period 1910~1910, 귀순 서술 포함 확인)
    if e['target'] == 'per-059':
        assert e['period'] == {'from': '1910', 'to': '1910'} and '귀순' in e['description']
    edges.append(e)

for su in supp.get('edges_unconfirmed', []):
    u = remap_st(copy.deepcopy(su))
    if u.get('evidence_event_ids'):
        u['related_event_ids'] = ev(*u['evidence_event_ids'])
        u['evidence_event_ids'] = []
    u['grade'] = 'D'
    u['unconfirmed_reason'] += " [Phase 2 판정: 보류 유지 — 직접 상호작용·입단 근거 부재 확인, 연구원 분리 판단에 동의.]"
    unconfirmed.append(u)

# =====================================================================
# 3. 인명 정규화 테이블 (변형 표기 → 노드 id)
# =====================================================================
def strip_paren(s):
    return s.split('(')[0].strip()

norm = {}
ambiguous = {}
for n in nodes:
    keys = {n['name']}
    if n.get('hanja'):
        keys.add(n['hanja'])
    for a in n.get('alt_names', []):
        keys.add(a)
        keys.add(strip_paren(a))
    for k in keys:
        if not k:
            continue
        if k in norm and norm[k] != n['id']:
            ambiguous.setdefault(k, sorted({norm[k], n['id']})).append(n['id'])
            ambiguous[k] = sorted(set(ambiguous[k]))
        else:
            norm[k] = n['id']
for k in ambiguous:
    norm.pop(k, None)

# =====================================================================
# 4. 고립 노드 산출(문서화) 및 메타
# =====================================================================
ref = set()
for e in edges:
    ref.add(e['source']); ref.add(e['target'])
isolated = sorted(n['id'] for n in nodes if n['id'] not in ref)

ISOLATED_DOC = {
    'per-028': "안중근 — 관계 유형 미확정 보류(edges_unconfirmed). primary-source 증분(공판 기록 역추적) 대기.",
    'per-035': "박용만 — 등장 사건 레코드 0건으로 엣지 3건 전부 미확정 보관. 표적 보완 라운드(v1.1)에서도 미발굴 — 신한민보 원지면 등 미주 신문 사료 필요.",
    'per-039': "손정도 — 본체 근거 레코드 0건. 표적 보완 라운드(v1.1)에서 evt-chrono-110(원동위원부 참여) 발굴되었으나 D·미확인(heungsadan 검증 인계 중) — 검증 통과 시 재승격 후보.",
    'per-047': "조만식 — 시드 인물. 1907 감화·1932 옥바라지 레코드 미생산으로 엣지 미확정 보관. 표적 보완 라운드(v1.1)에서도 미발굴 — 1순위 발굴 대상 유지.",
}
assert set(isolated) == set(ISOLATED_DOC), f"고립 노드 불일치: {isolated} vs {sorted(ISOLATED_DOC)}"

meta = {
    "producer": "relation-analyst (14)",
    "version": "v1.2.1-phase2",
    "status": "final-frozen — v1.2.1 마이크로 증분(team-lead 승인) 후 최종 동결. 이후 변경은 Phase 4 이후 일괄 대기 목록으로만 보관. Phase 4 데이터 변환의 입력.",
    "date": "2026-06-06",
    "schema": "network-mapping (S06)",
    "inputs": ["01_research/network_nodes_edges.json (v1.0-round1)", "02_verified/timeline.json (161 events)",
               "02_verified/conflicts.md (cfl-001~062)", "00_director/gaps.md §2-1"],
    "event_id_basis": ("timeline.json 확정 id 체계(161건, merged_from 별칭 263건 전부 해소). "
                       "Phase 1 events.json id는 timeline 병합 생존 id로 변환 후 참조."),
    "counts": {"nodes": len(nodes), "edges": len(edges), "edges_unconfirmed": len(unconfirmed)},
    "conventions": {
        "period.to": "사망·조직 해산 등 공지의 종결 사실은 사건 레코드 없이 연도 기재 허용(노드 birth/death와 정합 검사).",
        "period_note": "근거 사건이 period 범위 밖이거나 from/to가 통설 기준 추정일 때 의무 기재 — 검증 스크립트의 면제 조건.",
        "org_relation": ("조직-조직 엣지의 보조 필드(predecessor/subsidiary/affiliate/organ). "
                         "type은 스킬 6분류 준수를 위해 comrade 유지(신설 금지 — 정책 4), description 첫머리 [전신/후신]/[산하] 규약 유지."),
        "org_org_patron": ("조직→조직 patron 허용(v1.2 판정) — 재정 후원 목적 조직과 피후원 기관의 관계. "
                           "patron은 6분류 내 유형이며 org_relation 보조 필드는 불요(type 자체가 관계 성격을 기술)."),
        "edges_unconfirmed": "근거 사건 미연결 엣지의 D등급 분리 보관(스킬 §5 — 삭제 금지·본체 제외). 발굴 시 승격."
    },
    "cross_validator_applied": [
        "cfl-001(부친 별세 미해소 — to 비움)", "cfl-005(약혼 1896)", "cfl-006(독립협회 가입 1897)",
        "cfl-012(중앙총회장 1914-11 당선·1915-06-23 취임 — org-012·엣지 정정, '1912 초대 총회장' 서술 금지)",
        "cfl-016(청도회의 4월 단정 금지)", "cfl-030(동우구락부 1923-01-16)", "cfl-041(105인 유죄 6인 — 옥관빈 포함)",
        "cfl-044(미주 신민회 구상·초안설)", "cfl-046(청년학우회 직책 표기 병기)", "cfl-051(한독당 기초위원 양론 병기)"
    ],
    "place_normalization": [
        {"standard": "남곶면(南串面)", "variants": ["남부산면"], "status": "잠정 채택(cfl-036)",
         "note": "이주지 면명. 인명사전 기준 — 행정구역 개편(남곶면→남부산면 통합 가능성)으로 양립 가능성 병기."},
        {"standard": None, "variants": ["심정리(민백)", "노남리(인명사전)"], "status": "미해소(cfl-037)",
         "note": "김현진 서당 위치. 거주지(노남리)/수학지(심정리) 분리 양립 가능성 — 양설 병기 의무."},
        {"standard": "암화리", "variants": ["화암리"], "status": "잠정 채택(cfl-038)",
         "note": "점진학교 소재 리. 화암리는 글자 전도 오기 개연성 — 민백 내 항목 간 표기 불일치 가능성 주석."},
        {"standard": "대동문 밖 대동공사", "variants": ["조양문 밖 대동공창(大同工廠)"], "status": "잠정 채택(cfl-039)",
         "note": "길림사건(1927) 장소. 대동공사/대동공창은 동일 시설 표기 변형 개연성, 문 명칭은 실질 상충 — 병기."}
    ],
    "changes_from_round1": {
        "promoted_nodes": ["per-052 임치정", "per-053 방화중"],
        "added_edges": 9,
        "demoted_edges": sorted(DEMOTE.keys()),
        "retyped_edges": ["안창호→장리욱 mentor→comrade (근거 사건이 보여주는 관계만 분류 — 스킬 §2)"],
        "unconfirmed_rulings": "기존 미확정 3건(서재필·안중근·박용만) 전부 보류 유지 — 직접 상호작용 레코드 부재 확인(gaps.md §2-1 조건 ④)"
    },
    "changelog_v101": [
        "cross-validator 회부(2026-06-06) 이행: cfl-041 '잠정' 표기 보강(per-052·신민회 membership)",
        "per-054 조소앙 추가 + 엣지 2건(comrade 안창호, membership 한국독립당) — cfl-051 상충 주석을 관계 엣지에 기재(회부 요청 이행)",
        "meta.place_normalization 신설 — 지명 상충 4건(cfl-036/037/038/039) 채택 권고·병기 규칙 수록",
        "cfl-042(Moongate 형제)는 관계망 무영향 확인 — 해당 엣지·서술 없음(가족 family 엣지는 출생 레코드 근거)"
    ],
    "changelog_v102": [
        "timeline-analyst id 증분 통보(2026-06-06) 반영: 분리 신규 evt-tla-001(1912-11-20 중앙총회 출범 선포식, 안창호 actor)을 "
        "안창호→대한인국민회 membership 근거에 추가하고 description에 cfl-013 분리(11-08 대표원의회/11-20 선포식) 명기",
        "evt-tla-002(1920-01-01 신년축하회 연설 분리)는 network.json 무영향 확인 — evt-provgov-012 참조 엣지 0건"
    ],
    "changelog_v103": [
        "fact-checker 판정 3건 반영(2026-06-06, claims_register 288건): clm-0286 안치호 한자 D(판단 불가 — 양 표기 보존 유지, cfl-064 후보 회부), "
        "clm-0287 조병옥 흥사단 B(상충 불성립 — '확인 대상' 표기를 판정 결과로 교체), "
        "clm-0288 서재필→독립협회 B(간접 근거 채택 적합 — 개인 영향 clm-0259 D와 구분 명기)"
    ],
    "changelog_v110": [
        "표적 보완 라운드 증분(timeline.json 172건, evt-chrono-102~110) 반영 — D 강등 엣지 5건 재승격: "
        "신채호 conflict(evt-chrono-105, period 1919~1923→1923 축소), 이갑 patron(evt-chrono-104), "
        "송종익 patron(evt-chrono-103), 김규식 conflict(evt-chrono-105), 이광수 conflict(evt-chrono-108)",
        "근거 보강 4건: 이종호 comrade(+evt-shin-019 동반 망명), 송종익 comrade(+evt-chrono-102 약법 회람), "
        "이광수 comrade(+evt-chrono-106 입단)·흥사단 membership(+evt-chrono-106)",
        "evt-chrono-110(손정도 원동위원부)은 confidence D·미확인으로 승격 부적합(timeline-analyst 판정 동의) — D 보관 사유에 기록",
        "잔존 D 16건 사유에 표적 보완 라운드 결과(미발굴/검증 대기) 추기",
        "노드 후보 추가 제안: 김동삼·윤해(evt-chrono-105), 박현환(evt-chrono-107), 오영선(evt-chrono-109), 김희선(evt-shin-019 보강) "
        "+ 조직 후보 임시정부경제후원회(evt-chrono-109) — 차기 보완 라운드 회부"
    ],
    "changelog_v120": [
        "최종 증분(network_nodes_supplement.json) 병합 — 노드 6 추가(김동삼 per-055/윤해 per-056/박현환 per-057/오영선 per-058/김희선 per-059/임시정부경제후원회 org-022). "
        "supplement의 per-052~056은 본체 선점 id(임치정·방화중·조소앙)와 충돌해 재발급(REMAP 기록)",
        "확정 엣지 8건 병합(supplement 9건 중): 안창호-김동삼 comrade(1923)·안창호-윤해 conflict(1923, 갈등 축 8건째)·"
        "안창호-오영선 comrade(1926)·안창호-김희선 comrade(1910 한정, 1922 귀순 주석 유지 — 판정 ③)·"
        "박현환→수양동맹회 membership·오영선→org-022·안창호→org-022 membership·org-022→임정 patron",
        "판정 ①: 박현환 미확정 2건(직접 엣지·흥사단 membership) 보류 유지 + 박현환→수양동우회 membership은 evt-hsd-019 미거명으로 D 강등(레코드 거명 의무 일관 적용) — D 16→19",
        "판정 ②: org-org patron(org-022→org-014) 승인 — 6분류 내 유형, 후원 목적 정박·전달 실적 1차 미확인 명기",
        "cfl-066 최종 판정 반영(cross-validator): 안치호 한자 미해소 — 양표기 병기 확정, per-003 주석 갱신(fact-checker 번호 정정 cfl-064→066 포함)",
        "supplement 별칭 3건(evt-chrono-035/068, evt-phil-011) → 생존 id(evt-shin-019/evt-provgov-016/evt-provgov-022) 치환"
    ],
    "changelog_v121": [
        "fact-checker 통보 반영(team-lead 동결 예외 승인, 구조 변경 0): "
        "① per-003 안치호 — clm-0305(B) 이중 구조 주석 추가(가족 '존재'는 B, 한자 '표기'만 D) "
        "② per-054 조소앙 — death 1958→1958-09-10(민백 원문 day 확인, B), birth 1887 유지 + 음/양력 환산 쌍일 개연 주석",
        "v1.2.1 이후 최종 동결 — 추가 증분(cfl-041 판결문 등)은 Phase 4 이후 일괄 대기 목록으로 보관"
    ],
    "isolated_nodes": ISOLATED_DOC,
    "priority_gaps": [
        "[v1.1 해소] 갈등 구도 3건(신채호·이광수·김규식)·patron 2건(이갑·송종익) — 표적 보완 라운드로 재승격 완료",
        "조만식(시드 인물) 고립 지속 — 1907 감화·1932 옥바라지 레코드 (보완 라운드에서도 미발굴)",
        "박용만 고립 지속 — 미주 신문(신한민보 원지면) 사료 필요",
        "손정도 — evt-chrono-110 검증(heungsadan 인계) 통과 시 재승격 후보",
        "안중근 — primary-source 증분(공판 기록 역추적) 결과 대기"
    ]
}

out = {
    "meta": meta,
    "name_normalization": dict(sorted(norm.items())),
    "ambiguous_aliases": {k: {"node_ids": v, "note": "동명이호 '우강' — 양기탁(雩岡)/송종익(한자 미확인). 생몰·활동 무대로 구분(각 노드 summary 판정 기록)."}
                          for k, v in ambiguous.items()},
    "nodes": nodes,
    "edges": edges,
    "edges_unconfirmed": unconfirmed,
}

with open(OUT, 'w') as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

print(f"OK: nodes={len(nodes)} edges={len(edges)} unconfirmed={len(unconfirmed)}")
print(f"normalization aliases={len(norm)} ambiguous={list(ambiguous)}")
print(f"isolated(documented)={isolated}")
conf = sum(1 for e in edges if e['type'] == 'conflict')
print(f"conflict edges(main)={conf}")
ev_linked = sum(1 for e in edges if e['evidence_event_ids'])
print(f"evidence 연결률(본체): {ev_linked}/{len(edges)}")
