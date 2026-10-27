# Current takeover state

Updated October 27, 2026, 19:23 EDT. Read this with README.md and AGENTS.md.
The private raw task directory is `data/context-expansion-20261027/`; its
HANDOFF.md, ROLLOUT-CHECKLIST.md, immutable trial folders and JSON states provide
local details. Recover results before running anything. Do not repeat completed
measurements or launch competing GPU work.

## Scope, approvals and deployed state

Assess larger contexts for all six maintained model/quant/engine profiles, retain
one qualified setting per group, preserve history and update both NVIDIA repos.
Use the saved lcz.me/Level1Techs/Digital Spaceport trail. No new models, engine
binaries, drivers, firmware, clocks, fan settings or unlock benchmarks.

The user accepted GLM 65,536 and Strata DeepSeek 131,072 tradeoffs. They also
approved guarded 600-second idle unload, lifecycle telemetry and manual candidate
staging after context rollout. Model coverage and recurring schedules stay unchanged.

The user approved unlimited worker swap occupancy with active churn protection.
All six guarded launch paths now request infinity; RAM/GPU limits remain. A real
CPU scope and normal HyperQwen restore read back kernel swap `max`; the latter
kept its 30/36 GiB RAM bounds. Active guard thresholds remain 1 MiB/s writes or
8 MiB/s combined over a continuous 30-second active window, plus pressure and
telemetry guards. Failed Maya trials demonstrate owned-only stops. Loading and
parked pages alone are allowed. No global swapoff or swap-file growth.

The user separately approved a bounded swappiness 60-to-10 trial, automatic
restoration, and keeping 10 only if matched checks pass. **It has not started:
administrator authentication is pending and the host still reads 60.** The
approved proposal and answer are saved privately. Do not infer permission from
the old six-file archive approval for a different archive export.

Production context settings have not been promoted: HyperQwen 32,768; SGLang
16,384; Flash Strata 32,768; GLM Maya 32,768; DeepSeek Strata 65,536; DeepSeek
Maya 32,768. The new policy's active guard rejects the tested Maya cache settings;
normal Maya compatibility is not yet qualified. Router/DSH stay running.

## Qualified candidates and failures

- HyperQwen 56,320, KV 704 MiB/rank, chunks 256: median 1,491.65 prefill /
  1.4985 s TTFT / 89.10 decode; three requests and near-window retrieval passed.
- SGLang 32,768, chunks 384, .92 static pool: 2,613.82 / .8532 s / 46.59;
  three matched requests and near-window retrieval passed. The larger 36,864
  candidate failed the GPU-headroom guard; its partial request is not throughput.
- GLM 65,536: 65.5 / 33.740 s / 4.809, all better than its fresh 32K control;
  JSON/arithmetic/image and 58,986-input retrieval passed.
- Strata DeepSeek 131,072: 33.3 / 65.796 s / 2.955; JSON/arithmetic and
  117,866-input retrieval passed. Versus fresh 64K: prefill -1.77%, TTFT +1.86%,
  decode +5.44%, within the user's accepted tradeoff. Long retrieval TTFT was
  1,722.88 s; this is additional work, not comparable to the 2.2K speed fixture.
- Flash's initial host-KV/reserve trials hit reclaim pressure with the old 1 GiB
  cap. All four new-policy full-arena/resident-budget screens are complete and
  missed the speed rule. Retain 32,768 pending the separately approved VM10 check.
- Maya smaller load caches, bounded/disabled post-prompt read-ahead and bounded/
  disabled Engram row caches still crossed active-write limits. A first passing
  request or zero-I/O window was followed by failure and is not qualification.
  Smaller-cache records show below-37-GiB samples and no recorded soft-limit
  crossings. Ancestors have no tighter limits. Most RAM is file cache; only
  about 182 MB of the unloaded dense checkpoint was resident in the measured
  snapshot. No cache eviction or ancestor protection change was applied.

## Exact live pipeline

Old v1-v4 parents were stopped only after their children finished and restored
normal state. Do not restart them. The independent VM60 tail and combined
SGLang queue have both completed successfully; final-queue-complete.json and
post-queue-complete.json are saved privately. Their tests must not be repeated.
Maya remains unresolved; promotion refuses a known-churning setting as newly
policy-qualified.

The administrator-gated launcher is pending in the local exec session. Once
Ubuntu authenticates it, it first tests failure/restoration on a root-owned fake
value without modifying real VM settings. It then creates two bounded system
services: `llm-swappiness10-context-trial.service` and
`llm-swappiness10-five-checks.service`. Their coordinators/engines run as the normal
user. The first waits for the independent VM60 tail and SGLang to finish before
setting 10 and testing a new Maya64 candidate. Its privileged stop hook restores
60 and preserves other admin changes. If Maya qualifies, the second rechecks the
other five selected configurations under 10 against those identical settings'
saved VM60 medians (not an earlier smaller-context allowance), restores 60, and only conditionally
persists 10 after all stated checks pass. No existing result is overwritten.
Prior long retrievals keep their original policy/date; they are not relabeled.
The pending authentication request was replaced after correcting newline escaping
in the conditional sysctl-file writer. Generated persistence code compiles and
its sysctl text was checked for proper newlines without changing the host.

Private worker units are `llm-context-test-worker.service` and the dense
`llm-test-qwen27b.service`. GPU-LOCK is removed only by its matching owner.
A read-only `llm-context-normal-launch-observer.service` saves actual normal
invocation RAM/swap readbacks; stop it after verification with the private flag.

## Operational drafts and next actions

70 CPU tests pass. Idle unload, bounded private lifecycle logs and manual source
staging/evidence review are implemented. **Idle/logging flags remain disabled;
the native adapter is prepared but unapplied.** It distinguishes encoder loading
from image computation, preserves native FIFO/GPU reservations, and defers both
switching and manual unload during native busy/loading/compute. Lifecycle sensors
read both GPUs and six board/CPU devices; owned memory/I/O counters support write
attribution. No candidate engine was built or promoted by the staging tool.

The serial VM60 queues are complete. Wait for administrator authentication and
the approved host-policy experiment. Review all six
choices and actual qualification/policy attribution. Then prepare hash-verified
preimages, apply qualified contexts under an owned reservation, refresh DSH
metadata, deploy the approved operational features, run normal JSON/image and
real idle/reload checks, restore HyperQwen, and finish grouped tables/ledger.
The private rollout checklist and prepared scripts describe these steps. Preserve
all historical numeric hashes. Archive only reviewed retired source/settings;
exclude chats, credentials, runtime distributions, weights and raw logs.

Publish reviewed exports with nonpersonal commits, preserve concurrent changes,
verify both branches clean/upstream 0/0, and update publication-checkpoint.json.
Inspect actual Git heads rather than treating a dated checkpoint ID as current.
