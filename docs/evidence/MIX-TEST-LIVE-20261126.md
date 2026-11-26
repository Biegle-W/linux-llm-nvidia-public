# Mix quality test, first live runs — November 26, 2026

All ten enabled routes ran the new mix test ([QUALITY-MIX-TEST-PLAN.md](../QUALITY-MIX-TEST-PLAN.md)) live through the router on November 26, one at a time, on the engines now serving (Strata 0.2.22, Maya 1.1.81; see the engine records of the same day). Run ID `mix-20261126`; driver and per-route journals are under the harness folder `mix/runs/` on the server (benchmark data and answers are not committed). Before each route the driver checked that the GPU unlock read VERIFIED, the router was idle and unloaded and both GPUs were empty (at most 16 MiB used); after each route it checked the router had unloaded again. Every check passed.

## Results

36 items per route, all scored on every route (no timeouts, cuts or errors). Three answers scored 0 without a wrong answer as such: both Qwen 27B routes hit the 4,096-token cap on MMLU-Pro item 4790 (truncated), and `qwen27b-hyperqwen` gave no extractable code on one LiveCodeBench item. Overall = mean of the six category accuracies.

| Route | Tier | Overall | Knowledge | Maths | Code | Instructions | Reasoning | Tools | Load (s) | Items (s) | Wall (min) | Limit (min) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `flash-next-strata` | small | 97.2 | 5/6 | 6/6 | 5/5 | 7/7 | 6/6 | 6/6 | 35 | 177 | 3:35 | 15 |
| `hy4-flash-strata` | large | 94.8 | 6/6 | 6/6 | 5/5 | 6/7 | 5/6 | 6/6 | 51 | 492 | 9:05 | 30 |
| `deepseek-unsloth-strata` | large | 94.4 | 6/6 | 6/6 | 5/5 | 7/7 | 4/6 | 6/6 | 21 | 567 | 9:51 | 30 |
| `hy4-flash-maya` | large | 94.4 | 5/6 | 6/6 | 5/5 | 7/7 | 5/6 | 6/6 | 424 | 653 | 17:59 | 30 |
| `deepseek-maya` | large | 91.7 | 5/6 | 6/6 | 5/5 | 7/7 | 4/6 | 6/6 | 26 | 627 | 10:55 | 30 |
| `inkling-strata` | small | 89.7 | 5/6 | 6/6 | 5/5 | 5/7 | 5/6 | 6/6 | 10 | 73 | 1:25 | 15 |
| `qwen27b-sglang` | small | 88.3 | 5/6 | 6/6 | 4/5 | 7/7 | 5/6 | 5/6 | 23 | 266 | 4:54 | 15 |
| `kolibri-llamacpp` | small | 86.1 | 5/6 | 6/6 | 5/5 | 7/7 | 2/6 | 6/6 | 138 | 149 | 4:48 | 15 |
| `glm-maya` | large | 86.0 | 5/6 | 5/6 | 4/5 | 6/7 | 5/6 | 6/6 | 39 | 230 | 4:34 | 30 |
| `qwen27b-hyperqwen` | small | 85.6 | 5/6 | 6/6 | 4/5 | 7/7 | 4/6 | 5/6 | 76 | 299 | 6:17 | 15 |

- **Time limits:** every route finished well inside its limit; the longest was `hy4-flash-maya` at 18 of 30 minutes, 7 of them loading. Small routes took 1.4-6.3 of 15 minutes.
- **Nothing is separated.** The 95% interval of every overall score is about 23 points wide on the low side (Hoeffding; for example 74.5-100 for `flash-next-strata`, 62.8-100 for `qwen27b-hyperqwen`). No pair of routes differs at the 5% level, not even before the Holm adjustment (smallest paired p = 0.125, 45 pairs). The order above is observed scores only.
- **Why:** the form is too easy for these models. 24 of the 36 items were answered correctly by all ten routes (5 of 6 knowledge, 5 of 6 maths, 2 of 5 code, 5 of 7 instruction, 2 of 6 reasoning and 5 of 6 tool items); only 12 items told any routes apart. The hardest items: one MMLU-Pro history question (2 of 10 right; two of the misses are the Qwen answers cut at the token cap), the two BBH navigation items (4 and 6 of 10) and one Boolean expression (6 of 10).
- **Against the ranking test.** The order differs a lot from the short tool-use test: `flash-next-strata` is first here and last there (40.6). The two tests measure different things (single short answers here, multi-turn tool episodes there), and neither run separates most pairs.
- **RAM:** during `hy4-flash-strata` (the tightest entry) used RAM peaked at 82.7 GiB with at least 9.1 GiB available, as on November 22 (8.5-9.1 GiB), so Strata 0.2.22's RAM-sized conversation cache did not reduce the margin.

## Scorer amendment (BBH, `mix-new-2`)

The first run showed `qwen27b-hyperqwen` answering the two logical-deduction items with the right letter followed by that option's exact text (for example "(B)" followed by the full text of option B, target "(B)"), which the strict v1 scorer counted wrong. The same happened on `qwen27b-sglang`, `kolibri-llamacpp` and `glm-maya`. That measures answer format rather than reasoning, so the chair amended the BBH scorer: a letter target now also accepts "(X) <exact option text>" or the exact option text alone (case and spacing ignored, one trailing full stop allowed), with the option text parsed from the item's own prompt. Bare-letter, Yes/No and True/False scoring is unchanged; anything else is still wrong. The change was made after the last route finished (the runner code was not changed during the runs); stored answers were rescored without any model call. It changed 8 answers, all wrong to correct (those two items on those four routes); no other answer changed. IFEval scoring is unchanged (`mix-new-1`). Tests: 54 mix tests, the fast-test suite and the harness suite pass.

## Checks of this record

The figures above were recomputed from the run journals by a second reviewer (see the commit). The targets of the items most routes missed (`boolean_expressions:79`, `navigate:26`, `navigate:107`) were checked by hand and are right.
