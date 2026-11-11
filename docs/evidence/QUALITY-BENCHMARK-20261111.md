# Quality benchmark: first measured ranking of the text entries — November 11, 2026

Five of the seven enabled text entries were scored on 390 items taken from public benchmarks, run locally through the router on November 10–11. This is the first measured quality result for this server; earlier rankings were estimates from published numbers. Machine-readable results: [`20261111-quality-benchmark.json`](benchmark-results/20261111-quality-benchmark.json).

## Ranking

| Rank | Entry | Macro score (95% interval) | Not separated from |
| ---: | --- | ---: | --- |
| 1 | `deepseek-unsloth-strata` | 73.0% (67.3–78.4) | `qwen27b-hyperqwen` |
| 2 | `qwen27b-hyperqwen` | 68.0% (62.3–73.7) | `deepseek-unsloth-strata`, `flash-next-strata` |
| 3 | `flash-next-strata` | 62.0% (56.5–67.5) | `qwen27b-hyperqwen`, `glm-maya` |
| 4 | `glm-maya` | 57.2% (52.1–62.3) | `flash-next-strata`, `bolt-llamacpp` |
| 5 | `bolt-llamacpp` | 53.9% (48.7–59.4) | `glm-maya` |

The macro score is the plain average of the five benchmark accuracies. "Not separated" means the paired 95% interval for the difference includes zero, so the order of those two could flip on a rerun. Adjacent ranks are not separated anywhere in the list; entries two or more ranks apart are.

What decides the order:

- **DeepSeek** is at or near the top on every benchmark.
- **Qwen 27B** is weakest of the top four on knowledge and code but best at multi-turn tool use (20/30).
- **Flash-Next** matches DeepSeek on knowledge, math and code, and is the weakest at tool calling: 44/60 single-turn (it called a tool in 6 of 15 cases where none applied) and 6/30 multi-turn.
- **GLM** matches DeepSeek on knowledge, code and single-turn tools but scored 2/30 on AIME: with thinking off it gave short guesses, 10 of them without a final boxed answer. Counting any final integer as the answer would make it 3/30.
- **Bolt** is last on knowledge, code and multi-turn tools. Half of its AIME answers ran out of the 12,288-token limit.

## Complete result list

Hardware: i9-13900KS, 96 GB-class RAM, RTX 3080 Ti 12 GB + RTX 3080 10 GB. Quality cells are percent correct (correct/items), one generation per item. `qwen27b-sglang` and `deepseek-maya` were not run: each shares a checkpoint with a tested entry but uses a different engine and chat template, so the twin's score is not assumed.

Speed rows are the latest short DSH tool-call check for each entry (about 5.6K prompt tokens, one request, load time excluded), not new measurements: `qwen27b-hyperqwen`, `deepseek-maya` November 9; `flash-next-strata`, `glm-maya` November 10; the rest November 5 ([ALL-MODELS-RERUN-20261105.md](ALL-MODELS-RERUN-20261105.md), [ENGINE-UPDATES-20261109-HYPERQWEN-80cf059.md](ENGINE-UPDATES-20261109-HYPERQWEN-80cf059.md), [ENGINE-UPDATES-HANDS-ON-20261109.md](ENGINE-UPDATES-HANDS-ON-20261109.md), [LAUNCH-TUNING-20261110.md](LAUNCH-TUNING-20261110.md)). The `deepseek-unsloth-strata` row is its last cold-prompt figure; with its prompt cache reused it measured 28.1 prefill tok/s, 6.13 s and 12.2 decode tok/s on November 9. Storage is decimal GB of checkpoint files; shared checkpoints repeat on each engine row but occupy storage once.

### VRAM-only models

| Model / quant | Engine | Prefill (tok/s) | Time to first token (s) | Decode (tok/s) | Context limit (tokens) | Storage size (GB) | Storage location |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Qwen3.8-27B / AutoRound-INT4-fast-heads-INT8-embedding | HyperQwen-vLLM | 2,092.0 | 2.80 | 62.6 | 86,016 | 15.792 | SATA, `models/engine-tests/qwen38-27b-hyperqwen-fast` |
| Qwen3.8-27B / AutoRound-INT4-fast-heads-INT8-embedding | SGLang | 2,130.13 | 2.897 | 60.121 | 57,344 | 15.792 | SATA, `models/engine-tests/qwen38-27b-hyperqwen-fast` |

| Model / quant | Engine | MMLU-Pro (210) | AIME 2025 (30) | LiveCodeBench (60) | BFCL single-turn (60) | BFCL multi-turn (30) | Macro (95% interval) | Rank |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Qwen3.8-27B / AutoRound-INT4-fast-heads-INT8-embedding | HyperQwen-vLLM | 81.9% (172/210) | 60.0% (18/30) | 40.0% (24/60) | 91.7% (55/60) | 66.7% (20/30) | 68.0% (62.3–73.7) | 2 |
| Qwen3.8-27B / AutoRound-INT4-fast-heads-INT8-embedding | SGLang | Not measured | Not measured | Not measured | Not measured | Not measured | Not measured | Not measured |

