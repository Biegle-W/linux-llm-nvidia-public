# Linux LLM NVIDIA — public reference

## Latest: OpenAI-compatible request retries repaired — October 30

The router now reuses a verified running worker and waits for its existing cold load after a client disconnect, avoiding repeated reloads and the reported “Native worker state is unavailable” error. Ownership, active-work and resource guards remain intact. All 224 CPU tests passed. Live loopback streaming/non-streaming and Tailscale requests completed in under half a second without restarting the worker. Only the router was restarted; the loaded worker and DSH were preserved. See [repair](docs/API-RELIABILITY-20261030.md) and [verification](docs/validation-results/20261030-api-reliability.json).


## Latest: Qwen resident mode qualified and selected — October 30

Qwen now keeps the non-GPU expert cache complement resident across both GPUs at 32K. The matched full-qualification screen measured 88.12 versus 78.74 decode tok/s, 628.8 versus 435.1 prefill tok/s, and 3.46 versus 4.99 seconds TTFT. Both arms passed JSON/arithmetic/image, 29,435-input uncached retrieval, over 120 seconds sustained generation and fresh reload. Two selected normal guarded loads passed. Guards, runtime pins, quantization, context and GPU selection remain unchanged. GLM's exploratory gain did not survive confirmation; DeepSeek fixed/auto both failed the specific JSON fixture, so neither profile changed. The Strata native tokenizer counter was repaired;27 targeted CPU regressions and the real saved-reference counter check passed. See [qualification](docs/HARDWARE-TUNING-QUALIFICATION-20261030.md) and [numeric evidence](docs/validation-results/20261030-hardware-tuning.json).


## Latest: forum-backed hardware tuning candidates — October 29

Research supports testing Qwen resident experts on both GPUs, GLM native calibration, and DeepSeek/Maya automatic CPU-lane selection on the restored 64GB system. These are unvalidated candidates; no runtime, model, guard or selected setting changed and no GPU test was started. The installed Qwen setup has a quant-specific budget restriction requiring a native launcher compatibility check. DeepSeek source warns against assuming partial RAM copies improve speed. See [research](docs/HARDWARE-TUNING-RESEARCH-20261029.md) and [candidate evidence](docs/validation-results/20261029-hardware-tuning-research.json).


## Latest: completed terminals close automatically — October 29

Harness and selector windows now close when the command finishes, including failures. Private transcripts and atomic exit-code receipts retain the results. Service viewers close after their own service stops; active work, router/DSH service processes, unknown state and unrelated terminals are preserved. Minimized/no-focus startup remains. All 207 CPU regressions and real PTY success/failure/service-stop checks passed; final project terminal inventory was zero. No model or guard setting changed and no GPU benchmark was repeated. See [terminal lifetime](docs/TERMINAL-LIFETIME-20261029.md) and [verification](docs/validation-results/20261029-terminal-lifetime.json).


## Latest: targeted 15% pressure guard and two-profile 64GB benchmark — October 29

Qwen/Strata and DeepSeek/Maya now use 15% full-memory-pressure thresholds, up from 10%, with the same 30-second active window and three-sample stop rule. All other profiles retain 10%. The 128/160 MiB/s SSD swap limits and every independent RAM/VRAM/thermal/telemetry guard remain unchanged, as do contexts, weights, precision, runtime pins, expert caches, swappiness 60, concurrency 1 and idle 600 seconds. Both profiles completed a warmup and three valid 128-output measured requests without a guard violation. Only Qwen/Strata and DeepSeek/Maya were repeated; HyperQwen, SGLang, GLM/Maya and DeepSeek/Strata rows are explicitly carried forward from their earlier October 29 records. This composite table is not a new six-profile matched run. See [report](docs/BENCHMARK-PRESSURE-GUARD-64GB-20261029.md) and [numeric evidence](docs/benchmark-results/20261029-pressure-guard.json). Workers are stopped; router idle; no GPU lock; DSH preserved; no fallback.


The earlier 10% stop records remain archived. Explicit model selection cleared the old invocation latches; neither profile has a new guard latch. Peak inference pressure was 0% for Qwen and 6.80% for Maya; the added allowance was not exercised in these short runs.

## Latest: four SSD profiles use 128/160 swap limits — October 29

