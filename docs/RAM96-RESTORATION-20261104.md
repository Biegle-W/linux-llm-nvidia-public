# 96 GB restoration and two-GiB headroom — November 4, 2026

**Later selected-entry update:** native IQ2/llama.cpp has replaced the AWQ Bolt API/DSH entry under compatibility ID`bolt-vllm`. [Current Bolt entry and research](BOLT-IQ2-ENTRY-20261104.md). The AWQ row and nine-model results below retain their earlier restoration-stage configuration and are historical evidence for Bolt.

All nine profiles passed one normal-router actual DSH read/tool-result/exact-follow-up and owned unload on the corrected boot. Five paused profiles are restored in the API and DSH. Early GPU unlock and current-boot host-staged transport proof passed after the user disabled Secure Boot. Linux reports 96,227,660 KiB / 91.76984787 GiB usable RAM; the RTX 3080 Ti / RTX 3080 use CPU PCIe4 x8/x8 without CUDA peer access. This does not establish a P2P comparison.

At the user's request the six RAM-heavy profiles leave **exactly 2 GiB outside the hard worker limit**: MemoryMax 96,389,640,192 bytes (89.76984787 GiB), MemoryHigh 94,242,156,544 bytes (87.76984787 GiB). Reclaim starts 2 GiB before the hard cap. These are fixed measured-boot settings, not an automatic expansion on future hardware. The separate 2 GiB available-host-memory stop remains. Dense GPU-resident profiles retain 32/36 GiB. Every profile requires at least 90 GiB Linux MemTotal before loading these settings. Effective kernel byte limits were verified in every check.

## Short actual-tool measurements

Loading and follow-up are excluded from prefill/TTFT/decode. Contexts are allocated limits, not newly stress-qualified windows. Weights use decimal GB; the TensorFold total includes its drafter, and HyperQwen/SGLang share weights.

| Model / quant | Engine | Prefill tok/s | TTFT s | Decode tok/s | Context tokens | Storage GB | Storage location |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Qwen3.8-27B / AutoRound-INT4-fast-heads-INT8-embedding | HyperQwen-vLLM | 2065.02 | 2.852 | 62.33 | 86,016 | 15.792 | SATA SSD |
| Qwen3.8-27B / AutoRound-INT4-fast-heads-INT8-embedding | SGLang | 2211.30 | 2.790 | 60.21 | 57,344 | 15.792 | SATA SSD |
| Qwen3.8-27B / EXL3-2.0bpw | TensorFold | 575.26 | 10.135 | 186.95 | 12,288 | 13.522 | SATA SSD |
| Qwen3.8-Flash-Next / Unsloth-Dynamic-v3.1-UD-IQ1_S | llama.cpp11909 | 120.21 | 48.674 | 35.94 | 12,288 | 66.379 | NVMe SSD |
| Qwen3.8-Flash-Next / IQ3_XXS | Strata | 934.80 | 6.205 | 63.20 | 131,072 | 75.840 | NVMe SSD |
| GLM-5.3-Flash / Maya-S24 | Maya | 546.90 | 10.199 | 15.20 | 65,536 | 94.702 | NVMe SSD |
| DeepSeek-V4.1-Flash-1017 / UD-IQ1_S (Unsloth Dynamic3.1) | Maya | 217.10 | 27.452 | 7.10 | 32,768 | 232.980 | NVMe + SATA SSDs |
| NVIDIA-Nemotron-3.5-Bolt-74B-A9B / AWQ-INT4 | vLLM-offload | 217.35 | 29.320 | 0.36 | 163,840 | 55.333 | SATA SSD |
| DeepSeek-V4.1-Flash-1017 / UD-IQ1_S (Unsloth Dynamic3.1) | Strata | 29.10 | 5.840 | 12.20 | 32,768 | 232.980 | NVMe + SATA SSDs |

These are single short-call observations, not a quality ranking or sustained throughput test. TensorFold uses DFlash2-4bit/copies and its decode figure is a short speculative tool-argument burst. Client TTFT includes tool-parser/SSE buffering. Native cache counters and timing methods are retained in the numeric record; OS file caches were not dropped. The current DeepSeek/Strata request reused 5,539 of 5,707 prompt tokens from its native persistent cache; its 29.1 prefill tok/s covers only the uncached remainder, and its TTFT is a cached-prompt observation. DeepSeek/Strata's historical reference reused 5,539 of 5,710 prompt tokens, so its older prefill figure cannot be compared as a cold full-prompt speed. The already completed matching-policy HyperQwen check was retained when the user changed the RAM-heavy limits; it was not replayed to select a better score.

## Effective guard policy

All rows retain host-available reserve 2 GiB, thermal stop 82 C with three bad two-second resource samples, fail-closed telemetry, unlimited swap occupancy, 30-second active I/O windows and three bad pressure samples. Rates are writes / reads+writes MiB/s; pressure is full PSI. Active windows reset outside inference. A short run may not fill a complete active window. Current-boot transport, ownership/admission, swappiness60, parallel1 and idle600 remain. No guard was disabled.

