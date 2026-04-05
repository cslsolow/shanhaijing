"""Compile workflow — process raw/*.md into wiki/ using LLM."""

import json
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from . import config as cfg_mod
from . import llm, state

SUMMARY_SYSTEM = """\
You are a wiki compiler. Given a source document, write a 150-400 word wiki summary.
Output ONLY the markdown document — no extra commentary.
Include frontmatter with ALL of these fields:
---
title: "<concise, specific title>"
source: "<original filename>"
ingested: <YYYY-MM-DD today's date>
visibility: private
type: <paper|article|note|book|video|other>
desc: "<ONE sentence, ≤20 words, capturing the key claim or contribution>"
---
Then write the summary with headers, lists, and code blocks as appropriate.
The desc field is critical — it will appear in the index so agents can scan without opening files.\
"""

CONCEPTS_SYSTEM = """\
Extract 2-8 key concepts from the document summary as kebab-case slugs.
These become wiki article titles — choose broadly useful concepts, not overly specific ones.
Return ONLY a JSON array of strings. Example: ["transformer", "attention-mechanism"]\
"""

CONCEPT_ARTICLE_SYSTEM = """\
Write a 200-500 word wiki concept article. Output ONLY the markdown — no extra commentary.
Use this exact format:
---
title: "<Human-readable title>"
type: concept
desc: "<ONE sentence ≤20 words defining this concept>"
sources: [<source-slug>]
---
## Definition
## Key Properties
## Relevance
## Related
(list 2-5 related concepts as [[wikilinks]])
## Sources
(list source filenames)\
"""

CONCEPT_UPDATE_SYSTEM = """\
Update the concept article: add the new source to the `sources` frontmatter list and ## Sources section.
Keep all existing content unchanged. Output the full updated article.\
"""

CONCEPT_RESOLVE_SYSTEM = """\
You are a knowledge base deduplicator. Given existing concept slugs and newly extracted concepts, \
decide for each new concept whether to merge into an existing one or create new.

Merge only when concepts are semantically equivalent or one is a clear alias/subset of the other.
Do NOT merge merely related concepts.

Return ONLY a JSON array, one object per new concept:
[
  {"input": "<new concept>", "action": "merge", "target": "<existing-slug>"},
  {"input": "<new concept>", "action": "create", "target": "<new-kebab-slug>"}
]
No explanation, no markdown fences, just the JSON array.\
"""


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _resolve_concepts(cfg, new_concepts: list[str], existing_slugs: list[str]) -> list[dict]:
    """Ask LLM to map each new concept to an existing slug or a new slug."""
    if not new_concepts:
        return []
    if not existing_slugs:
        return [{"input": c, "action": "create", "target": _slugify(c)} for c in new_concepts]

    prompt = (
        f"Existing concepts: {json.dumps(existing_slugs)}\n\n"
        f"New concepts: {json.dumps(new_concepts)}"
    )
    raw = llm.call(cfg, CONCEPT_RESOLVE_SYSTEM, prompt, max_tokens=400)
    try:
        start = raw.index("[")
        end = raw.rindex("]") + 1
        decisions = json.loads(raw[start:end])
        # validate shape
        return [
            d for d in decisions
            if isinstance(d, dict) and d.get("action") in ("merge", "create") and d.get("target")
        ]
    except (ValueError, json.JSONDecodeError):
        # fallback: create all as new
        return [{"input": c, "action": "create", "target": _slugify(c)} for c in new_concepts]


