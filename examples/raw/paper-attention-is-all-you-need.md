---
title: "Attention Is All You Need"
source: "https://arxiv.org/abs/1706.03762"
ingested: "2026-04-03"
visibility: public
type: paper
---

# Attention Is All You Need

Vaswani et al. (2017) introduce the Transformer, a sequence transduction model based entirely on attention mechanisms, dispensing with recurrence and convolutions.

## Key Contributions

- **Self-attention** as the sole mechanism for computing representations of input and output sequences
- **Multi-head attention** allowing the model to attend to information from different representation subspaces at different positions
- **Positional encoding** using sinusoidal functions to inject sequence order information without recurrence
- **Encoder-decoder architecture** with 6 layers each, using residual connections and layer normalization

## Results

- Achieves 28.4 BLEU on English-to-German and 41.8 BLEU on English-to-French translation (SOTA at time of publication)
- Trains significantly faster than recurrent or convolutional models due to parallelizability
- The architecture generalizes well beyond translation to other sequence tasks

## Significance

The Transformer architecture became the foundation for virtually all modern large language models (GPT, BERT, T5, etc.) and has expanded to vision (ViT), audio, and multimodal domains. Self-attention's ability to model long-range dependencies without the sequential bottleneck of RNNs was the key breakthrough.
