---
title: "Scaling Laws for Neural Language Models"
source: "raw/paper-scaling-laws.md"
compiled: "2026-04-03"
visibility: public
---

# Scaling Laws for Neural Language Models

Kaplan et al. empirically demonstrate that Transformer language model loss follows power-law relationships with model size (N), dataset size (D), and compute budget (C). Performance improves smoothly and predictably over many orders of magnitude, and larger models are more sample-efficient.

The key practical implication: given a fixed compute budget, training a larger model for fewer steps outperforms training a smaller model longer. This enables predicting final loss from early training dynamics, fundamentally changing how training runs are planned.

The paper directly influenced GPT-3's development and launched "scaling laws" as a research subfield. Later work (Chinchilla, 2022) refined the compute-optimal frontier, showing the original paper overweighted model size relative to data size.

## Related Concepts

- [[scaling-laws]]
- [[transformer]]
- [[compute-optimal-training]]
