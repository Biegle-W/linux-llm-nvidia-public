# Current takeover state

## Latest: completed terminals close automatically — October 29

Harness and selector windows now close when the command finishes, including failures. Private transcripts and atomic exit-code receipts retain the results. Service viewers close after their own service stops; active work, router/DSH service processes, unknown state and unrelated terminals are preserved. Minimized/no-focus startup remains. All 207 CPU regressions and real PTY success/failure/service-stop checks passed; final project terminal inventory was zero. No model or guard setting changed and no GPU benchmark was repeated. See [terminal lifetime](TERMINAL-LIFETIME-20261029.md) and [verification](validation-results/20261029-terminal-lifetime.json).


## Latest: targeted 15% pressure guard and two-profile 64GB benchmark — October 29

Qwen/Strata and DeepSeek/Maya now use 15% full-memory-pressure thresholds, up from 10%, with the same 30-second active window and three-sample stop rule. All other profiles retain 10%. The 128/160 MiB/s SSD swap limits and every independent RAM/VRAM/thermal/telemetry guard remain unchanged, as do contexts, weights, precision, runtime pins, expert caches, swappiness 60, concurrency 1 and idle 600 seconds. Both profiles completed a warmup and three valid 128-output measured requests without a guard violation. Only Qwen/Strata and DeepSeek/Maya were repeated; HyperQwen, SGLang, GLM/Maya and DeepSeek/Strata rows are explicitly carried forward from their earlier October 29 records. This composite table is not a new six-profile matched run. See [report](BENCHMARK-PRESSURE-GUARD-64GB-20261029.md) and [numeric evidence](benchmark-results/20261029-pressure-guard.json). Workers are stopped; router idle; no GPU lock; DSH preserved; no fallback.


The earlier 10% stop records remain archived. Explicit model selection cleared the old invocation latches; neither profile has a new guard latch. Peak inference pressure was 0% for Qwen and 6.80% for Maya; the added allowance was not exercised in these short runs.

## Latest: four SSD profiles use 128/160 swap limits — October 29

Four SSD-streaming profiles now use bounded swap limits of 128 MiB/s writes and 160 MiB/s combined over 30 seconds. Dense and unknown profiles retain 1/8 MiB/s. All other resource guards, contexts, expert-cache settings, precision choices, runtime pins and model settings are unchanged. 2 of four SSD profiles completed three valid measured requests without guard violations on restored 64GB RAM. RAM remains DDR5-4200 MT/s across four 16GB DIMMs (61.3013GiB usable; 2100MHz DDR clock). The dense profiles were not repeated; their table rows carry forward the earlier October 29 full-RAM run. deepseek-maya did not pass: Sustained full-memory pressure during inference. Qwen reached three outputs but stopped on the unchanged pressure guard; its timings are diagnostic and no new passing median is selected. See [the new report](BENCHMARK-SSD-SWAP-64GB-20261029.md) and [numeric evidence](benchmark-results/20261029-ssd-relaxed-swap.json). The earlier DeepSeek/Maya guard failure and all prior measurements remain dated evidence; this speed screen does not repeat full-window quality qualification.


Workers are stopped; router idle; no GPU reservation; DSH preserved. Both pressure-stop latches are retained. No fallback was loaded. No benchmark work remains pending.

## Latest: all six current profiles benchmarked on 64GB — October 29

Firmware configured RAM speed is DDR5-4200 MT/s across four 16GB DIMMs
(equivalent DDR clock2100MHz); Linux sees61.3013GiB usable. No clock/BIOS change.
Five selected model/engine profiles completed one warmup and three valid
128-output fixed-fixture requests with current full-RAM caches and unchanged
guards. Fresh medians and ranges are in [the report](docs/BENCHMARK-64GB-20261029.md)
and [numeric evidence](docs/benchmark-results/20261029-full-ram.json); the registry
now points to five measured results and retains prior entries in history. DeepSeek/Maya failed its first measured request at5.31MiB/s swap writes above1MiB/s; no new speed median or pass is claimed. Its guard remains latched and source settings unchanged.
These approximately2.2K-input screens exclude model loading; they do not replace
full-window quality or long-duration qualification. Prior configurations/runs are
not paired controls for a RAM-only causal comparison. Source readiness/cleanup
corrections do not change model/runtime settings or the fixed measured fixtures.

## Latest: 64GB RAM restored — October 29

