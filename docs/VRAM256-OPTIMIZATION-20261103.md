# 256 MiB reruns and continued optimization — November 3, 2026

Hardware: RTX 3080 Ti 12 GB + RTX 3080 10 GB, 64 GB installed RAM. The graphical desktop was active during these tests and used the second GPU. The free-VRAM stop floor is256 MiB per card; all other guards are retained. These are short per-arm observations, not full-context or sustained qualifications. Each arm includes bounded chat observations, one actual DSH read-tool call, matching result/follow-up, owned unload and transactional restoration. Selection decisions follow the measured results below. Earlier measurements remain historical.

Model loading and the follow-up answer are excluded from first-tool-call timing. Native request timings or one-request engine counters measure decode; generated tool arguments count as output. Client TTFT includes parser buffering where engine counters are absent. Prompts differ slightly in fixture path/nonce and token counts; single observations do not establish a lasting gain. DeepSeek/Strata restores conversation prefixes; report its cached suffix separately.

## Outcome

**GLM/Maya selects the 1.1.50 engine in normal mode at unchanged 65,536 context.** Two fresh baseline/candidate pairs passed actual tool/result/follow-up, resource checks, owned unload and restoration. Tool-call decode 5.5→6.8 and5.8→6.8 tok/s (+23.6%/+17.2%). Prefill 300.5→316.6 and 304.9→297.5 tok/s; TTFT 18.543→17.531 and 18.276→18.663 s. Prefill was mixed, so this is a confirmed decoding gain rather than a promise that every prompt is faster. All four tool calls reported zero cached tokens.

The selected executable has a versioned location and an enforced binary/profile/hash manifest. The previous engine and configuration remain archived. A separate normal authenticated-router tool/result check and owned unload passed after selection: 342.4 prefill tok/s, 16.310 s TTFT, 7.1 decode tok/s. That verification is an additional short observation, not another matched gain estimate. Nineteen focused CPU checks passed, including updater activation/rollback keeping the binary and manifest together.

Retain the other selected settings:

- HyperQwen: the 86,016-context baseline and allocator-GC0.8 repair both crossed below 256 MiB during loading. A 0.25 GiB/card CPU-offload trial was rejected before loading by the existing dense-weight residency check. No policy check was bypassed. The desktop remained active on the second GPU; these are not fully headless measurements.
- SGLang: the non-MTP 57,344-context baseline passed. MTP3 still failed CUDA graph capture with OOM. MTP3 eager fell below 256 MiB and was stopped by missing running-request telemetry; MTP1 eager also fell below 256 MiB. Failed arms were unloaded and restored; retain non-MTP.
- Bolt: the baseline passed. Pinned host-offload was again killed during loading by systemd-oomd, with journal peaks 56 GiB RAM / 3.1 GiB swap. The bounded deactivation wait allowed verified rollback. Prefetch-two passed tool/result/follow-up, but tool decode 0.39225→0.39256 tok/s and prefill 240.66→239.88 tok/s showed no material gain. Retain prefetch-one.
- DeepSeek/Maya: baseline, 1.1.50 normal and P2P-flag arms passed. Tool prefill 198.8/189.4/185.6 tok/s, TTFT 28.660/30.110/30.713 s, decode 4.8/5.0/5.0 tok/s; all uncached. Longer-prompt prefill 164.8/158.7/155.0 tok/s was also slower on the candidates. Retain the installed 1.1.46 controller/runtime. The current quant has nine 256-value blocks across its 2304-wide expert dimension; requested TP2 falls back to TP1 with separate layers per GPU. The new P2P all-reduce path was not active, so the flag arm is not a successful P2P-performance experiment.

All provisional trials restored their preimages after owned unload. GLM was selected separately and verified through the normal router. Model weights, configured contexts, expert/cache settings, 256 MiB free-VRAM checks, RAM/swap/thermal/telemetry/ownership guards and 600-second idle policy were preserved. The previously selected Strata prefill 512 remains unchanged. No XS weights, Turbo, full-context or sustained tests were added.

## P2P transport evidence

