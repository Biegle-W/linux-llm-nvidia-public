# Fast quality test plan (tool use first) — November 22, 2026

**Status: built, replayed on stored records, and run live once (Inkling 2 Mini, November 22).** Asked for by the owner: the 390-item quality test takes 2 to 10 hours per model; the new test must finish in 15 minutes for the smaller models and in 1 hour at most for the larger ones, and put tool use first. The scores and times below come from the stored records of the existing runs on the chosen items; nothing was run on the GPUs for them.

## The ranking (owner's decision, November 24)

This test is now the quality ranking on the website and in the README; the 390-item test is archived and no longer ranks models. To keep one standard, every model is ranked on the same 49 items (40 single-turn, 9 common episodes) with score = 50 × (single-turn accuracy + episode pass rate). Larger models still run the 6 extra episodes, which are reported but not used for the ranking. Each score gets a 95% interval (normal approximation over both parts); with one run no model is separated from another. The table the website reads is [WEBSITE-SUMMARY.md](WEBSITE-SUMMARY.md).

## Live rerun of every route (November 24-25)

At the owner's request every enabled route was rerun live through the router; the ranking now uses these runs, and the replay table below is history. Results and the comparison with the earlier scores: [SHORT-TEST-RERUN-20261124.md](evidence/SHORT-TEST-RERUN-20261124.md). One change to how it was run: `hy4-flash-maya` needs about 6.5 minutes to load, so its run used `--load-cap 600` (load time is not scored).

## Shared with the AMD server (November 26)

Owner, November 26: both servers run the same models and benchmarks. The frozen item list `fast/manifest.json` (version `fast-1`, sha256 field `b29b71cd…5e69f9`) is now also committed in [`benchmarks/shared/tooluse-short-manifest.json`](../benchmarks/shared/README.md), byte-identical in both repos; the AMD runner takes its 55 items from there. AMD had drawn other items until then (none of its 55 matched), so AMD scores from before November 26 are not comparable with these. Nothing changed in the harness here. `python3 benchmarks/shared/check_shared.py --server nvidia` checks that the harness manifest still matches the shared list.

## When it runs

Owner's rule, November 22: the test is run **only for new models and new weights**. Nothing that already has stored records is run again; the eight ranked models are scored on this test from their stored records. The 390-item test is no longer the routine test.

## The test

Tool use only. Every item comes from the tool-calling parts of the current test (BFCL v4), with request settings unchanged (temperature 0.6, top-p 0.95, same seed, thinking as served, 2,048 output tokens per request, one request at a time). Because nothing about the requests changes, the stored records of the eight ranked models already answer the new test: its first ranking costs no GPU time.

| Part | Items | Smaller models | Larger models |
|---|---|---:|---:|
| Single turn: parallel calls | all 15 current | 15 | 15 |
| Single turn: no tool fits, must not call | all 15 current | 15 | 15 |
| Single turn: one plain call | 10 of the current 15 | 10 | 10 |
| Multi turn: base episodes | seeded draw from the current 10 | 3 | 5 |
| Multi turn: a parameter is missing | seeded draw | 3 | 5 |
| Multi turn: a function is missing | seeded draw | 3 | 5 |
| **Total** | | **49** | **55** |

- **Smaller models** (Qwen 27B, Flash-Next, trial models of that size) run the 49 core items. **Larger models** (GLM, DeepSeek) run the same 49 plus 6 more multi-turn episodes.
- The draw uses seed 20261122 on sorted item ids and never looks at results. The item list is frozen in a manifest with a hash.
- Dropped from the tool parts: the "choose among several functions" subset, where every model scores 87-100% and little is learned.
- Dropped entirely: MMLU-Pro, AIME 2025 and LiveCodeBench. They are 84-89% of today's run time and are not tool use. The 390-item test stays as the deep run, on request.

**Score** = 50 × (single-turn correct ÷ 40) + 50 × (multi-turn episodes passed ÷ 9), out of 100. Larger models also get a second figure with 15 episodes, used only between larger models. Multi-turn carries half the weight because that is where the models differ (single turn: 70-90% for all; multi turn: 11-44%).

## Time limit

| Step | Smaller | Larger |
|---|---:|---:|
| Model load, at most (longer = aborted as a setup failure, no score) | 3:00 | 3:00 |
| Items, fixed budget after the model answers a first request | 11:30 | 56:00 |
| Report | 0:30 | 1:00 |
| **Hard limit** | **15:00** | **60:00** |

- The item budget is a deadline inside the harness; the whole run also sits under an outer kill timer, so a hung harness still ends on time.
- Order: all 40 single-turn items first, then multi-turn in triplets (base, missing parameter, missing function). A cut therefore removes a balanced tail.
- An item cut by the deadline is not scored as wrong; it is left out, and the report states coverage (for example "9 of 9 episodes" or "6 of 9"). Two models are compared on the items both completed.
- The item budget does not depend on how long the load took, so a slow load cannot change the score.
- Per-item timeouts are the same for both groups (120 s single turn, 480 s per episode), so a result means the same thing in either group. A timeout counts as wrong and is reported separately.
- After a cut the harness waits until the server is idle again before it lets go of the GPUs.