| Profile | Worker RAM high/max GiB | GPU policy | Active swap writes/combined | Active / loading PSI % |
| --- | ---: | --- | ---: | --- |
| qwen27b-hyperqwen | 32.00/36.00 | 256 MiB free/card after ready | 1/8 | 10 / none separately |
| qwen27b-sglang | 32.00/36.00 | 256 MiB free/card after ready | 1/8 | 10 / none separately |
| qwen27b-tensorfold | 32.00/36.00 | GPU0; native 1024 MiB reserve; 256 MiB free/card after ready | 1/8 | 10 / none separately |
| flash-next-iq1s-llamacpp | 87.77/89.77 | 256 MiB free/card after ready; 1536 MiB fit targets | 128/160 | 15 / none separately |
| flash-next-strata | 87.77/89.77 | 1024 MiB native reserve | 128/160 | 15 / none separately |
| glm-maya | 87.77/89.77 | 1024 MiB native reserve | 128/160 | 10 / none separately |
| deepseek-maya | 87.77/89.77 | 1024 MiB native reserve | 128/160 | 15 / none separately |
| bolt-vllm | 87.77/89.77 | 256 MiB free/card after ready | 1/8 | 10 / 15 |
| deepseek-unsloth-strata | 87.77/89.77 | 256 MiB free/card after ready; 1024 MiB native reserve | 128/160 | 15 / 15 |

## Sampled resources and release

Telemetry samples can miss transient peaks. Cgroup charged memory includes file-cache charging; MemAvailable includes reclaimable cache and is not MemFree. GPU loading transients are recorded separately from after-ready floors. The numeric record preserves both, plus active-window coverage and pressure readings.

| Profile | Peak charged RAM GiB | Peak swap MiB | Minimum host available GiB | Minimum nonloading GPU free MiB (0/1) | Max GPU C (0/1) | Tool / follow-up / unload |
| --- | ---: | ---: | ---: | --- | --- | --- |
| qwen27b-hyperqwen | 22.16 | 0.0 | 81.16 | 3305/1316 | 52/42 | PASS / PASS / PASS |
| qwen27b-sglang | 8.90 | 0.0 | 80.37 | 528/1847 | 52/39 | PASS / PASS / PASS |
| qwen27b-tensorfold | 15.45 | 0.0 | 84.99 | 1489/9928 | 65/34 | PASS / PASS / PASS |
| flash-next-iq1s-llamacpp | 37.05 | 0.0 | 86.56 | 1593/1512 | 61/38 | PASS / PASS / PASS |
| flash-next-strata | 82.87 | 0.0 | 42.99 | 547/638 | 57/40 | PASS / PASS / PASS |
| glm-maya | 75.52 | 0.0 | 16.33 | 799/818 | 59/44 | PASS / PASS / PASS |
| deepseek-maya | 80.46 | 0.0 | 83.03 | 853/858 | 59/49 | PASS / PASS / PASS |
| bolt-vllm | 50.52 | 0.0 | 38.66 | 5643/3654 | 59/47 | PASS / PASS / PASS |
| deepseek-unsloth-strata | 63.67 | 0.0 | 33.91 | 921/940 | 59/48 | PASS / PASS / PASS |

## Dated reference comparison

These changes compare single observations across different RAM/cache/topology conditions, not a controlled causal estimate. The first four older entries used the 32 GB host; the others used the earlier 64 GB switched host. DeepSeek/Strata prefill is omitted from comparison because its older prompt was mostly cached.

| Profile | Earlier prefill / decode tok/s | Current prefill / decode tok/s | Observed decode change |
| --- | --- | --- | ---: |
| qwen27b-hyperqwen | 2065.24 / 62.59 | 2065.02 / 62.33 | -0.4% |
| qwen27b-sglang | 2232.88 / 60.23 | 2211.30 / 60.21 | -0.0% |
| qwen27b-tensorfold | 580.96 / 180.34 | 575.26 / 186.95 | +3.7% |
| flash-next-iq1s-llamacpp | 88.79 / 31.10 | 120.21 / 35.94 | +15.5% |
| flash-next-strata | 506.20 / 60.20 | 934.80 / 63.20 | +5.0% |
| glm-maya | 342.40 / 7.10 | 546.90 / 15.20 | +114.1% |
| deepseek-maya | 198.80 / 4.80 | 217.10 / 7.10 | +47.9% |
| bolt-vllm | 240.66 / 0.39 | 217.35 / 0.36 | -7.9% |
| deepseek-unsloth-strata | cached; incomparable / 3.70 | 29.10 / 12.20 | +229.7% |

## Selected caches and pinning

Flash-Next IQ1_S keeps mmap/lazy mode and the NVMe n-gram table. Flash-Next IQ3 restores the previously qualified resident non-GPU-cache complement. GLM/Maya uses a 64 decimal GB native RAM tier. DeepSeek/Maya uses a 64 GiB file-cache target, 56 decimal GB startup warming cap and 8 decimal GB decode warming. DeepSeek/Strata uses a 64 decimal GB CPU expert store. Bolt retains its qualified unpinned host-prefetch adapter; the earlier pinned experiment remains rejected evidence. Dense weight placement, contexts, quantization, native reserves, runtime/source pins and defaults are preserved. Additional RAM does not expand VRAM-bound dense context/drafter allocations.

[Forum and upstream pinning research](RAM96-PREPARATION-20261104.md#forum-research-and-pinning-decisions) informed bounded supported settings; newer unsupported pin/copy flags, global mlock and an engine upgrade were not selected. These settings passed the requested short checks, which do not establish a universal optimum. Daily updates remain paused.

446 CPU regressions passed, including fractional-GiB byte-exact systemd/cgroup limits and the installed-capacity gate. The current software can represent those byte limits without rounding. API/hub/DSH finish healthy, all model workers unloaded and the reservation released; all nine entries remain available. Earlier preparation and 32/64 GB benchmark artifacts remain dated evidence, superseded for current operation by this report. [Sanitized numeric results, methods, resource samples and older references](benchmark-results/20261104-ram96-restoration.json).
