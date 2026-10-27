# CUDA engine qualification on mixed Ampere cards

Tested on an unlocked RTX 3080 Ti 12 GB and RTX 3080 10 GB, with 64 GB host RAM,
Ubuntu 26.04 and NVIDIA 595.99.02. The display uses the smaller card. No P2P driver,
power-limit changes, additional reboot, or memory-balance guard bypass was used.
These are unlocked-engine tests, not measurements of each engine before and after
unlocking. The existing Strata/Maya profiles were not replaced.

## Results

| Engine / route | Actual result on this pair |
| --- | --- |
| HyperQwen, patched vLLM 0.31.0, Qwen3.8-27B W4A16, TP2 | GPU-only startup ran out of VRAM while repacking on the 10 GB card. With 2 GiB CPU offload per rank, authenticated streamed generation and arithmetic, JSON, and conversation checks passed. |
| NInfer upstream | Its RTX 5090 specialization is not an Ampere deployment candidate. The Ampere fork below was built and tested instead. |
| NInfer-3090, Qwen3.8-27B native artifact | Native build, five selected CPU tests, five numerical GPU tests on each card, and a multi-GPU transfer test passed. The model loaded 15.9 GiB, then refused startup: pipeline devices must have the same streaming-multiprocessor count. This pair has 80 and 68. No model throughput result. |
| FreeToken main, Qwen3.8-27B NVFP4, TP2 | Its checkpoint diagnostic passed config, construction and dense loading. Actual startup rejected free-VRAM imbalance: approximately 8.3 versus 11.4 GiB, exceeding its 2 GiB tolerance. No throughput result. |
| FreeToken-Kai, existing Flash-Next IQ3_XXS GGUF, PP2 | GGUF dry loading passed and the layer split initialized. An initial host-embedding setting was rejected; the subsequent full-RAM expert load caused host memory pressure and the OS killed the inherited application scope. This configuration is disabled. No generation benchmark. |
| SGLang baseline, Qwen3.8-27B W4A16, TP2 with CPU offload | Refused startup because the smaller card has less than 90% of the larger rank's available memory. The balance check remains enabled. |
| SGLang, same model, PP2 with CPU offload | Pipeline initialization passed, then the zero-centered layernorm weight loader failed with CPU/CUDA tensors on different devices. The isolated process peaked at 21.3 GiB; the application survived. |
| Dual-3080 SGLang patch, TP2 | Package tests, application against the pinned source, runtime-loader installation and rollback passed. Actual startup still rejected the VRAM imbalance. Its KV/DFlash changes do not fix that check. |

Failures are compatibility results, not zero-token/s benchmarks. The Kai test uses
the existing Flash-Next MoE; the other new model tests use dense Qwen3.8-27B.
Different models and quantizations cannot establish engine speed differences alone.

## HyperQwen measurements

The successful configuration used a prepared AutoRound W4A16 checkpoint, TP2,
2 GiB CPU offload per rank, one request at a time, 4,096-token allocation,
eager execution, text only, no drafting, and a 0.70 GPU memory fraction.
It retained the checkpoint's prepared quantized embedding/head assets.

| Fixture | Input tokens, three requests | Median client decode | Median first-token latency |
| --- | --- | --- | --- |
| Short | 168–171 | 2.55 tokens/s | 1.24 s |
| Long | 2,199–2,209 | 2.55 tokens/s | 14.81 s |

Each measured output contained 128 tokens, temperature zero, thinking disabled,
and streamed usage. The same short/long prompt texts were used in the earlier
Strata/Maya tests, but this is a different model. Client decode is
`(output_tokens - 1) / (last_content_time - first_content_time)`; no unreported
native prefill rate is inferred from first-token latency. All six requests finished.
Unauthenticated model and completion requests returned 401. Arithmetic returned
437, JSON parsed to the requested object, and conversation recall returned copper.
Initial qualification overlapped compilation/downloads. In the final run, the
first short request overlapped the last build activity; the remaining short and
all long requests followed it. These are practical measurements, not an isolated
GPU compute microbenchmark. CPU offload and the smaller card's PCIe x4 connection
make the result unsuitable as evidence of unlock scaling.

## SGLang projects found

- [kk-pcl's dual-3080 patch](https://github.com/kk-pcl/sglang-qwen38-dual-3080-patch):
  TP-sharded DFlash projection, static per-head target FP8 KV scales, and an
  Ampere communication fallback. Its published hardware has **20 GiB per card**,
  not stock 10/12 GB cards. The tested source baseline was
  `4cb5aebfe08fa0abbd5fbcf84b29ad3d541bd5d3`; the locally built package reported
  0.5.22 from its version-generation script. Torch 2.13.0, FlashInfer 0.6.17,
  and Transformers 5.12.1 were installed. A pinned source hash is more precise
  than treating that generated package label as the patch author's wheel version.
- [qwen-serve's 3090 SGLang recipe](https://github.com/sybil-solutions/qwen-serve/tree/main/qwen3.8/3090-sglang):
  pinned Marlin W4A16 plus optional DSpark, validated by its author on 24 GB
  3090 cards. This is a deployment recipe, not a separate inference engine.
  Its container and DSpark preset were reviewed, not benchmarked on this host.
- [club-3090](https://github.com/noonghunna/club-3090): recipes and an AutoRound
  W4A8 Marlin patch, plus reasoning-budget patches. Its published dual-3090
  settings have a different VRAM budget. W4A8 uses integer activations, so it
  should not be assumed to gain from an FP16/BF16 compute unlock. The patch
  requires its matching checkpoint layout and engine baseline; it was reviewed,
  not transplanted into this different pinned SGLang build.

[HyperQwen](https://github.com/syv-ai/HyperQwen),
[NInfer-3090](https://github.com/Don-Chad/ninfer-3090),
[FreeToken](https://github.com/FlashML-org/FreeToken), and
[FreeToken-Kai's pipeline documentation](https://github.com/yuuki-net/FreeToken-Kai/blob/kai/docs/pipeline.md)
provide the upstream scope and supported layouts. Kai's documented pipeline
families do not include dense Qwen3.8-27B; its Flash-Next route was tested instead.

## Memory incident and containment

The failed Kai load ran inside the application's inherited process group. The
OS memory-pressure manager reported 56 GB in that shared scope and killed it.
The budget estimate considered resident expert banks but did not adequately cover
loader transients and pinned allocations. The attempted monitoring command did
not complete before the interruption; it did not protect this run.

Do not retry that full-RAM configuration. A smaller disk-backed bank needs a
separately validated GGUF loader path before use. Remaining SGLang tests were run
in independent user systemd services with `MemoryHigh=30G`, `MemoryMax=36G`,
`MemorySwapMax=1G`, and `OOMPolicy=kill`. These limits were read back from systemd.
`scripts/run_bounded_test.sh` provides that boundary for future experimental
workers. The service command must remain running to supervise its children;
short-lived launchers must wait for the worker. These are host-RAM limits;
per-engine VRAM admission checks still apply.

The native build also needed isolated CUDA 13 headers/libraries, local FFmpeg
libraries, a Linux integer-type fix in a memory-planner test, and an environment
API-key fallback so credentials were not passed in process arguments. The CUDA
header declaration adjustment follows the
[NVIDIA discussion of the glibc conflict](https://forums.developer.nvidia.com/t/fedora-43-and-nvcc-cuda13-1-error-exception-specification-is-incompatible-rsqrt-rsqrtf/354510).
No system toolkit or driver was replaced. Exact revisions, local diffs, artifact
hash verification, failure logs, downloaded checkpoint provenance, and raw
responses remain in ignored local state. They are not exported to the public repo.
