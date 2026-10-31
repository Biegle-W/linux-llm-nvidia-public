# Unsloth Dynamic3.1 DeepSeek — bounded SSD qualification, October 31, 2026

A working **2K isolated candidate is qualified on Strata 0.2.9 / engine 0.1.55**: exact arithmetic and JSON passed, followed by **two complete 256-token streams** with no guard stop. All five pinned model hashes passed. The existing maintained catalog and client defaults are preserved.

## Qualified SSD settings

| Setting | Tested value |
| --- | --- |
| Swap writes / combined swap I/O | **128 / 160 MiB/s**, rolling **30 seconds** |
| Loading / inference full-memory pressure | **15% / 15%**, sustained-sample guard retained |
| Worker memory | **46 / 48 GiB** soft/hard |
| Host / GPU reserve | **2 GiB / 512 MiB**; engine requests **768 MiB** internally |
| Temperature ceiling | **82 C**, all three GPUs monitored |
| Context / requests | **2,048 tokens / one request** |
| Quality and placement | All **6 experts**, drafting disabled; 3080 Ti/3080 main pair, 3060 auxiliary |
| CPU expert-store budget | **36 decimal GB**; read-only official hot-expert profile |

The swap ceilings are the existing maintained SSD-streaming policy, applied only to this isolated candidate. Independent memory, pressure, reserve, thermal, telemetry and ownership guards remain active. No maintained profile's limits were edited. Missing optional block-I/O accounting does not suppress mandatory swap/pressure or GPU telemetry checks.

## Actual Strata results

The signed engine loaded in **96.71 s**, using a metadata-only **8,727,668-byte pack** referencing the existing GGUF shards. No weight copy or model redownload was needed. Model-scoped, read-only clean-cache advice preceded loading; no global cache purge was used. The engine retained all six experts and automatically used layer splitting across both main GPUs when its requested tensor split could not divide the 2,304-wide expert dimension into two whole 256-value blocks.

| Check | Result |
| --- | --- |
| Arithmetic | Exact `323` for `17 × 19`; **19.86 s** |
| JSON | Exact object with numeric answer 42 and status ok; **6.80 s** |
| Stream 1 | **256 tokens**, **5.769 decode tok/s**, **4.696 s TTFT**, **44.20 s** generation |
| Stream 2 | **256 tokens**, **7.745 decode tok/s**, **0.205 s TTFT**, **32.93 s** generation |

Both streams returned the final SSE completion marker and exact output-token count. Each had 22 input tokens; the first reported zero cached prompt tokens, the second **21 cached tokens**. Decode is `(output tokens - 1) / first-to-last-content interval`. These are separate single observations after correctness requests, without a dedicated speed-fixture warmup or three-request median. The cache-advised start does not make later requests cold. These are not a matched causal speed comparison with Maya, the native alternative or other hardware.

Across **101 resource samples**, including **39 overlapping rolling-window samples**, peak worker memory was **41.975 GiB**, worker swap **zero**, loading and inference full-memory pressure **zero**, and measured swap rates **zero**. Minimum sampled GPU free memory was **745 MiB**, maximum temperature **51 C**. Hard-limit, OOM and OOM-kill events were zero. Both streams exceeded 30 seconds of generation, so this exercises the guard window rather than merely finishing before it.

## Measured path to a working candidate

Earlier attempts remain evidence; they were not reclassified as successes.

| Candidate | Outcome |
| --- | --- |
| Original native runtime, 1/8 swap, 10% pressure | Loaded and passed arithmetic; 1.562 MiB/s writes stopped JSON |
| Native, 8/16 swap, 10% pressure | Writes 1.810 and combined 2.242 MiB/s were allowed; pressure peaked at 14.45% and stopped JSON |
| Native, 8/16 swap, 15% pressure | Eager mapping population hit the unchanged 15% loading guard before readiness |
| Demand-loaded native, 8/16, 15% pressure | Arithmetic and JSON passed; partial stream stopped on pressure, peak 18.5%, with zero swap and no soft-limit reclaim |
| Demand-loaded native, 8/16, 25% pressure | Warm 64-token screen passed at 3.921 tok/s; too short to exercise a full guard window |
| Same candidate with clean-cache advice | Arithmetic and JSON passed; 11.820 MiB/s warming writes exceeded the 8 MiB/s cap during streaming |
| Demand-loaded native, 128/160, 25% pressure | Cache-advised arithmetic/JSON and all 256 streamed tokens passed |
| Official Strata 0.1.55, 128/160, 15% pressure | Arithmetic/JSON and both 256-token streams passed; preferred isolated candidate |

