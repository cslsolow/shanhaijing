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

## How It Works

### Phase 1: Personal Knowledge Base (Current)

```
Your raw docs          Your structured wiki
  papers.md       →      _index.md (searchable)
  blogs.md        →      summaries/ (per document)
  notes.md        →      concepts/ (auto-extracted)
```

**Three ways to use:**

1. **CLI mode** (no Claude Code required)
   ```bash
   uv run main.py compile ./myknowledge
   uv run main.py query "What is attention?"
   ```

2. **Claude Code skill** (`/shj` commands)
   ```
   /shj compile ./myknowledge
   /shj query "What is attention?"
   ```

3. **Web UI** (streaming, model configuration)
   ```bash
   uv run web/server.py --kb ./myknowledge
   # open http://127.0.0.1:8000
   ```

### Phase 2: Public Registry + Sharing (Near-term)

- Mark articles as `public` or `private`
- Publish your wiki to a static site
- Register your wiki in a central discovery index
- Query multiple wikis at once

### Phase 3: Federated Query Network (Long-term)

- Search across all public wikis in the registry
- Answers pull knowledge from anyone's wiki
- Your concepts are linked and traceable to their sources
- Distributed, no central authority

## Install & Quick Start

```bash
git clone https://github.com/cslsolow/shanhaijing.git
cd shanhaijing
uv sync

# Set up API (Anthropic or any OpenAI-compatible)
export OPENAI_API_KEY=sk-...

# Initialize knowledge base
uv run main.py init ./myknowledge

# Ingest some documents (future: /shj ingest)
cp ./my-research-notes.md ./myknowledge/raw/

# Compile into wiki
uv run main.py compile ./myknowledge

# Query
uv run main.py query "What did I learn about transformers?" --kb ./myknowledge
```

## Features

### Compile

- **Incremental processing**: SHA-256 hashing tracks changes, only re-compiles delta
- **Auto-summarization**: LLM generates 150-400 word summaries per document
- **Concept extraction**: Auto-discovers 2-8 key concepts per document
- **Cross-references**: Generates concept articles with `[[wikilinks]]`
- **State tracking**: `.wiki_state.json` enables crash recovery

### Query

- **Lightweight retrieval**: LLM reads summary index only (~10K tokens)
- **Selective reading**: Pulls 3-7 relevant full articles on-demand
- **Citation tracking**: Answers include `[[wikilink]]` references to sources
- **Streaming output**: Real-time token delivery

### Model Flexibility

| Provider | API Key env | Notes |
|----------|-------------|-------|
| **Anthropic** | `ANTHROPIC_API_KEY` | Default: claude-haiku-4-5 |
| **OpenAI** | `OPENAI_API_KEY` | gpt-4o, gpt-4 turbo, etc. |
| **Ollama** (local) | not required | `base_url=http://localhost:11434/v1` |
| **DeepSeek** | `OPENAI_API_KEY` | Private endpoints supported |

Configure via CLI or Web UI settings panel. Config file (`.shj.config.json`) is git-ignored.

## Output Format

Standard markdown + `[[wikilinks]]` — fully compatible with Obsidian. Open `wiki/` as a vault for:
- Graph visualization of concepts
- Backlink navigation
- Full-text search
- Note-taking

## Example

`examples/` contains a sample knowledge base compiled from a research paper on SWE-agent. Query it:

```bash
uv run main.py query "What is agent-computer interface?" --kb ./examples
```

## Project Philosophy

- **No vector DB, no RAG**: LLM reads the index directly — simpler, cheaper, transparent
- **Incremental**: Only reprocess changed files
- **Obsidian-native**: Open `wiki/` as a vault out of the box
- **Decentralized**: Each person owns their knowledge base; opt-in sharing
- **Portable**: Markdown everywhere — no lock-in

## Roadmap

| Phase | Focus | Timeline |
|-------|-------|----------|
| **1** | Core skill + direct API mode + Web UI | ✅ Done |
| **2** | Public/private separation, publish command, static site export | Q2 2026 |
| **3** | Federated registry, cross-KB querying, global discovery | Q3 2026+ |

## Future: Federated Knowledge Network

```
Your Wiki          Alice's Wiki        Bob's Wiki
  (public)           (public)            (public)
      ↓                  ↓                   ↓
   [Central Registry] ← auto-register
      ↓
  [Global Query]
  "What is self-attention?"
      ↓
  Returns answers from all three wikis with citations
```

## Name

山海经 (*Shānhǎi Jīng*, "Classic of Mountains and Seas") — an ancient Chinese encyclopedia. This project is a modern, collaborative encyclopedia of human knowledge, compiled by LLMs and owned by everyone.

## License

MIT

---

**Start with your own knowledge. End with everyone's knowledge.**
