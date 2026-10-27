# Inference swap and memory-pressure policy

Loading and parked swap pages are allowed inside the existing worker limits.
NVIDIA workers retain their selected RAM soft/hard limits, **1 GiB swap occupancy
cap**, 8 GiB host-available floor, temperature guards and GPU placement/reserves.
No global swapoff, swappiness change or RAM-cap expansion is part of this policy.
The observed host swappiness is the Linux default 60; occupancy alone does not
measure active swap I/O.

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

49 CPU tests passed, including loading/parked swap, active rate windows, pressure,
missing counters, latching, explicit reload and GPU-lock containment. The router
has loaded the new wrapper ownership/reload code. Dense and MoE supervisors use
the new monitor on subsequent launches; the already-running GLM long-context
qualification received an owned-invocation observer without repeating its speed
tests. Final normal-launch verification remains part of the context rollout.

Saved measurements identify why this is needed: the failed Flash host-KV trials
reclaimed heavily at the 44 GiB soft limit with full bounded swap. Their evidence
is retained; no throughput is invented. Maya DeepSeek's current-control telemetry
also contains active swap-write windows above the new threshold, so bounded
warming/cache alternatives must qualify before a new setting is promoted.
GLM's ongoing long-input observation has parked swap near 1 GiB with zero measured
active swap writes and negligible full-memory pressure. Parked pages alone do not
invalidate it. Old reports retain their original guard policy and are not
retroactively labeled as fully monitored by the new implementation.
