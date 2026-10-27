# Current takeover state

Updated October 27, 2026, 18:16 EDT, during the context-expansion task. This document is the
current handoff; dated reports preserve history. Read it with the root README
and maintained registry. Do not reconstruct state from chat alone.

## Active task and approvals

Test larger contexts for all six maintained profiles; retain one setting per
model/weight quant/engine, preserve raw and historical results, deploy qualified
choices and update both NVIDIA repositories. Consult the saved lcz.me,
Level1Techs and Digital Spaceport source trail.

The user explicitly accepted GLM 64K and Strata DeepSeek 128K tradeoffs on
October 27. Their screens versus fresh controls were:

| Candidate | Prefill change | TTFT change | Decode change |
| --- | ---: | ---: | ---: |
| GLM 65,536 | +0.31% | -0.40% | -4.48% |
| Strata DeepSeek 131,072 | -5.31% | +5.95% | +4.92% |

These are one-request screens, not deployed full-window results. GLM64K subsequently
confirmed 65.5 prefill / 33.740 s TTFT / 4.809 decode across three requests, all
better than its fresh 32K control; its 58,986-input retrieval passed, alongside JSON/arithmetic/image checks. It is
qualified for deployment; StrataDeepSeek128K subsequently confirmed 33.3 / 65.796 s / 2.955 and passed
117,866-input three-marker retrieval plus JSON/arithmetic. Both are qualified. Confirmation,
JSON/arithmetic, vision where enabled, resource checks and near-window retrieval
remain required. The other four profiles retain the matched no-loss rule.

The user also requested current AGENTS/README/benchmark handoffs, an AMD/NVIDIA
gap audit followed by a choice before filling optional gaps, conservative active
inference swapping, and an unlock assessment using saved evidence only.

## Deployment and evidence

Production settings have not yet changed: HyperQwen 32,768; SGLang 16,384;
Flash Strata 32,768; GLM Maya 32,768; DeepSeek Strata 65,536; DeepSeek Maya 32,768.
Router and DSH remain active. Current qualified candidates include:

- HyperQwen 56,320, KV 704 MiB/rank, chunks 256: three-request median
  1,491.65 prefill / 1.4985 s TTFT / 89.10 decode; near-window retrieval passed.
- SGLang 21,504, chunks 384, original .88 pool: three-request median
  2,621.01 / .8521 s / 46.17; near-window retrieval passed.
- The larger SGLang .92/.93 pools with 512-token chunks crossed the retained
  1 GiB free-GPU floor during inference. Smaller-chunk combinations are pending.
- Flash host-KV trials with both GPU reserves raised to 1536 MiB hit reclaim
  pressure at the 44 GiB soft limit and full bounded swap. Both were stopped and
  preserved, without completed performance. A documented resident-budget variant
  is pending; weights, expert selection and INT8 KV remain unchanged.

Private raw evidence and executable coordinators are under
`data/context-expansion-20261027/`; its `HANDOFF.md` and JSON states contain local
details. Do not overwrite a result directory. Numeric samples and sanitized
progress are in [the context report](CONTEXT-EXPANSION-20261027.md).
Earlier numeric files have saved SHA-256 preservation checks.

## Exact work ownership and remaining steps

StrataDeepSeek128K completed at 18:02 EDT. The v2 queue's Maya 49,152 /
warm-cap 32 GB child also crossed the active-write threshold, preserved its
failure and restored the default. The waiting v3 coordinator then safely closed
the held v2 parent; neither old parent should be restarted.
`llm-context-policy-v3-queue.service` now runs Maya 65,536 / load cap 28 GB /
post-prompt read-ahead 2 GB. Pinned Maya source shows `DS4_WARM_GB` reads ahead
while decoding, independently of the load-time cap. V3 bounds/disables this
separate budget without weakening the swap guard. It preserves any qualified
fallback, then continues the existing Flash plan.
`llm-context-combined-queue.service` waits for final-queue completion, then tests
promising SGLang chunk/pool combinations. No competing GPU work is authorized.
The old `llm-context-final-queue.service` was stopped only after its active
HyperQwen child completed and restored the default. Do not restart it.

Workers are exclusively `llm-context-test-worker.service` for MoE trials and
`llm-test-qwen27b.service` for dense trials. Never kill broad Python/GPU process
sets. GPU-LOCK must be released only by its matching owner. Wait for both the
final-queue and post-queue completion records before promotion.

The swap-rate guard, 50 CPU tests and real CPU-only systemd readback are complete;
the user explicitly approved unlimited worker swap occupancy with active churn
protection. RAM/GPU limits are unchanged. The completed Strata trial retained its
original 1 GiB cap; subsequent launches use infinity and counters/pressure guards. The router has loaded its
ownership/latch handling, and GLM long retrieval was observed through completion. Normal
launch verification remains. The user selected operational gaps only: after context
rollout, implement guarded ten-minute idle unload, full lifecycle telemetry and
manual engine-candidate staging. Keep current model coverage. Keep the existing RAM,
active swap-I/O, GPU placement, quality, host-floor and thermal protections.
Loading/parked swap and active swap churn are different; do not set global
swapoff or change VM knobs blindly. Saved Maya telemetry contains active write
churn that needs cache tuning before it can qualify under the new guard.

Then review selections, prepare hash-verified old settings, apply only qualified
changes, refresh DSH context metadata, check normal deployment, restore default
HyperQwen, finish the grouped report/ledger, run appropriate CPU checks, export
reviewed files and push both repos. Do not repeat completed GPU tests to publish.
Private archive-export approval from the earlier task covered its six specific
files; do not assume approval for a different private-data export.

The initial-matrix checkpoint was pushed as private `6ddb09a` / public `c267927`.
These are dated checkpoint IDs, not a claim about current HEAD. Inspect Git
HEAD/upstream and private `publication-checkpoint.json` for the latest exact
publication state. Replace pending statements as each remaining step finishes.

Operational implementation checkpoint: guarded idle unload and lifecycle telemetry
pass the expanded 68-test CPU suite, but their access flags remain disabled.
The native idle adapter is prepared and has not been applied. Candidate source
staging/evidence review passes CPU tests and is available as a manual tool; no
candidate has been built, benchmarked or promoted by it. No timer or model was added.

Publication checkpoint: private `33a3aa0`, public `df7e053`, both clean and
synchronized when published. Subsequent refinements distinguish native unloaded
state, verify source staging uses an actual Git root, reload an idled selected
worker, and test the normal Maya monitor receives the cgroup path. These CPU
changes are not new GPU performance tests. Lifecycle sensor readback found both
GPUs and six board/CPU sensor devices, with private mode-600 output.

A CPU-only `llm-context-normal-launch-observer.service` records each recognized
normal dense/MoE invocation's cgroup RAM/swap readback. It makes no inference
requests; stop it via `stop-normal-launch-observer` after rollout verification.
Private `verify-normal-deployment.py` is prepared, not executed; it performs one
functional JSON request per normal profile and images where enabled, not a speed
benchmark. It requires both queue completion and applied promotion records.

The prepared native adapter now distinguishes lazy encoder startup from active
image encoding, including exception cleanup. Both loading and active image work
defer model switching. It remains unapplied; CPU tests pass, and normal real
image/idle/reload verification still follows rollout. Native preview v3 captures
exact before/after hashes. Normal Hyper restore independently confirmed the
30/36 GiB RAM limits and kernel swap maximum `max`.
