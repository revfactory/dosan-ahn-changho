#!/usr/bin/env python3
"""출처 마스터(citations.json sources 절) 생성 — citation-manager.

입력:
  _workspace/01_research/primary-source_catalog.json  (47건, src-pri-001~047 — id 승계)
  _workspace/02_verified/claims_register.json          (305건의 sources 절 — 중복 제거 후 등재)

출력:
  _workspace/03_content/citations.json                 {refs: [...기존 유지...], sources: [...]}
  _workspace/03_content/_citation_work/claim_source_map.json  claim_id -> [{source_id, locator}]
  _workspace/03_content/_citation_work/source_keys.json       정규화 키 -> source_id (증분 등재·id 안정성)

재실행 규칙: source_keys.json이 있으면 기존 발급 id를 절대 변경하지 않고
신규 키에만 다음 일련번호를 발급한다 (id 재사용·변경 금지).
"""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote

ROOT = Path(__file__).resolve().parents[2]  # _workspace/
CATALOG = ROOT / "01_research" / "primary-source_catalog.json"
CLAIMS = ROOT / "02_verified" / "claims_register.json"
TIMELINE = ROOT / "02_verified" / "timeline.json"
CONFLICTS = ROOT / "02_verified" / "conflicts.md"
OUT_DIR = ROOT / "03_content"
WORK_DIR = OUT_DIR / "_citation_work"
CITATIONS = OUT_DIR / "citations.json"
KEYS_FILE = WORK_DIR / "source_keys.json"
MAP_FILE = WORK_DIR / "claim_source_map.json"
EVT_MAP_FILE = WORK_DIR / "event_source_map.json"
CFL_MAP_FILE = WORK_DIR / "conflict_event_map.json"

ACCESSED = "2026-06-06"  # 검증(Phase 2) 수행일 = 전 출처 실접속일

TYPE_CODE = {"primary": "pri", "academic": "aca", "institutional": "ins",
             "encyclopedia": "enc", "web": "web"}


# ---------------------------------------------------------------- URL 정규화
def canon_url(u: str) -> str:
    """같은 출처의 URL 변형(모바일 경로·여분 쿼리·인코딩 차이)을 단일 키로."""
    p = urlparse(u.strip())
    host = p.netloc.lower().replace("www.", "")
    q = parse_qs(p.query)
    if "search.i815.or.kr" in host and q.get("id"):
        return f"i815-dict-{q['id'][0]}"
    if "encykorea.aks.ac.kr" in host:
        if q.get("contents_id"):                      # 구형 Contents/Index URL
            return f"encykorea-{q['contents_id'][0]}"
        return "encykorea-" + unquote(p.path).rstrip("/").split("/")[-1]
    if "contents.history.go.kr" in host and q.get("levelId"):
        return f"contents-history-{q['levelId'][0]}"
    if "db.history.go.kr" in host and q.get("levelId"):
        return f"db-history-{q['levelId'][0]}"
    if "wikipedia.org" in host or "wikisource.org" in host or "namu.wiki" in host:
        return host + ":" + unquote(p.path).rstrip("/")
    return host + unquote(p.path).rstrip("/") + ("?" + p.query if p.query else "")


def canon_key(src: dict) -> str:
    if src.get("url"):
        return canon_url(src["url"])
    return "TITLE:" + re.sub(r"\s+", "", src["title"])[:80]


