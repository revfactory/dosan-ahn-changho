#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_ledger.py — 도산 소설 사실-허구 대장 기계 검사 엔진
소유자: fiction-fact-keeper (Task #3)
근거 스킬: fact-fiction-ledger §3(반사실 5종)·§4(검증 절차)

작가들이 분산 기록한 ledger(novel/ledger/ledger_a.json·ledger_b.json)와
정본(scene_ledger.json)을 검증 DB(_workspace/02_verified/)에 대조한다.

검사 항목(스킬 §4 기계 검사 부분):
  S1. ledger 스키마 유효 + scene_id 유일
  S2. 본문 장면 ↔ ledger 레코드 1:1 (chapters/*.md 안의 scene marker 대조)
  S3. 등장 인물 생몰 대조 (network.json birth/death — §3-1)
  S4. 시공간 대조 (timeline.json 동선 — 그 시기 도산이 다른 대륙? §3-2)
  S5. fact_anchors / adopted_lore / disputed_choice id 실재 (timeline·claims·conflicts)
  S6. disputed_choice 작품 내 일관성 (같은 cfl을 다르게 택하지 않음)
  S7. 1932+ 시대착오 호칭 금지표 휴리스틱 (voices.md C표)

* 의미 검사(대사가 검증 입장과 모순?)는 사람 판단 — 이 스크립트는 기계 검사만.
  단 S7 같은 패턴 검사로 명백한 시대착오는 보조 검출한다.

사용:
  python3 check_ledger.py                # 전 장 검사 + 정본 병합 미리보기
  python3 check_ledger.py --merge        # 정본 scene_ledger.json 병합 기록(verified는 손대지 않음)
  python3 check_ledger.py --chapter 9    # 특정 장만 검사
  python3 check_ledger.py --json         # 기계 판독용 JSON 결과
"""

import json
import os
import re
import sys
import argparse
from collections import defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
VER = os.path.join(ROOT, "_workspace", "02_verified")
NOVEL = os.path.join(ROOT, "novel")
LEDGER_DIR = os.path.join(NOVEL, "ledger")
CHAP_DIR = os.path.join(NOVEL, "chapters")

# ---------------------------------------------------------------------------
# 검증 DB 로드
# ---------------------------------------------------------------------------

def load_db():
    db = {}
    with open(os.path.join(VER, "timeline.json"), encoding="utf-8") as f:
        tl = json.load(f)
    db["events"] = {e["id"]: e for e in tl["events"]}

    with open(os.path.join(VER, "network.json"), encoding="utf-8") as f:
        nw = json.load(f)
    db["nodes"] = {n["id"]: n for n in nw["nodes"]}
    db["edges"] = nw["edges"]
    db["name_norm"] = nw.get("name_normalization", {})
    # 이름→per id 색인: 정규표 + 노드 name/alt_names 전부
    name_index = dict(db["name_norm"])
    for n in nw["nodes"]:
        name_index.setdefault(n["name"], n["id"])
        for a in n.get("alt_names", []):
            name_index.setdefault(a, n["id"])
    db["name_index"] = name_index

    with open(os.path.join(VER, "claims_register.json"), encoding="utf-8") as f:
        claims = json.load(f)
    db["claims"] = {c["claim_id"]: c for c in claims}

    with open(os.path.join(VER, "conflicts.md"), encoding="utf-8") as f:
        db["cfl_ids"] = set(re.findall(r"cfl-\d+", f.read()))

    return db


# ---------------------------------------------------------------------------
# 인물명 → per id 해석 (생몰 대조용)
# ---------------------------------------------------------------------------

def resolve_person(name, db):
    """장면 characters 항목의 이름을 per id로 해석. 못 찾으면 None(=창작 단역 후보).
    생몰 검사의 입력이므로 '실존 인물을 못 찾는 위음성'을 줄이는 방향으로 관대하게 해석.
    (창작 단역 오인 시는 경고일 뿐 차단이 아니므로, 미해석 비용 < 미검출 비용.)"""
    name = name.strip()
    if name in db["name_index"]:
        return db["name_index"][name]
    # 괄호 주석 제거: "안창호(도산)"·"밀러(민노아)"·"안필선(차남)" → 본이름
    bare = re.sub(r"[\(（].*?[\)）]", "", name)
    bare = re.sub(r"^\s*창작\s*단역\s*[:：]\s*", "", bare).strip()
    if bare in db["name_index"]:
        return db["name_index"][bare]
    # 토큰 단위(호+이름 분리): "도산 안창호"·"일송 김동삼"
    for token in re.split(r"[\s·]+", bare):
        if token and token in db["name_index"]:
            return db["name_index"][token]
    # 노드명이 복합어인 경우 부분 일치: "밀러" ⊂ "프레더릭 밀러"
    if len(bare) >= 2:
        for full_name, pid in db["name_index"].items():
            # bare가 노드 정식명/별칭의 공백분리 토큰 중 하나면 매칭
            if bare in re.split(r"[\s·]+", full_name):
                return pid
    return None


# 명시적으로 창작 단역/노드 미수록임이 outline·voices에 선언된 이름(생몰 검사 면제)
KNOWN_NONNODE = {
    "럼지", "코닐리어스 럼지", "Cornelius Rumsey",
    "조부", "할아버지",
    "한 손님", "손님",
    "심문자", "취조관", "일제 심문자", "형사", "프랑스조계 형사",
    "노파", "여관 주인", "오렌지밭 노동자", "군중", "청중",
    "조민희",  # 쾌재정 청중 — 노드 미수록 가능
}


# ---------------------------------------------------------------------------
# 시기/장소 → 대륙·지역 추정 (시공간 대조용)
# ---------------------------------------------------------------------------

REGION_KEYWORDS = {
    "미주": ["샌프란시스코", "리버사이드", "로스앤젤레스", "뉴욕", "캘리포니아",
             "솔트레이크", "상항", "파차파", "하와이", "시애틀", "밴쿠버",
             "미국", "멕시코", "공립관", "America", "U.S"],
    "중국": ["상하이", "상해", "프랑스조계", "베이징", "북경", "난징", "남경",
             "칭다오", "청도", "위해위", "웨이하이웨이", "길림", "만주", "봉천",
             "대동공사", "삼일당", "중국", "산둥"],
    "노령": ["블라디보스토크", "연해주", "노령", "시베리아", "봉밀산"],
    "유럽": ["베를린", "런던", "유럽"],
    "일본": ["도쿄", "동경", "일본"],
    "국내": ["평양", "강서", "한성", "서울", "정동", "종로", "대동군", "노남리",
             "봉상도", "도롱섬", "쾌재정", "삼선평", "용산", "대성학교", "행주",
             "인천", "제중원", "대전", "서대문", "송태산장", "대보산", "경성",
             "경기도", "탄포리", "동진면", "국수당", "마산동", "심정리", "망우리"],
}


def infer_region(place):
    if not place:
        return None
    hits = set()
    for region, kws in REGION_KEYWORDS.items():
        for kw in kws:
            if kw in place:
                hits.add(region)
                break
    if len(hits) == 1:
        return hits.pop()
    return None  # 모호하면 검사 보류(과잉 차단 회피)


def parse_year(s):
    if not s:
        return None
    m = re.search(r"(18|19)\d{2}", str(s))
    return int(m.group(0)) if m else None


def dosan_region_in_year(year, db):
    """그 해 도산(per-001)이 등장하는 timeline 사건들의 추정 지역 집합."""
    if year is None:
        return set()
    regions = set()
    for e in db["events"].values():
        if "안창호" not in e.get("actors", []):
            continue
        d = e.get("date", {})
        ys, ye = parse_year(d.get("start")), parse_year(d.get("end"))
        if ys is None:
            continue
        if ye is None:
            ye = ys
        if ys <= year <= ye:
            r = infer_region(e.get("place", {}).get("name", ""))
            if r:
                regions.add(r)
    return regions


# ---------------------------------------------------------------------------
# ledger 로드/병합
# ---------------------------------------------------------------------------

REQUIRED_FIELDS = ["scene_id", "chapter", "time", "place", "characters",
                   "fact_anchors", "inferences"]
INFERENCE_TYPES = {"추정대화", "추정장면", "창작인물", "시간압축", "내면추정"}


def load_ledgers():
    """ledger_a.json + ledger_b.json(작가 분산) + 이미 병합된 scene_ledger.json을 모은다.
    같은 scene_id가 여러 곳에 있으면 정본(scene_ledger) > a/b 순으로 우선."""
    records = {}
    sources = {}
    # 작가 분산 ledger 먼저(나중에 정본이 덮어씀)
    for fname in ["ledger_a.json", "ledger_b.json"]:
        path = os.path.join(LEDGER_DIR, fname)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as ex:
                print(f"  [경고] {fname} JSON 파싱 실패: {ex}", file=sys.stderr)
                continue
        scenes = data.get("scenes", data) if isinstance(data, dict) else data
        for rec in scenes:
            sid = rec.get("scene_id")
            if sid:
                records[sid] = rec
                sources[sid] = fname
    return records, sources


def load_canonical():
    path = os.path.join(LEDGER_DIR, "scene_ledger.json")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    scenes = data.get("scenes", data) if isinstance(data, dict) else data
    return {r["scene_id"]: r for r in scenes if r.get("scene_id")}


# ---------------------------------------------------------------------------
# 본문 scene marker 추출 (1:1 대조용)
# ---------------------------------------------------------------------------

def chapter_num_from_scene(sid):
    m = re.match(r"ch(\d+)", sid)
    return int(m.group(1)) if m else None


def scene_markers_in_chapters(chapter_filter=None):
    """chapters/*.md 안에서 <!-- scene: chXX-sY --> 형태의 마커를 수집.
    마커가 없는 장은 '마커 미기재'로 보고(차단 사유 아님 — 작가 합의 형식)."""
    found = defaultdict(set)  # chapter_num -> set(scene_id)
    files_seen = {}
    if not os.path.isdir(CHAP_DIR):
        return found, files_seen
    for fn in sorted(os.listdir(CHAP_DIR)):
        if not fn.endswith(".md"):
            continue
        m = re.match(r"ch(\d+)", fn)
        if not m:
            continue
        cnum = int(m.group(1))
        if chapter_filter is not None and cnum != chapter_filter:
            continue
        text = open(os.path.join(CHAP_DIR, fn), encoding="utf-8").read()
        markers = re.findall(r"<!--\s*scene:\s*(ch\d+-s\d+)\s*-->", text)
        files_seen[cnum] = (fn, len(markers))
        for mk in markers:
            found[cnum].add(mk)
    return found, files_seen


# ---------------------------------------------------------------------------
# 1932+ 시대착오 호칭 휴리스틱 (voices.md C표)
# ---------------------------------------------------------------------------

# 호칭(대사 형태)만 본문 스캔으로 검사 — 인물의 사후 '등장'은 S3(생몰, characters
# 배열 기준)가 권위 있게 잡으므로 본문 이름 스캔에서 제외(배경·전언 언급은 허용 — 거짓
# 양성 회피. 예: ch22 "1909년 안중근 의거 때도"는 정당한 전언).
ANACHRONISM_RULES = [
    # (적용 조건 함수, 위반 정규식, 설명)
    (lambda y: y is not None and y >= 1932,
     r"우남\s*형",
     "1932+ 이승만 '우남 형'(협력기 호칭) — '우남 박사' 또는 서신 형식"),
    (lambda y: y is not None and y < 1922,
     r"백범",
     "1922 이전 김구 '백범'(동지 승격 후 호칭) — '김구 군'"),
]


# S8 — D등급 금지 어록 자구 인용 검사 (voices.md §④·§D등급 3건)
# 본문에 아래 통용 D등급 어록의 자구가 그대로 나오면 차단(사상은 새 문장으로만 허용).
DGRADE_BANNED = [
    (r"낙망은\s*청년의\s*죽음", "§④ 통용 어록 '낙망은 청년의 죽음…'"),
    (r"서로\s*사랑하면\s*살고", "§④ 통용 어록 '서로 사랑하면 살고…'"),
    (r"힘은\s*건전한\s*인격과\s*공고한\s*단결", "§④ 통용 어록 '힘은 건전한 인격과 공고한 단결…'"),
    (r"우리는\s*자유의\s*인민", "§④ 통용 어록 '우리는 자유의 인민이니…'"),
    (r"참배나무에는\s*참배가", "§④ 통용 어록 '참배나무에는 참배가…'"),
    (r"밥을\s*먹어도\s*대한의\s*독립", "③ 신문조서 미확인 어록(20장 D등급)"),
    (r"낙심\s*마오", "② 임종 어록(22장 D등급)"),
]


def check_dgrade_quotes_in_chapter(cnum):
    """장 본문에서 D등급 금지 어록 자구를 검출(차단 사유)."""
    issues = []
    if not os.path.isdir(CHAP_DIR):
        return issues
    for fn in os.listdir(CHAP_DIR):
        if re.match(rf"ch0*{cnum}(\D|$)", fn) or fn == f"ch{cnum:02d}.md":
            text = open(os.path.join(CHAP_DIR, fn), encoding="utf-8").read()
            for pat, desc in DGRADE_BANNED:
                if re.search(pat, text):
                    issues.append(f"[S8 D등급] {fn}: 금지 어록 자구 인용 — {desc} "
                                  f"(사상은 새 문장으로만, 자구 금지)")
            break
    return issues


# 사망 후 직접 등장 금지(생몰표 — voices C표 + network death)
def check_dead_persons(rec, db, year):
    """장면 characters 중 그 해 이미 사망(또는 미출생)한 실명 *인물*의 직접 등장 검출.
    제외: ① org 노드(단체의 birth/death는 창립/해산 연도 — 인물 생몰 아님),
         ② '유해'·'묘'·'(전언)'·'회상' 표지(사후 안장·전언·회상은 스킬 명시 허용 —
            '사후 회상·묘는 가능', §3-1 직접 등장만 금지)."""
    issues = []
    for name in rec.get("characters", []):
        if name in KNOWN_NONNODE:
            continue
        # 사후 허용 표지: 유해/묘/전언/회상/추모 — 직접 '등장'이 아님
        if re.search(r"유해|묘|시신|영전|추모|회상|전언|\(전언\)|（전언）", name):
            continue
        pid = resolve_person(name, db)
        if pid is None:
            continue  # 창작 단역 후보 — 별도 보고(아래)
        if not pid.startswith("per-"):
            continue  # org 등 비인물 노드는 생몰 검사 대상 아님
        node = db["nodes"].get(pid)
        if not node:
            continue
        by, dy = parse_year(node.get("birth")), parse_year(node.get("death"))
        if year is not None and by is not None and year < by:
            issues.append(f"미출생 등장: {name}({pid}) 출생 {by} > 장면 {year}")
        if year is not None and dy is not None and year > dy:
            issues.append(f"사망 후 등장: {name}({pid}) 사망 {dy} < 장면 {year}")
    return issues


# ---------------------------------------------------------------------------
# 단일 레코드 검사
# ---------------------------------------------------------------------------

def check_record(rec, db):
    """한 장면 레코드를 검사. (errors, warnings, info) 반환."""
    errors, warnings, info = [], [], []
    sid = rec.get("scene_id", "<no scene_id>")

    # S1 스키마
    for fld in REQUIRED_FIELDS:
        if fld not in rec:
            errors.append(f"[S1] 필수 필드 누락: {fld}")
    for inf in rec.get("inferences", []):
        t = inf.get("type")
        if t and t not in INFERENCE_TYPES:
            warnings.append(f"[S1] 미정의 inference type: {t}")
        if t and "basis" not in inf and "desc" not in inf:
            warnings.append(f"[S1] inference에 basis/desc 없음: {inf}")

    year = parse_year(rec.get("time"))

    # S3 생몰
    for msg in check_dead_persons(rec, db, year):
        errors.append(f"[S3 생몰] {msg}")

    # 노드 미해석 인물 보고(창작 단역인지 확인 필요 — 차단 아님)
    # "이름(창작 단역)"·"이름(시점)" 류 괄호 주석은 떼고 본이름으로 판정
    creinf = " ".join(str(inf.get("desc", "")) for inf in rec.get("inferences", [])
                      if inf.get("type") == "창작인물")
    for name in rec.get("characters", []):
        # 작가 표기 관행 흡수: "창작단역: 신한촌 노인", "이름(창작 단역)", "이름(시점)"
        bare = re.sub(r"^\s*창작\s*단역\s*[:：]\s*", "", name)
        bare = re.sub(r"[\(（].*?[\)）]", "", bare).strip()
        if name in KNOWN_NONNODE or bare in KNOWN_NONNODE:
            continue
        # 괄호 주석에 '창작'이 표기되어 있으면 자기선언으로 인정
        if re.search(r"창작", name):
            continue
        if resolve_person(name, db) is None:
            # inferences 창작인물 desc에 이름이 들어 있으면 선언으로 인정
            declared = bool(bare) and (bare in creinf or name in creinf)
            if not declared:
                warnings.append(
                    f"[S3] '{name}' network 노드 미해석 — 실존 인물이면 정상(노드 미수록), "
                    f"창작 단역이면 inferences에 창작인물로 등록 권고")

    # S4 시공간
    region = infer_region(rec.get("place", ""))
    if region and year is not None:
        dosan_regions = dosan_region_in_year(year, db)
        if dosan_regions and region not in dosan_regions and "안창호" in [
                resolve_person(c, db) == "per-001" or c in ("안창호", "도산")
                for c in rec.get("characters", [])] or True:
            # 도산이 등장 인물이고, 장면 지역이 그 해 timeline 도산 지역과 불일치
            dosan_present = any(
                resolve_person(c, db) == "per-001" for c in rec.get("characters", []))
            if dosan_present and dosan_regions and region not in dosan_regions:
                warnings.append(
                    f"[S4 시공간] 장면 지역 '{region}'({rec.get('place')}) ≠ "
                    f"{year}년 timeline 도산 동선 {sorted(dosan_regions)} — "
                    f"시간압축/이동 중이면 inferences에 명기 권고")

    # S5 앵커 id 실재
    for anc in rec.get("fact_anchors", []):
        aid = anc.get("id", "")
        if aid.startswith("evt-"):
            if aid not in db["events"]:
                errors.append(f"[S5] fact_anchor evt 미실재: {aid}")
        elif aid.startswith("clm-"):
            if aid not in db["claims"]:
                errors.append(f"[S5] fact_anchor clm 미실재: {aid}")
        elif aid:
            warnings.append(f"[S5] fact_anchor id 형식 불명: {aid}")
    for lore in rec.get("adopted_lore", []):
        lid = lore.get("id", "")
        if lid.startswith("clm-") and lid not in db["claims"]:
            errors.append(f"[S5] adopted_lore clm 미실재: {lid}")
    for dc in rec.get("disputed_choice", []):
        did = dc.get("id", "")
        if did.startswith("cfl-") and did not in db["cfl_ids"]:
            errors.append(f"[S5] disputed_choice cfl 미실재: {did}")
        elif did.startswith("evt-") and did not in db["events"]:
            errors.append(f"[S5] disputed_choice evt 미실재: {did}")

    return errors, warnings, info


def check_anachronism_in_chapter(cnum, db):
    """장 본문에서 1932+ 호칭 등 시대착오 패턴 휴리스틱 검사.
    장의 대표 연도는 ledger 레코드 time에서 취득(없으면 본문 연도 스캔)."""
    issues = []
    fn = None
    for f in os.listdir(CHAP_DIR) if os.path.isdir(CHAP_DIR) else []:
        if re.match(rf"ch0*{cnum}\b", f) or f == f"ch{cnum:02d}.md":
            fn = f
            break
    if not fn:
        return issues
    text = open(os.path.join(CHAP_DIR, fn), encoding="utf-8").read()
    years = [int(y) for y in re.findall(r"(?:18|19)\d{2}", text)]
    rep_year = max(years) if years else None
    for cond, pat, desc in ANACHRONISM_RULES:
        if cond(rep_year) and re.search(pat, text):
            issues.append(f"[S7 시대착오] {fn}(연도~{rep_year}): {desc}")
    return issues


# ---------------------------------------------------------------------------
# 전체 검사 실행
# ---------------------------------------------------------------------------

def run(chapter_filter=None):
    db = load_db()
    records, rec_src = load_ledgers()
    canonical = load_canonical()
    # 정본이 작가 분산을 덮어쓴다(정본이 진실)
    merged = dict(records)
    merged.update(canonical)

    if chapter_filter is not None:
        merged = {s: r for s, r in merged.items()
                  if chapter_num_from_scene(s) == chapter_filter}

    result = {"scenes": {}, "global": [], "summary": {}}

    # scene_id 유일성(이미 dict라 충돌은 로드 시 흡수 — 원본 중복 재검)
    seen_ids = defaultdict(int)
    for fname in ["ledger_a.json", "ledger_b.json", "scene_ledger.json"]:
        path = os.path.join(LEDGER_DIR, fname)
        if os.path.exists(path):
            data = json.load(open(path, encoding="utf-8"))
            scenes = data.get("scenes", data) if isinstance(data, dict) else data
            for r in scenes:
                if r.get("scene_id"):
                    seen_ids[r["scene_id"]] += 1
    dup = {s: c for s, c in seen_ids.items() if c > 1}
    # 정본+a/b에 같은 id가 있는 건 정상(병합) — a와 b 양쪽에만 있으면 충돌
    # 단순화: 3회 이상 등장만 경고
    for s, c in dup.items():
        if c >= 3:
            result["global"].append(f"[S1] scene_id 다중 정의(>={c}): {s}")

    # S6 disputed_choice 작품 내 일관성
    # 핵심 결정(choice의 '—'/'('/':' 앞 본절)이 다르면 진짜 모순(차단).
    # 본절은 같고 부가 설명만 다르면 표기 정돈 권고(경고) — 작품 자체는 일관.
    def core_choice(s):
        # 핵심 결정만 추출: 부가 설명은 보통 '—'(em-dash) 뒤에 온다(분리 기준).
        # ASCII 하이픈('1910-여름')·괄호 안 병기(전승명 등)는 결정 본절이므로 유지.
        # 결정 키워드 정규화: 채택/미채택/회피 등은 핵심 — 괄호 병기만 제거 후 비교.
        s = str(s)
        s = re.split(r"—", s, maxsplit=1)[0]            # em-dash 뒤 설명 제거
        s = re.sub(r"[(（][^)）]*[)）]", "", s)            # 괄호 안 병기 제거
        return re.sub(r"\s+", "", s).strip()

    cfl_full = defaultdict(set)
    cfl_core = defaultdict(set)
    for r in merged.values():
        for dc in r.get("disputed_choice", []):
            if dc.get("id"):
                ch = str(dc.get("choice", ""))
                cfl_full[dc["id"]].add(ch)
                cfl_core[dc["id"]].add(core_choice(ch))
    for cid, fulls in cfl_full.items():
        if len(cfl_core[cid]) > 1:
            result["global"].append(
                f"[S6] disputed_choice 불일치 — {cid}: 핵심 결정 상충 "
                f"{sorted(cfl_core[cid])} (한 작품 내 일관 택일 위반)")
        elif len(fulls) > 1:
            result["global"].append(
                f"[S6 표기] disputed_choice {cid}: 결정은 일관하나 표기 상이 — "
                f"문구 정돈 권고 {sorted(fulls)}")

    # S2 본문↔레코드 1:1
    markers, files_seen = scene_markers_in_chapters(chapter_filter)
    for cnum, mk_set in markers.items():
        ledger_scenes = {s for s in merged if chapter_num_from_scene(s) == cnum}
        only_text = mk_set - ledger_scenes
        only_ledger = ledger_scenes - mk_set
        if only_text:
            result["global"].append(
                f"[S2] 본문 마커에만 있고 ledger 없음(ch{cnum}): {sorted(only_text)}")
        if only_ledger:
            result["global"].append(
                f"[S2] ledger에만 있고 본문 마커 없음(ch{cnum}): {sorted(only_ledger)}")

    # 레코드별 검사
    for sid, rec in sorted(merged.items()):
        e, w, i = check_record(rec, db)
        result["scenes"][sid] = {
            "chapter": rec.get("chapter"),
            "verified": rec.get("verified", False),
            "errors": e, "warnings": w, "info": i,
            "source": rec_src.get(sid, "scene_ledger.json"),
        }

    # S7 시대착오(본문 휴리스틱)
    if os.path.isdir(CHAP_DIR):
        # ledger 유무와 무관하게 존재하는 모든 본문 장을 D등급·시대착오 스캔.
        # (D등급 어록 자구는 ledger가 오기 전에라도 잡아야 한다 — 가장 치명적)
        chap_nums = set()
        for f in os.listdir(CHAP_DIR):
            m = re.match(r"ch(\d+)", f)
            if m and (chapter_filter is None or int(m.group(1)) == chapter_filter):
                chap_nums.add(int(m.group(1)))
        chap_nums |= {chapter_num_from_scene(s) for s in merged
                      if chapter_num_from_scene(s) is not None}
        for cnum in sorted(c for c in chap_nums if c is not None):
            for iss in check_anachronism_in_chapter(cnum, db):
                result["global"].append(iss)
            for iss in check_dgrade_quotes_in_chapter(cnum):
                result["global"].append(iss)

    # 요약
    n_scenes = len(merged)
    # "[S6]"는 진짜 모순(차단), "[S6 표기]"는 권고(비차단) — 후자는 카운트 제외
    n_err = sum(len(v["errors"]) for v in result["scenes"].values()) + \
        sum(1 for g in result["global"] if "[S1]" in g or "[S2]" in g or
            "[S6] " in g or "[S6]:" in g or "[S7]" in g or "[S8" in g)
    n_verified = sum(1 for v in result["scenes"].values() if v["verified"])
    result["summary"] = {
        "scenes": n_scenes,
        "verified": n_verified,
        "errors": n_err,
        "global_issues": len(result["global"]),
        "chapter_files": {c: f for c, (f, _) in files_seen.items()},
    }
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chapter", type=int, default=None)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--merge", action="store_true",
                    help="정본 scene_ledger.json 병합 기록(verified 미변경)")
    args = ap.parse_args()

    result = run(args.chapter)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    s = result["summary"]
    print("=" * 64)
    print("check_ledger.py — 사실-허구 대장 기계 검사")
    print("=" * 64)
    if s["scenes"] == 0:
        print("등록된 장면 레코드 없음(작가 ledger 미도착).")
        print(f"본문 장 파일: {s['chapter_files'] or '없음'}")
    print(f"장면: {s['scenes']} | verified: {s['verified']} | "
          f"레코드 오류: {sum(len(v['errors']) for v in result['scenes'].values())} | "
          f"전역 이슈: {s['global_issues']}")
    print()

    if result["global"]:
        print("── 전역 이슈 ──")
        for g in result["global"]:
            print(f"  {g}")
        print()

    for sid, v in result["scenes"].items():
        if v["errors"] or v["warnings"]:
            flag = "❌" if v["errors"] else "⚠"
            print(f"{flag} {sid} (ch{v['chapter']}, src={v['source']}, "
                  f"verified={v['verified']})")
            for e in v["errors"]:
                print(f"    오류: {e}")
            for w in v["warnings"]:
                print(f"    경고: {w}")
    clean = [sid for sid, v in result["scenes"].items()
             if not v["errors"] and not v["warnings"]]
    if clean:
        print(f"\n무결 장면({len(clean)}): {', '.join(clean)}")

    if args.merge:
        merge_canonical(result)


def merge_canonical(result):
    """작가 분산 ledger를 정본 scene_ledger.json에 병합.
    verified 플래그는 절대 손대지 않는다(keeper 수동 확정 영역)."""
    records, _ = load_ledgers()
    canonical = load_canonical()
    out = dict(records)
    # 정본에 이미 있는 verified 상태 보존
    for sid, rec in canonical.items():
        out[sid] = rec
    for sid, rec in records.items():
        if sid in canonical:
            # 작가 수정분 반영하되 keeper의 verified는 유지
            v = canonical[sid].get("verified", False)
            out[sid] = rec
            out[sid]["verified"] = v
    payload = {
        "meta": {
            "owner": "fiction-fact-keeper",
            "note": "정본 — verified=true는 keeper만 기록. check_ledger.py --merge 생성.",
        },
        "scenes": [out[s] for s in sorted(out)],
    }
    path = os.path.join(LEDGER_DIR, "scene_ledger.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"\n[병합] 정본 기록: {path} ({len(out)} 장면)")


if __name__ == "__main__":
    main()
