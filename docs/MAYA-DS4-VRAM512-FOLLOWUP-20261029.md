# DeepSeek/Maya did not qualify at 512 MiB after three cache follow-ups

Later October 29 update: the [demand-file-cache controller](MAYA-DEMAND-CACHE-20261029.md) qualified DeepSeek/Maya at 512 MiB. Outcomes below remain historical evidence for earlier configurations.

Three additional isolated candidates failed the unchanged owned-worker swap guard on the 45.55 GiB reduced-RAM machine. **Nothing was applied:** DeepSeek/Maya retains its original 2,048 MiB reserve and configuration. GLM and DeepSeek/Strata retain their previously qualified 512 MiB selections; dense RAM-cap removal is unchanged.

## What stopped the worker

The original 512 MiB run wrote 7.94 MiB/s to swap over 30.43 seconds. This exceeded the existing 1 MiB/s sustained-write threshold. The supervisor deliberately stopped the worker. Cgroup memory.high, memory.max, OOM and OOM-kill counters stayed zero in the original and all three follow-ups. The engine’s later generic “usual cause is running out of RAM” message is not proof of an OOM kill.

The working set was dominated by file-backed model pages. Linux reported substantial MemAvailable because clean file cache is reclaimable; that does not mean no reclaim or swap can occur. The evidence is consistent with file-cache/anonymous-memory reclaim competition at swappiness 60, but does not isolate the exact kernel page-selection cause. This is an observed swap-policy failure, not proof that physical RAM was exhausted.

## Candidates and outcomes

| Candidate | Change from original 512 MiB candidate | Furthest completed request | Swap writes at stop (MiB/s) | Swap reads at stop (MiB/s) | Window (s) |
| --- | --- | --- | ---: | ---: | ---: |
| deepseek-maya-vram512 | Original: 4,096-token chunks, 8 GB post-prompt warming | None (stopped during warm-up) | 7.94 | 0.0033 | 30.43 |
| deepseek-maya-vram512-no-prefetch | Warming, Engram cache and speculative prefetch disabled; 4,096-token chunks | None (stopped during warm-up) | 7.23 | 0.0126 | 30.42 |
| deepseek-maya-vram512-chunk256 | Same disabled caches/prefetch; 256-token chunks | Warm-up (628 input / 64 output) | 4.29 | 0.0008 | 30.41 |
| deepseek-maya-vram512-pinned12 | 256-token chunks; native copied/pinned expert cache capped at 12 decimal GB, warming off, 128 MB read-ahead, predictive prefetch off | None (stopped during warm-up) | 6.03 | 0.0039 | 30.43 |

Disabling speculative prefetch did not bound demand-loaded file residency. Smaller chunks completed warm-up, then failed during the first measured response. The pinned-cache run confirmed native placement: 12.0 GB pinned and 11.6 GB of expert payload copied; remaining experts still read in place. It also failed during warm-up. These are distinct rejected configurations, not repeated attempts at the same settings. Earlier October 28 reduced-RAM cache failures were reused as evidence rather than rerun.

## Resource evidence

| Candidate | Peak charged worker (GiB) | Peak charged file pages (GiB) | Peak worker swap (MiB) | Minimum host available (GiB) | Maximum temperature (C) |
| --- | ---: | ---: | ---: | ---: | ---: |
| deepseek-maya-vram512 | 39.80 | 39.21 | 318.9 | 35.14 | 52 |
| deepseek-maya-vram512-no-prefetch | 36.02 | 35.47 | 228.6 | 34.79 | 54 |
| deepseek-maya-vram512-chunk256 | 30.84 | 30.11 | 134.0 | 36.83 | 59 |
| deepseek-maya-vram512-pinned12 | 37.12 | 25.42 | 279.6 | 25.84 | 57 |

These are sampled extrema, not instantaneous maxima. Cgroup file residency reflects charge ownership and can differ substantially from a process’s total mapped residency when model pages are shared. A sampled process/cgroup check was used to identify this distinction; lower charged memory alone was not treated as success.

## What remains selected

DeepSeek/Maya remains at 32,768 context, 2,048 MiB native VRAM reserve, mmap experts on, 4,096-token prefill chunks and DS4_WARM_GB=8. Canonical config, credentials, runtime binaries, weights, precision, cache seed and selected benchmark metadata are unchanged. No complete three-request benchmark median was produced by these candidates; partial speeds do not replace the historical selected result.

The 46/48 GiB MoE worker budgets, 2 GiB host-available floor, 82 C thermal stop, active owned-worker swap/PSI/telemetry guards, swappiness 60, concurrency one and 600-second idle unload were preserved. No guard threshold, swap limit or host memory policy was relaxed. All normal promotion checks were skipped because isolated qualification failed.

No passing 512 MiB setup was established using these tested native cache controls. Further work could target a separately implemented and qualified bound on demand-loaded expert residency, or a new test after the human explicitly confirms restored RAM. Neither is claimed here. Full-RAM restoration still requires Linux capacity verification and guarded loading; elapsed time or MemAvailable is not a trigger.

Final owned worker is stopped, GPU reservation released and router idle; DSH was preserved. No fallback was restored.

[Numeric evidence](benchmark-results/20261029-maya512-followup.json). [Current six selected results](MOE-VRAM512-20261029.md).