# -------------------------------------------- primary 표기 -> 카탈로그 id 승계
# claims_register의 type=primary 표기(고유 22종)를 사료 카탈로그 id로 수동 매핑.
# 카탈로그에 없는 신규 사료(중외일보 1930-01-11)만 src-pri-048을 증분 발급.
PRIMARY_MAP = [  # (제목 판별 부분 문자열, [카탈로그 id, ...], locator 보강)
    ("105인 사건 제30회 공판시말서", ["src-pri-029"], None),
    ("「개조」, 주요한 편", ["src-pri-006"], "『안도산전서』 수록본"),
    ("「거국가」 전문", ["src-pri-010"], "위키문헌 전재본"),
    ("「동포에게 고하는 글」 원문", ["src-pri-009"], "『안도산전서』 수록 추정"),
    ("『서우』 게재 삼선평 연설", ["src-pri-032"], "게재 호수 미확인"),
    ("공립신보 창간호", ["src-pri-011"], "창간호(1905-11-22)"),
    ("공립신보(共立新報) 1905", ["src-pri-011"], None),
    ("대한민국임시정부 공보", ["src-pri-030"], None),
    ("도산 안창호 일기", ["src-pri-001"], None),
    ("독립신문 「독립운동의 진행책과 시국문제의 해결」", ["src-pri-013"],
     "「독립운동의 진행책과 시국문제의 해결」(원문 미확인, 2차 인용)"),
    ("독립신문 연재 「우리 국민이 단정코 실행할 육대사」", ["src-pri-007"],
     "『독립신문』 1920-01 연재(원문 미확인, 2차 인용)"),
    ("독립신문(상하이판) 1919-08-21", ["src-pri-013"], None),
    ("독립신문(상하이판) 창간호", ["src-pri-013"], "창간호(1919-08-21)"),
    ("독립신문(상해판) 창간호", ["src-pri-013"], "창간호(1919-08-21)"),
    ("동광 창간호", ["src-pri-022"], "창간호(1926-05)"),
    ("동광(東光) 1926-05", ["src-pri-022"], None),
    ("동아일보 1932-06 압송", ["src-pri-014"], "1932-06 압송·공판 보도 기사군"),
    ("동아일보·조선일보 1938-03 서거 보도", ["src-pri-014", "src-pri-015"],
     "1938-03 서거 보도 기사군"),
    ("상해판 『독립신문』 1920년 1월 연재 연설문", ["src-pri-007"],
     "『독립신문』 1920-01 연재(원문 미열람)"),
    ("신한민보(新韓民報) 1909-02-10", ["src-pri-012"], None),
    ("안창호 집조", ["src-pri-024"], None),
    ("중외일보 1930년 1월 11일자", ["src-pri-048"], "1930-01-11자(필리핀 이주 계획 보도)"),
]

# 카탈로그 외 신규 사료 — citation-manager 발급분 (primary-source-researcher에 통지 대상)
NEW_PRIMARY = [{
    "id": "src-pri-048",
    "type": "primary",
    "author": None,
    "title": "중외일보 1930-01-11자 필리핀 이주 계획 보도 기사",
    "publisher": "중외일보 — 한국사데이터베이스 수록",
    "year": 1930,
    "url": "https://db.history.go.kr/modern/level.do?levelId=npjo_1930_01_11_w0003",
    "accessed": ACCESSED,
}]


