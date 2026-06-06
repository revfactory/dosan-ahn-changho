#!/usr/bin/env python3
"""도산 하네스 구조 검증 스크립트 — 청사진(.claude/harness-blueprint.md) 대비 전수 검사.

검사 항목:
  1. 에이전트 30개 존재, frontmatter(name=파일명, model: opus, description), 필수 섹션 8종
  2. 에이전트 Trait Vector 값 == 청사진 Traits 값 (8축 전수)
  3. 스킬 14개 존재, frontmatter(name=디렉토리명, description), 500줄 이내
  4. 에이전트 '사용 스킬'이 실제 스킬 디렉토리로 존재
  5. 오케스트레이터가 30개 에이전트 전부를 참조
  6. .claude/commands/ 미생성
재실행: python3 .claude/harness-validate.py  (하네스 유지보수 시 사용)
"""
import re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AGENTS = ROOT / ".claude" / "agents"
SKILLS = ROOT / ".claude" / "skills"
BLUEPRINT = ROOT / ".claude" / "harness-blueprint.md"
TRAIT_ORDER = ["주도성", "근거성", "계획성", "사회성", "협력성", "위험성향", "도구성향", "반성성"]
REQUIRED_SECTIONS = ["## 핵심 역할", "## Trait Vector", "## Policy", "## 사용 스킬",
                     "## 입력/출력 프로토콜", "## 에러 핸들링", "## 팀 통신 프로토콜", "## 재호출 지침"]

errors, warnings = [], []

def err(m): errors.append(m)
def warn(m): warnings.append(m)

# --- 청사진 파싱 ---
bp = BLUEPRINT.read_text(encoding="utf-8")
bp_agents = {}  # name -> [8 trait ints]
for m in re.finditer(r"^#### \d+\. ([a-z0-9-]+) —[^\n]*\n(.*?)(?=^#### |^### |^## )", bp, re.M | re.S):
    name, body = m.group(1), m.group(2)
    tm = re.search(r"Traits:\s*([\d/]+)", body)
    if tm:
        bp_agents[name] = [int(x) for x in tm.group(1).split("/")]
bp_skills = set(re.findall(r"^### S\d+\. ([a-z0-9-]+)", bp, re.M))

if len(bp_agents) != 30: err(f"청사진 에이전트 수 {len(bp_agents)} != 30")
if len(bp_skills) != 14: err(f"청사진 스킬 수 {len(bp_skills)} != 14")

# --- 에이전트 검사 ---
agent_files = sorted(AGENTS.glob("*.md"))
agent_names = {f.stem for f in agent_files}
if len(agent_files) != 30: err(f"에이전트 파일 수 {len(agent_files)} != 30")
missing = set(bp_agents) - agent_names
extra = agent_names - set(bp_agents)
if missing: err(f"청사진에 있으나 파일 없음: {sorted(missing)}")
if extra: err(f"청사진에 없는 파일: {sorted(extra)}")

