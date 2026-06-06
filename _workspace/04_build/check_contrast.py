#!/usr/bin/env python3
"""
check_contrast.py — WCAG 2.x 색 대비 검증 (a11y-engineer / Phase 4b)

design-system.md §2 대비표의 모든 전경/배경 조합을 site/css/tokens.css의 실측 값으로
독립 계산해 AA(본문 ≥4.5, 큰글씨·UI ≥3.0) 통과 여부를 판정한다.

근거: WCAG 2.1 SC 1.4.3 (Contrast Minimum). 상대휘도·대비비 공식은 WCAG 정의.
  L = 0.2126*R + 0.7152*G + 0.0722*B  (R/G/B는 선형화된 sRGB 채널)
  contrast = (L_lighter + 0.05) / (L_darker + 0.05)

용도:
  - 대기/감사 중 대비표 자체 검증 (design-system.md 수치 ↔ 실측 일치)
  - 페이지 감사 시 임의 전경/배경 조합 즉석 판정 (--pair 옵션)
  - tokens.css 변경 시 회귀 검사 (exit 1 = 위반 존재)

사용:
  python3 check_contrast.py                 # 대비표 전건 검증
  python3 check_contrast.py --tokens path   # tokens.css 경로 지정
  python3 check_contrast.py --pair '#1A1815' '#F7F3EB'   # 임의 조합 1건
  python3 check_contrast.py --json          # 기계 판독용 JSON 출력
"""
import argparse
import json
import re
import sys
from pathlib import Path

DEFAULT_TOKENS = Path(__file__).resolve().parent.parent.parent / "site" / "css" / "tokens.css"

# ---------------------------------------------------------------------------
# WCAG 대비 계산
# ---------------------------------------------------------------------------