### MoE models with CPU RAM offload

| Model / quant | Engine | Prefill (tok/s) | Time to first token (s) | Decode (tok/s) | Context limit (tokens) | Storage size (GB) | Storage location |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| NVIDIA-Nemotron-3.5-Bolt-74B-A9B / native-IQ2 | llama.cpp | 496.94 | 12.991 | 67.172 | 163,840 | 22.018 | SATA, `models/engine-tests/bolt-iq2` |

| Model / quant | Engine | MMLU-Pro (210) | AIME 2025 (30) | LiveCodeBench (60) | BFCL single-turn (60) | BFCL multi-turn (30) | Macro (95% interval) | Rank |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| NVIDIA-Nemotron-3.5-Bolt-74B-A9B / native-IQ2 | llama.cpp | 76.2% (160/210) | 50.0% (15/30) | 33.3% (20/60) | 90.0% (54/60) | 20.0% (6/30) | 53.9% (48.7–59.4) | 5 |

### MoE models with SSD streaming

| Model / quant | Engine | Prefill (tok/s) | Time to first token (s) | Decode (tok/s) | Context limit (tokens) | Storage size (GB) | Storage location |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Qwen3.8-Flash-Next / IQ3_XXS | Strata | 1,031.6 | 5.54 | 85.4 | 131,072 | 75.840 | NVMe, `models/strata/models/IQ3_XXS` |
| GLM-5.3-Flash / Maya-S24 | Maya | 550.1 | 10.06 | 14.7 | 65,536 | 94.702 | NVMe, `models/maya/Maya-S24` |
| DeepSeek-V4.1-Flash-1017 / UD-IQ1_S (Unsloth Dynamic3.1) | Maya | 177.3 | 33.5 | 7.7 | 32,768 | 232.980 | NVMe core + SATA Engram, `models/unsloth/deepseek-v41-1017-dynamic31-8a6ec9cf/UD-IQ1_S` |
| DeepSeek-V4.1-Flash-1017 / UD-IQ1_S (Unsloth Dynamic3.1) | Strata | 87.10 | 65.591 | 12.000 | 32,768 | 232.980 | NVMe core + SATA Engram, `models/unsloth/deepseek-v41-1017-dynamic31-8a6ec9cf/UD-IQ1_S` |

| Model / quant | Engine | MMLU-Pro (210) | AIME 2025 (30) | LiveCodeBench (60) | BFCL single-turn (60) | BFCL multi-turn (30) | Macro (95% interval) | Rank |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Qwen3.8-Flash-Next / IQ3_XXS | Strata | 85.2% (179/210) | 73.3% (22/30) | 58.3% (35/60) | 73.3% (44/60) | 20.0% (6/30) | 62.0% (56.5–67.5) | 3 |
| GLM-5.3-Flash / Maya-S24 | Maya | 86.2% (181/210) | 6.7% (2/30) | 55.0% (33/60) | 91.7% (55/60) | 46.7% (14/30) | 57.2% (52.1–62.3) | 4 |
| DeepSeek-V4.1-Flash-1017 / UD-IQ1_S (Unsloth Dynamic3.1) | Maya | Not measured | Not measured | Not measured | Not measured | Not measured | Not measured | Not measured |
| DeepSeek-V4.1-Flash-1017 / UD-IQ1_S (Unsloth Dynamic3.1) | Strata | 86.7% (182/210) | 76.7% (23/30) | 55.0% (33/60) | 90.0% (54/60) | 56.7% (17/30) | 73.0% (67.3–78.4) | 1 |

### Resource guards

Configured limits as recorded on November 5; no guard setting has been changed since. All entries keep 2 GiB host available, a 100 C stop, three bad 2-second samples, concurrency 1 and a 600 s idle unload. No guard stopped a worker during the quality run.

