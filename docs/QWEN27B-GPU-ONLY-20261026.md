# Dense Qwen3.8-27B entirely in VRAM

**October 27 update:** the default is now the faster [32K HyperQwen/MTP3 profile](DENSE-ENGINE-OPTIMIZATION-20261027.md). This dated report preserves the October 26 measurements; select `qwen27b llama` to launch its GGUF configuration.

Qwen3.8-27B now runs successfully across the RTX 3080 Ti 12 GB and RTX 3080
10 GB with **no host-RAM model-weight offload**. The maintained profile uses
llama.cpp, IQ4_XS weights, two-token MTP drafting and a 32,768-token allocation.
Retrieval passed on a **29,496-token input**; the full allocated window has not
been exhaustively tested. Both GPU compute unlocks remain enabled; P2P remains
unavailable. No new driver changes or reboots were needed.

## Measured results

Medians of three requests per fixture, one active request and one engine at a
time. All weights and the active drafter remained on CUDA devices.

| Configuration | Short decode | Longer-input decode | Code decode | Prose decode |
| --- | ---: | ---: | ---: | ---: |
| llama.cpp IQ4_XS, no drafting, 4K allocation | 42.4 tok/s | 41.8 tok/s | 42.6 tok/s | 42.2 tok/s |
| HyperQwen fast INT4, GPU-only PP2, 4K allocation | 36.4 tok/s | 34.7 tok/s | 35.0 tok/s | 34.2 tok/s |
| **Maintained: llama.cpp IQ4_XS, MTP2, 32K allocation** | **68.6 tok/s** | **66.4 tok/s** | **88.0 tok/s** | **58.6 tok/s** |

| Configuration | Short first-token latency | Longer-input first-token latency |
| --- | ---: | ---: |
| llama.cpp, no drafting | 0.475 s | 1.444 s |
| HyperQwen PP2, no drafting | 0.110 s | 0.885 s |
| Maintained llama.cpp MTP2 | 0.490 s | 1.902 s |

Short and longer fixtures used the previous community-garden prompts, 168–171
and 2,199–2,209 input tokens, 128 output tokens, temperature zero and thinking
disabled. Code and prose used the two archived benchmark prompts, three runs
of 256 output tokens, temperature 0.6, top-p 0.95 and seed 42. One warmup was
excluded. Generation is client-observed `(output_tokens - 1) / (last_content_time
- first_content_time)`; speculative bursts affect this measurement. First-token
latency includes frontend, prompt processing and the first output step, rather
than isolating prefill.

The baseline and HyperQwen use different quantization formats, execution paths
and allocated contexts from the maintained profile. These are comparisons of
runnable configurations, not an isolated engine or unlock experiment. Short and
longer measurements had zero cached prompt tokens. The initial non-drafting
llama.cpp code/prose runs reused 21–25 prefix tokens on repeats; final MTP runs
explicitly disabled prompt reuse. This limits comparing their tiny-prompt
latencies, while the generation measurements remain useful. Three repetitions
are not statistical confidence intervals or a general quality evaluation.

## Maintained profile and placement proof

