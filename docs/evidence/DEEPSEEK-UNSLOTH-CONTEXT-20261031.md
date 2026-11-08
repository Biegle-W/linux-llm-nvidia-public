# Additional Unsloth DeepSeek Strata profile — October 31, 2026

**Selected context: 32,768 tokens.** The normal Strata shortcut now includes **DeepSeek-V4.1-Flash-1017 / Unsloth Dynamic3.1 UD-IQ1_S / Strata** as an additional option. The existing Qwen/Strata and DeepSeek Maya-S/Strata options remain available with their original settings. All original seven profile objects were preserved.

Use the Strata desktop shortcut and select the Unsloth entry, or run `./scripts/start_model.sh strata-unsloth`. Its router model ID is `deepseek-unsloth-strata`. Existing API clients use the same router; only the selected model ID changes.

## Context qualification

The requested scope was a practical default up to 32K. Each completed screen used arithmetic and a separate exact-JSON check, then three independently generated access codes placed at the start/middle/end of a prompt near 90% of the allocated window, then one complete 256-token stream. Returned usage confirmed the actual prompt-token count. Both GPUs were used through the engine's layer-split fallback because the expert width cannot divide into two whole quantization blocks for tensor splitting. All six experts remained enabled.

| Allocated context | Actual retrieval input | Retrieval result | Retrieval request wall time | Start-to-ready |
| ---: | ---: | --- | ---: | ---: |
| 8,192 | 7347 | pass | 309.3 s | 47.8 s |
| 32,768 | 29446 | pass-content | 901.8 s | 44.9 s |

The 32K retrieval returned all three correct codes wrapped in a Markdown JSON code fence. The initial strict raw-JSON checker recorded a formatting failure; its original output and failed state were preserved. Content evaluation was corrected without repeating the long inference. A separate fresh 32K load with identical engine arguments then passed arithmetic, exact JSON and the complete 256-token stream. This is a formatting deviation, not a resource or retrieval-content failure.

The selected 32,768-token window was actually exercised; this is not merely an allocation or startup check. Contexts above the selected setting are not qualified by this work. These synthetic retrieval checks do not establish general long-document reasoning quality. Long prompts remain slow because this is an SSD-streamed model.

## Normal-menu and lifecycle verification

Two independent fresh router loads passed arithmetic, JSON and complete streaming requests. The first also passed a separate three-marker prompt through the normal router. Unauthorized access returned HTTP 401; attempts to unload during each active stream returned HTTP 409 and the streams completed. Idle policy remains 600 seconds. Both verification loads were unloaded afterward; other applications and the DSH service were preserved.

## Runtime, storage and guards

The independent runtime uses the previously verified signed Strata 0.2.9/engine 0.1.55 release plus the existing managed idle adapter on a separate copy of its Python serving control. Engine, pack and serving-code hashes are checked before launch. The older Strata and Maya runtimes were not upgraded. New app state and engine prefix-cache storage are isolated and loading is offline-only. The first normal load used the previous shared prefix-cache folder, where the engine cleared four incompatible/incomplete KV snapshot entries; these are regenerable caches, not saved chat history. The new profile now explicitly uses its own prefix-cache directory, which was verified on the second load. No saved-chat API was used by these tests. This does not update the separate official desktop app.

All five previously verified GGUF shards were reused: 232,979,608,420 bytes in total. Core shards remain on NVMe and the Engram shard on SATA; explicit per-shard transport and size checks preserve that placement. No model weights were downloaded, duplicated or moved. The RTX3080Ti/3080 pair performs inference; the RTX3060 remains auxiliary and unused by this profile.

The qualified policy retains 46/48 GiB worker soft/hard limits, 2 GiB host reserve, 512 MiB free-VRAM guard, 768 MiB engine reserve, 82°C ceiling, all six experts, 36 decimal GB CPU expert store, and bounded 128 MiB/s swap writes /160 MiB/s combined swap I/O over 30 seconds. Loading and active full-memory pressure limits are 15%. Missing mandatory telemetry stops the owned worker. The engine reports prompt chunks of 256 despite the requested 128 flag; qualification uses that observed behavior. The new runtime is explicitly pinned in updater coverage so generic nightly source builds cannot replace it without package-specific requalification.

Detailed sampled resources, per-stream observations and normal-load checks are in the [numeric record](validation-results/20261031-unsloth-strata-context.json). Stream observations follow other requests and are not matched cold benchmarks or a causal comparison with the older quant.

## Regression checks

The 320-test CPU suite passed. A further 13 focused runtime/storage/cache-isolation checks passed after the final cache-path change. GPU-dependent qualification is recorded separately above.
