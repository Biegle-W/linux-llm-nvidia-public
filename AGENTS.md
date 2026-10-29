# Agent entry point

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
work. All 197 CPU regressions passed. See [schedule and gates](docs/DAILY-ENGINE-UPDATE-POLICY.md)
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

## Latest: current Qwen/Flash-Next reduced-RAM loading test — October 29

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

See [current normal-profile test](docs/QWEN-CURRENT-GUARDS-20261029.md) and
[numeric evidence](docs/validation-results/20261029-qwen-current-guards.json).


## Latest: bounded DeepSeek/Maya cache qualifies at 512 MiB — October 29

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

See [demand-cache qualification and six selected results](docs/MAYA-DEMAND-CACHE-20261029.md)
and [numeric evidence](docs/benchmark-results/20261029-maya-demand-cache.json).


## Latest: DeepSeek/Maya 512 MiB follow-up rejected — October 29

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

See [DeepSeek/Maya follow-up](docs/MAYA-DS4-VRAM512-FOLLOWUP-20261029.md) and
[numeric evidence](docs/benchmark-results/20261029-maya512-followup.json).


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

See [qualification and current results](docs/MOE-VRAM512-20261029.md) and
[numeric evidence](docs/benchmark-results/20261029-moe-vram512.json).


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

See [all-profile reserve change](docs/ALL-PROFILES-HOST-RESERVE2-20261029.md) and
[verification](docs/validation-results/20261029-all-profiles-host-reserve2.json).


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
[guard selection and retest](docs/QWEN-HOST-RESERVE2-20261028.md) and
[numeric evidence](docs/benchmark-results/20261028-qwen-host-reserve2.json).
Next action: after explicit human RAM-restoration confirmation, verify Linux
capacity, restore appropriate full-RAM caches and verify normal guarded loading.
Preserve this separately approved reserve selection and unrelated router/Desktop
changes unless the human changes that direction. No timer/MemAvailable trigger.


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

See [candidate settings and failure evidence](docs/QWEN-STRATA-LCZ-20261028.md) and
[numeric results](docs/benchmark-results/20261028-qwen-strata-lcz.json).
The next action is to await explicit human RAM-restoration confirmation, verify
Linux capacity, then restore appropriate full-RAM caches and verify normal guarded
loading. No timer/MemAvailable trigger, guard relaxation or unrelated rollback.


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

See [qualification and all six current results](docs/REDUCED-RAM-20261028.md) and
[machine-readable evidence](docs/benchmark-results/20261028-reduced-ram.json).

Unresolved on reduced RAM: `deepseek-maya`, `flash-next-strata`. Their original cache settings and historical full-RAM table values are retained; they may stop at the unchanged guards. No passing reduced-RAM operating configuration or reliable slowdown percentage was established for them.

Earlier dated qualification statements below remain historical evidence.

Read [README.md](README.md) for standing policy, then
[the current takeover state](docs/CURRENT-STATE.md) before acting. The registry is
`config/maintained-profiles.json`; historical measurements are evidence, not live
settings. Update these entry points, the benchmark ledger and both NVIDIA repos
after meaningful changes so another agent can resume without chat history.

Before yielding, record the objective, selected versus candidate settings,
completed verification, actual blockers, active jobs/locks, unfinished steps and
one concrete next action in the canonical takeover handoff. Verify both pushes
or record the exact outstanding sync step. Do not rerun completed GPU tests for docs.

Latest router update: bounded FIFO admission and separate backend transport are
deployed; one active operation/eight waiters. Same-model concurrency is NOT enabled:
all maintained engines are configured for one execution slot. Preserve that limit
until separate engine/resource/state-isolation qualification. 94 CPU regressions
and normal nonstream/SSE smoke passed; see docs/ROUTER-IMPROVEMENTS-20261028.md.
Desktop integration, all guards and DSH ownership remain unchanged.

