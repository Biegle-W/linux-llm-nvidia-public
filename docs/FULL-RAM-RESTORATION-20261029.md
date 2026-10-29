# Full-RAM restoration — October 29, 2026

The owner confirmed the 64GB RAM configuration was restored. Linux reports **61.3013 GiB usable** (64,279,104 KiB MemTotal). Both NVIDIA GPUs retain verified unlock; kernel 7.0.0-42-generic and driver 595.99.02 are unchanged. Host swappiness remains 60.

## Selected cache settings

| Profile | Restored full-RAM setting | Preserved |
|---|---|---|
| GLM / Maya | 40 GiB expert RAM tier | 64K context, 512 MiB native VRAM reserve, on-demand CPU vision |
| DeepSeek / Strata | 42 decimal GB expert store, LFU policy | 128K context, 512 MiB reserve, text-only |
| DeepSeek / Maya | 8 decimal GB warming and original mapped-expert mode | 32K context, 512 MiB reserve, newer hash-pinned binary |
| Qwen Flash-Next / Strata | Automatic cache choices adapt to the restored capacity | Mapped experts, both GPUs, 32K, Qwen-only 128/160 MiB/s swap limits |
| Dense Qwen / HyperQwen and SGLang | Unchanged GPU-resident settings | 56,320 / 32,768 context, uncapped worker RAM and dense GPU-headroom guard |

Maya DeepSeek's temporary 16 GiB file-residency target, explicit 12 GB pinned-cache setting and reduced-RAM read-ahead overrides are removed. The saved full-RAM environment is restored; the optional file controller defaults to inactive without its target variable. The improved binary and its identity check remain installed. Original native binaries and all historical evidence remain preserved.

## Verification and limits

All six profiles passed normal guarded loading and a parsed JSON arithmetic request. The three restored cache profiles also passed a distinct fresh-process reload and JSON check: nine successful checks in total. Selected contexts, exact cgroup budgets, native 512 MiB reserves, concurrency one, idle 600 seconds and the 2 GiB host floor were read back. No observed active swap-guard violation or OOM kill occurred. Qwen's separately approved exception remains local to Qwen; other profiles retain 1/8 MiB/s swap limits.

The larger GLM tier caused loading-time soft cgroup reclaim and parked swap. Those are recorded in the numeric evidence rather than described as zero swap. The updater now distinguishes soft `memory.high` throttling from hard `memory.max`/OOM events; missing counters still fail closed. Paired speed, hard-memory, thermal, active swap and full-pressure guards remain enforced.

These are **startup/JSON/reload checks, not new speed, image, near-window retrieval or sustained-generation qualifications**. Existing benchmark values keep their original dates, hardware and cache scope; reduced-RAM measurements were not relabeled as full-RAM results. The initial harness queried admission immediately after one completed Strata JSON stream and saw a transient busy flag. Its correct completed response and resource readbacks were reconciled; the corrected harness ran the remaining checks without replaying completed GLM tests.

The router returned idle, owned model workers stopped and no GPU reservation remains. DSH was preserved. The daily update timer is resumed for **03:00 America/Toronto**, next October 30 at 03:00 EDT, with no daytime catch-up.
