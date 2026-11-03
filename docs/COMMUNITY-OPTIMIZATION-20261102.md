# Community optimization screens — November 2, 2026

Hardware: RTX 3080 Ti 12 GB + RTX 3080 10 GB, 64 GB installed RAM. These are short per-arm observations, not full-context or sustained qualifications. Each arm includes bounded chat observations, one actual DSH read-tool call, matching result/follow-up, owned unload and transactional restoration. Strata prefill chunk512 is selected after two passing matched pairs; other selected settings are retained. Earlier measurements remain historical.

Model loading and the follow-up answer are excluded from first-tool-call timing. Native request timings or one-request engine counters measure decode; generated tool arguments count as output. Client TTFT includes parser buffering where engine counters are absent. Prompts differ slightly in fixture path/nonce and token counts; single observations do not establish a lasting gain. DeepSeek/Strata restores conversation prefixes; report its cached suffix separately.

Normal-router verification of the selected setting passed its read-tool/result check and owned unload. The5704-input/5539-cached/59-output call measured24.0 tok/s for the165-token uncached suffix,6.930s TTFT and9.5 decode tok/s. This cached call does not replace the uncached1064-token comparison. Both workers finished idle. Fifteen focused runtime tests passed.

## Selection and limits

- Select DeepSeek/Strata prefill512: uncached1064-token prefill87.1→109.4 tok/s in the screen and85.1→108.5 tok/s in confirmation (+25.6%/+27.5%). TTFT12.22→9.72 s and12.52→9.82 s. Corresponding decode8.9→8.8 and8.1→8.5 tok/s. Both arms in both pairs passed actual tool/result/follow-up and unload. Configured128 was internally clamped to256; candidate512 was confirmed in engine logs. Retain32,768 context and all guards. Cached tool prefixes are not evidence of uncached prefill improvement.
- Retain GLM settings: PCIe-quarter chat aggregate-2.41%; first tool decode5.9→5.6 tok/s.
- Retain DeepSeek/Maya cache controller: initial90% tool decode4.7→4.9 reversed to5.1→4.5 in a fresh confirmation; both used uncached tool prompts. Small chat gains were not a reliable tool-workload win.
- Retain Flash-Next settings: async tool69.4→78.6 reversed to74.1→73.8 in confirmation. Split17 was slower. Do not select from one favorable sample.
- HyperQwen baseline stopped at its512 MiB free-VRAM guard. No MTP inference result. SGLang baseline passed; MTP3 failed CUDA graph capture with CUDA OOM at retained57,344 context. No guard or context reduction.
- Bolt corrected baseline passed. Pinned host-offload was killed during loading by systemd-oomd (journal56 GiB RAM peak/3.1 GiB swap peak). A shutdown race retained provisional files; after both workers were verified idle, all three preimages were hash-restored and its dead reservation released. Prefetch-two was not reached. The earlier direct-backend tool404 was a private harness model-alias mismatch, fixed before the passing baseline; preserve that failed attempt separately.
- New Maya1.1.50 normal-mode comparison remains pending; XS weights were not downloaded. No new full-context or sustained suite.

## VRAM-only

| Model / quant | Engine / arm | Prefill (tok/s) | Time to first token (s) | Decode (tok/s) | Context limit (tokens) | Storage size (GB) | Storage location |
|---|---|---:|---:|---:|---:|---:|---|
| Qwen3.8-27B / AutoRound INT4, INT8 embedding | HyperQwen-vLLM: baseline (221003) | Not measured | Not measured | Not measured | 86016 | 15.79 | SATA SSD: models/engine-tests/qwen38-27b-hyperqwen-fast |
| Qwen3.8-27B / AutoRound INT4, INT8 embedding | SGLang: baseline (221156) | 2373.514 | 2.603 | 59.090 | 57344 | 15.79 | SATA SSD: models/engine-tests/qwen38-27b-hyperqwen-fast |
| Qwen3.8-27B / AutoRound INT4, INT8 embedding | SGLang: mtp3 (221156) | Not measured | Not measured | Not measured | 57344 | 15.79 | SATA SSD: models/engine-tests/qwen38-27b-hyperqwen-fast |

## CPU RAM offload

