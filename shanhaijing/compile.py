"""Compile workflow — process raw/*.md into wiki/ using LLM."""

import json
import re
from pathlib import Path

from . import config as cfg_mod
from . import llm, state

SUMMARY_SYSTEM = """\
You are a wiki compiler. Given a source document, write a 150-400 word wiki summary.
Output ONLY the markdown document — no extra commentary.
Include frontmatter:
---
title: <Title>
source: <original filename>
---
Then write the summary with headers, lists, and code blocks as appropriate.\
"""

CONCEPTS_SYSTEM = """\
Extract 2-8 key concepts from the document summary as kebab-case slugs.
These become wiki article titles — choose broadly useful concepts, not overly specific ones.
Return ONLY a JSON array of strings. Example: ["transformer", "attention-mechanism"]\
"""

CONCEPT_ARTICLE_SYSTEM = """\
Write a 200-500 word wiki concept article. Format:
---
title: <Human-readable title>
---
## Definition
## Key Properties
## Relevance
## Sources
(list source filenames in Sources)
Output ONLY the markdown — no extra commentary.\
"""

CONCEPT_UPDATE_SYSTEM = """\
Update the ## Sources section of the concept article to add a new source.
Keep all existing content unchanged. Output the full updated article.\
"""


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def run(kb_path: str, verbose: bool = True) -> dict:
    cfg = cfg_mod.load(kb_path)
    wiki = Path(kb_path) / "wiki"
    (wiki / "summaries").mkdir(parents=True, exist_ok=True)
    (wiki / "concepts").mkdir(parents=True, exist_ok=True)

    new_files, changed_files, deleted_files = state.diff(kb_path)
    to_process = new_files + changed_files

    if not to_process and not deleted_files:
        if verbose:
            print("Nothing to compile — all files up to date.")
        return {"new": 0, "changed": 0, "deleted": 0, "concepts": 0}

    st = state.load(kb_path)
    new_concepts = 0

    for rel in to_process:
        p = Path(kb_path) / rel
        content = p.read_text(encoding="utf-8")
        if verbose:
            print(f"  compiling {rel}…")

        # 1. Summary
        summary = llm.call(cfg, SUMMARY_SYSTEM,
                           f"Filename: {p.name}\n\n{content}", max_tokens=600)
        slug = p.stem
        summary_path = wiki / "summaries" / f"{slug}.md"
        summary_path.write_text(summary, encoding="utf-8")

        # 2. Extract concepts
        concepts_raw = llm.call(cfg, CONCEPTS_SYSTEM,
                                f"Summary:\n{summary}", max_tokens=200)
        try:
            start = concepts_raw.index("[")
            end = concepts_raw.rindex("]") + 1
            concepts = json.loads(concepts_raw[start:end])
        except (ValueError, json.JSONDecodeError):
            concepts = []

        # 3. Generate / update concept articles
        for concept in concepts[:8]:
            concept_slug = _slugify(concept)
            concept_path = wiki / "concepts" / f"{concept_slug}.md"
            if concept_path.exists():
                existing = concept_path.read_text(encoding="utf-8")
                updated = llm.call(cfg, CONCEPT_UPDATE_SYSTEM,
                                   f"Article:\n{existing}\n\nNew source: {slug}.md\nSummary excerpt:\n{summary[:500]}",
                                   max_tokens=800)
                concept_path.write_text(updated, encoding="utf-8")
            else:
                article = llm.call(cfg, CONCEPT_ARTICLE_SYSTEM,
                                   f"Concept: {concept}\n\nSource: {slug}.md\nSummary:\n{summary}",
                                   max_tokens=800)
                concept_path.write_text(article, encoding="utf-8")
                new_concepts += 1
                if verbose:
                    print(f"    + concept: {concept_slug}")

            st.setdefault("concepts", {})[concept_slug] = {
                "slug": concept_slug,
                "sources": list(set(
                    st.get("concepts", {}).get(concept_slug, {}).get("sources", []) + [slug]
                )),
            }

        # 4. Update state
        st.setdefault("files", {})[rel] = {
            "hash": state.file_hash(p),
            "summary": f"summaries/{slug}.md",
            "concepts": [_slugify(c) for c in concepts],
        }

    # Handle deletions
    for rel in deleted_files:
        slug = Path(rel).stem
        summary_path = wiki / "summaries" / f"{slug}.md"
        if summary_path.exists():
            summary_path.unlink()
        st["files"].pop(rel, None)
        if verbose:
            print(f"  deleted {rel}")

    # 5. Rebuild _index.md
    _rebuild_index(wiki, st)
    state.save(kb_path, st)

    result = {
        "new": len(new_files),
        "changed": len(changed_files),
        "deleted": len(deleted_files),
        "concepts": new_concepts,
    }
    if verbose:
        print(f"Done: {result['new']} new, {result['changed']} changed, "
              f"{result['deleted']} deleted, {result['concepts']} concepts added.")
    return result


def _rebuild_index(wiki: Path, st: dict):
    lines = ["# Wiki Index\n"]

    summaries = sorted((wiki / "summaries").glob("*.md"))
    if summaries:
        lines.append("## Summaries\n")
        for p in summaries:
            title = p.stem.replace("-", " ").title()
            lines.append(f"- [{title}](summaries/{p.name})")
        lines.append("")

    concepts = sorted((wiki / "concepts").glob("*.md"))
    if concepts:
        lines.append("## Concepts\n")
        for p in concepts:
            title = p.stem.replace("-", " ").title()
            lines.append(f"- [{title}](concepts/{p.name})")
        lines.append("")

    (wiki / "_index.md").write_text("\n".join(lines), encoding="utf-8")
