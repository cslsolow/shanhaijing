---
title: "Transformer"
compiled: "2026-04-03"
visibility: public
---

# Transformer

A neural network architecture based entirely on self-attention mechanisms, introduced by Vaswani et al. (2017). Replaces recurrence and convolutions with multi-head attention over encoder-decoder stacks, enabling full parallelization during training and effective modeling of long-range dependencies.

The Transformer is the foundational architecture behind virtually all modern large language models (GPT, BERT, T5, LLaMA) and has expanded to vision (ViT), audio (Whisper), and multimodal domains. Its scaling properties — smooth power-law improvement with increased parameters, data, and compute — make it the default choice for large-scale AI systems.

## Sources

- [[summaries/paper-attention-is-all-you-need]] — Introduces the Transformer architecture
- [[summaries/paper-scaling-laws]] — Studies how Transformer LM performance scales with size, data, and compute
- [[summaries/experience-debugging-cuda-oom]] — Practical debugging of memory issues in large Transformer training

## Related Concepts

- [[self-attention]]
- [[multi-head-attention]]
- [[scaling-laws]]
- [[positional-encoding]]
