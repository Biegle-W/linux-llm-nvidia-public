# Context-expansion tests — October 27, 2026

**In progress. No production context setting has been changed.**
The six current profiles are being tested for larger allocations without lower
prefill/decode throughput or higher TTFT on the same approximately 2.2K input /
128-output fixture. [Numeric samples and current progress](benchmark-results/20261027-context-expansion.json).

The [forum and primary-source trail](FORUM-OPTIMIZATION-SOURCES.md) covers lcz.me,
Level1Techs Forums and Digital Spaceport. Other hardware's measurements identify
candidates; they do not establish performance on this machine.

## Method and selection

Fresh controls account for current cache and run variation; older dated results
remain preserved. Controls use three requests after 64-token warm-up, initial
screens one, and confirmations three. A close screen may be rechecked, but final
selection normally requires median prefill and decode at least as high as the matched
control, and TTFT no higher, plus resource and quality checks. The user explicitly
accepted GLM64K and StrataDeepSeek128K screen tradeoffs; these still require
confirmation and resource/near-window quality checks. Longer inputs add
work: near-window retrieval and its latency are recorded separately, not called
speed-neutral against a 2.2K prompt. Three runs are not a population guarantee.

All model weights, quantizations, dense GPU-only placement and owned worker guards
remain. Dense workers use 30/36 GiB soft/hard RAM; selected MoE budgets remain capped
at 48 GiB hard. Initial trials used a 1 GiB swap occupancy cap. After explicit
user approval, subsequent trials permit loading/parked swap without that fixed cap
and enforce active swap-I/O/pressure limits; each trial records its actual policy. Host available RAM below 8 GiB or
GPU temperature at 82 C for three two-second samples stops the owned test.
New dense allocations must retain at least 1 GiB GPU headroom after loading.
The Flash streaming/headroom variant applies the same floor. These bounds are
not increased to make a context fit. No engine, driver or model was upgraded.

Long-window qualification includes arithmetic/JSON and three-marker retrieval near
90% of the new allocation, using actual input usage to verify its length. Vision
is checked where the retained profile supports it. A context that merely starts
is not a fully qualified larger window. Failed trials remain evidence.

## Measured trials so far

These are test configurations, not additional maintained presets. Configured
context and completed retrieval coverage are separate fields in the numeric file.
Sizes are decimal GB of base weights, excluding packs/caches; both dense engines
and both DeepSeek engines respectively share their checkpoints. SATA is Samsung
870 QVO; NVMe is CT1000P3PSSD8.

### VRAM-only models

