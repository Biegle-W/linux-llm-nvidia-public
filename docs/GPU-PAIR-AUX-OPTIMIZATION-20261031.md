# Main GPU pair and auxiliary 3060 optimization — October 31, 2026

Main inference remains on the RTX 3080 Ti 12 GB and RTX 3080 10 GB. The RTX 3060 12 GB is reserved for auxiliary work. No GPU relocation, driver replacement, reboot, model-weight download or runtime-pin update was required.

## Selected dense changes

The previous dense launcher disabled NCCL P2P despite the pair's earlier successful correctness tests. Matched screens compared that control, NCCL P2P, and custom all-reduce on the same hardware and fixed prompts. Both selected profiles now set `NCCL_P2P_DISABLE=0` and `NCCL_P2P_LEVEL=SYS`, with only GPUs 0/1 visible to main inference. HyperQwen enables custom all-reduce; SGLang keeps it disabled because enabling it offered no material extra gain in the screen.

Actual NCCL logs changed from SHM to P2P/CUMEM for HyperQwen and P2P/IPC for SGLang. HyperQwen's selected custom collective was also confirmed in its native dispatch log. P2P checks were not skipped.

| Engine | Arm | Prefill tok/s | Decode tok/s |
| --- | --- | ---: | ---: |
| hyperqwen | control | 2,097.29 | 99.86 |
| hyperqwen | p2p-nccl | 2,527.97 | 104.91 |
| hyperqwen | p2p-custom | 2,508.23 | 111.90 |
| sglang | control | 2,349.89 | 92.95 |
| sglang | p2p-nccl | 2,779.74 | 96.27 |
| sglang | p2p-custom | 2,782.72 | 96.32 |

Fresh-process confirmation and quality/resource qualification followed the screens:

- **hyperqwen**: 112.14 decode tok/s (**+12.30%**) and 2516.49 prefill tok/s (**+19.99%**) against its fresh control. Tool call and tool-result roundtrip passed; retrieval at 49,049 input tokens passed. A 49,106-input/4,096-output stream generated continuously for 174.26 seconds.
- **sglang**: 95.86 decode tok/s (**+3.14%**) and 2778.24 prefill tok/s (**+18.23%**) against its fresh control. Tool call and tool-result roundtrip passed; retrieval at 27,049 input tokens passed. A 27,106-input/4,096-output stream generated continuously for 153.80 seconds.

Two subsequent fresh normal-router loads per engine passed arithmetic, selected environment and actual KV capacity checks. HyperQwen's pool covered its 56,320-token allocation; all four SGLang pools covered 32,768. These long-context runs establish tested quality/resources, not a matched long-context speed comparison against the control.

## Current selected settings: fresh speed evidence

Protocol: same fixed synthetic prompts across the six profiles, one warmup (64 output tokens), three requested measured requests (128 output tokens), temperature zero, concurrency one; medians of complete three-repetition runs. DeepSeek/Maya completed two repetitions before its existing sustained-memory-pressure guard stopped the third; its partial result is not selected as a new benchmark. Model loading is excluded. Models and expert caches are warm/adaptive; conversation cached-token counts are checked. Prefill uses the native per-request counter/timing; decode is client SSE `(completion_tokens - 1)/(last_content - first_content)`. Token counts vary by tokenizer. Dense rows use the selected fresh confirmation; native rows use unchanged selected settings on current hardware. The native rows are fresh short screens; their earlier full-context qualifications are retained and are not relabeled as newly repeated.

### VRAM-only models

| Model / quant | Engine | Prefill (tok/s) | Time to first token (s) | Decode (tok/s) | Context limit (tokens) | Storage size (GB) | Storage location |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Qwen3.8-27B / AutoRound-INT4-fast-heads-INT8-embedding | HyperQwen-vLLM | 2,516.49 | 0.891 | 112.14 | 56,320 | 15.79 | SATA: models/engine-tests/qwen38-27b-hyperqwen-fast |
| Qwen3.8-27B / AutoRound-INT4-fast-heads-INT8-embedding | SGLang | 2,778.24 | 0.804 | 95.86 | 32,768 | 15.79 | SATA: models/engine-tests/qwen38-27b-hyperqwen-fast |

### MoE models with CPU RAM offload

None currently maintained as fully RAM-resident offload. Bolt remains an experimental candidate described below; expert caches in the next section are part of SSD-streaming profiles.

### MoE models with SSD streaming

| Model / quant | Engine | Prefill (tok/s) | Time to first token (s) | Decode (tok/s) | Context limit (tokens) | Storage size (GB) | Storage location |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Qwen3.8-Flash-Next / IQ3_XXS | Strata | 695.20 | 3.199 | 98.42 | 32,768 | 75.84 | NVME: models/strata/models/IQ3_XXS |
| GLM-5.3-Flash / Maya-S24 | Maya | 74.10 | 29.837 | 6.39 | 65,536 | 94.70 | NVME: models/maya/Maya-S24 |
| DeepSeek-V4.1-Flash-1017 / Maya-S | Strata | 30.80 | 70.845 | 3.27 | 131,072 | 339.48 | NVME: models/maya/DeepSeek-V4.1-Flash-1017-GGUF/Maya-S |
| DeepSeek-V4.1-Flash-1017 / Maya-S | Maya | Incomplete | Incomplete | Incomplete | 32,768 | 339.48 | NVME: models/maya/DeepSeek-V4.1-Flash-1017-GGUF/Maya-S |

