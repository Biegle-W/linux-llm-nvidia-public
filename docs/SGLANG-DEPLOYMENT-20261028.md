# Deployed SGLang TP2 + MTP3 W4A8 — October 28, 2026

The user selected the fastest tested SGLang generation configuration. The existing
`qwen27b-sglang` router ID, SGLang Desktop shortcut and DSH `nvidia-sglang` provider
now use the verified heterogeneous TP2/MTP3 runtime at **32,768 tokens**. There are
still six maintained profiles and one profile for this model/weight quant/engine.

The selected architecture measured 82.79 decode tok/s at 32K, versus 64.18 for the
prior 32K TP2 no-MTP control. The same architecture at 16K reached 84.63; retaining
the qualified 32K window follows the existing capacity preference. PP2 W4A8 has
faster prefill (3233.72 versus 1664.67 tok/s), so this is a user-selected generation
tradeoff, not an assertion that all metrics improved. The carried median TTFT is
1.34646 s. No completed three-request benchmark was repeated for deployment.
[Original measurements and method](SGLANG-MTP3-512MIB-20261028.md).

[Machine-readable deployment verification](benchmark-results/20261028-sglang-deployment.json).

## Active configuration

- Pinned `efschu/htsglang` commit 62271fd7c8aa8fe9edebf04e00a414b7fbf64388 plus the
  existing [qualified local patch](../scripts/patches/sglang-hetero-ct-w4a8-mtp.patch).
- TP2/PP1, physical ranks 3080 Ti/3080; base ratio 9:8 and aligned MLP ratio 10:7
  (10,240/7,168 channels), admission budgets 11,008/8,960 MiB.
- Decoder MLP-only W4A8; packed INT8 embedding/INT4 head, BF16 recurrent state/KV,
  one Mamba slot, chunk 384, one active request, decode CUDA graphs at batch 1,
  no prefix cache, no CPU weight offload. NEXTN/MTP3 verifies four tokens.
- Dense free-VRAM floor 512 MiB, host available floor 8 GiB, worker RAM 30/36 GiB,
  temperature 82°C, swappiness 60, unlimited worker swap occupancy and unchanged
  active swap/pressure/telemetry guards. NCCL P2P remains disabled.

## Stable runtime and startup checks

The source is copied unchanged from the qualified candidate to
`runtimes/sglang-hetero-62271fd/python/sglang`; caches are copied to
`runtimes/cache-sglang-hetero-62271fd`. Production no longer imports from a dated
trial directory. The native interpreter remains `runtimes/env-htsglang-62271fd`.
The older `env-sglang` remains an active read-only fallback for general Python
packages; do not delete it. Native dependencies take precedence in the new env.

[config/sglang-runtime.json](../config/sglang-runtime.json) pins the full source-tree
hash, patch hash, interpreter, paths and exact native/Python package versions.
The normal launcher verifies the tree and patch before starting, checks the loaded
module path and dependency versions, enables MLP W4A8 and clears the obsolete PP
partition override. Target/draft placement audits and a runtime receipt are saved
per user-service invocation under `data/router/sglang-placement/`.

The fork does not accept the old server-level default-template option. The router
now applies `enable_thinking=false` as a per-profile Chat Completions default when
omitted, matching the qualified requests. Explicit request overrides are preserved.
Streaming and non-streaming use the same defaults; three router regression tests
cover the default, explicit thinking override and invalid option types.

## Normal-path verification

The deployment coordinator and backend logs ran in visible terminals. All 50 CPU
checks passed: runtime integrity 6, router 22, benchmark accounting 7, supervisor 4
and swap guard 11. Through authenticated port 10100, verification passed streamed
JSON, a parsed `report_number(value=42)` tool call and 29,434-input three-marker
retrieval. The request deliberately omitted template kwargs to verify normal
router defaults. The existing DSH provider points to the same router/model ID;
its saved UI selection was preserved and no provider rewrite was required.

A continuous 4,096-output request completed in 39.62s and exercised
4 complete active swap windows. Maximum measured owned swap writes and
combined swap I/O were both 0 MiB/s; no guard violation occurred. This verifies a
short continuous run, not multi-hour stability or all possible tool behavior.

All 256 decoder rank/projection W4A8 audit entries, both draft completeness checks,
both packed-vocab sharing checks and all four GPU-only target/draft placements
passed. All four target/draft KV pools back 32,768 tokens. Source and runtime checks
confirmed the stable production copy, not a fallback engine.

Minimum sampled free VRAM: [759.0, 997.0] MiB (Ti/3080);
peak temperatures: [62.0, 49.0]°C. Minimum host available
RAM 32.26 GiB, peak owned RAM 7.36 GiB and swap 0.000 GiB.
Normal router unload/reload completed with a different owned invocation and the
same verified source, then passed JSON again. SGLang was left selected and ready
after this requested deployment; its ordinary
ten-minute idle unload still applies. No automatic HyperQwen restoration occurred.

## Rollback and preserved evidence

Four exact source/settings preimages were hash-verified and archived privately in
`Biegle-W/retired-llm-setting`, batch
`linux-nvidia/2026-10-28-sglang-tp2-mtp3-deployment`, commit 733820f. The active registry
contains a retirement pointer and preserved numerical history, not a parallel
runnable PP2 preset. Old dated benchmark and qualification reports are unchanged.
A rollback requires an explicit selection change, restoration of the matching
launcher/router/profile sources and verification under the current guards.

Raw API requests/events, terminal transcript, guard samples, runtime/placement
receipts, telemetry and rollback snapshots are private under
`data/sglang-deployment-20261028/`. No model download, weight change, driver update,
unlock change, clock change or swap-file change was performed.