| Model / quant | Engine / trial | Prefill (tok/s) | Time to first token (s) | Decode (tok/s) | Context limit (tokens) | Storage size (GB) | Storage location |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Qwen3.8-27B / AutoRound-INT4-fast-heads-INT8-embedding | HyperQwen-vLLM / `hyperqwen-32768-control` | 1,376.8 | 1.623 | 87.57 | 32,768 | 15.79 | SATA: `models/engine-tests/qwen38-27b-hyperqwen-fast` |
| Qwen3.8-27B / AutoRound-INT4-fast-heads-INT8-embedding | HyperQwen-vLLM / `hyperqwen-40000-screen` | 1,372.8 | 1.625 | 89.19 | 40,000 | 15.79 | SATA: `models/engine-tests/qwen38-27b-hyperqwen-fast` |
| Qwen3.8-27B / AutoRound-INT4-fast-heads-INT8-embedding | HyperQwen-vLLM / `hyperqwen-49152-kv704-pf256-confirmed` | 1,497.2 | 1.494 | 89.35 | 49,152 | 15.79 | SATA: `models/engine-tests/qwen38-27b-hyperqwen-fast` |
| Qwen3.8-27B / AutoRound-INT4-fast-heads-INT8-embedding | HyperQwen-vLLM / `hyperqwen-49152-kv704-pf256-screen` | 1,489.3 | 1.500 | 85.45 | 49,152 | 15.79 | SATA: `models/engine-tests/qwen38-27b-hyperqwen-fast` |
| Qwen3.8-27B / AutoRound-INT4-fast-heads-INT8-embedding | HyperQwen-vLLM / `hyperqwen-49152-kv704-screen` | 1,377.5 | 1.622 | 92.36 | 49,152 | 15.79 | SATA: `models/engine-tests/qwen38-27b-hyperqwen-fast` |
| Qwen3.8-27B / AutoRound-INT4-fast-heads-INT8-embedding | HyperQwen-vLLM / `hyperqwen-56320-kv704-pf256-final-confirmed` | 1,491.7 | 1.499 | 89.10 | 56,320 | 15.79 | SATA: `models/engine-tests/qwen38-27b-hyperqwen-fast` |
| Qwen3.8-27B / AutoRound-INT4-fast-heads-INT8-embedding | HyperQwen-vLLM / `hyperqwen-56320-kv704-pf256-screen` | 1,488.8 | 1.500 | 85.45 | 56,320 | 15.79 | SATA: `models/engine-tests/qwen38-27b-hyperqwen-fast` |
| Qwen3.8-27B / AutoRound-INT4-fast-heads-INT8-embedding | SGLang / `sglang-16384-control` | 2,556.6 | 0.869 | 45.85 | 16,384 | 15.79 | SATA: `models/engine-tests/qwen38-27b-hyperqwen-fast` |
| Qwen3.8-27B / AutoRound-INT4-fast-heads-INT8-embedding | SGLang / `sglang-16384-paired-control` | 2,571.1 | 0.864 | 46.00 | 16,384 | 15.79 | SATA: `models/engine-tests/qwen38-27b-hyperqwen-fast` |
| Qwen3.8-27B / AutoRound-INT4-fast-heads-INT8-embedding | SGLang / `sglang-21504-confirmed` | 2,535.0 | 0.877 | 46.32 | 21,504 | 15.79 | SATA: `models/engine-tests/qwen38-27b-hyperqwen-fast` |
| Qwen3.8-27B / AutoRound-INT4-fast-heads-INT8-embedding | SGLang / `sglang-21504-pf1024-screen` | 2,250.2 | 0.991 | 46.27 | 21,504 | 15.79 | SATA: `models/engine-tests/qwen38-27b-hyperqwen-fast` |
| Qwen3.8-27B / AutoRound-INT4-fast-heads-INT8-embedding | SGLang / `sglang-21504-pf384-final-confirmed` | 2,621.0 | 0.852 | 46.17 | 21,504 | 15.79 | SATA: `models/engine-tests/qwen38-27b-hyperqwen-fast` |
| Qwen3.8-27B / AutoRound-INT4-fast-heads-INT8-embedding | SGLang / `sglang-21504-pf384-screen` | 2,632.1 | 0.848 | 46.26 | 21,504 | 15.79 | SATA: `models/engine-tests/qwen38-27b-hyperqwen-fast` |
| Qwen3.8-27B / AutoRound-INT4-fast-heads-INT8-embedding | SGLang / `sglang-21504-pf768-screen` | 2,441.2 | 0.914 | 46.17 | 21,504 | 15.79 | SATA: `models/engine-tests/qwen38-27b-hyperqwen-fast` |
| Qwen3.8-27B / AutoRound-INT4-fast-heads-INT8-embedding | SGLang / `sglang-21504-screen` | 2,569.8 | 0.868 | 46.27 | 21,504 | 15.79 | SATA: `models/engine-tests/qwen38-27b-hyperqwen-fast` |
| Qwen3.8-27B / AutoRound-INT4-fast-heads-INT8-embedding | SGLang / `sglang-32768-mem92-pf384-combined-confirmed` | 2,613.8 | 0.853 | 46.59 | 32,768 | 15.79 | SATA: `models/engine-tests/qwen38-27b-hyperqwen-fast` |
| Qwen3.8-27B / AutoRound-INT4-fast-heads-INT8-embedding | SGLang / `sglang-32768-mem92-pf384-screen` | 2,662.9 | 0.838 | 46.42 | 32,768 | 15.79 | SATA: `models/engine-tests/qwen38-27b-hyperqwen-fast` |

### MoE models with CPU RAM offload

None currently kept.

### MoE models with SSD streaming

