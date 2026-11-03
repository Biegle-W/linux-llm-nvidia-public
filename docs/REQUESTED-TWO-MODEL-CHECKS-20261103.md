# Requested checks of the two enabled models — November 3, 2026

The user confirmed that RAM has not been upgraded and requested tests of the two enabled models. Both passed one normal guarded load, an actual DSH read-tool call with a matching fixture result and exact assistant follow-up, then owned unload and GPU-release verification. HyperQwen finished and released before SGLang selection. Both workers are inactive, both GPUs returned to 1 MiB used, API/hub/DSH remain active, and no GPU reservation remains. No selected setting or guard changed.

## VRAM-only models

| Model / quant | Engine | Prefill (tok/s) | Time to first token (s) | Decode (tok/s) | Context limit (tokens) | Storage size (GB) | Storage location |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Qwen3.8-27B / AutoRound INT4, INT8 embedding | HyperQwen-vLLM | 2077.9 | 2.821 | 62.53 | 86,016 | 15.792 | Samsung SATA: models/engine-tests/qwen38-27b-hyperqwen-fast (shared) |
| Qwen3.8-27B / AutoRound INT4, INT8 embedding | SGLang | 2137.9 | 3.044 | 60.20 | 57,344 | 15.792 | Samsung SATA: models/engine-tests/qwen38-27b-hyperqwen-fast (shared) |

The same eight safetensors files total 15,791,777,864 bytes and are counted once physically. HyperQwen uses vLLM 0.31.0; SGLang retains source 62271fd7c8aa8fe9edebf04e00a414b7fbf64388. These are single uncached short observations with different engine templates/input lengths, not matched engine rankings or sustained/full-context qualification. Loading and assistant follow-up are excluded from speed metrics. Tool arguments count as output. HyperQwen measures 5,829 input / 41 output tokens with native prefill, first-token and decode counters; SGLang measures 6,092 / 38 with native prefill/inter-token timing and client first delivered content/tool delta for TTFT, including parser buffering. Both report zero cached tokens. Actual tool/result/follow-up wall times are 8.013 seconds each. Unload duration was not separately timed; owned inactivity and return to baseline within the 64 MiB release tolerance were verified.

SGLang logged 57,344 KV tokens on each native rank. HyperQwen's normal guarded context admission passed, but its native KV log was not separately archived before the next engine replaced the shared log; its prior 88,931-token evidence remains historical. No new full-window quality claim is made.

## Effective guards

| Model / quant | Engine | RAM guards | VRAM guards | Swap guards |
| --- | --- | --- | --- | --- |
| Qwen3.8-27B INT4/INT8 | HyperQwen-vLLM | 24/26 GiB high/max; host available >=2 GiB | Free >=256 MiB each after readiness; startup >=9728/8960 MiB | Unlimited occupancy; writes <=1, combined <=8 MiB/s over 30 s |
| Qwen3.8-27B INT4/INT8 | SGLang | 24/26 GiB high/max; host available >=2 GiB | Free >=256 MiB each after readiness; startup >=11520/8960 MiB | Unlimited occupancy; writes <=1, combined <=8 MiB/s over 30 s |

Actual cgroup memory.high/max readbacks are 25,769,803,776 / 27,917,287,424 bytes; memory.swap.max is max. RAM, readiness VRAM and 82 C temperature stops use three consecutive samples at two-second intervals. Dense loading has no separate PSI threshold. During inference, full-memory PSI >10% stops after three bad samples once a complete 30-second window exists; a complete-window swap-I/O violation stops immediately. The inference I/O/PSI window resets outside inference. Missing telemetry fails closed after three samples. Host swappiness60, idle600 and ownership/transport protections remain. The current-boot root-owned host-staged proof passed; CUDA peer access remains disabled both ways. Short requests do not exercise a full 30-second active-inference window.

## Sampled usage

| Engine | Worker RAM peak (GiB) | Worker swap peak (MiB) | Minimum free VRAM all phases (MiB) | Minimum free after first nonloading lifecycle sample (MiB) | Maximum GPU temperatures (C) |
| --- | ---: | ---: | --- | --- | --- |
| HyperQwen-vLLM | 22.13 | 0 | [1887.0, 28.0] | [3301.0, 1312.0] | [50.0, 41.0] |
| SGLang | 8.75 | 0 | [528.0, 1847.0] | [528.0, 1847.0] | [54.0, 42.0] |

HyperQwen has 84 external samples at median 1.047-second intervals; SGLang has 34 at 1.034 seconds. Observed extrema are sampled, not absolute peaks. Host available RAM stayed >=20.62/19.75 GiB respectively. Both sampled zero worker swap and zero host swap-in/out page deltas. HyperQwen's 28 MiB RTX3080 transient occurred during loading: lifecycle samples on both sides still reported loading. The 256 MiB stop floor applies after readiness. Ready API free VRAM was 3305/1316 MiB; sampled post-readiness minima were 3301/1312 MiB. SGLang stayed >=528/1847 MiB. No guard was relaxed.

## RAM-offload models

None currently enabled or tested. Bolt remains disabled pending explicit RAM-upgrade confirmation, measured capacity and guarded qualification.

## SSD-streaming models

None currently enabled or tested. Flash-Next, GLM and both DeepSeek profiles remain disabled pending the same RAM upgrade and guarded qualification. Their historical measurements and failures remain unchanged. Daily updates remain paused.

Machine-readable results: [20261103-requested-two-model-checks.json](benchmark-results/20261103-requested-two-model-checks.json).