Four SSD-streaming profiles now use bounded swap limits of 128 MiB/s writes and 160 MiB/s combined over 30 seconds. Dense and unknown profiles retain 1/8 MiB/s. All other resource guards, contexts, expert-cache settings, precision choices, runtime pins and model settings are unchanged. 2 of four SSD profiles completed three valid measured requests without guard violations on restored 64GB RAM. RAM remains DDR5-4200 MT/s across four 16GB DIMMs (61.3013GiB usable; 2100MHz DDR clock). The dense profiles were not repeated; their table rows carry forward the earlier October 29 full-RAM run. deepseek-maya did not pass: Sustained full-memory pressure during inference. Qwen reached three outputs but stopped on the unchanged pressure guard; its timings are diagnostic and no new passing median is selected. See [the new report](docs/BENCHMARK-SSD-SWAP-64GB-20261029.md) and [numeric evidence](docs/benchmark-results/20261029-ssd-relaxed-swap.json). The earlier DeepSeek/Maya guard failure and all prior measurements remain dated evidence; this speed screen does not repeat full-window quality qualification.


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

## Qwen reduced-RAM qualification — October 29, 2026

Qwen/Flash-Next IQ3_XXS passed with mapped experts, both GPUs and Qwen-only swap limits of 128 MiB/s writes and 160 MiB/s combined over 30 seconds. Quality checks, 29,450-token retrieval, 8,192-output continuous generation and fresh reload passed across the recorded trials. Other model limits and independent resource guards are unchanged. See [qualification and limitations](docs/QWEN-RELAXED-SWAP-20261029.md).

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

## NVIDIA-agent parity handoff — October 27

The user requested [notes for NVIDIA-server agents](docs/AMD-PARITY-HANDOFF-20261027.md)
to address AMD/NVIDIA gaps. Start with loading-swap policy, request-aware idle
unload, documentation repair and reporting consistency; the handoff distinguishes
AMD-owned items and optional model/schedule choices. The original notes are dated background;
[CURRENT-STATE.md](docs/CURRENT-STATE.md) records current implementation. Root `AGENTS.md` points here
and to the current handoff/results; this README remains canonical policy.

Native Linux inference on the **i5-13600KF / 64 GB DDR5 / RTX 3080 Ti 12 GB +
RTX 3080 10 GB** workstation. A later PEX88096 switch installation adds
**RTX 3060 12 GB**. The separate dual-RX-7900-XTX Linux machine has its own
repositories and must not be modified as part of this migration.

The initial Windows-side preparation did not validate native Linux operation.
Do not promote inherited Windows profiles to validated Linux settings. Follow
[the Linux-agent migration handoff](docs/MIGRATION-HANDOFF.md).

**Native setup, October 26, 2026:** Ubuntu 26.04, the RTX 3080 Ti / RTX 3080 pair
and distribution NVIDIA driver 595.99.02 are now verified. Native llama.cpp CUDA
build and a short two-GPU inference smoke test passed; 31 focused matrix tests
passed on each GPU. Those initial checks did not establish unlock, P2P or sustained thermals.
[The two-card unlock is installed and verified](docs/UNLOCK-SETUP-20261026.md);
759 matrix tests per GPU passed after activation. See the
[unlocked-versus-stock comparison](docs/BENCHMARK-UNLOCK-20261026.md).
[A bounded native speed benchmark](docs/BENCHMARK-20261026.md) now covers all three
downloaded models and compares DeepSeek's two engines on shared Maya-S weights.
API smoke checks passed for Strata Qwen3.8-Flash-Next,
Maya GLM-5.3-Flash and DeepSeek on both engines. Strata also passed arithmetic,
JSON and conversation tests using Maya-S's shared DeepSeek weights; the separate
IST-DAS weight files were removed. See [native validation](docs/VALIDATION-20261026.md) and
[local setup](docs/LOCAL-SETUP.md); raw machine details remain ignored.

**Dense Qwen3.8-27B now defaults to HyperQwen/patched vLLM:** GPU-only TP2,
MTP3, BF16 recurrent state, INT4 KV and a 56,320-token allocation. The earlier 32K profile
measured **155 code / 108 prose tok/s** and passed 29,496-token retrieval; the
current 56,320 setting passed 50,627-input retrieval and uses the dated context
study metrics linked below.
The SGLang choice uses GPU-only PP2, CUDA graphs and 32K context; earlier 16K
code/prose checks measured **47 / 47 tok/s**.
[Engine settings, comparisons and validation](docs/DENSE-ENGINE-OPTIMIZATION-20261027.md)
include the old 4070 + 3060 reference and guarded DFlash/SGLang TP failures.
Start the default with `./scripts/start_model.sh qwen27b`, or explicitly select
`./scripts/start_model.sh qwen27b sglang`. The retired
[IQ4_XS/MTP2 measurements](docs/QWEN27B-GPU-ONLY-20261026.md) remain preserved.

