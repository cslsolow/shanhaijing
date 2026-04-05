---
title: "Shanhaijing — LLM-compiled Personal Knowledge Base"
source: "raw/README.md"
ingested: "2026-04-03"
visibility: private
type: note
desc: "LLM-compiled PKB with incremental compile, no vector DB, Obsidian-compatible wikilinks."
---

# Shanhaijing — LLM-compiled Personal Knowledge Base

Shanhaijing is a Claude Code skill that turns raw documents into a structured, queryable markdown wiki. The core loop is: **ingest → compile → query**.

## Key Points

- **No vector DB, no RAG**: the LLM reads `_index.md` directly and selects relevant articles to fetch, keeping the architecture simple and transparent.
- **Incremental compile**: files are hashed (SHA-256); only new or changed files are reprocessed. State is persisted in `.wiki_state.json` for crash recovery.
- **Multiple input types**: arxiv URLs, blog URLs, local PDFs, local markdown, or free-text oral knowledge — all normalized to structured markdown in `raw/`.
- **Obsidian-compatible output**: wiki articles use `[[wikilinks]]` and standard frontmatter; open `wiki/` as a vault for graph view and backlinks.
- **Scale**: designed for up to ~500 articles (index fits in one context window).

## Commands

| Command | Purpose |
|---------|---------|
| `init [path]` | Scaffold `raw/`, `wiki/summaries/`, `wiki/concepts/`, `_index.md` |
| `ingest <url\|file>` | Import and structure a source document into `raw/` |
| `compile [path]` | Process delta, generate summaries and concept articles, rebuild index |
| `query "question"` | Answer from wiki with `[[wikilink]]` citations |
| `lint [path]` | Health check: broken links, orphans, stale summaries, concept gaps |

## Roadmap

- Phase 1: Core skill ← current
- Phase 2: public/private separation, `publish` command, static site
- Phase 3: Federated registry, cross-KB linking, global search
- `distill`: convert any input (chat, code, notes) into structured knowledge entries

## Related Concepts

[[llm-compiled-wiki]] [[incremental-compile]] [[wikilinks]] [[personal-knowledge-base]]
