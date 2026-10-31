# Benchmark ledger

## Latest: Unsloth Dynamic3.1 DeepSeek bounded trial — October 31

The pinned UD-IQ1_S candidate did not achieve a completed basic-quality pass; maintained selections are unchanged. The report records pinned sizes/hashes, the final-shard HTTP failure and Xet recovery, actual outcome and unchanged guards. [Results and limits](DEEPSEEK-DYNAMIC31-20261031.md).

## October 31: installed Bolt normal-router verification

Two fresh loads passed at 8K with exact near-window retrieval and sustained generation. The final shard-level clean mapping reclaim follows measured pressure and per-tensor scan failures. Normal and isolated speed observations remain separate from Maya’s three-request median. [Report](BOLT-MAYA-RELIABILITY-20261031.md).

## October 31: DeepSeek/Maya bounded residency and Bolt isolated qualification

DeepSeek/Maya passed its repeated speed screen, near-window checks, sustained generation and two reloads with explicit file residency and warming bounds. Bolt passed three fresh isolated 8K loads, JSON/arithmetic, 7,373-input retrieval and a sustained stream. Bolt was then unselected pending integration; the later normal-router result above supersedes that status. Earlier failures remain historical evidence. [Report](BOLT-MAYA-RELIABILITY-20261031.md), [numeric evidence](benchmark-results/20261031-bolt-maya-reliability.json).

## October 31: main-pair P2P optimization and auxiliary draft comparison

Both dense Qwen profiles now use qualified P2P communication. Fresh confirmation, near-window quality/resource checks and normal reloads passed. Three native profiles completed fresh fixed-fixture short measurements without cache/context retuning. DeepSeek/Maya stopped on its existing memory-pressure guard during repetition three; its partial two-repetition result did not replace the prior selected benchmark. Dedicated 3060 drafting was slower in the tested GGUF setup and was not selected. Prior records remain historical; native differences against older dates are not causal estimates. [Report](GPU-PAIR-AUX-OPTIMIZATION-20261031.md), [numeric evidence](benchmark-results/20261031-pair-main-aux.json).

## October 31: Nemotron INT4 startup rejection; no benchmark

Bolt real-weight offload loads failed RAM/VRAM guards; Super VL constructor gates failed layout/resources, and neither model completed SGLang startup. No speed or quality result replaces historical benchmarks. [Startup report](NEMOTRON-INT4-OFFLOAD-20261031.md), [evidence](validation-results/20261031-nemotron-int4-offload.json).

## October 29: bounded 15% pressure trial for two profiles

Qwen/Strata and DeepSeek/Maya now use 15% full-memory-pressure thresholds, up from 10%, with the same 30-second active window and three-sample stop rule. All other profiles retain 10%. The 128/160 MiB/s SSD swap limits and every independent RAM/VRAM/thermal/telemetry guard remain unchanged, as do contexts, weights, precision, runtime pins, expert caches, swappiness 60, concurrency 1 and idle 600 seconds. Both profiles completed a warmup and three valid 128-output measured requests without a guard violation. Only these two profiles were repeated. [Report](BENCHMARK-PRESSURE-GUARD-64GB-20261029.md), [numeric evidence](benchmark-results/20261029-pressure-guard.json). Prior 10% guard stops remain historical evidence.


## October 29: matched four SSD 128/160 swap-policy rerun

2 of four SSD profiles completed three valid measured requests without guard violations on restored 64GB RAM. RAM remains DDR5-4200 MT/s across four 16GB DIMMs (61.3013GiB usable; 2100MHz DDR clock). The dense profiles were not repeated; their table rows carry forward the earlier October 29 full-RAM run. All other settings/guards unchanged. [Report](BENCHMARK-SSD-SWAP-64GB-20261029.md), [numeric evidence](benchmark-results/20261029-ssd-relaxed-swap.json). Original saved fixtures reused; old results preserved.


## October 29: six-profile 64GB / DDR5-4200 screen

All six were attempted: five completed three valid fixed-fixture requests after a warmup; DeepSeek/Maya stopped at its swap-write guard and has no new speed median. Latest measured results are in [the full-RAM report](BENCHMARK-64GB-20261029.md); previous latest entries are retained under each profile's benchmark history. RAM configured speed4200MT/s was verified read-only through firmware DMI. No settings or guard were relaxed for the benchmark.