| Model / quant | Engine / arm | Prefill (tok/s) | Time to first token (s) | Decode (tok/s) | Context limit (tokens) | Storage size (GB) | Storage location |
|---|---|---:|---:|---:|---:|---:|---|
| Nemotron-3.5-Bolt-74B-A9B / AWQ INT4 | vLLM offload: baseline (221950) | Not measured | Not measured | Not measured | 163840 | 55.33 | SATA SSD: models/bolt-awq-int4 |
| Nemotron-3.5-Bolt-74B-A9B / AWQ INT4 | vLLM offload: baseline (222625) | 237.520 | 26.781 | 0.389 | 163840 | 55.33 | SATA SSD: models/bolt-awq-int4 |
| Nemotron-3.5-Bolt-74B-A9B / AWQ INT4 | vLLM offload: pinned-host-offload (222625) | Not measured | Not measured | Not measured | 163840 | 55.33 | SATA SSD: models/bolt-awq-int4 |

## SSD streaming

| Model / quant | Engine / arm | Prefill (tok/s) | Time to first token (s) | Decode (tok/s) | Context limit (tokens) | Storage size (GB) | Storage location |
|---|---|---:|---:|---:|---:|---:|---|
| GLM-5.3-Flash / Maya-S24 | Maya: baseline (215604) | 299.200 | 18.628 | 5.900 | 65536 | 94.70 | NVMe SSD: models/maya/Maya-S24 |
| GLM-5.3-Flash / Maya-S24 | Maya: pcie-quarter (215604) | 290.300 | 19.207 | 5.600 | 65536 | 94.70 | NVMe SSD: models/maya/Maya-S24 |
| DeepSeek-V4.1-Flash-1017 / UD-IQ1_S | Maya: baseline (220453) | 184.600 | 30.910 | 4.700 | 32768 | 232.98 | NVMe core + SATA Engram: models/unsloth/deepseek-v41-1017-dynamic31-8a6ec9cf/UD-IQ1_S |
| DeepSeek-V4.1-Flash-1017 / UD-IQ1_S | Maya: rebuilt-75 (220453) | 188.000 | 30.308 | 4.700 | 32768 | 232.98 | NVMe core + SATA Engram: models/unsloth/deepseek-v41-1017-dynamic31-8a6ec9cf/UD-IQ1_S |
| DeepSeek-V4.1-Flash-1017 / UD-IQ1_S | Maya: reclaim-90 (220453) | 196.700 | 29.008 | 4.900 | 32768 | 232.98 | NVMe core + SATA Engram: models/unsloth/deepseek-v41-1017-dynamic31-8a6ec9cf/UD-IQ1_S |
| DeepSeek-V4.1-Flash-1017 / UD-IQ1_S | Maya: baseline (223927) | 196.900 | 28.957 | 5.100 | 32768 | 232.98 | NVMe core + SATA Engram: models/unsloth/deepseek-v41-1017-dynamic31-8a6ec9cf/UD-IQ1_S |
| DeepSeek-V4.1-Flash-1017 / UD-IQ1_S | Maya: reclaim-90 (223927) | 193.900 | 29.413 | 4.500 | 32768 | 232.98 | NVMe core + SATA Engram: models/unsloth/deepseek-v41-1017-dynamic31-8a6ec9cf/UD-IQ1_S |
| Qwen3.8-Flash-Next / IQ3_XXS | Strata: async-adaptation (221344) | 903.900 | 6.601 | 78.600 | 131072 | 75.84 | NVMe SSD: models/strata/models/IQ3_XXS |
| Qwen3.8-Flash-Next / IQ3_XXS | Strata: baseline (221344) | 872.700 | 6.827 | 69.400 | 131072 | 75.84 | NVMe SSD: models/strata/models/IQ3_XXS |
| Qwen3.8-Flash-Next / IQ3_XXS | Strata: split-17 (221344) | 527.300 | 11.371 | 66.700 | 131072 | 75.84 | NVMe SSD: models/strata/models/IQ3_XXS |
| Qwen3.8-Flash-Next / IQ3_XXS | Strata: async-adaptation (224310) | 906.800 | 6.572 | 73.800 | 131072 | 75.84 | NVMe SSD: models/strata/models/IQ3_XXS |
| Qwen3.8-Flash-Next / IQ3_XXS | Strata: baseline (224310) | 909.400 | 6.563 | 74.100 | 131072 | 75.84 | NVMe SSD: models/strata/models/IQ3_XXS |
| DeepSeek-V4.1-Flash-1017 / UD-IQ1_S | Strata: baseline (221707) | 23.200 | 7.058 | 6.800 | 32768 | 232.98 | NVMe core + SATA Engram: models/unsloth/deepseek-v41-1017-dynamic31-8a6ec9cf/UD-IQ1_S |
| DeepSeek-V4.1-Flash-1017 / UD-IQ1_S | Strata: prefill-512 (221707) | 23.300 | 6.902 | 6.800 | 32768 | 232.98 | NVMe core + SATA Engram: models/unsloth/deepseek-v41-1017-dynamic31-8a6ec9cf/UD-IQ1_S |
| DeepSeek-V4.1-Flash-1017 / UD-IQ1_S | Strata: baseline (224549) | 23.700 | 6.921 | 6.800 | 32768 | 232.98 | NVMe core + SATA Engram: models/unsloth/deepseek-v41-1017-dynamic31-8a6ec9cf/UD-IQ1_S |
| DeepSeek-V4.1-Flash-1017 / UD-IQ1_S | Strata: prefill-512 (224549) | 23.900 | 6.735 | 7.000 | 32768 | 232.98 | NVMe core + SATA Engram: models/unsloth/deepseek-v41-1017-dynamic31-8a6ec9cf/UD-IQ1_S |

