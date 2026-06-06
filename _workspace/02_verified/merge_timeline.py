#!/usr/bin/env python3
"""timeline.json 병합 스크립트 (timeline-analyst).

6개 연구원 events.json(263건)을 병합한다.
- 골격(chronology) ↔ 상세 레코드 중복: 상세 레코드 우선, 골격 id를 merged_from에 보존 (정보 손실 금지 — 골격 detail을 병합 주석으로 보존).
- philosophy 주제 레코드가 시기 연구원 레코드와 동일 사건일 때: 시기 레코드를 canonical로, phil id를 merged_from에 보존.
- 해소 불가 상충: disputed=true + dispute(adopted/variants) 구조 — cross-validator 채택 권고 대기.
- 날짜 정밀화/시공간 보정: 출처 근거가 있는 경우에만, 보정 사유를 detail에 기록.
"""
import json, copy
from datetime import date

BASE = "/Users/robin/Downloads/DOSAN/_workspace/01_research/"
OUT = "/Users/robin/Downloads/DOSAN/_workspace/02_verified/timeline.json"
SOURCE_FILES = [
    "chronology_events.json", "early-life_events.json", "america_events.json",
    "shinminhoe_events.json", "provisional-gov_events.json",
    "heungsadan_events.json", "philosophy_events.json",
    # 보완 라운드 증분 (2026-06-06, evt-chrono-101~110 — 관계망 D 강등 엣지 근거 사건)
    "chronology_events_supplement.json",
]

events = {}
for f in SOURCE_FILES:
    for e in json.load(open(BASE + f)):
        assert e["id"] not in events, f"입력 id 중복: {e['id']}"
        events[e["id"]] = e
INPUT_IDS = set(events)
assert len(INPUT_IDS) == 273, f"입력 사건 수 273(263+보완 10) != {len(INPUT_IDS)}"

# ---------------------------------------------------------------
# 1. 병합 결정 테이블: merged_id -> canonical_id
#    (골격→상세 93건 + phil→시기 9건 = 102건)
# ---------------------------------------------------------------
MERGE = {
    # --- chronology -> early-life ---
    "evt-chrono-001": "evt-early-001", "evt-chrono-002": "evt-early-005",
    "evt-chrono-003": "evt-early-006", "evt-chrono-004": "evt-early-008",
    "evt-chrono-005": "evt-early-009", "evt-chrono-006": "evt-early-010",
    "evt-chrono-007": "evt-early-012", "evt-chrono-008": "evt-early-013",
    "evt-chrono-009": "evt-early-014", "evt-chrono-010": "evt-early-016",
    "evt-chrono-011": "evt-early-017", "evt-chrono-012": "evt-early-018",
    "evt-chrono-013": "evt-early-019", "evt-chrono-014": "evt-early-020",
    "evt-chrono-015": "evt-early-022",
    # --- chronology -> america ---
    "evt-chrono-016": "evt-amer-001", "evt-chrono-017": "evt-amer-002",
    "evt-chrono-018": "evt-amer-003", "evt-chrono-019": "evt-amer-005",
    "evt-chrono-020": "evt-amer-006", "evt-chrono-021": "evt-amer-030",
    "evt-chrono-022": "evt-amer-010", "evt-chrono-023": "evt-amer-011",
    "evt-chrono-041": "evt-amer-016", "evt-chrono-044": "evt-amer-018",
    "evt-chrono-046": "evt-amer-020", "evt-chrono-049": "evt-amer-022",
    "evt-chrono-050": "evt-amer-023", "evt-chrono-051": "evt-amer-024",
    "evt-chrono-052": "evt-amer-024", "evt-chrono-072": "evt-amer-025",
    "evt-chrono-073": "evt-amer-025", "evt-chrono-074": "evt-amer-026",
    "evt-chrono-077": "evt-amer-027",
    # --- chronology -> shinminhoe ---
    "evt-chrono-024": "evt-shin-001", "evt-chrono-025": "evt-shin-003",
    "evt-chrono-026": "evt-shin-004", "evt-chrono-027": "evt-shin-005",
    "evt-chrono-028": "evt-shin-006", "evt-chrono-029": "evt-shin-012",
    "evt-chrono-030": "evt-shin-010", "evt-chrono-031": "evt-shin-011",
    "evt-chrono-032": "evt-shin-013", "evt-chrono-033": "evt-shin-014",
    "evt-chrono-034": "evt-shin-015", "evt-chrono-035": "evt-shin-019",
    "evt-chrono-036": "evt-shin-021", "evt-chrono-037": "evt-shin-023",
    "evt-chrono-038": "evt-shin-025", "evt-chrono-039": "evt-shin-027",
    "evt-chrono-040": "evt-shin-028", "evt-chrono-042": "evt-shin-029",
    # --- chronology -> provisional-gov ---
    "evt-chrono-053": "evt-provgov-001", "evt-chrono-054": "evt-provgov-003",
    "evt-chrono-055": "evt-provgov-002", "evt-chrono-056": "evt-provgov-004",
    "evt-chrono-057": "evt-provgov-005", "evt-chrono-058": "evt-provgov-006",
    "evt-chrono-059": "evt-provgov-008", "evt-chrono-060": "evt-provgov-010",
    "evt-chrono-061": "evt-provgov-012", "evt-chrono-064": "evt-provgov-013",
    "evt-chrono-065": "evt-provgov-014", "evt-chrono-067": "evt-provgov-015",
    "evt-chrono-068": "evt-provgov-016", "evt-chrono-069": "evt-provgov-018",
    "evt-chrono-070": "evt-provgov-020", "evt-chrono-078": "evt-provgov-021",
    "evt-chrono-080": "evt-provgov-022", "evt-chrono-082": "evt-provgov-024",
    "evt-chrono-083": "evt-provgov-025", "evt-chrono-086": "evt-provgov-026",
    "evt-chrono-087": "evt-provgov-028", "evt-chrono-088": "evt-provgov-029",
    # --- chronology -> heungsadan ---
    "evt-chrono-045": "evt-hsd-001", "evt-chrono-063": "evt-hsd-004",
    "evt-chrono-066": "evt-hsd-006", "evt-chrono-075": "evt-hsd-008",
    "evt-chrono-079": "evt-hsd-009", "evt-chrono-085": "evt-hsd-010",
    "evt-chrono-089": "evt-hsd-011", "evt-chrono-090": "evt-hsd-014",
    "evt-chrono-091": "evt-hsd-015", "evt-chrono-092": "evt-hsd-016",
    "evt-chrono-093": "evt-hsd-018", "evt-chrono-094": "evt-hsd-020",
    "evt-chrono-095": "evt-hsd-021", "evt-chrono-096": "evt-hsd-022",
    "evt-chrono-097": "evt-hsd-023", "evt-chrono-098": "evt-hsd-025",
    "evt-chrono-099": "evt-hsd-028", "evt-chrono-100": "evt-hsd-029",
    # --- chronology -> philosophy ---
    "evt-chrono-071": "evt-phil-009",
    # --- 보완 라운드 증분: 북미실업주식회사는 evt-amer-017과 동일 사건 (amer가 발기인 10인 전원 보유) ---
    "evt-chrono-101": "evt-amer-017",
    # --- philosophy -> 시기 연구원 (동일 사건의 사상 측면) ---
    "evt-phil-001": "evt-early-016", "evt-phil-002": "evt-early-019",
    "evt-phil-003": "evt-shin-007", "evt-phil-004": "evt-shin-012",
    "evt-phil-005": "evt-shin-013", "evt-phil-006": "evt-hsd-001",
    "evt-phil-008": "evt-provgov-012", "evt-phil-011": "evt-provgov-022",
    "evt-phil-012": "evt-provgov-026",
}
# 골격에서 유지되는 7건: chrono-043/047/048/062/076/081/084 (자녀 출생 4·도산일기·길림행·필리핀)

# ---------------------------------------------------------------
# 2. 날짜 채택 예외 (canonical 날짜 대신 병합 레코드의 더 정밀한 출처 날짜 채택)
# ---------------------------------------------------------------
DATE_OVERRIDE = {
    # 출생: 원본 음력 1878-10-06 → 양력 환산 1878-11-09 (chrono-001의 역법 판정 채택)
    "evt-early-001": (
        {"start": "1878-11-09", "end": "1878-11-09", "precision": "day", "calendar": "lunar"},
        "〔역법〕 원본 기록은 음력 1878년 10월 6일(흥사단 연보·한인역사박물관 병기) — start는 양력 환산값 1878-11-09, calendar는 원본 역법(lunar). 골격 evt-chrono-001의 판정 채택."),
    # 청일전쟁 목격: 전투일(1894-09-15) 기준 day 정밀도 채택 (chrono-004 전사 기록 기준)
    "evt-early-008": (
        {"start": "1894-09-15", "end": None, "precision": "day", "calendar": "solar"},
        "〔정밀화〕 평양전투 일자(1894-09-15)는 전사 기록 기준(evt-chrono-004 출처) — 목격 자체는 회고 기반이므로 일자는 전투일에 의존."),
    # 상항친목회: 우리역사넷 1903-09-23 day 채택 (chrono-019 출처)
    "evt-amer-005": (
        {"start": "1903-09-23", "end": None, "precision": "day", "calendar": "solar"},
        "〔정밀화〕 우리역사넷은 1903년 9월 23일 조직·회장 선출로 기록(evt-chrono-019 출처) — day 정밀도 채택."),
}