## October 29: full RAM restored without rebenchmarking

64GB hardware was confirmed and Linux verified 61.3013GiB usable. Full-RAM cache choices were restored and normal guarded load/JSON/reload checks passed. No new throughput measurement was produced; all earlier speed records retain their original hardware/cache scope. See [restoration](FULL-RAM-RESTORATION-20261029.md).

## October 29: Qwen mapped experts and daily update policy

Qwen Flash-Next passed 29,450-token retrieval and separate continuous generation of 8,192 outputs over 139.52s (58.71 client decode tok/s) plus fresh reload with Qwen-only relaxed swap limits. This is a different workload from the dated three-request benchmark, which remains unchanged. See [qualification](QWEN-RELAXED-SWAP-20261029.md). The [daily updater](DAILY-ENGINE-UPDATE-POLICY.md) was installed without running new GPU benchmarks or promoting an engine; future paired results go in [its ledger](DAILY-ENGINE-UPDATES.md).

Current settings live in the registry and [maintained-profile table](MAINTAINED-PROFILES.md).
Read [CURRENT-STATE.md](CURRENT-STATE.md) for active jobs and incomplete work.
Preserve dated raw/private evidence and numeric records; never rerun GPU tests
only to refresh documentation or publication.

| Date / scope | Evidence | Attribution |
| --- | --- | --- |
| October 26 stock and unlock comparison | [Saved comparison](BENCHMARK-UNLOCK-20261026.md) | Older 8K MoE settings, three requests/case, before/after reboot caveats; no current dense stock baseline. |
| October 27 dense engine optimization | [Dense report](DENSE-ENGINE-OPTIMIZATION-20261027.md) | GPU-only HyperQwen/SGLang, distinct code/prose and long-input fixtures. |
| October 27 six-profile matched run | [Full report](BENCHMARK-20261027-101219.md) | Approximately 2.2K input / 128 output, three requests; historical allocations/settings preserved. |
| October 27 MoE cache optimization | [Cache report](MOE-OPTIMIZATION-20261027.md) | GLM and both DeepSeek engines retested at unchanged contexts; current composite retained. |
| October 27 context expansion — in progress | [All trials and numeric progress](CONTEXT-EXPANSION-20261027.md) | Fresh controls, guarded candidate windows, actual near-window retrieval; user accepted GLM64K/StrataDeepSeek128K tradeoffs. No pending candidate is a deployed result. |

The context task also adds phase-aware swap-churn checks. Old benchmark records
retain their original policy; do not relabel them as full qualification under a
later guard. The unlock assessment uses existing evidence and adds no GPU test.

VM60 queue checkpoint, 19:23 EDT: SGLang 32K (.92 pool, chunks384) qualified at
2,613.82 prefill / .8532 s TTFT /46.59 decode. All four larger Flash screens
missed speed; Maya cache trials remain unsafe under active-write guards. The
approved VM10 experiment still awaits OS authentication; no VM10 results exist.

## Swappiness60 continuation — October 27

The user superseded the proposed VM10 trial: host swappiness remains 60.
A distinct Maya64 screen disables existing DS4_AHEAD speculative lookahead, with
24 GB load warming, post-prompt warming and Engram row cache disabled. One
measured 2,198-input/128-output request passed the active swap guard at
44.7 prefill tok/s, 49.1786 s TTFT and 3.80265 decode tok/s. Full confirmation and
near-window quality qualification remain pending; no production promotion.
Historical numeric hashes remain unchanged. See CURRENT-STATE.md.

## Partial context deployment at swappiness 60

Four qualified settings were applied: HyperQwen 56,320; SGLang 32,768; GLM 65,536;
Strata DeepSeek 131,072. Flash remains 32,768. Maya remains 32,768 and is explicitly
unresolved under the active-swap policy. Its lookahead-off 64K confirmation stopped
at 7.68287 MiB/s writes; the passing screen was not promoted. Native idle adapters,
600-second release and bounded lifecycle logging are deployed. Normal functional
and actual idle/reload verification are in progress; see CURRENT-STATE.md.

## Final lifecycle verification

