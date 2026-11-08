# Flash-Next Strata hand-set layer split — November 7, 2026

`flash-next-strata` (Qwen3.8-Flash-Next GSQ-RCO IQ3_XXS, Strata 0.2.11 / engine 0.1.57) now runs a hand-set two-card
split instead of `auto`:

| Setting | Before | Now |
|---|---|---|
| `gpu` (PCI order) | `[0, 1]` | `[1, 0]` with `"gpu_order": "as_given"` |
| `layer_split` | `auto` (chose K=20) | `"29"` |
| `--trim-stage-weights` | off | on |

Layers 0-28 run on the RTX 3080 and layers 29-47, the output head, the draft layer and the verify run on the RTX 3080 Ti.
Each card loads only its own layers' dense weights, so the 3080 Ti's expert cache grows from 2,325 slots (4.16 GiB) to
3,402 slots (6.41 GiB). `scripts/serve_router_moe.py` refuses a Flash-Next launch whose preset card order, split or trim
differs from `config/maintained-profiles.json`; the updater's preset rewrite only replaces executable paths, so these
fields survive engine updates.

## Short sweep (isolated, port 10004, production config except split)

Means over repeated arms; full rows in `docs/validation-results/20261107-strata-layer-split.json`.

| Arm | Tool prompt read (5.7K) | 24K prompt read | Writing (400 tokens) |
|---|---|---|---|
| auto (K=20, 3080 Ti last), 2 runs | ~1,134 tok/s | 1,981 tok/s | 101.7 tok/s |
| K=20 trim, 3080 Ti first | 1,173 | 1,859 | 102.9 |
| K=20 no trim, 3080 Ti last | 1,167 | 1,981 | 102.3 |
| K=23 trim, 3080 Ti last, 2 runs | ~1,225 | ~2,415 | ~110.5 |
| K=26 trim, 3080 Ti last | 1,192 | 2,504 | 111.0 |
| **K=29 trim, 3080 Ti last, 2 runs** | **~1,244** | **~2,412** | **~115.4** |
| K=32 trim, 3080 Ti last | 1,177 | 2,258 | 110.5 |
| K=35 trim, 3080 Ti last | 1,156 | 2,135 | 109.9 |

Every arm made the correct `run_shell` tool call and returned all three retrieval markers in order. Peak free VRAM stayed
about 730-820 MiB per card; worker RAM stayed within the existing 87.77/89.77 GiB limits. Trim and the 3080 Ti as last
card are both required: either alone did not beat `auto`.

## Guarded router check

`daily_engine_update.py --smoke-current flash-next-strata` passed the short DSH tool/result/follow-up with owned unload:
**1,022.7 prefill tok/s, 6.00 s TTFT, 73.8 decode tok/s** (5,594-token prompt, 40 output tokens). The same check under
`auto` earlier the same day measured 924.0-940.9 prefill and 69.4-71.3 decode. GPU unlock was VERIFIED before every run.

## Limits

Short runs only; no sustained, full-context (131,072) or image re-qualification was run for the new split. The IQ1_M
Strata entry keeps `auto`. Strata 0.2.12 was rejected by the same day's paired gates (IQ1_M decode and DeepSeek cache
mismatch) and is not part of this change.