The [maintained-profile registry](docs/MAINTAINED-PROFILES.md) now keeps exactly
one selected setting per model, weight quantization and engine: six profiles.
Superseded launchers and the duplicate Strata alias are retired; completed
measurements remain available as dated evidence.
[Strata DeepSeek Maya-S earlier qualified 64K context](docs/DEEPSEEK-STRATA-CONTEXT-20261027.md),
with 58,969-token three-marker retrieval passed; the current context rollout uses 131,072 with 117,866-input retrieval. Its previous 8K speed results
remain preserved as historical measurements.

[The model router and desktop apps](network/README.md) provide authenticated
OpenAI model/engine selection on port 10100 over loopback and Tailscale. DSH is a
separate client on port 3080; Strata and Maya shortcuts open their native web apps.
The [router admission update](docs/ROUTER-IMPROVEMENTS-20261028.md) adds bounded FIFO
queuing, request-state reporting and faithful backend errors. Same-model execution
remains serial after auditing the qualified one-slot configurations; desktop
integration and all resource/ownership guards are preserved.

[Current takeover state](docs/CURRENT-STATE.md), [benchmark ledger](docs/BENCHMARK-HISTORY.md),
[inference swap policy](docs/INFERENCE-SWAP-POLICY.md),
[operational lifecycle controls](docs/OPERATIONAL-LIFECYCLE.md),
[saved-evidence unlock assessment](docs/UNLOCK-IMPACT-20261027.md), and
[AMD/NVIDIA gap audit](docs/AMD-NVIDIA-GAP-AUDIT-20261027.md) are maintained with this task.

**Context rollout:** [four qualified context upgrades deployed at swappiness 60](docs/CONTEXT-EXPANSION-20261027.md). Flash remains 32K; Maya DeepSeek remains 32K with unresolved sustained-swap qualification. All six normal functional paths passed; idle/reload verification passed with the documented shutdown fix.

**Latest results:** [GLM/DeepSeek cache optimization at unchanged contexts](docs/MOE-OPTIMIZATION-20261027.md).
The [previous full six-profile benchmark](docs/BENCHMARK-20261027-101219.md) and all
historical evidence remain preserved; the current [grouped maintained table](docs/MAINTAINED-PROFILES.md) includes the
new SGLang deployment alongside preserved measurements for other profiles.

**Model storage policy:** [NVMe for SSD-streaming models; SATA for GPU/RAM-resident weights](docs/STORAGE-POLICY.md).
Dense Qwen uses the SATA SSD through its existing checkpoint alias.
[Unused trial weights and preparation files were removed](docs/UNUSED-MODEL-CLEANUP-20261027.md)
after saved-evidence review and bounded DSpark comparisons. All six active
profiles and historical benchmark results remain preserved.

**SGLang deployed:** [TP2 + MTP3 with decoder MLP W4A8 at 32K](docs/SGLANG-DEPLOYMENT-20261028.md)
now backs `qwen27b-sglang`, the SGLang shortcut and the DSH SGLang provider. It is
the fastest tested SGLang generation architecture at this qualified context:
The latest matched control measured 84.76 decode tok/s, 1667.87 prefill tok/s and
1.34554 s TTFT; the original 82.79 qualification remains preserved. The user selected faster
generation despite slower prefill than PP2 W4A8. The normal route passed streaming,
tool calls, 29,434-input retrieval and a 39.62 s continuous-generation guard check.
The dense free-VRAM floor remains 512 MiB; swappiness 60 and visible terminals remain.

Earlier [PP/BF16 tuning](docs/SGLANG-TUNING-20261027.md),
[isolated W4A8](docs/SGLANG-W4A8-20261027.md),
[heterogeneous TP/MTP](docs/SGLANG-HETERO-MTP-20261028.md) and
[512 MiB retest](docs/SGLANG-MTP3-512MIB-20261028.md) evidence is preserved.
The machine still has 45.55 GiB usable RAM while one stick is temporarily removed;
MoE profiles have not been newly qualified on reduced RAM. HyperQwen's default
catalog selection and the user's saved DSH UI selection were not changed.

## Repository ownership