| Model / quant | Engine | RAM guards | VRAM guards | Swap guards |
| --- | --- | --- | --- | --- |
| qwen27b-hyperqwen / AutoRound-INT4-fast-heads-INT8-embedding | HyperQwen-vLLM | 87.77/89.77 GiB high/max, 2 GiB host reserve, active PSI 10%, no separate loading threshold | 256 MiB free/card after readiness | Unlimited occupancy, 1/8 MiB/s write/combined over 30 s |
| qwen27b-sglang / AutoRound-INT4-fast-heads-INT8-embedding | SGLang | 87.77/89.77 GiB high/max, 2 GiB host reserve, active PSI 10%, no separate loading threshold | 256 MiB free/card after readiness | Unlimited occupancy, 1/8 MiB/s write/combined over 30 s |
| bolt-llamacpp / native-IQ2 | llama.cpp | 87.77/89.77 GiB high/max, 2 GiB host reserve, active/loading PSI 10/15% | 256 MiB free/card after readiness + 384 MiB native reserve/fit target | Unlimited occupancy, 1/8 MiB/s write/combined over 30 s |
| flash-next-strata / IQ3_XXS | Strata | 87.77/89.77 GiB high/max, 2 GiB host reserve, active PSI 15%, no separate loading threshold | Native reserve guard + 1024 MiB native reserve/fit target | Unlimited occupancy, 128/160 MiB/s write/combined over 30 s |
| glm-maya / Maya-S24 | Maya | 87.77/89.77 GiB high/max, 2 GiB host reserve, active PSI 10%, no separate loading threshold | Native reserve guard + 1024 MiB native reserve/fit target | Unlimited occupancy, 128/160 MiB/s write/combined over 30 s |
| deepseek-maya / UD-IQ1_S (Unsloth Dynamic3.1) | Maya | 87.77/89.77 GiB high/max, 2 GiB host reserve, active PSI 15%, no separate loading threshold | Native reserve guard + 1024 MiB native reserve/fit target | Unlimited occupancy, 128/160 MiB/s write/combined over 30 s |
| deepseek-unsloth-strata / UD-IQ1_S (Unsloth Dynamic3.1) | Strata | 87.77/89.77 GiB high/max, 2 GiB host reserve, active/loading PSI 15/15% | 256 MiB free/card after readiness + 1024 MiB native reserve/fit target | Unlimited occupancy, 128/160 MiB/s write/combined over 30 s |

## Method

- **Items (390 per entry, the same for all):** MMLU-Pro 210 (15 per category); AIME 2025 all 30; LiveCodeBench 60 recent problems; BFCL v4 single-turn 60 (15 each of simple, multiple, parallel and irrelevance); BFCL v4 multi-turn 30 (10 each of base, missing function and missing parameter). Subsets were drawn with seed 20261110 and frozen before any model ran.
- **Settings:** thinking off, as every entry is served; temperature 0.6, top-p 0.95; one generation per item; one request at a time. Output limits: 4,096 tokens for MMLU-Pro, 12,288 for AIME and LiveCodeBench, 2,048 per call for BFCL.
- **Scoring:** deterministic, no judge model. MMLU-Pro by final answer letter, AIME by the final boxed integer, LiveCodeBench by running the generated program against the tests in a sandbox with no network, BFCL by the upstream checker (call matching for single-turn, final simulated state and responses for multi-turn). An answer that hit the token limit, had no final answer, looped or produced a malformed tool call counts as wrong.
- **Statistics:** Wilson 95% intervals per benchmark; the macro interval and pairwise differences come from a paired bootstrap over items (10,000 resamples).
- **Run:** entries ran one after another through the router, each loaded once and unloaded at the end. Run time: Flash-Next about 2.0 h, Bolt 2.8 h, Qwen 27B 4.2 h, GLM 5.0 h, DeepSeek 8.6 h.

## Per-benchmark detail