The owner confirmed hardware restoration. Linux sees 61.3013 GiB usable.
Saved full-RAM cache choices are restored: GLM 40 GiB, Strata DeepSeek 42 decimal
GB and Maya DeepSeek 8 GB warming with original mapped-expert mode. The newer
Maya binary/hash guard remains; its temporary 16 GiB file-cache target is inactive.
Qwen mapped experts/both GPUs and its separate 128/160 MiB/s swap allowance,
512 MiB native reserves, 2 GiB host floor, all independent guards, swappiness60,
concurrency one and idle600 remain unchanged. All six normal guarded startup/JSON
paths passed; the three cache restorations passed fresh reloads. No speed,
near-window, image or sustained benchmark was repeated. Older reduced-RAM
measurements retain their hardware/cache scope and are not current speed claims.
The daily 03:00 Toronto timer is resumed; next October30 03:00EDT. Router idle,
workers stopped, DSH preserved, no GPU reservation. See [restoration](docs/FULL-RAM-RESTORATION-20261029.md).

## Latest: daily gated engine updates and qualified Qwen — October 29

The daily NVIDIA engine updater is installed and enabled for 03:00 local time
(America/Toronto), with no missed-night catch-up. Next run at installation:
October 30, 03:00 EDT. Six selected profiles are covered by independent components:
HyperQwen, heterogeneous SGLang, Strata Qwen, Maya GLM, Maya DeepSeek and Strata
DeepSeek. No engine was updated during setup. The read-only discovery found newer
sources for five components; discovery does not qualify them.

Production and candidate must pass matched speed, quality, near-window retrieval,
sustained generation, fresh reload and resource checks. Paired performance uses
the AMD 95% prefill/decode and bounded TTFT envelope. Patch drift, missing evidence,
failed production baselines or candidate gates block promotion. Durable preimages,
recovery-before-router ordering and exact reservation ownership protect existing
work. All 198 CPU regressions passed. See [schedule and gates](docs/DAILY-ENGINE-UPDATE-POLICY.md)
and [daily ledger](docs/DAILY-ENGINE-UPDATES.md).

Qwen Flash-Next now uses plain mapped experts and both GPUs at 32K, with its
qualified Qwen-only 128 MiB/s writes / 160 MiB/s combined swap allowance over
30 seconds. JSON/arithmetic/image, 29,450-token retrieval, separate 8,192-output
continuous generation (139.52s) and fresh reload passed. Other profiles retain
1/8 MiB/s swap limits. Independent guards and existing historical benchmarks are
unchanged. See [qualification](docs/QWEN-RELAXED-SWAP-20261029.md).

DeepSeek/Maya retains its qualified 512 MiB reserve, 16 GiB periodic model-file
residency target and native 12 GB pinned hot cache. Reduced-RAM cache choices stay
temporary: full-RAM cache restoration still requires explicit hardware confirmation
and capacity verification. Older failure/pause/no-updater notes below are historical
and superseded for the specific configurations described here.

Updated October 28, 2026, after engine-switch and context-visibility fixes. Read README.md and AGENTS.md first.

## Standing direction

Keep host swappiness at 60. The user superseded the earlier VM10 approval; that
experiment never ran and administrator authentication was dismissed. The private
VM10 launcher refuses execution when the saved new direction exists. Do not
launch it or persist 10. Unlimited worker swap occupancy and the existing active
churn, RAM/GPU/headroom/temperature safeguards remain. No swap-file growth,
swapoff, driver, engine binary, hardware, firmware, clocks or fan changes occurred.

Scope remains six profiles. AMD repos are read-only reference. No model expansion was selected. The October 29 daily updater selection above supersedes the old no-updater state. Preserve all completed evidence; do not repeat
benchmarks. The old thread handed off and will not initiate work.

## Deployed settings and unresolved Maya

Four independently qualified upgrades are deployed: HyperQwen 56,320 (50,627-input
retrieval); SGLang 32,768 (now TP2/MTP3 W4A8, chunk 384; 29,434-input retrieval); GLM 65,536
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
heterogeneous patch. Preserve swappiness 60, all resource guards and the automatic
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
made visible without restarting or rebenchmarking it. The user explicitly
confirmed publication of all pending reports, handoffs, experimental patches and
visible-terminal changes to Biegle-W/linux-llm-nvidia-public. The prior external
public-push restriction is resolved; all four previously pending commits were
published successfully. Continue keeping both repositories and Markdown files
updated under that standing authorization.

Visible foreground verification passed 19 router tests. The router was reloaded
without restarting the inference worker or changing its selection. Console GUI
processes launch in separate user services, outside inference resource cgroups.
Evidence is private under data/visible-backends-20261028/. No new GPU benchmark
was run. Swappiness remains 60.

## Repository publication — October 28

