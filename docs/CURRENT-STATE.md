# Current takeover state

Updated October 27, 2026, 20:12 EDT. Read README.md and AGENTS.md first.

## Direction and ownership

The continuation owns remaining work. The earlier thread has handed off and will
initiate no new jobs. The user explicitly superseded the earlier VM10 approval:
**keep host swappiness at 60**. No VM10 experiment ran; administrator authentication
was dismissed. The saved private VM10 launcher refuses execution when the new
direction record exists. Do not launch it or persist 10. Unlimited worker swap
occupancy and all active churn, RAM/GPU/temperature guards remain unchanged.

Scope remains six profiles, no new models, engine binaries, drivers, hardware,
firmware, clocks, fan settings or recurring schedules. AMD repositories remain
read-only reference. Preserve numerical history and do not repeat completed tests.

## Deployed contexts and outstanding Maya limitation

Four independently qualified upgrades are applied: HyperQwen 56,320 (50,627-input
retrieval); SGLang 32,768 (.92 pool/chunk 384; 29,434-input retrieval); GLM 65,536
(58,986-input retrieval); Strata DeepSeek 131,072 (117,866-input retrieval).
The user accepted the Strata speed/capacity tradeoff; GLM confirmation improved
all three speed metrics against its fresh control. Flash remains 32,768 because
larger candidates missed selection rules. Exact three-request medians, source
variants and actual legacy/new swap-policy attribution are in the registry and
CONTEXT-EXPANSION-20261027.md. Prior long checks retain their actual policy/date.

Maya DeepSeek remains 32,768 with its previous speed/retrieval evidence; it is
**not newly qualified for sustained inference under the active swap guard**.
The new Maya64 DS4_AHEAD=0/warmcap24/postwarm0/engram0 screen passed once at
44.7 prefill/49.1786s TTFT/3.80265 decode, but the separate confirmation stopped
at 7.68287 MiB/s writes over 30.42 s. Its failure is preserved, not promoted. Do not
relax guards or relabel short API success as resolving this limitation.
The final-selection.json attention state remains needs-safe-cache. Explicit
partial promotion in promotion/manifest-private.json excludes Maya; its existing
production setting and historical benchmark fields were preserved.

## Operational deployment and live jobs

The hash-reviewed native idle adapters are now applied to Maya and Strata.
Before/after source and hashes are in idle-applied/<family>. Private router
idle_timeout_s=600 and lifecycle_telemetry=true are enabled. DSH web/headless
context metadata is refreshed, preserving other settings. The router and DSH
were restarted only while idle under an owned GPU reservation. Production RAM
and GPU limits were not increased; all guarded launch paths request swap max.
Manual candidate staging remains manual, with no engine built or activated.

The normal functional verifier completed all six profiles successfully.
It serially selects Flash, Strata DeepSeek, Maya DeepSeek, SGLang, HyperQwen and
GLM, checking actual cgroup RAM/swap readbacks, catalog contexts, JSON and supported
images. Evidence: data/context-expansion-20261027/normal-deployment-verification/.
It left GLM selected. llm-context-idle-verification.service now runs actual idle
and reload proof: GLM 600 seconds, isolated Strata 30 seconds with production 600,
and dense 600 seconds, then HyperQwen restore. Do not duplicate GPU work.
Inspect its live host-side state; sandbox snapshots can lag systemd-owned writes.

The new screen and confirmation coordinators finished and restored the default
before deployment. All older VM60 queues completed; do not restart them. The
read-only llm-context-normal-launch-observer.service remains active until final
verification. GPU-LOCK is removed only by its matching owner. Private test worker:
llm-context-test-worker.service; normal dense: llm-test-qwen27b.service; normal
MoE: llm-router-worker.service. No coordinator should bypass a guard stop.

## Next actions

Finish normal functional verification, retaining Maya's sustained-swap limitation
regardless of short-request success. Prove real GLM 600-second idle/vision release
and fresh-image reload; verify Strata native idle/reload using an isolated short
timeout under the outer owned GPU reservation, then dense actual 600-second expiry
and normal API reload. Restore HyperQwen as default. Record bounded lifecycle
sensors and ownership/readbacks; stop the read-only observer afterward.

Reports currently describe a partial deployment with unresolved Maya, not a
completed six-profile safety qualification. Update README/entry points and the
ledger, preserve the historical numeric hash manifest, and archive only reviewed
retired source/settings with hashes. Exclude DSH chats/settings, keys, weights,
runtime distributions and raw logs. Prepare/review exact export before publishing.

70 CPU checks passed in the continuation. The preceding policy checkpoint was
published to private ed83869 and public 7ec565e, with 88 sanitized exports verified
identical (README title excepted) and the key absent. GitHub verified signed-in
Biegle-W owns the private repo with admin access; a review concern about ownership
was resolved before pushing. The current deployment changes are not published
yet. Inspect actual Git heads and update publication-checkpoint.json after final
sync; preserve concurrent changes and never force-push.

Normal lifecycle coverage passed for all six profiles: both GPUs, six hwmon
devices and owned cgroup counters were present, with owner-only logs. Peak GPU
temperature during these functional checks was 55 C; this is not a sustained
thermal benchmark or a power-saving measurement. The 12-file retirement batch
was published to the verified private archive at 15e6f2e; committed hashes match.
