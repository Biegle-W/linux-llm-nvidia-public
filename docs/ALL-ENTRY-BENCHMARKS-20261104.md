# All current entry benchmarks — November 4, 2026

Historical November4 index. [Current November5 engine-refresh observations](ALL-ENTRY-BENCHMARKS-20261105.md).

[Requested ComfyUI native2K/4K results](COMFY-2K4K-20261104.md): both2K profiles passed; native4K failed GPU memory/guard qualification. This is separate from the unchanged nine-entry LLM catalog.

Diffusion image workflows have a [separate ComfyUI benchmark and resource-guard report](COMFY-DUAL-GPU-20261105.md). They do not add text-model IDs to the nine-entry API/DSH catalog.

Nine entries are enabled on the96 GB-class Z690/13900KS host with RTX3080Ti/3080, CPU PCIe4 x8/x8 and host-staged transport. Bolt now selects native IQ2 on llama.cpp11909 under the historical compatibility ID`bolt-vllm`; the AWQ entry is replaced. Its normal-router check below is newer than the other eight96 GB restoration observations. No CUDA P2P or runtime update was introduced.

These are single short actual DSH read/tool-result/exact-follow-up observations with owned unload. Loading and follow-up are excluded from the first-request metrics. Contexts are allocated limits, not newly stress-qualified windows. Weights use decimal GB; HyperQwen/SGLang share their checkpoint and TensorFold's size includes its drafter. Different precision, cache states and speculation prevent an equal-quality ranking.

| Model / quant | Engine | Prefill tok/s | TTFT s | Decode tok/s | Context tokens | Storage GB | Storage location |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Qwen3.8-27B / AutoRound-INT4-fast-heads-INT8-embedding | HyperQwen-vLLM | 2065.02 | 2.852 | 62.334 | 86,016 | 15.792 | SATA SSD |
| Qwen3.8-27B / AutoRound-INT4-fast-heads-INT8-embedding | SGLang | 2211.30 | 2.790 | 60.215 | 57,344 | 15.792 | SATA SSD |
| Qwen3.8-27B / EXL3-2.0bpw | TensorFold | 575.26 | 10.135 | 186.951 | 12,288 | 13.522 | SATA SSD |
| Qwen3.8-Flash-Next / Unsloth-Dynamic-v3.1-UD-IQ1_S | llama.cpp | 120.21 | 48.674 | 35.937 | 12,288 | 66.379 | NVMe SSD |
| Qwen3.8-Flash-Next / IQ3_XXS | Strata | 934.80 | 6.205 | 63.200 | 131,072 | 75.840 | NVMe SSD |
| GLM-5.3-Flash / Maya-S24 | Maya | 546.90 | 10.199 | 15.200 | 65,536 | 94.702 | NVMe SSD |
| DeepSeek-V4.1-Flash-1017 / UD-IQ1_S (Unsloth Dynamic3.1) | Maya | 217.10 | 27.452 | 7.100 | 32,768 | 232.980 | NVMe + SATA SSDs |
| NVIDIA-Nemotron-3.5-Bolt-74B-A9B / native-IQ2 | llama.cpp11909 | 502.58 | 12.870 | 68.046 | 163,840 | 22.018 | SATA SSD |
| DeepSeek-V4.1-Flash-1017 / UD-IQ1_S (Unsloth Dynamic3.1) | Strata | 29.10 | 5.840 | 12.200 | 32,768 | 232.980 | NVMe + SATA SSDs |

TensorFold's decode is a short DFlash2-4bit/copies tool burst. DeepSeek/Strata reused5,539 of5,707 prompt tokens; its prefill figure covers the uncached remainder and TTFT is cached-prompt evidence. All other rows report zero native prompt-cache reuse; OS file caches were not dropped. Client TTFT includes parser/SSE buffering. [Bolt's maintained entry, selected placement and slowdown diagnosis](BOLT-IQ2-ENTRY-20261104.md), [eight other current observations and detailed resources](RAM96-RESTORATION-20261104.md).

## Current guards

All profiles retain2 GiB host available,82 C/three bad2-second resource samples, fail-closed telemetry and unlimited swap occupancy. Active swap rates are writes/combined MiB/s over30 seconds; pressure is full PSI with3 bad samples. Short runs may not fill that window. Current-boot transport, ownership/admission, swappiness60, parallel1 and idle600 remain. Exact byte caps for RAM-heavy workers retain2 GiB outside the hard cap. The native Bolt fit target384 MiB/card is separate from its independent256 MiB free-VRAM floor.

| Profile | Worker RAM high/max GiB | GPU policy | Active swap writes/combined | Active/loading PSI % |
| --- | ---: | --- | ---: | --- |
| qwen27b-hyperqwen | 32.00/36.00 | 256 MiB free/card after ready | 1/8 | 10 / none separately |
| qwen27b-sglang | 32.00/36.00 | 256 MiB free/card after ready | 1/8 | 10 / none separately |
| qwen27b-tensorfold | 32.00/36.00 | 256 MiB free/card after ready; GPU0; native1024 MiB reserve | 1/8 | 10 / none separately |
| flash-next-iq1s-llamacpp | 87.77/89.77 | 256 MiB free/card after ready; 1536 MiB fit targets | 128/160 | 15 / none separately |
| flash-next-strata | 87.77/89.77 | 1024 MiB native reserve | 128/160 | 15 / none separately |
| glm-maya | 87.77/89.77 | 1024 MiB native reserve | 128/160 | 10 / none separately |
| deepseek-maya | 87.77/89.77 | 1024 MiB native reserve | 128/160 | 15 / none separately |
| bolt-vllm | 87.77/89.77 | 256 MiB free/card after ready; 384 MiB fit targets | 1/8 | 10 / 15 |
| deepseek-unsloth-strata | 87.77/89.77 | 256 MiB free/card after ready; 1024 MiB native reserve | 128/160 | 15 / 15 |

## Historical evidence retained

The same-day AWQ baseline remains217.35 prefill /29.320 s TTFT /0.361 decode at163,840 context,55.333 GB SATA; it is not current performance of the compatibility ID. Native2-bit384/512 MiB candidate arms and the rejected256 MiB arm remain in[the fit study](BOLT-NATIVE-IQ2-20261104.md). [Former complete index before replacement](ALL-ENTRY-BENCHMARKS-PRE-IQ2-20261104.md) retains earlier32/64 GB results, guard tables and all recent successful observations. No historical result was overwritten or relabeled.

[Machine-readable current index and retained references](benchmark-results/20261104-all-entry-benchmarks.json). All nine remain registered and workers finish unloaded.