DeepSeek/Maya: incomplete. Two measured requests completed (49.4 prefill tok/s, 2.58 decode tok/s median); the third stopped on sustained full-memory pressure. The previous selected benchmark remains historical and unchanged. No guard was relaxed and the run was not repeated.

Measured prompt-token ranges: qwen27b-hyperqwen [2212, 2222], qwen27b-sglang [2212, 2222], flash-next-strata [2212, 2222], glm-maya [2199, 2209], deepseek-strata [2179, 2198].

Storage counts decimal GB of base checkpoint weights. Qwen's safetensors are shared between its two engines, and DeepSeek's base weights are shared between its two engines; count each shared base once. Derived packs/caches and the separate GGUF trial assets are excluded from those base sizes. No native cache, context or worker budget was changed. Differences against older dated runs are not causal P2P estimates.

## Dedicated 3060 drafting experiment

The already-downloaded Qwen Q4_K_M GGUF contains an MTP head. A 2,008,054,496-byte MTP-only file was extracted on SATA, including its embedding/output tensors. Each selected tensor was verified byte-for-byte against the original. The original GGUF was preserved and no new weights were downloaded.

All cases used the same 32,768 configured context and fixed short prompts; this is a short screen, not new full-window qualification. Arithmetic passed in every case.

| GGUF case | Prefill tok/s | Decode tok/s |
| --- | ---: | ---: |
| layer-no-draft | 1,952.53 | 38.80 |
| tensor-no-draft | 1,231.65 | 55.32 |
| tensor-pair-mtp | 1,158.27 | 84.67 |
| tensor-3060-mtp | 1,152.55 | 67.39 |

The dedicated-drafter case explicitly kept the target on CUDA0/1 and placed the extracted draft on CUDA2; GPU memory telemetry confirmed the 3060 allocation. Main-pair MTP was faster, so the dedicated 3060 drafter was not selected. HyperQwen also remains faster overall than these GGUF cases. The 3060 remains available for independent auxiliary services. This trial does not establish that every dedicated-draft engine or model pair would behave the same way.

## Existing Bolt INT4 candidate

A new pageable/no-UVA/no-pinning loader experiment was motivated by the upstream offloader controls and earlier pinned-memory pressure. The first 18 GiB/rank trial reached the GPU reserve guard while retaining host headroom. A calculated 20 GiB/rank follow-up kept the same 46 GiB soft/48 GiB hard cap and all independent guards. It used the previously reviewed pinned checkpoint/configuration source with offline model loading. This did not retry the earlier pinned configurations.

Follow-up outcome: **failed**. Error/guard: `RAM/VRAM reserve guard`. Bolt was not promoted to a maintained production profile; short responses alone do not establish full-context/reload qualification. Super VL remains the previously blocked, partially downloaded candidate and was not retested or completed here.

## Guarding, cleanup and research

All 263 CPU regression tests passed. Catalog validation and whitespace checks passed. All owned inference/test units finished inactive, the router was idle and no GPU reservation remained. Restored conversation snapshots matched their original hashes.

Host reserve 2 GiB, GPU reserve 512 MiB, temperature 82 C, swappiness 60, concurrency one and idle 600 seconds were preserved. Dense active swap limits remain 1 MiB/s writes / 8 MiB/s combined over 30 seconds. Native profiles retain their selected bounded swap/pressure policies and RAM budgets. The Bolt trial retains a 48 GiB hard limit and an additional conservative loading-pressure stop. Existing native expert/file caches were preserved; persisted conversation snapshots were isolated for uncached measurements and restored byte-for-byte.

The attention terminal launcher now falls back to raising the owned frame and focusing its client when the window manager ignores the activation message. Actual foreground acknowledgement and existing terminal regressions passed; backend monitors still start minimized. No global focus policy was changed.

Forum reports supplied hypotheses, which were checked against installed source and matched local experiments:

- [HyperQwen multi-GPU guidance](https://github.com/syv-ai/HyperQwen/blob/main/docs/multi-gpu.md): TP2 plus an independent third-card service and topology-dependent P2P settings.
- [NCCL consumer-GPU field report](https://github.com/syv-ai/HyperQwen/issues/254): verify the actual transport rather than infer it from peer capability.
- [Three-3060 community discussion](https://www.reddit.com/r/LocalLLM/comments/1wpc1rz/best_local_coding_model_for_3x_rtx_3060_12gb/): additional cards can reduce throughput; this is a community report, not evidence for this machine.
- [htsglang source/guidance](https://github.com/efschu/htsglang): solo drafting is hosted on an existing TP rank; that is distinct from a separate 3060 outside the target group.
- [NVIDIA NCCL environment reference](https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/env.html), [vLLM offloader source](https://github.com/vllm-project/vllm/blob/main/vllm/model_executor/offloader/uva.py).

Numeric evidence: [20261031-pair-main-aux.json](benchmark-results/20261031-pair-main-aux.json). Raw transcripts, ownership records, authentication data, source-review copies and snapshot contents remain private.