## Correctness and cache attribution

| Profile / arm | Input / cached / output tokens | Result |
|---|---:|---|
| glm-maya / baseline (215604) | 5432 / 0 / 26 | PASS; unload and restoration verified |
| glm-maya / pcie-quarter (215604) | 5435 / 0 / 27 | PASS; unload and restoration verified |
| deepseek-maya / baseline (220453) | 5702 / 0 / 65 | PASS; unload and restoration verified |
| deepseek-maya / rebuilt-75 (220453) | 5696 / 0 / 63 | PASS; unload and restoration verified |
| deepseek-maya / reclaim-90 (220453) | 5702 / 0 / 65 | PASS; unload and restoration verified |
| deepseek-maya / baseline (223927) | 5699 / 0 / 61 | PASS; unload and restoration verified |
| deepseek-maya / reclaim-90 (223927) | 5699 / 0 / 61 | PASS; unload and restoration verified |
| qwen27b-hyperqwen / baseline (221003) | — / — / — | FAIL: Dense GPU headroom below 512 MiB; unload/restoration True |
| qwen27b-sglang / baseline (221156) | 6126 / 0 / 84 | PASS; unload and restoration verified |
| qwen27b-sglang / mtp3 (221156) | — / — / — | FAIL: Worker stopped during loading; inspect its journal.; unload/restoration True |
| flash-next-strata / async-adaptation (221344) | 5589 / 0 / 41 | PASS; unload and restoration verified |
| flash-next-strata / baseline (221344) | 5583 / 0 / 39 | PASS; unload and restoration verified |
| flash-next-strata / split-17 (221344) | 5580 / 0 / 38 | PASS; unload and restoration verified |
| flash-next-strata / async-adaptation (224310) | 5586 / 0 / 40 | PASS; unload and restoration verified |
| flash-next-strata / baseline (224310) | 5589 / 0 / 41 | PASS; unload and restoration verified |
| deepseek-unsloth-strata / baseline (221707) | 5702 / 5539 / 61 | PASS; unload and restoration verified |
| deepseek-unsloth-strata / prefill-512 (221707) | 5699 / 5539 / 60 | PASS; unload and restoration verified |
| deepseek-unsloth-strata / baseline (224549) | 5702 / 5539 / 61 | PASS; unload and restoration verified |
| deepseek-unsloth-strata / prefill-512 (224549) | 5699 / 5539 / 63 | PASS; unload and restoration verified |
| bolt-vllm / baseline (221950) | — / 0 / — | FAIL: Actual DSH tool/result/follow-up did not pass; unload/restoration True |
| bolt-vllm / baseline (222625) | 6358 / 0 / 39 | PASS; unload and restoration verified |
| bolt-vllm / pinned-host-offload (222625) | — / — / — | FAIL: systemd-oomd killed worker during loading; journal peak56GiB RAM and3.1GiB swap; no inference result; unload/restoration True |

