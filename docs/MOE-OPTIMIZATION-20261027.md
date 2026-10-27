# GLM and DeepSeek cache optimization — October 27, 2026

GLM and both DeepSeek profiles were requalified at their existing context limits:
**32,768 / 65,536 / 32,768**. No model, quantization or context was removed or
reduced. Results use medians of three fresh matched requests after warm-up.
[Numeric samples, candidates, settings and resources](benchmark-results/20261027-moe-optimized.json).

## Why the earlier numbers were faster

The October 26 speed run used 8K allocations and a different host-cache budget.
GLM then pinned about 45.5 GiB of expert RAM. Managed deployment capped it at
32 GiB. The later GLM logs show many more SSD misses; a smaller cache changed
performance even though the model and GPUs stayed the same. The CPU vision
fallback also loaded eagerly when the engine could not lend enough GPU memory.

DeepSeek's old Strata store was about 42.5 GB, versus 26.2 GB under the later
36 GiB worker cap. Maya's old expert read-ahead was 46.8 GB, versus about 29.8 GB
under that cap. Its canonical defaults also differed from the old benchmark:
vision was enabled, prompt chunks defaulted to 8192, and the explicit expert
profile/mmap controls were missing. Auto CPU selection still chose 14 threads,
so a missing explicit thread flag was not evidence of fewer actual threads.
Restoring those controls alone gave only a modest gain; cache capacity was the
larger constraint.

The older native/client decode rates agree closely (GLM 7.5/7.48, Strata
DeepSeek 2.7/2.71 and Maya DeepSeek 4.4/4.32 tok/s). The regression is not explained
by changing decode definitions. However, the older run interleaved short and long
requests and used more warm-up traffic, different allocations and dynamic cache
state. It is historical evidence, not an isolated context-size comparison.
GLM and DeepSeek remained on NVMe throughout; dense Qwen's later SATA move did
not relocate their files. Both qualified GPUs remain compute-unlocked.

## Matched before and after

This comparison uses the October 27 matched baseline, the same approximately
2.2K-token fixtures, 128 output tokens, temperature zero, thinking off and one
request at a time. Loading is excluded. Prefill is native engine timing; TTFT and
decode are client-observed. Speculative chunks affect stream throughput.

| Profile | Prefill before → after | TTFT before → after (s) | Decode before → after | Decode change |
| --- | ---: | ---: | ---: | ---: |
| GLM-5.3-Flash / Maya | 56.0 → 64.5 | 39.469 → 36.247 | 3.05 → 4.73 | +55.3% |
| DeepSeek-V4.1-Flash-1017 / Strata | 31.5 → 32.4 | 69.195 → 67.527 | 1.71 → 2.87 | +68.4% |
| DeepSeek-V4.1-Flash-1017 / Maya | 36.1 → 49.6 | 60.602 → 44.017 | 1.22 → 4.08 | +234.2% |

## Current kept results

Only GLM and DeepSeek were retested for this optimization. Dense Qwen and
Flash-Next rows reuse their unchanged October 27 measurements; storage locations
show current placement. Size counts base GGUF/safetensors weights in decimal GB,
excluding separate packs/caches. Shared weights count once in physical totals.

### VRAM-only models

| Model / quant | Engine | Prefill (tok/s) | Time to first token (s) | Decode (tok/s) | Context limit (tokens) | Storage size (GB) | Storage location |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Qwen3.8-27B / AutoRound INT4 / INT8 embedding | HyperQwen-vLLM | 1,385.5 | 1.613 | 89.01 | 32,768 | 15.79 | Samsung SSD 870 QVO SATA: `models/engine-tests/qwen38-27b-hyperqwen-fast` |
| Qwen3.8-27B / AutoRound INT4 / INT8 embedding | SGLang | 2,606.3 | 0.852 | 46.71 | 16,384 | 15.79 | Samsung SSD 870 QVO SATA: `models/engine-tests/qwen38-27b-hyperqwen-fast` |

### MoE models with CPU RAM offload

None currently kept. RAM tiers in streamed profiles are caches, not full-model RAM residency.

### MoE models with SSD streaming

| Model / quant | Engine | Prefill (tok/s) | Time to first token (s) | Decode (tok/s) | Context limit (tokens) | Storage size (GB) | Storage location |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Qwen3.8-Flash-Next / IQ3_XXS | Strata | 609.6 | 3.648 | 105.64 | 32,768 | 75.84 | CT1000P3PSSD8 NVMe: `models/strata/models/IQ3_XXS` |
| GLM-5.3-Flash / Maya-S24 | Maya | 64.5 | 36.247 | 4.73 | 32,768 | 94.70 | CT1000P3PSSD8 NVMe: `models/maya/Maya-S24` |
| DeepSeek-V4.1-Flash-1017 / Maya-S | Strata | 32.4 | 67.527 | 2.87 | 65,536 | 339.48 | CT1000P3PSSD8 NVMe: `models/maya/DeepSeek-V4.1-Flash-1017-GGUF/Maya-S` |
| DeepSeek-V4.1-Flash-1017 / Maya-S | Maya | 49.6 | 44.017 | 4.08 | 32,768 | 339.48 | CT1000P3PSSD8 NVMe: `models/maya/DeepSeek-V4.1-Flash-1017-GGUF/Maya-S` |