# ---------------------------------------------------------------
# 3. 정규화 보정 (시공간 정합·스키마 보정 — 사유 필수 기록)
# ---------------------------------------------------------------
NORMALIZE = {
    # range인데 end 누락 → 은거 시작(1935년 중) 이전까지로 범위 보정
    "evt-hsd-017": (
        {"start": "1935-02-10", "end": "1935-12-31", "precision": "range", "calendar": "solar"},
        "〔보정〕 원 레코드는 range인데 end 누락 — 순회 종료 시점 미확인이므로 송태산장 은거 시작 추정 구간(1935년 중)을 상한으로 1935-12-31까지 범위 표기."),
    # 은거 시작이 가출옥(1935-02-10) 이전으로 표기됨 → 자체 detail("가출옥 후")과 모순, 시작을 가출옥일로 보정
    "evt-hsd-018": (
        {"start": "1935-02-10", "end": "1937-06-28", "precision": "range", "calendar": "solar"},
        "〔보정〕 원 range 시작(1935-01-01)은 가출옥일(1935-02-10, evt-hsd-016) 이전 — 레코드 자체 서술('가출옥 후 지방 순회를 마친 1935년부터')과 모순되어 시작을 가출옥일로 보정. 정밀 시점은 미확인(1935년 중)."),
    # 미주 고별 range 종료(2-28)가 SF 출항(1907-01-20, evt-shin-002) 이후까지 이어짐 → 출항일로 보정
    "evt-amer-012": (
        {"start": "1907-01-01", "end": "1907-01-20", "precision": "range", "calendar": "solar"},
        "〔보정〕 원 range 종료(1907-02-28)는 샌프란시스코 출항(1907-01-20, evt-shin-002) 이후까지 미주 체류가 이어지는 시공간 모순 — 종료를 출항일로 보정. 원 표기는 인명사전 '1907년 2월 귀국'의 역산이었음."),
}

# ---------------------------------------------------------------
# 4. disputed (해소 불가 상충 — 양설 병기, cross-validator 채택 권고 대기)
# ---------------------------------------------------------------
DISPUTES = {
    "evt-early-016": {  # 쾌재정 연설
        "date": {"start": "1898-01-01", "end": "1898-12-31", "precision": "year", "calendar": "solar"},
        "note": "연설 연도(1897 vs 1898)와 일자(만수성절 음력 7-25 전승)가 상충 — 잠정 1898년(연 단위, 기관 사료 기준) 채택. 원 레코드의 음력 7-25 day 표기는 전승 의존이므로 변형(variants)으로 강등. cross-validator 권고 대기.",
        "adopted": {"start": "1898-01-01", "end": "1898-12-31", "precision": "year",
                    "basis": "독립운동인명사전 등 기관 사료의 1898년 — 조민희 평남 관찰사 재임(1897.9~1899.2)과 정합"},
        "variants": [
            {"claim": "1898년 연중(일자 미상)", "source": "독립운동인명사전·위키백과", "assessment": "기관 기준 — 잠정 채택"},
            {"claim": "만수성절(음력 7월 25일) 개최 전승 — 1898년이면 양력 1898-09-10(만세력 환산)", "source": "흥사단 칼럼·이광수 전기 계열(전승)", "assessment": "일자 특정은 전승 의존"},
            {"claim": "1897년 음력 7월 25일(만 18세)", "source": "안도산전서·김삼웅 평전 인용 칼럼", "assessment": "조민희 관찰사 임명(1897.9) 이전이어서 시공간 부정합"},
        ]},
    "evt-shin-021": {  # 청도회의
        "date": {"start": "1910-08-01", "end": "1910-09-30", "precision": "range", "calendar": "solar"},
        "note": "개최 시점 3설 상충(1910-04 / 1910 늦여름~9월 / 1911 이른봄). 4월설은 본인 이동 일정(4-7 행주 출발 evt-shin-019, 5월 웨이하이웨이 도착 evt-shin-020)과 시공간 모순이어서 잠정 채택 범위는 1910-08~09(골격 evt-chrono-036과 일치). cross-validator 권고 대기.",
        "adopted": {"start": "1910-08-01", "end": "1910-09-30", "precision": "range",
                    "basis": "시공간 정합성 검사 — 4월 개최는 망명 이동 일정과 모순, 8~9월설이 정합"},
        "variants": [
            {"claim": "1910년 4월 개최", "source": "우리역사넷 신민회 항목", "assessment": "행주 출발(4-7)·웨이하이웨이 도착(5월)과 모순 — 시공간 검사 기각"},
            {"claim": "1910년 늦여름~9월 개최", "source": "위키백과 신채호 계열 서술", "assessment": "이동 일정과 정합 — 잠정 채택"},
            {"claim": "1911년 이른 봄 방책 논의", "source": "독립운동인명사전 이종호 항목", "assessment": "이종호 개인의 합류 시점일 가능성 — 회의 본체와 구분 필요"},
        ]},
    "evt-hsd-011": {  # 국내 압송
        "date": None,
        "note": "압송 일자 상충 — 6월 2일설(잠정 채택)과 6월 7일 인천 도착설 병존. 6-2는 경기도경찰부 신문 개시일(evt-hsd-012)과 정합. 6-7 도착설은 6-2를 상하이 출발일로 해석하면 양립 가능하나 신문 개시일과 충돌. cross-validator 권고 대기.",
        "adopted": {"start": "1932-06-02", "end": "1932-06-02", "precision": "day",
                    "basis": "경기도경찰부 신문 개시(evt-hsd-012, 6-2)와 정합"},
        "variants": [
            {"claim": "1932-06-02 압송(경성 도착)", "source": "흥사단·기관 기록 계열", "assessment": "잠정 채택"},
            {"claim": "1932-06-07 인천 도착", "source": "일부 문헌(골격 evt-chrono-089 detail)", "assessment": "6-2 출발설로 해석 시 양립 가능하나 신문 개시일(6-2)과 충돌"},
        ]},
    "evt-hsd-025": {  # 망우리 안장
        "date": None,
        "note": "안장 일자 상충 — 3월 10일(디지털구리문화대전) vs 3월 12일(통용 문헌), 기관·학술 출처 미확인. 월 범위 표기 유지. cross-validator 권고 대기.",
        "adopted": {"start": "1938-03-10", "end": "1938-03-31", "precision": "range",
                    "basis": "일자 미확정 — 범위 보존"},
        "variants": [
            {"claim": "1938-03-10 안장", "source": "디지털구리문화대전", "assessment": "순국 당일 안장은 장례 통제 정황상 검토 필요"},
            {"claim": "1938-03-12 안장", "source": "통용 문헌(골격 evt-chrono-098 detail)", "assessment": "통설"},
        ]},
    "evt-amer-023": {  # 파리강화회의 대표 선출 전체회의
        "date": None,
        "note": "전체회의 시점 상충 — 1918년 11월(우리역사넷·대한인국민회기념재단 50년사, 잠정 채택) vs 1918-12-01 소집(독립운동인명사전, 골격 evt-chrono-050). cross-validator 권고 대기.",
        "adopted": {"start": "1918-11-01", "end": "1918-11-30", "precision": "month",
                    "basis": "독립 출처 2개(우리역사넷·국민회 50년사) 일치"},
        "variants": [
            {"claim": "1918년 11월 전체회의 소집·대표 3인 선출", "source": "우리역사넷·대한인국민회기념재단 50년사", "assessment": "잠정 채택"},
            {"claim": "1918-12-01 재미한인전체대표자회의 소집", "source": "독립운동인명사전", "assessment": "11월 소집 결정·12월 개최로 양립 가능성 — 검증 필요"},
        ]},
    "evt-hsd-015": {  # 대전형무소 이감
        "date": None,
        "note": "이감 시점 상충 — 1933-02(독립운동인명사전) vs 1933-03(일부 문헌) vs 1933-06-01 이전(대전발 서한 역산, 위키백과 계열). 월 미확정으로 연 단위 보존. cross-validator 권고 대기.",
        "adopted": {"start": "1933-01-01", "end": "1933-12-31", "precision": "year",
                    "basis": "월 미확정 — 연 단위 보존"},
        "variants": [
            {"claim": "1933년 2월 이감", "source": "독립운동인명사전", "assessment": "기관 출처 — 채택 후보"},
            {"claim": "1933년 3월 이감", "source": "일부 문헌(골격 evt-chrono-091 detail)", "assessment": "출전 추적 필요"},
            {"claim": "1933-06-01 이전(대전발 서한 존재)", "source": "위키백과 계열", "assessment": "하한 제약으로만 유효"},
        ]},
    "evt-shin-001": {  # 신민회 미주 구상 vs 결성
        "date": None,
        "note": "사건 성격 상충 — 리버사이드에서의 '구상·취지서 작성'(한국민족문화대백과, 잠정 채택) vs '대한인신민회 결성'(독립운동인명사전, 골격 evt-chrono-024). cross-validator 권고 대기.",
        "adopted": {"start": "1906-11-01", "end": "1907-01-19", "precision": "range",
                    "basis": "한국민족문화대백과 — 구상·초안 작성 후 귀국 서술"},
        "variants": [
            {"claim": "1906 말~1907 초 신민회 구상·취지서/장정 초안 작성", "source": "한국민족문화대백과", "assessment": "잠정 채택"},
            {"claim": "1907년 1월 리버사이드 대한인신민회 결성", "source": "독립운동인명사전", "assessment": "미주 조직 결성설 — 국내 신민회(evt-shin-005)와의 관계 검증 필요"},
        ]},
    "evt-shin-008": {  # 이토 히로부미 면담
        "date": None,
        "note": "면담의 시점(1907 연중)과 실재 여부가 출처 간 상충(레코드 detail 참조) — chronology 골격 미등재 인계 사항. 연 단위 보존. cross-validator 권고 대기.",
        "adopted": {"start": "1907-01-01", "end": "1907-12-31", "precision": "year",
                    "basis": "연대·진위 미확정 — 연 단위 보존"},
        "variants": [
            {"claim": "1907년 중 면담('안창호 내각' 제안설의 전사)", "source": "shin 레코드 detail의 출처 계열", "assessment": "전기류·후대 서술 의존"},
            {"claim": "면담 진위·시점 불확정", "source": "출처 상충 — detail 참조", "assessment": "1차 사료 미확인"},
        ]},
    "evt-amer-018": {  # 1912 중앙총회 결성 — '초대 중앙총회장' 인물 상충 (날짜 아닌 사실 상충)
        "date": None,
        "note": "1912년 중앙총회장 인물 상충 — 신편한국사(사료 기반)는 1912-11-08 선거에서 윤병구 당선·안창호 낙선을 명시, 통설(독립기념관 인명사전·흥사단·기념사업회)은 안창호를 1912년 선출 회장으로 표기. 채택: 윤병구 당선(출처 위계 상위). 안창호의 중앙총회장 당선은 1914-11(evt-amer-020)로 분리 등재 — 통설은 1912 결성 주도와 1914 당선의 압축 오류 개연성(cfl-012). 골격 evt-chrono-044의 구 제목 표기는 병합으로 폐기되었고, 해당 칭호 표현은 전 필드 사용 금지(디렉터 §4·cross-validator 지시).",
        "adopted": {"claim": "1912-11-08 제1차 대표원의회에서 중앙총회장 윤병구 당선 — 안창호는 만주 지방총회 대표 대리로 참가, 낙선",
                    "basis": "국사편찬위 신편한국사·우리역사넷 — 사료 기반 서술, 출처 위계 상위"},
        "variants": [
            {"claim": "1912-11-08 대표원의회에서 중앙총회장 윤병구·부회장 황사용 선임", "source": "국사편찬위 신편한국사·우리역사넷·국민회 50년사(독립 지지)", "assessment": "채택 확정(cfl-012)"},
            {"claim": "안창호가 1912년 11월 중앙총회장으로 선출되었다는 통설 표기", "source": "독립기념관 인명사전·흥사단·기념사업회 자료", "assessment": "1912 결성 주도와 1914 당선(evt-amer-020)의 영웅 서사 압축 오류 개연성 — 열세 판정(cfl-012)"},
        ]},
    "evt-shin-015": {  # 석방 — 구금 기간 상충
        "date": None,
        "note": "용산 헌병대 구금 해제 시점·구금 기간이 출처 간 상충(레코드 detail 참조) — 범위 보존. cross-validator 권고 대기.",
        "adopted": {"start": "1909-12-01", "end": "1910-02-28", "precision": "range",
                    "basis": "상충 범위 전체 보존"},
        "variants": [
            {"claim": "1909년 12월경 석방(약 2개월 구금)", "source": "shin 레코드 detail의 출처 계열", "assessment": "검증 필요"},
            {"claim": "1910년 2월경 석방(약 3개월+ 구금)", "source": "골격 evt-chrono-034(독립운동인명사전 계열)", "assessment": "검증 필요"},
        ]},
}

