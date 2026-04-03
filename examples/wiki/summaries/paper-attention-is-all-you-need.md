---
title: "Attention Is All You Need"
source: "raw/paper-attention-is-all-you-need.md"
compiled: "2026-04-03"
visibility: public
---

# Attention Is All You Need

Vaswani et al. introduce the Transformer, replacing recurrence and convolutions entirely with self-attention for sequence transduction. The model uses multi-head attention across 6-layer encoder-decoder stacks with residual connections and layer normalization. Positional information is injected via sinusoidal encodings.

The Transformer achieves 28.4 BLEU on EN-DE and 41.8 BLEU on EN-FR translation, training significantly faster than recurrent alternatives due to full parallelizability. This architecture became the foundation for GPT, BERT, T5, ViT, and virtually all modern large-scale models across language, vision, and multimodal domains.

The key insight is that self-attention can model long-range dependencies without the sequential bottleneck of RNNs, enabling both better performance and more efficient training at scale.

## Related Concepts

- [[self-attention]]
- [[transformer]]
- [[multi-head-attention]]
- [[positional-encoding]]