The user explicitly authorized the pending reports, handoffs, experimental patch
and visible-terminal changes for Biegle-W/linux-llm-nvidia-public, and reaffirmed
continuous maintenance of both repositories and Markdown documentation. The four
pending public commits through 8042ea1 were pushed successfully. No pending public
approval remains. Continue reviewed, sanitized exports and independent pushes;
do not ask for redundant routine publication approval. Keep private evidence,
credentials, local paths, binaries and model weights out of the public repository.
Final synchronization evidence is private under data/repository-sync-20261028/.

## 32K SGLang TP2/MTP3 retest with 512 MiB floor — October 28

The user explicitly approved lowering the dense VRAM-free floor from 1,024 to
512 MiB. The normal dense supervisor and isolated retest share that constant;
swappiness 60, RAM 30/36 GiB, host available 8 GiB, temperature 82°C, unlimited swap
occupancy and active churn thresholds remain unchanged. This supersedes the
current 1 GiB dense guard requirement, not the historical attribution of old runs.

The corrected unchanged fork candidate completed three requests at 32,768 context:
1664.67 prefill tok/s, 1.34646 s TTFT and 82.7856 decode tok/s. JSON, arithmetic
and 29,434-input three-marker retrieval passed. All 256 W4A8 rank/projection
entries, both draft weight-completeness/sharing checks, GPU-only target/draft
placement and full 32K KV pools passed. Minimum sampled free VRAM 802/997 MiB
(Ti/3080); maximum GPU temperatures 57/45°C. Minimum host available RAM 32.15 GiB,
peak owned RAM 7.26 GiB and swap 0. No guard stop or OOM occurred. Fifteen swap and
supervisor regressions passed in the visible foreground harness.

The 82.79 decode median is about 29.0% above the prior 32K TP2 no-MTP control;
that control was not rerun and the comparison is historical, not a fresh pairing.
Long retrieval completed in about 24 seconds; no complete 30-second continuous
inference swap-rate window was observed, so this is not sustained-load qualification.
The previous 1 GiB-guard failures remain unchanged and valid for their policy.

The foreground harness and backend logs were visible. Cleanup left the router
idle with no selected worker, no port 10000 listener and no GPU-LOCK. HyperQwen
was not restored; swappiness is 60. No production fork promotion or engine setting
change was made. The selected normal SGLang remains PP2 W4A16/FP32/32K, while
the normal dense GPU guard is now 512 MiB on future launches.

See [the retest report](SGLANG-MTP3-512MIB-20261028.md) and matching numeric results.
Raw evidence is private under data/sglang-mtp3-512mib-20261028/. Do not repeat
completed control/kernel tests or silently promote this candidate.

## Router/harness and Desktop names — October 28

Live read-only verification confirms six router IDs and four DSH NVIDIA providers,
all using http://127.0.0.1:10100/v1. Changing the selected DSH provider/model sends
a different model ID; the router serializes requests, waits for active work and
switches its single owned backend. Same-profile requests reuse a ready worker.
The router is idle with no selected/loaded worker. DSH retains its saved HyperQwen
UI default; this does not preload it. No GPU request or new benchmark was run.

The SGLang API ID still launches maintained PP2 W4A16/FP32 at 32K. The successful
TP2/MTP3 W4A8 512 MiB retest remains isolated, not registered or silently deployed.
The normal dense reserve is 512 MiB; swappiness remains 60. See network/README.md.

Removed the LLM prefix from all four managed Desktop shortcut display names and
filenames: HyperQwen-vLLM.desktop, SGLang.desktop, Strata.desktop and Maya.desktop.
All are executable/trusted, with unchanged launch commands, icons and terminal
behavior. DSH and unrelated RGB shortcuts are preserved. The installer now writes
these names and removes only its own legacy LLM-* Desktop/menu entries. No service
reinstallation/restart, provider reconfiguration or backend selection was needed.

## Latest deployment: SGLang TP2 + MTP3 W4A8 — October 28, 01:07 EDT

The user explicitly deployed the fastest tested SGLang generation architecture.
The normal `qwen27b-sglang` router ID, SGLang shortcut and DSH `nvidia-sglang`
provider now load the pinned htsglang 62271fd plus qualified local patch, TP2/PP1,
MLP-only W4A8, BF16 state/KV, one Mamba slot and 32K context. Earlier PP2 FP32 /
“not deployed” statements describe superseded stages. The carried qualification
median is 1664.67 prefill / 1.34646 s TTFT / 82.79 decode. This was fastest tested at
qualified 32K for generation; PP2 W4A8 had faster prefill and the same MTP3 setup
at 16K reached 84.63. The user selected the larger qualified window and generation
tradeoff. No completed speed benchmark or kernel matrix was repeated.

