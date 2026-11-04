# Native IQ2 Bolt selected in API and DSH — November 4, 2026

Bolt's selected API and DSH entry now runs the tested official native IQ2 checkpoint on pinned llama.cpp11909, replacing the AWQ INT4/vLLM-offload launch. The historical **`bolt-vllm` ID is retained for client compatibility**; its API engine/quant metadata and both DSH display names now say native IQ2/llama.cpp. It does not start vLLM or the AWQ checkpoint. There remain nine entries, and saved Bolt selections continue to resolve. Unrelated providers and defaults are preserved.

The normal router passed guarded loading, an actual DSH read, its executed result, an exact follow-up answer and owned unload. Both GPUs returned to 1 MiB and no reservation remained. This is fresh verification of the maintained route, separate from the earlier isolated candidate tests. A final reload checked parity with the old loading-stage VRAM floor and owner-only/nonempty API-key guards. Both normal-route observations are retained below; the final guarded launch is the selected record, not a best-score choice.

## Current performance and configuration

| Model / quant | Engine | Prefill tok/s | TTFT s | Decode tok/s | Context tokens | Storage GB | Storage location |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Bolt 74B-A9B / Native IQ2 — selected | llama.cpp11909 | 502.58 | 12.870 | 68.046 | 163,840 | 22.018 | SATA SSD |
| Bolt 74B-A9B / Native IQ2 — initial route check | llama.cpp11909 | 502.03 | 12.888 | 66.577 | 163,840 | 22.018 | SATA SSD |
| Bolt 74B-A9B / AWQ INT4 — retired reference | vLLM-offload | 217.35 | 29.320 | 0.361 | 163,840 | 55.333 | SATA SSD |

The new normal-route decode observation is **188.4x** the same-day AWQ reference. This is a comparison of complete quantization/engine/placement configurations, not equal-quality or sustained-throughput evidence. Native/AWQ first prompts contain 6,369/6,369 tokens and 42/41 generated tool-argument tokens, with zero reported prompt-cache reuse. OS file caches were not dropped. Loading and the follow-up are excluded from the metrics; TTFT includes client/parser buffering. Context is the unchanged allocated limit, not a new full-window quality test.

Selected settings are the previously qualified 384 MiB native fit target per card, layer split, Q8_0 K/V cache, mmap/lazy-off, batch/ubatch256/128, eight threads, one slot, reasoning off, no vision projector and no drafter. Native model buffers are 10,123.69/8,634.88 MiB on the GPUs and 2,232.22 MiB (2.180 GiB) CPU-mapped:89.4% of weight-buffer bytes are GPU-resident. The earlier256 MiB arm remains rejected after its independent VRAM guard stop; it was not promoted.

The publisher-hash-verified22.018 GB file stays on SATA. Binary/source/shared-library pins remain unchanged. [Exact maintained runtime manifest](../config/bolt-iq2-runtime.json), [prior fit qualification and provenance](BOLT-NATIVE-IQ2-20261104.md). The old AWQ checkpoint, dedicated runtime and obsolete adapters were subsequently deleted at the user's request. Dated benchmark records, Git history and small private source/configuration preimages remain. [Removal verification](BOLT-AWQ-REMOVAL-20261104.md).

## Guards, telemetry and release

| Profile | RAM high/hard GiB; host reserve | VRAM / thermal | Swap / pressure |
| --- | --- | --- | --- |
| Selected native IQ2 Bolt | 87.76984787/89.76984787; separate2 GiB available-host floor | 256 MiB free/card during loading and after ready;82 C; 3 bad 2-second resource samples | Unlimited occupancy; active writes1 / combined8 MiB/s over30 s; active full PSI10%, loading15%,3 bad samples |

Exact kernel caps94,242,156,544/96,389,640,192 bytes were observed, retaining2 GiB outside the hard cap. Current-boot unlock/host-staged transport, fail-closed telemetry, minimum90 GiB installed usable RAM, swappiness60, parallel1 and idle600 remain. Busy detection, deferred-request protection, switching and idle observation now use llama.cpp processing **and deferred** gauges for this entry; missing/nonfinite gauges cannot authorize unload. The daily updater explicitly recognizes the new pinned runtime, and updates remain paused.

The 12 resource samples (median interval 2.06 s) recorded peak charged worker RAM 1.54 GiB, swap 0.0 MiB, minimum available host RAM 86.10 GiB, minimum nonloading GPU free 621/458 MiB and GPU temperatures up to 49/35 C. No RAM max/OOM/guard event occurred. Charged memory is not total CPU weight residency: shared clean pages can be charged outside the worker. Samples may miss transient peaks, and the short native calls did not fill a complete30-second active swap window.

