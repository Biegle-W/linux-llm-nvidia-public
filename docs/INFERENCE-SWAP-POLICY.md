# Inference swap and memory-pressure policy

The user explicitly approved unlimited worker swap occupancy with active churn
protection on October 27. Loading and parked pages are allowed; normal workers
use `MemorySwapMax=infinity`, whose kernel readback is `memory.swap.max=max`.
The host swap file is not enlarged. Selected MoE RAM soft/hard limits, uncapped guarded dense RAM, and the user-approved 2 GiB
host-available floor across all six profiles, temperature guards and GPU placement/reserves remain.
No global swapoff or swappiness change is part of this policy. The latest user
direction supersedes an earlier separate VM10 experiment approval: keep host
swappiness at 60; that experiment never ran. The observed host
swappiness is the Linux default 60; occupancy alone does not measure swap I/O.
The former 1 GiB cap remains historical benchmark attribution, not current policy.

`scripts/inference_swap_guard.py` reads the owned cgroup's cumulative `pswpin` and
`pswpout` page counters and full-memory pressure. It distinguishes loading,
warm-up, idle and actual inference using native busy state or dense running-request
gauges. Benchmark warm-up is explicitly marked. After a continuous 30-second
inference window, more than **1 MiB/s swap writes** or **8 MiB/s combined swap
I/O** stops the owned worker. Full-memory pressure above 10% for three samples
after that active window also stops it. Missing telemetry and counter continuity
fail closed after the documented checks. Short requests may have no complete
30-second window; that is not a sustained-churn qualification.

Violations latch per profile. Automatic generation does not repeatedly reload a
stopped worker; an explicit model selection clears its latch, subject to normal
locks/admission. Only the configured owned worker is stopped. Router, DSH,
unrelated applications and other models' latches remain. Private per-worker logs
record counters, rates, pressure and the reason, with bounded production rotation.