Stable source: runtimes/sglang-hetero-62271fd/python/sglang; native interpreter:
runtimes/env-htsglang-62271fd; copied caches: runtimes/cache-sglang-hetero-62271fd.
config/sglang-runtime.json pins the full source tree, patch hash and dependency
versions. The normal launcher verifies all of them, checks the import location,
clears stale PP partition overrides and writes per-invocation GPU placement and
runtime receipts. Retain env-sglang as an active general-Python dependency fallback.
The router now supplies non-thinking chat defaults while allowing explicit overrides.

All 50 CPU regressions passed in a visible foreground harness. Normal router/API
streamed JSON, parsed tool call and 29,434-input retrieval passed. A 4,096-output
request ran 39.62 s and exercised four complete 30-second active swap windows, with
zero owned swap I/O and no pressure/guard violation. All 256 decoder MLP rank/
projection checks, both draft completeness/sharing checks, four GPU-only placements
and four full 32K KV pools passed. Minimum sampled GPU free 759/997 MiB (Ti/3080),
peak temperatures 62/49°C, minimum host available 32.26 GiB, peak worker RAM 7.36 GiB,
swap 0. Normal unload/reload produced a new owned invocation, the same verified
source and a passing JSON response. This is a short deployment check, not a
multi-hour reliability claim.

Keep the 512 MiB dense reserve, swappiness 60, RAM 30/36 GiB, host 8 GiB, temperature 82°C,
unlimited swap occupancy and active swap/pressure/telemetry guards. All launches
and harnesses remain visible. SGLang is intentionally selected after this deployment;
normal ten-minute idle release applies. HyperQwen was not restored. DSH provider
mapping was verified and its saved UI default was preserved; no new profile ID.

Four exact launcher/router/config/test preimages were archived privately in
Biegle-W/retired-llm-setting at 733820f, with hashes and original paths/commits.
The active registry retains a pointer and numeric history, not a second runnable
PP2 profile. Raw evidence and private rollback snapshots are under
data/sglang-deployment-20261028/. See SGLANG-DEPLOYMENT-20261028.md and its numeric
verification. Historical numeric reports are unchanged.

## Latest context study complete — October 28, 01:22 EDT

The user requested context beyond 32K without losing generation speed. The deployed
TP2/MTP3 W4A8 source, precision, rank ratios/budgets and guards were unchanged.
A fresh 32K control passed tool/JSON/arithmetic and 29,434-input retrieval at 1667.87
prefill / 1.34554 s TTFT / 84.7639 decode. This is now the latest measured control for
the same selected profile; the original 82.79 qualification and deployment evidence
is retained, not relabeled or discarded. No production context/engine change.

The predeclared 40K/38K/36K sequence found no initial candidate meeting the criterion.
40,960 advertised tokens backed only 40,760 in every target/draft KV pool; the worker
was rejected before timing. At 38,912, generation 83.3212 was 1.70% below control;
at 36,864, generation 83.5018 was 1.49% below. Their short screens are not qualified
larger contexts: tool/near-window qualification was skipped after the speed gate
failed. The planned late-control/candidate confirmation was not run because none
passed initially. Small measured differences can include normal variation; these
screens do not prove that other tuning or contexts are impossible, but do not
establish a no-loss upgrade. Do not repeat these settings to seek a favorable run.

Keep context 32,768 and max_total_tokens 32,768. Dense reserve 512 MiB, swappiness 60,
RAM 30/36 GiB, host available 8 GiB, temperature 82°C, unlimited swap occupancy and
active swap/pressure guards remain. The visible coordinator finished, all owned
workers stopped, GPU-LOCK was released and router is idle. Do not automatically
restore HyperQwen or SGLang after this isolated study. The unchanged deployed
SGLang profile will load normally on request; DSH still advertises 32K and requires
no metadata change. Other five profiles and historical numeric files are unchanged.

[Report](SGLANG-CONTEXT-20261028.md) and matching numeric evidence record all four
trials. Private plans, terminal logs, native metrics, audits and telemetry are under
data/sglang-context-20261028/. complete.json, progress.json and final-health.json
are authoritative. No study worker/coordinator remains active.

## Latest user clarification — proportional context tradeoffs

The user accepts a proportional context/performance tradeoff; the prior strict
zero-generation-loss gate is no longer the acceptance rule for future work.
Assess percentage context gain against measured generation slowdown and report
both. The 38K screen offers 18.75% more allocated context for 1.70% slower generation;
36K offers 12.5% more for 1.49% slower. These screens remain unqualified for promotion:
tool/near-window quality and full-workload resource checks were skipped under the
old gate. 38K is the stronger next qualification candidate; no new speed result,
quality pass or context deployment is implied by this reassessment. Keep 32K until
qualification is complete. The 512 MiB reserve, swappiness 60 and visible terminals
remain mandatory; no further guard relaxation was authorized.


