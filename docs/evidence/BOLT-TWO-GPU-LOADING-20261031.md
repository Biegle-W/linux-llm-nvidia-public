# Bolt loading on the RTX 3080 Ti and RTX 3080 — October 31

Bolt passed two fresh normal-router loads on the two-card host after removal of the auxiliary RTX 3060. Both loads passed arithmetic/JSON. The first also passed three-marker retrieval at 7,373 actual input tokens and a complete 32-token SSE stream. The selected context remains 8,192 tokens. Both owned test loads unloaded cleanly.

## Cause and fix

The previous recipe failed on the 10GB RTX 3080 during `gptq_marlin_moe_repack`: a 310MiB allocation had only 191.69MiB free. The desktop now also uses the main GPUs. The adapter now includes Mamba `in_proj` parameters in the existing prefetch offload alongside `experts` and `out_proj`, moving about 2.83GiB more persistent weights per rank to CPU storage. Tensor parallelism remains two; weights, quantization, expert routing and kernels are unchanged. This adds CPU storage and transfers and may reduce generation speed.

An intermediate offload-only trial passed weight repacking but automatic KV-cache allocation consumed the recovered VRAM. The unchanged 512MiB reserve guard stopped it; the 3080 had 331MiB free. That rejection is preserved independently. The final recipe sets `--kv-cache-memory-bytes 1073741824`, bounding KV cache to 1GiB per GPU instead of filling the recovered space. Actual near-window retrieval verifies the existing 8K context still works.

## Validation

Load times were 224.54s and 223.44s. All 325 CPU regression tests passed. 394 swap/pressure guard samples recorded zero violations and zero worker swap. Peak worker memory was 49.75GiB and minimum sampled host availability was 4.86GiB. No cgroup high/max/OOM events occurred.

- NVIDIA GeForce RTX 3080 Ti: minimum sampled free VRAM 5627MiB; maximum temperature 53C.
- NVIDIA GeForce RTX 3080: minimum sampled free VRAM 2708MiB; maximum temperature 51C.

Worker limits remain 56/58GiB; host reserve 2GiB, temperature 82C, GPU reserve 512MiB, swap I/O, pressure and idle600s guards remain active. This is bounded loading and correctness verification, not a throughput benchmark or long stress test. Earlier benchmark observations keep their historical meaning and were not relabeled as results of this recipe.

[Numeric evidence](validation-results/20261031-bolt-two-gpu-loading.json).