## Selected settings and implementation

- GLM retains auto prefill, MTP, KV streaming, both GPUs, 2048 MiB GPU reserves and
  32K context, with a 40 GiB expert RAM tier and 46/48 GiB soft/hard
  worker budget. The CPU encoder fallback now starts for images and ends after their
  embeddings are produced, preserving image support while freeing idle RAM.
- Strata DeepSeek retains six experts, 14 CPU threads, 4096-token chunks, mmap,
  drafting/vision off, both GPUs and 2048 MiB reserves at 64K. Its 42 GB RAM store
  uses frequency-based eviction (LFU) in the bounded 48 GiB worker class. The
  engine's internal 8 GiB cache floor remains in force.
- Maya DeepSeek retains 32K and image support, with explicit CPU/prefill/mmap and
  expert-profile controls. It uses an 8 GB post-prompt expert-warming target
  (`DS4_WARM_GB=8`) within its 46/48 GiB soft/hard worker budget. Three measured
  requests and JSON, retrieval and image checks qualified this choice. Model
  weights still stream from NVMe.
- Dense workers retain 30/36 GiB soft/hard limits. MoE budgets are now explicit
  per selected profile, capped at 48 GiB hard and 1 GiB swap, with at least 2 GiB
  between soft and hard limits. The launcher verifies the exact cgroup budget.
  All maintained MoE shell commands use the router, so they use the same budget
  as Desktop/DSH/API launches. The host 8 GiB floor, 82 C temperature threshold,
  full expert counts, owned-process checks and GPU reserves remain enabled.

The [Maya patch](../scripts/patches/maya-lazy-cpu-vision.patch) changes Python vision
lifecycle only. Native engine binaries and model weights were not upgraded or
requantized. Maya remains 1.1.29; Strata remains installed component 0.1.51.
Budget validation and shell dispatch have regression coverage; vision tests cover
lazy CPU encoding/cache/shutdown and GPU lending/reclaim. All 34 CPU tests passed;
switch tests use temporary state independent of live GPU reservations. The installed source
patch must be retained or reapplied when replacing the pinned Maya checkout.

## Qualification and resource evidence

| Profile | JSON arithmetic | Three-marker retrieval input | Image | Configured context |
| --- | --- | ---: | --- | ---: |
| glm-maya | Passed | 10,908 | Passed, 1024 × 1024 red fixture | 32,768 |
| deepseek-strata | Passed | 9,673 | Off in retained profile | 65,536 |
| deepseek-maya | Passed | 9,674 | Passed, 1024 × 1024 red fixture | 32,768 |

These new retrieval checks exercise multiple prompt chunks. They do not claim a
new full-window accuracy qualification. The previous 58,969-input Strata DeepSeek
retrieval remains separately dated evidence for its 64K allocation. All configured
context limits remain unchanged.

| Profile | Soft / hard RAM GiB | Sampled peak worker GiB | Peak worker swap GiB | Minimum host available GiB | GPU peaks C |
| --- | ---: | ---: | ---: | ---: | --- |
| glm-maya | 46 / 48 | 45.98 | 1.00 | 10.25 | 60 / 46 |
| deepseek-strata | 44 / 48 | 44.00 | 0.00 | 14.85 | 59 / 48 |
| deepseek-maya | 46 / 48 | 45.07 | 0.64 | 51.18 | 58 / 46 |

Peaks include loading, measurements and qualification, sampled every five seconds.
Workers monitor host RAM and temperatures every two seconds and stop after three
bad samples. Soft-limit reclaim and bounded swap occupancy are recorded rather
than hidden; peak swap is not a claim about sustained churn. No OOM or resource
abort occurred in the selected runs. This is not a sustained thermal stress test.
Three repetitions are not confidence intervals or a broad workload/quality eval.

Production deployment checks passed for all three selected profiles through the
managed worker path. GLM's shell command selected the router; DeepSeek's two API
selections loaded successfully. Each actual cgroup matched its selected soft/hard
RAM and swap limits, retained the allocated context and returned correct JSON
arithmetic. HyperQwen was restored afterward; router and DSH stayed active and the
owned GPU reservation was removed. These are deployment checks, not a repeat of
the performance benchmark.

## Screening and preservation

The numeric record retains every measured candidate. In particular, GLM with a
38 GiB tier and 2048-token prompt chunks improved decode but substantially harmed
prefill/TTFT and hit its swap cap, so it was rejected. Intermediate private tuning
files are evidence, not additional maintained presets. Fixed per-engine expert
seeds were copied for comparisons; live profiles resume learning after deployment.
OS page cache was not flushed and request order was not randomized.

Six prior source/settings snapshots, with credential fields omitted and hashes
verified, are preserved in private `retired-llm-setting`, batch
`linux-nvidia/2026-10-27-moe-cache-optimization`, commit `b2c865d`. Raw SSE, canonical config
snapshots, frozen profiles, all measurements, qualification responses, unit limits,
cgroup/IO telemetry and production checks remain private under
`data/moe-optimization-20261027/`. Earlier benchmark reports and raw data remain
preserved. Exactly six model/quant/engine profiles remain maintained.