Four qualified context upgrades and the approved lifecycle controls are deployed.
All six normal launch paths passed functional/limit checks. Actual GLM/dense idle
expiry and normal reload, plus isolated Strata idle/reload, are verified. No test
coordinator remains active. Maya sustained-swap qualification remains unresolved;
retain its guarded 32K setting and do not relabel short API success as qualification.
Do not repeat completed measurements. CURRENT-STATE.md records exact evidence.

The user accepted GLM 65,536 and Strata DeepSeek 131,072 despite the recorded
speed tradeoffs. Resource and near-window quality qualification still applies.
That historical no-loss gate is superseded by the shared proportional-tradeoff policy below.
The AMD repository is read-only reference for the requested gap audit; ask before
filling optional cross-repository feature/model gaps. No new unlock tests or
hardware changes are authorized by that audit.

The user approved three operational additions after context rollout: guarded
ten-minute idle unload, full lifecycle telemetry and manual candidate staging.
Do not ask again for those additions. Model coverage stays unchanged.

Read the [additional AMD parity task background](docs/AMD-PARITY-HANDOFF-20261027.md)
as a dated backlog. CURRENT-STATE.md is authoritative for live jobs and completion.

The user approved unlimited worker swap occupancy with active churn protection.
The maintained guarded paths implement this; preserve RAM/GPU limits and consult
[the policy and rollout evidence](docs/INFERENCE-SWAP-POLICY.md).

The latest user instruction supersedes the earlier VM10 trial approval: keep host
swappiness at 60. Do not launch or persist swappiness10. Continue remaining
qualification and deployment at 60 with the existing worker swap/churn guards.

## GPU unlock persistence after updates

