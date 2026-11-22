# Inkling 2 Mini trial — November 21, 2026

**Status: trial measured. Not a router model; no profile, launcher or guard was added.** The owner pointed at the model on its second day and asked for a test. The quality run is complete (60.0% macro, thinking on) and Unsloth's llama.cpp build was measured at 41-44 tok/s, against 24-27 on production llama.cpp. Whether it becomes a router model is the owner's call.

## The model

Thinking Machines Lab's Inkling 2 Mini, released November 20, 2026 under Apache 2.0. A 26B mixture-of-experts model (128 experts per layer, 8 used per token) with a "looped" design: 24 stored layers of which layers 6-17 run three times, so every token passes 48 layers. Text and pictures, up to 1M context. The vendor's table puts it ahead of Qwen3.8-27B on two software-engineering benchmarks and level on others; none of that was checked here.

Weights used: Unsloth's `Inkling-2-Mini-UD-Q4_K_XL` (17.63 GB) in the layout mainline llama.cpp reads (`Mainline_Support/`), plus `mmproj-F16.gguf` for pictures; both verified against the publisher's hashes. Kept under `models/engine-tests/inkling2-mini-trial/` (SATA). Unsloth's own comparison gives this quant 98.0% top-token agreement with the 8-bit file.

## Which engine can run it here

| Engine | State on this server (12 GB + 10 GB, sm_86) |
|---|---|
| llama.cpp main `19bc41d` (production since November 21) | **Runs**, slowly (below). Reads only the `Mainline_Support` layout. |
| Unsloth's llama.cpp build `b12588-mix-c0c3de8` | **Runs, and is the fastest engine measured here** (section below). Downloaded binary (commit `8832860`, build 12588), reads the repository-root layout, has the DSpark drafter. Trial folder only; not installed as a runtime. |
| Maya 1.1.72 (`maya-ik2`, experimental) | **Refused as released.** The engine and the setup require one card with 22 GiB or more and refuse two GPUs; it decodes only the `UD-Q4_K_XL` file. Upstream measured 124.6 tok/s on one RTX 3090. The source has an unsupported switch (`IK2_UNSUPPORTED=1` with `--gpus 2` and expert parallel) that nobody has run on Linux or on 22 GB in total; with about 12.4 GiB of room for 14.7 GiB of experts, part would stream from RAM. Not tried. |
| Strata 0.2.18 | No Inkling support. |
| vLLM, SGLang | Ruled out by a source review: their Inkling paths need newer GPU generations and more memory on one card. |

## Measured on llama.cpp (two GPUs, 32K context)

Launch: `-ngl 99 --tensor-split 15,34 -fa on --ctx-size 32768 --batch-size 256 --ubatch-size 128 --parallel 1`. The default layer split and auto-fit both failed to load or crashed on a long prompt (the split counts 48 loop slots, not 24 stored layers); the default batch size asked for about 10 GB of work memory on one card.

| | Trial build (`2a28df0`) | Production (`19bc41d`) |
|---|---:|---:|
| VRAM used | 11.1 of 12 GB, 9.8 of 10 GB | 11.0 of 12 GB, 9.7 of 10 GB |
| Generation, short prompts | 23-27 tok/s | 24-27 tok/s |
| Generation after a 19.6K-token prompt | 12.9 tok/s | 12.8 tok/s |
| Prompt reading, 19.6K tokens | 341 tok/s | 317 tok/s |
| JSON answer, arithmetic, picture, tool call | pass | pass |

For scale, on the same server Qwen3.8-27B generates 60-110 tok/s and `bolt-llamacpp` (74B) 66 tok/s.

**Why it is slow.** During generation the GPUs are 30-45% busy and one CPU thread is at 100%. A source review (cross-checked by a second agent) puts the main cause in how mainline places the loop on two cards: the per-pass caches of loop passes 2 and 3 are assigned to devices independently of the shared weights, which cuts every token's work into hundreds of pieces that hop between cards. Upstream issue 32718 reports the same and measured +32.5% generation with the placement fixed on another two-card PC; it is open. A local patch for it exists from that review and has not been run. All gains named here are estimates until measured.

**Thinking cannot be turned off on mainline.** Every answer carries reasoning. `--reasoning off`, `reasoning_effort` set to `"none"` and to `0.0` through the template settings all still produce reasoning (shorter with the last two). Adding `--reasoning-budget 0` breaks the output: the model repeats empty thinking blocks until the token limit. Upstream issue 32753 covers the template; the model card says reasoning cannot be fully disabled.

## Measured on Unsloth's llama.cpp build (two GPUs, 32K context)

Tested November 21 at the owner's request. Binary: Unsloth's `app-b12588-mix-c0c3de8-linux-x64-cuda13-portable` release (hash verified), run from the trial folder with the CUDA 13 libraries of the engine tools. Weights: `Inkling-2-Mini-UD-Q4_K_M.gguf` (16.61 GB, repository-root layout) and the drafter `dspark-Inkling-2-Mini-Q8_0.gguf` (402 MB), both hash-verified. The file is one quant step smaller than the `UD-Q4_K_XL` used on mainline (17.63 GB), so the comparison is engine plus a 6% smaller file.

Launch: `-ngl 99 --tensor-split 13,12 -fa on --ctx-size 32768 --parallel 1`, default batch size. With the drafter: `--tensor-split 15,10 --batch-size 512 --ubatch-size 256 --model-draft … --spec-type draft-dspark --spec-draft-n-max 3 --gpu-layers-draft 99`. The drafter's work memory lands on the second card whatever `--spec-draft-device` says, so the 13,12 split ran out of memory there; 15,10 loads.