| Engine | Current evidence |
|---|---|
| HyperQwen | NCCL P2P/CUMEM initialized; current desktop VRAM qualification failed. Historical matched P2P-on/off gains are retained. |
| SGLang | NCCL P2P/IPC observed in the passing non-MTP baseline. Historical matched P2P-on/off gains are retained. |
| Bolt | NCCL P2P/CUMEM observed; no separate causal gain measured. |
| DeepSeek/Maya new all-reduce | Inactive because current quant forces TP2→TP1 fallback. This does not establish that every cross-layer copy avoids peer transfers. |
| GLM/other native engines | No causal P2P-on/off speed claim from this batch. |

The [earlier matched dense study](GPU-PAIR-AUX-OPTIMIZATION-20261031.md) establishes P2P benefits on this machine under its dated contexts and guards. It does not compare the existing switch against a working direct CPU x8/x8 motherboard. New topology requires fresh peer-read/write correctness and transport verification.

## Build and method

Both engine binaries were built from [Maya v1.1.50](https://github.com/mw00/project-maya/releases/tag/v1.1.50), commit 10e69a0, using the unchanged pinned ggml dependency. The existing 75% bounded file-cache controller was retained for the DeepSeek candidate and passed its CPU check. Build scope: CPU 200%, RAM high 6 GiB / max 8 GiB, two jobs. Only the GLM engine binary is selected; the guarded router/frontend remains in place. The [PyTorch allocator option](https://docs.pytorch.org/docs/2.15/notes/cuda.html#optimizing-memory-usage-with-pytorch-cuda-alloc-conf) was a failed repair screen, not a selected setting.

Seventeen arm records: 10 passed and 7 failed/rejected, plus the selected GLM normal-router validation. Single short observations retain token/cache counts below. Conversation prefixes were not globally cleared; the dedicated longer-prompt observation checks cached-prefix counts, and all listed first-tool calls in this batch reported zero cached tokens. Earlier benchmark history remains unchanged.

## VRAM-only

| Model / quant | Engine / arm | Prefill (tok/s) | Time to first token (s) | Decode (tok/s) | Context limit (tokens) | Storage size (GB) | Storage location |
|---|---|---:|---:|---:|---:|---:|---|
| Qwen3.8-27B / AutoRound INT4, INT8 embedding | HyperQwen-vLLM: baseline (000007) | Not measured | Not measured | Not measured | 86016 | 15.79 | SATA SSD: models/engine-tests/qwen38-27b-hyperqwen-fast |
| Qwen3.8-27B / AutoRound INT4, INT8 embedding | HyperQwen-vLLM: allocator-gc80 (002257) | Not measured | Not measured | Not measured | 86016 | 15.79 | SATA SSD: models/engine-tests/qwen38-27b-hyperqwen-fast |
| Qwen3.8-27B / AutoRound INT4, INT8 embedding | SGLang: baseline (000140) | 2351.623 | 2.636 | 59.031 | 57344 | 15.79 | SATA SSD: models/engine-tests/qwen38-27b-hyperqwen-fast |
| Qwen3.8-27B / AutoRound INT4, INT8 embedding | SGLang: mtp3 (000140) | Not measured | Not measured | Not measured | 57344 | 15.79 | SATA SSD: models/engine-tests/qwen38-27b-hyperqwen-fast |
| Qwen3.8-27B / AutoRound INT4, INT8 embedding | SGLang: mtp3-eager (002426) | Not measured | Not measured | Not measured | 57344 | 15.79 | SATA SSD: models/engine-tests/qwen38-27b-hyperqwen-fast |
| Qwen3.8-27B / AutoRound INT4, INT8 embedding | SGLang: mtp1-eager (003318) | Not measured | Not measured | Not measured | 57344 | 15.79 | SATA SSD: models/engine-tests/qwen38-27b-hyperqwen-fast |

## CPU RAM offload

| Model / quant | Engine / arm | Prefill (tok/s) | Time to first token (s) | Decode (tok/s) | Context limit (tokens) | Storage size (GB) | Storage location |
|---|---|---:|---:|---:|---:|---:|---|
| Nemotron-3.5-Bolt-74B-A9B / AWQ INT4 | vLLM offload: baseline (000304) | 240.662 | 26.452 | 0.392 | 163840 | 55.33 | SATA SSD: models/bolt-awq-int4 |
| Nemotron-3.5-Bolt-74B-A9B / AWQ INT4 | vLLM offload: pinned-host-offload (000304) | Not measured | Not measured | Not measured | 163840 | 55.33 | SATA SSD: models/bolt-awq-int4 |
| Nemotron-3.5-Bolt-74B-A9B / AWQ INT4 | vLLM offload: prefetch-two (000304) | 239.877 | 26.526 | 0.393 | 163840 | 55.33 | SATA SSD: models/bolt-awq-int4 |

## SSD streaming

| Model / quant | Engine / arm | Prefill (tok/s) | Time to first token (s) | Decode (tok/s) | Context limit (tokens) | Storage size (GB) | Storage location |
|---|---|---:|---:|---:|---:|---:|---|
| GLM-5.3-Flash / Maya-S24 | Maya: baseline (003507) | 300.500 | 18.543 | 5.500 | 65536 | 94.70 | NVMe SSD: models/maya/Maya-S24 |
| GLM-5.3-Flash / Maya-S24 | Maya: baseline-confirm (003507) | 304.900 | 18.276 | 5.800 | 65536 | 94.70 | NVMe SSD: models/maya/Maya-S24 |
| GLM-5.3-Flash / Maya-S24 | Maya: maya150-normal (003507) | 316.600 | 17.531 | 6.800 | 65536 | 94.70 | NVMe SSD: models/maya/Maya-S24 |
| GLM-5.3-Flash / Maya-S24 | Maya: maya150-normal-confirm (003507) | 297.500 | 18.663 | 6.800 | 65536 | 94.70 | NVMe SSD: models/maya/Maya-S24 |
| DeepSeek-V4.1-Flash-1017 / UD-IQ1_S | Maya: baseline (004512) | 198.800 | 28.660 | 4.800 | 32768 | 232.98 | NVMe core + SATA Engram: models/unsloth/deepseek-v41-1017-dynamic31-8a6ec9cf/UD-IQ1_S |
| DeepSeek-V4.1-Flash-1017 / UD-IQ1_S | Maya: maya150-normal (004512) | 189.400 | 30.110 | 5.000 | 32768 | 232.98 | NVMe core + SATA Engram: models/unsloth/deepseek-v41-1017-dynamic31-8a6ec9cf/UD-IQ1_S |
| DeepSeek-V4.1-Flash-1017 / UD-IQ1_S | Maya: maya150-p2p (004512) | 185.600 | 30.713 | 5.000 | 32768 | 232.98 | NVMe core + SATA Engram: models/unsloth/deepseek-v41-1017-dynamic31-8a6ec9cf/UD-IQ1_S |

## Unclassified placement attempt

| Model / quant | Engine / arm | Prefill (tok/s) | Time to first token (s) | Decode (tok/s) | Context limit (tokens) | Storage size (GB) | Storage location |
|---|---|---:|---:|---:|---:|---:|---|
| Qwen3.8-27B / AutoRound INT4, INT8 embedding | HyperQwen-vLLM (CPU offload requested; rejected before loading): cpu-quarter (003301) | Not measured | Not measured | Not measured | Not reached | 15.79 | SATA SSD: models/engine-tests/qwen38-27b-hyperqwen-fast |

## Correctness and cache attribution

| Profile / arm | Input / cached / output tokens | Result |
|---|---:|---|
| qwen27b-hyperqwen / baseline (000007) | — / — / — | FAIL: Dense GPU headroom below 256 MiB; unload/restoration True |
| qwen27b-hyperqwen / allocator-gc80 (002257) | — / — / — | FAIL: Dense GPU headroom below 256 MiB; unload/restoration True |
| qwen27b-hyperqwen / cpu-quarter (003301) | — / — / — | FAIL: Dense weight offload is not qualified: qwen27b-hyperqwen; unload/restoration True |
| qwen27b-sglang / baseline (000140) | 6129 / 0 / 70 | PASS; unload and restoration verified |
| qwen27b-sglang / mtp3 (000140) | — / — / — | FAIL: Worker stopped during loading; inspect its journal.; unload/restoration True |
| qwen27b-sglang / mtp3-eager (002426) | — / — / — | FAIL: Remote end closed connection without response; unload/restoration True |
| qwen27b-sglang / mtp1-eager (003318) | — / — / — | FAIL: Dense GPU headroom below 256 MiB; unload/restoration True |
| bolt-vllm / baseline (000304) | 6364 / 0 / 41 | PASS; unload and restoration verified |
| bolt-vllm / pinned-host-offload (000304) | — / — / — | FAIL: Worker stopped during loading; inspect its journal.; unload/restoration True |
| bolt-vllm / prefetch-two (000304) | 6361 / 0 / 42 | PASS; unload and restoration verified |
| glm-maya / baseline (003507) | 5432 / 0 / 26 | PASS; unload and restoration verified |
| glm-maya / baseline-confirm (003507) | 5429 / 0 / 25 | PASS; unload and restoration verified |
| glm-maya / maya150-normal (003507) | 5426 / 0 / 24 | PASS; unload and restoration verified |
| glm-maya / maya150-normal-confirm (003507) | 5432 / 0 / 26 | PASS; unload and restoration verified |
| deepseek-maya / baseline (004512) | 5693 / 0 / 63 | PASS; unload and restoration verified |
| deepseek-maya / maya150-normal (004512) | 5699 / 0 / 61 | PASS; unload and restoration verified |
| deepseek-maya / maya150-p2p (004512) | 5696 / 0 / 65 | PASS; unload and restoration verified |

## Resource guards

| Model / quant | Engine | RAM guards | VRAM guards | Swap guards |
|---|---|---|---|---|
| Qwen3.8-27B / AutoRound INT4, INT8 embedding | HyperQwen-vLLM | Worker high/max unlimited/unlimited GiB; host available ≥2 GiB; inference PSI 10% for 3 samples | Free floor 256 MiB/GPU; native cache reserve not applicable MiB; startup admission [9728, 8960] | Occupancy unlimited; writes ≤1 MiB/s; combined R+W ≤8 MiB/s over 30 s; first violating complete active window stops |
| Qwen3.8-27B / AutoRound INT4, INT8 embedding | SGLang | Worker high/max unlimited/unlimited GiB; host available ≥2 GiB; inference PSI 10% for 3 samples | Free floor 256 MiB/GPU; native cache reserve not applicable MiB; startup admission [11520, 8960] | Occupancy unlimited; writes ≤1 MiB/s; combined R+W ≤8 MiB/s over 30 s; first violating complete active window stops |
| Nemotron-3.5-Bolt-74B-A9B / AWQ INT4 | vLLM offload | Worker high/max 56/58 GiB; host available ≥2 GiB; inference PSI 10% for 3 samples | Free floor 256 MiB/GPU; native cache reserve not applicable MiB; startup admission native policy | Occupancy unlimited; writes ≤1 MiB/s; combined R+W ≤8 MiB/s over 30 s; first violating complete active window stops |
| GLM-5.3-Flash / Maya-S24 | Maya | Worker high/max 56/58 GiB; host available ≥2 GiB; inference PSI 10% for 3 samples | Free floor native policy MiB/GPU; native cache reserve 1024 MiB; startup admission native policy | Occupancy unlimited; writes ≤128 MiB/s; combined R+W ≤160 MiB/s over 30 s; first violating complete active window stops |
| DeepSeek-V4.1-Flash-1017 / UD-IQ1_S | Maya | Worker high/max 56/58 GiB; host available ≥2 GiB; inference PSI 15% for 3 samples | Free floor native policy MiB/GPU; native cache reserve 1024 MiB; startup admission native policy | Occupancy unlimited; writes ≤128 MiB/s; combined R+W ≤160 MiB/s over 30 s; first violating complete active window stops |

Independent qualification samples every 2 seconds and rejects any sampled host-floor, dense-VRAM, telemetry, memory-event or ≥82°C thermal violation; production supervisors also retain their sustained-sample rules. Swap active-window enforcement excludes loading and idle. Effective configured limits are not measured peaks. SGLang and HyperQwen both use the shared256 MiB floor; no legacy448 MiB override is used. Unlimited swap occupancy does not remove swap-I/O limits.

Base weights use decimal GB, excluding auxiliary packs and caches. Qwen engines share a checkpoint; DeepSeek engines share 232.98 GB (122.38 GB NVMe core + 110.60 GB SATA Engram). Configured contexts are retained limits, not newly tested full-window claims.

[Numeric evidence](benchmark-results/20261103-vram256-optimization.json).
