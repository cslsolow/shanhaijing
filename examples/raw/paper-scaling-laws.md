---
title: "Scaling Laws for Neural Language Models"
source: "https://arxiv.org/abs/2001.08361"
ingested: "2026-04-03"
visibility: public
type: paper
---

# Scaling Laws for Neural Language Models

Kaplan et al. (2020) empirically study how the performance of Transformer language models scales as a function of model size (N), dataset size (D), and compute budget (C).

## Key Findings

- **Power-law relationships**: Loss scales as a power law with each of N, D, and C when the other two are not bottlenecked
- **Smooth scaling**: Performance improves predictably over many orders of magnitude
- **Larger models are more sample-efficient**: Reaching the same performance level requires fewer data points as model size increases
- **Optimal allocation**: Given a fixed compute budget, it's better to train a larger model for fewer steps than a smaller model for more steps
- **Data requirements grow sublinearly** with model size

## Implications

- Enables planning of training runs before execution: predict final loss from early training dynamics
- Suggests that scaling up is a reliable path to improved performance (no diminishing returns observed within tested range)
- Influenced the development philosophy behind GPT-3 and subsequent large-scale models
- Opened the field of "scaling laws" as a research area in its own right

## Limitations Noted

- Experiments limited to Transformer LMs; generalization to other architectures uncertain
- Does not account for data quality, only quantity
- Chinchilla (2022) later showed the compute-optimal frontier differs from what this paper suggested