# ---------------------------------------------------------------
# 5. 교차 참조·연관 주석 (분리 유지된 사건 간 안내)
# ---------------------------------------------------------------
XNOTES = {
    "evt-early-006": "〔연관〕 골격 evt-chrono-003은 서당 수학과 필대은 교유를 묶어 등재 — 필대은 교유는 evt-early-007로 분리.",
    "evt-early-010": "〔연관〕 골격 evt-chrono-006은 입학과 기독교 입교를 묶어 등재 — 입교는 evt-early-011로 분리(early 조사는 1896년 입교).",
    "evt-early-014": "〔연관〕 골격 evt-chrono-009는 가입과 관서지부 활동을 묶어 등재 — 관서지부 설립은 evt-early-015로 분리.",
    "evt-early-020": "〔연관〕 골격 evt-chrono-014는 교회 건립과 매축(개간) 사업을 묶어 등재 — 개간 사업은 evt-early-021로 분리.",
    "evt-shin-019": "〔연관〕 골격 evt-chrono-035는 망명 출발과 거국가를 묶어 등재 — 거국가 작사는 evt-shin-018로 분리.",
    "evt-shin-027": "〔연관〕 골격 evt-chrono-039는 시베리아 횡단~도미 여정 전체를 등재 — 횡단열차 승차는 evt-shin-026, 뉴욕 도착은 evt-shin-028로 분리.",
    "evt-shin-028": "〔날짜〕 골격 evt-chrono-040은 도착일을 1911-09-03으로 표기 — 본 레코드의 range(09-02~03)에 포함되어 보존.",
    "evt-shin-029": "〔연관〕 골격 evt-chrono-042는 105인 사건 전체(와해까지)를 등재 — 1심은 evt-shin-030, 항소·상고심은 evt-shin-031, 사면·와해 확정은 evt-shin-032로 분리.",
    "evt-amer-020": "〔연관〕 골격 evt-chrono-046은 재선과 취임을 묶어 등재 — 취임식(1915-06-23)은 evt-amer-021로 분리.",
    "evt-amer-024": "〔연관〕 골격의 day 사건 2건을 병합 보존 — 3·1소식 국민회 긴급협의회 연설 1919-03-13(evt-chrono-051, 독립운동인명사전), 중국 특파 결정 1919-03-24(evt-chrono-052, 동 사전. 단 본 레코드는 3-24 결의설 1차 미확인으로 기록).",
    "evt-provgov-010": "〔연관〕 골격 evt-chrono-060은 통합 임정 출범과 노동국총판을 묶어 등재 — 노동국총판 선임은 evt-provgov-011로 분리.",
    "evt-provgov-021": "〔연관〕 골격 evt-chrono-077(미주 출발)·evt-chrono-078(상하이 복귀)을 병합 — 미주 측 고별·출발 결정 국면은 evt-amer-027로 분리.",
    "evt-hsd-001": "〔연관〕 약법 제정·4대 정신은 evt-hsd-002, 입단문답 제도는 evt-hsd-003으로 분리.",
    "evt-hsd-016": "〔이설〕 한국독립운동정보시스템(i815)의 '1933-02-10 가출옥' 표기는 골격 조사에서 오기로 판정(통설 1935-02-10 채택, evt-chrono-092 detail) — 이설로 병기.",
    "evt-hsd-018": "〔연관〕 가출옥 후 치료·지방 순회는 evt-hsd-017로 분리. 골격 evt-chrono-093은 순회와 은거를 묶어 등재.",
    "evt-hsd-021": "〔연관〕 송치 전 종로경찰서 구금 경위는 evt-hsd-020(1937-06-28~11-01) 참조 — 골격 evt-chrono-095의 '8월 예심종결·수감' 서술(독립운동인명사전)은 병합 보존.",
}

# ---------------------------------------------------------------
# 6. 자녀 출생 레코드 정밀화 (amer 가족 생애 레코드의 출처 차용 — 차용원 명시)
# ---------------------------------------------------------------
BIRTH_ENRICH = {
    # (대상 골격 id, 날짜, 정밀도, 차용원 id, 주석)
    "evt-chrono-043": ("1912-07-05", "day", "evt-amer-032",
        "〔정밀화〕 출생일 1912-07-05는 america 조사(evt-amer-032)의 출처에 따름(원 골격은 연 단위)."),
    "evt-chrono-047": ("1915-01-16", "day", "evt-amer-033",
        "〔정밀화〕 출생일 1915-01-16은 america 조사(evt-amer-033)의 출처에 따름(원 골격은 연 단위)."),
    "evt-chrono-076": ("1926-09-28", "day", "evt-amer-035",
        "〔정밀화〕 출생일 1926-09-28은 america 조사(evt-amer-035)의 출처에 따름(원 골격은 연 단위)."),
    # 안수라: amer-034가 D등급이므로 일자 정밀화 보류 — 주석만
    "evt-chrono-048": (None, None, "evt-amer-034",
        "〔보류〕 america 조사(evt-amer-034, D등급)는 출생일을 1917-05-27로 기록 — 등급 미달로 일자 정밀화 보류, 연 단위 유지."),
}

# ---------------------------------------------------------------
# 병합 실행
# ---------------------------------------------------------------
merged = {}
for eid, e in events.items():
    if eid in MERGE:
        continue
    rec = copy.deepcopy(e)
    rec["merged_from"] = []
    rec["disputed"] = False
    rec["dispute_note"] = None
    merged[eid] = rec

def union_list(a, b):
    return a + [x for x in b if x not in a]

def union_sources(a, b):
    seen = {(s.get("title"), s.get("url")) for s in a}
    out = list(a)
    for s in b:
        if (s.get("title"), s.get("url")) not in seen:
            out.append(s); seen.add((s.get("title"), s.get("url")))
    return out

for src_id, dst_id in MERGE.items():
    assert dst_id in merged, f"canonical 부재: {dst_id} (<- {src_id})"
    src, dst = events[src_id], merged[dst_id]
    dst["merged_from"].append(src_id)
    dst["actors"] = union_list(dst["actors"], src["actors"])
    dst["orgs"] = union_list(dst.get("orgs", []), src.get("orgs", []))
    dst["tags"] = union_list(dst.get("tags", []), src.get("tags", []))
    dst["sources"] = union_sources(dst["sources"], src["sources"])
    if src.get("detail"):
        dst["detail"] = (dst.get("detail") or "") + f"\n\n〔병합 {src_id}: {src['title']}〕 {src['detail']}"

