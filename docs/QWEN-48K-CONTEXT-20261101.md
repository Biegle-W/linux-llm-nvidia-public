# Qwen27B context increased to 48K — November 1, 2026

HyperQwen increased from 40,960 to 49,152 tokens (+20%); SGLang increased from 32,768 to 49,152 (+50%). All guards remain unchanged, including the 512 MiB free-VRAM floor, host reserve, pressure/swap/temperature checks and P2P proof gate. Both engines passed one actual short DSH read-tool call with matching contents and owned unload through the API-only router. Neither is left loaded. No full-window quality, sustained-generation or repeated-reload suite ran.

HyperQwen's INT4 KV pool increased from 448 to 512 MiB per GPU and reported native capacity for 56,173 tokens. SGLang's BF16 KV increased to 49,152 tokens (0.75 GiB K + 0.75 GiB V per GPU); bounded rank-memory targets increased from 11,008/8,448 to 11,520/8,960 MiB. Both ranks confirmed the full requested allocation. Quantization, GPU weight placement, engine runtimes and other model settings were preserved.

| Engine | Context | GPU0 used/free MiB | GPU1 used/free MiB | Prefill tok/s | Engine TTFT s | Native decode tok/s |
|---|---:|---:|---:|---:|---:|---:|
| HyperQwen-vLLM | 49,152 | 8,457 / 3,507 | 8,986 / 941 | 2370.31 | 2.468 | 65.825 |
| SGLang | 49,152 | 11,122 / 843 | 8,360 / 1,566 | 2496.43 | 2.476 | 60.043 |

VRAM snapshots are total per-card use at model readiness, including desktop/driver use. These are not full-context peak measurements. Single short observations exclude loading and follow-up answer. HyperQwen input/output: 5,826/40 tokens; SGLang: 6,095/39; both report zero cached tokens. The previous matched short observations were 64.074 and 58.801 decode tok/s respectively; this one-call screen shows no apparent slowdown but is not a statistical performance comparison. Base Qwen weights remain the shared 15.79 decimal GB SATA checkpoint.

[Numeric evidence](validation-results/20261101-qwen-48k.json). Older contexts and qualifications elsewhere remain historical evidence.