# -------------------------------------------------- 도메인 -> 서지 필드 기본값
# (작성 주체 author, 사이트명 publisher) — 웹/기관/백과 표기 형식의 두 좌표.
DOMAIN_BIB = {
    "encykorea.aks.ac.kr": ("한국학중앙연구원", "한국민족문화대백과사전"),
    "search.i815.or.kr": ("독립기념관", "독립운동인명사전(한국독립운동정보시스템)"),
    "i815.or.kr": ("독립기념관", "월간 독립기념관"),
    "contents.history.go.kr": ("국사편찬위원회", "우리역사넷"),
    "db.history.go.kr": ("국사편찬위원회", "한국사데이터베이스"),
    "yka.or.kr": ("흥사단", "흥사단 공식 사이트"),
    "ykabs.or.kr": ("부산흥사단", "부산흥사단 사이트"),
    "tgyka.or.kr": ("대구흥사단", "대구흥사단 사이트"),
    "syka.dothome.co.kr": ("서울흥사단", "서울흥사단 사이트"),
    "ykausa.org": ("흥사단 미주위원부(LA)", "흥사단 미주위원부 사이트"),
    "e-gonghun.mpva.go.kr": ("국가보훈부", "공훈전자사료관"),
    "knamf.org": ("대한인국민회기념재단", "대한인국민회기념재단 사이트"),
    "kahistorymuseum.org": ("한인역사박물관", "한인역사박물관 사이트"),
    "ko.wikipedia.org": (None, "위키백과"),
    "en.wikipedia.org": (None, "Wikipedia(영문)"),
    "ko.wikisource.org": (None, "위키문헌"),
    "namu.wiki": (None, "나무위키"),
    "newworldencyclopedia.org": (None, "New World Encyclopedia"),
    "britannica.com": (None, "Encyclopaedia Britannica"),
    "guri.grandculture.net": ("한국학중앙연구원", "디지털구리문화대전(한국향토문화전자대전)"),
    "grandculture.net": ("한국학중앙연구원", "디지털강남문화대전(한국향토문화전자대전)"),
    "okpedia.kr": ("한국학중앙연구원", "세계한민족문화대전"),
    "heritage.go.kr": ("국가유산청", "국가유산포털"),
    "theme.archives.go.kr": ("국가기록원", "국가기록원"),
    "archive.sb.go.kr": ("성북구청", "성북마을아카이브"),
    "nmkpg.go.kr": ("국립대한민국임시정부기념관", "국립대한민국임시정부기념관 웹진"),
    "ncms.nculture.org": ("한국문화정보원", "지역N문화"),
    "kculture.or.kr": ("한국문화정보원", "한국문화정보원"),
    "korea.kr": ("국가보훈처", "대한민국 정책브리핑"),
    "ahnchangho.or.kr": ("도산안창호선생기념사업회", "도산안창호선생기념사업회 온라인기념관"),
    "dornsife.usc.edu": ("USC Dornsife Korean Studies Institute", "USC Dornsife"),
    "oac.cdlib.org": ("USC Libraries", "Online Archive of California"),
    "pachappacamp.ucr.edu": ("UCR Young Oak Kim Center for Korean American Studies",
                             "Pachappa Camp 프로젝트 사이트"),
    "history.navy.mil": ("Naval History and Heritage Command", "history.navy.mil"),
    "khan.co.kr": (None, "경향신문"),
    "kgnews.co.kr": (None, "경기신문"),
    "seoul.co.kr": (None, "서울신문"),
    "hankookilbo.com": (None, "한국일보"),
    "koreaherald.com": (None, "The Korea Herald"),
    "kidoktimes.co.kr": (None, "기독타임즈"),
    "m.e-jlmaeil.com": (None, "e-전라매일"),
    "brunch.co.kr": (None, "브런치"),
    "pbs.org": (None, "PBS NewsHour"),
    "asamnews.com": (None, "AsAmNews"),
    "imdb.com": (None, "IMDb"),
    "walkoffame.com": (None, "Hollywood Walk of Fame"),
    "hmdb.org": (None, "Historical Marker Database(HMDB)"),
    "wikitree.com": (None, "WikiTree"),
    "kci.go.kr": (None, "KCI 한국학술지인용색인"),
    "dbpia.co.kr": (None, "DBpia"),
    "scienceon.kisti.re.kr": (None, "ScienceON"),
    "db.koreascholar.com": (None, "Korea Scholar"),
    "escholarship.org": (None, "eScholarship(UC)"),
    "accesson.kr": (None, "AccessON"),
    "iat.kookmin.ac.kr": (None, "국민대학교"),
    "archive.much.go.kr": ("대한민국역사박물관", "근현대사 아카이브"),
}

# 그룹 단위 type 확정 (claims 내 type 표기가 갈린 그룹 + 분류 원칙 보정)
#   원칙: 백과사전 표제어(위키류·문화대전류)는 enc, 공공·단체 기관물은 ins.
TYPE_OVERRIDE = {
    "ko.wikipedia.org:/wiki/안창호": "encyclopedia",
    "guri.grandculture.net/guri/toc/GC06142033": "encyclopedia",
    "grandculture.net/gangnam/toc/GC04830008": "encyclopedia",
    "okpedia.kr/Contents/ContentsView?contentsId=GC95100282&localCode=naw": "encyclopedia",
    "okpedia.kr/Contents/ContentsView?contentsId=GC95100211&localCode=naw": "encyclopedia",
    "archive.sb.go.kr/isbcc/town/815/timeline.do": "institutional",
    "yka.or.kr/html/info/book_search.asp?no=1018": "institutional",
}

