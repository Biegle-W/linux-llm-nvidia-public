# Short actual-tool benchmark observations — November 1, 2026

All eight profiles completed an actual DSH read call with a matching fixture result, followed by owned unload. Measurements cover the same first tool-call generation. Loading and the intentionally blocked follow-up answer are excluded. Each row is one short observation, with no averaging. Hardware: RTX 3080 Ti 12 GB + RTX 3080 10 GB, 64 GB installed RAM. Temporary P2P audit instrumentation was enabled. No full-context, sustained, repeated-reload suite or timed-idle test ran. Configured windows are calculated limits, not newly tested full-window quality.

## VRAM-only

| Model / quant | Engine | Prefill (tok/s) | Time to first token (s) | Decode (tok/s) | Context limit (tokens) | Storage size (GB) | Storage location |
|---|---|---:|---:|---:|---:|---:|---|
| Qwen3.8-27B / AutoRound-INT4-fast-heads-INT8-embedding | HyperQwen-vLLM | 2342.64 | 2.495 | 64.798 | 40,960 | 15.79 | SATA SSD: models/engine-tests/qwen38-27b-hyperqwen-fast |
| Qwen3.8-27B / AutoRound-INT4-fast-heads-INT8-embedding | SGLang | 2470.02 | 2.502 | 59.361 | 32,768 | 15.79 | SATA SSD: models/engine-tests/qwen38-27b-hyperqwen-fast |

## CPU RAM offload

| Model / quant | Engine | Prefill (tok/s) | Time to first token (s) | Decode (tok/s) | Context limit (tokens) | Storage size (GB) | Storage location |
|---|---|---:|---:|---:|---:|---:|---|
| NVIDIA-Nemotron-3.5-Bolt-74B-A9B / AWQ-INT4 | vLLM-offload | 235.60 | 27.032 | 0.388 | 163,840 | 55.33 | SATA SSD: models/bolt-awq-int4 |

## SSD streaming

| Model / quant | Engine | Prefill (tok/s) | Time to first token (s) | Decode (tok/s) | Context limit (tokens) | Storage size (GB) | Storage location |
|---|---|---:|---:|---:|---:|---:|---|
| Qwen3.8-Flash-Next / IQ3_XXS | Strata | 792.40 | 7.582 | 61.700 | 131,072 | 75.84 | NVMe SSD: models/strata/models/IQ3_XXS |
| GLM-5.3-Flash / Maya-S24 | Maya | 107.10 | 51.957 | 2.500 | 65,536 | 94.70 | NVMe SSD: models/maya/Maya-S24 |
| DeepSeek-V4.1-Flash-1017 / UD-IQ1_S (Unsloth Dynamic3.1) | Maya | 56.80 | 101.244 | 1.600 | 32,768 | 232.98 | NVMe + SATA SSDs: models/unsloth/deepseek-v41-1017-dynamic31-8a6ec9cf/UD-IQ1_S |
| DeepSeek-V4.1-Flash-1017 / UD-IQ1_S (Unsloth Dynamic3.1) | Strata | 7.30 | 23.128 | 3.600 | 32,768 | 232.98 | NVMe + SATA SSDs: models/unsloth/deepseek-v41-1017-dynamic31-8a6ec9cf/UD-IQ1_S |
| NVIDIA-Nemotron-3.5-Super-VL-120B-A12B / W4A16-Merlin | vLLM-offload | 60.06 | 106.160 | 0.249 | 65,536 | 72.89 | SATA weights; NVMe working cache: models/nemotron-super-int4 |

Base checkpoint GGUF/safetensors sizes use decimal GB. The Qwen engines share one 15.79 GB checkpoint; the two Unsloth DeepSeek engines share one 232.98 GB checkpoint (122.38 GB NVMe core + 110.60 GB SATA Engram). Super weights are on SATA, with its bounded processed working cache on NVMe. Prepared packs, working caches and other auxiliary assets are excluded. Bolt uses host offload to GPU kernels; Strata/Maya retain bounded host caches within their SSD-streaming profiles.

## Measurement details

| Profile | Input / cached / output tokens | Tool round trip (s) | TTFT method |
|---|---:|---:|---|
| qwen27b-hyperqwen | 5820 / 0 / 38 | 4.41 | engine first-token counter |
| qwen27b-sglang | 6095 / 0 / 39 | Not retained | engine first-token counter |
| bolt-vllm | 6366 / 0 / 41 | 131.19 | engine first-token counter |
| flash-next-strata | 5597 / 0 / 41 | 10.42 | client first delivered content/tool delta; parser buffering included |
| glm-maya | 5437 / 0 / 25 | 61.88 | client first delivered content/tool delta; parser buffering included |
| deepseek-maya | 5704 / 0 / 60 | 139.99 | client first delivered content/tool delta; parser buffering included |
| deepseek-unsloth-strata | 5707 / 5539 / 60 | 41.71 | client first delivered content/tool delta; parser buffering included |
| super-vllm | 6366 / 0 / 41 | 268.78 | engine first-token counter |

Prefill rates exclude reported reused tokens. Persistent native conversation KV may survive process reload, so cache reuse is shown rather than assumed absent. These short functional-tool observations are not a controlled uncached throughput comparison. Strata/Maya decode uses native request clocks; vLLM uses (output tokens − 1) divided by native decode time, and SGLang uses native inter-token interval count/time. Client TTFT includes tool-parser buffering where labeled; it is not an exact engine-first-token timestamp. Different lengths, cache states and clock definitions limit comparisons.

HyperQwen’s earlier 64K/768 MiB KV setting left only 368 MiB free on GPU 1 and was stopped by the unchanged 512 MiB free-VRAM guard. Its selected allocation was reduced to a 448 MiB KV pool and a calculated 40,960-token window before the passing short tool capture; native KV capacity was 47,786 tokens and GPU 1 had 678 MiB free at readiness. Timing-tap faults separately caused missing Flash/GLM/Unsloth-Strata timing artifacts. Only these affected captures were corrected after serialized owned unload. Original evidence is retained privately. SGLang’s actual matching tool result succeeded before the intentionally blocked follow-up returned 409; its status and native interval rate were recovered from saved evidence without another model call.

[Sanitized numeric evidence](benchmark-results/20261101-short-tool.json). Earlier benchmark reports remain dated evidence and do not describe the newer Unsloth Maya replacement.