## Shared all-engine policy active — October 28

Canonical config/inference-policy.json enforces 600-second automatic idle unload,
required visible terminals/lifecycle telemetry and proportional context/performance
tradeoffs across all six models and four engines. Router/native launchers and
lifecycle logger read it. The worker manager defaults to that timeout and rejects
zero/invalid disabling. The installer persists timeout/telemetry on reinstall.
Dense normal CLI launches now enter router ownership; an internal launch marker
prevents recursion and retains all original setup/storage/port/resource preflight.
Maya/Strata native configs always get 600s, per-profile activity and exclusive idle
reservation; a missing native adapter refuses launch. Active/queued/loading/vision
work, reservations and unknown state defer unload. Health/catalog polling does
not refresh the idle clock. Native web/control servers can remain after weights
unload; router, DSH and unrelated applications/terminals are preserved.

Visible verification observed actual SGLang idle-unloaded at timeout 600, about
610.15 seconds including scheduler checks/teardown, without a manual unload or
shorter timeout. Router/DSH remained active and GPU-LOCK was released. A separate
normal Chat Completions request then automatically reloaded SGLang, passed JSON,
and was explicitly unloaded only for final smoke-test cleanup. Do not confuse
that later cleanup with the recorded automatic-expiry proof. Final router is idle;
no HyperQwen was restored. Shared-policy, idle/FIFO/races, router, supervisor,
MoE and telemetry regressions passed. New live 600s proof is SGLang; other profiles
have audited shared wiring and prior evidence, not six new live expiry tests.
Large MoE models were not reloaded while RAM is reduced.

All contexts/cache/precision settings and benchmark values are unchanged, including
SGLang 32K and its 38K qualification backlog. Preserve dense 512 MiB reserve,
swappiness 60, all existing RAM/thermal/swap guards and visible terminals. Proportional
tuning is a shared qualification rule, not an automatic context updater or new
fixed loss tolerance. Six exact source preimages were archived privately at 8ca025e.
[Policy/report](ALL-ENGINE-POLICY-20261028.md) and validation JSON record scope,
settings, tests and timer proof. Raw logs/receipts are under
data/all-engine-policy-20261028/. verification.json and final-verification.json
are complete; no idle-check GPU worker remains running.

## Handoff upkeep — October 28

The user requested the AMD context-monitor/handoff workflow here. The general
handoff rule is now explicit in README/AGENTS: before yielding after meaningful
work, record objective/constraints, selected versus candidate settings, completed
verification, actual blockers/failures, active jobs/locks, unfinished steps and
one concrete next action. Update this canonical takeover record and applicable
reports, review public sanitization, push both repositories and verify sync, or
state the exact outstanding publication step. Do not create competing current
runtime handoffs or rerun completed benchmarks just for documentation.

No inference settings, benchmark values, services or GPU tests changed in this
workflow task. The existing 32K SGLang deployment, 38K qualification backlog,
reduced-RAM MoE caveats, shared 600s idle policy and all guards still apply.

## Latest: SGLang 38K qualification completed, 32K retained — October 28

The user resumed 38,912 under the proportional context/speed policy. Isolated
GPU-only placement, W4A8/MTP audits and all four 38,912-token KV pools passed.
JSON/arithmetic, parsed tool call and tool-result roundtrip, 34,964-input retrieval
and 35,063-input full-history checks passed. A 34,973-input/3,072-output stream ran
for 163.28 s, including 135.81 s continuous generation. Sampled GPU free memory never
fell below 560/795 MiB; worker swap and active-window I/O were zero. Keep the existing
512 MiB reserve, swappiness 60, 600s idle policy and all other guards.

Normal-router retrieval and automatic request reload worked, but the reloaded
worker advertised 38,912 while all four KV pools backed only 37,501. The deployment
check rejected that shortfall and restored 32,768 in the maintained profile and
DSH web/headless providers. Saved DSH defaults were preserved. 39 CPU regressions
passed after correcting an old visible-console test fixture; production launcher
and guards were unchanged. A correct fenced tool answer was accepted using the
existing JSON convention; passed quality checks were reused rather than rerun.

The earlier 83.32 versus 84.76 decode medians remain saved fixed-input screens:
18.75% more capacity for 1.70% slower generation. No speed measurements were
repeated. Near 35K actual input, the long resource stream observed 22.61 decode tok/s, a different workload; this does not replace the fixed-input benchmark.
The failure is normal-reload KV coverage, not speed, OOM or an isolated guard stop.

