---
title: "Self-Attention"
compiled: "2026-04-03"
visibility: public
---

# Self-Attention

A mechanism where each element in a sequence computes attention weights over all other elements in the same sequence, producing context-aware representations. Each position queries all positions (including itself) using learned Q/K/V projections, then aggregates values weighted by softmax(QK^T/sqrt(d)).

Self-attention's key advantage over recurrence: it connects any two positions in O(1) sequential operations (vs O(n) for RNNs), enabling parallel computation and better gradient flow for long-range dependencies. The quadratic cost O(n^2) in sequence length is its primary limitation, driving research into efficient attention variants.

## Sources

- [[summaries/paper-attention-is-all-you-need]] — Introduces self-attention as the core mechanism of the Transformer

## Related Concepts

- [[transformer]]
- [[multi-head-attention]]
- [[positional-encoding]]
