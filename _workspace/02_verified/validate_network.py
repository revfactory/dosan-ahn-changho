#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_network.py — relation-analyst (14)
network.json 확정 전 무결성 검사 (network-mapping 스킬 §산출물 검증 1~10항).

검사 항목:
 1. JSON 파싱, nodes/edges 배열 존재
 2. 노드 id 전역 유일 + 접두(per-/org-) 규칙
 3. 모든 엣지(본체+미확정)의 source/target 실재 — 끊어진 노드 참조 0건
 4. type 허용값(6종) — 미확정은 null 허용
 5. 본체 엣지 evidence_event_ids 비어 있지 않음 + 전 id가 timeline.json에 실재 — 끊어진 사건 참조 0건
 6. alt_names 충돌 → ambiguous_aliases 등재 + 판정 기록 확인
 7. conflict 엣지 ≥ 1 (0건이면 수집 누락 신호)
 8. 고립 노드 == meta.isolated_nodes 문서화 목록 (미문서 고립 0건)
 9. period-근거 사건 날짜 정합 (연 단위) — 범위 밖 근거는 period_note 의무
10. 시드 인물·조직 전원 노드 존재
+  period from<=to, 노드 생몰/조직 존속과의 정합(경고), 정규화 테이블 무결성
"""
import json, sys, os, re

BASE = os.path.dirname(os.path.abspath(__file__))
errors, warnings = [], []

def err(m): errors.append(m)
def warn(m): warnings.append(m)

# 1. 파싱
try:
    with open(os.path.join(BASE, 'network.json')) as f:
        net = json.load(f)
except Exception as e:
    print(f"FAIL: network.json 파싱 실패 — {e}"); sys.exit(1)
try:
    with open(os.path.join(BASE, 'timeline.json')) as f:
        tl = json.load(f)
except Exception as e:
    print(f"FAIL: timeline.json 파싱 실패 — {e}"); sys.exit(1)

for k in ('nodes', 'edges', 'edges_unconfirmed', 'name_normalization', 'meta'):
    if k not in net:
        err(f"[1] 필수 키 누락: {k}")

nodes = net.get('nodes', [])
edges = net.get('edges', [])
unconf = net.get('edges_unconfirmed', [])

# 2. 노드 id 유일성·접두
ids = [n['id'] for n in nodes]
dup = {i for i in ids if ids.count(i) > 1}
if dup: err(f"[2] 노드 id 중복: {sorted(dup)}")
for i in ids:
    if not re.match(r'^(per|org)-\d{3}$', i):
        err(f"[2] 접두/형식 위반 노드 id: {i}")
node_ids = set(ids)
nmap = {n['id']: n for n in nodes}

# 노드 필수 필드
for n in nodes:
    for k in ('id', 'name', 'alt_names', 'role', 'summary'):
        if k not in n or n[k] in (None, '') and k != 'alt_names':
            if not (k == 'alt_names' and isinstance(n.get(k), list)):
                err(f"[2] 노드 {n.get('id')} 필수 필드 결손: {k}")

# 3. 엣지 노드 참조
for tag, arr in (('본체', edges), ('미확정', unconf)):
    for j, e in enumerate(arr):
        for side in ('source', 'target'):
            if e.get(side) not in node_ids:
                err(f"[3] {tag} 엣지#{j} 끊어진 노드 참조: {side}={e.get(side)}")

# 4. type 허용값
ALLOWED = {'comrade', 'conflict', 'mentor', 'family', 'membership', 'patron'}
for j, e in enumerate(edges):
    if e.get('type') not in ALLOWED:
        err(f"[4] 본체 엣지#{j} type 위반: {e.get('type')}")
for j, e in enumerate(unconf):
    if e.get('type') is not None and e.get('type') not in ALLOWED:
        err(f"[4] 미확정 엣지#{j} type 위반: {e.get('type')}")

# 5. evidence 참조 무결성 (timeline.json 기준 + merged_from 별칭도 허용 범위로 인정하되 직접 id 권장)
tl_ids = {e['id'] for e in tl['events']}
tl_dates = {}
for e in tl['events']:
    d = e.get('date', {})
    sy = int(d['start'][:4]) if d.get('start') else None
    ey = int(d['end'][:4]) if d.get('end') else sy
    tl_dates[e['id']] = (sy, ey)
for j, e in enumerate(edges):
    evs = e.get('evidence_event_ids', [])
    if not evs:
        err(f"[5] 본체 엣지#{j} ({e['source']}->{e['target']} {e['type']}) evidence_event_ids 비어 있음")
    for i in evs:
        if i not in tl_ids:
            err(f"[5] 본체 엣지#{j} 끊어진 사건 참조: {i} (timeline.json에 없음)")

# 6. alt_names 충돌
seen = {}
collisions = {}
def strip_paren(s): return s.split('(')[0].strip()
for n in nodes:
    keys = {n['name']} | ({n['hanja']} if n.get('hanja') else set())
    for a in n.get('alt_names', []):
        keys |= {a, strip_paren(a)}
    for k in keys:
        if not k: continue
        if k in seen and seen[k] != n['id']:
            collisions.setdefault(k, set()).update([seen[k], n['id']])
        else:
            seen[k] = n['id']
amb = net.get('ambiguous_aliases', {})
for k, v in collisions.items():
    if k not in amb:
        err(f"[6] alt_names 충돌 미등재: '{k}' = {sorted(v)} (ambiguous_aliases에 판정 기록 필요)")
    else:
        for nid in v:
            if '동명' not in nmap[nid]['summary'] and '판정' not in nmap[nid]['summary']:
                warn(f"[6] '{k}' 충돌 노드 {nid} summary에 동명이인/이호 판정 기록 미확인")

# 7. conflict 엣지
n_conf = sum(1 for e in edges if e['type'] == 'conflict')
if n_conf == 0:
    err("[7] 본체 conflict 엣지 0건 — 수집 누락 신호 (스킬 §검증 7)")

# 8. 고립 노드 문서화
ref = set()
for e in edges:
    ref.add(e['source']); ref.add(e['target'])
isolated = sorted(node_ids - ref)
doc = set(net['meta'].get('isolated_nodes', {}))
undoc = [i for i in isolated if i not in doc]
stale = [i for i in doc if i not in isolated]
if undoc: err(f"[8] 미문서 고립 노드: {undoc}")
if stale: warn(f"[8] 문서화됐으나 실제로는 비고립: {stale}")

# 9. period-근거 정합 (연 단위) — 범위 밖 근거는 period_note 의무
for j, e in enumerate(edges):
    p = e.get('period', {})
    f_, t_ = p.get('from'), p.get('to')
    fy = int(f_[:4]) if f_ else None
    ty = int(t_[:4]) if t_ else None
    if fy and ty and fy > ty:
        err(f"[9] 엣지#{j} period 역전: {f_}~{t_}")
    out_of_range = []
    for i in e.get('evidence_event_ids', []):
        if i not in tl_dates: continue
        sy, ey = tl_dates[i]
        if sy is None: continue
        if (fy and ey < fy) or (ty and sy > ty):
            out_of_range.append(f"{i}({sy})")
    if out_of_range and not e.get('period_note'):
        err(f"[9] 엣지#{j} ({e['source']}->{e['target']} {e['type']}) 근거 사건이 period({f_}~{t_}) 밖인데 period_note 없음: {out_of_range}")
    # from이 모든 근거보다 이르고 period_note가 없으면 출처 없는 기간 주장
    yrs = [tl_dates[i][0] for i in e.get('evidence_event_ids', []) if i in tl_dates and tl_dates[i][0]]
    if fy and yrs and fy < min(yrs) and not e.get('period_note'):
        err(f"[9] 엣지#{j} ({e['source']}->{e['target']} {e['type']}) from({f_}) < 최조기 근거({min(yrs)})인데 period_note 없음")

# 노드 생몰 정합 (경고 수준) — period_note로 문서화된 엣지는 면제(검사 [9]와 동일 규약,
# 예: 전신-후신 전환 엣지의 to는 후신의 승계 완료 시점 기준이라 전신 해산일을 넘을 수 있음)
for j, e in enumerate(edges):
    p = e.get('period', {})
    for side in ('source', 'target'):
        n = nmap[e[side]]
        death = n.get('death')
        if death and p.get('to'):
            if int(p['to'][:4]) > int(str(death)[:4]):
                if e.get('period_note'):
                    continue  # 문서화된 면제
                warn(f"[9+] 엣지#{j} to({p['to']}) > {n['name']} 사망/해산({death}) — period_note 문서화 필요")

# 10. 시드 인물·조직
SEED = ['안창호','이승만','김구','이광수','서재필','양기탁','신채호','이동휘','조만식','송종익','이혜련',
        '독립협회','공립협회','신민회','대한인국민회','흥사단','수양동우회']
names = {n['name'] for n in nodes}
seed_missing = [s for s in SEED if s not in names and not any(s in (n['name'] or '') for n in nodes)]
if seed_missing: err(f"[10] 시드 누락: {seed_missing}")

# 정규화 테이블 무결성
for k, v in net.get('name_normalization', {}).items():
    if v not in node_ids:
        err(f"[N] 정규화 테이블 끊어진 참조: '{k}' -> {v}")

# 미확정 엣지에 사유 존재
for j, e in enumerate(unconf):
    if not e.get('unconfirmed_reason'):
        err(f"[D] 미확정 엣지#{j} unconfirmed_reason 누락")
    if e.get('grade') != 'D':
        err(f"[D] 미확정 엣지#{j} grade != 'D'")

print(f"검사 대상: 노드 {len(nodes)} / 본체 엣지 {len(edges)} / 미확정(D) {len(unconf)}")
print(f"conflict 엣지: {n_conf} / 고립 노드(문서화): {isolated}")
print(f"오류 {len(errors)}건 / 경고 {len(warnings)}건")
for m in errors: print("  ERROR:", m)
for m in warnings: print("  WARN :", m)
if errors:
    print("FAIL"); sys.exit(1)
print("PASS — 끊어진 참조 0(노드·사건), 미문서 고립 0, id 유일성 확인")
