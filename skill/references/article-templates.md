# Article Templates

## Summary Article

Generated during compile for each raw document.

```markdown
---
title: "<Document Title>"
source: "raw/<filename>.md"
compiled: "<YYYY-MM-DD>"
visibility: <inherited from raw file>
---

# <Document Title>

<150-400 word summary covering:>
- What the document is about
- Key points, methodology, or approach
- Main findings, arguments, or insights
- Why it matters / relevance to the knowledge base

## Related Concepts

- [[concept-a]]
- [[concept-b]]
- [[concept-c]]
```

### Guidelines

- Lead with the most important insight, not background
- Be specific: include names, numbers, concrete claims
- If the source is a paper: mention the method and key results
- If the source is a blog: capture the author's main argument
- If the source is notes: synthesize the key takeaways

## Concept Article

Generated when a new concept is extracted. Updated incrementally.

```markdown
---
title: "<Concept Name>"
compiled: "<YYYY-MM-DD>"
visibility: public
---

# <Concept Name>

<100-300 word explanation covering:>
- What it is (definition)
- Why it matters (significance)
- Key properties or characteristics
- Common usage or context in the knowledge base

## Sources

- [[summaries/paper-attention]] — Introduces the concept in the context of Transformer architecture
- [[summaries/blog-scaling-laws]] — Discusses how it relates to scaling behavior

## Related Concepts

- [[other-concept-a]]
- [[other-concept-b]]
```

### Guidelines

- Write as if explaining to a knowledgeable peer (not a beginner)
- The explanation section is preserved across compiles — write it well the first time
- Only the Sources section is updated during incremental compiles
- Related Concepts should link to actually existing concept articles
- Default visibility for concepts is `public` (concepts are generally shareable)

## Master Index (_index.md)

Rebuilt from scratch every compile.

```markdown
# Knowledge Base Index

Last compiled: <ISO timestamp>
Articles: <N> summaries, <M> concepts

## Summaries

- [paper-attention](summaries/paper-attention.md) — Introduces Transformer architecture using self-attention, eliminating recurrence
- [blog-scaling-laws](summaries/blog-scaling-laws.md) — Analysis of neural scaling laws across model size, data, and compute

## Concepts

- [attention-mechanism](concepts/attention-mechanism.md) — Core mechanism for computing weighted representations of input sequences
- [transformer](concepts/transformer.md) — Neural architecture based on self-attention, dominant in NLP and beyond
```

### Guidelines

- One-sentence descriptions must be information-dense
- They serve as the retrieval signal during query — the LLM reads these to decide which articles to fetch
- Avoid generic descriptions like "A paper about transformers" — instead: "Introduces the Transformer architecture, replacing recurrence with multi-head self-attention and positional encoding"
- Sort summaries alphabetically
- Sort concepts alphabetically
- Use relative markdown links (not wikilinks) in the index for broader compatibility
