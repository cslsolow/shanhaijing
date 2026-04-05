---
title: Incremental Compile
visibility: private
type: concept
desc: A compilation strategy where only new or changed files are processed. Files are identified by SHA-256 hash; the previous compilation…
sources: [summaries/README]
---

# Incremental Compile

A compilation strategy where only new or changed files are processed. Files are identified by SHA-256 hash; the previous compilation state is stored in `.wiki_state.json`. On each compile run, hashes are compared to determine the delta (new / changed / deleted). This keeps compile time proportional to change volume, not total knowledge base size, and allows crash recovery.

## Sources

- [[summaries/README]]

## Related Concepts

[[llm-compiled-wiki]] [[personal-knowledge-base]]