# 날짜 채택 예외 적용
for eid, (d, note) in DATE_OVERRIDE.items():
    merged[eid]["date"] = d
    merged[eid]["detail"] += "\n\n" + note

# 정규화 보정 적용
for eid, (d, note) in NORMALIZE.items():
    merged[eid]["date"] = d
    merged[eid]["detail"] += "\n\n" + note

# disputed 적용
for eid, dis in DISPUTES.items():
    rec = merged[eid]
    rec["disputed"] = True
    rec["dispute_note"] = dis["note"]
    rec["dispute"] = {"status": "pending_cross_validator",
                      "adopted": dis["adopted"], "variants": dis["variants"]}
    if dis["date"]:
        rec["date"] = dis["date"]

# 교차 참조 주석
for eid, note in XNOTES.items():
    merged[eid]["detail"] += "\n\n" + note

# 자녀 출생 정밀화
for eid, (start, prec, borrow_id, note) in BIRTH_ENRICH.items():
    rec = merged[eid]
    if start:
        rec["date"] = {"start": start, "end": start, "precision": prec, "calendar": "solar"}
        rec["sources"] = union_sources(rec["sources"], events[borrow_id]["sources"])
    rec["detail"] += "\n\n" + note

# ---------------------------------------------------------------
# 7. cross-validator 채택 권고 반영 (conflicts.md v1.1, 2026-06-06 수신)
#    위 1~6절은 권고 수신 전 잠정판의 감사 추적으로 보존 — 본 절이 이를 덮어쓴다.
#    형식: (a) 통설 채택 → disputed=False + dispute.status=adopted, 이설 보존
#          (b) 양론 병기 → disputed=True + variants
#          (c) 재분류    → 레코드 분리/양립 주석
# ---------------------------------------------------------------
def adjudicate(eid, note, date=None, disputed=None, status=None, adopted=None, variants=None, place_name=None):
    rec = merged[eid]
    rec["detail"] += "\n\n" + note
    if date:
        rec["date"] = date
    if place_name:
        rec["place"]["name"] = place_name
    if disputed is not None:
        rec["disputed"] = disputed
        rec["dispute_note"] = note
        d = rec.get("dispute") or {}
        if status:
            d["status"] = status
        if adopted:
            d["adopted"] = adopted
        if variants:
            d["variants"] = variants
        rec["dispute"] = d
        if not disputed and not d.get("status"):
            d["status"] = "adopted"

# --- A형 (a) 채택·주석 ---
adjudicate("evt-early-005", "〔판정 cfl-002·036〕 이사 연도 1886 채택(잠정) — 위키 1892설은 별도 연보 계통 개연성으로 보존(cfl-001 해소 시 재검). 면 명칭은 남곶면 잠정 채택 — 남부산면(흥사단 연보·위키)은 행정구역 변천 가능성과 함께 병기.")
adjudicate("evt-early-013", "〔판정 cfl-005〕 약혼 연도 1896 잠정 채택(기관 우위) — 1897설(민백 「이혜련」) 병기.",
           date={"start": "1896-01-01", "end": "1896-12-31", "precision": "year", "calendar": "solar"})
adjudicate("evt-early-014", "〔판정 cfl-006〕 가입 연도 1897 채택 — 1898설(국민회기념재단 약전)은 관서지부 발기(1898)와의 압축 서술 개연성으로 보존.")
adjudicate("evt-early-019", "〔판정 cfl-038〕 소재 리 '암화리' 잠정 채택(기관+직접 열람) — 민백 「안창호」의 '화암리'는 글자 전도 오기 개연성 병기. 일제강점기 지형도로 확정 가능.")
adjudicate("evt-early-022", "〔판정 cfl-008〕 출국일 1902-09-04 채택 — 위키 11-04설은 SF 도착(10-14)과의 시공간 모순으로 기각·보존.")
adjudicate("evt-amer-001", "〔판정 cfl-008·040〕 출국일 09-04 채택(11-04설 시공간 모순 기각). 호 '도산' 유래는 미해소 양설 병기 확정 — 항해 중 하와이 작명설(전기류)과 고향 도롱섬 유래설(한글 일부) 모두 1~3단계 출처 미확인 전승.")
adjudicate("evt-amer-005", "〔판정 cfl-009〕 기관 출처는 월 단위까지만 보장 — month(1903-09) 유지, 23일설은 〔단체 연보 단독〕 표기로 병기. 직전 병합의 day 정밀화(09-23)는 본 판정으로 철회. 신한민보·공립신보 회고 기사 발굴 시 승격 가능.",
           date={"start": "1903-09-01", "end": "1903-09-30", "precision": "month", "calendar": "solar"})
adjudicate("evt-amer-011", "〔판정 cfl-011〕 창간일 1905-11-22 채택(독립 2출처+신문사 표준 서술) — 11-20설(우리역사넷) 보존. 창간호 원지면(src-pri-011) 대조 시 최종 확정.")
adjudicate("evt-shin-004", "〔판정 cfl-014〕 1907-02-20 서울 도착 채택(기관 2 독립) — 민백 '을사조약 이듬해(1906)'설은 지시 오류 개연성으로 보존.")
adjudicate("evt-shin-010", "〔판정 cfl-021〕 1908-05 채택 — 1905설(나무위키 단독) 기각 권고·보존.")
adjudicate("evt-shin-029", "〔판정 cfl-018〕 검거 개시 1911-10-24 채택(선천 신성중학교 27명 체포) — 민백 '9월 시작'설은 선행 검거 포함 광의 서술 개연성으로 보존. 규모는 '600~700여 명' range 병기, 기소 인원(122/123)은 미해소 — 판결문 전사(src-pri-016) 대조 대기(조건부).",
           date={"start": "1911-10-24", "end": "1911-12-31", "precision": "range", "calendar": "solar"})
adjudicate("evt-shin-031", "〔판정 cfl-019·041〕 항소심=경성복심법원 채택 — 1912-11-26~1913-03-20 52회 공판, 99인 무죄·6인 유죄, 1913-10 상고 종결(10-09 종결설). 민백 '대구복심 1913-07-15'설은 환송 절차와의 압축 혼합 개연성으로 보존. 유죄 6인 명단은 옥관빈 포함설(민백+학술) 잠정 채택, 유동열설(우리역사넷 단독) 보존. 판결문 전사 도착 시 최우선 재판정(조건부).",
           date={"start": "1912-11-26", "end": "1913-10-09", "precision": "range", "calendar": "solar"})
adjudicate("evt-provgov-013", "〔판정 cfl-023〕 사임일 05-11 잠정 채택(다수 계열) — 05-12(임정기념관)는 '면직 공보 게재일 vs 사표 제출일' 차이 개연성 병기. 임정 공보 원문 도착 시 확정(조건부).")
adjudicate("evt-provgov-026", "〔판정 cfl-025·051·057〕 창당일 1930-01-25 채택(학술 포함 3계) — 우리역사넷 1929설은 준비기 압축 개연성 보존. 당의·당강 기초위원 6인/7인(조소앙 포함 여부)은 미해소 — 민백 항목 간 내부 상충, 차리석 1942 문서 도착 시 재판정(조건부). 대공주의 실체·명명은 학술 양론 병기 확정.")
adjudicate("evt-hsd-007", "〔판정 cfl-030〕 창립대회 1923-01-16 잠정 채택(기관+일자 구체성) — 민백 1922-07설은 준비 모임 개연성 병기.",
           date={"start": "1923-01-16", "end": "1923-01-16", "precision": "day", "calendar": "solar"})
