# Kolibri 1.1 Q5_K_M trial on llama.cpp — November 24, 2026

**Status: trial only, no router entry.** The owner asked for a trial of Aleph Alpha's Kolibri 1.1 in the Q5_K_M quant on llama.cpp. Whether it becomes a router entry is the owner's call.

## The model

Aleph Alpha's Kolibri 1.1, released November 23, 2026 under Apache 2.0, for German and English. A 75B mixture-of-experts model with 3.44B parameters active per token: 2 dense layers, then 48 MoE layers with 384 routed experts (6 used per token) plus one shared expert. Attention alternates sliding-window and sparse attention 4:1, with K/V shared between the full-attention layers. Native context is 262,144 tokens. It supports reasoning (efforts none, low, medium, high) and tool calls. Aleph Alpha's own tables put it at 73.2 overall, below Qwen3.8 Flash Next (80.1) and GLM-5.3 Flash (80.0); no independent rankings exist yet.

Weights: the official `Aleph-Alpha/Kolibri-1.1-GGUF` file `Kolibri-1.1-Q5_K_M.gguf`, revision `90116812`, 53,394,217,408 bytes, SHA-256 `f338bb58…2195`, matched to the publisher's hash. Aleph Alpha measures Q5_K_M at +0.1 points against the full model (Q4_K_M −0.7). Stored at `models/engine-tests/kolibri-1.1-gguf/` (SATA). Only 2.0 GB of the file is outside the routed experts.

## Engine

