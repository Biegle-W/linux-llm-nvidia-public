# Unused model and preparation cleanup — October 27, 2026

Removed **102.89 GB** of unused downloads and
preparation artifacts after dependency checks and the screening below. All six
maintained model/quant/engine profiles remain available, with unchanged settings,
contexts and kept benchmark values. The registry is byte-for-byte unchanged.
[Numeric screening, removal and validation evidence](benchmark-results/20261027-dspark-screening.json).

## Decisions from saved evidence

NInfer-3090 already refused the unequal 80/68-SM cards. FreeToken/NVFP4 refused
available-VRAM imbalance. DFlash2 already failed its cache-capacity guard; SGLang's
pinned PP route prohibits speculation. Those completed failures were not rerun,
and no admission, numerical or offload safeguard was relaxed to retain downloads.
The larger AutoRound base and fast-head source are preparation inputs already
incorporated into the standalone selected checkpoint, rather than independent
new candidates. The AWQ trial checkpoint has no qualified competing result.
See the preserved [engine tests](ENGINE-TESTS-20261026.md) and
[dense optimization](DENSE-ENGINE-OPTIMIZATION-20261027.md).

## New DSpark screening

DSpark had been explicitly disabled without a saved local speed calibration. It
was therefore tested in both DeepSeek engines before deciding whether to remove
its files. Each candidate retained the selected context, quality/expert count,
cache environment and worker budget. One 64-token warm-up preceded one measured
128-token request using the saved approximately 2.2K fixture. Loading is excluded.
Kept comparisons are the existing three-run medians. A competitive screening
candidate would receive three-run confirmation plus quality checks; a rejected
single request is not a new qualified deployment or a confidence interval.

### VRAM-only models

No fresh speed tests. Saved compatibility failures and superseded preparation
assets informed removal; the active HyperQwen/vLLM and SGLang checkpoints remain.

### MoE models with CPU RAM offload

None currently kept.

### MoE models with SSD streaming

The rows below are historical DSpark candidates, not current kept settings.

| Model / quant | Engine | Prefill (tok/s) | Time to first token (s) | Decode (tok/s) | Context limit (tokens) | Storage size (GB) | Storage location |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| DeepSeek-V4.1-Flash-1017 / Maya-S + DSpark | Maya | 43.1 | 51.033 | 2.28 | 32,768 | 339.48 base + 7.97 draft | CT1000P3PSSD8 NVMe: `models/maya/DeepSeek-V4.1-Flash-1017-GGUF/` |
| DeepSeek-V4.1-Flash-1017 / Maya-S + DSpark | Strata | 30.5 | 72.054 | 2.44 | 65,536 | 339.48 base + 7.97 draft | CT1000P3PSSD8 NVMe: `models/maya/DeepSeek-V4.1-Flash-1017-GGUF/` |

- Maya: screened decode 2.28 versus kept 4.08 tok/s; TTFT 51.033 versus 44.017 s. Rejected at screening.
- Strata: screened decode 2.44 versus kept 2.87 tok/s; TTFT 72.054 versus 67.527 s. Rejected at screening.

Prefill uses native engine timing; decode uses client SSE throughput. Samples,
reused-prompt counts and exact budgets are in the numeric record. No page-cache
flush or randomized order was used. The full context windows were not retested.
Current kept results remain in the [MoE optimization report](MOE-OPTIMIZATION-20261027.md).

## Removed files and active dependencies

| Removed artifact | Drive | Size (GB) |
| --- | --- | ---: |
| `models/engine-tests/qwen38-27b-awq` | SATA | 21.04 |
| `models/engine-tests/qwen38-27b-nvfp4` | SATA | 21.95 |
| `models/engine-tests/qwen38-27b-w4a16-base` | SATA | 23.13 |
| `models/engine-tests/qwen38-27b-ninfer` | SATA | 20.44 |
| `models/engine-tests/qwen38-dflash2-w4a16` | SATA | 1.28 |
| `models/engine-tests/qwen38-fast-head-source` | SATA | 0.98 |
| Flash-Next raw MTP tensors, intermediate GGUF and preparation metadata; `mtp/rt` retained | NVMe | 6.10 |
| `models/maya/DeepSeek-V4.1-Flash-1017-GGUF/dspark` | NVMe | 7.97 |

Logical bytes include package metadata and base-checkpoint backups. Small source,
configuration and provenance records were preserved privately without retaining
the removed weight payloads. This is a model-artifact cleanup; installed engines,
source trees, build environments and active numerical regression fixtures remain.

Flash-Next retains its converted `models/strata/mtp/rt` draft pack. The intermediate
MTP GGUF, raw BF16 tensors and fetch inventories are unnecessary at runtime.
The standalone dense fast checkpoint remains on SATA; all active streamed weights,
vision weights, generated dense packs and expert profiles remain on NVMe.

DeepSeek's pack loader opens every file listed in `tensors.txt`, even when drafting
is disabled. Removing the DSpark payload therefore also requires removing its
unused `mtp.*` tensor records and compacting file IDs in both generated pack
indexes. Every retained tensor was checked to preserve its original dtype, source
file name, byte offset, length and shape; vision remains referenced correctly.
Original indexes, hashes and exact changes are preserved privately. No native
engine code, model quantization or context setting was changed.

## Post-cleanup validation and preservation

Files were first moved into same-drive quarantine. All six profiles then loaded
fresh through the router and passed authenticated arithmetic/JSON checks and
unauthenticated-access rejection. Exact worker memory/swap budgets were checked.
Maya DeepSeek also passed a real 1024 × 1024 red-image check after index remapping.
All 34 local CPU regression tests passed. Only after the model checks passed
were the quarantined payloads permanently removed.
HyperQwen was restored; router and DSH remained active and the owned GPU lock was
removed. A fresh authenticated stream through the router also passed after
permanent deletion. These checks validate function; the saved speed suite was
not repeated.

All **1,038 historical raw evidence files** retained their recorded size and
modification time, and all **11 benchmark reports/numeric result files** retained
their SHA-256. Previous speed
results and retrieval qualifications remain dated and unchanged. Shared active
weights, configuration and profile count are preserved. Private manifests,
metadata snapshots, screening SSE and telemetry, index preimages, deletion records
and functional responses are under `data/model-cleanup-20261027/`.
