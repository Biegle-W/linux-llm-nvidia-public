# Current takeover state

**Superseding direction relayed by the continuation:** continue without lowering
swappiness. Keep 60; do not launch the prepared VM10 experiment. The earlier
VM10 approval is superseded. At final transfer no authentication request or
VM10 launcher remained pending; workers and evidence were preserved. The
continuation owns further work.

Updated October 27, 2026, 19:59 EDT. Read this with README.md and AGENTS.md.
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

The latest user instruction supersedes the earlier swappiness10 trial approval.
Keep host swappiness at 60. The administrator request was dismissed before any
experiment ran; no VM10 units or pending authentication remain. The saved VM10
launcher now refuses execution when the new user-direction record is present.

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
  missed the speed rule. Retain 32,768; the previously proposed VM10 check is cancelled.
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

The VM10 experiment is cancelled by the latest user direction. Its prepared
scripts remain historical local preparation only. Do not execute them. Continue
qualification at swappiness60, preserving all completed VM60 evidence.

A new owned continuation screen tests DeepSeek Maya64 with DS4_AHEAD=0,
DS4_WARM_CAP_GB=24, DS4_WARM_GB=0 and DS4_ENGRAM_CACHE_MB=0. This disables
speculative expert prefetch via an existing engine setting; all numerical and
resource guards remain. Coordinator: llm-context-vm60-continuation.service.
Evidence: vm60-deepseek-maya-65536-ahead0-warm24-engram0-screen. Do not duplicate.

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

The serial VM60 queues are complete. The continuation owns remaining qualification at swappiness60; the
host-policy experiment is cancelled. Review all six
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

## Final transfer to continuation — 19:59 EDT

The continuation thread requested takeover. This thread will initiate no further
work. No global VM setting was changed and no VM10 experiment started.
Administrator authentication was dismissed (exit126); no pending pkexec remains.
Both system VM10 units are inactive/dead. Both VM60 coordinators are
inactive/dead with success; their completed tests must not be repeated.

The read-only normal-launch observer remains active and was preserved. Normal
HyperQwen worker, model router and DSH remain active; normal MoE and private MoE
test worker are inactive. GPU-LOCK is absent. No running job was stopped.

Private raw evidence and prepared scripts remain in the task data directory.
The latest published checkpoints are private fe4c571 and public0a84537, with
88 exports verified equal and both branches clean/upstream0/0 before this final
handoff edit. This handoff edit is intentionally left for the continuation to
review, commit and sync with its next publication; no competing Git writes or
new benchmarks will be initiated here.

## Continuation direction — swappiness remains 60

The user superseded the earlier VM10 approval. Do not launch the prepared VM10
experiment or persist 10. The authentication was already dismissed; the launcher
now refuses execution when the saved new direction is present. Continue Maya
qualification and deployment at 60. Completed VM60 results remain preserved.
Continuation owner: thread 01a17f96-2727-7da1-aab6-f334dedd785c.

## VM60 continuation checkpoint

Latest instruction: keep host swappiness60; prior VM10 approval is superseded.
The new Maya64 screen with speculative expert lookahead disabled completed its
measured request without a guard stop: 44.7 prefill tok/s, 49.1786 s TTFT,
3.80265 decode tok/s. Its matched Maya32 control is 41.5 / 52.9631 / 2.48181.
This is one screen, not a qualified promotion. Confirmation is queued in
llm-context-vm60-confirmation.service after screen cleanup; it runs three
requests then JSON/arithmetic/image/near-window retrieval only if speeds pass.
Evidence variant: vm60-deepseek-maya-65536-ahead0-warm24-engram0-confirmed.
70 CPU checks passed. Production settings and operational flags remain unchanged.