adjudicate("evt-hsd-008", "〔판정 cfl-031〕 발족 1926-01 채택 — 부산흥사단 1925-12설은 '통합 결의 시점' 개연성 병기.")
adjudicate("evt-hsd-016", "〔판정 cfl-029〕 1935-02-10 채택 확정 — i815 '1933-02-10'은 오기 판정(위계·수량 압도 + 1932-12-26 선고와의 시공간 모순 + 디렉터 표본 확인). 각주에도 '오기로 판정됨' 명기 의무(단순 이설 격상 금지).")
adjudicate("evt-hsd-019", "〔판정 cfl-032〕 검거 개시일 1937-06-06 잠정 채택(현행 표기와 일치, 학술 기반) — 06-07설(부산흥사단) 보존. 기소 인원은 3설 미해소(49명 기소·기소유예 57·기소중지 75〔민백〕 / 41명〔우리역사넷〕 / 1938-08-15 42명〔위키 계열〕) — 동우회 판결문 대조 대기(조건부).")
adjudicate("evt-hsd-022", "〔판정 cfl-033〕 출감 12-23 잠정 채택(학술 계열 우위) — 12-24는 '보석 결정일 vs 출감·입원일' 차이 가설로 병기. 현행 range(12-23~24)가 양일을 포괄. 이명화 논문 본문 대조 시 확정.")
adjudicate("evt-hsd-001", "〔판정 cfl-056〕 창립지 샌프란시스코(강영소 집) 채택(기관·백과 일치) — LA설(디지털강남문화대전)은 1912년 LA 약법 초안 제시와의 혼동 개연성으로 기각·보존.")
adjudicate("evt-hsd-023", "〔판정 cfl-055〕 사인 표기 출처 간 상이 — '간경화를 포함한 복합 만성질환' 수준으로 서술 권고, 개별 병명 단정 금지. 사망진단서 원문 미확보(발굴 요청 #5).")
adjudicate("evt-shin-003", "〔판정 cfl-045〕 주최 태극학회 잠정 채택 — 대한유학생회설(디지털구리문화대전) 병기, 합동 강연 양립 가능성. 태극학보 1907년 초 호 보도 확인이 확정 경로.")
adjudicate("evt-shin-013", "〔판정 cfl-046〕 발기인 범위·임원은 민백 기준 잠정 채택(신민회 간부 5인 발기·총무 최남선) + 위키 명단(12인+유길준·김윤식 발의 등) 병기 — 설립취지서 원문(『소년』지 추정) 발굴 시 확정.")
adjudicate("evt-shin-019", "〔판정 cfl-049〕 출발 수단(열차/선박) 양설 모두 근거 미달 — 미해소, 수단 서술 보류 권고. 본문은 '행주에서 출발'까지만.")
adjudicate("evt-shin-025", "〔판정 cfl-050〕 양립 독법 채택 — '방문(시찰)은 실행, 근거지 건설 계획은 자금 문제로 보류'. 김도형 2015 여행권 연구 원문이 이동 실증 확정 경로.")
adjudicate("evt-provgov-006", "〔판정 cfl-043〕 공포 명의 직명 미확정 — '대통령 이승만' 명의 표기는 후대 정리 자료의 직명 소급 개연성(공포 시점은 통합 개헌 이전으로 대통령직 부재). 공보 원문 대조 필요(조건부).")
adjudicate("evt-provgov-029", "〔판정 cfl-052·053〕 방문 목적은 한인소년동맹 지원금 전달 약속(공훈 계열) 잠정 채택, '딸 생일 선물' 설(위키) 병기 — 1932 신문조서 도착 시 재판정(조건부). 체포 주체는 '일제 요청·주도 하에 프랑스조계 당국 협조로 체포·인도' 종합 서술 권고 — 세부 절차 단정 금지.")
adjudicate("evt-provgov-030", "〔판정 cfl-026 연동〕 압송의 서울 도착 6-02 채택에 따라 상하이 출발은 5월 말~6-01로 해석 — 본 레코드의 구금 종료(06-01)는 출항 시점과 정합.")
adjudicate("evt-phil-007", "〔판정 cfl-060〕 텍스트 신빙성 미해소 — 속기 원본 미확인 + 제목 이설 + 편집 계통 오염 가설. 자구 인용 시 '안도산전서 수록본에 따름' 한정 의무.")
adjudicate("evt-provgov-022", "〔판정 cfl-062〕 연설 제목 어순 양표기 병기('우리 혁명운동과 임시정부 문제에 대하여' vs '임시정부 문제와 우리의 혁명운동에 대하여') — 원문 대조 대기.")
adjudicate("evt-amer-034", "〔판정 cfl-042〕 Moongate 동업 형제는 필립 잠정 채택(식당명 'Phil Ahn's Moongate' + 기관 계열) — 필선 '공동 참여' 양립 가능성 병기.")
adjudicate("evt-shin-014", "〔판정 cfl-035 부속〕 구금이 1회(연속)인지 2회(안중근 의거 건+이재명 의거 건)인지 미확정 — 용산헌병대 신문기록(소재 미확정)이 유일 확정 경로. 석방 시점은 evt-shin-015 참조.")

# --- A·B·C형 (b) 양론 병기 — disputed 신규 ---
adjudicate("evt-early-004", "〔판정 cfl-001〕 별세 시점 기관 2종 동률 상충 — 미해소, range(1885~1890) 유지 지시. 족보·호적 원본 발굴이 결정 변수.",
           disputed=True, status="unresolved (cfl-001)",
           adopted={"start": "1885-01-01", "end": "1890-12-31", "precision": "range", "basis": "기관 동률 — 범위 보존 지시(cfl-001)"},
           variants=[
               {"claim": "8세 때(1885년경)", "source": "우리역사넷(기관)", "assessment": "동률"},
               {"claim": "11세 때(1888년경)", "source": "독립운동인명사전(기관)", "assessment": "동률 — 상세함은 위계가 아님(재검토 명기)"},
               {"claim": "1890년(12세)", "source": "위키백과", "assessment": "별도 연보 계통 유입 추정"}])
adjudicate("evt-early-006", "〔판정 cfl-037〕 서당(김현진) 위치 양설 — 거주지(노남리)와 수학지(심정리)가 별개일 양립 가능성. 미해소, '기록이 갈린다' 서술 권고.",
           disputed=True, status="unresolved (cfl-037)",
           adopted={"claim": "수학 사실 자체는 확정 — 위치만 양설", "basis": "양설 병기(cfl-037)"},
           variants=[
               {"claim": "대동군 노남리", "source": "독립운동인명사전(기관)", "assessment": "위계 우위이나 구체성 동급"},
               {"claim": "강서군 심정리(9~14세 거주 명시)", "source": "한국민족문화대백과", "assessment": "거주지/수학지 분리 양립 가능"}])
_cfl003 = dict(disputed=True, status="unresolved (cfl-003)",
    adopted={"start": "1894-09-01", "end": "1895-12-31", "precision": "range", "basis": "range(1894 가을~1895) 유지 — 단년 단정 금지(cfl-003)"},
    variants=[
        {"claim": "1894년(16세) 상경", "source": "우리역사넷(기관)", "assessment": "위계 우위이나 인명사전 비특정이 방어를 깸"},
        {"claim": "1895년 상경", "source": "민백·흥사단 연보", "assessment": "보존"},
        {"claim": "1894년 말~1895년 초 수렴", "source": "인명사전 서술 구조('전국을 돌고 도착')", "assessment": "양설 포괄 — 채택 범위"}])
adjudicate("evt-early-009", "〔판정 cfl-003〕 상경 연도 미해소 — range(1894 가을~1895) 유지, 본문 서술은 '1894~95년 무렵 상경'.", **_cfl003)
adjudicate("evt-early-010", "〔판정 cfl-003〕 입학 연도는 상경 연도(cfl-003)에 연동 — range 유지, 단년 단정 금지.", **_cfl003)
adjudicate("evt-early-012", "〔판정 cfl-004〕 졸업 연도 1896 잠정 채택(기관 우위) — 단 입학 연도(cfl-003)에 연동되어 1896~97 range 표기 허용. 부분해소.",
           disputed=True, status="unresolved (cfl-004, cfl-003 연동)",
           adopted={"start": "1896-01-01", "end": "1896-12-31", "precision": "year", "basis": "기관 우위 잠정 — cfl-003 해소 전 양론 유지"},
           variants=[
               {"claim": "1896년 졸업", "source": "독립운동인명사전(기관)", "assessment": "잠정 채택"},
               {"claim": "1897년 졸업", "source": "위키백과·흥사단 연보", "assessment": "1895 입학 시 '3년 수학'과 정합"}])
adjudicate("evt-amer-007", "〔판정 cfl-010〕 캠프 설립 연도 미해소(학술 자체 비확정) — range 유지. '1904-03 도착(evt-amer-006)과 캠프 형성은 단계적' 서술 권장.",
           disputed=True, status="unresolved (cfl-010)",
           adopted={"start": "1904-03-23", "end": "1905-12-31", "precision": "range", "basis": "학술 출처의 불확정성 보존(cfl-010)"},
           variants=[
               {"claim": "1904년 설립", "source": "영문 위키백과", "assessment": "백과 단독"},
               {"claim": "1905년(또는 1904년 말)", "source": "UCR Young Oak Kim Center 연표(학술)", "assessment": "학술 우위이나 자체 비확정 표현"}])
adjudicate("evt-shin-005", "〔판정 cfl-015〕 결성 시점은 현재 진행형 학술 논쟁 — 기준 표기 '1907년 4월(통설)' + 1906설·1908년 초설(이선민 2023) 병기. 단정 서술 금지.",
           disputed=True, status="unresolved (cfl-015, 학설 병존)",
           adopted={"start": "1907-04-01", "end": None, "precision": "month", "basis": "통설(신용하 계열·신편한국사·민백) — '통설' 명기 의무"},
           variants=[
               {"claim": "1907년 4월 결성(통설)", "source": "신편한국사·민백(신용하 계열)", "assessment": "기준 표기"},
               {"claim": "1906년 선행 결성설", "source": "일부 연구", "assessment": "병기"},
               {"claim": "1907년경, 정확히 알 수 없음", "source": "우리역사넷", "assessment": "비특정"},
               {"claim": "1908년 초설", "source": "이선민 2023(대동문화연구 121)", "assessment": "사료 비판적 신설 — 학계 수용 확인 전 통설 대체 불가"}])
adjudicate("evt-shin-024", "〔판정 cfl-017〕 안명근 체포 시점 미해소 — range(1910-11~12) 유지(레코드는 안악사건 국면 전체를 포괄). 신문조서 원문 대조 시 확정.",
           disputed=True, status="unresolved (cfl-017)",
           adopted={"start": "1910-11-01", "end": "1911-01-31", "precision": "range", "basis": "체포 시점 미확정 — 국면 범위 보존"},
           variants=[
               {"claim": "1910-11 체포", "source": "우리역사넷 「105인 사건」(기관)", "assessment": "위계 우위"},
               {"claim": "1910-12 평양역 체포", "source": "민백 「105인 사건」", "assessment": "장소 구체성"}])