def hex_to_rgb(h):
    h = h.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) != 6:
        raise ValueError(f"잘못된 hex: #{h}")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _linearize(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def relative_luminance(rgb):
    r, g, b = (_linearize(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(fg_hex, bg_hex):
    l1 = relative_luminance(hex_to_rgb(fg_hex))
    l2 = relative_luminance(hex_to_rgb(bg_hex))
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


# ---------------------------------------------------------------------------
# tokens.css 파싱 — 원시 hex + 시맨틱 별칭(var 체인) 해소
# ---------------------------------------------------------------------------

def parse_tokens(css_path):
    """--name: value; 를 추출하고 var(--alias) 체인을 hex로 해소한다."""
    text = Path(css_path).read_text(encoding="utf-8")
    raw = {}
    for m in re.finditer(r"(--[\w-]+)\s*:\s*([^;]+);", text):
        raw[m.group(1)] = m.group(2).strip()

    resolved = {}

    def resolve(name, seen=None):
        seen = seen or set()
        if name in resolved:
            return resolved[name]
        if name in seen:
            raise ValueError(f"순환 참조: {name}")
        seen.add(name)
        val = raw.get(name)
        if val is None:
            return None
        var_m = re.fullmatch(r"var\((--[\w-]+)\)", val)
        if var_m:
            r = resolve(var_m.group(1), seen)
            resolved[name] = r
            return r
        hex_m = re.fullmatch(r"#[0-9A-Fa-f]{3,6}", val)
        if hex_m:
            resolved[name] = val
            return val
        # 색이 아닌 토큰(간격·폰트 등)은 None
        resolved[name] = None
        return None

    colors = {}
    for name in raw:
        try:
            v = resolve(name)
        except ValueError:
            v = None
        if v:
            colors[name] = v
    return colors


# ---------------------------------------------------------------------------
# design-system.md §2 대비표 (검증 대상 — 토큰명·기대 등급)
#   level: "body"=본문 AA(≥4.5) 필요, "large"=큰글씨/UI(≥3.0)만 필요
#   기대(통과/불통과)는 design-system.md 표 그대로 — 실측과 어긋나면 보고
# ---------------------------------------------------------------------------

TABLE = [
    # (fg_token, bg_token, level, expect_pass, 용도)
    ("--ink", "--paper", "body", True, "본문 기본"),
    ("--ink", "--paper-dim", "body", True, "카드 본문"),
    ("--ink-soft", "--paper", "body", True, "캡션·메타"),
    ("--ink-soft", "--paper-dim", "body", True, "카드 내 메타"),
    ("--ink-faint", "--paper", "body", True, "비활성·플레이스홀더"),
    ("--ink-faint", "--paper-dim", "body", True, "카드 내 미확인 라벨"),
    ("--dancheong", "--paper", "body", True, "링크·강조"),
    ("--dancheong", "--paper-dim", "body", True, "카드 내 링크"),
    ("--dancheong-dim", "--paper", "body", True, "링크 hover"),
    ("--on-accent", "--dancheong", "body", True, "강조 버튼"),
    ("--on-accent", "--dancheong-dim", "body", True, "버튼 hover"),
    ("--celadon", "--paper", "large", True, "큰 제목(24px+)·테두리·아이콘만"),
    ("--celadon", "--paper-dim", "large", True, "카드 테두리·비텍스트만"),
    ("--celadon-deep", "--paper", "body", True, "청자색 본문 텍스트(불가피 시)"),
    ("--celadon-deep", "--paper-dim", "body", True, "카드 내 청자 텍스트"),
    ("--grade-a-text", "--paper-dim", "body", True, "A등급 배지(카드 위)"),
    ("--grade-a-text", "--paper", "body", True, "A등급 배지(본문 위)"),
    ("--grade-c-text", "--paper-dim", "body", True, "C등급 배지(카드 위)"),
    ("--grade-c-text", "--paper", "body", True, "C등급 배지(본문 위)"),
    ("--loc-confirmed", "--paper-dim", "body", True, "소재 확인 배지"),
    ("--loc-cited", "--paper-dim", "body", True, "cited_only 배지"),
    ("--loc-unlocated", "--paper-dim", "body", True, "소재 미확인 배지"),
    # 금지 조합 — design-system.md가 명시적으로 불통과로 등재
    ("--celadon", "--paper", "body", False, "celadon 본문크기 금지 확인(불통과 기대)"),
    ("--celadon", "--paper-dim", "body", False, "celadon 본문크기 금지 확인(불통과 기대)"),
    ("--dancheong", "--ink", "large", False, "금지 조합(불통과 기대)"),
]

AA_BODY = 4.5
AA_LARGE = 3.0


def verify_table(colors):
    rows = []
    failures = []  # 실측이 기대와 어긋난 항목(=보고 대상)
    for fg, bg, level, expect_pass, use in TABLE:
        fg_hex, bg_hex = colors.get(fg), colors.get(bg)
        if not fg_hex or not bg_hex:
            rows.append({"fg": fg, "bg": bg, "ratio": None, "level": level,
                         "use": use, "status": "토큰 미해소", "ok": False})
            failures.append((fg, bg, "토큰 미해소"))
            continue
        ratio = contrast_ratio(fg_hex, bg_hex)
        threshold = AA_BODY if level == "body" else AA_LARGE
        passes = ratio >= threshold
        # 기대와 실측 일치 여부
        consistent = (passes == expect_pass)
        rows.append({
            "fg": fg, "bg": bg, "fg_hex": fg_hex, "bg_hex": bg_hex,
            "ratio": round(ratio, 2), "level": level, "threshold": threshold,
            "use": use, "passes_aa": passes, "expected_pass": expect_pass,
            "consistent": consistent,
        })
        if not consistent:
            failures.append((fg, bg,
                             f"실측 {ratio:.2f}:1 → {'통과' if passes else '불통과'} "
                             f"(표 기대: {'통과' if expect_pass else '불통과'})"))
    return rows, failures


def main():
    ap = argparse.ArgumentParser(description="WCAG 2.x 대비 검증")
    ap.add_argument("--tokens", default=str(DEFAULT_TOKENS))
    ap.add_argument("--pair", nargs=2, metavar=("FG", "BG"),
                    help="임의 전경/배경 hex 1건 판정")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.pair:
        fg, bg = args.pair
        r = contrast_ratio(fg, bg)
        out = {
            "fg": fg, "bg": bg, "ratio": round(r, 2),
            "body_aa_4.5": r >= AA_BODY, "large_ui_aa_3.0": r >= AA_LARGE,
            "aaa_7.0": r >= 7.0,
        }
        print(json.dumps(out, ensure_ascii=False, indent=2) if args.json
              else f"{fg} / {bg} = {r:.2f}:1  "
                   f"[본문AA {'통과' if r >= AA_BODY else '불통과'} / "
                   f"큰글씨·UI {'통과' if r >= AA_LARGE else '불통과'}]")
        return 0

    colors = parse_tokens(args.tokens)
    rows, failures = verify_table(colors)

    if args.json:
        print(json.dumps({"rows": rows, "failures": failures},
                         ensure_ascii=False, indent=2))
    else:
        print(f"WCAG 대비 검증 — tokens: {args.tokens}\n")
        print(f"{'전경':<18}{'배경':<14}{'대비':>8}  {'등급':<6}{'판정':<8}용도")
        print("-" * 92)
        for r in rows:
            if r["ratio"] is None:
                print(f"{r['fg']:<18}{r['bg']:<14}{'?':>8}  {r['level']:<6}{r['status']}")
                continue
            mark = "통과" if r["passes_aa"] else "불통과"
            flag = "" if r["consistent"] else "  ⚠ 표와 불일치"
            print(f"{r['fg']:<18}{r['bg']:<14}{r['ratio']:>7.2f}:1  "
                  f"{r['level']:<6}{mark:<8}{r['use']}{flag}")
        print("-" * 92)
        if failures:
            print(f"\n⚠ 표와 실측 불일치 {len(failures)}건:")
            for fg, bg, why in failures:
                print(f"  - {fg} / {bg}: {why}")
        else:
            print("\n✓ design-system.md §2 대비표 전건이 실측과 일치한다.")

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
