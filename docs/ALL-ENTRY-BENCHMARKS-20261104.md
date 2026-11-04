# All entry benchmark references — November 4, 2026

Four entries are currently enabled on the temporary32 GB Z690/13900KS host, using direct CPU PCIe4 x8/x8 without CUDA P2P. Flash-Next IQ1_S is now `flash-next-iq1s-llamacpp`, with its n-gram table lazily mapped on NVMe. Five older entries remain disabled; their numbers below are explicitly historical64 GB/switched-host references. Defaults and their disabled state are preserved.

These are short actual DSH read-tool observations, excluding loading and follow-up timing. Current entries passed matching executed tool results, exact follow-ups and owned unload. Context columns are allocated limits, not full-window stress qualification. Different precision, cached prompts, speculation and hardware prevent an equal-quality ranking. Decimal GB are used for weights; HyperQwen and SGLang share one checkpoint. The TensorFold size includes its separate drafter.

## Latest current enabled results

| Model / quant | Engine | Prefill tok/s | TTFT s | Decode tok/s | Context tokens | Storage GB | Storage location |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Qwen3.8-27B / AutoRound-INT4-fast-heads-INT8-embedding | HyperQwen-vLLM | 2065.24 | 3.073 | 62.59 | 86,016 | 15.792 | SATA SSD |
| Qwen3.8-27B / AutoRound-INT4-fast-heads-INT8-embedding | SGLang | 2232.88 | 2.767 | 60.23 | 57,344 | 15.792 | SATA SSD |
| Qwen3.8-27B / EXL3-2.0bpw | TensorFold | 580.96 | 10.029 | 180.34 | 12,288 | 13.522 | SATA SSD |
| Qwen3.8-Flash-Next / Unsloth-Dynamic-v3.1-UD-IQ1_S | llama.cpp11909 | 88.79 | 66.292 | 31.10 | 12,288 | 66.379 | NVMe SSD |

TensorFold decode is a short DFlash2-4bit/copies burst, not sustained prose. It runs on GPU0 with host-mapped embeddings. Flash-Next uses both GPUs and CPU-mapped weights; its table is SSD-backed but OS caches were not dropped, so cold-SSD performance is not established. See [the new entry qualification](FLASH-IQ1S-ENTRY-20261104.md) and [the 26/28rerun](RAM26-28-RERUN-20261104.md).

## Current effective guards

| Profile | Worker RAM high/max; host reserve | VRAM policy | Swap / pressure policy |
| --- | --- | --- | --- |
| HyperQwen | 26/28 GiB; 2 GiB host available | 256 MiB free/card after ready | Unlimited occupancy; active writes 1 / reads+writes 8 MiB/s over 30 s; full PSI>10% for 3 samples |
| SGLang | 26/28 GiB; 2 GiB host available | 256 MiB free/card after ready | Unlimited occupancy; active writes 1 / reads+writes 8 MiB/s over 30 s; full PSI>10% for 3 samples |
| TensorFold | 26/28 GiB; 2 GiB host available | GPU0; native 1 GiB reserve; 256 MiB free/card after ready | Unlimited occupancy; active writes 1 / reads+writes 8 MiB/s over 30 s; full PSI>10% for 3 samples |
| Flash-Next IQ1_S | 26/28 GiB; 2 GiB host available | Both GPUs; 1536 MiB fit targets; 256 MiB independent stop floor/card | Unlimited occupancy; active writes 128 / reads+writes 160 MiB/s over 30 s; full PSI>15% for 3 samples |

Resource/temperature checks use three bad2-second samples and 82 C; missing telemetry fails closed after three. PSI applies after a complete30-second active window; rate violations stop once that window exists. Outside inference the window resets. These entries have no separate loading-PSI stop. Current-boot host-staged proof remains mandatory. Swappiness60, parallel1 and idle600 remain. Actual cgroup limits were verified in each current check; no guard violation occurred. Sampled usage and loading-transient exceptions remain in the linked numeric records.

## Disabled entries: dated historical references

