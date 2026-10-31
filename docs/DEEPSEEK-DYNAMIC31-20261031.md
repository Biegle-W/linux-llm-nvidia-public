# Unsloth Dynamic3.1 DeepSeek trial — October 31, 2026

All five shard sizes and SHA-256 hashes passed. The model loaded at 2K and answered arithmetic correctly, then the unchanged inference swap guard stopped the JSON request. The new quant remains unselected.

## Pinned model and storage

The candidate is `unsloth/DeepSeek-V4.1-Flash-1017-GGUF`, revision `8a6ec9cf118e785a362ea94ee123c61c70553be6`, **UD-IQ1_S**, exactly five GGUF shards totaling **232,979,608,420 bytes**. The four core shards total **122,384,317,828 bytes** on NVMe; the **110,595,290,592-byte** Engram shard is on SATA and linked into the unified shard directory only after verification. A **40 GiB free-space reserve per drive** is preserved. Existing Maya/Strata weights and settings remain available.

Downloaded metadata identifies `deepseek41`, 40 layers, 5,120 embedding width, 384 experts and 6 used per token. Core tensor headers account for **115,228,016,640 expert-weight bytes** and **7,150,453,184 other-weight bytes**. Header inspection does not establish runtime fit or speed.

## Download failure and bounded recovery

The initial regular-HTTP job verified the first four shard sizes and SHA-256 hashes. The installed client rejected the final file because it exceeds its 50 GB HTTP-method limit. The dependent trial correctly stopped before launching a GPU worker.

Recovery uses the already-installed **hf_xet 1.7.0** for only that final shard, fixed download concurrency two, shared/per-file download-buffer settings `64mb`/`32mb` and a `384mb` download-buffer limit. The process retains 768/1,536 MiB soft/hard memory bounds, 256 MiB swap cap, low CPU/I/O priority and disk-reserve monitoring. No environment package was installed or upgraded, and verified core weights were reused. [Official Xet buffer/concurrency controls](https://huggingface.co/docs/hub/xet/using-xet-storage).

## Guarded trial and result

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
