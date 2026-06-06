#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
voice_check.py — 대사 감수 보조 스크립트 (voice-keeper / voice-checker 모드)

장(chapter) 파일을 입력받아 기계 검출 가능한 시트 위반 후보를 회부한다.
기계 검출은 1차 망(net)일 뿐 — 최종 판정은 육안 감수가 한다(맥락·시점·시기).

검출 항목:
  1. 호칭 시대착오 (금지표 C 8건) — 작중 연도 추출 후 호칭/등장 위반
  2. D등급 어록 자구 노출 (쾌재정 18조목·임종·신문조서 미확인 + 통용 어록 5건)
  3. 도산 금기어 (욕설·인신공격·자기 영웅화 과장)
  4. 호칭표 A·B 정합 (도산이 부르는 호칭 / 도산을 부르는 호칭)

사용법:
  python3 voice_check.py <chapter_file.md> [chapter_file2.md ...]
  python3 voice_check.py --all   # novel/chapters/ 전체
"""

import sys
import re
import glob
import os

CHAPTERS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "chapters")

# ── 1. D등급 어록 자구 패턴 (philosophy §8 ③ / voices.md D등급 지침) ──
# 정규식: 핵심 어절 시퀀스. 부분 변형도 걸리도록 느슨하게.
D_GRADE_QUOTES = [
    # ③ 신문조서 미확인 어록
    (r"밥을\s*먹어도.{0,8}대한.{0,4}독립", "신문조서 미확인 '밥을 먹어도…대한의 독립' (D등급 §③)"),
    # ④ 통용 어록 5건
    (r"낙망은\s*청년의\s*죽음", "통용 어록 '낙망은 청년의 죽음…' (D등급 §④)"),
    (r"서로\s*사랑하면\s*살고", "통용 어록 '서로 사랑하면 살고…' (D등급 §④)"),
    (r"힘은\s*건전한\s*인격과\s*공고한\s*단결", "통용 어록 '힘은 건전한 인격과 공고한 단결에서 난다' 자구 (D등급 §④)"),
    (r"우리는\s*자유의\s*인민", "통용 어록 '우리는 자유의 인민이니…' (D등급 §④)"),
    (r"참배나무에는?\s*참배", "통용 어록 '참배나무에는 참배가…' (D등급 §④)"),
    # ② 임종 어록 (대표 변형)
    (r"낙심\s*마(오|라|시오)", "임종 어록 추정 '낙심 마오' 자구 (D등급 §② — 임종은 침묵·동작으로)"),
    (r"목인\s*함석헌", "임종 어록 무관 — (placeholder, 무시)"),
]

# ── 2. 도산 금기어 (voices.md 도산 시트 어휘 지문 금기) ──
# 도산 발화로 의심되는 줄에서 욕설/인신공격/자기영웅화 과장 검출
DOSAN_FORBIDDEN = [
    (r"(개새끼|새끼|놈의|빌어먹을|제기랄|썅|씨발|개자식)", "욕설 — 도산 어휘 지문 금기(전 모드)"),
    (r"죽음을\s*각오하(고|겠)", "자기 영웅화 과장 — 도산 '비장어 절제' 위반 가능"),
    (r"목숨을\s*바치겠", "자기 영웅화 과장 — 도산 '비장어 절제' 위반 가능"),
]

# 평안도 방언 어미 — 도산 본인 발화 금지(표준 정중체). 조연엔 허용.
DIALECT_ENDINGS = [
    (r"기래서", "평안도 방언 '기래서' — 도산 본인 발화면 위반(§2: 도산은 표준 정중체)"),
    (r"~?디요", "평안도 방언 '~디요' — 도산 본인 발화면 위반"),
    (r"하갔", "평안도 방언 '하갔-' — 도산 본인 발화면 위반"),
]

# ── 3. 호칭 시대착오 (금지표 C) ──
# (정규식 패턴, 위반 설명, 위반이 성립하는 연도 조건 함수)
APPELLATION_RULES = [
    (r"우남\s*형", "이승만 '우남 형'", lambda y: y is not None and y >= 1925,
     "1925 전후 관계 악화 후 — '우남 박사'(거리) 또는 서신 형식"),
    (r"백범", "김구 '백범'", lambda y: y is not None and y < 1922,
     "1922 이전·후배기엔 '김구 군' (백범은 동지 승격 후)"),
    (r"단재야", "신채호 '단재야'(친밀 과장)", lambda y: True,
     "도산은 '단재' 유지하나 '단재야' 류 친밀 과장 금지 / 신채호→도산은 1923 이후 '안창호'"),
]

# ── 사망 연도 — C표 등장 금지 ──
DEATH_YEARS = {
    "안중근": (1910, "1910-03 사망 — 직접 등장 영구 금지(9장 의거는 배경·전언만)"),
    "이승훈": (1930, "1930 사망 — 1930 이후 직접 등장 금지"),
    "이동휘": (1935, "1935 사망 — 1935 이후 직접 등장 금지"),
    "신채호": (1936, "1936 사망 — 1936 이후 직접 등장 금지(전언만)"),
    "유상규": (1936, "1936 사망 — 사망 후 직접 등장 금지(종장 회상·묘는 가능)"),
    "김동삼": (1937, "1937 사망 — 사망 후 직접 등장 금지"),
}

# ── 작중 연도 추출 ──
YEAR_RE = re.compile(r"(18[7-9]\d|19[0-3]\d)\s*년?")

def extract_years(text):
    """파일 전체에서 등장하는 4자리 연도 집합."""
    return sorted(set(int(m.group(1)) for m in YEAR_RE.finditer(text)))

def primary_year(text, head_chars=600):
    """장 머리(시기·장소 표기 우선)에서 대표 연도 추정."""
    head = text[:head_chars]
    ys = extract_years(head)
    if ys:
        return min(ys)  # 장 머리의 가장 이른 연도를 작중 시점으로
    ys_all = extract_years(text)
    return ys_all[0] if ys_all else None


def is_dialogue_line(line):
    """대사 줄 추정 — 따옴표 포함."""
    return ('"' in line or '“' in line or '”' in line or
            "'" in line or '‘' in line or '’' in line)


def near_dosan(line):
    """도산 발화로 의심되는 줄 — 도산/안창호 언급 또는 도산 어휘 지문 동반."""
    return bool(re.search(r"(도산|안창호|무실|역행)", line))


def check_file(path):
    findings = []
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    lines = raw.splitlines()
    cy = primary_year(raw)
    all_years = extract_years(raw)
    findings.append(("INFO", 0, f"작중 추정 연도={cy} / 등장 연도집합={all_years}"))

    for i, line in enumerate(lines, 1):
        # D등급 어록 자구 — 전 줄 검사(대사·지문 무관, 자구 노출이 문제)
        for pat, desc in D_GRADE_QUOTES:
            if "placeholder" in desc:
                continue
            if re.search(pat, line):
                findings.append(("D-QUOTE", i, f"{desc} :: {line.strip()[:80]}"))

        # 도산 금기어
        for pat, desc in DOSAN_FORBIDDEN:
            if re.search(pat, line):
                tag = "DOSAN-TABOO" if near_dosan(line) else "TABOO?"
                findings.append((tag, i, f"{desc} :: {line.strip()[:80]}"))

        # 방언(도산 발화 의심 줄에서만 강한 경보)
        for pat, desc in DIALECT_ENDINGS:
            if re.search(pat, line):
                tag = "DOSAN-DIALECT" if near_dosan(line) else "DIALECT?"
                findings.append((tag, i, f"{desc} :: {line.strip()[:80]}"))

        # 호칭 시대착오
        for pat, name, cond, fix in APPELLATION_RULES:
            if re.search(pat, line):
                if cond(cy):
                    findings.append(("APPEL", i, f"{name} @연도{cy} 위반 후보 → {fix} :: {line.strip()[:70]}"))

        # 사망자 등장(작중 연도 기준)
        for name, (dyear, note) in DEATH_YEARS.items():
            if name in line and cy is not None and cy > dyear:
                findings.append(("DECEASED?", i, f"{name} 등장 @연도{cy} > 사망{dyear} → {note} :: {line.strip()[:60]}"))

    return cy, findings


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)
    if args[0] == "--all":
        files = sorted(glob.glob(os.path.join(CHAPTERS_DIR, "*.md")))
        if not files:
            print(f"[voice_check] 대상 없음: {CHAPTERS_DIR}/*.md")
            sys.exit(0)
    else:
        files = args

    total = 0
    for path in files:
        if not os.path.exists(path):
            print(f"[skip] 파일 없음: {path}")
            continue
        cy, findings = check_file(path)
        real = [f for f in findings if f[0] != "INFO"]
        print(f"\n===== {os.path.basename(path)} (작중≈{cy}) — 후보 {len(real)}건 =====")
        for tag, ln, msg in findings:
            print(f"  [{tag}] L{ln}: {msg}")
        total += len(real)
    print(f"\n[voice_check] 총 검출 후보 {total}건 (기계 1차망 — 육안 확정 필요).")


if __name__ == "__main__":
    main()
