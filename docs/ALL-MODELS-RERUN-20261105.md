# All downloaded model coverage and rerun — November 5, 2026

Fresh tests on the i9-13900KS, 96GB-class RAM and RTX3080Ti12GB plus RTX308010GB. Both GPUs use host-staged PCIe4x8/x8 with CUDA P2P unavailable. Nine text entries and four ComfyUI entries passed their selected guarded checks. Separately downloaded vision-adapter outcomes appear below.

Each text row is one actual DSH read tool generation followed by executed tool/result, exact proof follow-up and owned unload. Loading and follow-up are excluded from performance timing. Native engine request timing or one-request counters provide prefill/decode. TensorFold uses the native TPOT inverse for a short DFlash2 speculative tool burst. All first calls report zero cached prompt tokens. OS file caches were retained. Prompt/output lengths differ by tokenizer and appear in the machine-readable evidence. No aggregation, sustained test or full-window quality claim.

## VRAM-only models

| Model / quant | Engine | Prefill (tok/s) | Time to first token (s) | Decode (tok/s) | Context limit (tokens) | Storage size (GB) | Storage location |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Qwen3.8-27B / AutoRound-INT4-fast-heads-INT8-embedding | HyperQwen-vLLM | 2100.79 | 2.783 | 62.343 | 86,016 | 15.792 | SATA, `models/engine-tests/qwen38-27b-hyperqwen-fast` |
| Qwen3.8-27B / AutoRound-INT4-fast-heads-INT8-embedding | SGLang | 2130.13 | 2.897 | 60.121 | 57,344 | 15.792 | SATA, `models/engine-tests/qwen38-27b-hyperqwen-fast` |

## MoE models with CPU RAM offload

Bolt retains its qualified minimum CPU-mapped weight component while most weights execute on both GPUs. The previous native placement audit recorded 89.4% GPU weight-buffer bytes and 2.18 GiB CPU-mapped weights. This rerun does not newly measure residency or isolate CPU expert execution.

| Model / quant | Engine | Prefill (tok/s) | Time to first token (s) | Decode (tok/s) | Context limit (tokens) | Storage size (GB) | Storage location |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| NVIDIA-Nemotron-3.5-Bolt-74B-A9B / native-IQ2 | llama.cpp | 496.94 | 12.991 | 67.172 | 163,840 | 22.018 | SATA, `models/engine-tests/bolt-iq2` |

## MoE models with SSD streaming

| Model / quant | Engine | Prefill (tok/s) | Time to first token (s) | Decode (tok/s) | Context limit (tokens) | Storage size (GB) | Storage location |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Qwen3.8-Flash-Next / IQ3_XXS | Strata | 934.00 | 6.482 | 62.700 | 131,072 | 75.840 | NVMe, `models/strata/models/IQ3_XXS` |
| GLM-5.3-Flash / Maya-S24 | Maya | 552.20 | 10.057 | 15.000 | 65,536 | 94.702 | NVMe, `models/maya/Maya-S24` |
| DeepSeek-V4.1-Flash-1017 / UD-IQ1_S (Unsloth Dynamic3.1) | Maya | 184.10 | 32.195 | 7.900 | 32,768 | 232.980 | NVMe core + SATA Engram, `models/unsloth/deepseek-v41-1017-dynamic31-8a6ec9cf/UD-IQ1_S` |
| DeepSeek-V4.1-Flash-1017 / UD-IQ1_S (Unsloth Dynamic3.1) | Strata | 87.10 | 65.591 | 12.000 | 32,768 | 232.980 | NVMe core + SATA Engram, `models/unsloth/deepseek-v41-1017-dynamic31-8a6ec9cf/UD-IQ1_S` |
| Qwen3.8-Flash-Next / Unsloth-Dynamic-v3.1-UD-IQ1_M | Strata | 1079.50 | 5.328 | 77.900 | 131,072 | 68.007 | NVMe, `models/unsloth/flash-next-iq1m-v31` |

## Other host-backed selected profiles

TensorFold is a dense model with host-mapped embeddings and GPU0 DFlash2 execution.

