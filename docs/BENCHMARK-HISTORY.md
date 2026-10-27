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

VM60 queue checkpoint, 19:23 EDT: SGLang32K (.92 pool, chunks384) qualified at
2,613.82 prefill / .8532 s TTFT /46.59 decode. All four larger Flash screens
missed speed; Maya cache trials remain unsafe under active-write guards. The
approved VM10 experiment still awaits OS authentication; no VM10 results exist.