adjudicate("evt-shin-028", "〔판정 cfl-020〕 도착일 기관 동률(09-02 공훈 vs 09-03 인명사전) — 미해소, range(09-02~03) 유지. 선박명(머제스틱/칼레도니아)도 양설 〔미확인〕 병기. NARA/엘리스섬 승선자 명부 도착 시 재판정.",
           disputed=True, status="unresolved (cfl-020)",
           adopted={"start": "1911-09-02", "end": "1911-09-03", "precision": "range", "basis": "기관 동률 — 범위 보존"},
           variants=[
               {"claim": "1911-09-02 도착", "source": "공훈전자사료관(기관)", "assessment": "동률"},
               {"claim": "1911-09-03 도착", "source": "독립운동인명사전(기관)·위키", "assessment": "동률"},
               {"claim": "선박 머제스틱호 vs 칼레도니아호", "source": "위키(단독) vs 보도 계열", "assessment": "미확인 양설"}])
adjudicate("evt-provgov-024", "〔판정 cfl-024·039·054〕 일자 미해소 — range(1927-01~02) 유지(음력 정월/양력 1월 혼동 가설은 검증 불가, 1-27 지지 출처 미발견). 장소는 '대동문 밖 대동공사' 잠정 채택 — '조양문 밖 대동공창'(민백) 병기. 구금 약 20일(인신 석방)과 약 6개월(사건의 외교적 종결)은 대상이 달라 비상충 — 분리 서술. 동아일보 1927-02 보도 대조가 해소 경로.",
           disputed=True, status="unresolved (cfl-024)", place_name="길림 대동문 밖 대동공사(大同公司)",
           adopted={"start": "1927-01-01", "end": "1927-02-28", "precision": "range", "basis": "일자 미확정 — 범위 보존"},
           variants=[
               {"claim": "1927-02 피검", "source": "독립운동인명사전·민백", "assessment": "기관·백과 — 일자 미특정"},
               {"claim": "1927-01(-27) 피검", "source": "일부 언론·연표", "assessment": "지지 출처 미발견(WebSearch)"}])
adjudicate("evt-hsd-013", "〔판정 cfl-027〕 입감 7-15 vs 수형카드 촬영 7-04의 선후 모순 — 같은 뿌리(이명화 기반 보도) 내 모순으로 미해소, month(1932-07) 유지. 논문 본문 직접 대조로만 해소.",
           disputed=True, status="unresolved (cfl-027)",
           adopted={"start": "1932-07-01", "end": "1932-07-31", "precision": "month", "basis": "선후 모순 미해소 — 월 단위 보존"},
           variants=[
               {"claim": "1932-07-15 입감", "source": "이명화 논문 기반 보도", "assessment": "같은 뿌리 내 모순"},
               {"claim": "수형기록카드 촬영 7-04(입감 선행 모순)", "source": "동일 계열", "assessment": "보도 단계 전사 오류 가설"}])
adjudicate("evt-shin-016", "〔판정 cfl-048〕 제의 주체·형식 불명, 회고 단일 계통 — 미해소, D등급 유지·한정 문형 의무. 통감부 문서 방증 발굴 전 사실 승격 금지.",
           disputed=True, status="unresolved (cfl-048)",
           adopted={"claim": "'내각 조직 제의·거절' 전승의 존재만 기록 — 사실 단정 불가", "basis": "회고 단일 계통(cfl-048)"},
           variants=[
               {"claim": "1910년 초 통감부의 내각 조직 제의와 거절", "source": "위키+한국문화정보원(회고 계열)", "assessment": "단일 계통 — 독립 확인 0"},
               {"claim": "사실성 미확정", "source": "동시대 사료 부재", "assessment": "한정 문형 의무"}])

# --- 기존 disputed 갱신 ---
adjudicate("evt-early-016", "〔판정 cfl-007〕 1898년 채택(조건부) — 양력 환산 1898-09-10(음력 7-25 만수성절). 환산 검증: 한국천문연구원 데이터 기반 korean_lunar_calendar로 독립 확인 — 음력 1898-07-25=양력 1898-09-10, 음력 1897-07-25=양력 1897-08-22(1897설은 조민희 평남 관찰사 임명(1897-09) 이전이라 부정합 — 환산으로 재확인). 1897년설은 만수성절 명칭 성립(1897-10 칭제 후)과도 모순으로 열세 — 보존. '연설=만수성절 당일' 전제 자체가 전승이므로 '조건부' 한정.",
           disputed=False, status="adopted_conditional (cfl-007)",
           date={"start": "1898-09-10", "end": "1898-09-10", "precision": "day", "calendar": "lunar"},
           adopted={"start": "1898-09-10", "end": "1898-09-10", "precision": "day",
                    "basis": "cfl-007 — 1898년 채택(조건부), 음력 1898-07-25(만수성절)의 양력 환산. 원본 역법 lunar 보존"})
adjudicate("evt-shin-021", "〔판정 cfl-016〕 1910년 4월 단정 금지(시공간 모순 — 본 분석과 cross-validator 판정 일치). 권고 range(1910-05~09) 채택 — 잠정 8~9월 range를 권고 범위로 확장. 시기 특정은 미해소 — 김도형 2015 여행권 연구 원문이 해소 열쇠.",
           disputed=True, status="unresolved (cfl-016, 4월설 기각)",
           date={"start": "1910-05-01", "end": "1910-09-30", "precision": "range", "calendar": "solar"},
           adopted={"start": "1910-05-01", "end": "1910-09-30", "precision": "range",
                    "basis": "cfl-016 — 내적 정합성 검사로 4월설 기각, 시기 미확정 범위 보존"})
adjudicate("evt-hsd-011", "〔판정 cfl-026〕 06-02(서울 도착) 채택(잠정) — 학술(이명화 2013) 기반, 6-07설은 지지 출처 미발견(WebSearch 재확인)·'상하이 출항일 vs 인천 도착일' 양립 가능성 잔존으로 보존. 동아일보 1932-06 보도 대조로 압송 경로 전체 복원 권장.",
           disputed=False, status="adopted_provisional (cfl-026)")
adjudicate("evt-hsd-025", "〔판정 cfl-034〕 안장일 미해소 — range(03-10~03-15)로 갱신(권고 범위). 03-10(구리문화대전)은 당일 안장의 절차상 개연성 낮음(단 일제의 추도 차단 변수 배제 불가), 03-12(통용)는 기관 확정 출처 부재. 동아·조선 1938-03 보도 대조가 해소 경로.",
           disputed=True, status="unresolved (cfl-034)",
           date={"start": "1938-03-10", "end": "1938-03-15", "precision": "range", "calendar": "solar"},
           adopted={"start": "1938-03-10", "end": "1938-03-15", "precision": "range", "basis": "cfl-034 — 일자 미확정 범위 보존"})
adjudicate("evt-hsd-015", "〔판정 cfl-028〕 1933-02 잠정 채택(기관+대전발 서한(1933-06-01) 정합 — 서한은 상한선 제공) — 3월설 병기. 서한 실물 특정(primary-source 증분)이 보강 경로.",
           disputed=False, status="adopted_provisional (cfl-028)",
           date={"start": "1933-02-01", "end": "1933-02-28", "precision": "month", "calendar": "solar"},
           adopted={"start": "1933-02-01", "end": "1933-02-28", "precision": "month", "basis": "cfl-028 — 기관(인명사전)+서한 정합"})
adjudicate("evt-shin-001", "〔판정 cfl-044〕 A(구상·취지서/장정 초안 작성) 채택 — 신편한국사의 '미국 초안 → 국내 창건 회합 승인' 절차 서술이 사료 밀착. B는 '미주 발기 조직설'로 병기(양립 부분 있음). 취지서·통용장정 원문이 확정 사료.",
           disputed=False, status="adopted (cfl-044)")
adjudicate("evt-shin-008", "〔판정 cfl-047〕 면담 사실성 판단 불가 — 독립 출처 0(이광수 전기→안도산전서→위키 단일 사슬), 동시대 사료(통감부 문서) 0건. 면담 가능 시기는 1907~1909 중반(이토 1909-10 사망). D등급 유지·사실 단정 금지 — '후대 전기에 따르면 ~라고 전해진다' 한정 문형만 허용. '1910 내각 제의'(evt-shin-016)와 병합 서술 금지(시간 모순).",
           disputed=True, status="unresolved (cfl-047)")
adjudicate("evt-shin-015", "〔판정 cfl-035〕 C 구조(연말 석방 후 재소환) 잠정 채택 — A·B의 기간 차이(2개월/3개월)는 1차/재소환 구간 포함 여부로 양립 가능. 기간 단정 금지, range(1909-12~1910-02) 유지. 용산헌병대 신문기록이 유일 확정 경로.",
           disputed=True, status="partially_resolved (cfl-035, 구조 채택·기간 미확정)",
           adopted={"start": "1909-12-01", "end": "1910-02-28", "precision": "range",
                    "basis": "cfl-035 — '연말 석방 후 재소환' 구조(기관 2계) 채택, 기간 단정 금지"},
           variants=[
               {"claim": "약 2개월 구금", "source": "위키", "assessment": "1차 구간만 계산 개연성"},
               {"claim": "3개월 구금", "source": "민백", "assessment": "재소환 구간 포함 개연성"},
               {"claim": "연말 석방 후 재소환", "source": "우리역사넷·공훈(기관 2)", "assessment": "구조 채택"}])
