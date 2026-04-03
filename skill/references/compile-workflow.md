# Compile Workflow — Detailed Algorithm

## Step 1: Load State

Read `.wiki_state.json`. If missing or corrupt, treat as empty state (full recompile). Print warning if state was reset.

Parse into working structure:
```json
{
  "version": 1,
  "lastCompiled": "ISO timestamp",
  "files": { "<relative-path>": { "hash": "...", "concepts": [...], "lastCompiled": "..." } },
  "concepts": { "<slug>": { "sources": [...], "lastUpdated": "..." } }
}
```

## Step 2: Scan Raw Directory

1. `Glob raw/**/*.md` to get all markdown files
2. For each file, compute hash: `Bash: shasum -a 256 raw/file.md | cut -d' ' -f1`
3. Build a `currentFiles` map: `{ "<relative-path>": "<hash>" }`
4. Log non-markdown files found in raw/ (skipped)

## Step 3: Compute Delta

- **new**: in `currentFiles` but not in state
- **changed**: in both but hash differs
- **deleted**: in state but not in `currentFiles`
- **unchanged**: in both, hash matches → skip

Print delta summary before processing.

## Step 4: Process New/Changed Files

For each file in `new` + `changed`:

1. Read the raw file
2. If the file exceeds ~8000 words, read in chunks using offset/limit and accumulate understanding
3. Generate a summary article (150-400 words):
   - Title (from document)
   - Key points
   - Methodology/approach (if applicable)
   - Main findings/arguments
   - Relevance to the knowledge base
   - End with `## Related Concepts` section listing `[[concept-name]]` wikilinks
4. Extract concept list: 2-8 key concepts/topics/entities as lowercase-hyphenated slugs (e.g., "attention mechanism" → `attention-mechanism`)
5. Write summary to `wiki/summaries/<slug>.md` where slug is derived from filename
6. Record in state: `{ "hash": "...", "concepts": [...], "lastCompiled": "ISO timestamp" }`

### Slug Convention for Nested Paths

- `raw/paper.md` → `wiki/summaries/paper.md`
- `raw/subdir/paper.md` → `wiki/summaries/subdir--paper.md`

State keys always use the relative path from `raw/` (e.g., `subdir/paper.md`).

## Step 5: Handle Deleted Files

- Remove corresponding `wiki/summaries/<slug>.md`
- Remove from state `files` map
- Update state `concepts` map: remove deleted file from each concept's `sources` list
- Do NOT auto-delete concept articles (they may be cross-referenced by other summaries)
- Concept articles with zero sources will be flagged by lint

## Step 6: Generate/Update Concept Articles

1. Collect all concepts across all files in state (not just the delta)
2. For each concept that has no `wiki/concepts/<concept>.md`: generate full article
   - 100-300 word explanation
   - `## Sources` section listing `[[summaries/<file>]]` for every raw doc that mentions this concept
   - `## Related Concepts` section listing `[[other-concept]]` wikilinks
3. For existing concept articles where the source list changed: read existing article, update only the `## Sources` section using Edit tool. Preserve the explanation text (it accumulates knowledge across compiles)
4. Update state `concepts` map

## Step 7: Rebuild Index

Generate `wiki/_index.md` from scratch every compile. Structure:

```markdown
# Knowledge Base Index

Last compiled: <ISO timestamp>
Articles: <N> summaries, <M> concepts

## Summaries
- [paper-attention](summaries/paper-attention.md) — One-sentence description
- [blog-scaling-laws](summaries/blog-scaling-laws.md) — One-sentence description

## Concepts
- [attention-mechanism](concepts/attention-mechanism.md) — One-sentence description
- [transformer](concepts/transformer.md) — One-sentence description
```

One-sentence descriptions must be information-dense — they are what the LLM reads during query to decide which articles to fetch. Extract from the first paragraph of each article.

## Step 8: Write State

Write updated `.wiki_state.json` to disk.

## Step 9: Report

Print summary:
```
Compile complete:
  New:     3 files
  Changed: 1 file
  Deleted: 0 files
  Concepts added: 5
  Total:   12 summaries, 18 concepts
```

## Batching for Large Deltas

If more than 20 files are new/changed:
1. Sort files alphabetically for deterministic order
2. Process in batches of 10
3. Write `.wiki_state.json` after each batch completes
4. This provides crash recovery — if session is interrupted, only the current batch needs reprocessing
5. Rebuild index once at the end (not after each batch)

## Handling Large Raw Files

If a raw file exceeds ~8000 words:
1. Read first 8000 words with `Read` using limit parameter
2. Generate partial summary
3. Read next chunk
4. Merge understanding and refine summary
5. Continue until file is fully read
6. This is guidance, not a hard cutoff — use judgment
