# Kolibri 1.1 added as router entry `kolibri-llamacpp` — November 24, 2026

At the owner's request ("Add it now"), Kolibri 1.1 Q5_K_M became a router entry on the same llama.cpp pull-request build and the same settings as the [trial](KOLIBRI-1.1-TRIAL-20261124.md). The owner chose not to wait for the upstream merge.

## Setup

| | |
|---|---|
| API id | `kolibri-llamacpp` (launcher alias `kolibri`) |
| Model | Aleph Alpha Kolibri 1.1, 75B MoE with 3.44B active, German and English, Apache 2.0 |
| Weights | official `Kolibri-1.1-Q5_K_M.gguf` (53.4 GB), `models/engine-tests/kolibri-1.1-gguf` on SATA. The publisher's SHA-256 is recorded, and the size is checked at every start. |
| Engine | llama.cpp built from pull request [#32891](https://github.com/ggml-org/llama.cpp/pull/32891), head `5f4d2228`, CUDA 12.4, sm_86, at `runtimes/llamacpp-manual/kolibri-pr32891-5f4d222-20261124/`. The binary and its eight libraries are pinned by SHA-256 in `config/kolibri-llamacpp-runtime.json` and checked before every start. |
| Placement | Routed experts of layers 2-6 are on the 3080 Ti and 45-49 on the 3080. Layers 7-44 stay in RAM, read from the memory-mapped file. Attention, the dense layers and the shared experts are on the GPUs. |
| Context | 131,072 tokens, one slot, F16 KV cache (about 1.1 GB), prompt batch 2,048 |
| Thinking | Off by default. A request can turn it on with `chat_template_kwargs` `{"reasoning_effort":"medium","enable_thinking":true}`. |
| Guards | The router's worker unit with 87.77 GiB soft / 89.77 GiB hard RAM and a 2 GiB host reserve. The worker stops on sustained swap, memory pressure, less than 256 MiB free VRAM on either card or GPU temperature. It must also show both cards and 131,072 context in the engine log. |
| Updates | Pinned in `config/daily-update.json` (`pinned_profiles`), so no updater replaces the engine. Update by hand when the pull request merges or its head changes ([runbook](../ENGINE-UPDATE-RUNBOOK.md)). |

The llama.cpp worker (`scripts/llamacpp_worker.py`), retired with `inkling-llamacpp` earlier the same day, was restored for this entry. `scripts/kolibri_llamacpp_runtime.py` builds the launch command from `selected_settings` in the registry.

## Router checks

| Check | Result |
|---|---|
| First load (weights read from SATA) | 2 min 14 s |
| Load with the file in RAM | about 4 s |
| VRAM when ready (3080 Ti / 3080) | 10.1 / 9.1 GB used, 1.9 / 0.8 GB free |
| Short DSH check (5.7K-token prompt with tools), two runs | tool call and follow-up pass, owned unload. Prompt reading 542 and 511 tok/s, first token 10.8 and 11.4 s, generation 36.2 and 36.5 tok/s over the 37-token reply. |
| gBench chat-template check | 6/6 (5.1 s warm-up, 13.4 s run), owned unload |
| Plain 6.1K-token prompt through the router | 1,316 tok/s prompt reading |
| 500-word answer through the router | 43.1 tok/s generation |
| Short tool-use test | not rerun; the trial's **41.8** (thinking off) stands, since engine, weights and settings are the same |

**Why the DSH prompt reads at half speed.** The web client's prompt has several messages. llama-server stops at message boundaries near the end to save context checkpoints, so the prompt ran in five batches (2,048, 1,608, 1,872, 53 and 119 tokens). With the experts in RAM, each batch costs about a second, however small. A single-message 5.2K-token prompt with tools reads in 5.0-5.2 s (about 1,000 tok/s). In an agent loop the follow-ups reuse the cache and take about 1 s each, whether or not checkpoints are on (`--ctx-checkpoints 0` measured on the trial server). The setting was left at its default. Turning checkpoints off could save about 5 s on the first reply in the web client, but it would lose cache reuse when a conversation is edited. It has not been tried through the router.

## Not done

- No multi-hour run, and nothing at the very top of the 131,072 window (largest 119.2K in the trial).
- No 390-item quality test.
- Generation still falls with context, from 44 tok/s on short prompts to 11 at 111K tokens: one CPU thread builds the sparse-attention masks. That is the pull request's code; a later head may fix it.
- The pull request still has no human review.
