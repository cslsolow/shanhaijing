"""Distill workflow — structure fragmented input into a knowledge entry."""

import hashlib
from datetime import date
from pathlib import Path

from . import config as cfg_mod
from . import llm, compile

DISTILL_SYSTEM = """\
You are a knowledge distiller. The user gives you a fragment — a thought, a sentence, \
a conversation snippet, a random observation. Your job is to structure it into a clean \
markdown knowledge entry.

Output format (EXACTLY):

---
title: <concise, specific title — not generic>
source: distill
ingested: <today's date YYYY-MM-DD>
visibility: private
type: fragment
desc: <ONE sentence ≤20 words capturing the core insight>
---

## Insight

<Restate the core idea clearly in 1-3 sentences>

## Context

<Why this matters, what domain it relates to, any implications>

## Connections

<List 2-5 related concepts as [[wikilinks]] that this idea connects to>

Rules:
- Write in the same language as the input
- Be concise but complete — capture the full meaning
- The title should be specific, not generic
- desc must be ≤20 words — it will appear in the wiki index for fast scanning
- Wikilink slugs should be kebab-case: [[attention-mechanism]]
- Output ONLY the markdown, nothing else\
"""


def run(kb_path, text, auto_compile=True, verbose=True):
    cfg = cfg_mod.load(kb_path)
    today = date.today().isoformat()
    short_hash = hashlib.sha256(text.encode()).hexdigest()[:8]
    filename = f"distill-{today}-{short_hash}.md"

    raw_dir = Path(kb_path) / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    out_path = raw_dir / filename

    if verbose:
        print(f"Distilling into {filename}...")

    result = llm.call(
        cfg, DISTILL_SYSTEM,
        f"Today: {today}\n\nFragment:\n{text}",
        max_tokens=800,
    )

    out_path.write_text(result, encoding="utf-8")

    # Extract title from frontmatter
    title = filename
    for line in result.splitlines():
        if line.startswith("title:"):
            title = line.split(":", 1)[1].strip()
            break

    if verbose:
        print(f"  -> {title}")

    compiled = False
    if auto_compile:
        if verbose:
            print("Auto-compiling...")
        compile.run(kb_path, verbose=verbose)
        compiled = True

    return {"file": f"raw/{filename}", "title": title, "compiled": compiled}