456 CPU tests passed, including maintained manifest/context/fit matching, managed port/alias, DSH name replacement without disturbing unrelated providers, native busy/deferred preservation and updater coverage. The CPU run also required protocol fixtures to follow the now-native Bolt entry and deterministic waiting for fixture admission release; production response ordering was not changed. The idle hub was refreshed once to load the new routing code; the independent API and unrelated sessions were preserved. All tests finish with model workers unloaded.

## Why AWQ/vLLM-offload was so slow

The primary diagnosis is repeated host-to-device weight movement in this particular offload configuration. This is supported by local code and logs, not a GPU bus timing trace.

1. **The old placement offloaded almost the whole large parameter set.** The55.333 GB AWQ checkpoint was served with `--offload-backend prefetch --offload-group-size1 --offload-num-in-group1 --offload-prefetch-step1 --offload-params experts out_proj in_proj`. Initialization recorded160 offloaded-module instances across two ranks and47,005,917,184 CPU parameter bytes combined. The post-initialization offloader summary reports80 modules and23.5030 decimal GB per rank, with only0.8613 GB of reusable GPU prefetch buffers per rank. These are model-weight buffers, not KV cache or SSD spill.

2. **Active MoE parameter count does not bound this transfer volume.** The installed `_ModuleOffloader.start_onload_to_static` loops over each offloaded parameter buffer and executes `gpu_buffer.copy_(cpu_storage, non_blocking=True)`. It is not a selected-expert-only transfer/cache in this path. Routing only9B active parameters reduces arithmetic, while complete offloaded expert arrays still cross the CPU–GPU boundary as their layers run. The compact pool saves VRAM through reuse; it does not make the other layers' weights persist on the GPUs. [vLLM prefetch implementation](https://docs.vllm.ai/en/latest/api/vllm/model_executor/offloader/prefetch/).

3. **Pageable staging limits the prefetch benefit.** The selected AWQ runtime disabled pinned host weights and UVA, preserving the earlier guarded choice. PyTorch documents pinned host data as a requirement for copy/compute overlap, alongside suitable hardware and a separate stream. This makes the old pageable copies a likely additional synchronization/staging cost. [PyTorch transfer guidance](https://docs.pytorch.org/tutorials/intermediate/pinmem_nonblock.html). A historical pinned-host arm was killed by oomd on the64 GB setup; no new96 GB pinned AWQ trial was run. More RAM does not by itself remove repeated PCIe traffic.

4. **One-step prefetch and eager execution leave limited overlap.** Prefetch depth1 was selected to fit the small cards; deeper prefetch needs additional VRAM. The earlier prefetch-two trial changed decode only0.39225→0.39256 tok/s. The old command also uses eager execution, adding launch overhead. These are plausible secondary costs, not separately timed contributions. [vLLM offload settings](https://docs.vllm.ai/en/latest/api/vllm/config/offload/), [local prior tuning evidence](VRAM256-OPTIMIZATION-20261103.md).

5. **The observed limits do not point to swap or thermal throttling.** In the same-day AWQ run, sampled swap was0 MiB, active pressure was0%, no guard fired and peak GPU temperature was59 C. The file was loaded from SATA before the timed request, and decode metrics exclude loading. Both GPUs retain direct CPU PCIe4 x8/x8 links; enabling GPU P2P would not turn their CPU-to-GPU transfers into peer transfers. The native replacement retains disabled P2P and is much faster with most weights remaining on the GPUs.

At0.36113 tok/s the AWQ decode observation is about2.77 s/token. About23.5 GB of offloaded buffers per rank represents a large transfer burden on PCIe4 x8 before staging, synchronization and computation. This is an order-of-magnitude consistency argument, not a measured bus-utilization result. No Nsight trace was collected, so a precise percentage attributable to transfers versus kernels, collectives, eager launches or allocator behavior is unknown. GPU utilization alone is insufficient to assign that split.

Native IQ2 reduces the checkpoint to22.018 GB and keeps about18.32 GiB of weight buffers across the GPUs, leaving only2.18 GiB CPU-mapped. That placement change, smaller mixed-precision weights and a different inference engine jointly explain the strong improvement; the benchmark cannot isolate their individual contributions. Full quality equivalence between AWQ INT4 and the native trained IQ2 mix was not tested.

[Sanitized normal-router results and slowdown evidence](benchmark-results/20261104-bolt-iq2-entry.json). Historical AWQ speeds are preserved under their original configuration; they are not current performance of the compatibility ID.