- Model: [bartowski/Qwen3.8-27B-GGUF](https://huggingface.co/bartowski/Qwen3.8-27B-GGUF),
  `Qwen3.8-27B-IQ4_XS.gguf`, 15,475,951,328 bytes, including MTP tensors.
- Revision: `87410e7b9a5c21e6ca70c0c9cc5237de909fe621`.
- SHA256, verified against the publisher:
  `4b927360fa7c4aa41a734302f0795ca45df0e8b8a258bc76cc5fbf9d98a484db`.
- llama.cpp: `caa8191df159f764fb0160e3d2fc6be008948aee`, CUDA SM86 build.
- Full GPU layers, layer split `0.61,0.39`, automatic fit disabled, lazy tensor
  reads disabled, Q8_0 K/V, Flash Attention, batch/microbatch 512, one sequence,
  six CPU support threads, MTP draft count two, and reasoning disabled.
- Explicit `^token_embd[.]weight$=CUDA0` placement moves the embedding table
  onto the larger card. Merely requesting all decoder layers would leave this
  table on the CPU in this llama.cpp revision.
- The maintained worker reports **66/66 layers offloaded**, CUDA0 model buffers
  of **8,887.35 MiB**, CUDA1 model buffers of **5,861.18 MiB**, and no CPU model
  buffer. The MTP context shares this GPU-resident model. Both cards retained
  approximately **1.4–1.5 GiB free** during the final test.
- A 64K allocation loaded but left only a few hundred MiB on the smaller card;
  it was stopped and rejected as a maintained configuration. The 32K split was
  adjusted toward the larger card to preserve headroom.

Five arithmetic cases, conversation recall, authenticated streaming and
schema-constrained JSON passed. Prompt-only JSON responses sometimes included
Markdown fences; clients requiring strict JSON should use the JSON-schema API.
A separate request with 29,496 actual input tokens recovered exact markers near
the beginning, middle and end, with zero cached prompt tokens and 54 output
tokens, in 22.83 seconds. That is a capacity/retrieval check, not another
three-run speed benchmark. Broad reasoning quality, tools, vision, concurrent
users and sustained thermal behavior are not established by these checks.

## Archived HyperQwen setup

The private retirement repository contains the old 4070 12 GB + 3060 12 GB Linux
setup. It used GPU-resident INT4 body/output/MTP weights, an INT8 embedding,
pinned KV reservations, and MTP or DFlash2. Its preparation and benchmark records
were inspected as historical evidence, not executed as current instructions.

The previous test here used larger INT8 output/MTP heads. Adapting the archive's
published fast-head recipe reduced the prepared checkpoint to 14.71 GiB. The
new body uses `dbirks/Qwen3.8-27B-W4A16-AutoRound` at
`1f05c441c4e64ae0549de44fa9ea5a6d43610314`; the archive used a different retained
body. The new body's quantization group and model layout were checked against
[the published fast heads](https://huggingface.co/syvai/qwen3.8-27b-3090-fast-variant)
at `124c14e7e8c7d2f5402933b9af368e772a9fcf0c`. Immutable body shards were reused;
no second full body copy was needed.

[HyperQwen](https://github.com/syv-ai/HyperQwen) source
`ce9615c4f2309be727407918a6c979bd67968069`, patched vLLM 0.31.0, then worked with
**PP2 split 42/22**, no tensor parallelism, BF16 KV, FP32 SSM state, a 384 MiB
KV reservation per rank, 256-token prompt chunks, eager execution, and **CPU
offload set to zero**. Read-only parameter audits found 969 parameter tensors
on CUDA0 and 514 on CUDA1, with no non-CUDA model parameters. It passed the
same arithmetic, conversation, JSON-schema and streaming checks. This successful
configuration is retained as benchmark evidence; the faster GGUF profile is the
single maintained deployment for this model.

The first GPU-only tensor-parallel trial was too tight on the 10 GB card and
failed one arithmetic smoke case with INT4 KV/FP16 state. A 36/28 pipeline split
ran out of VRAM while loading; a 40/24 split with a 128 MiB KV reservation loaded
weights but correctly rejected insufficient cache capacity. Those failures were
retained, not relabeled as successful profiles. No memory-balance or numerical
checks were removed. The final PP2 result uses the larger valid KV reservation
and higher cache/state precision. Older 4070/3060 speculative speeds are not
claimed for this different pair or workload.

## Start, stop and memory isolation

```bash
./scripts/start_model.sh qwen27b llama
systemctl --user stop llm-test-qwen27b
```

The API is authenticated at `http://127.0.0.1:10000/v1`, model ID
`qwen3.8-27b`, using the existing local API-key file. Stop another model before
starting it. The default `qwen` launcher still selects Flash-Next.

`serve_qwen27b.py` requires the bounded service's cgroup, checks the artifact
size and private key-file permissions, and refuses startup unless both expected
cards have sufficient free VRAM. The service has a 30 GiB soft host-memory limit,
a 36 GiB hard limit and a 1 GiB swap limit; it does not start automatically at
login. Model weights are installed under ignored `models/qwen3.8-27b-iq4-xs/`.
Runtime/build files and private raw evidence remain excluded from public export.
The normal port-10000 profile was started and passed a fresh authenticated
streaming check after the benchmark profile was retired.