| Build | Private operational repository | Public reference |
|---|---|---|
| Windows NVIDIA | [windows-llm-nvidia](https://github.com/Biegle-W/windows-llm-nvidia) | [windows-llm-nvidia-public](https://github.com/Biegle-W/windows-llm-nvidia-public) |
| Linux NVIDIA | [linux-llm-nvidia](https://github.com/Biegle-W/linux-llm-nvidia) | [linux-llm-nvidia-public](https://github.com/Biegle-W/linux-llm-nvidia-public) |
| Linux AMD | [linux-llm-amd](https://github.com/Biegle-W/linux-llm-amd) | [linux-llm-amd-public](https://github.com/Biegle-W/linux-llm-amd-public) |
| Retired settings | [retired-llm-setting](https://github.com/Biegle-W/retired-llm-setting) | Private only |

The AMD repositories retain their original history and installed checkout paths;
their former GitHub names were `ubuntu-llm-amd` and `ubuntu-llm-amd-public`.
Historical settings belong only in the private retirement repository's current
tree. Previously published Git history is preserved, not rewritten.

## Contents

- `docs/MIGRATION-HANDOFF.md`: ordered migration, unlock, P2P, engine and client work.
- `scripts/native_linux_gpu_unlock.py`: pinned Ubuntu/Debian/GRUB preparation for
  the three intended GPU product IDs; explicit current Linux PCI addresses only.
- `scripts/test_native_linux_gpu_unlock.py`: host-only policy/rollback tests.
- `config/maintained-profiles.json`: one selected setting per model, weight quant and engine.
- `docs/MAINTAINED-PROFILES.md`: selected settings, speed/context tradeoffs and retirement pointer.
- `config/model-catalog.example.json`: pointer for the retired preparation-only inventory.
- `docs/REPOSITORY-MAP.md`: the seven-repository ownership and retirement policy.

Model aliases go under ignored `models/`; native builds/environments under `runtimes/`;
private inventories, mount mappings, credentials, captures and validation under
`data/`. Build native executables on Linux filesystems. Existing Windows model
weights can be reused after locating and verifying their files; never copy Windows
CUDA DLLs, UEFI payloads, AMD runtime configurations or old disk identifiers.

## Maintenance instructions

This README holds standing maintenance policy; [AGENTS.md](AGENTS.md) is the root
agent entry point and [CURRENT-STATE.md](docs/CURRENT-STATE.md) is the live takeover
handoff. Keep them, the benchmark ledger and both repositories current after
meaningful changes; another agent must be able to resume without chat history.
Keep all GitHub-facing prose,
code comments, messages and commits in English. Keep private/public repositories
current after validated changes, with nonpersonal commits and no force pushes.
Export selected sanitized files only; never export private history or state.

Before yielding after meaningful work, update the existing canonical takeover
handoff with the objective, selected versus candidate settings, completed checks,
actual blockers/failures, active jobs/locks, unfinished work and one concrete next
action. Verify both repository pushes, or record the exact outstanding publication
step. Preserve evidence and avoid competing copies of current runtime state.

Always preserve benchmark results and keep both Linux NVIDIA repositories updated.
After each benchmark, qualification, or maintained-setting change, save dated raw
results privately and update the relevant benchmark report and profile registry.
Record exact settings, engine versions, hardware, input/output lengths, repetitions,
prefill/TTFT and decode measurements, allocated context, tested input lengths, and
failures or limitations. Preserve historical measurements when replacing settings
or removing a model; recover saved evidence before repeating completed tests.
Publish sanitized results and settings to the public reference using
`scripts/sync_public.py`, review both diffs, commit and push both repositories,
and verify both branches match their upstreams. If publication is blocked, retain
the local results and report exactly what remains unsynchronized.

For every future benchmark result list, group all model/quant/engine entries in
this order: **VRAM-only models**, **MoE models with CPU RAM offload**, and
**MoE models with SSD streaming**. Keep empty categories visible and state that
none are currently kept. After model, quantization and engine, list these columns
in order: **prefill (tokens/s), time to first token (seconds), decode (tokens/s),
context limit (tokens), storage size (GB), storage location**. Include the physical
drive and checkpoint folder. Classify the selected runtime's actual weight access;
an SSD-streaming MoE with RAM/GPU caches remains in the SSD-streaming category.
See [benchmark reporting conventions](docs/BENCHMARK-REPORTING.md). Preserve
measurement dates, protocol, context qualifications and shared-weight accounting.

Create model and DSH shortcuts on the Desktop only; do not add application-menu
entries. Preserve unrelated application launchers.

Store only SSD-streaming models on NVMe. Put GPU/RAM-resident model weights and
dense trial checkpoints on the SATA SSD, using stable aliases under `models/`.
Check actual resolved weight files before launch or downloading new checkpoints;
see [the model storage policy](docs/STORAGE-POLICY.md). Keep engines and builds on
the Linux filesystem.

Use one maintained profile per model, weight quantization and engine. Select the
largest locally validated safe context with competitive prefill and decode;
record tradeoffs rather than claim one setting maximizes every metric. Keep
selected dense-engine arguments in `config/maintained-profiles.json` and private
MoE engine settings in their single canonical runtime configuration. KV precision,
draft count, chunk size and context variants do not create separate weight quants.
Record allocated context separately from tested input lengths. Keep numerical,
quality, memory, thermal and owned-process protections. Stop only owned inference
workers; preserve unrelated applications. Do not relax guards merely to load a model.

Normal inference workers allow loading and parked swap pages without a fixed
occupancy cap. Scope `MemorySwapMax=infinity` to the maintained guarded workers;
keep their selected RAM limits. Monitor owned active swap I/O/pressure, latch
unsafe stops and require explicit selection for reload. Keep the host swap-file size unchanged; global VM changes require separately
recorded approval and validation. The latest user instruction supersedes the earlier swappiness-10 trial approval:
keep host swappiness at 60; see CURRENT-STATE.md.

Dense models must keep model execution weights in GPU memory by default. Do not
use generic host-RAM weight offload to make them fit. An exception requires a
community fork with documented offload performance optimizations relevant to the
installed hardware; evaluate its evidence before testing, then validate locally
inside the bounded worker service. This restriction concerns dense-model weight
offload, not ordinary loading buffers or the existing MoE expert-streaming paths.

The [OS-level GPU unlock health checker](docs/GPU-UNLOCK-HEALTH.md) is installed
and enabled for package-update and boot events, independent of agents. Check
`gpu-unlock-health status --brief`; root-owned services save results and expose
failed/pending verification automatically. Both initial live audits passed.

GPU unlock persistence is a standing maintenance requirement. Whenever an agent
updates the kernel or NVIDIA driver, or resumes after either version changed, it
must automatically perform the [unlock update checks](docs/UNLOCK-SETUP-20261026.md#required-checks-after-kernel-or-nvidia-driver-updates),
record next-boot readiness, then verify actual unlock after the user reboots.
DKMS installation alone does not establish successful unlock on the new boot.
Report failures or pending reboot verification in CURRENT-STATE.md.

The user chooses when to reboot and switch OS. Do not repartition, flash VBIOS,
change firmware security, restore the removed Windows NVMe unlock or install a
blanket `targets=all` unlock through a documentation migration. Record fresh native
Linux baselines before unlock; test compute unlock, peer transfers and inference
independently. Adding a GPU or switch requires rediscovering topology and addresses.

Retire unused source/settings into the private archive with hashes, original path,
source repository, source commit, date and reason. Keep only a pointer in active
repositories. Preserve dated benchmark evidence and active regression fixtures.

Consult the [forum and primary-source trail](docs/FORUM-OPTIMIZATION-SOURCES.md)
when researching inference tuning. Distinguish community proposals and other
hardware from locally validated results, and cite direct post/article and upstream
implementation URLs beside source-derived claims.

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
silently through detached API commands. Completed harness and selector terminals close automatically after the command exits,
including failures. Private transcripts and exit-code receipts retain the results;
do not wait for Enter merely to keep a finished terminal open.

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
now backs the maintained qwen27b-sglang profile after the authorized deployment.

The [larger-context study](docs/SGLANG-CONTEXT-20261028.md) retains 32K: 38K and 36K
screens measured 1.7%/1.5% slower generation than a fresh 32K control, while 40K
failed full-KV capacity proof. No larger profile was promoted; precision, the
512 MiB reserve, swappiness 60 and all other guards remain unchanged.

The user now accepts proportional context/speed tradeoffs. 38K adds 18.75% context
for 1.70% measured fixed-input slowdown. Tool/near-window and sustained-resource
checks now pass, but normal reload backed only 37,501 KV tokens and blocked 38K
promotion; 32K remains deployed. The 600-second idle rule is enabled. Saved automatic
expiry proof covers HyperQwen; new SGLang was explicitly unloaded about 11 seconds
before its deadline, so timed expiry was not yet verified at that checkpoint; the subsequent shared-policy setup verified it. See
[the lifecycle evidence clarification](docs/OPERATIONAL-LIFECYCLE.md).

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