## Resource guards

| Model / quant | Engine | RAM guards | VRAM guards | Swap guards |
|---|---|---|---|---|
| GLM-5.3-Flash / Maya-S24 | Maya | Worker high/max 56/58 GiB; host available ≥2 GiB; inference PSI 10% for 3 samples | Free floor native policy MiB/GPU; native cache reserve 1024 MiB; startup admission native policy | Occupancy unlimited; writes ≤128 MiB/s; combined R+W ≤160 MiB/s over 30 s; first violating complete active window stops |
| DeepSeek-V4.1-Flash-1017 / UD-IQ1_S | Maya | Worker high/max 56/58 GiB; host available ≥2 GiB; inference PSI 15% for 3 samples | Free floor native policy MiB/GPU; native cache reserve 1024 MiB; startup admission native policy | Occupancy unlimited; writes ≤128 MiB/s; combined R+W ≤160 MiB/s over 30 s; first violating complete active window stops |
| Qwen3.8-27B / AutoRound INT4, INT8 embedding | HyperQwen-vLLM | Worker high/max unlimited/unlimited GiB; host available ≥2 GiB; inference PSI 10% for 3 samples | Free floor 512 MiB/GPU; native cache reserve not applicable MiB; startup admission [9728, 8960] | Occupancy unlimited; writes ≤1 MiB/s; combined R+W ≤8 MiB/s over 30 s; first violating complete active window stops |
| Qwen3.8-27B / AutoRound INT4, INT8 embedding | SGLang | Worker high/max unlimited/unlimited GiB; host available ≥2 GiB; inference PSI 10% for 3 samples | Free floor 448 MiB/GPU; native cache reserve not applicable MiB; startup admission [11520, 8960] | Occupancy unlimited; writes ≤1 MiB/s; combined R+W ≤8 MiB/s over 30 s; first violating complete active window stops |
| Qwen3.8-Flash-Next / IQ3_XXS | Strata | Worker high/max 56/58 GiB; host available ≥2 GiB; inference PSI 15% for 3 samples | Free floor native policy MiB/GPU; native cache reserve 1024 MiB; startup admission native policy | Occupancy unlimited; writes ≤128 MiB/s; combined R+W ≤160 MiB/s over 30 s; first violating complete active window stops |
| DeepSeek-V4.1-Flash-1017 / UD-IQ1_S | Strata | Worker high/max 56/58 GiB; host available ≥2 GiB; inference PSI 15% for 3 samples | Free floor 512 MiB/GPU; native cache reserve 1024 MiB; startup admission native policy | Occupancy unlimited; writes ≤128 MiB/s; combined R+W ≤160 MiB/s over 30 s; first violating complete active window stops |
| Nemotron-3.5-Bolt-74B-A9B / AWQ INT4 | vLLM offload | Worker high/max 56/58 GiB; host available ≥2 GiB; inference PSI 10% for 3 samples | Free floor 512 MiB/GPU; native cache reserve not applicable MiB; startup admission native policy | Occupancy unlimited; writes ≤1 MiB/s; combined R+W ≤8 MiB/s over 30 s; first violating complete active window stops |

Independent qualification samples every 2 seconds and rejects any sampled host-floor, dense-VRAM, telemetry, memory-event or ≥82°C thermal violation; production supervisors also retain their sustained-sample rules. Swap active-window enforcement excludes loading and idle. Effective configured limits are not measured peaks. SGLang uses its deployed 448 MiB exception; the private legacy monitor is adapted only to that selected floor. Unlimited swap occupancy does not remove swap-I/O limits.

Base weights use decimal GB, excluding auxiliary packs and caches. Qwen engines share a checkpoint; DeepSeek engines share 232.98 GB (122.38 GB NVMe core + 110.60 GB SATA Engram). Configured contexts are retained limits, not newly tested full-window claims.

[Numeric evidence](benchmark-results/20261102-community-screens.json).
