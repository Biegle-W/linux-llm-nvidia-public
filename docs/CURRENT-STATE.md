# Current takeover state

Updated October 28, 2026, after the heterogeneous TP2/MTP study. Read README.md and AGENTS.md first.

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

## Standing follow-up: unlock persistence

The user requires future agents to automatically check GPU unlock persistence
after any authorized kernel or NVIDIA driver update, and on resuming with changed
versions. Follow UNLOCK-SETUP-20261026.md's required update checks. Verify DKMS and
the target boot image before reboot; verify both per-card unlock results and
NVIDIA availability after the user's reboot. Record versions and evidence, and
leave post-boot status pending until actually verified. No update, reboot, new
unlock benchmark or unlock-source change is authorized by this reminder.

## Automatic unlock health checks — installed and verified

The user explicitly requested OS checks independent of agent memory. Ten fixed
root-owned files are installed: the checker/status/queue helpers, pinned GPU
identity configuration, boot/update services, dpkg/boot-image watcher, APT/kernel
post-install queue hooks and MOTD status. Boot service and watcher are enabled;
the watcher is active on dpkg status and /boot. The checker executes its installed
copy, never user-writable project code. It only verifies; it does not change the
unlock, drivers, swappiness, firmware or reboot the host.

`gpu-unlock-health status --brief` reports VERIFIED. Initial boot and update-hook
checks passed for kernel 7.0.0-38-generic and NVIDIA 595.99.02: exact-target DKMS,
all five firmware assets, module and early-loader in the image, generated GRUB,
both successful unlocks before NVIDIA initialization, and both cards available.
All installed hashes, root ownership/modes and unit states were checked. 103 CPU
tests pass. Hook shell/APT syntax and systemd unit verification passed.

The initial service sandbox hid kernel module files, producing a false DKMS
failure. Module files are now readable but read-only, with CAP_SYS_MODULE and
module-loading syscalls denied. Corrected live audits pass; old failure evidence
and both bundles remain under data/gpu-unlock-health-20261027/. Three superseded
source/settings snapshots are archived privately at ac7474a with hashes verified.

Authoritative status is root-written /var/lib/gpu-unlock-health/{boot,update,latest}.json;
failed units expose failures, and supported MOTD logins show a brief result.
Package transactions are allowed to finish; checks queue asynchronously and wait
for settled package state. Changed software awaiting boot stays pending, not
verified. A new successful boot resolves stale old-boot status. No real package
update or reboot was performed for installation; future actual events must save
fresh evidence automatically. See GPU-UNLOCK-HEALTH.md. Preserve these OS hooks.

## SGLang tuning study — October 27, 23:15 EDT

The user approved isolated pipeline split and BF16 recurrent-state tests, not
W4A8 patches or a heterogeneous-TP fork. Fresh 32/32 FP32 control measured
46.4499 decode tok/s. 34/30 briefly measured 46.648 on one request, then the
GPU-headroom guard stopped it (sampled 975 MiB free on the 3080 Ti); this is not
a qualified three-request median. 36/28 failed the immediate post-load 1 GiB
headroom check (sampled 665 MiB on the Ti). BF16 on 32/32 measured 46.8734
decode (+0.91%), with prefill 2656.12 versus 2672.75 and TTFT .8374 versus .8320.
Both complete trials passed JSON, arithmetic and 29,434-input three-marker
retrieval. Retain 32/32 FP32; no candidate was promoted. Host swappiness is 60,
all guards remain intact, and no engine/checkpoint/driver/hardware changes occurred.

Raw plans, candidate catalogs, requests, logs and telemetry are private under
data/sglang-tuning-20261027/. The trial coordinator finished and restored the
HyperQwen default through the normal router; GPU-LOCK was released. See
[SGLANG-TUNING-20261027.md](SGLANG-TUNING-20261027.md) and the corresponding
numeric results. Earlier measurements and source settings are preserved.

## Isolated SGLang W4A8 — October 27, 23:48 EDT

The user explicitly approved the isolated MLP-only patch test. One RAM stick is
temporarily removed: Linux reports 45.55 GiB usable. SATA weights were mounted
through the normal UUID-checked preflight after reboot. Both GPUs are available
and automatic GPU-unlock health reports VERIFIED. No MoE test was run.

A copied installed SGLang package preserved its embedding/placement fixes.
The community AutoRound adapter did not match the checkpoint serialization
(compressed-tensors); its zero-activation audit rejected that candidate before
benchmarking. The corrected adapter targets only compressed-tensors decoder MLP
gate/up and down projections. All 128 expected projections were audited on both
GPUs. Eighteen standalone kernel cases passed on both SM86 GPUs. JSON, arithmetic
and 29,434-input three-marker retrieval passed for the final control and candidate.

Final matched medians: W4A16 2659.91 prefill / .83394 s TTFT / 46.3513 decode;
MLP W4A8 3233.72 / .687705 / 45.6912. Prefill +21.57%, TTFT -17.54%, decode -1.42%.
No candidate was promoted. Production SGLang remains W4A16, 32/32 PP2, FP32
recurrent state, 32K context. HyperQwen is restored as default; GPU-LOCK is
released and the coordinator has finished. Swappiness60 and all existing guards
remain. Normal engine binaries, checkpoint metadata and weights are unchanged.

