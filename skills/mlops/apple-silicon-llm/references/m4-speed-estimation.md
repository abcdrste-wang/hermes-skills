# M4 Apple Silicon Speed Estimation

## Methodology

Apple Silicon LLM inference speed is **memory-bandwidth bound** for decode (token generation). The computation is so fast on the Neural Engine / GPU that the bottleneck is how quickly you can stream model weights from unified memory.

### Formula

```
theoretical_max_tok_s = memory_bandwidth / model_size_in_GB
real_world_tok_s = theoretical_max * 0.70~0.90
```

The 0.70-0.90 multiplier accounts for:
- Attention computation overhead (grows with context length)
- PCIe/Metal scheduling overhead
- Other processes competing for bandwidth

### M4 Bandwidth

| Chip | Bandwidth |
|------|----------|
| M4 (base) | 120 GB/s |
| M4 Pro | 273 GB/s |
| M4 Max | 410/546 GB/s |

### Context Length Impact

At longer contexts, KV cache access competes for memory bandwidth:

| Context | Bandwidth hit | Multiplier |
|---------|:------------:|:----------:|
| < 8K | negligible | 0.85-0.90 |
| 32K | small | 0.80-0.85 |
| 64K | moderate | 0.75-0.80 |
| 128K | significant | 0.65-0.75 |

### Worked Example: Qwen 3.5 4B on M4 (base)

```
Model: Qwen 3.5 4B Q4_K_M ≈ 2.4 GB
Bandwidth: 120 GB/s
Theoretical max: 120 / 2.4 = 50 tok/s

At 8K context:  50 * 0.87 ≈ 43 tok/s
At 64K context: 50 * 0.78 ≈ 39 tok/s
```

### KV Cache Memory Formula

```
kv_per_token = 2 * num_layers * num_kv_heads * head_dim * 2_bytes
kv_total = kv_per_token * context_length
```

For Qwen 3.5 4B (estimated: 32 layers, 4 KV heads, 128 head_dim):
```
kv_per_token = 2 * 32 * 4 * 128 * 2 = 65,536 bytes ≈ 64 KB
kv_at_64k = 64 KB * 65536 ≈ 4.2 GB
```

### Real-World Validation (June 2026)

Qwen 2.5 7B forced to 64K (RoPE extension beyond native 32K):
- Speed: 5-10 tok/s (unusable)
- Root cause: RoPE extension + KV cache overflow on 16GB

Qwen 3.5 4B at native 64K (well within native 256K):
- Speed: 35-45 tok/s (estimated, pending validation)
- Expected to be 4-8× faster than the 7B forced case
