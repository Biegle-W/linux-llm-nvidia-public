# Mix quality test (broad, short) — November 25, 2026

**Status: built, checked offline, and run live on all ten routes on November 26 ([results](evidence/MIX-TEST-LIVE-20261126.md)). Every route finished inside its limit, but the form is too easy to rank these models: all ten scored 85.6-97.2 and no pair is separated.** Asked for by the owner: a quality test that ranks models on a broad mix (knowledge, maths, code, following instructions, reasoning and some tool calls) and finishes in 15 minutes for smaller models and 30 minutes for larger ones. It was built by the council (Codex, Hermes, Agy and Claude Code as members, Claude as chair); every result below was checked by a second member. The ranking stays on the [short tool-use test](QUALITY-FAST-TEST-PLAN.md) unless the owner decides otherwise.

## The test

One fixed set of 36 items, the same for every model, in the same order:

| Category | Items | Source | Output cap | Hang guard |
|---|---:|---|---:|---:|
| Knowledge | 6 | MMLU-Pro (biology, economics, history, law, philosophy, psychology) | as stored | 120 s |
| Maths | 6 | MMLU-Pro maths | as stored | 180 s |
| Code | 5 | LiveCodeBench easy, run in the existing sandbox | as stored | 300 s |
| Following instructions | 7 | IFEval, short prompts with checks that need no extra libraries (3 with several instructions, 2 keyword, 2 format) | 4,096 | 90 s |
| Reasoning | 6 | BIG-Bench Hard: 2 navigation, 2 logical deduction (three objects), 2 Boolean expressions | 4,096 | 120 s |
| Tool calls | 6 | BFCL single turn: 2 parallel, 2 where no tool fits, 2 plain calls | as stored | 90 s |

- Items were drawn with a fixed seed (`mix-20261125`) from sorted IDs; no item was chosen by how models did on it. The list is frozen in a manifest with a hash (`0f684887…259d0`).
- Request settings are the harness's (temperature 0.6, top-p 0.95, same seed, thinking as served, one request at a time). The new instruction and reasoning items get 4,096 output tokens so thinking models still have room for a visible answer.
- Items alternate categories (knowledge, maths, code, instructions, reasoning, tools, then again), so a cut at the deadline removes a balanced tail.
- IFEval answers are checked strictly (every instruction must pass) with a port of Google's checks to plain Python; reasoning answers must be only the final answer (Yes/No, True/False or a letter; since scorer `mix-new-2`, November 26, a letter may be followed by that option's exact text, as in "(B) The pears are the second-most expensive", or the exact option text may stand alone; case and spacing are ignored and one trailing full stop is allowed). A truncated answer scores 0.
- **Maths and code are basic here.** MMLU-Pro maths and easy LiveCodeBench are nearly solved by every current model (14 of 15 and 9 of 10 unanimous in the stored runs); AIME and harder code take minutes per item and do not fit 15 minutes. The 390-item test stays the deep run for hard maths and code.

## Time limits

| Step | Smaller | Larger |
|---|---:|---:|
| Load, at most (longer = setup failure, no score) | 3:00 | 10:00 |
| Items, fixed budget after the model first answers | 11:00 | 19:00 |
| Report, wait for an idle server, clean-up | 1:00 | 1:00 |
| **Hard limit** | **15:00** | **30:00** |

Smaller: Qwen 27B routes, Flash-Next, Inkling and new models of that size. Larger: GLM, DeepSeek, Hy4. The larger load cap exists because Hy4 on Maya needs about 6.5 minutes to load; load time is never scored and a fast load does not add item time.

The hang guards stop stuck requests; they are set well above the slowest stored answers so a slow but correct model is not marked wrong (one stored DeepSeek Unsloth knowledge answer, 229 s, would hit its 120 s guard). A hit guard scores 0 and is reported. After a timeout the runner waits, inside the item budget, until the server is idle before sending the next item. Items cut by the deadline are left out, not scored wrong, and the report states coverage.

## Score

- Per category: correct out of scored, with a 95% Wilson interval.
- **Overall = mean of the six category accuracies, 0-100** (equal weight, so the many cheap tool items cannot decide the rank).
- **95% interval: about ±23 points** (conservative Hoeffding bound for 36 items in six groups; the usual normal figure is ±16). This is about as coarse as the tool-use test (±17): one run tells apart only models far apart.
- Pairs of models are compared on the items both answered with a paired sign-flip test (Holm-adjusted); pairs the data cannot order are reported as "not separated".

## First live runs (November 26)

