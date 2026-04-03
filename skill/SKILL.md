---
name: shanhaijing
description: This skill should be used when the user says "/shanhaijing", "shj", "knowledge base", "compile wiki", "query my notes", "ingest this", "lint my wiki", or wants to build, query, or maintain a personal markdown knowledge base compiled by an LLM. Reads raw source documents and incrementally compiles a structured wiki with summaries, concept articles, cross-references, and a master index. Supports ingesting URLs, PDFs, and markdown files.
---

# Shanhaijing — Personal Knowledge Base Compiler

Incrementally compile raw documents into a structured, LLM-readable markdown wiki with cross-references and a queryable index. No vector DB, no RAG — read the index directly.

## When to Activate

- User invokes `/shanhaijing` or `/shj` with any sub-command
- User mentions compiling, querying, or linting a knowledge base or wiki
- User wants to ingest a URL, PDF, or markdown file into their knowledge base
- User asks a question referencing "my notes", "my wiki", or "my knowledge base"

## Sub-commands

| Command | Usage | Purpose |
|---------|-------|---------|
| `init` | `/shj init [path]` | Create directory scaffold + empty state |
| `ingest` | `/shj ingest <url\|file>` | Import source → preprocess → LLM structurize → store in raw/ |
| `compile` | `/shj compile [path]` | Process new/changed raw docs, update wiki/ |
| `query` | `/shj query "question"` | Answer question from wiki with citations |
| `lint` | `/shj lint [path]` | Health check: broken links, orphans, gaps |

Default path is the current working directory. Look for `raw/` and `wiki/` relative to that path.

## Directory Layout

The skill operates on this structure:

```
<base>/
├── raw/                    # User's source documents (read-only for compile)
│   ├── paper-attention.md
│   ├── blog-scaling-laws.md
│   └── notes-2024-03.md
├── wiki/                   # LLM-managed output (user should not edit)
│   ├── _index.md           # Master index: one-line description per article
│   ├── summaries/          # One summary per raw file
│   │   ├── paper-attention.md
│   │   └── blog-scaling-laws.md
│   └── concepts/           # Auto-extracted concept articles
│       ├── transformer.md
│       └── attention-mechanism.md
└── .wiki_state.json        # Compilation state tracker
```

## Init Workflow

1. Create directories: `raw/`, `wiki/summaries/`, `wiki/concepts/`
2. Write empty `wiki/_index.md` with header
3. Write initial `.wiki_state.json` with `{"version": 1, "files": {}, "concepts": {}}`
4. Print confirmation

## Ingest Workflow

Determine input type and preprocess into clean markdown in `raw/`:

1. **URL (arxiv)**: Detect arxiv URL → run `scripts/pdf_to_md.py` to download PDF and convert → LLM reads the raw text and restructures into clean markdown → save to `raw/`
2. **URL (blog/webpage)**: Run `scripts/web_clip.py` to extract content → LLM reads and restructures → save to `raw/`
3. **Local PDF**: Run `scripts/pdf_to_md.py` on the file → LLM restructures → save to `raw/`
4. **Local .md**: Copy directly to `raw/`
5. **Personal experience/oral knowledge**: LLM structures the user's input directly into markdown → save to `raw/`

For all types, the LLM is responsible for:
- Cleaning up formatting artifacts
- Adding frontmatter: `title`, `source`, `ingested` date, `visibility: private` (default)
- Ensuring readable structure with headers, lists, code blocks as appropriate

Consult `references/ingest-workflow.md` for detailed per-type instructions.

## Compile Workflow (Overview)

Consult `references/compile-workflow.md` for the full algorithm.

1. Read `.wiki_state.json`
2. Glob `raw/**/*.md`, compute SHA-256 hash via `shasum -a 256`
3. Compare hashes against state → identify new, changed, deleted files
4. For each new/changed file: read it, generate summary (150-400 words), extract 2-8 concept slugs
5. For new concepts: generate concept article. For existing concepts with new sources: update Sources section only
6. Rebuild `wiki/_index.md` from scratch (one line per article with info-dense description)
7. Write updated `.wiki_state.json`
8. Report: N new, N changed, N deleted, N concepts added

Key: process only the delta. Batch in groups of 10 if >20 files changed, writing state after each batch.

## Query Workflow

1. Read `wiki/_index.md` to get the full article inventory (~500 lines ≈ ~10K tokens)
2. From the index, select 3-7 articles most relevant to the question
3. Read those articles
4. Synthesize answer with `[[wikilink]]` citations pointing to wiki articles
5. If insufficient, select additional articles from index (max 2 retrieval rounds)
6. End with a `## Sources` list of articles consulted

## Lint Workflow

1. **Broken wikilinks**: Grep all `[[...]]` in wiki/, verify targets exist
2. **Orphaned articles**: Articles not in `_index.md` and not linked from anywhere
3. **Uncompiled raw files**: Raw files with no entry in `.wiki_state.json`
4. **Stale summaries**: Raw file hash differs from state
5. **Concept gaps**: Concepts referenced by 3+ summaries but no concept article exists
6. **Thin articles**: Articles under 50 words

Output as a structured checklist report.

## Visibility Convention

Every article in `raw/` and `wiki/` has frontmatter:

```yaml
---
visibility: public  # or private (default)
---
```

The LLM sets `visibility: private` by default during ingest. User changes it manually. `/shj publish` (future) exports all public articles to a standalone static wiki.

## Wikilink Convention

- Format: `[[article-name]]` where `article-name` matches filename without `.md`
- Summaries link to concepts; concepts link to other concepts and back to summaries
- `_index.md` uses relative markdown links `[title](summaries/slug.md)` for broader compatibility

## Non-goals and Constraints

- No vector DB, no embeddings, no external services beyond LLM API
- Wiki is LLM-managed; user does not edit wiki/ manually
- Works for up to ~500 articles (index fits in context)
- Non-markdown files in raw/ are logged but skipped during compile
- Images: note existence in summary of co-located .md files

## Additional Resources

### Reference Files

For detailed workflows and schemas, consult:
- **`references/compile-workflow.md`** — Step-by-step compile algorithm with delta computation, concept extraction, index rebuild
- **`references/ingest-workflow.md`** — Per-type ingest instructions, preprocessing details
- **`references/wiki-state-schema.md`** — `.wiki_state.json` JSON schema with field descriptions and example
- **`references/article-templates.md`** — Templates for summary, concept, and index articles

### Scripts

Preprocessing utilities in `scripts/`:
- **`scripts/web_clip.py`** — URL → raw markdown via trafilatura
- **`scripts/pdf_to_md.py`** — PDF → raw markdown via pymupdf4llm
- **`scripts/requirements.txt`** — Python dependencies