Mainline llama.cpp cannot load Kolibri 1.1. It was built from the open pull request [ggml-org/llama.cpp#32891](https://github.com/ggml-org/llama.cpp/pull/32891) at head `5f4d2228` (one commit on master `6aee50801`). The build is in its own folder, `runtimes/llamacpp-manual/kolibri-pr32891-5f4d222-20261124/`, and touches no live runtime. It uses CUDA 12.4 and sm_86, with the same flags as the earlier llama.cpp builds. `llama-server` SHA-256 is `eb2d249d…8060`.

The pull request adds a rounding operation (`ROUND_NVFP4`, for the model's NVFP4 training) and a CUDA kernel for the sparse-attention indexer. A source review by codex found that both have software paths for Ampere and need no FP4 or FP8 hardware. llama.cpp's own tests pass on both cards: `ROUND_NVFP4` 4/4, `LIGHTNING_INDEXER` 240/240 and `FLASH_ATTN_EXT` 4,433/4,433. The PR had no human review yet, and there is no Kolibri-specific chat parser. Tool calls go through llama.cpp's generic template-derived parser.

## Setup found

The server ran as a separate user unit (`kolibri-trial`), capped at the router's worker RAM limits (87.77 GiB soft, 89.77 GiB hard), on loopback with its own key, while the router was idle and unloaded.

```
llama-server -m Kolibri-1.1-Q5_K_M.gguf -ngl 99 -sm layer --tensor-split 12,10 \
  -ot "blk\.([7-9]|[1-3][0-9]|4[0-4])\.ffn_(up|down|gate)_exps\.weight=CPU" \
  -c 131072 -np 1 -b 2048 -ub 2048 -fa on -ctk f16 -ctv f16 \
  --jinja --reasoning-format deepseek --temp 1.0 --top-p 0.99 --top-k 128 --min-p 0 \
  --chat-template-kwargs '{"reasoning_effort":"none","enable_thinking":false}'
```

The routed experts of layers 2-6 sit on the 3080 Ti and those of layers 45-49 on the 3080. All other experts stay in RAM, read from the memory-mapped file. Attention, the dense layers and the shared experts are on the GPUs. The KV cache at 131,072 tokens is about 1.1 GB.

| Run | Experts on GPU | Batch | VRAM used (3080 Ti / 3080) | Prompt reading, 6.8K tokens | Generation, short |
|---|---|---:|---|---:|---:|
| All experts in RAM | none | 512 | 2.9 / 2.3 GB | 435 tok/s | 35-37 tok/s |
| 13 layers | 2-8, 44-49 | 512 | 9.9 / 8.7 GB | 586 tok/s | 45.5 tok/s |
| 13 layers | 2-8, 44-49 | 1,024 | 10.7 / 9.3 GB | 892 tok/s | — |
| 13 layers | 2-8, 44-49 | 2,048 | out of memory on the 3080 Ti (2.8 GB work buffer) | — | — |
| **10 layers (chosen)** | **2-6, 45-49** | **2,048** | **10.1 / 9.1 GB** | **1,128-1,153 tok/s** | **43.7-45 tok/s** |
| 11 layers | 2-7, 45-49 | 2,048 | 11.1 / 9.1 GB | 1,154 tok/s | 43.7-43.9 tok/s |
| 7 layers | 2-4, 46-49 | 4,096 | out of memory on the 3080 (4.7 GB work buffer) | — | — |
| 11 layers, weights read into RAM (`--load-mode none`) | 2-7, 45-49 | 2,048 | 11.1 / 9.2 GB | 1,218 tok/s | 44.0 tok/s |

Loading takes 4-17 s once the file is cached in RAM. The run with weights read into RAM took 111 s to load and pushed the trial unit to 83 GB, close to its cap, so the setup keeps the memory-mapped file. With it, the unit used 8.3 GB of its own memory plus the shared file cache, and no memory pressure was recorded.

## Checks

| Check | Result |
|---|---|
| Tool call and follow-up (thinking off, medium, high) | pass in all three: one correct `get_weather` call returned as OpenAI `tool_calls`, no markup leaked, correct follow-up answer |
| German answer | correct and fluent |
| Recall of a code hidden at 40% depth | correct at 6.8K, 29.6K, 56.6K, 111.0K and 119.2K tokens |
| Prompt reading by length | 1,128 tok/s (6.8K), 1,227 (29.6K), 1,181 (56.6K), 1,048 (111.0K), 1,035 (119.2K) |
| Generation by context | 43.7-45 tok/s short, 24 tok/s at 29.6K, 17.4 at 56.6K, 11.4 at 111K |
| Prompt reuse | a second question on a 111K-token prompt reused 111,034 cached tokens and answered in 9 s |

**Generation slows down with context.** During generation at 111K one CPU thread is at 100% while both GPUs are about 40% busy. The pull request builds the sparse-attention cell maps and masks on the host for every step, so this is the engine and not memory; a later version of the pull request may fix it.

## Short tool-use test

Smaller-model limits (49 items, 15 minutes), run against the trial server.

| Serving | Score | Single turn | Multi-turn episodes | Item time |
|---|---:|---:|---:|---:|
| Thinking off (as other entries are served) | **41.8** | 29/40 (simple 10/10, irrelevance 14/15, parallel 5/15) | 1 of 9 | 7.2 min, all items run |
| Thinking at medium | 60.0 | 24/40 (simple 9/10, irrelevance 13/15, parallel 2/15) | 3 of 5 scored (1 cut by the deadline, 3 not run) | 11.5 min |

For comparison on the same test: `qwen27b-hyperqwen` 66.0, `inkling-strata` 59.3, `flash-next-strata` 40.6. One run is accurate to about ±17 points, and the medium score rests on 5 scored episodes.

**Parallel calls are the weak spot.** On "weather for three cities" the model emits one call and then ends its turn. Raw output without the parser shows the same, with thinking on or off and with `parallel_tool_calls` set or not. So it is the model, not llama.cpp's parser. Without a system prompt it sometimes refuses to use the tools at all.

## Not done

- No router entry, launcher, guard or web-client listing.
- No sustained or multi-hour run, and no request at the very top of the 131,072 window (largest 119.2K).
- No quality test beyond the short tool-use test.
- No Q8_0 KV cache, `--swa-full`, more than one slot, or quants other than Q5_K_M.
- The engine is an unmerged pull request. A router entry should wait for the merge, or pin this head.