| Route | Tier | Overall | Wall time | Limit |
|---|---|---:|---:|---:|
| `flash-next-strata` | smaller | 97.2 | 3:35 | 15:00 |
| `hy4-flash-strata` | larger | 94.8 | 9:05 | 30:00 |
| `deepseek-unsloth-strata` | larger | 94.4 | 9:51 | 30:00 |
| `hy4-flash-maya` | larger | 94.4 | 17:59 | 30:00 |
| `deepseek-maya` | larger | 91.7 | 10:55 | 30:00 |
| `inkling-strata` | smaller | 89.7 | 1:25 | 15:00 |
| `qwen27b-sglang` | smaller | 88.3 | 4:54 | 15:00 |
| `kolibri-llamacpp` | smaller | 86.1 | 4:48 | 15:00 |
| `glm-maya` | larger | 86.0 | 4:34 | 30:00 |
| `qwen27b-hyperqwen` | smaller | 85.6 | 6:17 | 15:00 |

All 36 items were scored on every route. No pair of routes is separated (smallest paired p = 0.125 before adjustment), so the order is observed scores only. 24 of the 36 items were answered correctly by all ten routes, which is why: maths, tools, knowledge and instruction items are close to saturated for current models. To rank, the form needs harder items in the same time (for example harder MMLU-Pro subjects, BBH tasks with five or seven objects, multi-step tool calls); that is the owner's decision. Per-category results, scorer amendment and RAM figures: [MIX-TEST-LIVE-20261126.md](evidence/MIX-TEST-LIVE-20261126.md).

## What stored answers already cover

Replaying the stored answers of earlier runs (no GPU time) covers 23 of the 36 items for the six current routes with full records (plus retired Bolt), and the 5 matching tool items for Inkling and both Hy4 routes. No stored answers existed for the 13 instruction and reasoning items, so before the live runs no overall score existed and every route needed one live run.

| Route | Knowledge | Maths | Code | Tools | Matched |
|---|---:|---:|---:|---:|---:|
| `deepseek-maya` | 5/6 | 6/6 | 5/5 | 6/6 | 23/36 |
| `deepseek-unsloth-strata` | 5/6 | 6/6 | 5/5 | 6/6 | 23/36 |
| `flash-next-strata` | 5/6 | 6/6 | 5/5 | 6/6 | 23/36 |
| `qwen27b-sglang` | 5/6 | 6/6 | 5/5 | 6/6 | 23/36 |
| `glm-maya` | 4/6 | 6/6 | 5/5 | 6/6 | 23/36 |
| `qwen27b-hyperqwen` | 5/6 | 6/6 | 4/5 | 5/6 | 23/36 |
| `inkling-strata`, `hy4-flash-strata`, `hy4-flash-maya` | — | — | — | 5/5 | 5/36 |

## Timing rehearsal

The real wrapper ran against a local fake server that replays each route's stored time per item (20 s assumed for the 13 new items); no GPU or router was used.

| Profile | Limit | Wall time | Items scored |
|---|---:|---:|---:|
| `flash-next-strata` | 15:00 | 6:52 | 36/36 |
| `qwen27b-sglang` | 15:00 | 8:21 | 36/36 |
| `qwen27b-hyperqwen` | 15:00 | 9:16 | 36/36 |
| `glm-maya` | 30:00 | 6:40 | 36/36 |
| `deepseek-maya` | 30:00 | 12:04 | 36/36 |
| `deepseek-unsloth-strata` | 30:00 | 14:09 | 36/36 |

The deadline cut, the outer kill timer and the stuck-server exit were also exercised. The live runs were faster than the rehearsal: the 13 new items took seconds on most routes, not the assumed 20 s.

## How it was built

Add-on folder `~/quality-eval-build/quality/mix/` beside the harness (outside this repository like the rest of it; no existing harness file changed): `prepare.py` (pinned downloads with checksums), `manifest.py` (frozen form), `ifeval_checks.py` and `checks.py` (scoring), `items.py`, `run_mix.py` and `mix.sh` (runner and limits), `score.py`, `replay.py`, `report_mix.py`, `NOTES.md`, and 54 unit and fake-server tests (all pass; the harness and fast-test suites still pass). Run: `mix/mix.sh MODEL small|large KEYFILE RUNID --select`; report: `python3 -m mix.report_mix --out DIR NAME=RUN_DIR ...`. Benchmark data stays on the server and is not committed.

Review caught and fixed: two drafts used 15-28 s per-item clocks (rejected: they measure speed, not quality) and only 22-25 items (±30 points); a race between two members left mismatched timing files; the reasoning scorer rejected lower-case letters; a stuck server after a cut was reported as a normal cut; after one timeout the runner gave up after 30 s of waiting and stopped DeepSeek at 13 of 36 items; and, found in the first live run, the reasoning scorer counted a right letter followed by its option text as wrong (8 answers on four routes, rescored from the stored answers).

Datasets: IFEval (Google, Apache-2.0), BIG-Bench Hard (MIT), plus the harness's MMLU-Pro, LiveCodeBench and BFCL.