The native alternative changes one loader call from eager mmap prefetch/population to demand loading. Tensor bytes, expert count, kernels and original installed binaries were preserved; only an independent `libllama` copy was relinked. The portable [source patch](../patches/llama-demand-mmap-prefault.patch) applies to base commit `caa8191df159f764fb0160e3d2fc6be008948aee`; its SHA-256 is `16f3112d51ca9d0b1abad4f70fa9662051753f8a2e3b76f4c81228206e702b23`. This alternative is separate from the official Strata engine.

With the maintained 128/160 swap policy and a model-only 25% inference-pressure ceiling, the native cache-advised run loaded in **16.48 s**, passed JSON and completed **256 tokens at 1.793 tok/s**, **13.951 s TTFT**, over **142.22 s** generation. It recorded **85 rolling-window samples**, peak writes **13.119 MiB/s**, combined **13.158 MiB/s**, inference pressure **12.70%**, swap occupancy **0.573 GiB**, and **373,033 major faults**. The latter supports actual backing-file reads during the cache-advised test. No guard stop or OOM occurred. Strata passed under the lower 15% pressure ceiling.

## Release integrity, terminal behavior and scope

The [official 0.2.9 release](https://github.com/Niko1221/Strata/releases/tag/v0.2.9) adds UD-IQ1_S/UD-IQ1_M support and names engine 0.1.55. The CUDA package was staged independently: **444,779,692 bytes**, SHA-256 `8eed51bf333bc3bc381bc3cc4daa7dbca51d612647732e6f2a63c63be4c66124`. Every file hash and its Ed25519 signature passed against the previous installation's trusted key. Source/API adapter commit is `c62d5e3a15b40ea51c96aae9e8d36928965f53ab`. The existing app, selected engines and model files were preserved. No release performance claim on other hardware is treated as a local result.

Automated tests and runtime inspections now use minimized native terminals and skip activation. Actual authentication/input can request `run --attention`; user selectors retain `launch` behavior. Completed commands still close automatically. Seven focused launcher checks, a real iconic/no-focus/auto-close check, all **307 repository CPU tests**, and **19 bounded-policy checks** passed. See [terminal behavior](TERMINAL-ATTENTION-20261031.md).

Owned workers and reservations were released after testing; router/DSH invocations and maintained catalog bytes were preserved. This qualifies the recorded isolated 2K arithmetic/JSON/streaming screen. Near-window retrieval, larger contexts, repeated normal-router reloads and multi-hour operation remain outside this screen; no new maintained-router selection is claimed. [Complete numeric evidence](validation-results/20261031-deepseek-dynamic31.json).

## Earlier pinned download and strict-policy evidence

## Pinned model and storage

The candidate is `unsloth/DeepSeek-V4.1-Flash-1017-GGUF`, revision `8a6ec9cf118e785a362ea94ee123c61c70553be6`, **UD-IQ1_S**, exactly five GGUF shards totaling **232,979,608,420 bytes**. The four core shards total **122,384,317,828 bytes** on NVMe; the **110,595,290,592-byte** Engram shard is on SATA and linked into the unified shard directory only after verification. A **40 GiB free-space reserve per drive** is preserved. Existing Maya/Strata weights and settings remain available.

Downloaded metadata identifies `deepseek41`, 40 layers, 5,120 embedding width, 384 experts and 6 used per token. Core tensor headers account for **115,228,016,640 expert-weight bytes** and **7,150,453,184 other-weight bytes**. Header inspection does not establish runtime fit or speed.

## Download failure and bounded recovery

The initial regular-HTTP job verified the first four shard sizes and SHA-256 hashes. The installed client rejected the final file because it exceeds its 50 GB HTTP-method limit. The dependent trial correctly stopped before launching a GPU worker.

Recovery uses the already-installed **hf_xet 1.7.0** for only that final shard, fixed download concurrency two, shared/per-file download-buffer settings `64mb`/`32mb` and a `384mb` download-buffer limit. The process retains 768/1,536 MiB soft/hard memory bounds, 256 MiB swap cap, low CPU/I/O priority and disk-reserve monitoring. No environment package was installed or upgraded, and verified core weights were reused. [Official Xet buffer/concurrency controls](https://huggingface.co/docs/hub/xet/using-xet-storage).

## Earlier native trial with the strict 1/8 swap policy

Recorded phase: **failed**. Guard stop: Sustained owned-worker swap churn during inference. Readiness took 248.46 seconds. No completed basic-quality pass was achieved; this does not prove every possible configuration cannot run.

The completed initial attempt used the existing llama.cpp build `caa8191df159f764fb0160e3d2fc6be008948aee`, binary SHA-256 `eed3e9ba6633c1d3ef2f835a0ebb265c6453680e08daca0f1cdd2c6d37c1b86f`. Binary revision, required flags and linked-library availability passed inspection while the router was idle. Initial context is **2,048**, concurrency one and prefill/microbatch 128. Routed experts use CPU mmap, Engram reads are lazy with the per-layer token embedding forced to CPU, and only the 3080 Ti/3080 main pair is visible to the engine. The 3060 remains auxiliary.

The separate owned worker has **46/48 GiB soft/hard memory bounds**, **2 GiB host reserve**, **512 MiB per-GPU reserve**, **82 C thermal ceiling**, **15% loading / 10% inference full-memory pressure bounds** and **1 MiB/s swap writes / 8 MiB/s combined swap I/O over 30 seconds**. Missing telemetry stops the owned attempt. Existing reservations and router work prevent launch; cleanup checks the owned invocation. A foreground harness and minimized backend monitor retain private logs and receipts.

### Actual check sequence

| Check | Result |
| --- | --- |
| Pinned download | All five size and SHA-256 checks passed; 232,979,608,420 bytes retained |
| Readiness | **248.46 s**; server reported one 2,048-token slot |
| Arithmetic | **Passed**: exact `323` for `17 × 19`, 16.59 s wall time, 17 input / 2 output tokens |
| JSON | Interrupted by the resource guard; no JSON correctness result |
| 64-token stream | Not attempted; no sustained decode benchmark |
| Selection | Unchanged; new UD-IQ1_S quant remains experimental |

The first complete 30.70-second inference window measured **1.562 MiB/s swap writes**, above the **1 MiB/s** limit. Combined swap reads+writes were **2.221 MiB/s**, below the separate 8 MiB/s limit. The latched reason was swap churn. Inference full-memory pressure also peaked at **16.39%**; this was not recorded as the latched stop reason.

Across **137 samples**, worker memory peaked at **46.001 GiB**, swap occupancy at **201.1 MiB**, temperature at **37 C**, and sampled GPU free memory stayed at or above **5811 MiB**. Loading full-memory pressure briefly peaked at **20.02%** without latching the sustained loading guard. Hard-memory-limit, OOM and OOM-kill event counts were **zero**. Loading swap occupancy and transient pressure are distinct from the measured inference-rate violation.

The owned native worker received the guarded stop, then required the configured 15-second stop timeout and SIGKILL to finish. Subsequent checks found the worker inactive, its reservation released and all completed helper consoles closed. Router and DSH invocations stayed unchanged. No guard was relaxed, no fallback model was loaded and all maintained profile configuration bytes were preserved.

This result is scoped to this 2K configuration and its recorded guards. The two-token arithmetic response is a correctness check, not a representative decode benchmark. JSON, near-window retrieval, sustained streaming and repeated reload qualification remain unpassed for this candidate. Bolt’s separate normal-router verification remains [documented here](BOLT-MAYA-RELIABILITY-20261031.md).

[Numeric evidence](validation-results/20261031-deepseek-dynamic31.json). Private jobs, raw logs, credentials and session records are excluded.

## Sources

- [Unsloth DeepSeek guidance](https://unsloth.ai/docs/models/deepseek-v4.1-flash).
- [Pinned GGUF repository](https://huggingface.co/unsloth/DeepSeek-V4.1-Flash-1017-GGUF/tree/8a6ec9cf118e785a362ea94ee123c61c70553be6).
- [Pinned native architecture implementation](https://github.com/ggml-org/llama.cpp/blob/caa8191df159f764fb0160e3d2fc6be008948aee/src/models/deepseek41.cpp).
