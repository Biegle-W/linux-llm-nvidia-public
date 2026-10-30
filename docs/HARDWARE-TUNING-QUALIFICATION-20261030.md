# Hardware tuning qualification — October 30, 2026

Qwen Flash-Next is selected in **resident-expert mode on both GPUs at 32K**, after paired performance and full quality/resource qualification. GLM and DeepSeek/Maya retain their prior settings. Tests began October 29 and completed October 30 on the restored 64 GB system. The [research report](HARDWARE-TUNING-RESEARCH-20261029.md) explains the upstream sources and candidate choices; [numeric evidence](validation-results/20261030-hardware-tuning.json) records every short trial.

## Selected Qwen result

| Matched full-qualification screen | Plain mapped baseline | Resident candidate |
|---|---:|---:|
| Decode, median tok/s | 78.74 | 88.12 |
| Prefill, median tok/s | 435.1 | 628.8 |
| Time to first token, median seconds | 4.994 | 3.462 |
| Retrieval actual input tokens | 29,435 | 29,435 |
| Continuous generation, seconds | 120.28 | 122.91 |

The matched screen improves decode by **11.9%** and prefill by **44.5%**. Both arms used the same three fixtures, 128 output tokens per request, 32,768 context, hardware, model and quantization. Loading is excluded. JSON, arithmetic, image, uncached near-window retrieval, sustained generation and fresh-process reload passed for both arms. Actual retrieval usage was 29,435 tokens with zero cached prompt tokens. The resident stream produced 10,624 tokens; the baseline produced 9,472. Sustained caps were sized separately to reach at least 90 seconds, so their durations establish resource coverage rather than a fixed-token speed comparison.

An earlier interleaved confirmation used two fresh runs per mode, three measured requests each. The median of the two run medians was **90.86 resident versus 66.46 mapped tok/s (36.7% gain)**. The different gain sizes reflect workload/cache variability. The initial exploratory medians were 46.72 mapped, 77.39 with a 32 GiB resident budget, and 88.15 fully resident. Those initial figures are not the final paired performance estimate.

Selection replaces the plain `--mmap-experts` argument with `--resident-experts`. The engine still maps backing files; residency changes where the non-GPU cache complement lives. Normal startup confirmed approximately 36.65 GiB resident and pinned. Some additional-GPU experts retain mapped fallback backing, so this is not a guarantee of zero SSD access under every cache transition. The 32 GiB budget passed a short screen but was not selected or fully qualified.

The installed native launcher accepted the IQ3_XXS budget candidate despite the setup script's quant-specific selector restriction. This resolves the native-launch compatibility question for the tested configuration; it does not change setup's supported options.

Two normal guarded loads using the selected production configuration each passed JSON and confirmed a real resident, pinned complement rather than silent plain-mmap fallback. The second was a fresh reload. Model workers were then unloaded; router and DSH were preserved. Selection used durable preimages and rollback on failed normal verification.

## Preserved configuration and resource evidence

Hardware: i5-13600KF, 64 GB installed/61.3013 GiB usable, DDR5-4200, RTX 3080 Ti 12 GB plus RTX 3080 10 GB. Runtime versions, IQ3_XXS weights, 32K context, MTP, int8 KV, spec 4, nine Qwen CPU workers, auto layer split and both GPUs remain unchanged. The Qwen engine's observed native reserve remains 700 MiB; no reserve flag was reduced. RAM 44/48 GiB high/hard limits, 2 GiB host floor, 128 MiB/s swap writes/160 MiB/s combined over 30 seconds, 15% pressure policy, thermal and telemetry guards, swappiness 60, idle 600 and concurrency 1 remain unchanged. Other profiles retain their own selected guard policies.