Final router is idle, DSH active, no GPU-LOCK or test coordinator remains; visible
review consoles may remain open. No fallback model was restored. No context,
runtime, precision, budget or model coverage change remains deployed. Keep both
repos and this canonical handoff current. The 38K quality/resource checks are now
complete; the remaining blocker is reliable full-KV backing on normal reload.
Next action: investigate startup memory/capacity variability without relaxing
guards; do not repeat completed speed screens for luck. Reduced-RAM MoE/Maya
sustained-swap caveats remain separate unresolved work. See [qualification](SGLANG-38K-QUALIFICATION-20261028.md).


## Latest: automatic engine switch closes only its backend — October 28

Normal model/engine selection drains an active API reply, stops the previous
recognized guarded worker, verifies resources released and starts the new one.
Backend consoles now follow the worker invocation and close on stop/switch;
completed Desktop selection launchers no longer remain waiting for Enter.
Only the registered backend viewer is signaled after path/mode/unit validation.
Router, DSH, harness/review consoles and unrelated processes remain. Protected
GPU-LOCK owners block selection; their reservations are never removed by switching.

A real SGLang 32K→HyperQwen 56,320 switch completed a 512-token active stream first,
closed old worker/viewer, opened the new backend console and passed API JSON.
Router/DSH invocations stayed unchanged. Normal unload closed the replacement
backend/viewer; final router idle, DSH active, no GPU-LOCK or coordinator. 53 engine/ownership
CPU regressions cover native busy/loading/vision, unknown state, ownership changes,
viewer PID reuse and protected harnesses. No new MoE loads or benchmarks.
Keep 512 MiB reserve,swappiness 60, 600s idle and all other guards; SGLang remains 32K.
See [engine switching verification](ENGINE-SWITCHING-20261028.md). Next action: follow the next user task;
do not repeat completed GPU qualification or restore a fallback automatically.


## Latest: all project terminals start minimized — October 28

The user requires engines, router, DSH/harnesses, selectors and test tasks to remain
visible in the taskbar but start minimized without taking focus. The shared
launcher now uses a SHA256-pinned project-local XTerm runtime with native-iconic
startup. There is no focus-then-minimize race or global desktop focus-policy change.
System packages and inference environments were not modified. Setup is reproduced
with scripts/install_visible_terminal_runtime.py and config/terminal-runtime.json.

All four engine shortcuts use Terminal=false and the shared minimized selector,
avoiding a foreground default-terminal window. Successful selectors close after
readiness; failures remain available for inspection. Native engine readiness prints
a web URL instead of activating a browser. Explicit UI opening remains user-controlled.
Backend-only auto-close and protected router/harness ownership rules remain.

A live window-manager audit verified initial Iconic,hidden and not-active state for
the test harness, router, DSH and actual SGLang backend. The real SGLang Desktop
shortcut passed API JSON; router/DSH invocations stayed unchanged during selection.
The DSH service was not restarted when its viewer was migrated. Router was activated
once while idle to load the launcher change. 53 engine/ownership regressions passed;
no benchmark, driver, precision, budget or context change. Final router idle, DSH active,
no GPU-LOCK. Dense 512 MiB, swappiness 60, 600s idle and other guards remain unchanged.
See [switching and minimized-window evidence](ENGINE-SWITCHING-20261028.md).


## Latest: router admission and transport improved — October 28

The AMD-inspired separation of HTTP, backend transport and lifecycle is deployed
in the existing router service. FIFO admission permits one active operation and
eight waiters; overload is reported explicitly, failed waiters release their place,
and queued requests take priority over automatic idle teardown. Backend error
status/messages are preserved and credentials redacted. Health exposes admission
state. All six model IDs, desktop/native paths and DSH defaults remain.

Same-model concurrency is deliberately disabled: actual HyperQwen, SGLang and
native configurations all have one execution slot. Enabling it would require
new engine/state/memory qualification, not merely removing the router lock.
94 CPU regressions and two sequential 32-token normal SGLang transport requests
passed. This was not a new speed benchmark or a concurrent GPU test. The router
was restarted only while idle under an owned temporary reservation; DSH ownership
was preserved. SGLang was left ready for normal600-second idle release; no fallback.

Keep512MiB dense reserve,swappiness60,600s idle,all other guards and SGLang32K.
Registry/runtime/guard/desktop-launcher source hashes are unchanged. The38K
normal-reload KV blocker and reduced-RAM MoE caveats remain unresolved. No existing
job/reservation was stopped or removed; no completed GPU qualification was repeated.
Next action: follow the next user task; do not enable concurrency without separate
qualification. See [router validation](ROUTER-IMPROVEMENTS-20261028.md).