| Model / quant | Engine | Prefill (tok/s) | Time to first token (s) | Decode (tok/s) | Context limit (tokens) | Storage size (GB) | Storage location |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Qwen3.8-27B / EXL3-2.0bpw | TensorFold | 570.85 | 10.218 | 190.767 | 12,288 | 9.673 | SATA, `models/engine-tests/qwen38-27b-tensorfold-mia-exl3-2bpw` |

Storage is decimal GB of checkpoint GGUF/safetensors files only. Shared Qwen and DeepSeek checkpoints repeat across engine rows but occupy storage once. Separate native packs, MTP/draft files and model tables remain in the coverage manifest.

## Effective resource guards

Configured limits are separate from observed usage. All entries retain 2 GiB host available, 100 C stop, three bad 2-second samples, fail-closed telemetry, swappiness 60, concurrency 1 and idle 600s. Swap occupancy is unlimited. I/O rates average over 30 seconds with three bad 2-second samples before stopping. Active full-PSI thresholds require three bad samples. Short calls can finish before the averaging window fills. Native cache reserves and llama fit targets differ from explicit free-VRAM floors. This report does not derive peak RAM or minimum VRAM from configured limits.

| Model / quant | Engine | RAM guards | VRAM guards | Swap guards |
| --- | --- | --- | --- | --- |
| qwen27b-hyperqwen / AutoRound-INT4-fast-heads-INT8-embedding | HyperQwen-vLLM |87.77/89.77GiB high/max,2GiB host reserve, active PSI 10%, no separate loading threshold | 256MiB free/card after readiness | Unlimited occupancy, 1/8MiB/s write/combined over30s |
| qwen27b-sglang / AutoRound-INT4-fast-heads-INT8-embedding | SGLang |87.77/89.77GiB high/max,2GiB host reserve, active PSI 10%, no separate loading threshold | 256MiB free/card after readiness | Unlimited occupancy, 1/8MiB/s write/combined over30s |
| flash-next-strata / IQ3_XXS | Strata |87.77/89.77GiB high/max,2GiB host reserve, active PSI 15%, no separate loading threshold | Native reserve guard + 1024MiB native reserve/fit target | Unlimited occupancy, 128/160MiB/s write/combined over30s |
| glm-maya / Maya-S24 | Maya |87.77/89.77GiB high/max,2GiB host reserve, active PSI 10%, no separate loading threshold | Native reserve guard + 1024MiB native reserve/fit target | Unlimited occupancy, 128/160MiB/s write/combined over30s |
| deepseek-maya / UD-IQ1_S (Unsloth Dynamic3.1) | Maya |87.77/89.77GiB high/max,2GiB host reserve, active PSI 15%, no separate loading threshold | Native reserve guard + 1024MiB native reserve/fit target | Unlimited occupancy, 128/160MiB/s write/combined over30s |
| bolt-vllm / native-IQ2 | llama.cpp |87.77/89.77GiB high/max,2GiB host reserve, active/loading PSI 10/15% | 256MiB free/card after readiness + 384MiB native reserve/fit target | Unlimited occupancy, 1/8MiB/s write/combined over30s |
| deepseek-unsloth-strata / UD-IQ1_S (Unsloth Dynamic3.1) | Strata |87.77/89.77GiB high/max,2GiB host reserve, active/loading PSI 15/15% | 256MiB free/card after readiness + 1024MiB native reserve/fit target | Unlimited occupancy, 128/160MiB/s write/combined over30s |
| qwen27b-tensorfold / EXL3-2.0bpw | TensorFold |87.77/89.77GiB high/max,2GiB host reserve, active PSI 10%, no separate loading threshold | 256MiB free/card after readiness + 1024MiB native reserve/fit target, GPU0 execution | Unlimited occupancy, 1/8MiB/s write/combined over30s |
| flash-next-iq1m-strata / Unsloth-Dynamic-v3.1-UD-IQ1_M | Strata |87.77/89.77GiB high/max,2GiB host reserve, active PSI 15%, no separate loading threshold | 256MiB free/card after readiness + 1024MiB native reserve/fit target | Unlimited occupancy, 128/160MiB/s write/combined over30s |
| qwen-image-2.1-turbo | ComfyUI |87.77/89.77GiB high/max,2GiB host reserve, active/loading PSI10/15% |256MiB free/card, three bad2s samples, both GPUs, GPU-only neural execution |Unlimited occupancy,1/8MiB/s write/combined over30s |
| flux3-klein | ComfyUI |87.77/89.77GiB high/max,2GiB host reserve, active/loading PSI10/15% |256MiB free/card, three bad2s samples, both GPUs, GPU-only neural execution |Unlimited occupancy,1/8MiB/s write/combined over30s |
| wan22-5b | ComfyUI |87.77/89.77GiB high/max,2GiB host reserve, active/loading PSI10/15% |256MiB free/card, three bad2s samples, both GPUs, GPU-only neural execution |Unlimited occupancy,1/8MiB/s write/combined over30s |
| ltx23-mesh | ComfyUI |87.77/89.77GiB high/max,2GiB host reserve, active/loading PSI10/15% |256MiB free/card, three bad2s samples, both GPUs, GPU-only neural execution |Unlimited occupancy,1/8MiB/s write/combined over30s |

