# Current Qwen/Flash-Next Strata fails the reduced-RAM loading guard

The unchanged normal `flash-next-strata` profile was tested through the router on October 29 with the currently deployed guards. **It failed during loading**, before becoming ready. This confirms a current reduced-RAM problem in the selected resident-expert configuration; it does not mean Strata does not support Qwen/Flash-Next.

## What happened

The native launcher announced loading about 47 GB of experts into RAM and locking part for the GPU. Its log requested an expert arena of 20,464 two-MiB pages (**39.97 GiB**), besides other engine/desktop memory. It had reported about38.9 GiB host available before that arena. That is too large to retain the required headroom on this 45.55 GiB host.

The normal supervisor stopped the worker after host available RAM stayed below its 2 GiB floor. Maximum GPU temperature was only42 C, so the combined RAM/temperature stop was caused by RAM, not heat. The API returned 503 after the guarded backend stopped.

| Observed resource | Value |
| --- | ---: |
| Minimum host available | 0.717 GiB |
| Minimum host free | 0.408 GiB |
| Peak charged worker memory | 41.18 GiB |
| Peak worker swap during loading | 1.68 GiB |
| Maximum GPU temperature | 42 C |
| GPU0 / GPU1 free-memory minima | 5321 / 5792 MiB |
| Loading start to error | 34.5 seconds |

There were 6 sampled below-floor readings. Cgroup high/max/OOM/OOM-kill event counts were all zero. These are sampled extrema, not instantaneous maxima. Unlike the earlier high-MemAvailable Maya cases, this run recorded both MemFree and MemAvailable collapsing during a resident allocation.

Swap occurred during loading, when the maintained policy permits parked/loading swap. The model never reached inference, so this was **not an active-inference swap-churn stop**. Active swap, PSI and telemetry enforcement remained installed, but no inference-rate window was reached. GPU memory was not close to exhaustion during the observed loading stage; steady-state VRAM qualification was not reached.

## Actual guards and unchanged profile

- Supervisor host-available floor 2 GiB; three-reading hysteresis.
- Actual cgroup memory.high 44 GiB, memory.max 48 GiB and memory.swap.max=max.
- Temperature 82 C, swappiness 60, concurrency 1 and idle unload 600 s.
- Native startup additionally reported an unchanged internal 2560 MiB RAM floor.
- Native automatic VRAM placement was retained; no reserve override was inserted or inferred from the dense 512 MiB free-VRAM policy.
- Current preset remains 32K, automatic VRAM expert cache/prefill, speculative width 4, MTP, INT8 KV, vision and 9 workers. No rejected lcz.me/pageable variant was substituted.

`--expert-cache auto` concerns the native VRAM expert cache; it does not guarantee that the remaining resident CPU-expert allocation fits this reduced-RAM desktop. The current startup followed the resident allocation path, not the bounded Maya file-cache runtime.

JSON/arithmetic/image, near-window retrieval, sustained generation and fresh reload were **not run** because loading did not pass. No speed benchmark was repeated. The existing 97.09 tok/s selected number remains its dated October27 historical result, not a new measurement or a pass under today's guards.

## Final state and next decision

Canonical launch settings, registry and guard implementations were unchanged during the test. The router and DSH were preserved. Owned worker stopped, router idle, GPU reservation absent, no fallback restored. Qualification-status documentation was updated afterward without changing launch settings.

Making this configuration operate on the current RAM would require a separately qualified CPU-expert residency/streaming strategy; this test did not tune or apply one. Full-RAM cache restoration still requires explicit human DIMM-restoration confirmation, Linux capacity verification and guarded loading. There is no timer or MemAvailable trigger. The five other selected profiles and the newly qualified Maya configuration are unchanged.

[Numeric evidence](validation-results/20261029-qwen-current-guards.json).