| | Production llama.cpp `19bc41d` | Unsloth build, no drafter | Unsloth build, DSpark drafter |
|---|---:|---:|---:|
| VRAM used | 11.0 of 12 GB, 9.7 of 10 GB | 9.7 of 12 GB, 9.5 of 10 GB | 11.9 of 12 GB, 9.6 of 10 GB |
| Generation, short prompts | 24-27 tok/s | 43.3-44.3 tok/s | 57-71 tok/s |
| Generation, 1,200-token essay | — | 43.6 tok/s | 38.1 tok/s |
| Generation after a 19.6K-token prompt | 12.8 tok/s | 41.1 tok/s | 43.2 and 48.8 tok/s |
| Prompt reading, 19.6K tokens | 317 tok/s | 810-817 tok/s | 733 tok/s |
| JSON answer, arithmetic, picture, tool call and follow-up | pass | pass | pass |

One run per cell (two for the long prompt); single-digit differences are within run-to-run noise.

- **The build alone is the gain**: 1.7 times the generation speed on short prompts, 3.2 times after a long prompt, 2.6 times the prompt reading, with 1.5 GB less memory.
- **The drafter is mixed.** It helps where the next words are predictable (short answers and tool calls: 55-79% of drafted tokens accepted) and hurts on free writing (24% accepted on the essay, 38.1 against 43.6 tok/s). It also fills the 12 GB card to 11.9 GB, leaving nothing for a longer context.
- Thinking is still on in every answer on this build too.
- Not measured: quality on this build and file, contexts above 32K, a sustained run, `--spec-draft-p-min` or greedy drafting.

## Quality run (complete)

The 390-item screening set used for the ranking in [QUALITY-BENCHMARK-20261111.md](QUALITY-BENCHMARK-20261111.md), same harness and sampling (temperature 0.6, top-p 0.95; the vendor recommends 1.0 and 1.0). Started November 21, paused for the engine update at 258 items, resumed on the same build (mainline trial build `2a28df0`, `UD-Q4_K_XL`) and finished at 22:10 EST. The run has thinking on, which the eight ranked entries did not, so the result is not like for like, and the harness's paired statistics do not apply (no shared request settings).

| Part | Items | Correct | Accuracy (95% Wilson) | Other outcomes |
|---|---:|---:|---|---|
| MMLU-Pro | 210 | 151 | 71.9% (65.5-77.6) | 53 truncated, 6 wrong |
| AIME 2025 | 30 | 18 | 60.0% (42.3-75.4) | 11 truncated, 1 wrong |
| LiveCodeBench | 60 | 30 | 50.0% (37.7-62.3) | 27 truncated, 1 looped, 2 wrong |
| Tool calling, single turn | 60 | 49 | 81.7% (70.1-89.4) | 10 wrong, 1 malformed call |
| Tool calling, multi turn | 30 | 11 | 36.7% (21.9-54.5) | 15 wrong, 4 truncated |
| **Macro (mean of the five)** | 390 | 259 | **60.0%** | |

**Where it would sit:** 60.0% falls between `flash-next-strata` (62.0%) and `glm-maya` (57.2%), seventh of nine. It is not added to the ranking table, because the run is not like for like and no interval against the others was computed.

**Truncation is most of the loss.** 95 of the 131 misses are answers cut off at the token limit (53 of the 59 MMLU-Pro misses), 92 of them with no answer text at all because the limit was spent on reasoning; only 34 are wrong answers. With reasoning that cannot be switched off, the harness's token limits, set for thinking-off models, do not fit this model, so 60.0% is a floor for this setup rather than the model's ceiling. A rerun with larger limits was not done.

The run averaged 89 s per MMLU-Pro item and 394 s per AIME item on the slow mainline build; the items add up to 17.3 hours of generation.

## Rerun on the Unsloth build (stopped)

A second run of the 390 items was started on November 21 at 22:29 EST on Unsloth's build (`UD-Q4_K_M`, no drafter) with larger token limits (MMLU-Pro 16,384 in place of 4,096; AIME 28,000; LiveCodeBench 24,000; tool calling 8,192 and 6,144). The owner stopped it on November 22 at 111 MMLU-Pro items and decided the first run is good enough.

| On the same 111 MMLU-Pro items | Correct | Cut off at the limit | Wrong |
|---|---:|---:|---:|
| First run (mainline, limit 4,096) | 82 (73.9%) | — | — |
| Rerun (Unsloth build, limit 16,384) | 97 (87.4%) | 6 | 8 |

This supports reading the first run's 60.0% as a floor set by the token limits, but it is a partial result on one part with a different build and file; no score is claimed from it. The partial records are kept under run id `inklingcmp2`.

On the short tool-use test that replaces the 390-item test for future models, the first run's stored records give Inkling 2 Mini 52.4 out of 100 (33 of 40 single-turn items, 2 of 9 episodes); see [QUALITY-FAST-TEST-PLAN.md](../QUALITY-FAST-TEST-PLAN.md).

## Not done

- No speed test of the mainline placement fix or Maya's unsupported two-GPU switch.
- No complete quality run on the Unsloth build or with token limits sized for a model that always reasons (stopped at 111 items).
- No run above 32K context, no sustained run, no router integration.
- The vendor's benchmark claims were not reproduced.
