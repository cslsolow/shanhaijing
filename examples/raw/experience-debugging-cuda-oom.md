---
title: "Experience: Debugging CUDA OOM in Large Model Training"
source: "personal"
ingested: "2026-04-03"
visibility: private
type: experience
---

# Debugging CUDA OOM in Large Model Training

Hard-won lessons from repeatedly running out of GPU memory training 7B+ parameter models on A100 80GB nodes.

## Common Causes

1. **Activation memory blowup**: Long sequences with large batch sizes. Activation checkpointing trades compute for memory but doesn't eliminate the problem for very long contexts.
2. **Optimizer state**: Adam stores 2 extra copies of parameters (momentum + variance). For a 7B model in fp32, that's ~84GB just for optimizer state.
3. **Fragmentation**: PyTorch's caching allocator can fragment GPU memory. `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` helps on recent versions.
4. **Hidden copies**: `.to(device)` inside training loops, gradient accumulation without `no_sync()`, or accidental double storage of parameters.

## Debugging Checklist

- `torch.cuda.memory_summary()` before and after each training step
- `torch.cuda.max_memory_allocated()` to find peak usage
- Profile with `torch.profiler` to find where memory spikes
- Check for tensors not being freed: `gc.collect(); torch.cuda.empty_cache()`

## Solutions That Worked

- **Gradient checkpointing** (activation checkpointing): 2-3x memory reduction for ~20% compute overhead
- **DeepSpeed ZeRO Stage 2/3**: Shard optimizer state and optionally parameters across GPUs
- **Mixed precision (bf16)**: Halves parameter and activation memory
- **Reduce batch size + gradient accumulation**: Obvious but often the fastest fix