def run(kb_path: str, verbose: bool = True, workers: int = 2) -> dict:
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
    lock = threading.Lock()

    def process_file(rel):
        """Phase 1: generate summary + extract concepts for one file. Thread-safe."""
        p = Path(kb_path) / rel
        content = p.read_text(encoding="utf-8")

        # 1. Summary
        summary = llm.call(cfg, SUMMARY_SYSTEM,
                           f"Filename: {p.name}\n\n{content}", max_tokens=600)

        slug = p.stem
        for line in summary.splitlines():
            if line.startswith("title:"):
                title_val = line.split(":", 1)[1].strip().strip('"')
                derived = _slugify(title_val)
                if derived and len(derived) > 3:
                    slug = derived[:60]
                break

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

        return rel, slug, summary, concepts

    # Phase 1: parallel summary + concept extraction
    results = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(process_file, rel): rel for rel in to_process}
        for future in as_completed(futures):
            rel = futures[future]
            try:
                results.append(future.result())
                if verbose:
                    print(f"  ✓ {rel}")
            except Exception as e:
                if verbose:
                    print(f"  ✗ {rel}: {e}")

    # Phase 2: serial concept merge/create (shared concept directory)
    for rel, slug, summary, concepts in results:
        existing_slugs = [p.stem for p in (wiki / "concepts").glob("*.md")]
        decisions = _resolve_concepts(cfg, concepts[:8], existing_slugs)

        for d in decisions:
            concept_slug = d["target"]
            concept_path = wiki / "concepts" / f"{concept_slug}.md"
            if d["action"] == "merge" and concept_path.exists():
                existing = concept_path.read_text(encoding="utf-8")
                updated = llm.call(cfg, CONCEPT_UPDATE_SYSTEM,
                                   f"Article:\n{existing}\n\nNew source: {slug}.md\nSummary excerpt:\n{summary[:500]}",
                                   max_tokens=800)
                concept_path.write_text(updated, encoding="utf-8")
                if verbose:
                    print(f"    ~ concept merged: {d['input']} → {concept_slug}")
            else:
                article = llm.call(cfg, CONCEPT_ARTICLE_SYSTEM,
                                   f"Concept: {d['input']}\n\nSource: {slug}.md\nSummary:\n{summary}",
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

        st.setdefault("files", {})[rel] = {
            "hash": state.file_hash(Path(kb_path) / rel),
            "summary": f"summaries/{slug}.md",
            "concepts": [d["target"] for d in decisions],
        }
        # Persist state after each file so progress survives interruption
        state.save(kb_path, st)

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


def _extract_frontmatter(path: Path) -> dict:
    """Parse YAML frontmatter from a markdown file."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    fm = {}
    for line in text[3:end].splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip().strip('"')
    return fm


def _rebuild_index(wiki: Path, st: dict):
    from datetime import date
    today = date.today().isoformat()

    summaries = sorted((wiki / "summaries").glob("*.md"))
    concepts  = sorted((wiki / "concepts").glob("*.md"))

    lines = [
        "# Wiki Index",
        "",
        f"compiled: {today}  |  summaries: {len(summaries)}  |  concepts: {len(concepts)}",
        "",
    ]

    if summaries:
        lines.append("## Summaries")
        lines.append("")
        for p in summaries:
            fm = _extract_frontmatter(p)
            title = fm.get("title") or p.stem
            desc  = fm.get("desc", "")
            src   = fm.get("source", "")
            typ   = fm.get("type", "")
            meta  = "  |  ".join(x for x in [typ, src] if x)
            desc_part = f" — {desc}" if desc else ""
            meta_part = f"  `{meta}`" if meta else ""
            lines.append(f"- [{title}](summaries/{p.name}){desc_part}{meta_part}")
        lines.append("")

    if concepts:
        lines.append("## Concepts")
        lines.append("")
        for p in concepts:
            fm = _extract_frontmatter(p)
            title = fm.get("title") or p.stem.replace("-", " ").title()
            desc  = fm.get("desc", "")
            # truncate desc at 80 chars for index readability
            if len(desc) > 80:
                desc = desc[:77].rstrip() + "…"
            srcs  = fm.get("sources", "")
            desc_part = f" — {desc}" if desc else ""
            srcs_part = f"  `src:{srcs}`" if srcs else ""
            lines.append(f"- [{title}](concepts/{p.name}){desc_part}{srcs_part}")
        lines.append("")

    (wiki / "_index.md").write_text("\n".join(lines), encoding="utf-8")
