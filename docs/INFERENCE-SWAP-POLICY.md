# Inference swap and memory-pressure policy

The user explicitly approved unlimited worker swap occupancy with active churn
protection on October 27. Loading and parked pages are allowed; normal workers
use `MemorySwapMax=infinity`, whose kernel readback is `memory.swap.max=max`.
The host swap file is not enlarged. Selected RAM soft/hard limits, the 8 GiB
host-available floor, temperature guards and GPU placement/reserves remain.
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