All six normal guarded launches passed functional/context/readback checks. GLM
and dense actual 600-second expiry were observed at 610.44s and 610.53s. Strata
passed isolated 30-second expiry/reload; production remains 600. Fresh blue-image
reloads passed for GLM/Strata. Dense reload exposed a false telemetry latch during
intentional SIGTERM; the supervisors now stop sampling at requested shutdown.
74 CPU checks passed, then a real normal stop and API auto-reload passed with no
latch and HyperQwen restored. Unexpected telemetry loss remains guarded. The
original timed expiry and its initial reload failure are preserved, not repeated
or silently relabeled. Maya sustained-swap qualification remains unresolved.

## Automatic unlock-health monitoring — October 27

Root-owned boot/update checks are installed and enabled, independent of agents.
Current kernel 7.0.0-38-generic/NVIDIA 595.99.02 passed DKMS, five firmware assets,
boot-image/GRUB and both pre-NVIDIA unlock records. All 103 CPU tests passed; no
new compute or LLM benchmark was run and no inference setting changed. This is
configuration/boot-persistence evidence, not a new measured performance result.
The initial module-visibility sandbox error was corrected and its preimages
archived; live service results now pass. See GPU-UNLOCK-HEALTH.md.

## SGLang pipeline and recurrent-state study — October 27

[Four isolated trials](SGLANG-TUNING-20261027.md) used unchanged 32K context,
.92 memory fraction, chunk384, CUDA graphs and swappiness60. Fresh 32/32 FP32
control: 2672.75 prefill / .8320 s TTFT / 46.45 decode. BF16: 2656.12 / .8374 /
46.87; both passed JSON, arithmetic and 29,434-input retrieval. 34/30 and 36/28
failed the existing GPU-headroom checks. Preserve the failed/partial trials;
no candidate was promoted and HyperQwen remains default.

## Isolated SGLang MLP W4A8 — October 27

[Final compressed-tensors candidate](SGLANG-W4A8-20261027.md), on temporarily
reduced RAM (45.55 GiB usable), activated all 128 intended MLP projections.
Fresh matched three-request medians: W4A16 2659.91 prefill / .83394 s TTFT /
46.3513 decode; W4A8 3233.72 / .687705 / 45.6912. Prefill +21.57%, TTFT -17.54%,
decode -1.42%. Both passed JSON, arithmetic and 29,434-input retrieval. Eighteen
standalone kernel cases passed on both GPUs. The first adapter was rejected
with zero activated layers before its benchmark; initial control/diagnostics
remain preserved. No production setting changed; HyperQwen remains default.

## Heterogeneous SGLang TP2/MTP — October 28

[Isolated pinned-fork study](SGLANG-HETERO-MTP-20261028.md), with the accepted
MLP W4A8 tradeoff, 45.55 GiB usable RAM and unchanged guards. Completed 32K
BF16/one-slot TP2 control: 1716.45 prefill / 1.2947 s TTFT / 64.18 decode;
+40.46% decode versus the prior PP2 W4A8 reference, with 46.92% slower prefill.
Matched 16K control: 1712.66 / 1.3001 / 63.87. Corrected MTP1: 1662.17 /
1.3454 / 70.25 (+10.00% decode); MTP3: 1662.79 / 1.3475 / 84.63 (+32.51%).
These complete trials passed JSON, arithmetic and near-window retrieval.
Corrected MTP1 at 32K measured 69.59 decode on short prompts but failed the
headroom guard during long retrieval (990 MiB sampled free); it is unqualified.
Initial MTP draft-fusion weights were skipped by the fork; zero-acceptance
measurements are invalid diagnostic evidence, not an MTP performance result.
The corrected loader audits all required draft parameters. Eighteen GPU kernel
cases, eight packed-shard checks, three candidate regressions and seven metric
regressions pass. No production profile was changed. See the report for every
startup/capacity failure, exact settings, final capacity checks and limitations.

Corrected MTP3 at 32K failed the immediate post-load GPU-free check: 904 MiB
on the 3080 Ti and 1,039 MiB on the 3080. No throughput was accepted for it.
The completed 16K retrieval checks used 14,686 input tokens.

October 28 operational update: visible backend/harness terminals are required;
future isolated tests finish idle rather than automatically restoring HyperQwen.
Nineteen router regressions passed in a visible terminal. No benchmark values changed.

## 32K SGLang MTP3 with user-approved 512 MiB floor — October 28