These are conservative operating thresholds, not measurements of physical NAND
wear or proof of SSD damage. Model-weight SSD reads are distinct from swap writes.
The kernel documents the difference between
[swap occupancy and its hard limit](https://docs.kernel.org/admin-guide/cgroup-v2.html#memory-interface-files)
and [swappiness as relative I/O cost](https://docs.kernel.org/admin-guide/sysctl/vm.html#swappiness).
Lowering a global knob blindly is not a substitute for measuring the worker.

## Rollout and evidence — October 27

70 CPU checks (including idle, telemetry and candidate-staging drafts) passed; 50 policy/router/storage checks passed under the approved policy. A real CPU-only systemd scope
confirmed 64/128 MiB RAM limits with `memory.swap.max=max` without allocating
swap or running GPU work. Checks include loading/parked swap, active rate windows, pressure,
missing counters, latching, explicit reload and GPU-lock containment. The router
has loaded the new wrapper ownership/reload code. Dense and MoE supervisors use
the new monitor on subsequent launches; the completed GLM long-context
qualification received an owned-invocation observer without repeating its speed
tests. Normal functional verification has now passed all six launch paths with actual
RAM/swap readbacks; sustained Maya qualification remains unresolved.

Saved measurements identify why this is needed: the failed Flash host-KV trials
reclaimed heavily at the 44 GiB soft limit with full bounded swap. Their evidence
is retained; no throughput is invented. Maya DeepSeek's current-control telemetry
also contains active swap-write windows above the new threshold, so bounded
warming/cache alternatives must qualify before a new setting is promoted.
GLM's long-input observation has parked swap near 1 GiB with zero measured
active swap writes and negligible full-memory pressure. Parked pages alone do not
invalidate it. Old reports retain their original guard policy and are not
retroactively labeled as fully monitored by the new implementation.

The first new-policy Maya 64K full-cache and 36 GB warm-cap trials exercised the
active guard on the GPUs: 30-second write rates reached 5.99 and 7.73 MiB/s.
Only the owned test worker was stopped. These are threshold crossings, not proof
of physical SSD wear or a prediction that the rate would have persisted. Smaller
cache budgets remain under test; unlimited occupancy does not disable active
inference protection.

A normal HyperQwen restore has also read back its actual 30/36 GiB RAM limits
with `memory.swap.max=max`; the observer made no additional inference request.
The prepared native adapter separates lazy encoder loading from active image
computation, rather than excluding the entire image request from protection.
All six normal-profile launch paths now passed short functional checks and
actual limit readbacks. That does not supersede the failed sustained Maya
measurements; its active guard remains enabled and may stop longer requests.

## Separately approved host-policy trial

The user approved testing swappiness 10 instead of 60, with automatic restoration
and keeping 10 only after matched checks pass. Administrator authentication is
pending; no host VM setting has changed. Existing RAM/GPU/active-I/O guards remain.
The trial waits for current VM60 tests, preserves their results and records the
new host-policy configurations separately. Earlier long retrievals retain their
actual policy/date. See CURRENT-STATE.md and the private concrete proposal.

## Dense VRAM reserve update — October 28

The user explicitly lowered the dense GPU free-memory guard from 1,024 MiB to
512 MiB and authorized a visible-terminal TP2/MTP3 32K retest. The normal dense
supervisor and isolated retest share DENSE_GPU_FREE_MIB=512. Normal workers stop
after three low-headroom checks; isolated trials also require at least 512 MiB
at readiness. Swappiness stays 60; host reserve 8 GiB, worker RAM 30/36 GiB,
temperature 82°C, unlimited swap occupancy and active swap-churn guards are unchanged.
Earlier 1 GiB failures remain historical evidence under their original guard.
This approval does not promote the experimental fork or change the selected
engine settings. Future tests still run visibly and finish idle after cleanup.


## October 29: dense worker RAM caps removed

HyperQwen and SGLang no longer have the 30/36 GiB per-worker RAM caps.
Their normal guarded launches passed JSON and actual MemoryHigh/MemoryMax
infinity readbacks (cgroup memory.high/memory.max=max). Ownership enforcement,
host-available floor 2 GiB, dense free-VRAM floor 512 MiB, temperature 82 C,
active owned-worker swap/PSI/telemetry stops, swappiness 60, concurrency one and
idle unload 600 seconds remain. MoE worker RAM budgets are unchanged.
Forty-two CPU guard/ownership/budget/runtime checks passed; no dense speed or
context measurements were repeated.

GLM and both DeepSeek engines were tested with 512 MiB native VRAM allocation
reserves on the current reduced-RAM machine. Only profiles passing isolated
quality, near-window retrieval, sustained generation, fresh-process reload and
normal guarded loading were applied:

- deepseek-maya: 512 MiB candidate not applied; original 2,048 MiB reserve retained.
- glm-maya: 512 MiB reserve qualified and applied.
- deepseek-strata: 512 MiB reserve qualified and applied.

Native allocation reserves and the dense minimum-free-VRAM stop are different
controls. All model/cache/context choices were preserved, and prior benchmark
values remain historical evidence. Only applied candidates have new selected
measurements. The two early GLM/Strata connection failures occurred before engine
loading because the router cached the old dense-budget validator; corrected
trials supersede those setup failures. One idle router reload loaded the new
validator with no worker interrupted; DSH was preserved.

Final router idle, owned workers stopped and no GPU reservation; no fallback
restored. Next action: after explicit human DIMM-restoration confirmation, verify
Linux capacity, restore appropriate full-RAM cache values and verify guarded
loading. Preserve the separately approved dense cap removal, host reserve and
qualified VRAM selections unless the human revises them. No timer trigger.

See [qualification and current results](MOE-VRAM512-20261029.md) and
[numeric evidence](benchmark-results/20261029-moe-vram512.json).


## DeepSeek/Maya 512 MiB follow-up — October 29

Three additional DeepSeek/Maya 512 MiB candidates were rejected: disabled warming/prefetch,
256-token prompt chunks, and a native 12 GB copied/pinned expert cache. All hit the
unchanged owned-worker swap-write guard (7.23, 4.29 and 6.03 MiB/s over ~30 seconds;
write limit 1 MiB/s). Smaller chunks completed warm-up but failed during the first
measured response. No cgroup high/max/OOM event occurred; the engine's generic
OOM suggestion is not evidence of an OOM kill. File-cache/anonymous reclaim
competition is consistent with the observations; exact kernel victim selection
was not isolated.

Nothing was applied. DeepSeek/Maya retains 2,048 MiB reserve, 32K, original cache/
prefill settings and historical benchmark. GLM/Strata DeepSeek 512 MiB selections
and dense RAM-cap removal remain unchanged. No runtime, precision, worker budget,
swappiness 60, host 2 GiB, thermal/swap/PSI/telemetry guard, idle 600s or concurrency
change. Trial workers stopped, GPU reservation released, router idle and DSH
preserved; no fallback. No passing 512 MiB setup was found in these tested controls.
Full-RAM cache restoration still requires explicit human confirmation and Linux
capacity verification.

See [DeepSeek/Maya follow-up](MAYA-DS4-VRAM512-FOLLOWUP-20261029.md) and
[numeric evidence](benchmark-results/20261029-maya512-followup.json).


## DeepSeek/Maya demand-cache qualification — October 29

DeepSeek/Maya passed at **512 MiB native VRAM reserve and unchanged 32,768-token context** on the 45.55 GiB reduced-RAM host. The selected temporary configuration combines a 16 GiB model-file cache target with a native 12 decimal GB pinned hot-expert cache. JSON, arithmetic, image, 29,467-input-token retrieval, 426.5s continuous generation, a fresh isolated process reload and two normal guarded loads all passed. Observed worker swap occupancy and swap read/write rates were zero.

The saved three-request screen measured **1.23 decode tok/s**, 42.5 prefill tok/s and 51.491s TTFT. Earlier full-RAM/historical rates remain preserved; no fresh paired 2,048 MiB control was produced, because the earlier reduced-RAM configuration failed its swap guard.

This supersedes the earlier unresolved DeepSeek/Maya reduced-RAM status only for
this qualified configuration. Other five selected settings/results remain unchanged;
Flash/Strata's earlier reduced-RAM failure remains unresolved. Native warming limits
did not bound demand mmap residency; the new controller targets clean model-file
residency, with overshoot possible between scans. Its qualified binary is hash-pinned.

The host 2 GiB floor, 46/48 GiB MoE worker budget, dense 512 MiB free-VRAM stop,
82 C thermal limit, owned swap/PSI/telemetry guards, swappiness 60, concurrency one
and idle 600s remain. Original native source/binary and archived preimages remain;
weights, precision and mathematical kernels are unchanged. Router idle, owned
workers stopped, no GPU reservation, DSH preserved and no fallback.

After explicit human RAM-restoration confirmation, verify Linux capacity, restore
appropriate full-RAM cache/prefill choices from preimages while preserving the
qualified VRAM reserve and guards, then verify normal guarded load/reload.
No timer or MemAvailable trigger.

See [demand-cache qualification and six selected results](MAYA-DEMAND-CACHE-20261029.md)
and [numeric evidence](benchmark-results/20261029-maya-demand-cache.json).
