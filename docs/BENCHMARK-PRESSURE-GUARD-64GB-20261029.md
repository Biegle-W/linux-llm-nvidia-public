# Two-profile memory-pressure adjustment and 64GB benchmark — October 29, 2026

Qwen/Strata and DeepSeek/Maya now use 15% full-memory-pressure thresholds, up from 10%, with the same 30-second active window and three-sample stop rule. All other profiles retain 10%. The 128/160 MiB/s SSD swap limits and every independent RAM/VRAM/thermal/telemetry guard remain unchanged, as do contexts, weights, precision, runtime pins, expert caches, swappiness 60, concurrency 1 and idle 600 seconds. Both profiles completed a warmup and three valid 128-output measured requests without a guard violation.

The 15% trial gives bounded headroom above the previous observed full-memory-pressure peaks of 13.19% and 12.21%. The CPU checks still stop both profiles above 15% for three eligible samples; defaults and every other stop remain. The limit bounds tolerated stalls for these two models; the independent hardware/resource guards remain active.

RAM remains 64GB installed/61.3013 GiB usable, four 16GB DIMMs at DDR5-4200 MT/s (2100 MHz DDR clock), verified earlier October 29; current Linux capacity was read again without hardware changes.

The protocol reused exact saved prompts (canonical JSON SHA-256 `33a05efdfcb7aa60c0dd422d8266fd0374c11f43a739b8b0b310ec6f38cbd39c`), targeting one 64-output warmup and three 128-output measured requests per profile. Approximately 2.2K inputs, temperature 0, top_p 1, seed 261026, thinking disabled and concurrency 1 were retained. Tables report medians: native prefill, request-to-first-content TTFT and client SSE decode `(completion tokens - 1)/(last - first content time)`. Loading/warmup are excluded; the OS page cache was not flushed. Cache warmth and run order were not controlled across historical runs. Native cached-token counts must pass the existing validity bound. Guard-stopped runs have no accepted median.

Only Qwen/Strata and DeepSeek/Maya were repeated; HyperQwen, SGLang, GLM/Maya and DeepSeek/Strata rows are explicitly carried forward from their earlier October 29 records. This composite table is not a new six-profile matched run.

### VRAM-only models

| Model / quant | Engine | Prefill (tok/s) | Time to first token (s) | Decode (tok/s) | Context limit (tokens) | Storage size (GB) | Storage location |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Qwen3.8-27B / AutoRound-INT4-fast-heads-INT8-embedding | HyperQwen-vLLM | 1,494.29 | 1.489 | 88.55 | 56,320 | 15.79 | Samsung SSD 870 QVO SATA: models/engine-tests/qwen38-27b-hyperqwen-fast |
| Qwen3.8-27B / AutoRound-INT4-fast-heads-INT8-embedding | SGLang | 1,587.90 | 1.396 | 80.87 | 32,768 | 15.79 | Samsung SSD 870 QVO SATA: models/engine-tests/qwen38-27b-hyperqwen-fast |

### MoE models with CPU RAM offload

None currently kept. Expert RAM tiers below are caches within SSD-streaming profiles.

### MoE models with SSD streaming

| Model / quant | Engine | Prefill (tok/s) | Time to first token (s) | Decode (tok/s) | Context limit (tokens) | Storage size (GB) | Storage location |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Qwen3.8-Flash-Next / IQ3_XXS | Strata | 67.10 | 32.842 | 16.87 | 32,768 | 75.84 | CT1000P3PSSD8 NVMe: models/strata/models/IQ3_XXS |
| GLM-5.3-Flash / Maya-S24 | Maya | 63.80 | 34.733 | 4.93 | 65,536 | 94.70 | CT1000P3PSSD8 NVMe: models/maya/Maya-S24 |
| DeepSeek-V4.1-Flash-1017 / Maya-S | Strata | 34.20 | 63.869 | 2.75 | 131,072 | 339.48 | CT1000P3PSSD8 NVMe: models/maya/DeepSeek-V4.1-Flash-1017-GGUF/Maya-S |
| DeepSeek-V4.1-Flash-1017 / Maya-S | Maya | 45.90 | 47.534 | 3.30 | 32,768 | 339.48 | CT1000P3PSSD8 NVMe: models/maya/DeepSeek-V4.1-Flash-1017-GGUF/Maya-S |

Storage sizes are decimal GB for base checkpoint weights only; dense engines share one checkpoint and DeepSeek engines share one checkpoint. Auxiliary packs, draft assets and caches are excluded. Context columns are configured allocations, not tested input lengths.

## Fresh request ranges

| Profile | Prefill range (tok/s) | TTFT range (s) | Decode range (tok/s) |
| --- | ---: | ---: | ---: |
| flash-next-strata | 60.900–81.900 | 26.859–36.276 | 11.026–28.339 |
| deepseek-maya | 34.100–47.200 | 46.513–63.800 | 1.904–3.745 |

## Guard observations

| Profile | Peak full PSI, all phases (%) | Peak swap writes (MiB/s) | Peak combined (MiB/s) | Peak worker swap (GiB) | Active 30s rate samples | Min host available (GiB) | Peak GPU (C) | Guard violations |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| flash-next-strata | 0.00 | 0.000 | 0.000 | 0.000 | 59 | 48.91 | 54 | 0 |
| deepseek-maya | 12.53 | 14.411 | 15.596 | 0.665 | 173 | 49.75 | 59 | 0 |

flash-next-strata peak inference full PSI was 0.00%. The recorded sequence contained up to 0 consecutive eligible samples above the former 10% threshold. This rerun did not exercise the additional pressure allowance.

deepseek-maya peak inference full PSI was 6.80%. The recorded sequence contained up to 0 consecutive eligible samples above the former 10% threshold. This rerun did not exercise the additional pressure allowance.

The 12.53% DeepSeek/Maya peak occurred during loading; peak inference pressure was 6.80%. Both reruns stayed below the former 10% inference threshold, so this short run does not establish that the raised threshold caused their successful completion.

Rate samples overlap and are not independent trials. Pressure is owned-cgroup full avg10; the 30-second active-window and three-sample rule are unchanged. Peaks include sampled loading/warmup; guard outcomes identify actual violations. Loading/parked swap remains allowed. Swap rates exclude model-weight reads and do not measure SSD endurance.

All 202 CPU regressions passed, including 15% scope/bounds/latching, unchanged 10% defaults, swap-write/combined limits, pressure transient reset, telemetry and counter continuity. Each runtime configuration and cgroup budget was compared with its saved preimage; only the two pressure thresholds changed. No new near-window retrieval, tool/image, fresh-reload or multi-hour qualification is claimed. Earlier guard failures and benchmarks remain dated evidence.

Workers are stopped, router idle, no GPU reservation remains, DSH preserved and no fallback loaded. Prior 10% stop records are archived unchanged; explicit model selection cleared their invocation latches before the new run. No conversation-KV snapshots were cleared or isolated for this two-profile run.

[Numeric results](benchmark-results/20261029-pressure-guard.json). [Earlier 10% pressure outcomes](BENCHMARK-SSD-SWAP-64GB-20261029.md).
