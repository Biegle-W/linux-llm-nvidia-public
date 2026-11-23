# Flash-Next on Strata 0.2.19: research and tuning — November 22, 2026

**Status: one setting adopted on both Flash-Next entries.** The owner noted that Strata 0.2.19 made Qwen3.8-Flash-Next much faster and asked for research and optimisation. The morning's update had shown only +4.5% generation on `flash-next-strata` and nothing on `flash-next-iq4xs-strata`.

## What was adopted

`STRATA_PREFILL_CPU_SHARE_AUTO=1` on `flash-next-strata` (UD-IQ3_XXS) and `flash-next-iq4xs-strata` (UD-IQ4_XS-v31). It lets the engine choose, from the measured PCIe link speed, how much of a prompt's expert work is staged through the CPU side; upstream turns it on by default only on its newest card generation.

| | IQ3_XXS before | after | IQ4_XS before | after |
|---|---:|---:|---:|---:|
| Prompt reading, 5.7K tokens (trial server, median of 3) | 1,386-1,388 tok/s | 1,639-1,640 (+18%) | 1,038-1,040 | 1,445 (+39%) |
| Prompt reading, 21.4K tokens | 2,293-2,311 | 2,348-2,350 (+2%) | 1,721-1,723 | 1,878-1,882 (+9%) |
| Whole request: 5.7K prompt and a 40-token answer (median of 6) | 4.6 s | 3.95 s | 6.05 s | 4.45 s |
| Generation, 400 tokens of prose | 85-90 tok/s | 88-90 | 69-74 | 69-72 |
| Generation, 700 tokens of code | 105-108 | 104-106 | 78-81 | 75-80 |
| Short DSH check through the router, prompt reading | 1,157 (morning) | 1,270-1,277 | 850 (morning) | 983-1,013 |

- **Generation is unchanged** within the run-to-run spread, which is large here (the first answer after a start is always the slowest: 63-78 tok/s against 86-106 later).
- **Answers are not bit-identical** to the old setting: the same weights are summed by a different route. No quality loss is expected and none was seen in the checks, but it was not scored.
- **Checks after the change:** 571 repository tests pass; three short DSH checks on each entry through the router pass (tool call, result, follow-up, owned unload).
- **Where it is set:** the registry entry's `selected_settings.environment` and the private launch preset, which the launcher compares. The earlier presets are kept in `data/flash-opt-20261122/` for rollback.

## Why the release's headline gain does not show here

A source review of 0.2.19 by four agents, each checked by a second one, found that most of the Ampere gain upstream reports (RTX 3090 and two A4000s: prompt reading +12% to +26%, generation +13% to +20%) is not reachable on a 10 GB + 12 GB layer split:

- The largest generation gain is enabled only when the main card has more than 16 GiB, and not across a layer split.
- Three changes need the lookup table memory-mapped; `flash-next-strata` reads it with direct I/O (chosen on November 10 for a faster load and 27 GiB less RAM).
- Upstream measured other weight files (IQ3_S, UD-Q4_K_XL, IQ2_XS).

The gain that does apply is real. With 0.2.19's new switches turned off as a control, `flash-next-iq4xs-strata` generated 62 tok/s against 69-74 with them on.

## Everything that was tried

Trial server on port 10052 outside the router, same memory limits, each variant a fresh start; three 5.7K-token prompts with 400-token answers, two 700-token code answers, one 21.4K-token prompt; temperature 0. Baselines were repeated four times (IQ3_XXS) and four times (IQ4_XS).

| Setting | IQ3_XXS | IQ4_XS |
|---|---|---|
| `STRATA_PREFILL_CPU_SHARE_AUTO=1` | **reading +18%**; repeated | **reading +39%**; repeated |
| the same with `STRATA_PREFILL_CPU_SHARE_NT=32` | no further change | no further change |
| the same with `STRATA_GRAPH_PRIO=1` | no further change | not run to completion |
| `--ple-io ram` (lookup table in RAM) | reading +2.6%, costs about 28 GiB of RAM; not adopted | not applicable |
| `--ple-io mmap` | no change | not applicable |
| `--adapt-async 1` | no change | no change |
| `STRATA_PF_FUSED=1`, `STRATA_PF_FUSED_Q50=1` | no change | no change |
| `STRATA_GRAPH_PRIO=1`, `STRATA_VHEAD_BITPLANE=1`, `STRATA_PREFILL_HELP=1` | within spread | not run |
| `--pipeline-windows 2` with `STRATA_MTP_STAGE0=1` | worse: prose 68 tok/s, 21K prompt -9% | worse: prose 64 tok/s, 21K prompt -7% |
| `--kv-resident 65536` | not applicable | slightly worse |
| `STRATA_QFUSE=0`, `STRATA_HC_Q8_TC=0` (controls) | no change | no change |
| `STRATA_SM86_PERF=0` (control: 0.2.19 switches off) | not run | generation -14% |

Three IQ4_XS starts in the repeat series did not come up within ten minutes. They followed the run that had loaded the 28 GiB table into RAM; the same variants started normally when rerun.

## Not done

- The DFlash2 drafter (not downloaded; Strata starts with MTP on both entries), larger prompt chunks for prompts above 8K, the settings that trade quality for speed (route tail skip and similar).
- No quality score was run after the change; the entries are not new weights.
