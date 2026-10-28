# Current takeover state

Updated October 27, 2026, 20:49 EDT. Read README.md and AGENTS.md first.

## Standing direction

Keep host swappiness at 60. The user superseded the earlier VM10 approval; that
experiment never ran and administrator authentication was dismissed. The private
VM10 launcher refuses execution when the saved new direction exists. Do not
launch it or persist 10. Unlimited worker swap occupancy and the existing active
churn, RAM/GPU/headroom/temperature safeguards remain. No swap-file growth,
swapoff, driver, engine binary, hardware, firmware, clocks or fan changes occurred.

Scope remains six profiles. AMD repos are read-only reference. No model expansion
or recurring updater was selected. Preserve all completed evidence; do not repeat
benchmarks. The old thread handed off and will not initiate work.

## Deployed settings and unresolved Maya

Four independently qualified upgrades are deployed: HyperQwen 56,320 (50,627-input
retrieval); SGLang 32,768 (.92 pool/chunk 384; 29,434-input retrieval); GLM 65,536
(58,986-input retrieval); Strata DeepSeek 131,072 (117,866-input retrieval). Flash
remains 32,768. Exact dated medians, source variants and actual legacy/new swap
policy attribution are preserved in the registry and context report. The user's
Strata tradeoff approval remains; GLM confirmation improved all speed metrics
against its fresh control. No earlier result was relabeled under a new policy.

Maya DeepSeek remains 32,768 with its prior speed/retrieval evidence and is **not
newly qualified for sustained inference under the active swap guard**. Cache
and lookahead-off trials crossed active-write limits. The new 64K lookahead-off
screen passed once, but its separate confirmation stopped at 7.68287 MiB/s over
30.42 seconds. It was not promoted. final-selection.json retains needs-safe-cache;
partial promotion explicitly excludes Maya and preserves its production settings
and historical benchmark fields. Longer requests may stop at the unchanged guard.
Short JSON/image success does not resolve this limitation.

## Operational controls and verified behavior

Hash-reviewed Maya and Strata idle adapters are applied. Before/after source and
hashes remain in idle-applied/<family>. Router idle_timeout_s=600 and bounded
private lifecycle_telemetry=true are enabled. DSH context metadata was refreshed,
preserving other settings. Manual source staging/evidence review is available;
no candidate engine was built or activated. Desktop shortcuts are unchanged.

All six normal guarded launch paths passed JSON, supported images, catalog
contexts and actual RAM/swap readbacks. Lifecycle coverage recorded both GPUs,
six hwmon devices and owned cgroup counters in mode 600 logs. Peak GPU temperature
in those functional checks was 55 C, not a sustained thermal/power benchmark.

Actual GLM 600-second expiry was observed at 610.44s: GPU use 17,995 to 660 MiB;
old engine PID exited while frontend/supervisor survived; owned memory 44.80 to
0.48 GiB. A fresh blue image with different bytes/dimensions reloaded successfully.
Lifecycle logs recorded unloaded. Strata's isolated 30-second timeout released at
35.33s, GPU use 21,078 to 669 MiB with frontend alive, then fresh blue-image reload
passed. Production Strata remains 600; this is not a real 600-second Strata test.

Dense actual 600-second expiry was observed at 610.53s, GPU use 18,218 to 666 MiB.
Its immediate reload exposed a false missing-telemetry latch during intentional
SIGTERM. Both supervisors now stop telemetry polling on intentional shutdown;
unexpected telemetry loss still fails closed. Four new regression cases plus the
full 74-test CPU suite passed. A real normal stop then API auto-reload passed with
no latch and HyperQwen restored. The original 600-second expiry evidence and
initial failure remain intact; the timer was not repeated after the shutdown fix.

## Live ownership and evidence

No benchmark, functional verifier or idle-test coordinator remains active.
HyperQwen is restored as default with its intended ten-minute idle release;
router and DSH remain running/enabled. GPU-LOCK is absent. Private test workers
are stopped. The read-only normal-launch observer was told to exit with its
private stop flag. Do not stop unrelated applications or remove foreign locks.

Private evidence: data/context-expansion-20261027/. Key folders are promotion/,
normal-deployment-verification/, idle-deployment-verification/ (including the
initial failure and shutdown-fix/ proof), idle-applied/ and immutable trial
folders. publication-checkpoint.json records verified actual heads. Live host-side
reads are authoritative; sandbox snapshots may lag systemd-owned writes.

The remaining technical limitation is Maya sustained-swap qualification. Further
work must preserve swappiness 60 and active guards, avoid repeating failed settings,
and use exact source/candidate evidence before considering any engine change.

## Publication and retirement

The 12-file context/lifecycle batch is private archive commit 15e6f2e. Two immediate
supervisor preimages are in a separate append-only batch, archive commit 0840f24.
All committed snapshot hashes match. DSH chats/settings, keys, weights, runtime
distributions and raw logs are excluded. Historical numeric hashes are unchanged.

Review/sync 89 allowlisted exports, README-title difference only, key excluded.
Update both NVIDIA repos with nonpersonal commits, no force pushes, verify clean
upstream 0/0 and record actual heads in publication-checkpoint.json. Final verified
heads and cleanliness are recorded privately in publication-checkpoint.json;
inspect actual Git state before further work.
