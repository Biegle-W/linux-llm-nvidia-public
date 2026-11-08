# Restored 64GB worker RAM policy — October 31, 2026

Linux reports 61.3013 GiB usable from the restored 64GB installation. All six selected MoE profiles now use **56 GiB MemoryHigh / 58 GiB MemoryMax**. This replaces their 44–46/48GiB caps and leaves approximately 3.3 GiB outside the worker. The two GPU-resident Qwen profiles remain explicitly uncapped, as previously selected.

Affected profiles: Flash-Next/Strata,GLM/Maya,DeepSeek Maya-S/Strata,DeepSeek Maya-S/Maya,Bolt/vLLM-offload,and Unsloth DeepSeek/Strata. The catalog defaults and bounded-MoE validator also use the restored-RAM ceiling. Production router workers and update qualification read these values from the catalog. The generic experimental launcher retains its separate conservative sandbox limits; current MoE profiles launch through the router.

The independent 2 GiB host-available stop remains active. GPU reserves,swap-rate limits,pressure and temperature guards,idle 600 seconds,contexts,CPU expert-store sizes,precision and model files were not changed. Higher caps provide headroom; they do not force a worker to consume 58 GiB or override the host reserve. Existing benchmark records and their old test limits remain historical evidence.

The router was idle and no inference worker was active. It was restarted to load the updated validator. All eight profile budgets were verified in actual transient kernel cgroups using lightweight probes,without loading model weights or allocating the limits. All 321 CPU regression tests passed,including host-memory,swap and thermal stops. These checks establish configured and enforced limits; they do not claim new model-speed or larger-context qualification.

[Numeric evidence](validation-results/20261031-worker-ram-64gb.json).