These measurements were not rerun or enabled on the 32 GB host. November3 rows use retained baseline/selected normal validation, rather than rejected tuning arms. The Flash-Next IQ3 historical context is131K, even though its preserved current disabled definition is32K. DeepSeek/Strata reused5539 of 5710 prompt tokens; its prefill figure covers the uncached remainder and is not a cold full-prompt comparison. Historical tool/follow-up protocols differed; do not infer current follow-up qualification from them.

| Model / quant | Engine / measurement date | Prefill tok/s | TTFT s | Decode tok/s | Tested allocation tokens | Storage GB | Storage location |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| NVIDIA-Nemotron-3.5-Bolt-74B-A9B / AWQ-INT4 | vLLM-offload (2026-11-03) | 240.66 | 26.452 | 0.39 | 163,840 | 55.333 | SATA SSD |
| Qwen3.8-Flash-Next / IQ3_XXS | Strata (2026-11-01) | 506.20 | 11.679 | 60.20 | 131,072 | 75.840 | NVMe SSD |
| GLM-5.3-Flash / Maya-S24 | Maya (2026-11-03) | 342.40 | 16.310 | 7.10 | 65,536 | 94.702 | NVMe SSD |
| DeepSeek-V4.1-Flash-1017 / UD-IQ1_S (Unsloth Dynamic3.1) | Maya (2026-11-03) | 198.80 | 28.660 | 4.80 | 32,768 | 232.980 | NVMe + SATA SSDs |
| DeepSeek-V4.1-Flash-1017 / UD-IQ1_S (Unsloth Dynamic3.1) | Strata (2026-11-01) | 7.60 | 22.631 | 3.70 | 32,768 | 232.980 | NVMe + SATA SSDs |

Historical guards below apply to those measurements, not their current disabled26/28 GiB definitions. The64 GB worker policy was56/58 GiB with 2 GiB host reserve. November1 artifacts lack per-run kernel snapshots; those rows describe the dated policy, not newly measured limits. November3 guard records are embedded in the linked numeric source.

| Historical profile | RAM high/max; host reserve | VRAM policy at that date | Swap writes/combined; pressure |
| --- | --- | --- | --- |
| Flash-Next IQ3 / Nov1 | 56/58 GiB; 2 GiB | Native1024 MiB cache reserve; separate explicit free floor not captured | Unlimited; 128/160 MiB/s over 30 s; 15% full PSI,3 samples |
| GLM/Maya / Nov3 | 56/58 GiB; 2 GiB | Native1024 MiB cache reserve; no separate explicit free floor in source | Unlimited; 128/160 MiB/s over 30 s; 10% full PSI,3 samples |
| DeepSeek/Maya / Nov3 | 56/58 GiB; 2 GiB | Native1024 MiB cache reserve; no separate explicit free floor in source | Unlimited; 128/160 MiB/s over 30 s; 15% full PSI,3 samples |
| Bolt / Nov3 | 56/58 GiB; 2 GiB | Explicit256 MiB free/card; loading PSI15% | Unlimited; 1/8 MiB/s over 30 s; 10% full PSI,3 samples |
| DeepSeek/Strata / Nov1 | 56/58 GiB; 2 GiB | Historical512 MiB free/card and native 1024 MiB cache reserve; per-run snapshot unavailable | Unlimited; 128/160 MiB/s over 30 s; 15% full PSI,3 samples |

Historical resource stops used three bad samples and 82 C; active swap windows/reset semantics remain dated policy. See [64 GB RAM policy](WORKER-RAM-64GB-20261031.md), [short-tool observations](SHORT-TOOL-BENCHMARKS-20261101.md) and [November3optimization evidence](VRAM256-OPTIMIZATION-20261103.md). Later256 MiB/current32 GB settings must not be retroactively applied to older measurements.

## All recent successful runs retained

This table keeps both earlier24/26 GiB and newer26/28 GiB observations. It is not a repeated best-score selection. Profile-specific context, storage, engine and guards are defined in the corresponding tables above and linked sources; the two earlier entry/candidate runs use 24/26 GiB rather than the current26/28.