# 정규화 키 -> 서지 필드 수동 확정 (고빈도·형식 판별이 자동화로 불완전한 그룹)
CURATED = {
    "i815-dict-696": {
        "author": "이명화", "title": "안창호",
        "publisher": "독립운동인명사전(독립기념관 한국독립운동정보시스템)", "year": None},
    "contents-history-kc_n402200": {
        "author": "국사편찬위원회", "title": "안창호 (한국사 인물)",
        "publisher": "우리역사넷", "year": None},
    "encykorea-E0035050": {
        "author": "한국학중앙연구원", "title": "안창호",
        "publisher": "한국민족문화대백과사전", "year": None},
    "ko.wikipedia.org:/wiki/안창호": {
        "author": None, "title": "안창호", "publisher": "위키백과", "year": None},
    "yka.or.kr/html/about_dosan/dosans_chronology.asp": {
        "author": "흥사단", "title": "도산 연보", "publisher": "흥사단 공식 사이트", "year": None},
    "contents-history-kc_o404400": {
        "author": "국사편찬위원회", "title": "흥사단 (한국사연대기)",
        "publisher": "우리역사넷", "year": None},
    "khan.co.kr/article/201905231407001": {
        "author": "이기환", "title": "[이기환의 흔적의 역사] 억장이 무너지는 도산 안창호 선생의 사진 3장",
        "publisher": "경향신문", "year": 2019},
    "ko.wikisource.org:/wiki/도산_안창호": {
        "author": "이광수", "title": "도산 안창호",
        "publisher": "위키문헌 수록본(초판 도산안창호기념사업회, 1947)", "year": 1947},
    "knamf.org/안창호": {
        "author": "대한인국민회기념재단", "title": "안창호 약전",
        "publisher": "대한인국민회기념재단 사이트", "year": None},
    "contents-history-eh_n0760_0010": {
        "author": "국사편찬위원회", "title": "안창호 관련 서술",
        "publisher": "우리역사넷", "year": None},
    "contents-history-kc_o400900": {
        "author": "국사편찬위원회", "title": "대한인 국민회",
        "publisher": "우리역사넷", "year": None},
    "archive.sb.go.kr/isbcc/town/815/timeline.do": {
        "author": "성북구청", "title": "성북마을발견+독립운동 아카이브 연표",
        "publisher": "성북마을아카이브", "year": None},
    "i815-dict-2281": {
        "author": "독립기념관", "title": "독립운동인명사전 표제어(항목명 미상 — 사전 id 2281, 서지 보강 대상)",
        "publisher": "독립운동인명사전(한국독립운동정보시스템)", "year": None},
    "seoul.co.kr/news/life/2016/03/01/20160301800020": {
        "author": None, "title": "멕시코까지 퍼져나간 독립의 꿈…안창호 행적 첫 발견",
        "publisher": "서울신문", "year": 2016},
    "m.e-jlmaeil.com/view.php?idx=240536": {
        "author": None, "title": "윤치호 '애국가', 안창호 '거국가'",
        "publisher": "e-전라매일", "year": None},
    "iat.kookmin.ac.kr/international/community/newnhot/press/1071250?pn=90": {
        "author": "장석흥", "title": "실록 대한민국임시정부 — 안창호와 민족유일당 운동",
        "publisher": "국민대학교(언론 기고 소개)", "year": None},
    "koreanperson.web3.newwaynet.co.kr/bbs/board.php?bo_table=sub02_03&wr_id=2": {
        "author": None, "title": "무실역행의 지도자, 안창호",
        "publisher": "역사 인물 웹자료(koreanperson.web3.newwaynet.co.kr)", "year": None},
    "brunch.co.kr/@charam/16": {
        "author": None, "title": "도산 안창호 상하이 연설",
        "publisher": "브런치(『안도산전서』 수록본 전사)", "year": None},
    "ahnchangho.or.kr/site/main/d02_02.php": {
        "author": "도산안창호선생기념사업회", "title": "온라인기념관 도산 연보",
        "publisher": "도산안창호선생기념사업회 온라인기념관", "year": None},
    "en.wikipedia.org:/wiki/Ahn_Chang_Ho": {
        "author": None, "title": "Ahn Chang Ho", "publisher": "Wikipedia(영문)", "year": None},
    "yka.or.kr/html/info/book_search.asp?no=364": {
        "author": "흥사단", "title": "흥사단 소장 『동광』 1926년 11월호(제7호) 서지",
        "publisher": "흥사단 공식 사이트", "year": None},
    "korea.kr/briefing/pressReleaseView.do?newsId=155805121": {
        "author": "국가보훈처", "title": "1월의 독립운동가 이갑 선생",
        "publisher": "대한민국 정책브리핑", "year": 2011},
    "dornsife.usc.edu/ksi/ahn-family-house": {
        "author": "USC Dornsife Korean Studies Institute", "title": "Ahn Family House",
        "publisher": "USC Dornsife", "year": None},
    "pachappacamp.ucr.edu/history-timeline": {
        "author": "UCR Young Oak Kim Center for Korean American Studies",
        "title": "Pachappa Camp: History & Timeline",
        "publisher": "Pachappa Camp 프로젝트 사이트", "year": None},
    "escholarship.org/uc/item/8p88m8mw": {
        "author": "Edward T. Chang", "title": "Pachappa Camp: The First Koreatown in the United States",
        "publisher": "Lexington Books(eScholarship 공개본)", "year": 2021},
    "oac.cdlib.org/findaid/ark:/13030/c8qj7pmj": {
        "author": "USC Libraries", "title": "Philip Ahn papers finding aid",
        "publisher": "Online Archive of California", "year": None},
    "accesson.kr/rks/assets/pdf/2562/journal-23-1-161.pdf": {
        "author": None, "title": "Deportation of Dosan Ahn Chang Ho (1924–1926)",
        "publisher": "Review of Korean Studies", "year": None},
    "TITLE:김원모,「한국민족운동의시단:미주대한인국민회중앙총회(안창호)의이광수신한민보주필초빙교섭(1914)」": {
        "author": "김원모",
        "title": "한국 민족운동의 시단: 미주 대한인국민회 중앙총회(안창호)의 이광수 신한민보 주필 초빙교섭(1914)",
        "publisher": "오프라인 학술 문헌(소장처: 국내 학술 DB 미확정 — 서지 보강 대상)", "year": None},
    # --- 학술 문헌 전수 수동 확정 (자동 파싱 금지 — 서지 정확성 우선) ---
    "db.koreascholar.com/Article/Detail/328875": {
        "author": None, "title": "도산 안창호의 멕시코 순행과 그 업적",
        "publisher": "Korea Scholar 등재 논문(저자·게재지 서지 보강 대상)", "year": None},
    "dbpia.co.kr/journal/articleDetail?nodeId=NODE11582497": {
        "author": "이선민", "title": "신민회의 결성 시점에 대한 재고찰",
        "publisher": "『대동문화연구』 121", "year": 2023},
    "kci.go.kr/kciportal/ci/sereArticleSearch/ciSereArtiView.kci?sereArticleSearchBean.artiId=ART002061754": {
        "author": "김도형", "title": "도산 안창호의 '여행권'을 통해 본 독립운동 행적",
        "publisher": "『한국독립운동사연구』 52", "year": 2015},
    "kci.go.kr/kciportal/ci/sereArticleSearch/ciSereArtiView.kci?sereArticleSearchBean.artiId=ART001459580": {
        "author": None, "title": "상해판 『독립신문』과 안창호",
        "publisher": "KCI 등재 논문(저자·게재지 서지 보강 대상)", "year": None},
    "accesson.kr/rks/assets/pdf/2562/journal-23-1-161.pdf": {
        "author": None, "title": "Deportation of Dosan Ahn Chang Ho (1924–1926)",
        "publisher": "『Review of Korean Studies』 23(1)", "year": None},
    "scienceon.kisti.re.kr/srch/selectPORSrchArticle.do?cn=DIKO0015504019": {
        "author": None, "title": "1930년 한국독립당 당의·당강의 이념과 성격",
        "publisher": "학위논문(ScienceON 등재 — 저자 서지 보강 대상)", "year": None},
    "kci.go.kr/kciportal/ci/sereArticleSearch/ciSereArtiView.kci?sereArticleSearchBean.artiId=ART001936844": {
        "author": "장석흥",
        "title": "차리석의 '한국독립당 당의의 이론체계 초안(1942)'과 안창호의 대공주의",
        "publisher": "『한국독립운동사연구』 49", "year": 2014},
    "dbpia.co.kr/journal/articleDetail?nodeId=NODE07369851": {
        "author": "박만규", "title": "안창호의 대공주의에 관한 두 가지 쟁점",
        "publisher": "『한국독립운동사연구』 61, 187–219쪽", "year": 2018},
    "kci.go.kr/kciportal/ci/sereArticleSearch/ciSereArtiView.kci?sereArticleSearchBean.artiId=ART001827032": {
        "author": "이명화", "title": "도산 안창호의 서대문형무소 투옥과 수감 생활",
        "publisher": "『한국독립운동사연구』 46", "year": 2013},
    "kci.go.kr/kciportal/ci/sereArticleSearch/ciSereArtiView.kci?sereArticleSearchBean.artiId=ART002430591": {
        "author": None, "title": "흥사단의 1차 약법개정 논의와 운동노선",
        "publisher": "KCI 등재 논문(저자·게재지 서지 보강 대상)", "year": None},
    # --- 제목 잔존 주석 보정 ---
    "ykausa.org/bbs/board.php?bo_table=Freeboard&wr_id=149": {
        "author": "흥사단 미주위원부(LA)", "title": "도산의 삼선평 연설 초록",
        "publisher": "흥사단 미주위원부 사이트", "year": None},
}

