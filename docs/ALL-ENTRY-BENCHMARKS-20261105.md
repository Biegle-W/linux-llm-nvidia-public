# Current entry observations — November 5, 2026

[Post-power-loss verification](POWERLOSS-RECOVERY-20261105.md): IQ1_M passed a fresh guarded short check on the new boot; selected settings are unchanged. The table below retains its original qualification observations.

Latest replacement: [Flash-Next IQ1_M /Strata](FLASH-IQ1M-STRATA-20261105.md) supersedes IQ1_S /llama.cpp after a passing guarded short actual DSH check. [Retired IQ1_S files were subsequently deleted](IQ1S-WEIGHT-REMOVAL-20261105.md); the active IQ1_M28.8GB table was preserved and hash-verified.

Latest Strata selection is0.2.11/engines0.1.57 following the explicit reviewed DeepSeek one-token exception. [Paired observations, acceptance and guards](STRATA-0211-QUALIFICATION-20261105.md); other entries below retain their dated observations.

[Engine versions, sharing audit and cleanup suggestions](ENGINE-REFRESH-AND-WEIGHT-SHARING-20261105.md). Eight updated text entries passed one short actual DSH read/result/exact followup and owned unload. TensorFold is a carried-forward November4 observation; its engine is unchanged. Loading and follow-up are excluded. No full-context or sustained test.

| API/DSH entry | Prefill tok/s | TTFT s | Decode tok/s | Context | Date |
| --- | ---: | ---: | ---: | ---: | --- |
| qwen27b-hyperqwen | 2077.77 | 2.818 | 62.186 | 86,016 | 2026-11-05 |
| qwen27b-sglang | 2219.46 | 2.785 | 60.135 | 57,344 | 2026-11-05 |
| glm-maya | 543.70 | 10.218 | 15.200 | 65,536 | 2026-11-05 |
| deepseek-maya | 186.70 | 31.944 | 7.900 | 32,768 | 2026-11-05 |
| bolt-vllm | 500.31 | 12.899 | 67.789 | 163,840 | 2026-11-05 |
| flash-next-iq1m-strata | 1092.50 | 5.267 | 78.200 | 131,072 | 2026-11-05 |
| flash-next-strata | 934.20 | 6.460 | 68.400 | 131,072 | 2026-11-05 |
| deepseek-unsloth-strata | 83.40 | 68.423 | 11.800 | 32,768 | 2026-11-05 |
| qwen27b-tensorfold | 575.26 | 10.135 | 186.951 | 12,288 | 2026-11-04 |

All November5 first calls reported zero native cached tokens; OS file caches were not dropped. DeepSeek/Strata’s old5.840sTTFT reused5539prompt tokens and cannot be compared directly with the earlier November5 uncached66.695s observation. TensorFold decode is a short speculative DFlash2/copies burst. Different quantizations, contexts, prompt lengths and speculation prevent equal-quality ranking or a causal performance-regression conclusion from these single observations.

## Effective resource guards

[November5 RAM-ceiling update](ALL-MODEL-RAM-CEILINGS-20261105.md): all13 entries now use87.77/89.77GiB. The performance observations above predate the dense/ComfyUI ceiling change; no inference was repeated for this configuration-only update. Historical reports preserve their original limits.

All profiles retain2GiB host available, **100C** temperature stops, three bad2-second resource samples, fail-closed telemetry, swappiness60, parallel1 and idle600s. Swap occupancy is unlimited; active write/combined-I/O limits below are MiB/s over30seconds. Active full-PSI uses three bad samples. Short calls may not fill the averaging window. These are configured limits, not measured peak usage. Historical observations retain their original temperature policies.

| Profile | Worker RAM high/max GiB | GPU policy | Active swap writes/combined | Active/loading PSI % |
| --- | ---: | --- | ---: | --- |
| qwen27b-hyperqwen | 87.77/89.77 | 256 MiB free/card after ready | 1/8 | 10 / none separately |
| qwen27b-sglang | 87.77/89.77 | 256 MiB free/card after ready | 1/8 | 10 / none separately |
| qwen27b-tensorfold | 87.77/89.77 | 256 MiB free/card after ready; GPU0; native1024 MiB reserve | 1/8 | 10 / none separately |
| flash-next-iq1m-strata | 87.77/89.77 | 256 MiB free/card; 1024 MiB native reserve/card | 128/160 | 15 / none separately |
| flash-next-strata | 87.77/89.77 | 1024 MiB native reserve | 128/160 | 15 / none separately |
| glm-maya | 87.77/89.77 | 1024 MiB native reserve | 128/160 | 10 / none separately |
| deepseek-maya | 87.77/89.77 | 1024 MiB native reserve | 128/160 | 15 / none separately |
| bolt-vllm | 87.77/89.77 | 256 MiB free/card after ready; 384 MiB fit targets | 1/8 | 10 / 15 |
| deepseek-unsloth-strata | 87.77/89.77 | 256 MiB free/card after ready; 1024 MiB native reserve | 128/160 | 15 / 15 |



## Diffusion entries

Both ComfyUI images remain unchanged: QwenTurbo1K7.133/4.086s,2K29.360/26.339s; FLUXKlein1K7.130/5.091s,2K27.341/24.279s. Native4K did not qualify. [Image protocol and guards](COMFY-2K4K-20261104.md).

Both video entries retain512x288/720p/1080p options. End-to-end HD entry checks: Wan720p67.746s/1080p170.847s; LTX720p50.598s/1080p74.839s. Render-only repetitions,33-frame scope and GPU-only guards remain in the [HD entry report](COMFY-VIDEO-HD-ENTRIES-20261105.md) and [render benchmark report](COMFY-VIDEO-720P1080P-20261105.md). These November5 results were not repeated during the text-engine refresh.

[Earlier engine-refresh observations](validation-results/20261105-engine-refresh.json); [selected IQ1_M observations](validation-results/20261105-flash-iq1m-strata.json); [latest IQ3_XXS/DeepSeek Strata pair](validation-results/20261105-strata0211-qualification.json). [November4 historical index](ALL-ENTRY-BENCHMARKS-20261104.md).