As part of every kernel or NVIDIA driver update, automatically check that the
existing GPU unlock remains installed and configured for the next boot. Also
perform this check when resuming on a different kernel/driver version. Follow
[the update verification procedure](docs/UNLOCK-SETUP-20261026.md#required-checks-after-kernel-or-nvidia-driver-updates).
Verify DKMS for the target kernel, GRUB targets and early initramfs loading; after
the user's next reboot, confirm successful unlock on both selected GPUs before
NVIDIA binds and record the running kernel/driver and boot evidence. Do not call
next-boot preparation post-boot verification. Keep incomplete/failed checks visible
in CURRENT-STATE.md. The user controls reboot; this requirement does not authorize
driver updates, new unlock benchmarks, firmware changes or switching unlock source.

The user subsequently requested OS-level automatic checks independent of agents.
The [health checker](docs/GPU-UNLOCK-HEALTH.md) is installed and enabled. Boot and
package-update events run root-owned services without an agent. Initial boot and
update-hook audits passed. Inspect `gpu-unlock-health status --brief`, root-written
results and failed units rather than relying on this reminder. Preserve the
root-owned installed copy and event hooks; agents must not silently substitute
user-writable service code. Actual updates/reboots remain user-controlled.

## SGLang pipeline and recurrent-state study

The user-approved 34/30 and 36/28 pipeline splits failed the unchanged 1 GiB
GPU-headroom requirement. BF16 on 32/32 passed the tested quality checks but
showed only +0.9% decode with slightly slower prefill/TTFT. No candidate was
promoted. Retain 32/32 FP32 and HyperQwen as default; do not repeat these
completed settings or weaken the guard. See docs/SGLANG-TUNING-20261027.md.

## Isolated SGLang W4A8 study and temporary RAM maintenance

The user subsequently approved an isolated MLP-only W4A8 patch test. The final
compressed-tensors adapter activated exactly 128 decoder MLP projections and
passed 18 standalone GPU kernel checks plus JSON, arithmetic and 29,434-input
retrieval. Prefill improved 21.6% and TTFT 17.5%, but decode regressed 1.4%;
no production promotion. The first AutoRound-loader attempt was rejected by its
zero-activation audit before benchmarking; preserve that diagnostic evidence.
Retain the existing W4A16 SGLang package and HyperQwen default. See
docs/SGLANG-W4A8-20261027.md; candidate source/cache is private evidence.

One RAM stick is temporarily removed; Linux currently sees 45.55 GiB usable.
This dense study used fresh controls and retained all guards at swappiness 60.
MoE profiles have not been qualified on reduced RAM; check capacity and budgets
before any future MoE work. GPU unlock health reports VERIFIED after reboot.

## Heterogeneous TP2/MTP follow-up — October 28

The user accepted the W4A8 tradeoff and authorized an isolated heterogeneous
TP2/MTP study. The earlier decode regression is not a reason to reject that
accepted tradeoff. This authorization does not silently promote the fork.
The pinned fork, separate native runtime, reproducible local compatibility patch,
all startup failures and completed controls are recorded in
[the study report](docs/SGLANG-HETERO-MTP-20261028.md). That study used a
1 GiB GPU-free guard (superseded by the user-approved 512 MiB floor below), 8 GiB host floor, 30/36 GiB worker limits, active swap-churn
protection and swappiness 60. No generic CPU weight offload is permitted.
The benchmark metric reader now counts one canonical TP replica after the final
PP stage; seven regression tests cover parallel-rank accounting. Do not recompute
historical measurements or repeat completed variants because the reader changed.

Final outcome: MTP3 qualified at 16K (84.63 decode tok/s, +32.51% over its
matched TP2 control; 14,686-input retrieval). Corrected MTP1/MTP3 failed 32K
GPU-headroom qualification. HyperQwen and normal worker were restored; no
experimental coordinator or GPU-LOCK remains. See CURRENT-STATE.md for details.

## Visible terminals and test cleanup — user direction, October 28

All backend and harness launches must have visible desktop terminals so the user
can monitor progress. Guarded services keep their resource limits; live terminal
consoles display their journals and redirected engine logs. Dense bounded launches,
router MoE launches, router startup and DSH web startup open consoles automatically.
A failed visible-console handshake must not silently fall back to a hidden launch.
Closing a console leaves the guarded service running; its stop command is printed.

Run every future benchmark/test coordinator through the visible foreground wrapper:
`python3 scripts/visible_terminal.py run --title "Test name" -- /absolute/command args`.
For custom worker units, open a console with `visible_terminal.py open --title
"Backend" --unit NAME.service --log /absolute/engine.log` before starting them.
Preserve dated logs/results as well as visible output. Do not run new harnesses
silently through detached API commands. Completed terminal harnesses retain their
exit code and wait for Enter so results remain visible.

Do not automatically reload HyperQwen after an isolated experiment. Unload the
owned test worker, release its reservation and report the idle state unless the
user explicitly requests a backend to be left running. HyperQwen's existing
catalog/default metadata is not permission to repeatedly reload it after tests.

## Standing repository publication authorization — October 28 clarification

The user explicitly authorized publication of all pending reports, handoffs,
experimental patches and visible-terminal changes to
`Biegle-W/linux-llm-nvidia-public`, and reaffirmed that both repositories and
Markdown documentation must always stay updated. Routine publication of reviewed, sanitized project reports, handoffs,
reference code and experimental patches is included in that standing direction;
do not ask for a separate approval after every study or implementation change.
Continue the existing export allowlist, privacy review, nonpersonal commits and
independent pushes. A platform automatic-review rejection is an external tool
restriction, not a user-requested approval policy. Describe it accurately and
never attribute that restriction to the user or bypass a rejection.

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

The [512 MiB retest](docs/SGLANG-MTP3-512MIB-20261028.md) passed at 32K: 82.79
decode tok/s, JSON/arithmetic and 29,434-input retrieval, minimum sampled free
VRAM 802/997 MiB. No production fork promotion; prior 1 GiB failures are preserved.
The visible test finished idle, with no automatic HyperQwen restoration.

## Desktop shortcut names — October 28

Managed Desktop shortcuts are named HyperQwen vLLM, SGLang, Strata and Maya,
without an LLM prefix. Their filenames omit that prefix too; the installer migrates
only project-owned legacy entries. Preserve DSH and unrelated shortcuts. CLI
llm-* command names remain unchanged. See network/README.md for current routing:
DSH/API model IDs select fixed engine profiles; the experimental TP2/MTP3 fork
now backs the maintained qwen27b-sglang profile after verified deployment.

## Latest: SGLang production deployment — October 28

The user explicitly deployed the fastest tested SGLang generation architecture:
TP2 + MTP3, decoder MLP W4A8, BF16 state/KV, one Mamba slot, 32K. It now backs
the existing qwen27b-sglang ID, shortcut and DSH provider. Earlier PP2/FP32 and
“no promotion” statements describe historical stages; do not restore PP2 as the
normal profile. Source/dependency pins are in config/sglang-runtime.json; the
normal launcher verifies hashes, import location and versions. env-sglang is still
an active general-dependency fallback; do not delete it. Source/caches are in
stable `runtimes/` paths, not dated trial folders. Previous source/settings were
archived privately at 733820f; keep only the retirement pointer in the active registry.

Fifty CPU regressions, normal-router streaming JSON/tool call, 29,434-input
retrieval, a 4,096-output, 39.62 s continuous check and a normal unload/reload check
passed. Four complete active swap windows had zero owned swap I/O. Keep the
512 MiB dense reserve, swappiness 60, all other guards and visible terminals.
The router supplies non-thinking defaults while preserving explicit overrides.
The original 82.79 tok/s qualification median is carried forward, not remeasured.
SGLang is intentionally selected after deployment; the ordinary 10-minute idle
unload still applies. HyperQwen was not restored and saved DSH defaults were not
changed. See docs/SGLANG-DEPLOYMENT-20261028.md and CURRENT-STATE.md.

## Context expansion authorization — October 28

The user authorized larger deployed SGLang context only without losing generation
speed. Preserve the512 MiB reserve, swappiness 60 and visible terminals. Use fresh
matched controls and confirmation, full KV capacity and near-window quality/resource
checks before promotion; do not equate a larger advertised limit with usable KV.
Current study evidence: data/sglang-context-20261028/. Keep both repositories and
Markdown documentation current and preserve previous benchmark attribution.

Context study completed: retain 32K. Fresh control 84.76 decode; 38K/36K screens
regressed 1.70%/1.49% and did not proceed to long-window qualification. Advertised 40K
backed only 40,760 KV tokens and was rejected before timing. No candidate qualified
for promotion or confirmation. These small screens do not prove other tuning is
impossible. Production settings/runtime are unchanged; router is idle after owned
cleanup. See docs/SGLANG-CONTEXT-20261028.md. Do not rerun rejected measurements
merely to refresh repositories or obtain a passing median.

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

## Shared policy for every maintained engine/model — October 28

config/inference-policy.json is authoritative: automatic 600-second idle unload,
required visible terminals/lifecycle telemetry and proportional context/speed
tradeoffs requiring quality/resource qualification. Applies to all six profiles
across HyperQwen-vLLM, SGLang, Strata and Maya. Active/queued/loading/vision work,
reservations and unknown state defer teardown; health/model listing does not
refresh the timer. Next request reloads; do not preload a fallback model.

Router/native wrappers/lifecycle logger read the shared file. The installer now
preserves 600s on reinstall. Normal dense CLI enters router ownership; its marked
internal worker path avoids recursion while retaining original preflight/guards.
No contexts or model/cache settings changed. Preserve 512 MiB dense reserve,
swappiness 60, all RAM/thermal/swap guards and the reduced-RAM MoE caveats.
See docs/ALL-ENGINE-POLICY-20261028.md for coverage and actual idle/reload proof.


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
sustained-swap caveats remain separate unresolved work. See [qualification](docs/SGLANG-38K-QUALIFICATION-20261028.md).


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
See [engine switching verification](docs/ENGINE-SWITCHING-20261028.md). Next action: follow the next user task;
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
See [switching and minimized-window evidence](docs/ENGINE-SWITCHING-20261028.md).