| Model / quant | Engine / trial | Prefill (tok/s) | Time to first token (s) | Decode (tok/s) | Context limit (tokens) | Storage size (GB) | Storage location |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| DeepSeek-V4.1-Flash-1017 / Maya-S | Maya / `deepseek-maya-32768-control` | 41.5 | 52.963 | 2.48 | 32,768 | 339.48 | NVME: `models/maya/DeepSeek-V4.1-Flash-1017-GGUF/Maya-S` |
| DeepSeek-V4.1-Flash-1017 / Maya-S | Maya / `deepseek-maya-65536-screen` | 46.3 | 47.434 | 3.10 | 65,536 | 339.48 | NVME: `models/maya/DeepSeek-V4.1-Flash-1017-GGUF/Maya-S` |
| DeepSeek-V4.1-Flash-1017 / Maya-S | Strata / `deepseek-strata-131072-accepted-confirmed` | 33.3 | 65.796 | 2.95 | 131,072 | 339.48 | NVME: `models/maya/DeepSeek-V4.1-Flash-1017-GGUF/Maya-S` |
| DeepSeek-V4.1-Flash-1017 / Maya-S | Strata / `deepseek-strata-131072-screen` | 32.1 | 68.434 | 2.94 | 131,072 | 339.48 | NVME: `models/maya/DeepSeek-V4.1-Flash-1017-GGUF/Maya-S` |
| DeepSeek-V4.1-Flash-1017 / Maya-S | Strata / `deepseek-strata-65536-control` | 33.9 | 64.592 | 2.80 | 65,536 | 339.48 | NVME: `models/maya/DeepSeek-V4.1-Flash-1017-GGUF/Maya-S` |
| Qwen3.8-Flash-Next / IQ3_XXS | Strata / `flash-next-strata-131072-fullarena-v2-screen` | 555.3 | 4.024 | 75.61 | 131,072 | 75.84 | NVME: `models/strata/models/IQ3_XXS` |
| Qwen3.8-Flash-Next / IQ3_XXS | Strata / `flash-next-strata-131072-resident36-v2-screen` | 536.3 | 4.208 | 68.04 | 131,072 | 75.84 | NVME: `models/strata/models/IQ3_XXS` |
| Qwen3.8-Flash-Next / IQ3_XXS | Strata / `flash-next-strata-32768-screen` | 593.2 | 3.753 | 97.09 | 32,768 | 75.84 | NVME: `models/strata/models/IQ3_XXS` |
| Qwen3.8-Flash-Next / IQ3_XXS | Strata / `flash-next-strata-65536-fullarena-v2-screen` | 562.3 | 3.971 | 86.49 | 65,536 | 75.84 | NVME: `models/strata/models/IQ3_XXS` |
| Qwen3.8-Flash-Next / IQ3_XXS | Strata / `flash-next-strata-65536-resident36-v2-screen` | 587.8 | 3.843 | 65.21 | 65,536 | 75.84 | NVME: `models/strata/models/IQ3_XXS` |
| Qwen3.8-Flash-Next / IQ3_XXS | Strata / `flash-next-strata-65536-screen` | 589.7 | 3.789 | 94.43 | 65,536 | 75.84 | NVME: `models/strata/models/IQ3_XXS` |
| GLM-5.3-Flash / Maya-S24 | Maya / `glm-maya-32768-control` | 65.2 | 33.901 | 4.22 | 32,768 | 94.70 | NVME: `models/maya/Maya-S24` |
| GLM-5.3-Flash / Maya-S24 | Maya / `glm-maya-65536-accepted-confirmed` | 65.5 | 33.740 | 4.81 | 65,536 | 94.70 | NVME: `models/maya/Maya-S24` |
| GLM-5.3-Flash / Maya-S24 | Maya / `glm-maya-65536-screen` | 65.4 | 33.765 | 4.03 | 65,536 | 94.70 | NVME: `models/maya/Maya-S24` |
| DeepSeek-V4.1-Flash-1017 / Maya-S | Maya / `vm60-deepseek-maya-65536-ahead0-warm24-engram0-screen` | 44.7 | 49.179 | 3.80 | 65,536 | 339.48 | NVME: `models/maya/DeepSeek-V4.1-Flash-1017-GGUF/Maya-S` |

## Status and preserved evidence

The numeric file records every measured trial, its repetition count and progress.
Unmeasured failures have no invented zero-token throughput. The first dense and
Flash control/screen phase is followed by confirmation and MoE tests. Existing
kept results remain the [previous matched measurements](MOE-OPTIMIZATION-20261027.md)
until a qualified new setting is explicitly promoted.

Private exact configurations, source snapshots, frozen profiles, requests, SSE,
metrics, telemetry, admission failures and qualification responses remain under
`data/context-expansion-20261027/`. All earlier benchmark/cleanup evidence remains.
