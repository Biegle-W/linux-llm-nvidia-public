# Bounded model-file residency qualifies DeepSeek/Maya at 512 MiB

DeepSeek/Maya passed at **512 MiB native VRAM reserve and unchanged 32,768-token context** on the 45.55 GiB reduced-RAM host. The selected temporary configuration combines a 16 GiB model-file cache target with a native 12 decimal GB pinned hot-expert cache. JSON, arithmetic, image, 29,467-input-token retrieval, 426.5s continuous generation, a fresh isolated process reload and two normal guarded loads all passed. Observed worker swap occupancy and swap read/write rates were zero.

The saved three-request screen measured **1.23 decode tok/s**, 42.5 prefill tok/s and 51.491s TTFT. Earlier full-RAM/historical rates remain preserved; no fresh paired 2,048 MiB control was produced, because the earlier reduced-RAM configuration failed its swap guard.

## Why more permitted RAM can still trip the swap guard

The controls are separate:

| Control | Meaning |
| --- | --- |
| Native VRAM reserve: 512 MiB per GPU | Leaves GPU allocation headroom; lowering it allows more GPU-resident experts. It is not a host-RAM allowance or a continuous free-VRAM floor. |
| Host-available floor: 2 GiB | Stops sustained low-headroom operation. Lowering this floor permits operation with less headroom; it does not force RAM allocation or prohibit swap above the floor. |
| Owned-worker swap guard | Stops writes above 1 MiB/s or combined reads/writes above 8 MiB/s over a 30-second inference window, independently of MemAvailable. |

Maya’s native warming controls bounded explicit prefetch/copies, not demand-loaded mmap residency. Demand reads could still grow the file-backed working set. Earlier failures showed mostly swap writes, not evidence of an OOM kill or repeated swap readback. Read-only model-file pages themselves can be discarded and reread; swap writes concern other swap-backed worker memory. The exact previous victim mappings were not isolated.

