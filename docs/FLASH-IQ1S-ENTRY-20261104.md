# Flash-Next IQ1_S entry — November 4, 2026

`flash-next-iq1s-llamacpp` is now a separate enabled model in the authenticated API and DSH NVIDIA server provider. The display name identifies Unsloth v3.1 IQ1_S, llama.cpp, the SSD n-gram table and 12K allocation. Select it through DSH/API, or run `./scripts/start_model.sh flash-iq1s`. HyperQwen, SGLang and TensorFold remain enabled; all five older RAM/offload entries remain disabled. Existing default selections are preserved.

## Qualified configuration

The entry reuses the already publisher-SHA256-verified Unsloth revision `d96201194f103c906994f283f504209dc8d2a10c`: three shards totaling 66.379 GB, including the 28.800 GB IQ4_NL n-gram table on NVMe. No checkpoint was copied or requantized. The clean llama.cpp build11909 / `caa8191df159f764fb0160e3d2fc6be008948aee` binary and ten native libraries are pinned in `config/flash-iq1s-runtime.json`.

The maintained launcher retains explicit mmap/lazy-mode on, 12,288 context, one sequence, 256/128 batch/microbatch, eight CPU threads, reasoning off, no MTP, 1536 MiB fit targets, private loopback/authentication and disabled Web UI. Computation uses both GPUs and CPU-mapped weights. Native lazy-table logs, an actual table-shard process mapping and native 12K allocation evidence are checked by the supervisor. This does not imply that all weights fit in VRAM or that a full12K prompt was stress-tested.

The normal router owns `llm-router-worker.service`, its26/28 GiB cgroup and the 600-second idle unload. It verifies exact executable/invocation ownership and preserves the GPU reservation protocol. The new entry has an independent pinned updater exemption; daily updates remain paused. The backend viewer includes its real engine log when a non-headless launch requires a visible monitor. DSH was reloaded to display the new entry; the API remained independent.

## Normal API/DSH verification

| Model / quant | Engine | Prefill tok/s | TTFT s | Decode tok/s | Context tokens | Storage GB | Storage location |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Flash-Next Unsloth v3.1 IQ1_S + IQ4_NL table | llama.cpp11909 | 88.79 | 66.292 | 31.10 | 12,288 | 66.379 | NVMe SSD |

One actual DSH read, matching executed tool result and exact follow-up passed, followed by normal owned unload and GPU release. The first request had 5824 input tokens,39 output tokens and no cached prompt tokens. Native prompt/decode times were65.595/1.222 s; TTFT is client first delivered tool/content and includes parser buffering. The short harness caps output at128; loading and follow-up generation are excluded from the performance table. No best-score selection, full-context, sustained or cold-SSD test was run. The earlier isolated runs are retained separately in [all entry results](ALL-ENTRY-BENCHMARKS-20261104.md).

| Profile | RAM high/max; host reserve | VRAM guards | Swap and pressure guards |
| --- | --- | --- | --- |
| Flash-Next IQ1_S | 26/28 GiB; 2 GiB host available | Both GPUs; 1536 MiB fit targets; independent 256 MiB free/card floor after readiness | Unlimited swap occupancy; active writes 128 / reads+writes 160 MiB/s over 30 s; full PSI>15% for three samples after a complete window |

RAM, GPU headroom and >=82 C stop after three bad2-second samples; missing owned telemetry fails closed after three. The current-boot root-owned host-staged proof remains required; no NCCL channel proof is fabricated for this native ggml engine. Active swap windows reset outside inference; there is no separate loading-PSI stop. Swappiness60, parallel1 and idle600 remain. Native request processing/deferred gauges are validated independently of vLLM/Strata gauges. Busy or unknown native request state prevents owned unload or a model switch. Other engines retain their own metric/status parsers.

Lifecycle sampled 61 rows at a median2.074 s. Charged RAM peaked 25.99 GiB, swap403.58 MiB, minimum free GPU memory1593/1512 MiB, temperatures56/38 C and host available27.09 GiB. Soft `memory.high` events numbered 2951, with no hard-max/OOM/OOM-kill event. Nineteen complete active windows had write/combined maxima4.95/5.27 MiB/s and full PSI<=4.51%; no guard violation occurred. Shared file-cache charging and sampling intervals limit these usage comparisons. All raw prompts/transcripts remain private; the [numeric record](benchmark-results/20261104-flash-iq1s-entry.json) contains only reviewed timing, guard and resource evidence.

All 441 CPU regressions passed, including new native-gauge, bounded-policy and busy/unknown-unload protection checks. The normal DSH integration check passed without a repeated speed attempt. Final state: four enabled API/DSH entries, test workers unloaded, GPUs returned to baseline, API/hub/DSH active and no GPU reservation. Complete historical results and rejected trials remain in the [benchmark ledger](BENCHMARK-HISTORY.md).
