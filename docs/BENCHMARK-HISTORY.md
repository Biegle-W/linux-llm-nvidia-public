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
