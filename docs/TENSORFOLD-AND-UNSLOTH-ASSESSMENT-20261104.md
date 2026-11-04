# TensorFold Qwen27B trial and Unsloth Flash-Next assessment — November 4, 2026

TensorFold 1.2.2 passed actual DSH read-tool/result/exact-follow-up checks in two isolated configurations, then owned unload and GPU-release verification. The drafted configuration produces a fast short decode burst, but slower cold prefill, lower target precision and much smaller context than the maintained engines. It is an experimental candidate, not a production replacement. Maintained profiles, guards and saved DSH choices are unchanged.

The pinned Linux x86_64 release archive SHA256 is 976c39d01ce0e165d67b7b3ede6e6ff5dad037823b35d1539752707c9a238be5, source commit 00e7dddbdb2dd0c481f3d7e8d850fa3e1f2e80b7. Its real host capability probe reports CUDA sm86 and EXL3 Qwen support. Target: [Mia EXL3 2.0bpw](https://huggingface.co/Mia-AiLab/Qwen3.8-27B-EXL3-2.0bpw/tree/b4925724092da59826c02d25a7201fb272bf4f34), with hash-verified model shards. Drafter: [DFlash2](https://huggingface.co/z-lab/Qwen3.8-27B-DFlash2/tree/50307d4c4cde6860d4eee73e2547cd786fe8e8a4), hash-verified and loaded at 4-bit without rewriting its checkpoint.

## GPU execution with host-RAM embedding offload

Only RTX3080Ti GPU0 is used; GPU1 remains unused. The native loader maps BF16 embedding rows to host memory when they do not fit beside stream storage. These are not fully VRAM-resident configurations. The target is lower precision than the maintained AutoRound4-bit checkpoint; its output quality has not been established as equivalent.

| Model / quant | Engine | Prefill (tok/s) | Time to first token (s) | Decode (tok/s) | Context limit (tokens) | Storage size (GB) | Storage location |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Qwen3.8-27B / EXL3 2.0bpw | TensorFold1.2.2 plain, no drafts | 584.6 | 9.982 | 34.40 | 16,384 | 9.673 shared target | Samsung SATA: models/engine-tests/qwen38-27b-tensorfold-mia-exl3-2bpw |
| Qwen3.8-27B / EXL3 2.0bpw | TensorFold1.2.2 DFlash2-4bit + copies | 576.6 | 10.108 | 180.38 | 12,288 | 9.673 shared target | Samsung SATA: models/engine-tests/qwen38-27b-tensorfold-mia-exl3-2bpw |

The target's two shards total 9,672,786,556 bytes, counted once physically. The drafted row additionally requires 3,848,817,896 bytes of DFlash2 weights under models/engine-tests/qwen38-27b-tensorfold-dflash2. Disk size and GPU allocation are different measures.

These are one successful uncached first-tool observation per configuration: plain 5,830 input / 41 output tokens, drafted 5,824 / 39; cached tokens zero. Native prefill and first-token counters and inverse native mean inter-token time supply the rates, including generated tool arguments. Loading and the assistant follow-up are excluded. The drafted request used four decode rounds with 35/60 proposed draft tokens accepted. Its 180.38 tok/s is a short tool-argument burst, not a general prose or sustained-rate estimate. Actual tool/result/follow-up wall times are 23.365 seconds plain and 22.003 seconds drafted. Owned unload/resource verification took 0.669 and 1.862 seconds respectively. Both exact fixture follow-ups passed. No full-context, sustained, quality-ranking or idle-expiry suite ran.

## VRAM-only and SSD-streaming categories

No new fully VRAM-only model or SSD-streaming model was tested in this batch. The maintained HyperQwen/SGLang pair and their historical results are unchanged. The new Flash-Next release below was assessed from metadata only.

## Effective guards

| Model / quant | Engine | RAM guards | VRAM guards | Swap guards |
| --- | --- | --- | --- | --- |
| Qwen27B EXL3 2.0bpw | TensorFold plain16K | 24/26 GiB high/max; host available >=2 GiB | >=256 MiB free/card after readiness; GPU0 startup >=11520 MiB; native reserve1GiB | Unlimited occupancy; writes <=1, combined <=8 MiB/s over30s |
| Qwen27B EXL3 2.0bpw + DFlash2-4bit | TensorFold drafted12K | Same | Same; GPU1 unused and protected by the test reservation | Same |

Actual cgroup memory.high/max are 25,769,803,776 / 27,917,287,424 bytes; memory.swap.max is max. The normal dense WorkerWatch/SwapGuard is reused with only the loopback port and tensorfold-to-vllm metric-name prefix adapted to TensorFold's real running-request gauge. Two CPU adapter checks passed, including missing-gauge failure after readiness. RAM, GPU free memory and >=82 C temperatures stop after three consecutive two-second samples; missing telemetry also fails closed after three. Dense loading has no separate PSI threshold. During inference, full-memory PSI >10% requires three bad samples after a complete30-second window; a swap-rate violation stops immediately once that window exists. Outside inference the window resets. Swappiness60 and idle600 remain. The single visible GPU needs no peer exchange; current-boot disabled-P2P proof is still required. The server binds authenticated loopback only. No reserve, cgroup, thermal, swap, pressure, ownership or telemetry check was relaxed.

| Variant | Sampled worker RAM peak GiB | Swap peak MiB | Minimum free GPU0/GPU1 MiB, all phases | Maximum temperatures C |
| --- | ---: | ---: | --- | --- |
| plain | 11.20 | 0 | [2729.0, 9928.0] | [56.0, 27.0] |
| drafted | 11.08 | 0 | [1359.0, 9928.0] | [64.0, 27.0] |

There were 28 plain and 50 drafted lifecycle samples, median intervals 2.081/2.073 seconds. Observed swap-in/out page deltas and cgroup high/max/OOM events were zero; no guard violation occurred. Host available RAM stayed >=24.86/24.62 GiB. Drafted post-first-nonloading-sample free minima were 1489/9928 MiB; its 1359 MiB overall GPU0 minimum occurred earlier. Sampled extrema are not guaranteed peaks. Short inference periods do not establish sustained swap/PSI qualification.

## Retained failures and corrections

- Plain8K loaded, but DSH's pi-ai estimate plus its4096-token safety allowance clamped max_tokens to1. Only the literal tool-call opener was emitted; no tool passed. CPU-only captures in the same isolated workspace proved8K sends1, while16K and12K send128. The16K plain correction passed. An initial CPU diagnostic used repository cwd and picked up repository instructions; it was corrected to the isolated workspace before drawing the budget conclusion. Its separate failed diagnostic path reference is also retained. No model benchmark was repeated to obtain a nicer number.
- Drafted16K was refused by native memory admission before readiness:1.96GiB required for a stream,1.78GiB available after8.60GiB model storage and the native1GiB reserve. That reserve remained unchanged. The calculated12K candidate needs1.71GiB and passed.
- The first12K launch was refused by systemd because the stopped failed transient unit still occupied its name; no model process started. Its exact owned executable and zero PID were checked before clearing only that unit's failed state and launching12K.

Every owned attempt released GPU resources and its reservation. Final maintained and experimental workers are inactive; GPU allocation returned to1MiB each. API/hub/DSH invocations are preserved. No fallback was preloaded and neither variant is selected in the maintained catalog.

## Screenshot: Unsloth Flash-Next Dynamic v3.1

The [publisher guide](https://unsloth.ai/docs/models/qwen3.8-next) and [model card](https://huggingface.co/unsloth/Qwen3.8-Flash-Next-GGUF) confirm the November4 Dynamic v3.1 release. The publisher's roughly15% benchmark advantage concerns accuracy against comparable quantizations on its suite, not15% faster inference or a guaranteed gain on every task.

Current file metadata is pinned at [revision d96201194f103c906994f283f504209dc8d2a10c](https://huggingface.co/unsloth/Qwen3.8-Flash-Next-GGUF/tree/d96201194f103c906994f283f504209dc8d2a10c). Its new smallest packages are smaller than the guide's older requirements table:

| Quant | All checkpoint shards GB | N-gram table GB | Other shards GB |
| --- | ---: | ---: | ---: |
| UD-IQ1_S | 66.38 | 28.80 | 37.58 |
| UD-IQ1_M | 68.01 | 28.80 | 39.21 |
| UD-Q2_K_XL | 79.58 | 28.80 | 50.78 |
| UD-IQ3_XXS | 83.63 | 28.80 | 54.83 |

The guide explicitly permits SSD-mapped PLE/n-gram tables. Thus the screenshot's32GB+ claim is plausible with the smallest quant and suitable offloading: IQ1_S has37.58GB outside its28.80GB table, and this server has32GB host RAM plus22GiB aggregate VRAM. This is a capacity hypothesis, not a measured fit: RAM/VRAM are separate pools, runtime overhead and cache traffic matter, and the serving engine must actually support that placement within our guards. Existing larger IQ3 settings must not be restored based on this arithmetic. A separate isolated IQ1_S qualification is the appropriate next study. No Flash-Next weights were downloaded, existing disabled profiles remain disabled, and no256K quality claim was tested here.

[Machine-readable evidence](benchmark-results/20261104-tensorfold-and-unsloth.json). [TensorFold release](https://github.com/ashhart/TensorFold/releases/tag/v1.2.2) and [native recipe](https://github.com/ashhart/TensorFold/blob/v1.2.2/docs/recipes/qwen3.8-27b.md).
