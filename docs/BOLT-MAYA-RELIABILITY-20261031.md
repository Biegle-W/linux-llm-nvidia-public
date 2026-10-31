# Bolt and DeepSeek/Maya reliability — October 31, 2026

DeepSeek/Maya is selected at its original 32K context. Bolt is **qualified in isolated tests; persistent deployment and normal-router verification remain pending** at 8K text-only. Existing weights, the RTX 3080 Ti/3080 main pair, the auxiliary RTX 3060 role, client defaults and independent resource guards are preserved. No model download or reboot was needed.

## DeepSeek/Maya selected bounded residency

The existing pinned cache controller uses a **36 GiB model-file residency target**, trimming toward 27 GiB, a **32 decimal GB startup expert read-ahead cap** and **4 decimal GB post-prompt warming**. Original **4,096-token prefill chunks** and **32,768-token context** remain. This periodic target is not a hard ceiling or a global cache purge.

After one 64-output warmup, three fixed-fixture 128-output requests measured median **1.8872 client decode tok/s**, **46.7 native prefill tok/s** and **46.8354 s TTFT**, with 2,179–2,198 input tokens. JSON, arithmetic, a 1024px red-image check, all three exact markers in **29,456 uncached input tokens**, a complete **512-token stream over 373.48 s** and **two fresh normal-router reloads** passed. The longer stream's 511/373.48 = **1.37 tok/s** is separate from the short-request median.

Peak qualification worker memory was **42.80 GiB**, worker swap **zero**, full-memory pressure **0.25%**, and hard-limit/OOM/OOM-kill events **zero**. Original conversation snapshots were restored byte-for-byte. Earlier pressure failures remain dated evidence. The other profiles retain their settings.

## Bolt: measured loading failures and qualified remedy

The existing cyankiwi AWQ INT4 checkpoint is revision `3df8bd99af5d58abe5f052ef81127dff092f26b4`, **55,332,700,488 base-weight bytes** on SATA. The existing vLLM 0.31/Marlin path runs text-only TP2/eager with 8,192 context, 1,024 batched tokens and concurrency one. The original checkpoint's Python, weights and configuration bytes were not edited.

The adapter maps the virtual gate projection in memory, releases unused CUDA reservations during construction and quantization, and offloads routed experts plus 2.5 GiB of Mamba output projections across the two ranks. Compact prefetch slots share storage only across layer shapes for the same parameter name/dtype, retaining separate fields/slots and the original copy/compute event ordering. Actual staging is **785,256,320 bytes per rank**, compared with **5,615,532,416 bytes** for the original shape-class pool. No text-model weights, expert routing or kernels are skipped by this storage change.

That compact adapter first passed basic 2K inference and then primary 8K correctness, but a fresh reload hit sustained loading pressure. glibc cleanup after postprocessing passed one load and then failed another at shard4, before postprocessing; it was insufficient on its own. Worker telemetry showed roughly 35–39 GiB anonymous memory plus several GiB of file cache pressing against the same 46 GiB soft budget despite ample host RAM.

The qualified variant keeps those safeguards and adds **checkpoint-scoped clean-cache advice during loading**. It preserves natural shard order, tensor objects and all loader options. After the caller consumes the first tensor from the next shard, the previous shard's clean cached pages can be advised away. Advice also runs before loading and once after loading, covering only the reviewed 27 checkpoint files. It opens files read-only and does not write weight bytes or purge global caches. Live CPU weight storage remains intact. glibc `malloc_trim(0)` runs after CPU-storage synchronization when free arena space is at least 64 MiB, returning freed pages rather than discarding live tensors. Local telemetry showed file-backed worker charge falling to about 35 MiB before postprocessing.

Two fresh-load arithmetic/JSON screens and a third full **8K quality/streaming load** passed with **687 guard samples** and **no guard stop**. The full test recovered all three exact markers from **7,373 input tokens** and completed **128 output tokens** over **281.27 s** between first and last content. Actual KV capacity was **52,662 tokens**, above the requested allocation. Fresh startup took **232–238 s**; the request speed measurements below exclude loading.

The one measured stream used 2,341 input tokens and gave **0.452 client SSE decode tok/s**, **254.35 native prefill tok/s**, **11.682 s TTFT** and **292.95 s total request time**. It followed correctness/retrieval requests, without a dedicated fixed-fixture warmup. It is **one observation**, not a three-request median or a matched comparison with Maya. Bolt is usable in this bounded scope but remains slow for generation.

Across the three loads, peak loading full-memory pressure was **5.07%**, peak inference pressure **0.00%**, and sampled worker memory about **46.001 GiB** against 46/48 GiB soft/hard limits. Loading swap occupancy reached **7.98 GiB**; occupancy is distinct from active churn. Peak measured 30-second inference swap writes were **zero** and combined I/O **0.074 MiB/s**, below the existing 1/8 MiB/s limits. Minimum sampled GPU free memory was **503 MiB** during loading; the existing reserve guard stops only after three consecutive bad samples and did not trip. The 512 MiB threshold was not relaxed. Maximum main-GPU temperature was **56 C**, below 82 C.

## Runtime integration and validation

The deployment proposal gives Bolt an independent copy of the same qualified runtime packages, with checked package origins, runtime and model-code/metadata hashes, weight-file sizes and relocatable command-line entry points. It does not replace Qwen's environment. The existing nightly update coverage remains complete for its six managed profiles; Bolt's custom adapter/runtime is explicitly pinned for manual requalification, so Qwen promotion cannot invalidate it.

**300 CPU tests passed** for the exact seven-profile deployment bundle using the independent runtime. The current live six-profile repository separately passed **263 CPU tests**. These include numerical prefetch layout/slot checks, live-tensor preservation, shard order/identity and read-only cache advice, authentication/placement/pin contracts, managed busy/queued unload protection, CLI alias handling and updater coverage. Persistent installation and normal-router verification status: **pending**. No normal-router success is inferred from isolated tests.

These are bounded quality, telemetry and reload checks, not a multi-hour or every-prompt guarantee. Historical benchmark results and rejected variants remain historical. [Numeric evidence](benchmark-results/20261031-bolt-maya-reliability.json).

## Research and source checks

- [Maya Linux RAM headroom discussion](https://github.com/mw00/project-maya/issues/77), [settings](https://github.com/mw00/project-maya/blob/main/docs/SETTINGS.md) and [prefill/cache discussion](https://github.com/mw00/project-maya/issues/280): motivated explicit residency, warming bounds and cache-state measurement. Other hardware did not predict local speed.
- [vLLM pinned-host allocation report](https://github.com/vllm-project/vllm/issues/56410): motivated allocator inspection. These trials retained pageable/no-UVA controls.
- [XPU materialization discussion](https://github.com/vllm-project/vllm/issues/57008): a diagnostic hypothesis, not proof of the same CUDA defect.
- [Official vLLM offload arguments](https://docs.vllm.ai/en/latest/configuration/engine_args/): generic byte-budget offload and grouped prefetch are different paths; installed code and measured failures determined the local adapter.
- [glibc heap trimming](https://man7.org/linux/man-pages/man3/malloc_trim.3.html) and [file-cache advice](https://www.man7.org/linux/man-pages/man2/posix_fadvise.2.html): the documented operations were CPU-tested, then measured under the unchanged GPU/cgroup guards.

Raw request logs, ownership data, credentials and conversation snapshot contents are excluded from the published evidence.