Publication complete: the user explicitly approved all three router destinations.
Private implementation aabf41f, sanitized public reference51ec194 and private
preimage archivefced113 were pushed and verified against their remote main branches.
The private context meter/switcher source, policy, helpers and raw state remain
excluded from public exports. No router implementation publication blocker remains.


## Latest: reduced-RAM SSD qualification — October 28

2 of the four SSD-streaming profiles now have bounded qualification with one 16 GiB
DIMM removed (45.55 GiB usable): unchanged contexts, JSON/arithmetic, near-window
retrieval, supported images, sustained generation, fresh-process reload and normal
router loading. Qualified cache choices are deployed temporarily. This supersedes earlier
reduced-RAM caveats only for these selected settings and this
bounded workload; it does not establish multi-hour reliability or an exhaustive
cache optimum. Dense measurements were carried forward without retesting.

- `glm-maya`: 2.11 decode tok/s (-56.1% against saved full-RAM fixtures), 65,536 context; 231.1s continuous generation and fresh-process reload passed.
- `deepseek-strata`: 1.80 decode tok/s (-39.2% against saved full-RAM fixtures), 131,072 context; 381.1s continuous generation and fresh-process reload passed.

Comparisons use saved historical full-RAM fixtures, not a fresh paired full-RAM
control. Preserve swappiness 60, 512 MiB dense reserve, native MoE GPU reserves,
8 GiB host floor, 82 C temperature limit, unchanged worker budgets and active
swap/churn/pressure/telemetry guards, concurrency one and 600-second idle unload.
Normal validation finished idle; router and DSH ownership were preserved and no
fallback was restored. Original credential-redacted settings are archived privately
with hashes; raw credentials and study evidence stay local.

Restore the appropriate full-RAM cache settings only after explicit human
confirmation that the DIMM is restored and Linux capacity verification, followed
by normal guarded loading checks and selected-setting metadata updates. A rise
in MemAvailable or elapsed time does not trigger restoration. Preserve unrelated
router/desktop improvements, credentials, guards and independent speed history.

See [qualification and all six current results](REDUCED-RAM-20261028.md) and
[machine-readable evidence](benchmark-results/20261028-reduced-ram.json).

Unresolved on reduced RAM: `deepseek-maya`, `flash-next-strata`. Their original cache settings and historical full-RAM table values are retained; they may stop at the unchanged guards. No passing reduced-RAM operating configuration or reliable slowdown percentage was established for them.

Final ownership: no qualification coordinator or GPU reservation remains; isolated
and normal workers are stopped. Completed minimized review consoles may remain
available. Router is idle and DSH remains active; no fallback was restored.

No publication or selected-profile validation work remains after the verified
both-repository push recorded privately. Flash and Maya DeepSeek reduced-RAM
qualification remains unresolved after the bounded cache study; do not relabel
partial retrieval/benchmark passes or repeat completed variants for luck.
Next action: when the human explicitly confirms the RAM DIMM is restored, verify
Linux capacity, restore only the appropriate full-RAM cache settings from saved
preimages, validate normal guarded loading and update selected metadata. Preserve
all unrelated router/desktop changes and independent benchmark history.


## Latest: lcz.me Qwen/Strata follow-up — October 28

The user requested qualification of the lcz.me pageable Qwen/Strata setup on the
current reduced-RAM machine, with application only after a pass. Both candidates
failed and **nothing was applied**. Full pageable residency needed 31.88 GiB for
CPU experts but only 30.51 GiB fit after native 8 GiB headroom. A bounded 28 GiB
pageable candidate, fixed 4096 prefill, seven workers, adaptation/PCIe sharing off,
1536 MiB VRAM reserve and no conversation cache loaded, then hit active owned-worker
swap protection at 92.35 MiB/s reads over 30.43 seconds. Its one completed measured
request does not establish a benchmark median or reliable operating performance.

Qwen context stays 32K. Canonical launch config, registry, runtime, all guards and
other five profiles are unchanged; the temporary GLM/Strata DeepSeek settings remain.
Worker stopped, GPU reservation released, router idle, DSH ownership preserved;
no fallback restored. Prior tests were preserved rather than repeated.

See [candidate settings and failure evidence](QWEN-STRATA-LCZ-20261028.md) and
[numeric results](benchmark-results/20261028-qwen-strata-lcz.json).
The next action is to await explicit human RAM-restoration confirmation, verify
Linux capacity, then restore appropriate full-RAM caches and verify normal guarded
loading. No timer/MemAvailable trigger, guard relaxation or unrelated rollback.


## Latest: Qwen host-RAM reserve 2 GiB — October 28

