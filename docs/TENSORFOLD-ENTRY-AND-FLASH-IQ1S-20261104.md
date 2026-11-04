# TensorFold entry and Flash-Next IQ1_S — November 4, 2026

TensorFold is now a separate enabled entry, `qwen27b-tensorfold`, in the normal authenticated API and DSH NVIDIA server provider. It uses the same tested Mia EXL3 2.0bpw target, TensorFold 1.2.2, DFlash2 quantized to 4-bit at runtime and automatic context copies. The HyperQwen/SGLang entries and default selection are preserved. Existing larger RAM/offload profiles remain disabled; the host still has temporary 32 GB RAM.

Select it in DSH, through the router, or with `./scripts/start_model.sh qwen27b tensorfold`. Its display name explicitly identifies the quant, drafter/copies and 12K context. DSH was reloaded for the entry; the API/hub stayed active during that reload. After the short check the worker was unloaded, with no fallback preload.

## Normal-router verification

| Model / quant | Engine | Prefill tok/s | TTFT s | Decode tok/s | Context tokens | Storage GB | Storage location |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Qwen3.8-27B / EXL3 2.0bpw + DFlash2-4bit/copies | TensorFold 1.2.2 | 581.98 | 10.019 | 183.92 | 12,288 | 9.673 target + 3.849 drafter | SATA SSD |

One actual DSH read call, matching executed result and exact follow-up passed. Total tool/follow-up duration was 21.84 s; loading is excluded from the table. Token counts and native one-request timing deltas are retained in the [numeric evidence](benchmark-results/20261104-tensorfold-entry-and-flash-iq1s.json). Decode is the inverse native TPOT of a short speculative tool-argument burst, not sustained prose throughput. This is lower target precision and context than the maintained AutoRound profiles; it is not an equal-quality speed comparison. No full-context, sustained or quality-ranking test was run.

## Guards and placement

| Profile | Worker RAM high/max; host reserve | VRAM policy | Swap and pressure policy |
| --- | --- | --- | --- |
| TensorFold | 24/26 GiB; 2 GiB host available | GPU0 only; native 1 GiB reserve; 256 MiB free floor on both cards after readiness | Unlimited occupancy; active writes 1 MiB/s and reads+writes 8 MiB/s over 30 s; full PSI >10% for three samples after a complete window |

Resource checks run every two seconds, stopping after three low-RAM/VRAM or >=82 C samples; missing request/cgroup telemetry fails closed after three. Current-boot root-owned host-staged transport proof remains mandatory. Single-device TensorFold does not create NCCL channels, so native GPU0/context/reserve/DFlash2+copies admission evidence replaces the two-device channel requirement for this entry only. The pinned launcher exposes only GPU0. Other profiles retain their channel checks. Runtime/weights/metadata are hash-pinned; key and backend bind stay private and loopback-only. Swappiness60, parallel1 and idle600 remain.

Lifecycle sampling at a median5.08 s captured ten rows: charged worker RAM peaked3.01 GiB, swap0, host available>=24.38 GiB, GPU free minima1355/9928 MiB and temperatures<=55/27 C. All cgroup high/max/OOM events were zero. Charged file cache can belong to another cgroup after previous reads; this is not a total model working-set measurement or evidence of reduced RAM requirements. Native host-mapped embeddings remain in use. Sampled extrema are not guaranteed peaks. Short inference does not exercise a sustained30-second swap window. Owned worker unload and GPU release passed.

## Flash-Next IQ1_S trial preparation

The requested new Unsloth v3.1 revision is `d96201194f103c906994f283f504209dc8d2a10c`. Its three IQ1_S shards total66.379 GB, including the28.800 GB IQ4_NL n-gram table. Files are downloading resumably with publisher SHA256 verification to NVMe SSD. This is a new isolated candidate, not restoration of the disabled older IQ3 profile or full-RAM cache choices.

The installed llama.cpp build11909 / `caa8191df` supports Qwen4exp PLE and native lazy table reads. The planned short trial uses explicit `--load-mode mmap --lazy-mode on`,12K allocated context, one sequence, bounded GPU fit margins and no MTP drafter. It requires native lazy-table evidence and an actual table-shard process mapping, alongside the normal resource/ownership guards. The existing Flash-family bounded active swap policy is128/160 MiB/s over30 s with15% full PSI and three bad samples; RAM24/26 GiB, host2 GiB, VRAM256 MiB/card and82 C remain independent. No inference result is claimed until download/hash checks and the guarded tool/unload sequence finish.

Sources: [Unsloth guide](https://unsloth.ai/docs/models/qwen3.8-next), [pinned GGUF repository](https://huggingface.co/unsloth/Qwen3.8-Flash-Next-GGUF/tree/d96201194f103c906994f283f504209dc8d2a10c). Earlier isolated TensorFold results, rejected8K/16K admissions and source pins remain [dated evidence](TENSORFOLD-AND-UNSLOTH-ASSESSMENT-20261104.md).
