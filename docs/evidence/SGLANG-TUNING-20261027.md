# SGLang pipeline and recurrent-state experiments — October 27, 2026

The user approved pipeline allocation and BF16 recurrent-state tests after forum research. These are isolated candidates; no engine patch, checkpoint change, driver change or production promotion occurred. HyperQwen remains the default, SGLang remains 32/32 with FP32 recurrent state, and host swappiness stays 60.

[Numeric samples, settings, quality and resource results](benchmark-results/20261027-sglang-tuning.json). The same GPU-resident AutoRound INT4/group128 checkpoint with INT8 embedding was used in every trial.

## VRAM-only models

| Model / quant / engine / trial | Prefill (tok/s) | First token (s) | Decode (tok/s) | Context limit (tokens) | Storage size (GB) | Storage location |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Qwen3.8-27B / AutoRound INT4 + INT8 embedding / SGLang / `control-32-32-fp32` | 2,672.75 | 0.8320 | 46.45 | 32,768 | 15.79 | Samsung SSD 870 QVO SATA: `models/engine-tests/qwen38-27b-hyperqwen-fast` |
| Qwen3.8-27B / AutoRound INT4 + INT8 embedding / SGLang / `split-34-30-fp32` | Incomplete (1/3) | Incomplete (1/3) | Incomplete (1/3) | 32,768 | 15.79 | Samsung SSD 870 QVO SATA: `models/engine-tests/qwen38-27b-hyperqwen-fast` |
| Qwen3.8-27B / AutoRound INT4 + INT8 embedding / SGLang / `split-36-28-fp32` | Not measured | Not measured | Not measured | 32,768 | 15.79 | Samsung SSD 870 QVO SATA: `models/engine-tests/qwen38-27b-hyperqwen-fast` |
| Qwen3.8-27B / AutoRound INT4 + INT8 embedding / SGLang / `state-32-32-bf16` | 2,656.12 | 0.8374 | 46.87 | 32,768 | 15.79 | Samsung SSD 870 QVO SATA: `models/engine-tests/qwen38-27b-hyperqwen-fast` |

## MoE models with CPU RAM offload

None tested in this study. Maintained MoE profiles are unchanged.

## MoE models with SSD streaming

None tested in this study. Maintained MoE profiles are unchanged.

## Checks and interpretation

Retain 32/32 FP32. BF16 changed decode by +0.91%, prefill by -0.62% and TTFT by +0.64%; this small mixed result does not justify a precision change. The altered splits fail the existing memory requirement.

- `control-32-32-fp32`: complete; json passed, arithmetic passed, retrieval passed (29,434 input tokens). Decode change versus fresh control: +0.00%. Minimum sampled GPU free: 1702/1045 MiB.
- `split-34-30-fp32`: incomplete; No completed quality checks. Minimum sampled GPU free: 975/1103 MiB. The GPU-headroom guard stopped the worker; the client then reported a closed connection. Its one completed measured request was 2,623.14 prefill tok/s, .8505 s TTFT and 46.65 decode tok/s; no three-request median or quality qualification exists.
- `split-36-28-fp32`: incomplete; No completed quality checks. Minimum sampled GPU free: 665/1921 MiB. Failure: Less than 1 GiB post-load GPU headroom; larger allocation rejected.
- `state-32-32-bf16`: complete; json passed, arithmetic passed, retrieval passed (29,434 input tokens). Decode change versus fresh control: +0.91%. Minimum sampled GPU free: 1699/1055 MiB.

All successful trials use three approximately 2.2K-input/128-output requests after a 64-output warmup. Medians exclude loading. The longer retrieval check is separate work and is not compared as equal prompt work. Measured order was control, 34/30, 36/28, then BF16 on 32/32. CUDA decode graphs, .92 memory fraction, chunk384, TP1/PP2, BF16 KV and max-running-requests1 remain fixed. There is no speculative decoding.

A faster layer split cannot remove the sequential single-request pipeline dependency. BF16 recurrent-state checks establish only the tested short tasks and retrieval fixture; they do not establish numerical equivalence across arbitrary long conversations.

Production settings and earlier benchmark fields remain unchanged. Retain the fresh control and rejected candidates as dated evidence. No W4A8 patch or heterogeneous-TP fork was installed. Raw requests, logs, plans, candidate catalogs and guard telemetry remain private under `data/sglang-tuning-20261027/`.
