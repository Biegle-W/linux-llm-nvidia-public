# NVIDIA Nemotron setup and short DSH checks — November 1, 2026

Bolt and Super are registered under the single **NVIDIA Server Router** provider in DSH. Both use 65,536-token configured contexts, explicit 4,096-token output caps and their independently pinned text-only vLLM runtimes. The same guarded router serves all maintained model entries.

Super's loader calculated 81,477 KV tokens with 384 MiB BF16 KV per GPU; 65,536 retains capacity headroom. Placement remains 6/1 resident expert layers, 12/20 CPU input-projection layers, 0/40 GPU output projections, and at most 2,048 MiB processed clean file backing per rank on NVMe. Source weights remain on SATA. No input truncation or weight-precision change was introduced.

Current verification uses a short real DSH `read` call on a tiny local fixture and checks the matching completed tool result. Both Nemotron checks passed and the owned workers unloaded. Extra answer generation is not required by this tool-only smoke. This verifies the harness tool path; it is not comprehensive agent-quality testing or full-window validation.

Super also passed normal-router arithmetic/JSON with greedy and nonzero-temperature native sampling. Its guarded load took 305.02 seconds. Super is slow on this offload configuration; successful tool execution does not imply interactive response speed.

The configured Super-only swap allowance is bounded to 64 MiB/s writes and 96 MiB/s combined reads/writes over 30 seconds. The earlier 32/64 normal-router long request stopped at 32.63/64.98MiB/s. At that stop host available RAM stayed above 5.31 GiB, GPU reserves were 727/995 MiB, maximum GPU temperature 54 C and maximum pressure 0.18%. Independent 2 GiB host RAM, 512 MiB GPU, 82 C temperature, 10% active/15% loading pressure, 56/58 GiB worker limits, telemetry, swappiness 60 and idle 600 remain intact. Other profiles retain their limits.

Historical evidence remains separate: the isolated 32/64 run passed 58,985-token retrieval, 64-token streaming and tool checks. The later 64/96 normal-router long suite was cancelled at the user's request and is not reported as complete. Default context setup now uses calculated RAM/VRAM/KV capacity plus a short actual harness tool check and unload. Full-context retrieval, generation stress, repeated reload or timed idle tests require an explicit request.

All 350 CPU regressions passed, plus the two focused provider-migration cases. See [numeric scope and measurements](validation-results/20261101-super-context.json), [DSH provider/API cleanup](DSH-ROUTER-CLEANUP-20261101.md) and [context validation policy](CONTEXT-VALIDATION-POLICY-20261101.md).
