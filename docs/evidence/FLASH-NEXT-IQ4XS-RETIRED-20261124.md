# Flash-Next UD-IQ4_XS router entry retired — November 24, 2026

At the owner's request `flash-next-iq4xs-strata` (Qwen3.8 Flash Next, Unsloth UD-IQ4_XS-v31 on Strata) was retired. `flash-next-strata` (IQ3_XXS) stays and remains the only Flash-Next entry.

## Why IQ3_XXS was kept

| | `flash-next-strata` (kept) | `flash-next-iq4xs-strata` (retired) |
|---|---|---|
| Latest short check (prompt reading / first token / generation) | 1,273 tok/s / 4.5 s / 69.5 tok/s | 989 tok/s / 6.3 s / 43.5 tok/s |
| 390-item quality test (macro) | 62.0% | 65.5% (intervals overlap) |
| Short tool-use test | 40.6 | 47.4 (within the ±17-point noise) |
| Weights on NVMe | 76 GB | 88 GB checkpoint + 1.4 GB pack |
| Engine | Qwen engine 0.1.65 | same; engine 0.1.66 failed this entry on its first prompt |

The larger quant was not measurably better and was about 40% slower at writing; keeping it also tied every Strata engine update to two presets.

## What changed

- Registry entry, launcher alias `qwen-iq4xs`, its preset checker (`scripts/flash_iq4xs_strata_runtime.py`) and pin file (`config/flash-iq4xs-strata-runtime.json`) removed, together with the branches for it in the router launcher, guards, update builders and daily-update config.
- Saved web-client selections of `flash-next-iq4xs-strata` move to `flash-next-strata`. The router answers `model_not_found` for the old id (`tests/test_flash_iq4xs_retired.py`).
- The router now lists nine text entries. Services restarted, DSH re-registered (9 models), router idle and unloaded, both GPUs at 1 MiB, GPU unlock VERIFIED. Unit tests: 576 pass.

## Weights

Not deleted. The UD-IQ4_XS-v31 checkpoint (`models/strata/models/unsloth-UD-IQ4_XS-v31`, about 88 GB) and its Strata pack (`models/strata/packs/unsloth-ud-iq4_xs-v31`, 1.4 GB), both on NVMe, are now listed as unused in `config/weights-inventory.json`. Under the standing storage rule they are deleted without asking when a new model needs the room. The MTP head and vision projector it shared stay with `flash-next-strata`.
