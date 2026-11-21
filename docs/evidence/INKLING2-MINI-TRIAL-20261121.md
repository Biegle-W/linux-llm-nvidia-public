# Inkling 2 Mini trial — November 21, 2026

**Status: trial in progress. Not a router model; no profile, launcher or guard was added.** The owner pointed at the model on its second day and asked for a test. This file records what has been measured so far and is updated when the quality run completes.

## The model

Thinking Machines Lab's Inkling 2 Mini, released November 20, 2026 under Apache 2.0. A 26B mixture-of-experts model (128 experts per layer, 8 used per token) with a "looped" design: 24 stored layers of which layers 6-17 run three times, so every token passes 48 layers. Text and pictures, up to 1M context. The vendor's table puts it ahead of Qwen3.8-27B on two software-engineering benchmarks and level on others; none of that was checked here.

Weights used: Unsloth's `Inkling-2-Mini-UD-Q4_K_XL` (17.63 GB) in the layout mainline llama.cpp reads (`Mainline_Support/`), plus `mmproj-F16.gguf` for pictures; both verified against the publisher's hashes. Kept under `models/engine-tests/inkling2-mini-trial/` (SATA). Unsloth's own comparison gives this quant 98.0% top-token agreement with the 8-bit file.

## Which engine can run it here

| Engine | State on this server (12 GB + 10 GB, sm_86) |
|---|---|
| llama.cpp main `19bc41d` (production since November 21) | **Runs**, slowly (below). Reads only the `Mainline_Support` layout. |
| Unsloth's llama.cpp build `b12588-mix-c0c3de8` | Not tried. It has correct two-GPU placement for the loop, banded attention and the DSpark drafter, and reads the repository-root layout. It is a downloaded binary or a source build with pinned pull requests; waiting for the owner's decision. |
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

## Quality run (in progress)

The 390-item screening set used for the ranking in [QUALITY-BENCHMARK-20261111.md](QUALITY-BENCHMARK-20261111.md), same harness and sampling (temperature 0.6, top-p 0.95; the vendor recommends 1.0 and 1.0). Started November 21, paused for the engine update at 258 items and resumed afterwards on the same build. The run has thinking on, which the eight ranked entries did not, so the result will not be like for like.

| Part | Done | Correct |
|---|---:|---:|
| MMLU-Pro | 210 of 210 | 151 (71.9%) |
| AIME 2025 | 30 of 30 | 18 (60.0%) |
| LiveCodeBench | 18 of 60 | 15 |
| Tool calling, single and multi | 0 of 90 | — |

No score or rank is claimed until the run completes.

## Not done

- No speed test of the placement fix, the Unsloth build with the drafter, or Maya's unsupported two-GPU switch.
- No run above 32K context, no sustained run, no router integration.
- The vendor's benchmark claims were not reproduced.