| Model / quant / arm | Engine | Prefill tok/s | TTFT s | Decode tok/s | Context tokens | Storage GB | Storage location |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Qwen3.8-27B / AutoRound-INT4-fast-heads-INT8-embedding / 24/26GiB enabled-model check | HyperQwen-vLLM | 2077.92 | 2.821 | 62.53 | 86,016 | 15.792 | SATA SSD |
| Qwen3.8-27B / AutoRound-INT4-fast-heads-INT8-embedding / 24/26GiB enabled-model check | SGLang | 2137.89 | 3.044 | 60.20 | 57,344 | 15.792 | SATA SSD |
| Qwen3.8-27B / EXL3-2.0bpw / 24/26GiB normal entry | TensorFold | 581.98 | 10.019 | 183.92 | 12,288 | 13.522 | SATA SSD |
| Qwen3.8-Flash-Next / Unsloth-Dynamic-v3.1-UD-IQ1_S / 24/26GiB isolated | llama.cpp11909 | 101.50 | 58.113 | 29.14 | 12,288 | 66.379 | NVMe SSD |
| Qwen3.8-27B / AutoRound-INT4-fast-heads-INT8-embedding / 26/28GiB rerun | HyperQwen-vLLM | 2065.24 | 3.073 | 62.59 | 86,016 | 15.792 | SATA SSD |
| Qwen3.8-27B / AutoRound-INT4-fast-heads-INT8-embedding / 26/28GiB rerun | SGLang | 2232.88 | 2.767 | 60.23 | 57,344 | 15.792 | SATA SSD |
| Qwen3.8-27B / EXL3-2.0bpw / 26/28GiB rerun | TensorFold | 580.96 | 10.029 | 180.34 | 12,288 | 13.522 | SATA SSD |
| Qwen3.8-Flash-Next / Unsloth-Dynamic-v3.1-UD-IQ1_S / 26/28GiB rerun | llama.cpp11909 | 93.35 | 63.238 | 28.23 | 12,288 | 66.379 | NVMe SSD |
| Qwen3.8-Flash-Next / Unsloth-Dynamic-v3.1-UD-IQ1_S / 26/28GiB normal entry qualification | llama.cpp11909 | 88.79 | 66.292 | 31.10 | 12,288 | 66.379 | NVMe SSD |

The two earlier isolated TensorFold settings also remain separate observations:

| Model / quant / arm | Engine | Prefill tok/s | TTFT s | Decode tok/s | Context tokens | Storage GB | Storage location |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Qwen27B EXL3 2bpw / plain | TensorFold 1.2.2 | 584.56 | 9.982 | 34.40 | 16,384 | 9.673 | SATA SSD |
| Qwen27B EXL3 2bpw / DFlash2-4bit + copies | TensorFold 1.2.2 | 576.63 | 10.108 | 180.38 | 12,288 | 13.522 | SATA SSD |

| Earlier profile | RAM high/max; host reserve | VRAM policy | Swap and pressure |
| --- | --- | --- | --- |
| HyperQwen / SGLang / TensorFold 24/26 references | 24/26 GiB; 2 GiB | 256 MiB free/card after ready; TensorFold native 1 GiB reserve | Unlimited; 1/8 MiB/s over 30 s; 10% full PSI,3 samples |
| Flash-Next IQ1_S24/26 reference | 24/26 GiB; 2 GiB | Both GPUs; 1536 MiB fit targets and 256 MiB free/card stop | Unlimited; 128/160 MiB/s over 30 s; 15% full PSI,3 samples |

Earlier plain/drafted TensorFold settings use that24/26 GiB policy, GPU0 only, native 1 GiB reserve,2-second resource checks,82 C and three bad samples; GPU1 remained reserved but unused. Their full token/cache/resource tables and rejected8K/16K admissions remain in [the original assessment](TENSORFOLD-AND-UNSLOTH-ASSESSMENT-20261104.md). No failed admission is presented as a qualified benchmark.

The [machine-readable index](benchmark-results/20261104-all-entry-benchmarks.json) retains source references, token/cache counts and timing methods. The complete older archive, tuning arms, failures and retired models remain linked from [the benchmark ledger](BENCHMARK-HISTORY.md); those hundreds of dated experiments are not replaced by this entry summary.