## Image and video results

Images use seeds27001 and27002, with one run per seed per size. The first run includes fresh-worker model-stage initialization. Videos use seed27001 and33frames per resolution, including text encoding, sampling, decoding and output serialization. LTX includes generated audio. Worker launch/loading outside the workflow request is excluded. All runs passed GPU-only forward audits and owned worker/reservation cleanup.

| Entry | Resolution | First run seconds | Second run seconds |
| --- | --- | ---: | ---: |
| qwen-image-2.1-turbo |1024×1024|28.349|4.054|
| qwen-image-2.1-turbo |2048×2048|30.315|26.288|
| flux3-klein |1024×1024|19.212|5.066|
| flux3-klein |2048×2048|27.305|24.377|
| wan22-5b |512×288|51.558|One clip|
| wan22-5b |1280×720|67.694|One clip|
| wan22-5b |1920×1080|170.818|One clip|
| ltx23-mesh |512×288|84.930|One clip|
| ltx23-mesh |1280×720|53.616|One clip|
| ltx23-mesh |1920×1080|75.839|One clip|

The rerun covers configured passing image options 1024/2048 and all video options 512×288/720p/1080p. Native 4K image shapes remain earlier failed qualifications and were not repeated.

## Separately downloaded vision adapters

| Owning profile | Actual image test | Asset access observed | Cleanup |
| --- | --- | --- | --- |
| flash-next-strata | PASS — Red | True | Worker inactive True, preset unchanged |
| glm-maya | PASS — Green | True | Worker inactive True, preset unchanged |
| deepseek-maya | PASS — Blue | True | Worker inactive True, preset restored True |

The initial GLM adapter request failed because the configured encoder executable was missing after the earlier frontend refresh. Its archived installed encoder was restored, and the adapter was retried. The updater now preserves this separate installed encoder directory with protected hashes during Maya frontend staging. 31 focused updater tests and 508 full CPU regressions pass. Flash-Next uses its selected CPU vision encoder. GLM uses its selected GPU encoder with native cache lending. DeepSeek needs a separate metadata-only pack and temporary vision-enabled preset to exercise its downloaded tower. Its original selected preset is restored after owned unload. Adapter tests inherit their owning profile guards and test one 512×512 solid-color image each.

## Disk coverage and remaining limitations

The managed model tree, its resolved SATA store and Hugging Face cache were checked. No unmatched complete large checkpoints were found outside the managed tree. Ollama and LMStudio model stores are absent. The manifest accounts for every discovered model-format file, including symlink aliases and small metadata. The initial large-file audit counted 46 unique physical files of at least 100 MB, including derived packs and a generated GLM prompt cache.

Every standalone main checkpoint has a fresh owning-profile result above. Text encoders, all image/video VAEs, LTX text projection, Flash MTP and TensorFold DFlash2 are exercised by their owning workflows. Derived dense packs and generated prompt caches are accounted for separately. Optional integrated Qwen vision and MTP heads are present inside the text checkpoints, but their separate modes remain unqualified under the selected dense configurations. The downloaded optional Qwen MTP tensors are retained disabled following earlier VRAM failures. These optional modes are not separate downloaded model entries.

[Machine-readable measurements, token lengths, guard values and full asset coverage](benchmark-results/20261105-all-models-rerun.json). Earlier observations remain in the [previous current index](ALL-ENTRY-BENCHMARKS-20261105.md).