Resource monitoring reported no hard-memory-limit, OOM or OOM-kill events for either full arm or the selected normal loads. Soft high-watermark throttling occurred and is retained as evidence. The resident full qualification's minimum available host RAM was 14.13 GiB; its peak worker swap occupancy was 2416.76 MiB (2.36 GiB). Eligible 30-second inference windows recorded zero swap writes and a peak combined swap rate of 33.75 MiB/s, below the unchanged 160 MiB/s limit. Swap occupancy is distinct from ongoing swap-write activity. Startup copies/pins about 36.7 GiB and can take longer than a mapped startup. Throughput figures describe inference after readiness, not cold launch time.

## GLM and DeepSeek findings

GLM retained S24, its 40 GiB RAM tier, 65,536 context and both GPUs. These native calibration dimensions were tested independently through the existing guarded service:

| GLM exploratory setting | Median decode tok/s |
|---|---:|
| Automatic baseline | 5.69 |
| PCIe share 0.0 | 5.47 |
| PCIe share 0.1 | 5.58 |
| PCIe share 0.25 | 5.93 |
| PCIe share 0.5 | 5.01 |
| PCIe share 0.75 | 5.55 |
| CPU lane 5 threads per stage | 6.04 |
| CPU lane 9 threads per stage | 5.52 |
| CPU lane 13 threads per stage | 5.25 |
| Disk read chunks 4 | 6.04 |
| Disk read chunks 2 | 5.78 |

Five threads and four read chunks initially tied near 6.04 tok/s. Five threads was carried into the preplanned interleaved confirmation. It then measured **5.85 versus 6.00 tok/s for default threads**, a 2.6% regression. It failed the greater-than 3% improvement threshold; no GLM change was promoted and no long qualification was needed for that rejected candidate. The four-chunk option was not independently confirmed. These tests exercise the native calibration controls; they do not claim an exhaustive search or a complete run of the upstream standalone calibration utility.

DeepSeek/Maya retained mapped experts, 8 GB warming, 32K context and its pinned runtime. Removing explicit 14 threads enabled native CPU-lane measurement, which selected 14 again (cores 1.08 ms versus P-cores 1.43 ms in that startup microbenchmark). Three-request speed medians were 3.32 fixed versus 3.44 auto, with substantial variation. Both failed the same JSON check: `sum` was returned as the expression string `17+25` rather than 42. That is a specific fixture failure, not a general conclusion about arithmetic capability. No DeepSeek setting was promoted. DeepSeek/Strata's 42 decimal GB LFU store and all dense profiles were unchanged and not benchmarked here.

## Harness repair and evidence handling

Full Qwen baseline qualification initially stopped before retrieval because Strata Terminal lacks Maya's `/api/tokens` endpoint. An initial local-counter repair then exposed Strata's native tokenizer-file format, which is incompatible with the generic Hugging Face tokenizer reader. The final counter recognizes native checkpoint format and uses the Python/tokenizer from the resolved installed Terminal bundle; generic checkpoints retain their existing counter and Maya retains its native endpoint. No tokenizer or runtime was downloaded. The actual response-usage near-window and prompt-cache gates remain mandatory.

All 27 targeted daily-update/qualification CPU regressions passed, including endpoint selection, native bundle resolution, actual usage coverage and counter failures. A real CPU-only integration reproduced the saved native 29,498-token reference. Completed baseline speed/JSON/arithmetic/image/resource evidence was retained with hashes; only the missing retrieval, sustained and reload checks resumed. Both harness failures remain archived and are not relabeled as model/guard failures. No guards were relaxed to repair the harness.

Twenty-four short trial arms completed before full qualification: 22 passed the speed/JSON screen and two DeepSeek arms failed JSON. There is no new six-profile matched benchmark. OS page cache was not flushed, expert-cache warmth was not perfectly controlled, and isolated experts/history files prevented trials from training the production history. Historical benchmarks, including the earlier 16.87 Qwen result, remain dated evidence and are not used as causal controls for this selection. NVIDIA async, pipeline, auxiliary-CPU placement and other flag combinations remain unqualified by this study.
