# Unsloth Dynamic3.1 DeepSeek trial — October 31, 2026

The bounded trial finished; see the recorded result below. The new quant is not selected for maintained use.

## Pinned model and storage

The candidate is `unsloth/DeepSeek-V4.1-Flash-1017-GGUF`, revision `8a6ec9cf118e785a362ea94ee123c61c70553be6`, **UD-IQ1_S**, exactly five GGUF shards totaling **232,979,608,420 bytes**. The four core shards total **122,384,317,828 bytes** on NVMe; the **110,595,290,592-byte** Engram shard is on SATA and linked into the unified shard directory only after verification. A **40 GiB free-space reserve per drive** is preserved. Existing Maya/Strata weights and settings remain available.

Downloaded metadata identifies `deepseek41`, 40 layers, 5,120 embedding width, 384 experts and 6 used per token. Core tensor headers account for **115,228,016,640 expert-weight bytes** and **7,150,453,184 other-weight bytes**. Header inspection does not establish runtime fit or speed.

## Download failure and bounded recovery

The initial regular-HTTP job verified the first four shard sizes and SHA-256 hashes. The installed client rejected the final file because it exceeds its 50 GB HTTP-method limit. The dependent trial correctly stopped before launching a GPU worker.

Recovery uses the already-installed **hf_xet 1.7.0** for only that final shard, fixed download concurrency two, shared/per-file download-buffer settings `64mb`/`32mb` and a `384mb` download-buffer limit. The process retains 768/1,536 MiB soft/hard memory bounds, 256 MiB swap cap, low CPU/I/O priority and disk-reserve monitoring. No environment package was installed or upgraded, and verified core weights were reused. [Official Xet buffer/concurrency controls](https://huggingface.co/docs/hub/xet/using-xet-storage).

## Guarded trial and result

Recorded phase: **failed**. Guard stop: Sustained owned-worker swap churn during inference. Readiness took 248.46 seconds. No completed basic-quality pass was achieved; this does not prove every possible configuration cannot run.

The prepared initial attempt uses the existing llama.cpp build `caa8191df159f764fb0160e3d2fc6be008948aee`, binary SHA-256 `eed3e9ba6633c1d3ef2f835a0ebb265c6453680e08daca0f1cdd2c6d37c1b86f`. Binary revision, required flags and linked-library availability passed inspection while the router was idle. Initial context is **2,048**, concurrency one and prefill/microbatch 128. Routed experts use CPU mmap, Engram reads are lazy with the per-layer token embedding forced to CPU, and only the 3080 Ti/3080 main pair is visible to the engine. The 3060 remains auxiliary.

The separate owned worker has **46/48 GiB soft/hard memory bounds**, **2 GiB host reserve**, **512 MiB per-GPU reserve**, **82 C thermal ceiling**, **15% loading / 10% inference full-memory pressure bounds** and **1 MiB/s swap writes / 8 MiB/s combined swap I/O over 30 seconds**. Missing telemetry stops the owned attempt. Existing reservations and router work prevent launch; cleanup checks the owned invocation. A foreground harness and minimized backend monitor retain private logs and receipts.

If loading succeeds, the initial screen checks exact integer arithmetic and JSON, then one complete 64-token stream. Even a pass is a basic trial, not near-window, repeated-reload, multi-hour or production qualification. Existing maintained selections are preserved. Bolt’s separate two-load normal-router verification remains [documented here](BOLT-MAYA-RELIABILITY-20261031.md).

[Numeric evidence](validation-results/20261031-deepseek-dynamic31.json). Private jobs, raw logs, credentials and session records are excluded.

## Sources

- [Unsloth DeepSeek guidance](https://unsloth.ai/docs/models/deepseek-v4.1-flash).
- [Pinned GGUF repository](https://huggingface.co/unsloth/DeepSeek-V4.1-Flash-1017-GGUF/tree/8a6ec9cf118e785a362ea94ee123c61c70553be6).
- [Pinned native architecture implementation](https://github.com/ggml-org/llama.cpp/blob/caa8191df159f764fb0160e3d2fc6be008948aee/src/models/deepseek41.cpp).