# 제목에서 떼어낼 주석성 꼬리 (claims 검증 메모 — 서지가 아님)
# 대시는 반드시 양쪽 공백을 요구한다 — "e-전라매일"류 하이픈 합성어 절단 방지.
NOTE_PAT = re.compile(
    r"\s+[—–-]\s+[^—–]*(?:서술|단서|상충|확인|필요|미확인|역추적|재고|시도|기반|주장|"
    r"접근 실패|미발견|보도\)?$)[^—–]*$|"
    r"\s*\((?=[^)]*(?:서술|단서|상충|확인 필요|교차 확인|미확인|역추적|단독|5단계|"
    r"접근 실패|미열람|2차 인용|원문|일치|판|설\b))[^)]*\)\s*$")


def clean_title(t: str) -> str:
    prev = None
    while prev != t:
        prev = t
        t = NOTE_PAT.sub("", t).strip().rstrip(",")
    return t.strip()


# 제목 앞의 사이트명 접두(발행처와 중복)와 뒤의 발행 주체 괄호를 제거해
# "작성 주체, 「제목」, 사이트명" 표기 조립 시 중복이 생기지 않게 한다.
SITE_PREFIX = re.compile(
    r"^(?:우리역사넷|한국민족문화대백과사전|위키백과|나무위키|브런치|경향신문|경기신문|서울신문|"
    r"한국일보|기독타임즈|e-전라매일|흥사단 LA지부 게시판|흥사단 LA지부|흥사단 칼럼|흥사단|"
    r"부산흥사단|대구흥사단|서울흥사단|한인역사박물관|대한인국민회 ?기념재단,?|공훈전자사료관|"
    r"독립운동인명사전\(독립기념관\)|독립기념관 한국독립운동인명사전|독립운동인명사전|"
    r"한국독립운동정보시스템\(독립기념관\) 사전|세계한민족문화대전|디지털구리문화대전|"
    r"디지털강남문화대전|월간 독립기념관,?|국가기록원|국가유산청|성북마을발견\+독립운동 아카이브|"
    r"한국사데이터베이스|Wikipedia\(en\),?|New World Encyclopedia,?|Britannica,?|HMDB,?|"
    r"WikiTree,?|IMDb,?|PBS NewsHour,?|AsAmNews,?|The Korea Herald,?|Hollywood Walk of Fame,?|"
    r"Naval History and Heritage Command,?|국립대한민국임시정부기념관 웹진|지역N문화|"
    r"한국문화정보원 문화인물|국가보훈처 보도자료)\s*")
