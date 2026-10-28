# NVIDIA-server agent handoff: AMD parity gaps — October 27, 2026

The user requested notes in this repository so agents on the NVIDIA server can
address the gaps identified in the [AMD/native Linux NVIDIA audit](https://github.com/Biegle-W/linux-llm-amd-public/blob/main/linux/hardware/AMD-NVIDIA-GAP-AUDIT-2026-10-27.md).
The original publication added notes only. The implementation status below was
updated by the NVIDIA agent on October 27; CURRENT-STATE.md remains authoritative.

Read the current README, [maintained registry](../config/maintained-profiles.json),
[maintained results](MAINTAINED-PROFILES.md), [network handoff](../network/README.md)
and any in-progress context tests before starting. The audit is a dated snapshot:
recheck current code and completed work instead of assuming a gap still exists.
Inspect Git status, live GPU reservation, owned units and active requests. Preserve
concurrent agent/user work and recover saved evidence before repeating tests.

## Execution order and ownership

Address G1/G2 first, then the remaining G3 documentation repair and G4 reporting
alignment. Implement and validate runtime work on the NVIDIA server, not on the
AMD host. G5/G7 primarily belong to AMD agents; NVIDIA should provide references
and results rather than change the other server. G6 requires selecting models
and validating fit before downloads. G8 is optional: do not enable a schedule
without the user's explicit choice. This note does not authorize firmware,
driver, reboot, storage relocation or unrelated application changes.

| Gap | NVIDIA-server action | Status at publication |
|---|---|---|
| G1: loading swap | Adapt phase-aware loading/idle/inference policy below | Guarded paths updated; CPU/readback and normal dense path verified. Maya still crosses active-write limits. The user cancelled the separate VM10 proposal; keep swappiness 60. |
| G2: idle unload | Add request-aware 600-second unload of owned inference only | Deployed at 600 seconds with hash-reviewed native adapters; actual idle/reload verification in progress |
| G3: documentation | Repair GLM storage-location cell; maintain README/AGENTS/results | Agent entry point and GLM storage cell repaired |
| G4: reporting | Add a portable matched protocol and explicit storage scopes | Pending; existing measurements preserved |
| G5: Maya vision lifecycle | Keep lazy CPU-vision patch evidence available to AMD agents | NVIDIA already has the candidate patch; AMD qualification remains separate |
| G6: model coverage | Evaluate user-selected additional models against actual NVIDIA fit | Coverage expansion not selected; preserve the six profiles |
| G7: preload/unload controls | Share existing NVIDIA endpoints/tests with AMD agents | Already present on NVIDIA; AMD implementation is separate |
| G8: gated updater | Design opt-in candidate validation/rollback/publication if requested | Manual staging implemented/CPU-tested; no recurring updater or schedule selected |

## G1 — corrected swap policy

The standing user correction allows swap during model loading and parked swap
pages afterward. Prohibit sustained aggressive churn during inference that
creates excessive writes or slows inference; nonzero swap occupancy alone is
not failure. The user explicitly approved removing the former 1 GiB occupancy cap. All six
maintained guarded workers now request `MemorySwapMax=infinity`; the phase-aware
owned-cgroup monitor protects active inference. All entry points were updated, including
launcher: `scripts/run_bounded_test.sh`, `network/worker_manager.py`,
`scripts/serve_router_moe.py`, dense workers and their tests.

Reference the AMD [policy](https://github.com/Biegle-W/linux-llm-amd-public/blob/main/linux/hardware/LOADING-SWAP-POLICY-2026-10-27.md),
[owned-worker guard](https://github.com/Biegle-W/linux-llm-amd-public/blob/main/linux/dsh/inference_swap.py)
and [host activity monitor](https://github.com/Biegle-W/linux-llm-amd-public/blob/main/linux/hardware/swap_activity.py).
Adapt to NVIDIA ownership and telemetry; do not copy AMD runtime paths or guards.

- Track explicit loading, idle and active-compute phases, including lazy loading.
  Preserve parked pages without an occupancy or cumulative-loading-write cap.
- The AMD v2 defaults use active windows of at least 30 seconds, stopping above
  1 MiB/s swapout or 8 MiB/s combined swap I/O; full-memory PSI above 10% for
  three active samples also fails. Keep units, debounce and active-time coverage
  explicit. Host I/O is system-wide, not worker-only attribution or proof of SSD wear.
- For systemd, unlimited swap is `MemorySwapMax=infinity`; kernel cgroup readback
  is `memory.swap.max=max`. The CLI property value `max` is invalid.
- Retain NVIDIA's independent RAM high/max budgets, host-RAM floor, GPU reserves,
  thermal limits, numerical checks, exact owned-unit cleanup and fail-closed
  telemetry. The review recorded 30/36 GiB dense RAM, selected MoE RAM up to 48 GiB,
  an 8 GiB host-available floor and 82 C thermal debounce. Re-read live selected
  budgets first; do not replace them with AMD's smaller-host limits.
- Do not execute frozen strict-swap harnesses unchanged, remove I/O monitoring,
  or change global swappiness. CPU tests must cover loading/parked pages,
  sustained active churn, phase transitions, missing telemetry and owned cleanup.
  A real bounded CPU cgroup must confirm RAM caps remain while swap reads back max.
- Qualify normal CLI/Desktop/API paths on the actual NVIDIA pair, preserve
  lifecycle memory/thermal evidence and record startup separately from inference.
  Missing active-window evidence is incomplete, not a pass.

## G2 — ten-minute idle unload

NVIDIA already has authenticated manual selection/unload and owned systemd units.
Add automatic unloading after 600 seconds without inference activity, using AMD's
[idle-lifecycle policy](https://github.com/Biegle-W/linux-llm-amd-public/blob/main/linux/hardware/MODEL-HUB-2026-10-22.md#ten-minute-idle-power-saving--october24)
as behavioral reference.

Loading, active requests, switching, owned jobs and GPU reservation must defer
unload. Health/catalog polling must not keep a model warm forever. Stop only
the owned inference unit; preserve router, DSH, terminals, browsers and unrelated
GPU applications. Retain worker adoption after router restart. Test race cases,
reservation handling, manual unload interactions, one actual idle expiry and
successful subsequent reload/API response. Do not claim a power saving without
measuring it.

## G3 — documentation and takeover readiness

The reviewed `docs/MAINTAINED-PROFILES.md` GLM row places `10,908` retrieval
tokens in its storage-location cell. Verify the current registry and repair it
to the NVMe checkpoint folder `models/maya/Maya-S24`, with the correct drive
label. This is a documentation repair; no benchmark rerun is needed.

Keep README as canonical policy and AGENTS as its thin discovery entry point.
After relevant work update selected registry, benchmark Markdown/numeric
summaries, network handoff and both private/public repositories in the same task.
Record completed verification, actual blockers, active jobs/locks, unfinished
steps and a concrete next action before yielding. Preserve historical results
and private raw evidence. Never replace missing timings with invented zeros.

## G4 — comparable reporting, not transplanted performance

AMD's standard trials use separate code/prose requests, fresh approximately 8K
prompts and a 256-token cap. NVIDIA's latest matched table uses approximately 2.2K
input and 128-output prose; decode timestamp intervals also differ. Check exact
fixtures, tokenizer counts, seeds, cache state and first-output definitions.
Shared model names can use different quantizations, contexts and kernels.

Add an explicitly named portable fixture/export mode without overwriting old
results or silently changing current metrics. Report native versus engine-phase
prefill, fresh TTFT, code/prose decode, configured context versus tested input,
base-weight size versus total allocated associated storage, drive/folder and
shared-weight accounting. Preserve the user's three category headings, including
empty categories. Do not compare historical numbers as matched hardware results.
New GPU measurements need an idle/admitted host and retained guards.

NVIDIA already has a maintained-profile registry; AMD's proposed generated
current-selected summary is AMD-owned work. Do not copy NVIDIA settings to AMD.

## G5–G8 — references and conditional work

- G5: NVIDIA's [Maya lazy CPU-vision patch](../scripts/patches/maya-lazy-cpu-vision.patch)
  starts CPU vision only when needed and releases it after image encoding.
  AMD retains an older qualified Maya and previously rejected a newer build on
  speed gates. Share the patch and lifecycle tests; AMD needs separate pinned-code,
  image, memory and performance qualification. Newer does not imply faster.
- G6: AMD has Empero, Sage, Flint, Bolt, Super and Ornith selections absent from
  the sampled NVIDIA registry. Check actual CUDA quantization support, per-card
  headroom and host-memory requirements before choosing downloads. The 12+10 GB
  NVIDIA pair is not equivalent to the 24+24 GB AMD pair. Preserve dense GPU-only
  policy and existing MoE streaming distinctions.
- G7: Existing `/router/select` and `/router/unload`, their authentication,
  active-request refusal and owned-unit semantics are useful references for AMD.
  Do not implement duplicates on NVIDIA.
- G8: AMD's gated daily updater is paused. A NVIDIA updater would need isolated
  candidates, exact pins, correctness/quality/speed/memory acceptance, rollback,
  sanitized publication and verified cleanup. Do not copy or activate AMD timers.
  The user must choose any new schedule.

## Acceptance and publication checklist

For each addressed gap, record commit, affected paths, exact settings/versions,
tests and real hardware coverage, retained limits, failures, cleanup, rollback
and remaining work. Mark pending/partial/complete separately; CPU-only checks
do not qualify GPU inference. Keep raw prompts, SSE, keys, live addresses, machine
identifiers and logs private. Update both NVIDIA repositories via the reviewed
public allowlist, review diffs and verify remote commits. Do not overwrite
concurrent NVIDIA-agent changes or claim deployment from this documentation commit.

Current implementation: G1 code, registry, CPU checks and real bounded CPU cgroup
readback are complete. Normal-launch GPU verification remains part of context
rollout. The already-running Strata 128K qualification retains its earlier 1 GiB
cap for honest attribution; subsequent launches use the approved policy. G2 and
lifecycle logging are CPU-tested drafts, not yet enabled. Manual candidate
staging is implemented and CPU-tested; no candidate was built or activated. Inspect CURRENT-STATE.md for live ownership.
