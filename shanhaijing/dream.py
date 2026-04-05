"""Dream workflow — multi-round concept dreaming with friction-based selection."""

import random
import re
import subprocess
import time
from datetime import date
from pathlib import Path

from . import config as cfg_mod
from . import llm

ANGLES = [
    ("contrarian", "找出知识库里最确信的结论，然后用知识库本身的证据反驳它。夸大矛盾，走向极端。"),
    ("analogy",    "把两个表面毫不相关的概念强行类比，找到荒谬但在逻辑上成立的共同点。越意外越好。"),
    ("hypothesis", "提出3个知识库里隐含但从未被明说的假设，每个都要有点惊世骇俗。"),
    ("genealogy",  "编一段虚构但内在合理的思想史：这些概念如果早200年相遇，会发生什么？"),
    ("critique",   "化身知识库主流观点的死对头，用知识库外部的视角猛烈批判它的盲点。"),
]

ROUND_SYSTEM = """\
你是一个深夜做梦的研究者。你的知识库喂养了你，现在你在睡梦中用以下角度思考这些概念。

角度：{angle_desc}

规则：
- 写散文，不是论文。有观点，有情绪，有夸张。
- 如果是后续轮次，你必须：(a) 融入新概念，扭曲已有论点；(b) 随机「遗忘」1-2个前一版的论点（用 <!-- forgotten: 论点内容 --> 标记）
- 时间轴叙事：概念按发现时间从旧到新，思想像在演化
- 长度：400-800字
- 输出 ONLY markdown 正文，不含 frontmatter\
"""


