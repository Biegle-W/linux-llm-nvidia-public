# Hardware tuning research — October 29, 2026

Follow-up: [October30 qualification and selected result](HARDWARE-TUNING-QUALIFICATION-20261030.md). The research-only status below describes the earlier investigation.

Status: recommendations for qualification; no settings applied, runtime updated or GPU tests started by this research.

The 64GB RAM / RTX 3080 Ti 12GB / RTX 3080 10GB system has credible upstream support for Qwen Flash-Next. Its current mapped-expert configuration is one memory mode, not proof that the hardware cannot run a faster resident configuration. No exact forum-tested winner for this CPU and GPU pair was found.

## Evidence and hardware

The closest [community report, Strata #2367](https://github.com/Niko1221/Strata/issues/2367), uses a single 3080 Ti 12GB and 64GB DDR4 with a Ryzen 5800X3D on Windows. It reports 50.4 tok/s median in resident mode, then 66.1 after an engine update plus a tuning bundle. Its IQ3_S, context, CPU, OS and engine differ from this installation. The second result does not isolate one flag and includes no quality qualification. Its 42.85GiB resident budget is evidence of feasibility on that machine, not a safe budget to copy here.

Locally verified hardware is i5-13600KF (6P+8E, 20 logical CPUs), 64GB installed / 61.3013GiB usable, DDR5-4200, and the two cards above. Current Qwen startup measured approximately 6.4GB/s to the 10GB helper and 19.5GB/s to the 12GB main card. Both GPUs are already used; their 22GB aggregate capacity is split across stages. Measured transfer bandwidth matters more than advertised PCIe capability for balancing those stages.

The current Qwen engine is 0.1.50 (Terminal 0.1.51); inspected Strata source is 4b9e05a2. Maya source and the custom DeepSeek binary base are 8b4b39f84e35393833b31b80e82bee92e69bb646. Current upstream main documentation may describe later features. Confirm the actual binary/config path accepts each candidate before launch; do not upgrade merely to follow a forum command.

## Candidate matrix

| Profile | Preserve | First candidate | Subsequent isolated comparisons |
|---|---|---|---|
| Qwen / Strata | IQ3_XXS, 32,768 context, both GPUs, MTP, int8 KV, spec 4, 9 workers, observed 700MiB native reserve | Resident experts if the non-GPU complement and total working set fit; otherwise a bounded native resident tier, initially 32GiB, then up to 36GiB only if measured headroom permits | Auxiliary CPU placement; K17 versus current auto K20; CPU workers 5/9/13; async and pipeline separately |
| GLM / Maya | S24, 40GiB configured RAM tier, 65,536 context, current guards | Native GLM calibration for CPU/PCIe work split, thread count and SSD read chunks | Validate per-card lane choices against asymmetric PCIe bandwidth |
| DeepSeek / Maya | Mapped experts, 8GB warming, 32,768 context, current reserves and guards | Candidate without explicit `--cpu-threads 14`, allowing built-in CPU-lane timing | Compare automatic lane selection against fixed 14 under matched cache conditions |
| DeepSeek / Strata | Existing 42 decimal GB LFU hot store, 131,072 context | Retain as baseline pending a backend-specific experiment | Do not transfer Qwen resident flags or Maya copy policy to this backend |

All candidates are unvalidated. The 32–36GiB Qwen range is an engineering starting point, not a forum recommendation or selected optimum. The process has 44/48GiB high/hard memory limits; a resident-tier allocation is only part of its total memory. Host availability, process/cgroup memory, page cache, KV and staging overhead must all fit. An unsuccessful fit must fall back to the saved baseline without guard changes.

## Qwen rationale and compatibility

[Strata memory documentation](https://github.com/Niko1221/Strata/blob/main/docs/DETAILS.md) distinguishes plain mmap, fully resident non-GPU experts and a bounded hot resident tier. Plain mmap can require SSD reads on misses. Auxiliary CPU placement can move helper work off the host thread. These are reasons to test placement and residency rather than increase swap tolerance.

[Multi-GPU documentation](https://github.com/Niko1221/Strata/blob/main/docs/MULTI_GPU.md) supports resident modes on layer splits since 0.1.40. Keep the faster/larger main card last. NVIDIA pipeline windows are opt-in and consume additional cache/state memory; asynchronous operation needs quality checks. Test these only after a resident baseline. Avoid the experimental `STRATA_ROUTE_RESIDENT` combination implicated in [a dual-3080-Ti report](https://github.com/Niko1221/Strata/issues/1578).

Native inspected source accepts `--resident-budget-gib` and describes ranked non-GPU experts copied into RAM. However, installed `setup.py` warns that its setup-level budget selector is for UD-Q4_K_XL and UD-IQ4_XS. Therefore a budget for IQ3_XXS must be checked through the actual native config/launcher path; simply passing that option to setup is not an established recipe. Check startup explicitly reports resident bytes and both stages, rather than silently retaining mmap or selecting one GPU. Full resident mode can fall back to plain mapping when it cannot fit.

The [maintainer's i5-13600K discussion](https://github.com/Niko1221/Strata/issues/642) identifies nine workers as the intended default. Current nine workers are not an obvious configuration bug. Preserve them for the memory-mode comparison, then measure alternatives. Current native auto split selected K20 with K17 close in estimated timing; that makes K17 a bounded comparison, not a predetermined improvement.

## Maya rationale

[GLM settings](https://github.com/mw00/project-maya/blob/main/docs/SETTINGS.md) describe calibration of CPU/PCIe division, worker counts and disk reads, accepting improvements above 3%. Run the family-appropriate calibration against a candidate copy, then qualify its result through the guarded launcher. Keep the current RAM tier and S24 first. Full `--glm-ram-resident` requires the entire non-GPU expert set to fit; 64GB RAM plus 22GB VRAM alone does not establish that for this model. DSpark speed calibration is a separate DeepSeek drafting experiment.

The [installed DeepSeek source base](https://github.com/mw00/project-maya/blob/8b4b39f84e35393833b31b80e82bee92e69bb646/src/ds4/ds4_model.cu) provides two important constraints (copy policy around lines 5404–5450; CPU timing around 6033–6037). Auto copy policy uses all or none because partial copies reduced speed on 32/64GB systems. `DS4_COPY_GB` is an experimental static-copy budget, so `--mmap-experts off` plus a large partial copy is not a supported performance conclusion. Explicit CPU threads or a forced CPU lane bypass automatic timing; otherwise another measured lane must beat the default by over 5%. Eight GB warming populates file cache; it is not an eight GB resident expert store. Candidate CPU auto selection must leave the lane environment unset as well as omit fixed threads. Native default `cpu_threads` is zero. No unverified environment alias is needed.

A [Maya maintainer discussion](https://github.com/mw00/project-maya/issues/43) explains why adding a slower GPU can hurt stage timing. That observation on different cards does not establish single-GPU superiority for this pair. Keep both cards first and measure placement.

## Qualification and conclusion

Keep quantization, context, prompts, guards and runtime pins fixed. Compare each candidate to a fresh baseline in alternating order, recording cold versus warmed cache, startup resident bytes, per-stage cache hits, transfer timings, RSS/cgroup memory, major faults, swap, TTFT, prefill and decode. Repeat sufficient paired requests to distinguish variability. Follow speed screens with JSON/arithmetic/image where supported, near-window retrieval, sustained generation and a fresh reload. Promote only a reproducible improvement that passes the existing quality/resource gates; retain preimages and historical results.

The latest local short screen was Qwen 16.87 tok/s median and DeepSeek/Maya 3.30; those earlier measurements are not paired controls for these proposals. Historical higher Qwen figures and the community figures do not predict a resident-mode speed here. Research establishes a concrete test order: Qwen memory residency first, GLM native calibration, then DeepSeek/Maya automatic CPU selection. It does not establish an optimized winner yet.