Evidence is private under data/sglang-w4a8-20261027/ (initial and v2 studies,
source/patch manifests, compiler cache, raw requests and guard telemetry). The
reproducible experimental patch and sanitized results are linked in
[SGLANG-W4A8-20261027.md](SGLANG-W4A8-20261027.md). Initial cold isolated compilation
took about four minutes; loading/compilation are excluded from inference timing.
Do not repeat completed measurements or enable the candidate in production
without a separately reviewed selection. Reduced-RAM MoE capacity is unqualified.

## Heterogeneous TP2/MTP — October 28

The user accepted the W4A8 tradeoff and requested this isolated study. The
pinned htsglang 62271fd fork runs from a private candidate copy and a separate
Torch2.11/cu130 native environment. Its reproducible patch and all evidence are
in [SGLANG-HETERO-MTP-20261028.md](SGLANG-HETERO-MTP-20261028.md). Normal SGLang
remains W4A16 PP2/FP32/32K; HyperQwen remains the default. No fork promotion.

The 32K TP2 BF16/one-slot control qualified at 64.18 decode tok/s (+40.46% versus
accepted PP2 W4A8) but prefill fell 46.92%. At 16K, the matched control reached
63.87; corrected MTP1 reached 70.25 (+10.00%) and MTP3 84.63 (+32.51%).
Both corrected 16K MTP candidates passed JSON, arithmetic and near-window
three-marker retrieval with all 256 decoder rank/projection audits, both draft
weight-completeness audits, GPU-only placement and shared packed vocab modules.
MTP1 at 32K measured 69.59 on short prompts but failed the unchanged headroom
guard during retrieval at 990 MiB free. It is not qualified at 32K.

The fork required packed INT8 embedding/text-only adaptations, packed vocab
module sharing, cyclic discarded-vocab collection, verification-mask sizing and
quant-aware MTP fusion loading. The first 16K MTP1 run used an uninitialized
fusion projection because the fork skipped packed mtp.fc weights: its zero-
acceptance speed is invalid diagnostic evidence. MTP3 was interrupted on discovery.
The corrected loader rejects any missing required draft parameter before timing.
Three focused candidate regressions pass. The metric reader selects one TP
replica after the final PP stage; seven CPU regressions pass. This fixes duplicate
native counters/durations; historical results remain unchanged.

Raw evidence: data/sglang-hetero-mtp-20261027/; the study crossed midnight.
Eighteen standalone W4A8 kernel cases and eight bit-exact packed-shard checks
passed. Kernel math and maintained runtime/checkpoint files are unchanged by the
heterogeneous patch. Preserve swappiness60, all resource guards and the automatic
unlock checker. Reduced-RAM MoE capacity is still unqualified. Do not repeat these
completed variants or mistake a 16K candidate for a qualified 32K replacement.

Corrected MTP3 at 32K failed the immediate post-load GPU-free check: 904 MiB
on the 3080 Ti and 1,039 MiB on the 3080. No throughput was accepted for it.
The completed 16K retrieval checks used 14,686 input tokens.

Final restoration verified October 28 at 00:39 EDT: router selects HyperQwen,
not busy/loading, normal supervise_dense.py hyperqwen worker active, all isolated
coordinators finished and GPU-LOCK released. Swappiness is 60; OS unlock health
is VERIFIED. Private final-restoration-health.json records the check.

## Latest user direction: visible terminals

The user objected to repeated automatic restoration of HyperQwen. Future tests
must finish idle after owned-worker cleanup unless a final backend is explicitly
requested. Do not change the catalog/default model to infer a different selection.

Backend, router and DSH live consoles are now opened with visible_terminal.py.
Dense bounded starts, router MoE starts, router startup and DSH web startup open
visible consoles; foreground test coordinators must use the documented `run`
wrapper. All resource guards remain intact. The existing HyperQwen worker was
made visible without restarting or rebenchmarking it. The preceding public push was rejected by platform automatic review. This was
not a user-requested approval policy. The user has now expressly reaffirmed
that both repositories and Markdown files must always be kept updated; reviewed,
sanitized reports, handoffs and experimental patches remain within that standing
publication direction. Do not ask for redundant routine publication approval.

Visible foreground verification passed 19 router tests. The router was reloaded
without restarting the inference worker or changing its selection. Console GUI
processes launch in separate user services, outside inference resource cgroups.
Evidence is private under data/visible-backends-20261028/. No new GPU benchmark
was run. Swappiness remains 60.

## Repository publication clarification — October 28

The user did not request a separate publication approval step. Continue routine
sanitized synchronization and pushes under the standing instruction. An external
automatic-review rejection must be identified as such, without inventing a user
policy or bypassing the tool restriction. The pending public commits are being
published using this newly explicit clarification; final synchronization evidence
is recorded privately in data/repository-sync-20261028/.