[Visible retest](SGLANG-MTP3-512MIB-20261028.md): 1664.67 prefill / 1.34646 s TTFT /
82.7856 decode, three requests at 32K. JSON, arithmetic and 29,434-input retrieval
passed. Minimum sampled VRAM free 802/997 MiB; RAM and swap guards unchanged,
swappiness 60. Prior 1 GiB failures remain historical. The previous 32K TP2 no-MTP
control was not repeated; descriptive decode gain is about 29.0%. No sustained-load
claim or production engine promotion. Visible cleanup finishes idle, not HyperQwen.

## SGLang production promotion — October 28

[Deployed TP2/MTP3 W4A8 at 32K](SGLANG-DEPLOYMENT-20261028.md) under explicit user
authorization. The earlier 512 MiB retest median 1664.67 prefill / 1.34646 s TTFT /
82.79 decode is carried forward, not remeasured. PP2 W4A8 remains faster for
prefill, but the user selected generation speed and the larger qualified window.
Normal-router streamed JSON/tool call, 29,434-input retrieval, a 4,096-output, 39.62 s
continuous request and normal unload/reload passed. Four active swap windows had
zero I/O; all 50 CPU regressions passed. Runtime/source pins, rollback pointer and
current grouped measurements are updated. No other model profile changed.

## SGLang context screening — October 28

[Fresh 32K control and larger allocations](SGLANG-CONTEXT-20261028.md): control
1667.87 prefill / 1.34554 s TTFT / 84.7639 decode, with tool, JSON/arithmetic and
29,434-input retrieval passed. At 38,912, 83.3212 decode (-1.70%); at 36,864, 83.5018
(-1.49%). Both failed the initial no-generation-loss gate and did not undergo
long-window qualification. The 40,960 setting backed only 40,760 KV tokens and was
rejected before timing. No confirmation or benchmark retries followed. Keep 32K;
other settings unchanged. All runs were visible under reserve 512 MiB/swappiness 60;
cleanup finished idle. Small differences include normal timing variation and do
not prove a permanent architectural limit. Original numeric evidence is preserved.

October 28 operational policy update: shared 600-second idle release now applies to
all six profiles and survives reinstall/normal CLI launch. Real SGLang automatic
expiry and subsequent normal reload passed in visible terminals. No performance
benchmark, context or numerical setting changed; see ALL-ENGINE-POLICY-20261028.md.


## SGLang 38K qualification and rollback — October 28

[Missing quality/resource checks completed](SGLANG-38K-QUALIFICATION-20261028.md).
34,964-input retrieval, 35,063-input history, JSON/arithmetic and tool roundtrip passed.
A 34,973-input/3,072-output stream completed in 163.28 s (135.81 s continuous generation),
with zero worker swap/I/O and minimum sampled free VRAM 560/795 MiB. The original
38K 83.3212 versus 32K 84.7639 fixed-input medians were carried, not rerun.
Normal-router retrieval/reload worked, but the reload backed only 37,501 of 38,912
advertised tokens. Promotion was rejected; 32K was restored in router/harness/DSH
with defaults preserved. 39 CPU tests passed after an old visible-console fixture
was corrected. Final state idle; reserve 512 MiB, swappiness 60 and all guards unchanged.
The saved fenced-JSON answer was correctly parsed without retrying passed quality
checks; an unfinished sustained test resumed. Raw failed/successful evidence remains.


October 28 engine ownership/console update: a functional SGLang→HyperQwen switch
and API smoke passed without a performance benchmark. Existing speed results and
32K/38K qualification attribution remain. 53 engine/ownership CPU regressions and protected-harness
checks passed; see ENGINE-SWITCHING-20261028.md. Final state idle, all guards unchanged.


October 28 terminal correction: engine/router/harness/test consoles now start visible
but minimized. Live initial-iconic/non-activation checks and a normal SGLang Desktop
API smoke passed. This is presentation/ownership verification, not a new speed result.


October28 router update:94 CPU lifecycle/admission/guard checks and two sequential
32-token SGLang transport smoke requests passed. No speed, near-window or GPU
concurrency benchmark was run. One-slot engine limits and all qualified settings
remain; the router now fairly queues API clients. See ROUTER-IMPROVEMENTS-20261028.md.


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
