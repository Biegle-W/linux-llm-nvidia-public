# All model RAM ceilings — November 5, 2026

All13 maintained entries now use the same worker RAM ceilings: **87.76984786987305GiB high /89.76984786987305GiB maximum** (displayed87.77/89.77). These are94,242,156,544 /96,389,640,192bytes, leaving exactly2GiB outside the hard cap on the verified98,537,123,840-byte Linux usable capacity. They are ceilings, not reservations or automatic allocations.

| Entry group | Coverage | High / max GiB |
| --- | --- | ---: |
| Dense text | Qwen27B HyperQwen, SGLang, TensorFold |87.77/89.77|
| Other text | Flash-Next Strata and llama.cpp; GLM Maya; DeepSeek Maya and Strata; Bolt native IQ2 |87.77/89.77|
| ComfyUI images | Qwen Image2.1 Turbo; FLUX3Klein |87.77/89.77|
| ComfyUI videos | Wan2.2 5B; LTX2.3 Mesh, every configured resolution |87.77/89.77|

The three dense profiles and shared ComfyUI image/video budget changed from32/36GiB. The other six text profiles already used these exact ceilings. The guarded dense launcher now reads the selected profile rather than hardcoding32/36. ComfyUI launch and admission checks read the same shared configuration. All profiles retain the installed-capacity preflight; ComfyUI also requires90GiB usable capacity for this selected setting. Generic unrelated experimental commands retain their existing smaller defaults, and updater/build coordinators retain their separate limits.

All other settings remain:2GiB host available floor, unlimited maintained-worker swap occupancy, existing per-profile swap I/O and PSI limits, VRAM floors/native reserves,100C stops, three bad2-second samples, fail-closed telemetry, concurrency1, swappiness60 and idle600s. This does not enable CPU weight offload, move embeddings or increase context/cache targets. TensorFold retains its existing host-mapped embedding arrangement.

## Verification

501 installed-project CPU regressions passed, including all selected RAM budgets, exact dense launcher arguments, rejection of foreign/wrong cgroups, shared ComfyUI budget validation, capacity checks and byte-exact2GiB headroom. Shell syntax, Python compilation and whitespace checks passed. A short owned systemd unit with no model or GPU work read actual `memory.high=94242156544`, `memory.max=96389640192` and `memory.swap.max=max`, and checked all nine text profiles plus shared image/video configuration. It exited successfully and was collected.

All inference workers were inactive before the change; no request or reservation was interrupted. The new limits apply on their next normal launch, without preloading models or restarting API/hub/DSH. No inference benchmark was rerun: historical performance and guard attribution remain dated evidence. The current benchmark ledger shows the newly selected ceilings, not a claim that earlier tests used them. No active test, lock or pending updater transaction remains. Next action is normal model use.

[Machine-readable verification](validation-results/20261105-all-model-ram-ceilings.json).