used_skills = set()
for f in agent_files:
    t = f.read_text(encoding="utf-8")
    fm = re.match(r"^---\n(.*?)\n---\n", t, re.S)
    if not fm:
        err(f"{f.name}: frontmatter 없음"); continue
    fmt = fm.group(1)
    nm = re.search(r"^name:\s*(\S+)", fmt, re.M)
    if not nm or nm.group(1) != f.stem: err(f"{f.name}: frontmatter name 불일치 ({nm and nm.group(1)})")
    if not re.search(r"^model:\s*[\"']?opus", fmt, re.M): err(f"{f.name}: model: opus 누락")
    dm = re.search(r"^description:\s*(.+)", fmt, re.M)
    if not dm or len(dm.group(1).strip()) < 20: err(f"{f.name}: description 누락/빈약")
    for sec in REQUIRED_SECTIONS:
        if sec not in t: err(f"{f.name}: 섹션 누락 {sec}")
    # Trait 값 대조
    vals = {}
    for tr in TRAIT_ORDER:
        vm = re.search(rf"\|\s*{tr}\s*\|\s*(\d+)\s*/\s*10", t)
        if vm: vals[tr] = int(vm.group(1))
        else: err(f"{f.name}: Trait '{tr}' 행 없음/형식 오류")
    if f.stem in bp_agents and len(vals) == 8:
        actual = [vals[tr] for tr in TRAIT_ORDER]
        if actual != bp_agents[f.stem]:
            err(f"{f.name}: Trait 값 불일치 — 파일 {actual} vs 청사진 {bp_agents[f.stem]}")
    # 사용 스킬 수집
    sk_sec = re.search(r"## 사용 스킬\n(.*?)(?=\n## )", t, re.S)
    if sk_sec:
        for s in re.findall(r"`([a-z0-9-]+)`", sk_sec.group(1)):
            used_skills.add((f.stem, s))
    n_lines = t.count("\n") + 1
    if n_lines > 120: warn(f"{f.name}: {n_lines}줄 (목표 60~100)")

# --- 스킬 검사 ---
skill_dirs = sorted([d for d in SKILLS.iterdir() if d.is_dir()])
skill_names = {d.name for d in skill_dirs}
expected_skills = bp_skills | {"dosan-orchestrator"}
if skill_names != expected_skills:
    err(f"스킬 디렉토리 불일치 — 누락: {sorted(expected_skills - skill_names)}, 잉여: {sorted(skill_names - expected_skills)}")
for d in skill_dirs:
    sm = d / "SKILL.md"
    if not sm.exists(): err(f"{d.name}: SKILL.md 없음"); continue
    t = sm.read_text(encoding="utf-8")
    fm = re.match(r"^---\n(.*?)\n---\n", t, re.S)
    if not fm: err(f"{d.name}: frontmatter 없음"); continue
    nm = re.search(r"^name:\s*(\S+)", fm.group(1), re.M)
    if not nm or nm.group(1) != d.name: err(f"{d.name}: frontmatter name 불일치")
    dm = re.search(r"^description:\s*(.+)", fm.group(1), re.M)
    if not dm or len(dm.group(1).strip()) < 40: err(f"{d.name}: description 누락/빈약(pushy 요건 미달)")
    n_lines = t.count("\n") + 1
    if n_lines > 500: err(f"{d.name}: SKILL.md {n_lines}줄 > 500")
    if "## 산출물 검증" not in t and d.name != "dosan-orchestrator":
        warn(f"{d.name}: '## 산출물 검증' 섹션 없음")

# --- 에이전트→스킬 참조 무결성 ---
for agent, skill in sorted(used_skills):
    if skill not in skill_names:
        err(f"{agent}: 존재하지 않는 스킬 참조 `{skill}`")

# --- 오케스트레이터의 에이전트 전수 참조 ---
orch = SKILLS / "dosan-orchestrator" / "SKILL.md"
if orch.exists():
    ot = orch.read_text(encoding="utf-8")
    for a in sorted(bp_agents):
        if a not in ot: err(f"오케스트레이터가 에이전트 미참조: {a}")
else:
    err("dosan-orchestrator/SKILL.md 없음")

# --- commands 미생성 확인 ---
if (ROOT / ".claude" / "commands").exists(): err(".claude/commands/ 가 생성되어 있음 (금지)")

# --- 보고 ---
print(f"에이전트 파일: {len(agent_files)}/30 | 스킬: {len(skill_dirs)}/14 | 에이전트→스킬 참조: {len(used_skills)}건")
if warnings:
    print(f"\n⚠ 경고 {len(warnings)}건:"); [print("  -", w) for w in warnings]
if errors:
    print(f"\n✗ 오류 {len(errors)}건:"); [print("  -", e) for e in errors]
    sys.exit(1)
print("\n✓ 전체 구조 검증 통과")
