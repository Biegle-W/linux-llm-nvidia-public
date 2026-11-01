# Unsloth DeepSeek on Maya — November 1, 2026

DeepSeek/Maya now uses the same existing Unsloth Dynamic3.1 UD-IQ1_S GGUF shards as the separate Strata option, at 32,768 context. The previous Maya-S Strata entry is retired. Weight deletion is separately gated on replacement success and an all-process mapping/open-file check.

An isolated Maya v1.1.46 build (3589d6f12a3f77e813b184b51a586f8fc3de2185), compiled for SM86, retains the bounded file-cache controller. Its clean-page eviction/concurrent-read test passed. The router checks its exact binary hash through config/maya-unsloth-runtime.json. Previous binaries remain available.

The previous v1.1.29 runtime rejected Q6_K attention matrices as an unsupported matrix layout. The newer runtime loads them. A 128-token prefill chunk candidate was cancelled for poor prompt throughput; the selected 4,096-token prefill chunk completed an actual DSH read tool and matching tool result in 142.20 seconds. This is functional tool evidence, not a speed benchmark or full-context qualification. Vision is disabled for this configuration.

RAM/VRAM, pressure, temperature, swap, storage and worker-budget guards remain enabled. The bounded file cache remains 36 GiB. All eight retained profiles have a router-managed 600-second idle deadline in addition to existing native adapters. Thirteen focused idle tests passed, including preserving active inference for every original profile. No timed idle soak was run.

The obsolete Maya-S checkpoint was removed only after replacement tool success and the all-process mapping/open-file safety check. The recorded removal recovered 339.49 decimal GB (316.17 GiB); active Unsloth shards and earlier benchmark evidence remain. [Current short-tool observations](SHORT-TOOL-BENCHMARKS-20261101.md).
