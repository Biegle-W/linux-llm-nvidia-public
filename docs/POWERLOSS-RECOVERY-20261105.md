# Power-loss recovery verified — November 5, 2026

The NVIDIA LLM setup resumed successfully after the reported unexpected power loss. The earlier IQ1_S deletion and both repository pushes had completed before the outage; there was no interrupted model migration or updater transaction to resume. No stale GPU reservation, pending publication or leftover inference worker was found. Selected models, contexts, RAM/VRAM/thermal/swap guards and engine pins remain unchanged.

## Boot, storage and integrity

Current kernel`7.0.0-42-generic` and NVIDIA`615.71.09` passed the installed root-owned GPU unlock audit. The same audit verified target-kernel initramfs, GRUB and16 unlock firmware files for next-boot readiness. The actual current-boot root-owned transport proof passed: direct CPU PCIe4x8/x8, host-staged transfers and no CUDA P2P in either direction. No ownership or transport check was disabled.

The expected SATA filesystem is mounted, all nine selected text checkpoint directories and both image/video stores are accessible, and both DSH profiles contain the nine current text entries. The full SHA256 of every IQ1_M checkpoint shard—68.007GB total—matches the publisher pins. The selected native pack, runtime files, preset and tokenizer binding also verified. The retired IQ1_S directory remains absent; IQ1_M's28.800GB n-gram table remains intact with one hardlink. Other model directories were checked for accessibility, not subjected to another complete weight-hash or inference suite.

API and hub returned200 and DSH and the daily timer started automatically. No model-service repair or resource-policy change was required. These checks do not establish the cause of the power loss; older allocation errors elsewhere in the previous boot are not evidence of the outage's cause.

## One guarded post-boot inference check

IQ1_M passed actual DSH read-tool execution, matching tool result, exact proof follow-up, resource guards and owned unload. The worker was left unloaded; no fallback was preloaded.

| Model / quant | Engine | Prefill tok/s | First token s | Decode tok/s | Context | Prompt/output tokens | Cached tokens |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Flash-Next UD-IQ1_M +MTP | Strata0.2.11 /engine0.1.57 |1094.5|5.283|78.4|131,072|5595/39|0|

Loading and follow-up are excluded. OS file caches were not dropped; integrity hashing had read the weights. This is one short functional recovery observation, not sustained/full-window qualification or a matched performance comparison. Earlier selected-configuration benchmarks are preserved.

| Profile | Worker RAM high/max GiB | Host available floor | GPU policy | Swap write/combined MiB/s over30s |
| --- | ---: | ---: | --- | ---: |
| Flash-Next IQ1_M /Strata |87.76985/89.76985|2GiB|256MiB free/card;1024MiB native cache reserve/card|128/160|

Unlimited swap occupancy; active full PSI15% with three bad samples after its30-second window; no separate loading PSI threshold;100C temperature stops; three bad2-second resource samples; fail-closed telemetry; concurrency1, swappiness60 and idle600s remain. These are configured limits, not measured usage. Short calls may not fill an averaging window.

The model services and updater timer are healthy, inference workers are inactive and no transaction/reservation remains. The previous cleanup and selected IQ1_M setup are preserved. Next action is normal use; this recovery did not rerun all models or change hardware, drivers, firmware or model placement.

[Sanitized recovery evidence](validation-results/20261105-powerloss-recovery.json). [Selected IQ1_M qualification](FLASH-IQ1M-STRATA-20261105.md). [Completed IQ1_S deletion](IQ1S-WEIGHT-REMOVAL-20261105.md).
