# Flash-Next UD-IQ4_XS-v31 trial, November 17–18, 2026

Trial of `unsloth/Qwen3.8-Flash-Next-GGUF`, quant `UD-IQ4_XS-v31` (repository revision `f5d175de2cf7`), against the
installed `flash-next-strata` profile (UD-IQ3_XXS). Same engine binary for both: Strata engine 0.1.60.

Status: **trial only**. No router profile, registry entry or installed preset was added or changed. The trial was
served outside the router in a temporary user service capped at MemoryHigh 87 GiB / MemoryMax 89 GiB, so the
router's swap and VRAM guards did not apply to it.

## Setup

- Plan check (`strata launch --plan`): passed; 128K context, both cards, MTP reused, all experts in RAM.
- Download: four shards, 93,672,359,738 bytes (87.2 GiB), on NVMe at
  `models/strata/models/unsloth-UD-IQ4_XS-v31`; SHA-256 of every shard matches the publisher's values.
- The launcher resolved engine 0.1.50 from Strata's own component folder and refused ("needs engine 0.1.57 or
  newer"). The trial pointed `STRATA_COMPONENTS_DIR` at a hard-linked copy of the manual 0.1.60 package.
- Serving settings used for the scores: the launcher's automatic layout (layers 0–19 on the RTX 3080,
  20–47 on the RTX 3080 Ti, KV streaming with 32,768 of 131,072 cells in VRAM, 15 pool workers), one slot,
  thinking off, 131,072 context.

## Load and memory

| Measure | UD-IQ4_XS-v31 | Installed UD-IQ3_XXS |
|---|---|---|
| Ready after | 28–46 s | 29 s |
| Expert weights in RAM | 56.24 GiB | — |
| VRAM used (3080 Ti / 3080) | 11.3 GB / 9.35 GB | — |
| VRAM left free (automatic layout) | 711 MiB / 804 MiB | — |
| Service memory peak incl. file cache | 81.1 GiB over the 390-item run | — |
| Swap peak | under 5 MiB | — |

## Speed

One cold 19,956-token prompt, 300 tokens written, engine log figures. Baseline measured the same day through the router.

| Setup | Prompt reading (tok/s) | Writing (tok/s) | Time to first token |
|---|---|---|---|
| Installed UD-IQ3_XXS | 2,149–2,239 | 86–94 | about 9.0 s |
| UD-IQ4_XS-v31, automatic layout | 1,582–1,602 | 84–89 (64–67 on the first request) | about 12.5 s |
| UD-IQ4_XS-v31, installed profile's layout (split 29) | 1,611–1,649 | 61 (49 on the first request) | about 12.3 s |

Short prompts, measured inside the 390-item run (median writing speed, tok/s; baseline from November 11):

| Benchmark | UD-IQ3_XXS | UD-IQ4_XS-v31 |
|---|---:|---:|
| MMLU-Pro | 109.0 | 80.5 |
| AIME | 128.2 | 93.6 |
| LiveCodeBench | 117.5 | 84.6 |
| BFCL single | 126.6 | 87.3 |
| BFCL multi | 122.9 | 85.2 |
| Whole run | 117 min | 169 min |

## Quality (frozen 390 items, temperature 0.6, top-p 0.95, thinking off)

| Benchmark | UD-IQ3_XXS (Nov 11) | UD-IQ4_XS-v31 | Only old right / only new right |
|---|---:|---:|---:|
| MMLU-Pro | 179 / 210 | 184 / 210 | 8 / 13 |
| AIME | 22 / 30 | 24 / 30 | 2 / 4 |
| LiveCodeBench | 35 / 60 | 35 / 60 | 3 / 3 |
| BFCL single | 44 / 60 | 47 / 60 | 3 / 6 |
| BFCL multi | 6 / 30 | 7 / 30 | 3 / 4 |
| Equal-weight macro | 62.0% | 65.5% | |

Paired bootstrap, 95% interval for the macro difference (new minus old): −2.0 to +8.9 points. The interval
includes zero and no single benchmark separates (smallest exact p 0.38), so the 3.5-point lead is not established.

Notes on the comparison:

- The harness's pairing hash covers the base URL. The trial was served directly (port 10050) and the baseline
  through the router (port 10100), so the stock report found no shared items. Rows were paired in a derived
  folder only where the item, scorer version, request options and first messages were identical (all 390).
  Raw runs were not modified.
- The baseline was run six days earlier with a different harness file hash; scorer version, token limits and
  sampling settings match.
- A second agent (codex, GPT-6.1 Sol) recomputed the counts, macro, discordant pairs, interval and timing
  medians from the raw rows and confirmed them.

## Not tested

- Requests near the full 131,072-token context, and sustained load.
- Serving through the router with its guards (the trial was not a router profile).
- Whether the automatic layout would also change the installed UD-IQ3_XXS.

Datasets, items and raw answers stay on the server outside the repository.