## Replay on the stored records

| Model | Group | Single turn | Episodes | Score | Item time | With a 3-minute load |
|---|---|---:|---:|---:|---:|---:|
| `qwen27b-hyperqwen` | smaller | 35/40 | 4/9 | 66.0 | 8.6 min | 11.6 |
| `qwen27b-sglang` | smaller | 36/40 | 3/9 | 61.7 | 10.4 min | 13.4 |
| `flash-next-iq4xs-strata` (retired Nov 24) | smaller | 29/40 | 2/9 | 47.4 | 7.3 min | 10.3 |
| `flash-next-strata` | smaller | 28/40 | 1/9 | 40.6 | 5.1 min | 8.1 |
| `deepseek-unsloth-strata` | larger | 34/40 | 4/9 (8/15) | 64.7 (69.2) | 46.3 min | 49.3 |
| `deepseek-maya` | larger | 33/40 | 4/9 (6/15) | 63.5 (61.2) | 47.4 min | 50.4 |
| `glm-maya` | larger | 35/40 | 3/9 (4/15) | 60.4 (57.1) | 18.9 min | 21.9 |
| `bolt-llamacpp` (retired) | larger | 34/40 | 2/9 (3/15) | 53.6 (52.5) | 9.7 min | 12.7 |

Figures in brackets are the 15-episode score for larger models. Item times are the sums of the recorded seconds for exactly these items.

- **Every ranked model fits.** The tightest is `qwen27b-sglang`: 10.4 minutes of items against an 11.5-minute budget. A slow day would cost it the last episode or two, which the coverage figure would show.
- **Order is close to the 390-item ranking** at the ends: Qwen and DeepSeek on top, Flash-Next at the bottom. GLM moves up and Flash-Next down because the parts they were strong in (knowledge, code) are gone.
- **Always-reasoning models do not fit.** Inkling 2 Mini's stored run needs 44 minutes for the core on the slow build; on Unsloth's build, at roughly twice the speed, still more than 15. It would be reported with partial coverage. Its replay score on the core is 52.4.

## What this test can and cannot tell

- **As a ranking it is coarse.** One run puts a model's score within about ±17 points (smaller) or ±13 points (larger) at 95%. Two models need to be 20-25 points apart to be told apart by one run. The 390-item test could not separate neighbours either; this one is coarser still.
- **What it is good for:** catching a broken tool-calling setup after an engine or template update (a model against its own stored baseline, item by item), and a first look at a new model in the time of a coffee.
- **Sharper answer when needed:** a second form drawn the same way from the remaining 15 episodes doubles the multi-turn count for another 10-45 minutes.
- **Risk of dropping the other parts:** a model can lose reasoning or coding quality without this test noticing. Run the 390-item test when an entry's rank matters or the model is being swapped.

## What was built (November 22)

An add-on folder `fast/` inside the quality harness (`~/quality-eval-build/quality/fast/`, outside this repository like the rest of the harness). No existing harness file was changed, so stored records and the resume of running jobs are unaffected.

- `fast/manifest.json`: the frozen list of 55 items (seed 20261122), each with its hash.
- `fast/fast.sh MODEL small|large KEYFILE RUNID [--select] [--base-url URL]`: one run under the outer kill timer. It applies the 3-minute load cap, the item budget, the per-item deadlines, waits for the server to be idle after a cut, and writes `fast.jsonl` and `fast-result.json`. A run is never resumed; a cut is final.
- `python3 -m fast.report_fast --out DIR NAME=RUN_DIR ... [--baseline NAME]`: scores fast runs and stored 390-item runs on the same items, with coverage, timeouts and the item-by-item comparison. Models are paired when the request sent was the same, whatever server answered it, so a trial server pairs with router models.

Checks: 15 unit tests against a mock server pass on the server (deadline cut during a steady stream, item timeout, load cap, stuck server, scoring, report from old records). The report reproduces the replay table above exactly from the stored records, and pairs Inkling 2 Mini with the eight ranked models on all 55 items. **First live run (November 22, `inkling-llamacpp`, smaller-model limit):** the load cap, item budget and deadline cut worked as designed: 4.5 s load, 690.5 s of items, 41 of 49 items scored, the episode in flight at the deadline cut and left out, 7 not run. Result: 32 of 40 single-turn items, 1 of 9 episodes reached. One weakness seen: the runner gives the router 8 seconds to unload at the end and reported that it did not complete (that day the cause was a stale hub service, not the runner); the model stayed loaded until unloaded by hand, so check the GPUs after a run. Also learned: with one episode scored the printed score is not meaningful; read coverage first. The implementation was written by Codex (GPT-6.2 Astra) from a written specification and reviewed here; one fault was fixed in review (the wait for an idle server after a cut could outlast the kill timer and lose the result file).

## Review

Three independent designs were drafted and each was checked by a reviewer who redid the time arithmetic. This plan keeps what survived: one shared core so every result pairs, existing items and settings so old records count, single-turn first, a fixed item budget separate from load, cuts left out instead of scored as wrong, and the same timeouts for both groups.
