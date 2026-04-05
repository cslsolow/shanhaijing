<div align="center">
  <img src="logo.svg" width="120" alt="山海经">

  # Shanhaijing 山海经

  Federated knowledge network. Compile personal knowledge bases, share publicly, discover and query others' knowledge.

  ![License](https://img.shields.io/badge/license-MIT-gray?style=flat-square)
  ![Python](https://img.shields.io/badge/python-3.11+-blue?style=flat-square)
  ![Phase](https://img.shields.io/badge/phase-1%20core-brightgreen?style=flat-square)
</div>

---

## Vision

Everyone's brain is different. Your reading, work experience, research, and life lessons are unique knowledge. But they're isolated in your head.

**Shanhaijing** is a system to:
1. **Extract** your knowledge from raw documents (papers, blogs, notes, personal experience)
2. **Structure** it as a queryable wiki with concepts, summaries, and cross-references
3. **Share** publicly (or keep private) in a decentralized registry
4. **Discover** and **query** other people's knowledge as if it were your own

Imagine searching across thousands of people's brains — asking a question and getting answers backed by everyone's collective experience.

## Two Ways to Use

Every feature works in both modes. Choose based on your setup:

### Mode 1: Python CLI (private API)

Uses your own API key configured in `.shj.config.json`. Supports Anthropic, OpenAI-compatible endpoints (Ollama, DeepSeek, etc.).

```bash
uv run main.py compile ./myknowledge
uv run main.py query "What is attention?" --kb ./myknowledge
uv run main.py distill "attention and memory retrieval are the same thing" --kb ./myknowledge
uv run main.py sync --kb ./myknowledge
uv run main.py dream ./myknowledge
uv run main.py dream ./myknowledge --schedule   # nightly cron at 23:00
```

### Mode 2: Claude Code Skill (`/shj`)

Uses Claude Code's own Anthropic session — no API key setup needed.

```
/shj compile ./myknowledge
/shj query "What is attention?"
/shj dream ./myknowledge
```

Both modes produce identical output. Pick the one that fits your workflow.

## Features

### Compile

Incrementally turn raw docs into a structured wiki.

```bash
uv run main.py compile ./myknowledge
```

- **Incremental**: SHA-256 hashing tracks changes, only reprocesses delta
- **Auto-summarization**: LLM generates 150-400 word summaries per document
- **Concept extraction**: Discovers 2-8 key concepts per document
- **Semantic merging**: LLM deduplicates concepts across documents — `"transformer model"` merges into `"transformer"` rather than creating a duplicate
- **Wikilinks**: Concept articles with `[[cross-references]]`, Obsidian-compatible

### Distill

Turn any fragment into a structured knowledge entry:

```bash
uv run main.py distill "attention and memory retrieval are fundamentally the same" --kb ./myknowledge
# or from stdin
echo "my thought here" | uv run main.py distill --kb ./myknowledge
```

The LLM structures it into a titled, linked wiki entry and auto-compiles it in.

### Sync

Pull from external sources into `raw/` automatically:

```bash
uv run main.py sync --kb ./myknowledge          # all configured sources
uv run main.py sync --source zotero --kb ./myknowledge
uv run main.py sync --source notion --kb ./myknowledge
```

**Zotero** — papers with notes → abstract + notes; papers without notes + PDF → full PDF text via LLM; otherwise abstract only.

**Notion** — pages and databases, incremental (skips unchanged pages).

### Query

Lightweight retrieval without vector DB:

```bash
uv run main.py query "What did I learn about transformers?" --kb ./myknowledge
```

LLM reads the summary index (~10K tokens), selects 3-7 relevant articles, synthesizes an answer with `[[wikilink]]` citations.

### Dream

Every night, the knowledge base dreams. It picks concepts that rarely appear together (high friction), then runs a multi-round LLM evolution: each round adds one more concept and rewrites the previous dream to incorporate it, occasionally "forgetting" a prior claim. The result is a chain of drafts culminating in a final essay that surfaces hidden connections across your knowledge.

```bash
uv run main.py dream ./myknowledge              # run immediately
uv run main.py dream ./myknowledge --schedule   # register cron at 23:00 local time
uv run main.py dream ./myknowledge --unschedule # remove cron
```

Output in `dream/YYYY-MM-DD/`:
- `v1-<concept>.md`, `v2-<concept>.md`, … — per-round evolution
- `final.md` — last evolved version with evolution log

Each run picks a random angle (contrarian, analogy, hypothesis, genealogy, critique) and a random seed, so every dream is different.

### Lint

Health check:

```bash
uv run main.py lint ./myknowledge
```

Finds broken wikilinks, orphaned articles, uncompiled raw files, stale summaries, concept gaps.

## Install & Quick Start

```bash
git clone https://github.com/cslsolow/shanhaijing.git
cd shanhaijing
uv sync
```

**Option A — Anthropic API:**
```bash
export ANTHROPIC_API_KEY=sk-ant-...
uv run main.py init ./myknowledge
```

**Option B — OpenAI-compatible (Ollama, DeepSeek, etc.):**
```bash
uv run main.py config ./myknowledge --set provider=openai base_url=http://localhost:11434/v1 model=llama3
```

**Option C — Claude Code (no API key needed):**
```
/shj init ./myknowledge
```

Then drop files in `raw/` and compile:
```bash
cp my-notes.md ./myknowledge/raw/
uv run main.py compile ./myknowledge
uv run main.py query "What did I write about?" --kb ./myknowledge
```

## Model Flexibility

| Provider | API Key env | Notes |
|----------|-------------|-------|
| **Anthropic** | `ANTHROPIC_API_KEY` | Default: claude-haiku-4-5 |
| **OpenAI** | `OPENAI_API_KEY` | gpt-4o, gpt-4 turbo, etc. |
| **Ollama** (local) | not required | `base_url=http://localhost:11434/v1` |
| **DeepSeek** | `OPENAI_API_KEY` | Private endpoints supported |

Configure:
```bash
uv run main.py config ./myknowledge --set provider=anthropic model=claude-haiku-4-5
```

Config is stored in `.shj.config.json` (git-ignored).

## Output Format

Standard markdown + `[[wikilinks]]` — fully compatible with Obsidian.

**Open in Obsidian:** point it to `wiki/` inside your KB (`Open folder as vault → myknowledge/wiki/`). Graph view, backlinks, and full-text search work out of the box.

## Example

`examples/` contains a sample KB compiled from a research paper. Try it:

```bash
uv run main.py query "What is agent-computer interface?" --kb ./examples
```

## Roadmap

| Phase | Focus | Status |
|-------|-------|--------|
| **1** | Core compile/query/lint + distill + sync (Notion/Zotero) + dream | ✅ Done |
| **2** | Public/private separation, publish command, static site export | Q2 2026 |
| **3** | Federated registry, cross-KB querying, global discovery | Q3 2026+ |

## Project Philosophy

- **No vector DB, no RAG**: LLM reads the index directly — simpler, cheaper, transparent
- **Incremental**: Only reprocess changed files
- **Obsidian-native**: `wiki/` opens as a vault out of the box
- **Decentralized**: Each person owns their KB; opt-in sharing
- **Your knowledge, not the paper's**: `raw/` should reflect your understanding — notes, highlights, distilled thoughts

## Name

山海经 (*Shānhǎi Jīng*, "Classic of Mountains and Seas") — an ancient Chinese encyclopedia. This project is a modern encyclopedia of human knowledge, compiled by LLMs and owned by everyone.

## License

MIT

---

**Start with your own knowledge. End with everyone's knowledge.**
