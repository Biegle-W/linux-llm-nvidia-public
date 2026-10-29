# SSD-streaming swap-policy benchmark on 64GB — October 29, 2026

Four SSD-streaming profiles now use bounded swap limits of 128 MiB/s writes and 160 MiB/s combined over 30 seconds. Dense and unknown profiles retain 1/8 MiB/s. All other resource guards, contexts, expert-cache settings, precision choices, runtime pins and model settings are unchanged.

2 of four SSD profiles completed three valid measured requests without guard violations on restored 64GB RAM. RAM remains DDR5-4200 MT/s across four 16GB DIMMs (61.3013 GiB usable; 2100 MHz DDR clock). The dense profiles were not repeated; their table rows carry forward the earlier October 29 full-RAM run.

The protocol reused the exact saved prior prompts (canonical JSON SHA-256 `33a05efdfcb7aa60c0dd422d8266fd0374c11f43a739b8b0b310ec6f38cbd39c`), targeting one 64-output warmup and three 128-output measured requests per profile (guard-stopped runs ended early), temperature 0, top_p 1, seed 261026, thinking off and concurrency 1. Tables report medians: native prefill, request-to-first-content TTFT and client stream decode `(completion tokens - 1)/(last - first content time)`. Approximately 2.2K input tokens do not test the allocated full context. Loading/warmup are excluded; the OS page cache was not flushed. Cache warmth and run order can affect differences.

### VRAM-only models

| Model / quant | Engine | Prefill (tok/s) | Time to first token (s) | Decode (tok/s) | Context limit (tokens) | Storage size (GB) | Storage location |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Qwen3.8-27B / AutoRound-INT4-fast-heads-INT8-embedding | HyperQwen-vLLM | 1,494.29 | 1.49 | 88.55 | 56,320 | 15.79 | Samsung SSD 870 QVO SATA: models/engine-tests/qwen38-27b-hyperqwen-fast |
| Qwen3.8-27B / AutoRound-INT4-fast-heads-INT8-embedding | SGLang | 1,587.90 | 1.40 | 80.87 | 32,768 | 15.79 | Samsung SSD 870 QVO SATA: models/engine-tests/qwen38-27b-hyperqwen-fast |

### MoE models with CPU RAM offload

None currently kept. RAM tiers below are caches within SSD-streaming profiles.

### MoE models with SSD streaming

| Model / quant | Engine | Prefill (tok/s) | Time to first token (s) | Decode (tok/s) | Context limit (tokens) | Storage size (GB) | Storage location |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Qwen3.8-Flash-Next / IQ3_XXS | Strata | Not measured | Not measured | Not measured | 32,768 | 75.84 | CT1000P3PSSD8 NVMe: models/strata/models/IQ3_XXS |
| GLM-5.3-Flash / Maya-S24 | Maya | 63.80 | 34.73 | 4.93 | 65,536 | 94.70 | CT1000P3PSSD8 NVMe: models/maya/Maya-S24 |
| DeepSeek-V4.1-Flash-1017 / Maya-S | Strata | 34.20 | 63.87 | 2.75 | 131,072 | 339.48 | CT1000P3PSSD8 NVMe: models/maya/DeepSeek-V4.1-Flash-1017-GGUF/Maya-S |
| DeepSeek-V4.1-Flash-1017 / Maya-S | Maya | Not measured | Not measured | Not measured | 32,768 | 339.48 | CT1000P3PSSD8 NVMe: models/maya/DeepSeek-V4.1-Flash-1017-GGUF/Maya-S |

Storage sizes are decimal GB for base checkpoint weights. Dense engines share their 15.79 GB checkpoint; DeepSeek engines share their 339.48 GB checkpoint. Auxiliary packs/caches are excluded.

## Measured request ranges

| Profile | Prefill range (tok/s) | TTFT range (s) | Decode range (tok/s) |
| --- | ---: | ---: | ---: |
| glm-maya | 40.600–69.000 | 31.893–54.289 | 1.899–5.838 |
| deepseek-strata | 31.700–34.900 | 62.319–69.065 | 2.737–2.806 |

## Guard observations

| Profile | Peak worker swap (GiB) | Active 30s rate samples | Peak writes (MiB/s) | Peak combined (MiB/s) | Peak full PSI (%) | Min host available (GiB) | Peak GPU (C) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| flash-next-strata | 0.000 | 20 | 0.000 | 0.000 | 13.19 | 48.77 | 52 |
| glm-maya | 1.805 | 123 | 0.000 | 0.322 | 2.51 | 9.89 | 59 |
| deepseek-strata | 0.000 | 183 | 0.000 | 0.000 | 0.00 | 14.04 | 61 |
| deepseek-maya | 0.641 | 104 | 11.306 | 11.876 | 12.21 | 49.88 | 59 |

Qwen Flash-Next produced three valid 128-token responses, but the unchanged full-memory-pressure guard stopped the worker near the end of the third response (11.52% at the stop; peak full PSI 13.19%). Its captured diagnostic medians were 241.30 prefill tok/s, 9.132s TTFT and 47.65 decode tok/s; these are not promoted as a passing benchmark. Swap writes/reads were zero in observed windows. The interrupted switch to GLM was continued in a separate owned run using the same saved fixtures; Qwen was not repeated.

DeepSeek/Maya did not pass: the full-memory-pressure guard fired at 11.24% during its second measured request. It has one captured valid measured response, but no new passing speed median is selected. Any diagnostic timing is retained only in numeric evidence.

The first DeepSeek/Strata measured attempt reused 2191 of 2192 prompt tokens from persistent conversation KV and was rejected before selection. For the corrected DeepSeek run, only persisted conversation KV snapshots were temporarily isolated and restored byte-for-byte after cleanup. Exact saved prompts and all expert-cache/runtime settings were preserved. Corrected requests are recorded separately and must meet the existing cache-reuse validity bound; Qwen and GLM were not repeated.

Overlapping rate samples are not independent trials. Short requests may have no complete 30-second active window. Loading and parked swap remain allowed. These swap counters do not measure all model-weight SSD traffic or NAND endurance. The host floor 2 GiB, pressure 10%/three samples, telemetry/continuity checks, 82 C thermal stop, worker cgroup budgets, 512 MiB native reserves/dense free-VRAM floor, swappiness 60, concurrency 1 and idle 600 seconds remain.

All 201 CPU regressions passed, including each SSD profile's bounded writes, combined I/O, pressure, missing telemetry and counter continuity; dense and unknown profile defaults stayed at 1/8 MiB/s. The previous DeepSeek/Maya 1 MiB/s guard stop remains dated history. New guard outcomes are reported above. This is a speed screen, not a replacement for near-window, tool/image, fresh-reload or multi-hour qualification.

[Numeric results](benchmark-results/20261029-ssd-relaxed-swap.json). [Earlier full-RAM benchmark](BENCHMARK-64GB-20261029.md).

Workers are stopped, the router is idle, no GPU reservation remains, and DSH is preserved. Original conversation KV snapshots were restored exactly; no fallback model was loaded.
