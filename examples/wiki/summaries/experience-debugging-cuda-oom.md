---
title: "Experience: Debugging CUDA OOM in Large Model Training"
source: "raw/experience-debugging-cuda-oom.md"
compiled: "2026-04-03"
visibility: private
---

# Debugging CUDA OOM in Large Model Training

Practical lessons from debugging GPU memory exhaustion during 7B+ parameter model training on A100 80GB. Root causes include activation memory blowup (long sequences + large batches), optimizer state overhead (Adam stores 2 extra parameter copies, ~84GB for 7B fp32), memory fragmentation, and hidden tensor copies.

Key debugging tools: `torch.cuda.memory_summary()`, `max_memory_allocated()`, and `torch.profiler`. Effective solutions: gradient checkpointing (2-3x memory reduction, ~20% compute overhead), DeepSpeed ZeRO Stage 2/3, mixed precision (bf16), and reducing batch size with gradient accumulation.

## Related Concepts

- [[gpu-memory-optimization]]
- [[transformer]]
- [[mixed-precision-training]]
- [[deepspeed]]