adjudicate("evt-amer-018", "〔판정 cfl-012·013〕 윤병구 당선 채택 확정(★최대 안건) — B(신편한국사·우리역사넷·국민회 50년사 계열)는 절차·인명·일자를 갖춘 사료 기반 + '선거 패배'라는 불리한 세부를 담아 창작 동기 부재. 안창호를 1912년 선출 회장으로 칭하는 표기는 전 필드 사용 금지(통설은 압축 오류 개연성). 안창호 당선은 1914-11(evt-amer-020)·취임식 1915-06-23(evt-amer-021). cfl-013 재분류에 따라 11-20 선포식은 evt-tla-001로 분리 — 본 레코드는 11-08 대표원의회로 한정.",
           disputed=False, status="adopted (cfl-012)",
           date={"start": "1912-11-08", "end": "1912-11-08", "precision": "day", "calendar": "solar"})
adjudicate("evt-amer-023", "〔판정 대기〕 본 상충(1918-11 vs 12-01)은 conflicts.md v1.1 확정 이후 통보분 — §7 절차에 따른 증분 등재 대기(cfl-063은 1932 선고일 건에 배정되어 본 건은 이후 번호로 등재 예정). 잠정 채택(1918-11) 유지.",
           disputed=True, status="pending_cross_validator (증분 등재 대기)")

# --- (c) 재분류 — 레코드 분리 (cfl-013, cfl-022) ---
adjudicate("evt-provgov-012", "〔판정 cfl-022·061〕 재분류(비상충) — 1-01 임시정부 신년축하회 연설과 1-03 민단 주최 신년축하회 연설(약 5시간 육대사 설명)은 별개의 두 자리. 본 레코드는 육대사 본 연설(민단 주최, 통용 1-03·일부 1-05)로 한정하고, 1-01 임정 축하회 연설은 evt-tla-002로 분리. 제목 자구는 '단정코'(斷定코, 당대 국한문) 잠정 채택 — '결단코'는 현대어 윤문 개연성, 독립신문 1920-01-08 원지면 대조 의무.",
           date={"start": "1920-01-03", "end": "1920-01-05", "precision": "range", "calendar": "solar"})

# ---------------------------------------------------------------
# 7b. conflicts.md v1.2 증분 반영 (primary-source 카탈로그 47건 반영분, 날짜 관련 4건)
# ---------------------------------------------------------------
adjudicate("evt-shin-031", "〔판정 갱신 cfl-019 v1.2〕 해소(잠정) 승격 — 경성복심법원 제30회 공판시말서 1913-01-15 원문 전사(src-pri-029, confirmed)로 항소심=경성복심(1912-11-26~1913-03-20, 52회 공판)이 1차 사료에 정박됨. 항소심 판결 1913-03-20·상고심 종결 1913-10 확정 반영. 민백 '대구복심 7-15'설은 이설 보존.")
adjudicate("evt-provgov-013", "〔판정 갱신 cfl-023 v1.2〕 조건부 해제 — 임시정부 공보 1921-05분이 결호 구간(제20·22·25호 등)에 걸릴 가능성으로 공보 확정 경로 상실(src-pri-030 확인). 05-11 잠정 채택을 그대로 확정 처리. 보강 경로는 독립신문 1921-05 보도.")
adjudicate("evt-provgov-006", "〔판정 갱신 cfl-043 v1.2〕 검증 경로 재설정 — 공보 제1호 발행이 1919-09-03으로 확인되어 연통제 공포(07-10)는 공보 개시 전. '공보 게재분 대조' 경로 자체가 부적합 판명 — 명의 직명 미확정 유지, 대체 경로는 임정 자료집(ij_001) 법령편 국무원령 제1호 원문.")
adjudicate("evt-shin-018", "〔사료 보강 v1.2〕 「거국가」의 대한매일신보 게재일이 1910-05-12로 특정됨(src-pri-046, 지면 대조 대기) — 작사 시점(망명 결행 직전, 본 레코드 range)과 신문 게재일(망명 후 5-12)은 구분되는 별개 사실. 게재일은 작사가 망명 전에 이루어졌다는 선후관계를 보강.")

# ---------------------------------------------------------------
# 7c. fact-checker claims_register 확정 통지 반영 (연표 관련 주의 2건)
# ---------------------------------------------------------------
adjudicate("evt-early-001", "〔등급 주의 clm-0003〕 calendar=lunar 판정의 근거 한계 — 음력 1878-10-06 원본 표기의 전거는 한인역사박물관·흥사단 연보 계열에 한정되며(흥사단 연보는 자체 기록 가중 유의), 당대 원본 기록(호적·족보)의 역법은 1~3단계 출처로 미확인(fact-checker B등급 — early-life의 '역법 미확인'은 상충이 아닌 탐색 실패 보고로 판정되어 C에서 승급, 음/양력 환산 정합 확인. 호적·족보 원본 미확인이라 A 불가). lunar 판정은 현존 최선 전거에 따른 것으로 유지하되, 족보·호적 원본 발굴 시 재검 대상.")
adjudicate("evt-phil-009", "〔등급 주의 — 디렉터 위임 건 처리〕 fact-checker 재판정: 발표 사실 C(유지, 사유 명기 방식), 집필지 베이징은 src-pri-009 서술로 보충 가능하나 원문 미대조 — 장소는 '베이징(추정)' 표기로 한정. 초출 매체 '시대일보 1924-05-19'설은 D등급 — 날짜 정밀화 보류, 연 단위 유지.",
           place_name="북경(北京)〔추정〕")

# ---------------------------------------------------------------
# 7d. conflicts.md v1.5 증분 반영 (cfl-063)
# ---------------------------------------------------------------
adjudicate("evt-hsd-014", "〔판정 cfl-063 v1.5〕 선고일 1932-12-26 채택(잠정·조건부) 확인 — 현행 표기와 일치, 변경 없음. 인명사전 day 명시+우리역사넷+국가기록원 자료 기반 보도 일치. 12-19설은 src-pri-018 비고에만 있는 계통 미상 이설(각주 수준 — disputed 마커 불요 판정). 본 선고일은 가출옥 오기 판정(cfl-029, evt-hsd-016)의 시공간 논증 전제로 연동 — 판결문 원본(src-pri-018, unlocated) 확보 시 최종 확정.")

# ---------------------------------------------------------------
# 7e. cross-validator disputed 9건 회신 반영 (conflicts.md v1.6 동기화분)
#     일치 확인 5건(쾌재정 연도·압송·대전 이감·신민회 구상·이토 면담·석방 구조)은 변경 없음 —
#     실질 변경 4건만 반영. 청도회의(2번)는 현행 05~09 range가 권고와 일치(이견은 구판 잠정안 대상).
# ---------------------------------------------------------------
# (1) 쾌재정: day 승격 보류 — '연설=만수성절 당일' 전제가 전승이므로 year 복귀 + 환산값 detail 병기 유지
adjudicate("evt-early-016", "〔판정 갱신 cfl-007 v1.6〕 연도 1898 채택 확정 — 단 day 승격(양력 1898-09-10)은 '연설=만수성절 당일' 전제가 전승이라는 cross-validator 회신에 따라 보류, 연 단위로 복귀. 검증된 환산값(음 1898-07-25=양 1898-09-10)은 본 detail에 병기 보존 — 만수성절 당일설이 1차 사료로 확인되면 day 승격.",
           disputed=False, status="adopted (cfl-007 v1.6 — 1898 확정, day 승격 보류)",
           date={"start": "1898-01-01", "end": "1898-12-31", "precision": "year", "calendar": "solar"},
           adopted={"start": "1898-01-01", "end": "1898-12-31", "precision": "year",
                    "basis": "cfl-007 — 1898년 확정(인명사전 + 만수성절 명칭 성립 + 조민희 재임 정합). 일자는 만수성절 당일 전제가 전승이라 연 단위 보존"})
# (4) 안장: cross-validator가 본 분석의 보수 상한(03-31)을 수용 — 03-15 절단 철회, 03-12 통용설 우세 표기
adjudicate("evt-hsd-025", "〔판정 갱신 cfl-034 v1.6〕 cross-validator가 03-15 상한을 '근거 미상 절단'으로 철회하고 본 병합안의 보수 range(03-10~31)를 수용 — 대장 갱신 동기화. 03-12 통용설을 우세 표기로 병기. 동아·조선 1938-03 보도 대조가 해소 경로.",
           disputed=True, status="unresolved (cfl-034 v1.6)",
           date={"start": "1938-03-10", "end": "1938-03-31", "precision": "range", "calendar": "solar"},
           adopted={"start": "1938-03-10", "end": "1938-03-31", "precision": "range",
                    "basis": "cfl-034 v1.6 — 일자 미확정, 보수 상한(월말)이 근거 미상 절단보다 정직"})
# (5) 파리 대표 선출: cfl-064 신규 등재 — month를 range(11-01~12-03)로 확장, 절차 2단계 양립 가설 병기
adjudicate("evt-amer-023", "〔판정 cfl-064〕 신규 등재(미해소) — 기관 동률(우리역사넷·국민회 50년사 '11월' vs 인명사전 '12-01' day). 외부 검증에서 11-25 인선 결의 + 12-01 전체회의 + 12-03 이승만 파견 추가 결정의 절차 2단계 양립 가설이 유력하나 11-25가 위키 계열이라 재분류 확정 불가. month 잠정 표기는 12-01 day 이설을 은폐할 위험 — range(1918-11-01~12-03)로 확장. 확정 경로: 신한민보 1918-11~12 지면(src-pri-012, 한국사DB 경로 확보).",
           disputed=True, status="unresolved (cfl-064)",
           date={"start": "1918-11-01", "end": "1918-12-03", "precision": "range", "calendar": "solar"},
           adopted={"start": "1918-11-01", "end": "1918-12-03", "precision": "range",
                    "basis": "cfl-064 — 기관 동률 미해소, 양 진술과 양립 가설을 모두 포괄하는 범위 보존"},
           variants=[
               {"claim": "1918년 11월 전체회의 소집·대표 3인 선출", "source": "우리역사넷·대한인국민회기념재단 50년사", "assessment": "기관 동률"},
               {"claim": "1918-12-01 재미한인전체대표자회의 소집", "source": "독립운동인명사전", "assessment": "기관 동률 — day 명시"},
               {"claim": "11-25 인선 결의 → 12-01 전체회의 → 12-03 이승만 파견 추가 결정(절차 2단계 양립)", "source": "위키 계열(11-25) + 기관 교차", "assessment": "유력 가설이나 11-25 출처 위계 미달로 확정 불가 — 신한민보 지면 대조 대기"}])
