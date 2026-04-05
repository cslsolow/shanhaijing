---
title: LLM-Compiled Wiki
visibility: private
type: concept
desc: A knowledge base architecture where an LLM acts as the compiler: it reads raw source documents and outputs structured summaries,…
sources: [summaries/README]
---

# LLM-Compiled Wiki

A knowledge base architecture where an LLM acts as the compiler: it reads raw source documents and outputs structured summaries, concept articles, and a master index. Unlike traditional RAG systems, there are no embeddings or vector databases — the LLM reads the index directly and selects relevant articles by understanding, not vector similarity.

## Sources

- [[summaries/README]]

## Related Concepts

[[incremental-compile]] [[personal-knowledge-base]] [[wikilinks]]