The human explicitly lowered Qwen/Strata host-RAM headroom from 8 GiB to **2 GiB**.
The normal supervisor now reads this Qwen-only selected floor from the registry;
all other five profiles retain 8 GiB. Eight new boundary/thermal/swap checks and
18 existing budget/swap/supervisor regressions passed (26 total). Three low
readings still stop the worker; swap/pressure/telemetry, VRAM reserves, temperature
82 C, RAM/swap budgets, swappiness 60, idle 600s and concurrency one are preserved.
No router or DSH restart was needed.

The full-pageable lcz.me candidate was retested with native and isolated host
headroom 2 GiB. It loaded 35.38 GiB pageable expert RAM (zero pinned), completed
three benchmark screens (53.29 decode tok/s median), then hit the unchanged swap
guard at 76.90 MiB/s reads plus 18.81 MiB/s writes over 30.46 seconds. This is a
rejected screen, not a qualified operating benchmark. **The failed lcz.me cache/
execution setup was not applied.** Native launch config, selected benchmark fields,
contexts and the other five profiles are unchanged.

Test worker stopped, GPU reservation released, router idle, DSH ownership preserved;
no fallback restored. Preimages are archived privately with hashes. See
[guard selection and retest](QWEN-HOST-RESERVE2-20261028.md) and
[numeric evidence](benchmark-results/20261028-qwen-host-reserve2.json).
Next action: after explicit human RAM-restoration confirmation, verify Linux
capacity, restore appropriate full-RAM caches and verify normal guarded loading.
Preserve this separately approved reserve selection and unrelated router/Desktop
changes unless the human changes that direction. No timer/MemAvailable trigger.


## Latest: all profiles use 2 GiB host reserve — October 29

The human approved a **2 GiB host-available RAM floor across all six maintained
profiles**. The registry now explicitly selects 2 GiB for each profile; the common
reader also defaults to 2 GiB. Both dense and MoE supervisors use the selected
value, and the benchmark monitor records and follows the same per-profile floor.
This supersedes earlier Qwen-only 2 GiB / other-profile 8 GiB instructions.

Forty-one CPU checks passed, including both dense engines at the 2 GiB boundary,
below-floor stops, the unchanged 512 MiB VRAM boundary, thermal and swap stops,
worker budgets, intentional shutdown ownership and benchmark metric parsing.
Supervisor three-reading hysteresis, 82 C, all native VRAM reserves, worker
RAM/swap budgets, active swap/pressure/telemetry guards, swappiness 60, concurrency
one and 600-second idle unload are unchanged. No GPU models or benchmarks were
rerun. Model/cache/context settings and historical benchmark values are unchanged.

Normal workers were inactive; the new floor is read at their next launch. No
router/DSH restart or job cancellation occurred. Router idle, DSH preserved,
no GPU reservation and no fallback restored. The earlier Qwen/Maya reduced-RAM
failures remain unresolved; this policy change does not qualify those setups.

After explicit human confirmation that the RAM DIMM is restored, verify Linux
capacity, restore appropriate full-RAM cache values and validate normal guarded
loading. Preserve the separately approved 2 GiB reserve unless the human changes
that direction, along with unrelated router/Desktop improvements and credentials.
No timer or MemAvailable trigger.

See [all-profile reserve change](ALL-PROFILES-HOST-RESERVE2-20261029.md) and
[verification](validation-results/20261029-all-profiles-host-reserve2.json).


## Latest: dense RAM caps removed; MoE reserve study — October 29

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


## Current Qwen/Flash-Next guard test — October 29

The unchanged normal Qwen/Flash-Next Strata preset was tested through the router
with the current guards. It failed during loading: native startup announced
about 47 GB of RAM experts and a 39.97 GiB expert arena; host available fell to 0.717 GiB
(free 0.408 GiB), below the 2 GiB supervisor floor. Peak temperature 42 C; no cgroup
high/max/OOM event. The RAM guard stopped it safely before readiness.

Loading swap peaked at 1.68 GiB, but this was not an active-inference swap stop:
no inference window was reached. JSON/image/retrieval/sustained/reload checks
were not reached. No speed benchmark was repeated;97.09 tok/s remains historical.

Source/cache/context settings and every guard remain unchanged. 44/48 GiB cgroup
limits and unlimited loading swap occupancy were read back. Router/DSH preserved,
worker stopped, router idle, no reservation/fallback. This is a current reduced-RAM
resident-allocation failure, not general incompatibility between Qwen and Strata.
The other five selections remain unchanged. Do not apply rejected pageable variants
or restore full-RAM settings without explicit human confirmation and Linux capacity
verification. Further cache tuning requires its own qualification.

See [current normal-profile test](QWEN-CURRENT-GUARDS-20261029.md) and
[numeric evidence](validation-results/20261029-qwen-current-guards.json).