Linux MemAvailable includes reclaimable file cache; swappiness expresses relative swap/filesystem paging cost, not a RAM-utilization percentage. Reclaim may therefore choose swap-backed pages while MemAvailable remains high. This interpretation is consistent with the evidence, but does not identify the exact kernel page-selection mechanism. See [kernel MemAvailable documentation](https://www.kernel.org/doc/html/next/filesystems/proc.html#meminfo) and [swappiness documentation](https://docs.kernel.org/admin-guide/sysctl/vm.html#swappiness). The same Maya failure had occurred at 2,048 MiB before the 512 MiB trial, so lowering the reserve was not established as its cause.

## What the controller changes

The opt-in Linux patch scans the existing read-only GGUF mappings with mincore. Above the 16 GiB target, it rotates through 64 MiB ranges, drops this mapping’s page-table entries with MADV_DONTNEED and asks POSIX_FADV_DONTNEED to discard clean backing pages, trimming toward 12 GiB. The virtual mappings and file data remain intact; future reads fault the original bytes back in. It pauses 200 ms between complete scans; scans themselves take additional time. Only the model’s existing mappings/descriptors are selected, and the controller is joined before their destruction.

This is a periodic residency target, **not a hard ceiling** or a system-wide cache purge. It preserves normal read-ahead. The native copied hot-expert cache is separately capped/pinned at 12 decimal GB; other experts continue streaming. Normal model-file SSD reads remain permitted, while the unchanged guard still monitors actual swap I/O. No weights, quantization, precision, context, drafting or mathematical kernels changed.

## Screens and qualification

| Candidate | Outcome | Swap guard |
| --- | --- |
| 8 GiB target with random-access hints | Intentionally stopped after about 0.2 tok/s partial decode; not qualified | No stop; zero observed swap |
| 24 GiB target with random-access hints | Intentionally stopped for the same speed problem; not qualified | No stop; zero observed swap |
| 16 GiB file target + 12 GB pinned cache, normal read-ahead | Full isolated and normal qualification; applied temporarily | No stop; zero observed swap |

The first two screens support feasibility of controlling residency, not operating benchmarks. The final candidate removed the experimental random-access hints and used the native pinned hot cache for reuse. These combined changes are not a controlled estimate of any one knob’s speed effect. One executable-name allowlist rejection occurred before engine loading; the corrected trial did not repeat a genuine engine failure.

## Resource and validation evidence

- Minimum sampled host available: 21.66 GiB; peak charged worker memory: 34.09 GiB.
- Maximum temperature: 60 C; GPU free-memory minima: 298/324 MiB. Allocation reserve and the separate dense 512 MiB free-VRAM stop are different controls.
- Largest observed file-residency scan excluding initial scans: 16.89 GiB; including initial scans: 21.79 GiB. Largest estimated post-trim/scan value: 15.85 GiB. No reported eviction syscall errors.
- Zero sampled worker swap occupancy; all observed active swap rate windows were zero. Samples do not establish instantaneous extrema. Charged cgroup file memory is not identical to total shared mapped-file residency.
- C++ disk-backed tests passed real clean-page eviction, concurrent reread/data preservation and joined shutdown. Seven Python runtime-pin/MoE guard/shutdown tests passed.
- The separate-output builder reproduced the patched source and passed its tests without changing installed Maya source. Binary identity is pinned per build; bit-identical rebuilt binaries are not claimed.
- Two distinct normal worker processes passed effective binary/environment/context/guard-limit readback and JSON, with zero worker swap before unload. Router/DSH were preserved; final router idle, owned workers stopped, no GPU reservation or fallback.

The 46/48 GiB worker budgets, host floor 2 GiB, temperature 82 C, swap/PSI/telemetry guards, swappiness 60, concurrency one and idle unload 600 seconds remain. Existing dense settings and the other MoE selections are unchanged.

## Current six selected results

Only DeepSeek/Maya has a new measurement in this follow-up. Other rows retain their dated selected runs, identified in the numeric evidence. Shared checkpoints count once physically; sizes exclude auxiliary packs and caches. Expert RAM tiers in SSD-streamed profiles are caches, not complete CPU-RAM placement.

### VRAM-only models

| Model / quant | Engine | Prefill (tok/s) | TTFT (s) | Decode (tok/s) | Context (tokens) | Storage (GB) | Storage location |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Qwen3.8-27B / AutoRound INT4 / INT8 embedding | HyperQwen-vLLM | 1,491.7 | 1.499 | 89.10 | 56,320 | 15.79 | Samsung SSD 870 QVO SATA: models/engine-tests/qwen38-27b-hyperqwen-fast |
| Qwen3.8-27B / AutoRound INT4 / INT8 embedding | SGLang | 1,667.9 | 1.346 | 84.76 | 32,768 | 15.79 | Samsung SSD 870 QVO SATA: models/engine-tests/qwen38-27b-hyperqwen-fast |

### MoE models with CPU RAM offload

None currently kept. Expert RAM tiers in streamed profiles are caches.

### MoE models with SSD streaming

| Model / quant | Engine | Prefill (tok/s) | TTFT (s) | Decode (tok/s) | Context (tokens) | Storage (GB) | Storage location |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Qwen3.8-Flash-Next / IQ3_XXS | Strata | 593.2 | 3.753 | 97.09 | 32,768 | 75.84 | CT1000P3PSSD8 NVMe: models/strata/models/IQ3_XXS |
| GLM-5.3-Flash / Maya-S24 | Maya | 49.3 | 44.703 | 2.59 | 65,536 | 94.70 | CT1000P3PSSD8 NVMe: models/maya/Maya-S24 |
| DeepSeek-V4.1-Flash-1017 / Maya-S | Strata | 33.6 | 65.220 | 1.88 | 131,072 | 339.48 | CT1000P3PSSD8 NVMe: models/maya/DeepSeek-V4.1-Flash-1017-GGUF/Maya-S |
| DeepSeek-V4.1-Flash-1017 / Maya-S | Maya | 42.5 | 51.491 | 1.23 | 32,768 | 339.48 | CT1000P3PSSD8 NVMe: models/maya/DeepSeek-V4.1-Flash-1017-GGUF/Maya-S |

## Build, provenance and restoration

The [native patch](../patches/maya-ds4-file-cache-target.patch) and [isolated builder](../scripts/build_maya_file_cache_bound.py) require the recorded base-source SHA256 and never overwrite the installed native build. Use a fresh disk-backed --output directory; invoke the builder through the maintained minimized visible-terminal launcher. The disk-backed C++ test is included in the build. The qualified binary is separately installed and checked against [its manifest](../config/maya-cachebound-runtime.json) on normal launch; a changed binary is rejected. Raw configs, credentials, ownership IDs and telemetry remain local.

Current source/registry/launcher preimages and the original binary hash were archived privately and remotely verified before deployment. Original native source and binary remain installed. The selected cache choices are temporary for reduced RAM. After explicit human confirmation that the DIMM is restored, verify Linux capacity, restore appropriate full-RAM cache/prefill settings from preimages while preserving the qualified 512 MiB reserve and all guards, then verify normal guarded load/reload. No timer or MemAvailable trigger. Bounded qualification does not establish multi-hour reliability.

[Numeric evidence](benchmark-results/20261029-maya-demand-cache.json).
