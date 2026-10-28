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
