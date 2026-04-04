<div align="center">
  <img src="logo.svg" width="120" alt="山海经">

  # Shanhaijing 山海经

  LLM-compiled personal knowledge base. Ingest raw documents, compile them into a structured markdown wiki, query with natural language.

  ![License](https://img.shields.io/badge/license-MIT-gray?style=flat-square)
  ![Platform](https://img.shields.io/badge/platform-Claude%20Code-8b5cf6?style=flat-square)
  ![Phase](https://img.shields.io/badge/phase-1%20core%20skill-brightgreen?style=flat-square)
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

This is a [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skill. Requires [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/cslsolow/shanhaijing.git
cd shanhaijing
ln -s $(pwd)/skill ~/.claude/.cursor/skills/shanhaijing
uv sync
```

## Usage

In Claude Code:

```
/shanhaijing init                          # create raw/ wiki/ structure
/shanhaijing ingest https://arxiv.org/...  # ingest a paper
/shanhaijing ingest ./notes.md             # ingest a local file
/shanhaijing compile                       # build wiki from raw/
/shanhaijing query "What is self-attention?"
/shanhaijing lint                          # health check
```

Or use the short form: `/shj compile`

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
2. Select 3-7 relevant articles from descriptions
3. Read articles, synthesize answer with `[[wikilink]]` citations
4. Iterative deepening if needed (max 2 rounds)

### Public / Private

Every article has `visibility: public | private` in frontmatter. Default is `private`. Future: `/shj publish` exports public articles to a static site.

Long-term vision: a federated registry where everyone's public wiki is discoverable and cross-linkable.

## Output Format

Standard markdown + `[[wikilinks]]`. Open `wiki/` as an Obsidian vault for the best browsing experience — graph view, backlinks, search all work out of the box.

## Example

See `examples/` for a sample knowledge base with 3 raw documents compiled into a wiki.

## Roadmap

- [ ] Phase 1: Core skill (init, ingest, compile, query, lint) ← **current**
- [ ] Phase 2: Public/private separation, `publish` command, static site generation
- [ ] Phase 3: Federated public wiki registry, cross-KB linking, global search
- [ ] `distill` command: 任意输入（对话、代码、随手记）→ 结构化知识条目，自动合并进 wiki

## Name

山海经 (Shānhǎi Jīng, "Classic of Mountains and Seas") — an ancient Chinese encyclopedia of geography, mythology, and natural knowledge. This project aims to be your personal encyclopedia, compiled by LLMs.

## License

MIT
