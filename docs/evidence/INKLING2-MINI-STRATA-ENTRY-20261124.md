# Inkling 2 Mini back on Strata as a two-card 128K entry; llama.cpp entry retired — November 24, 2026

At the owner's request `inkling-strata` (Inkling 2 Mini, Strata SQ-10 pack) was added back, now on both cards with 131,072 tokens of context, and `inkling-llamacpp` (Unsloth llama.cpp build, UD-Q4_K_M, 32K) was retired.

## Setup

| | `inkling-strata` (new) | `inkling-llamacpp` (retired) |
|---|---|---|
| Weights | SQ-10 pack, 10.47 GB, NVMe (`models/strata/models/inkling-2-mini`), publisher revision `04996a1e`, SHA-256 matched | UD-Q4_K_M 17.25 GB with picture projector, SATA (kept on disk, unused) |
| Engine | `strata-inkling` 0.1.66 (Strata v0.2.20, `2e87c08db18a`) under control 0.1.66 | Unsloth llama.cpp build |
| Cards | both, `--layer-split auto` (`[cuda-ls 2 stages]`, all experts in VRAM, no P2P needed) | both |
| Context | 131,072 | 32,768 |
| Input | text | text and pictures |
| Thinking | hidden | always on |

Launch preset written by `scripts/inkling_strata_runtime.py --write-preset` (mode 0600, outside the repo) and checked against the registry and the pinned engine, weight and tokenizer hashes before every start. Saved web-client selections of `inkling-llamacpp` move to `inkling-strata`. The shared llama.cpp worker code went with the entry; no llama.cpp entry is left.

## Checks through the router

| Check | Result |
|---|---|
| Short DSH check (6,966-token prompt with tools) | tool call and follow-up pass; prompt reading 1,989 tok/s, first token 4.9 s, generation 66.2 tok/s; owned unload |
| Free VRAM when ready (3080 Ti / 3080) | about 5.9 / 4.1 GB |
| gBench chat-template check | 6/6, 5.6 s after an 8.4 s load |
| Short tool-use test (smaller-model limits, 15 min) | **59.3**: 36 of 40 single-turn items, 2 of 7 episodes reached (7 of 9), 11.5 min of items, 8 s load |

The llama.cpp entry scored 32 of 40 single-turn items and reached 1 of 9 episodes on the same test, because it always reasons. Trial numbers at long context (55-71 tok/s, 60K and 120K recalls correct) are in [ENGINE-UPDATES-20261123-STRATA-0220.md](ENGINE-UPDATES-20261123-STRATA-0220.md).

Not done: no multi-hour run and no request at the very top of the 131,072 window (the largest was 120.6K tokens in the trial).