| Entry | Benchmark | Correct | 95% interval (%) | Outcomes |
| --- | --- | ---: | ---: | --- |
| `deepseek-unsloth-strata` | MMLU-Pro | 182/210 | 81.4–90.6 | correct 182, truncated 2, wrong 26 |
| `deepseek-unsloth-strata` | AIME 2025 | 23/30 | 59.1–88.2 | correct 23, truncated 2, wrong 5 |
| `deepseek-unsloth-strata` | LiveCodeBench | 33/60 | 42.5–66.9 | correct 33, looped 1, truncated 16, wrong 10 |
| `deepseek-unsloth-strata` | BFCL single-turn | 54/60 | 79.9–95.3 | correct 54, wrong 6 |
| `deepseek-unsloth-strata` | BFCL multi-turn | 17/30 | 39.2–72.6 | correct 17, wrong 13 |
| `qwen27b-hyperqwen` | MMLU-Pro | 172/210 | 76.1–86.5 | correct 172, truncated 14, wrong 24 |
| `qwen27b-hyperqwen` | AIME 2025 | 18/30 | 42.3–75.4 | correct 18, truncated 1, wrong 11 |
| `qwen27b-hyperqwen` | LiveCodeBench | 24/60 | 28.6–52.6 | correct 24, no_answer 8, truncated 18, wrong 10 |
| `qwen27b-hyperqwen` | BFCL single-turn | 55/60 | 81.9–96.4 | correct 55, wrong 5 |
| `qwen27b-hyperqwen` | BFCL multi-turn | 20/30 | 48.8–80.8 | correct 20, wrong 10 |
| `flash-next-strata` | MMLU-Pro | 179/210 | 79.8–89.4 | correct 179, truncated 9, wrong 22 |
| `flash-next-strata` | AIME 2025 | 22/30 | 55.6–85.8 | correct 22, truncated 1, wrong 7 |
| `flash-next-strata` | LiveCodeBench | 35/60 | 45.7–69.9 | correct 35, no_answer 1, truncated 7, wrong 17 |
| `flash-next-strata` | BFCL single-turn | 44/60 | 61.0–82.9 | correct 44, malformed_tool 1, no_answer 2, wrong 13 |
| `flash-next-strata` | BFCL multi-turn | 6/30 | 9.5–37.3 | correct 6, wrong 24 |
| `glm-maya` | MMLU-Pro | 181/210 | 80.9–90.2 | correct 181, truncated 3, wrong 26 |
| `glm-maya` | AIME 2025 | 2/30 | 1.8–21.3 | correct 2, no_answer 10, truncated 3, wrong 15 |
| `glm-maya` | LiveCodeBench | 33/60 | 42.5–66.9 | correct 33, truncated 13, wrong 14 |
| `glm-maya` | BFCL single-turn | 55/60 | 81.9–96.4 | correct 55, wrong 5 |
| `glm-maya` | BFCL multi-turn | 14/30 | 30.2–63.9 | correct 14, wrong 16 |
| `bolt-llamacpp` | MMLU-Pro | 160/210 | 70.0–81.4 | correct 160, looped 1, no_answer 6, truncated 6, wrong 37 |
| `bolt-llamacpp` | AIME 2025 | 15/30 | 33.2–66.8 | correct 15, truncated 15 |
| `bolt-llamacpp` | LiveCodeBench | 20/60 | 22.7–45.9 | correct 20, truncated 7, wrong 33 |
| `bolt-llamacpp` | BFCL single-turn | 54/60 | 79.9–95.3 | correct 54, wrong 6 |
| `bolt-llamacpp` | BFCL multi-turn | 6/30 | 9.5–37.3 | correct 6, wrong 24 |

Macro differences (first minus second, percentage points, paired 95% interval):

| First | Second | Difference | Separated |
| --- | --- | ---: | --- |
| `bolt-llamacpp` | `deepseek-unsloth-strata` | -25.3 to -12.8 | yes |
| `bolt-llamacpp` | `flash-next-strata` | -14.8 to -1.7 | yes |
| `bolt-llamacpp` | `glm-maya` | -9.9 to +3.2 | no |
| `bolt-llamacpp` | `qwen27b-hyperqwen` | -21.0 to -7.1 | yes |
| `deepseek-unsloth-strata` | `flash-next-strata` | +4.3 to +17.4 | yes |
| `deepseek-unsloth-strata` | `glm-maya` | +8.9 to +22.6 | yes |
| `deepseek-unsloth-strata` | `qwen27b-hyperqwen` | -1.3 to +11.2 | no |
| `flash-next-strata` | `glm-maya` | -1.6 to +11.0 | no |
| `flash-next-strata` | `qwen27b-hyperqwen` | -12.3 to +0.2 | no |
| `glm-maya` | `qwen27b-hyperqwen` | -17.3 to -4.4 | yes |

Per benchmark, after correcting for the ten pairwise comparisons, few pairs separate: on MMLU-Pro only Bolt falls below DeepSeek, Flash-Next and GLM; on AIME only GLM falls below the other four; on LiveCodeBench Bolt and Qwen 27B fall below the top three (Qwen 27B is not separated from GLM); on single-turn BFCL only Flash-Next falls below GLM; on multi-turn BFCL Qwen 27B is above Bolt and Flash-Next.

## Limits

- **Screening-size samples.** Intervals are wide (about ±5 points on MMLU-Pro, ±15 or more on the 30-item sets). Differences under about 10 macro points are not established.
- **Thinking was off.** Scores describe the entries as served, not what the models can do with reasoning enabled. GLM's AIME result in particular reflects that setting.
- **Token limits count against slow reasoners.** Truncated answers are failures: Bolt 15 of 30 on AIME, Qwen 27B 18 of 60 and DeepSeek 16 of 60 on LiveCodeBench.
- **Not official leaderboard numbers.** The BFCL and LiveCodeBench scores use local subsets and a local runner around the upstream checkers; do not compare them with published leaderboards.
- **Quantization, engine and chat template are measured together.** No full-precision reference ran, so this does not isolate quantization loss.
- **Public items** may appear in training data.
- **Interrupted run.** A power loss on November 10 restarted the server during Bolt's AIME stage; the 13 lost answers were rerun. Flash-Next's first multi-turn stage stopped on a record-writing error after 3 episodes and was rerun in full after the fix. The fix changed only how records are saved; Flash-Next's other four stages and Bolt's MMLU-Pro stage were run before it and kept.
- The harness, downloaded datasets and raw answers stay on the server and are not in this repository.