# (9) 석방 부속: 장소 한정 판정
adjudicate("evt-shin-015", "〔판정 부속 cfl-035 v1.6〕 '영등포 감옥' 표기는 흥사단 단독 서술 — 구금·석방 장소는 용산 헌병대까지만 서술 가능(cross-validator 판정).")
# (6) 대전 이감: 서한 실물 소재 명시
adjudicate("evt-hsd-015", "〔보강 v1.6〕 1933-06-01 대전발 서한의 실물은 unlocated(src-pri-034) — 상한 논거는 서한 존재 서술(위키 계열)에 의존함을 명시.")

# ---------------------------------------------------------------
# 7f. clm-0254 정밀도 판정 반영 (conflicts.md v1.9 §5 비고)
#     추서일 03-01 day의 근거 미달 — 두 레코드가 동일 출처(공훈전자사료관) 인용으로 독립 2출처
#     미충족, 원 레코드 자인("일자 확정 출처 미확보"). 정밀도 정직성 원칙에 따라 year 하향.
#     상충이 아닌 근거 미달 건이므로 disputed 마커는 부여하지 않는다.
# ---------------------------------------------------------------
adjudicate("evt-hsd-028", "〔판정 clm-0254 v1.9〕 추서일 정밀도를 year(1962)로 하향 — 03-01 day는 본 레코드와 병합 골격(evt-chrono-099)이 동일 출처(공훈전자사료관)를 인용해 독립 2출처 미충족이며, 골격은 '포상년도만 확인, 3·1절설 일자 확정 출처 미확보'를 명시. '3·1절(1962-03-01) 계기 추서'설은 〔미확인〕으로 보존 — 공적조서 원문 또는 동아일보 1962년 3월 보도(src-pri-014 경로) 대조 시 day 승격.",
           date={"start": "1962-01-01", "end": "1962-12-31", "precision": "year", "calendar": "solar"})

# ---------------------------------------------------------------
# 8. 보완 라운드 증분 교차 참조 (evt-chrono-102~110 신규 9건 — 101은 amer-017 병합)
# ---------------------------------------------------------------
adjudicate("evt-chrono-105", "〔연관〕 본 레코드가 참조하는 골격 evt-chrono-068(개막)·069(결렬)는 evt-provgov-016·evt-provgov-018로 병합됨. 개조파 대표 탈퇴는 evt-provgov-017. 본 레코드는 회의 전 기간의 개조파/창조파 노선 대립 국면 기록으로, 안창호-신채호·김규식 갈등 관계의 근거 사건(관계망 교차 레코드).")
adjudicate("evt-chrono-106", "〔연관〕 흥사단 원동임시위원부 조직(evt-hsd-004)의 detail은 '2월부터 이광수 등 유망 청년들이 입단하기 시작'으로 기술 — 본 레코드의 4월 입단(우리역사넷)과는 입단 절차(문답 등) 진행 기간으로 양립 가능. 정밀 일자 미확정.")
adjudicate("evt-chrono-109", "〔연관〕 본 레코드가 참조하는 골격 evt-chrono-078(상하이 복귀)은 evt-provgov-021로 병합됨. 복귀(5월) 직후의 임정 재정 지원 활동으로 시공간 정합.")

NEW_EVENTS = [
    {
        "id": "evt-tla-001",
        "title": "대한인국민회 중앙총회 정식 출범 선포식 — '해외 한인의 최고기관' 선언",
        "date": {"start": "1912-11-20", "end": "1912-11-20", "precision": "day", "calendar": "solar"},
        "place": copy.deepcopy(events["evt-amer-018"]["place"]),
        "actors": copy.deepcopy(events["evt-amer-018"]["actors"]),
        "orgs": copy.deepcopy(events["evt-amer-018"].get("orgs", [])),
        "summary": "1912년 11월 20일 샌프란시스코에서 대한인국민회 중앙총회 결성 선포식이 열려 중앙총회를 '해외 한인의 최고기관'으로 선언했다.",
        "detail": "〔분리 등재 cfl-013〕 11-08 제1차 대표원의회(evt-amer-018)와 11-20 정식 출범 선포는 상충이 아니라 결성 절차의 두 단계(신편한국사가 모두 기록) — cross-validator 재분류 권고에 따라 timeline-analyst가 분리 등재. 출처는 evt-amer-018에서 승계.",
        "sources": copy.deepcopy(events["evt-amer-018"]["sources"]),
        "confidence": "B",
        "tags": copy.deepcopy(events["evt-amer-018"].get("tags", [])),
        "merged_from": [], "disputed": False, "dispute_note": None,
        "split_from": "evt-amer-018",
    },
    {
        "id": "evt-tla-002",
        "title": "임시정부 신년축하회 연설 (1920년 1월 1일)",
        "date": {"start": "1920-01-01", "end": "1920-01-01", "precision": "day", "calendar": "solar"},
        "place": copy.deepcopy(events["evt-provgov-012"]["place"]),
        "actors": ["안창호"],
        "orgs": ["대한민국임시정부"],
        "summary": "1920년 1월 1일 상하이 임시정부 신년축하회 자리에서 안창호가 연설했다. 1월 3일 민단 주최 신년축하회의 육대사 연설(evt-provgov-012)과는 별개의 자리다.",
        "detail": "〔분리 등재 cfl-022〕 인명사전의 '1-01 연설'과 통용 문헌의 '1-03(·05) 연설'은 단일 사건으로 압축되며 생긴 가짜 상충 — 별개의 두 자리(philosophy 조사·독립기념관 사전+학술 지지)로 판명되어 cross-validator 재분류 권고에 따라 분리 등재. 육대사 본 연설(약 5시간)은 evt-provgov-012.",
        "sources": [copy.deepcopy(events["evt-phil-008"]["sources"][0])],
        "confidence": "B",
        "tags": ["연설"],
        "merged_from": [], "disputed": False, "dispute_note": None,
        "split_from": "evt-provgov-012",
    },
]
# ---------------------------------------------------------------
# 9. cfl-012 표현 금지 스크럽 — '초대 중앙총회장' 표현은 timeline.json 전 필드 사용 금지
#    (디렉터 §4·cross-validator 지시. 구 제목·원문 인용도 의미 보존 환언으로 대체 — 원문은 01_research 원본에 보존)
# ---------------------------------------------------------------
_a18 = merged["evt-amer-018"]
_a18["detail"] = _a18["detail"].replace(
    "대한인국민회 중앙총회 결성 — 초대 중앙총회장〕",
    "대한인국민회 중앙총회 결성 (구 제목의 회장 칭호 표기는 cfl-012 판정으로 폐기)〕")
_a18["detail"] = _a18["detail"].replace(
    "흥사단·기념사업회 자료의 '초대 중앙총회장 안창호'",
    "흥사단·기념사업회 자료의 '안창호가 1912년 선출 회장'이라는 표기")
import json as _json
assert "초대 중앙총회장" not in _json.dumps(merged, ensure_ascii=False), "금지 표현 잔존 (cfl-012)"

NEW_IDS = {e["id"] for e in NEW_EVENTS}
for ne in NEW_EVENTS:
    assert ne["id"] not in merged and ne["id"] not in INPUT_IDS, f"신규 id 충돌: {ne['id']}"
    merged[ne["id"]] = ne

# 무결성: 입력 id 전수 = (생존 id − 신규) ∪ merged_from
alias_ids = [m for r in merged.values() for m in r["merged_from"]]
assert len(alias_ids) == len(set(alias_ids)), "merged_from 중복 등재"
assert (set(merged) - NEW_IDS) | set(alias_ids) == INPUT_IDS, "입력 id 누락/초과"
assert not (set(merged) & set(alias_ids)), "생존 id가 merged_from에 동시 존재"

# 시간순 정렬
out_events = sorted(merged.values(), key=lambda r: (r["date"]["start"], r["id"]))

data = {
    "meta": {
        "generated": str(date.today()),
        "event_count": len(out_events),
        "source_files": SOURCE_FILES,
        "input_event_count": len(INPUT_IDS),
        "merged_away_count": len(alias_ids),
        "analyst_added_ids": sorted(NEW_IDS),
        "disputed_count": sum(1 for r in out_events if r["disputed"]),
        "conflicts_register": "conflicts.md v1.1 채택 권고 반영 완료",
        "status": "confirmed — 잔여 증분 1건(evt-amer-023, cfl-063 등재 대기)",
    },
    "events": out_events,
}
json.dump(data, open(OUT, "w"), ensure_ascii=False, indent=2)
print(f"병합 완료: 입력 {len(INPUT_IDS)} → 사건 {len(out_events)} (병합 흡수 {len(alias_ids)}, 분리 신규 {len(NEW_IDS)}, disputed {data['meta']['disputed_count']})")
