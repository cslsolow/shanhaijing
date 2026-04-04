"""Lint workflow — health check on the wiki."""

import re
from pathlib import Path

from . import state


def run(kb_path: str) -> list[dict]:
    wiki = Path(kb_path) / "wiki"
    issues = []

    # All wiki article paths
    all_articles = {p.relative_to(wiki).as_posix() for p in wiki.rglob("*.md")}

    # 1. Broken wikilinks
    wikilink_re = re.compile(r"\[\[([^\]]+)\]\]")
    for p in wiki.rglob("*.md"):
        content = p.read_text(encoding="utf-8")
        for match in wikilink_re.finditer(content):
            slug = match.group(1)
            candidates = [f"concepts/{slug}.md", f"summaries/{slug}.md"]
            if not any(c in all_articles for c in candidates):
                issues.append({
                    "type": "broken_wikilink",
                    "file": str(p.relative_to(wiki)),
                    "link": slug,
                })

    # 2. Orphaned articles (not in _index and not linked from anywhere)
    index_path = wiki / "_index.md"
    index_content = index_path.read_text(encoding="utf-8") if index_path.exists() else ""
    link_re = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
    indexed = {m.group(2) for m in link_re.finditer(index_content)}
    for p in wiki.rglob("*.md"):
        rel = p.relative_to(wiki).as_posix()
        if rel.startswith("_"):
            continue
        if rel not in indexed:
            issues.append({"type": "orphaned_article", "file": rel})

    # 3. Uncompiled raw files
    st = state.load(kb_path)
    tracked = set(st.get("files", {}).keys())
    raw = Path(kb_path) / "raw"
    for p in raw.rglob("*.md"):
        rel = str(p.relative_to(kb_path))
        if rel not in tracked:
            issues.append({"type": "uncompiled_raw", "file": rel})

    # 4. Stale summaries
    for rel, info in st.get("files", {}).items():
        p = Path(kb_path) / rel
        if p.exists():
            from . import state as s
            if s.file_hash(p) != info.get("hash", ""):
                issues.append({"type": "stale_summary", "file": rel})

    # 5. Thin articles (<50 words)
    for p in wiki.rglob("*.md"):
        content = p.read_text(encoding="utf-8")
        words = len(content.split())
        if words < 50:
            issues.append({
                "type": "thin_article",
                "file": str(p.relative_to(wiki)),
                "words": words,
            })

    return issues
