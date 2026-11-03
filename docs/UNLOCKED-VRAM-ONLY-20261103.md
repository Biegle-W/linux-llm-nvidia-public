# Unlocked VRAM-only results — November 3, 2026

Subsequent normal-use correction: native output buffering could still cause a false guard stop after a short test ended. See the [buffering repair and beyond-deadline streaming verification](PROVIDER-ABORT-BUFFERING-20261103.md). The speed observations below remain valid short observations, not a sustained-runtime qualification.

Both maintained VRAM-only engines pass one short actual DSH read/tool-result/assistant-follow-up and owned unload/resource-release check on the Z690 Carbon WiFi DDR5 / i9-13900KS / temporary 32 GB host. Intel UHD 770 runs the desktop. Both RTX cards use direct CPU PCIe4 x8/x8. Secure Boot is disabled and ordered early GPU unlock is VERIFIED. Stock NVIDIA 615.71.09 and the root-owned current-boot host-staged proof verify no CUDA peer capability; native NCCL logs confirm shared-memory channels both directions. No P2P driver or switch ACS routing was restored.

## VRAM-only observations

| Model / quant | Engine | Prefill (tok/s) | Time to first token (s) | Decode (tok/s) | Context limit (tokens) | Storage size (GB) | Storage location |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Qwen3.8-27B AutoRound INT4 / INT8 embedding | HyperQwen-vLLM | 2082.6 | 2.810 | 62.52 | 86,016 | 15.792 | Samsung SATA: models/engine-tests/qwen38-27b-hyperqwen-fast (shared) |
| Qwen3.8-27B AutoRound INT4 / INT8 embedding | SGLang | 2210.1 | 2.888 | 60.17 | 57,344 | 15.792 | Samsung SATA: models/engine-tests/qwen38-27b-hyperqwen-fast (shared) |

The checkpoint is shared: 15,791,777,864 bytes in eight base safetensors shards, counted once physically. Ordinary host loading buffers and control work remain allowed. HyperQwen uses vLLM 0.31.0; SGLang is the pinned source at 62271fd7c8aa8fe9edebf04e00a414b7fbf64388. Native KV backing is 88,931 and 57,344 tokens respectively; these are allocation checks, not full-window quality tests.

HyperQwen's measured first request is 5,823 input / 39 output tokens; SGLang's is 6,095 / 39. Both report zero cached tokens. One successful observation per engine; different engine templates/input lengths, no aggregation or matched locked baseline. Prefill and decode use one-request native counters. Loading and the assistant follow-up are excluded from these speed measurements. TTFT uses the recorded engine counter where available, otherwise the first delivered client content/tool delta including parser buffering; exact methods are in the JSON evidence. No unlock speedup or controlled engine ranking is inferred.

## Effective guards

| Model / quant | Engine | RAM guards | VRAM guards | Swap guards |
| --- | --- | --- | --- | --- |
| Qwen3.8-27B INT4/INT8 | HyperQwen-vLLM | 24/26 GiB high/max; host available >=2 GiB | Free >=256 MiB per GPU after readiness; startup >=9728/8960 MiB | Unlimited worker occupancy; write <=1, read+write <=8 MiB/s over 30 s |
| Qwen3.8-27B INT4/INT8 | SGLang | 24/26 GiB high/max; host available >=2 GiB | Free >=256 MiB per GPU after readiness; startup >=11520/8960 MiB | Unlimited worker occupancy; write <=1, read+write <=8 MiB/s over 30 s |

The host-memory, GPU-temperature (82 C) and readiness VRAM conditions stop on three consecutive samples, sampled every two seconds. Dense loading has no separate PSI stop threshold; RAM/temperature and telemetry checks remain. During inference, full-memory PSI >10% stops after three bad samples once a complete 30-second window exists; a complete-window swap write/combined-rate violation stops immediately. Outside inference that I/O/PSI window resets. Missing owned telemetry stops after three bad samples. The host currently has an 8 GiB swap file; unlimited worker occupancy does not remove I/O or pressure checks. The native allocation reserves and startup admissions remain separate from the active free-VRAM floor. Short requests do not exercise the full 30-second inference window or establish sustained-swap qualification.

## Sampled resource use

| Engine | Sampled worker RAM peak (GiB) | Worker swap peak (MiB) | Free VRAM minimum, all phases (MiB) | Free VRAM minimum after first ready telemetry (MiB) | Maximum GPU temperatures (C) |
| --- | ---: | ---: | --- | --- | --- |
| HyperQwen-vLLM | 7.43 | 0 | [1876.0, 143.0] | [3288.0, 1299.0] | [54.0, 45.0] |
| SGLang | 8.72 | 0 | [515.0, 1835.0] | [515.0, 1835.0] | [52.0, 42.0] |

The sampler targeted one-second intervals across loading, tool execution, follow-up and unload. Exact sample counts and median intervals are in the JSON. Extrema are sampled observations, not guaranteed absolute peaks/minima. Both successful runs sampled zero worker swap and zero host swap-in/out page deltas. The 143 MiB RTX 3080 observation occurred during HyperQwen loading, between two lifecycle samples labeled loading, before the readiness VRAM stop floor applies. Its post-readiness samples stayed >=1,299 MiB free on that card. SGLang retained >=515 MiB in its samples. Both test-owned workers are unloaded; baseline GPU allocation was restored within the 64 MiB release tolerance.

## Temporary model availability

Bolt and the four Flash-Next/GLM/DeepSeek streaming/offload profiles are disabled in normal selection and hidden from the API/DSH picker. All seven model definitions and their weights remain. Only HyperQwen and SGLang are enabled. The 32 GB installation is temporary while more RAM is coming; restoration requires explicit installation confirmation, measured capacity and guarded requalification, with no timer or automatic cache restoration.

## Repairs and retained failures

The first HyperQwen attempt stopped because an overlooked supervisor demanded P2P channels. The second stopped because metrics readiness preceded complete channel logging. Neither failure supplies a usable performance result, and both workers released cleanly. The corrected mode-aware guard requires the current-boot disabled-P2P proof plus both native SHM directions, permits at most 30 seconds for startup log completion, and immediately rejects actual peer channels. The final HyperQwen attempt passes. SGLang's successful short observation and saved native SHM log also pass the corrected validator; no extra SGLang reload was run just for a better number.

The timing tap now forwards the assistant's real follow-up request while measuring request one only. Temporary availability filtering preserves busy/ownership checks for any already-running disabled profile. All 97 focused CPU checks pass for routing, availability, transport, metrics, worker budgets, DSH registration and shutdown. No RAM/offload model, full-context retrieval or sustained stress test was run.

Machine-readable evidence: [20261103-unlocked-vram-only.json](benchmark-results/20261103-unlocked-vram-only.json). Historical results retain their older hardware, P2P, RAM and guard attribution.
