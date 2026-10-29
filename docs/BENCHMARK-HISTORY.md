# Benchmark ledger

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
