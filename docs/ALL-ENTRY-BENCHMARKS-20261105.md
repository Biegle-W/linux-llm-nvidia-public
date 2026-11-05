# Current entry observations — November 5, 2026

[Engine versions, sharing audit and cleanup suggestions](ENGINE-REFRESH-AND-WEIGHT-SHARING-20261105.md). Eight updated text entries passed one short actual DSH read/result/exact followup and owned unload. TensorFold is a carried-forward November4 observation; its engine is unchanged. Loading and follow-up are excluded. No full-context or sustained test.

| API/DSH entry | Prefill tok/s | TTFT s | Decode tok/s | Context | Date |
| --- | ---: | ---: | ---: | ---: | --- |
| qwen27b-hyperqwen | 2077.77 | 2.818 | 62.186 | 86,016 | 2026-11-05 |
| qwen27b-sglang | 2219.46 | 2.785 | 60.135 | 57,344 | 2026-11-05 |
| glm-maya | 543.70 | 10.218 | 15.200 | 65,536 | 2026-11-05 |
| deepseek-maya | 186.70 | 31.944 | 7.900 | 32,768 | 2026-11-05 |
| bolt-vllm | 500.31 | 12.899 | 67.789 | 163,840 | 2026-11-05 |
| flash-next-iq1s-llamacpp | 120.73 | 48.463 | 36.861 | 12,288 | 2026-11-05 |
| flash-next-strata | 943.80 | 6.395 | 58.800 | 131,072 | 2026-11-05 |
| deepseek-unsloth-strata | 85.70 | 66.695 | 11.900 | 32,768 | 2026-11-05 |
| qwen27b-tensorfold | 575.26 | 10.135 | 186.951 | 12,288 | 2026-11-04 |

All November5 first calls reported zero native cached tokens; OS file caches were not dropped. DeepSeek/Strata’s old5.840sTTFT reused5539prompt tokens and cannot be compared directly with the new uncached66.695s. TensorFold decode is a short speculative DFlash2/copies burst. Different quantizations, contexts, prompt lengths and speculation prevent equal-quality ranking or a causal performance-regression conclusion from these single observations.

## Effective resource guards

All profiles retain2GiB host available, **100C** temperature stops, three bad2-second resource samples, fail-closed telemetry, swappiness60, parallel1 and idle600s. Swap occupancy is unlimited; active write/combined-I/O limits below are MiB/s over30seconds. Active full-PSI uses three bad samples. Short calls may not fill the averaging window. These are configured limits, not measured peak usage. Historical observations retain their original temperature policies.

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



## Diffusion entries

Both ComfyUI images remain unchanged: QwenTurbo1K7.133/4.086s,2K29.360/26.339s; FLUXKlein1K7.130/5.091s,2K27.341/24.279s. Native4K did not qualify. [Image protocol and guards](COMFY-2K4K-20261104.md).

Both video entries retain512x288/720p/1080p options. End-to-end HD entry checks: Wan720p67.746s/1080p170.847s; LTX720p50.598s/1080p74.839s. Render-only repetitions,33-frame scope and GPU-only guards remain in the [HD entry report](COMFY-VIDEO-HD-ENTRIES-20261105.md) and [render benchmark report](COMFY-VIDEO-720P1080P-20261105.md). These November5 results were not repeated during the text-engine refresh.

[Machine-readable current text observations](validation-results/20261105-engine-refresh.json). [November4 historical index](ALL-ENTRY-BENCHMARKS-20261104.md).
