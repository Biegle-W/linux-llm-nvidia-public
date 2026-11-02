# All maintained models through the API-only router — November 1, 2026

Seven of eight profiles passed an actual DSH read-tool call with matching fixture contents and owned unload. Super/vLLM stopped during loading on its unchanged pressure guard and returned HTTP 503 before readiness. Both workers are inactive and no GPU reservation remains. No fallback was loaded.

The authenticated gateway on port 10100 forwarded these calls through the private hub on 10101 to guarded backends. Unlock health was VERIFIED before and after. The root-owned current-boot 16 MiB seeded bidirectional P2P proof passed three remote read/write patterns each way, with 13.083/13.084 GB/s peer copy. This revalidated the current-boot proof, without running a new compute throughput sweep.

Hardware: RTX 3080 Ti 12 GB + RTX 3080 10 GB, 64 GB installed RAM. One short call per row, no averaging; model loading and follow-up answer excluded. Configured contexts are calculated limits, not new full-window quality qualification.

## VRAM-only

| Model / quant | Engine | Prefill (tok/s) | Time to first token (s) | Decode (tok/s) | Context limit (tokens) | Storage size (GB) | Storage location |
|---|---|---:|---:|---:|---:|---:|---|
| Qwen3.8-27B / AutoRound-INT4-fast-heads-INT8-embedding | HyperQwen-vLLM | 2297.66 | 2.547 | 64.074 | 40,960 | 15.79 | SATA SSD: models/engine-tests/qwen38-27b-hyperqwen-fast |
| Qwen3.8-27B / AutoRound-INT4-fast-heads-INT8-embedding | SGLang | 2331.76 | 2.646 | 58.801 | 32,768 | 15.79 | SATA SSD: models/engine-tests/qwen38-27b-hyperqwen-fast |

## CPU RAM offload

| Model / quant | Engine | Prefill (tok/s) | Time to first token (s) | Decode (tok/s) | Context limit (tokens) | Storage size (GB) | Storage location |
|---|---|---:|---:|---:|---:|---:|---|
| NVIDIA-Nemotron-3.5-Bolt-74B-A9B / AWQ-INT4 | vLLM-offload | 234.14 | 27.201 | 0.390 | 163,840 | 55.33 | SATA SSD: models/bolt-awq-int4 |

## SSD streaming

| Model / quant | Engine | Prefill (tok/s) | Time to first token (s) | Decode (tok/s) | Context limit (tokens) | Storage size (GB) | Storage location |
|---|---|---:|---:|---:|---:|---:|---|
| Qwen3.8-Flash-Next / IQ3_XXS | Strata | 506.20 | 11.679 | 60.200 | 131,072 | 75.84 | NVMe SSD: models/strata/models/IQ3_XXS |
| GLM-5.3-Flash / Maya-S24 | Maya | 74.90 | 74.943 | 1.700 | 65,536 | 94.70 | NVMe SSD: models/maya/Maya-S24 |
| DeepSeek-V4.1-Flash-1017 / UD-IQ1_S (Unsloth Dynamic3.1) | Maya | 57.20 | 100.413 | 1.600 | 32,768 | 232.98 | NVMe + SATA SSDs: models/unsloth/deepseek-v41-1017-dynamic31-8a6ec9cf/UD-IQ1_S |
| DeepSeek-V4.1-Flash-1017 / UD-IQ1_S (Unsloth Dynamic3.1) | Strata | 7.60 | 22.631 | 3.700 | 32,768 | 232.98 | NVMe + SATA SSDs: models/unsloth/deepseek-v41-1017-dynamic31-8a6ec9cf/UD-IQ1_S |
| NVIDIA-Nemotron-3.5-Super-VL-120B-A12B / W4A16-Merlin | vLLM-offload | Not measured | Not measured | Not measured | 65,536 | 72.89 | SATA weights; NVMe working cache: models/nemotron-super-int4 |

## Measurement and failure details

| Profile | Input / cached / output tokens | Tool roundtrip (s) | Result |
|---|---:|---:|---|
| qwen27b-hyperqwen | 5826 / 0 / 40 | 5.41 | Passed; owned unload |
| qwen27b-sglang | 6089 / 0 / 37 | 4.41 | Passed; owned unload |
| bolt-vllm | 6366 / 0 / 41 | 131.04 | Passed; owned unload |
| flash-next-strata | 5597 / 0 / 41 | 15.09 | Passed; owned unload |
| glm-maya | 5437 / 0 / 25 | 89.26 | Passed; owned unload |
| deepseek-maya | 5704 / 0 / 60 | 138.73 | Passed; owned unload |
| deepseek-unsloth-strata | 5710 / 5539 / 61 | 40.84 | Passed; owned unload |
| super-vllm | Not measured | Not reached | Loading-pressure stop; worker inactive |

DeepSeek/Strata reused 5,539 prompt tokens; its 7.6 tok/s prefill is for the 171-token uncached suffix. Other passing calls reported zero cached tokens. Strata/Maya TTFT is client first delivered content/tool delta and includes parser buffering; HyperQwen, SGLang and Bolt use engine first-token counters. Decode uses native timing/counter evidence, including generated tool arguments. These different cache states and timing definitions limit cross-engine comparisons.

Super loading pressure exceeded 15% for three consecutive samples: 21.37%, 28.00%, 23.11%. The supervisor stopped it after about 66.76 seconds. The journal reported 52.4 GiB memory peak and 4.8 GiB swap peak. No prefill, TTFT, decode or tool success is claimed for this attempt; earlier Super results remain historical. Resource guards and model settings were preserved.

Storage sizes count base weights in decimal GB, excluding auxiliary packs and working caches. Qwen engines share one checkpoint; DeepSeek engines share one checkpoint (122.38 GB NVMe core + 110.60 GB SATA Engram). Bolt supplies host weights to GPU kernels. Super has SATA weights and a bounded NVMe working cache.

[Numeric evidence](benchmark-results/20261101-new-router-all-models.json). [Earlier observations](SHORT-TOOL-BENCHMARKS-20261101.md) remain dated evidence.
