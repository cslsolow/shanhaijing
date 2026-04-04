<div align="center">
  <img src="logo.svg" width="120" alt="山海经">

  # Shanhaijing 山海经

  LLM-compiled personal knowledge base. Ingest raw documents, compile them into a structured markdown wiki, query with natural language.

  ![License](https://img.shields.io/badge/license-MIT-gray?style=flat-square)
  ![Python](https://img.shields.io/badge/python-3.11+-blue?style=flat-square)
  ![Phase](https://img.shields.io/badge/phase-1%20core-brightgreen?style=flat-square)
</div>

---

## What It Does

```
raw/                        wiki/
  paper.md          →         _index.md          (master index)
  blog.md           →         summaries/         (one per raw doc)
  experience.md     →         concepts/          (auto-extracted)
```

- **Ingest**: Feed URLs (blogs, arxiv), PDFs, markdown, or personal experience. LLM converts everything to structured markdown.
- **Compile**: Incrementally build a wiki with summaries, concept articles, cross-references (`[[wikilinks]]`), and a master index.
- **Query**: Ask questions. LLM reads the index, pulls relevant articles, synthesizes answers with citations.
- **Lint**: Health check — broken links, orphaned articles, stale summaries, concept gaps.

No vector DB. No RAG pipeline. The LLM reads `_index.md` directly. Works up to ~500 articles.

## Install

Requires [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/cslsolow/shanhaijing.git
cd shanhaijing
uv sync
```

To also use as a Claude Code skill:

```bash
ln -s $(pwd)/skill ~/.claude/skills/shanhaijing
```

## Usage

### Direct CLI (any model, no Claude Code required)

```bash
export ANTHROPIC_API_KEY=sk-ant-...   # or OPENAI_API_KEY

uv run main.py init ./myknowledge
uv run main.py compile ./myknowledge
uv run main.py query "What is self-attention?" --kb ./myknowledge
uv run main.py lint ./myknowledge
```

Configure model and provider:

```bash
# Use Anthropic (default)
uv run main.py config ./myknowledge --set provider=anthropic model=claude-sonnet-4-5

# Use OpenAI-compatible (Ollama, DeepSeek, etc.)
uv run main.py config ./myknowledge --set provider=openai model=llama3 base_url=http://localhost:11434/v1
```

Config is stored in `<kb>/.shj.config.json`. API keys always come from environment variables.

### Claude Code Skill

```
/shj init ./myknowledge
/shj ingest https://arxiv.org/abs/2405.15793
/shj compile ./myknowledge
/shj query "What is SWE-agent?"
/shj lint ./myknowledge
```

### Web UI

```bash
uv run web/server.py --kb ./myknowledge
# open http://127.0.0.1:8000
```

The web UI calls the model API directly (streaming). Click ⚙ in the sidebar to configure provider/model/base URL.

## How It Works

### Compile

1. Hash all files in `raw/` (SHA-256)
2. Compare with `.wiki_state.json` → find new/changed/deleted
3. For each changed file: generate summary + extract concepts
4. Generate/update concept articles
5. Rebuild `_index.md`
6. Save state

Only processes the delta. State file enables crash recovery.

### Query

1. Read `_index.md` (lightweight — one line per article)
2. LLM selects 3-7 relevant articles
3. Read articles, synthesize answer with `[[wikilink]]` citations

### Model Support

| Provider | Config | API Key env |
|----------|--------|-------------|
| Anthropic | `provider=anthropic` | `ANTHROPIC_API_KEY` |
| OpenAI | `provider=openai` | `OPENAI_API_KEY` |
| Ollama / local | `provider=openai`, `base_url=http://localhost:11434/v1` | not required |
| DeepSeek, etc. | `provider=openai`, `base_url=<endpoint>` | `OPENAI_API_KEY` |

## Output Format

Standard markdown + `[[wikilinks]]`. Open `wiki/` as an Obsidian vault for graph view, backlinks, and search.

## Example

See `examples/` for a sample knowledge base compiled from research papers.

## Roadmap

- [x] Phase 1: Core (init, ingest, compile, query, lint) + Web UI + direct API mode
- [ ] Phase 2: `distill` command (any input → structured knowledge entry), public/private separation, static site export
- [ ] Phase 3: Federated public wiki registry, cross-KB linking, global search

## Name

山海经 (Shānhǎi Jīng, "Classic of Mountains and Seas") — an ancient Chinese encyclopedia of geography, mythology, and natural knowledge.

## License

MIT
