# Larger Qwen27B context with less unused VRAM — November 1, 2026

Selected HyperQwen at 86,016 tokens (84 Ki, +75% over 49,152) and SGLang at 55,296 (54 Ki, +12.5%). The live router and DSH use the selected limits. Both passed one actual short DSH read-tool call with matching contents and owned unload. HyperQwen uses a 768 MiB INT4 KV pool per GPU and reports 88,931 native KV tokens. SGLang uses BF16 KV with 55,296 tokens on each rank and bounded rank-memory targets of 11,712/9,152 MiB. Engine binaries, weight placement, quantization and other profiles are unchanged.

The 512 MiB free-VRAM floor and all other guards remain. Approximate 0.5-second samples cover the short tool request, including prompt processing. These samples do not guarantee that every instantaneous peak was captured. No full-window quality, long-context peak-memory, sustained or repeated-reload suite ran. SGLang's remaining margin above the floor is narrow; future heavier requests remain subject to the guard.

| Engine | Context | GPU0 used/free MiB at readiness | GPU1 used/free MiB at readiness | Minimum sampled free GPU0/GPU1 MiB | Prefill tok/s | Engine TTFT s | Native decode tok/s |
|---|---:|---:|---:|---:|---:|---:|---:|
| qwen27b-hyperqwen | 86,016 | 8,719 / 3,245 | 9,248 / 679 | 3,245 / 679 | 2372.84 | 2.467 | 65.600 |
| qwen27b-sglang | 55,296 | 11,314 / 651 | 8,554 / 1,372 | 533 / 1,274 | 2508.85 | 2.465 | 60.091 |

SGLang 57,344 was rejected despite a successful tool call: readiness free VRAM was 587/1,308 MiB, but a transient sample reached 469 MiB on GPU0. The restored and then smaller 55,296 allocation passed with 533 MiB minimum. The rejected attempt is retained as evidence, not treated as a selected setting. HyperQwen had 679 MiB minimum on GPU1. Readiness figures are total card memory including desktop/driver use, rather than model-only allocation.

Each benchmark is one short call, excluding loading and follow-up answer. Both selected calls report zero reused prompt tokens. HyperQwen and SGLang use engine TTFT counters and native request decode metrics. Larger advertised windows are capacity-backed calculated allocations, not full-context quality qualifications. Shared base weights remain 15.79 decimal GB on SATA.

[Numeric evidence](validation-results/20261101-qwen-larger-context.json). [Previous 48K setting](QWEN-48K-CONTEXT-20261101.md) remains historical evidence.