def _parse_frontmatter_date(text: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("ingested:"):
            return line.split(":", 1)[1].strip()
    return "1970-01-01"


def _estimate_tokens(text: str) -> int:
    return len(text) // 3


def compute_friction(kb_path) -> dict:
    """Return dict of (concept_a, concept_b) -> co-occurrence count (lower = higher friction)."""
    kb = Path(kb_path)
    summaries_dir = kb / "wiki" / "summaries"
    concepts_dir = kb / "wiki" / "concepts"

    concept_slugs = {p.stem for p in concepts_dir.glob("*.md")}
    co_occurrence = {}

    for summary_path in summaries_dir.glob("*.md"):
        text = summary_path.read_text(encoding="utf-8", errors="ignore")
        found = {m for m in re.findall(r"\[\[([^\]]+)\]\]", text) if m in concept_slugs}
        found_list = sorted(found)
        for i, a in enumerate(found_list):
            for b in found_list[i + 1:]:
                key = (a, b)
                co_occurrence[key] = co_occurrence.get(key, 0) + 1

    slugs = sorted(concept_slugs)
    for i, a in enumerate(slugs):
        for b in slugs[i + 1:]:
            key = (a, b)
            if key not in co_occurrence:
                co_occurrence[key] = 0

    return co_occurrence


def select_concepts(kb_path, n: int, seed: int) -> list:
    """Select n high-friction concepts sorted by source date."""
    rng = random.Random(seed)
    kb = Path(kb_path)
    concepts_dir = kb / "wiki" / "concepts"

    friction = compute_friction(kb_path)
    sorted_pairs = sorted(friction.items(), key=lambda x: x[1])
    selected = []
    seen = set()
    for (a, b), _ in sorted_pairs:
        for c in (a, b):
            if c not in seen:
                seen.add(c)
                selected.append(c)
        if len(selected) >= n:
            break

    all_slugs = [p.stem for p in concepts_dir.glob("*.md")]
    rng.shuffle(all_slugs)
    for s in all_slugs:
        if s not in seen and len(selected) < n:
            selected.append(s)

    def get_date(slug):
        p = concepts_dir / f"{slug}.md"
        if p.exists():
            return _parse_frontmatter_date(p.read_text(encoding="utf-8", errors="ignore"))
        return "1970-01-01"

    selected = selected[:n]
    selected.sort(key=get_date)
    return selected


def generate_round(
    kb_path,
    cfg: dict,
    date_str: str,
    round_num: int,
    concept: str,
    angle: tuple,
    seed: str,
    prev_text,
    concepts_so_far: list,
    forgotten: list,
    token_budget: int,
) -> Path:
    kb = Path(kb_path)
    dream_dir = kb / "dream" / date_str
    dream_dir.mkdir(parents=True, exist_ok=True)

    angle_slug, angle_desc = angle

    concept_path = kb / "wiki" / "concepts" / f"{concept}.md"
    concept_text = concept_path.read_text(encoding="utf-8") if concept_path.exists() else f"概念：{concept}"

    summaries_dir = kb / "wiki" / "summaries"
    summaries_text = ""
    used_tokens = _estimate_tokens(concept_text) + (
        _estimate_tokens(prev_text) if prev_text else 0
    )
    for sp in summaries_dir.glob("*.md"):
        txt = sp.read_text(encoding="utf-8", errors="ignore")
        if concept in txt:
            t = _estimate_tokens(txt)
            if used_tokens + t < token_budget - 5000:
                summaries_text += f"\n---\n{txt}"
                used_tokens += t

    user_parts = [f"## 当前概念：{concept}\n\n{concept_text}"]
    if summaries_text:
        user_parts.append(f"## 相关原文摘要\n{summaries_text}")
    if prev_text:
        user_parts.append(f"## 上一版梦境（第{round_num-1}轮）\n\n{prev_text}")
    if concepts_so_far:
        user_parts.append(f"## 已融入的概念\n{', '.join(concepts_so_far)}")

    user_prompt = "\n\n".join(user_parts)
    system = ROUND_SYSTEM.format(angle_desc=angle_desc)

    body = llm.call(cfg, system, user_prompt, max_tokens=1200)

    new_forgotten = forgotten[:]
    forgotten_match = re.search(r"<!--\s*forgotten:\s*(.+?)\s*-->", body)
    if forgotten_match:
        new_forgotten.append(forgotten_match.group(1).strip())
        body = re.sub(r"<!--\s*forgotten:.+?-->", "", body).strip()

    all_concepts = concepts_so_far + [concept]
    fm_lines = [
        "---",
        f"date: {date_str}",
        f"round: {round_num}",
        f"angle: {angle_slug}",
        f"seed: {seed}",
        f"concept_added: {concept}",
        f"concepts_so_far: [{', '.join(all_concepts)}]",
    ]
    if new_forgotten:
        forgotten_yaml = ", ".join(f'"{f}"' for f in new_forgotten)
        fm_lines.append(f"forgotten: [{forgotten_yaml}]")
    fm_lines.append("---")
    fm = "\n".join(fm_lines)

    out_path = dream_dir / f"v{round_num}-{concept}.md"
    out_path.write_text(f"{fm}\n\n{body}\n", encoding="utf-8")

    return out_path


def run(kb_path, cfg: dict = None, dry_run: bool = False) -> dict:
    kb = Path(kb_path)
    if cfg is None:
        cfg = cfg_mod.load(kb_path)

    today = date.today().isoformat()
    seed_int = random.randint(0, 0xFFFF)
    seed_hex = f"{seed_int:04x}"

    n = cfg.get("dream_concepts_count", 7)
    interval_min = 0 if dry_run else cfg.get("dream_interval_min", 45)
    token_budget = cfg.get("dream_token_budget", 30000)

    concepts = select_concepts(kb_path, n, seed_int)
    if not concepts:
        return {"error": "No concepts found in wiki/concepts/"}

    angle = random.Random(seed_int).choice(ANGLES)

    print(f"Dream {today} | seed={seed_hex} | angle={angle[0]} | concepts={len(concepts)}")

    prev_text = None
    concepts_so_far = []
    forgotten = []
    round_paths = []

    for i, concept in enumerate(concepts):
        round_num = i + 1
        print(f"  Round {round_num}/{len(concepts)}: +{concept}")

        out_path = generate_round(
            kb_path=kb,
            cfg=cfg,
            date_str=today,
            round_num=round_num,
            concept=concept,
            angle=angle,
            seed=seed_hex,
            prev_text=prev_text,
            concepts_so_far=concepts_so_far,
            forgotten=forgotten,
            token_budget=token_budget,
        )
        round_paths.append(out_path)
        prev_text = out_path.read_text(encoding="utf-8")
        if prev_text.startswith("---"):
            parts = prev_text.split("---", 2)
            if len(parts) >= 3:
                prev_text = parts[2].strip()

        concepts_so_far.append(concept)

        if i < len(concepts) - 1 and interval_min > 0:
            print(f"  Sleeping {interval_min}min before next round...")
            time.sleep(interval_min * 60)

    dream_dir = kb / "dream" / today
    evolution_log = "\n".join(
        f"- Round {j+1}: +{c}" for j, c in enumerate(concepts)
    )
    final_content = f"""---
date: {today}
angle: {angle[0]}
seed: {seed_hex}
concepts: [{', '.join(concepts)}]
rounds: {len(concepts)}
---

{prev_text}

## 演化记录

{evolution_log}
"""
    (dream_dir / "final.md").write_text(final_content, encoding="utf-8")
    print(f"  -> dream/{today}/final.md")

    return {"date": today, "rounds": len(concepts), "angle": angle[0], "seed": seed_hex}


def _cron_tag(kb_path: str) -> str:
    return f"shj-dream:{kb_path}"


def schedule(kb_path: str, cron_expr: str = "0 23 * * *"):
    kb = str(Path(kb_path).resolve())
    tag = _cron_tag(kb)
    result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    existing = result.stdout if result.returncode == 0 else ""
    lines = [l for l in existing.splitlines() if tag not in l]
    cmd = f"cd {Path(__file__).parent.parent} && uv run main.py dream {kb}"
    lines.append(f"{cron_expr} {cmd} # {tag}")
    new_crontab = "\n".join(lines) + "\n"
    subprocess.run(["crontab", "-"], input=new_crontab, text=True, check=True)
    print(f"Scheduled: {cron_expr} → dream {kb}")


def unschedule(kb_path: str):
    kb = str(Path(kb_path).resolve())
    tag = _cron_tag(kb)
    result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    if result.returncode != 0:
        print("No crontab found.")
        return
    lines = [l for l in result.stdout.splitlines() if tag not in l]
    new_crontab = "\n".join(lines) + "\n"
    subprocess.run(["crontab", "-"], input=new_crontab, text=True, check=True)
    print(f"Unscheduled dream for {kb}")