PUB_PAREN = re.compile(
    r"\s*\((?:[^)]*(?:국사편찬위원회|한국학중앙연구원|독립기념관|국가보훈부|국가보훈처|성북구|"
    r"한국문화정보원|한국독립운동정보시스템|공훈전자사료관|자체 기록|"
    r"USC Libraries / Online Archive)[^)]*)\)\s*$")


def normalize_title(t: str) -> str:
    t = clean_title(t)
    prev = None
    while prev != t:
        prev = t
        t = SITE_PREFIX.sub("", t).strip()
        t = PUB_PAREN.sub("", t).strip().rstrip(",")
    # 전체가 따옴표 한 쌍으로 감싸여 있으면 풀어서 핵심 표제만 남긴다 (렌더링이 「」를 입힌다)
    m = re.fullmatch(r"[「'\"](.+)[」'\"]", t)
    if m and not re.search(r"[「」]", m.group(1)):
        t = m.group(1).strip()
    return t


def main():
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    claims = json.loads(CLAIMS.read_text(encoding="utf-8"))
    WORK_DIR.mkdir(parents=True, exist_ok=True)

    # 0) 기존 발급분 로드 (id 안정성 — 재실행 시 절대 재발급하지 않음)
    existing_keys = {}
    if KEYS_FILE.exists():
        existing_keys = json.loads(KEYS_FILE.read_text(encoding="utf-8"))
    existing_refs = []
    if CITATIONS.exists():
        existing_refs = json.loads(CITATIONS.read_text(encoding="utf-8")).get("refs", [])

    sources = []
    by_id = {}

    # 1) 사료 카탈로그 47건 — id 그대로 승계
    for c in catalog:
        year = None
        m = re.search(r"\b(1[89]\d{2}|20\d{2})\b", c.get("date_created") or "")
        if m:
            year = int(m.group(1))
        author = c.get("author")
        if author:
            author = re.split(r"\s*\(", author)[0].strip() or None
        holder = c.get("holder") or ""
        publisher = re.split(r"\s*\(", holder)[0].strip() or None
        url = c.get("access_url")
        rec = {"id": c["id"], "type": "primary", "author": author,
               "title": c["title"], "publisher": publisher, "year": year,
               "url": url, "accessed": ACCESSED if url else None}
        sources.append(rec)
        by_id[rec["id"]] = rec

    # 1b) 카탈로그 외 신규 사료
    for rec in NEW_PRIMARY:
        sources.append(dict(rec))
        by_id[rec["id"]] = dict(rec)

    # 2) claims + timeline 사건의 출처 전수 순회 — primary는 카탈로그 매핑, 나머지는 그룹화
    #    (작성 단계 마커가 clm-/evt- 식별자를 쓰므로 두 평면 모두 해석 가능해야 한다)
    events = json.loads(TIMELINE.read_text(encoding="utf-8"))["events"]
    entity_sources = [(c["claim_id"], c["sources"]) for c in claims]
    entity_sources += [(e["id"], e.get("sources") or []) for e in events]

    entity_map = defaultdict(list)
    groups = {}          # key -> {"mentions": [...], "order": n}
    unresolved = []
    order = 0
    for eid, src_list in entity_sources:
        for s in src_list:
            if s["type"] == "primary":
                hit = None
                for frag, ids, loc in PRIMARY_MAP:
                    if s["title"].startswith(frag) or frag in s["title"]:
                        hit = (ids, loc)
                        break
                if not hit:
                    unresolved.append((eid, s["title"]))
                    continue
                for sid in hit[0]:
                    entity_map[eid].append(
                        {"source_id": sid, "locator": s.get("locator") or hit[1]})
                continue
            key = canon_key(s)
            if key not in groups:
                groups[key] = {"mentions": [], "order": order}
                order += 1
            groups[key]["mentions"].append((eid, s))

    # 3) 그룹별 id 발급 (기존 키 우선, 신규는 유형별 다음 연번)
    counters = Counter()
    for k, sid in existing_keys.items():
        code = sid.split("-")[1]
        counters[code] = max(counters[code], int(sid.split("-")[2]))

    key_to_id = dict(existing_keys)
    for key, g in sorted(groups.items(), key=lambda kv: kv[1]["order"]):
        mentions = g["mentions"]
        # type 확정: 오버라이드 > 다수결
        typ = TYPE_OVERRIDE.get(key) or Counter(s["type"] for _, s in mentions).most_common(1)[0][0]
        code = TYPE_CODE[typ]
        if key not in key_to_id:
            counters[code] += 1
            key_to_id[key] = f"src-{code}-{counters[code]:03d}"
        sid = key_to_id[key]

        # 서지 필드: 수동 확정 > 도메인 기본값 + 제목 정제
        urls = Counter(s.get("url") for _, s in mentions if s.get("url"))
        url = urls.most_common(1)[0][0] if urls else None
        host = urlparse(url).netloc.lower().replace("www.", "") if url else ""
        d_author, d_site = DOMAIN_BIB.get(host, (None, None))

        cur = CURATED.get(key)
        if cur:
            author, title, publisher, year = cur["author"], cur["title"], cur["publisher"], cur["year"]
        else:
            if typ == "academic":
                # 학술 문헌은 자동 파싱 금지 — CURATED 누락이면 빌드 실패로 강제
                raise SystemExit(f"[FAIL] 학술 그룹 수동 서지 누락: {key}")
            raw = Counter(s["title"] for _, s in mentions).most_common(1)[0][0]
            title = normalize_title(raw)
            author, publisher, year = d_author, d_site, None

        rec = {"id": sid, "type": typ, "author": author, "title": title,
               "publisher": publisher, "year": year,
               "url": url, "accessed": ACCESSED if url else None}
        if sid in by_id:   # 재실행 — 기존 레코드 갱신(같은 키)
            by_id[sid].update(rec)
        else:
            sources.append(rec)
            by_id[sid] = rec

        for eid, s in mentions:
            entity_map[eid].append({"source_id": sid, "locator": s.get("locator")})

    # 3a-2) grade_reason이 인용한 사료 카탈로그 id 보충 매핑 — 검증자가 사료 대조
    #       근거를 grade_reason에만 적은 33건(소재 미확인 메타 주장 등) 커버.
    for c in claims:
        cited = set(re.findall(r"src-pri-\d{3}", c.get("grade_reason", "")))
        mapped = {m["source_id"] for m in entity_map.get(c["claim_id"], [])}
        for sid in sorted(cited - mapped):
            if sid in by_id:
                entity_map[c["claim_id"]].append(
                    {"source_id": sid, "locator": "사료 카탈로그 참조(grade_reason)"})

    # 3a-3) 같은 출처 중복 표기 정리 — entity당 source_id 1회(첫 locator 유지)
    for eid, lst in entity_map.items():
        seen, ded = set(), []
        for m in lst:
            if m["source_id"] in seen:
                continue
            seen.add(m["source_id"])
            ded.append(m)
        entity_map[eid] = ded

    # 3b) conflicts.md 헤더에서 cfl -> 관련 evt 인덱스 (cfl 마커 해석 보조)
    cfl_map = {}
    for line in CONFLICTS.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^### (cfl-\d+)\s*\|", line)
        if m:
            cfl_map[m.group(1)] = re.findall(r"evt-[a-z]+-\d+", line)

    # 3c) 병합 전 사건 id 별칭 — timeline 통합(merged_from) 이전 id로 들어오는
    #     마커·cfl 참조를 최종 사건의 출처로 해석한다.
    #     단, 기계 별칭이 본문 의미와 인접 사건으로 어긋나는 위험 케이스 2건은 제외
    #     (team-lead 검증 2026-06-06, synthesis life.md §14 — normalize_markers.py
    #      AMBIGUOUS_ALIAS와 동일 목록): 자동 별칭 등재 금지, 의미 판별로만 처리.
    ambiguous = {"evt-chrono-093", "evt-chrono-094"}
    for e in events:
        for old in (e.get("merged_from") or []):
            if old in ambiguous:
                continue
            if old not in entity_map and e["id"] in entity_map:
                entity_map[old] = entity_map[e["id"]]

    # 4) 산출
    claim_map = {k: v for k, v in sorted(entity_map.items()) if k.startswith("clm-")}
    evt_map = {k: v for k, v in sorted(entity_map.items()) if k.startswith("evt-")}
    sources.sort(key=lambda r: (r["id"].split("-")[1], int(r["id"].split("-")[2])))
    CITATIONS.write_text(
        json.dumps({"refs": existing_refs, "sources": sources}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    KEYS_FILE.write_text(json.dumps(key_to_id, ensure_ascii=False, indent=2), encoding="utf-8")
    MAP_FILE.write_text(json.dumps(claim_map, ensure_ascii=False, indent=2), encoding="utf-8")
    EVT_MAP_FILE.write_text(json.dumps(evt_map, ensure_ascii=False, indent=2), encoding="utf-8")
    CFL_MAP_FILE.write_text(json.dumps(cfl_map, ensure_ascii=False, indent=2), encoding="utf-8")

    tcount = Counter(r["type"] for r in sources)
    print(f"sources {len(sources)}건  ({dict(tcount)})")
    print(f"claims 매핑 {len(claim_map)}건 / {len(claims)}건")
    print(f"events 매핑 {len(evt_map)}건 / {len(events)}건 | cfl 인덱스 {len(cfl_map)}건")
    no_acc = [r["id"] for r in sources if r["url"] and not r["accessed"]]
    no_url_no_pub = [r["id"] for r in sources if not r["url"] and not r["publisher"]]
    print(f"url 있고 accessed 없음: {len(no_acc)}건 {no_acc}")
    print(f"url·소장처 모두 없음: {len(no_url_no_pub)}건 {no_url_no_pub}")
    if unresolved:
        print(f"[UNRESOLVED] primary 매핑 실패 {len(unresolved)}건:")
        for eid, t in unresolved:
            print("  -", eid, t[:80])
        sys.exit(1)
    # 미매핑 claim/event 검출
    missing = [c["claim_id"] for c in claims if c["claim_id"] not in claim_map]
    if missing:
        print(f"[WARN] 출처 매핑 0건인 claim: {missing}")
    missing_e = [e["id"] for e in events if e["id"] not in evt_map]
    if missing_e:
        print(f"[WARN] 출처 매핑 0건인 event {len(missing_e)}건: {missing_e[:10]}…")


if __name__ == "__main__":
    main()
