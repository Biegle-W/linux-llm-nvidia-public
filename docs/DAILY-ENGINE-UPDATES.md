# NVIDIA daily engine updates

## November5 manual entry replacement

Flash-Next IQ1_M /Strata qualified through one guarded actual DSH tool/result/exact follow-up and owned unload, replacing IQ1_S /llama.cpp. Engine versions did not change. Future grouped Strata updates now include both Flash-Next quants and DeepSeek; llama.cpp qualifies Bolt only. [Results, guards and lifecycle verification](FLASH-IQ1M-STRATA-20261105.md).

## 2026-11-05T11:48:40

- strata: **promoted**; upstream `c3b3f5035506`.
  - `flash-next-strata`: 131072 context, 934.20 prefill tok/s, 68.40 decode tok/s, 6.460 s TTFT.
  - `deepseek-unsloth-strata`: 32768 context, 83.40 prefill tok/s, 11.80 decode tok/s, 68.423 s TTFT.

Effective guards (configured, not peak usage):2GiB host available;100C;3 bad2-second samples; unlimited swap occupancy; swap rates averaged over30s. Selected native reserves and active/loading PSI exceptions remain unchanged.

| Profile | Worker RAM high/max GiB | GPU policy | Active swap writes/combined | Active/loading PSI % |
| --- | ---: | --- | ---: | --- |
| qwen27b-hyperqwen | 32.00/36.00 | 256 MiB free/card after ready | 1/8 | 10 / none separately |
| qwen27b-sglang | 32.00/36.00 | 256 MiB free/card after ready | 1/8 | 10 / none separately |
| qwen27b-tensorfold | 32.00/36.00 | 256 MiB free/card after ready; GPU0; native1024 MiB reserve | 1/8 | 10 / none separately |
| flash-next-iq1s-llamacpp | 87.77/89.77 | 256 MiB free/card after ready; 1536 MiB fit targets | 128/160 | 15 / none separately |
| flash-next-strata | 87.77/89.77 | 1024 MiB native reserve | 128/160 | 15 / none separately |
| glm-maya | 87.77/89.77 | 1024 MiB native reserve | 128/160 | 10 / none separately |
| deepseek-maya | 87.77/89.77 | 1024 MiB native reserve | 128/160 | 15 / none separately |
| bolt-vllm | 87.77/89.77 | 256 MiB free/card after ready; 384 MiB fit targets | 1/8 | 10 / 15 |
| deepseek-unsloth-strata | 87.77/89.77 | 256 MiB free/card after ready; 1024 MiB native reserve | 128/160 | 15 / 15 |


## 2026-11-05T11:44:11

- tensorfold: **pinned-current**; upstream `v1.2.2`.
- comfyui: **pinned-current**; upstream `v0.44.0`.
- raylight: **pinned-current**; upstream `1.11.0`.
- mesh: **pinned-current**; upstream `3804156b4b39`.
- gguf: **pinned-current**; upstream `6ea2651e7df6`.
- strata: **rejected-production-preserved**; upstream `c3b3f5035506`.

## 2026-11-05T05:29:58

- hyperqwen: **unchanged**; upstream `6ab9bd05cb84`.
- sglang: **unchanged**; upstream `d61ded5b9e2d`.
- strata: **unchanged**; upstream `ffa80d73133e`.
- llamacpp: **unchanged**; upstream `cd959bae99ff`.
- tensorfold: **pinned-current**; upstream `v1.2.2`.
- comfyui: **pinned-current**; upstream `v0.44.0`.
- raylight: **pinned-current**; upstream `1.11.0`.
- mesh: **pinned-current**; upstream `3804156b4b39`.
- gguf: **pinned-current**; upstream `6ea2651e7df6`.
- maya: **rejected-production-preserved**; upstream `c1670044bbc0`.

## 2026-11-05T05:03:10

- hyperqwen: **unchanged**; upstream `6ab9bd05cb84`.
- sglang: **unchanged**; upstream `d61ded5b9e2d`.
- strata: **unchanged**; upstream `ffa80d73133e`.
- llamacpp: **unchanged**; upstream `cd959bae99ff`.
- tensorfold: **pinned-current**; upstream `v1.2.2`.
- comfyui: **pinned-current**; upstream `v0.44.0`.
- raylight: **pinned-current**; upstream `1.11.0`.
- mesh: **pinned-current**; upstream `3804156b4b39`.
- gguf: **pinned-current**; upstream `6ea2651e7df6`.
- maya: **rejected-production-preserved**; upstream `c1670044bbc0`.

## Cleanup and transaction-layout review fixes — November5,2026

Review finding#3 is addressed: short qualification cleanup shares the bounded exact-owner retry, and overlapping file/directory targets are rejected before baseline or activation and within transactions.494 CPU tests passed; no model run, resource-policy change or serving restart. The enabled03:00Toronto timer is unchanged. [Details](DAILY-UPDATER-RESTORATION-20261105.md).

## Recovery review fixes — November5,2026

Headless restored-production verification is now independent of candidate visibility permission, and SIGHUP enters interruption/rollback.488 CPU tests and85 focused public checks passed, including a real provisional-transaction hangup. The timer was paused during repair and restored after verification; next run November6 at03:00EST. No extra GPU benchmark or live runtime rollback was performed. [Details](DAILY-UPDATER-RESTORATION-20261105.md).

## Daily updater restored — November5,2026

Daily engine maintenance is enabled at03:00 America/Toronto, including guarded headless scheduled tests with private logs. Eight text entries use current grouped staging, paired short actual DSH checks and durable rollback; TensorFold and the diffusion stack receive version monitoring. The repaired exact-owner DSH path and485 CPU regressions passed. All resource guards and the20-minute update-admission gate remain. [Restoration, scope and validation](DAILY-UPDATER-RESTORATION-20261105.md). Earlier paused-update and long-suite paragraphs remain dated history.

## Engine refresh and weight sharing — November5,2026

Removed the3.418GB incomplete Qwen cache. HyperQwen, SGLang, Maya, Strata and shared llama.cpp are refreshed; TensorFold and ComfyUI/video integrations were already current under the stable/default-branch policy. All eight changed text entries passed guarded actual DSH read/result/exact followup and owned unload. No complete duplicate checkpoints were found; compatible entries already share weights. Daily updates stay paused; all guards and selected contexts remain. [Versions, sharing and optional cleanup](ENGINE-REFRESH-AND-WEIGHT-SHARING-20261105.md); [current observations](ALL-ENTRY-BENCHMARKS-20261105.md).

## Paused — November 1, 2026

The daily-update timer is disabled and inactive. Resume only on an explicit request. The existing recovery safeguards remain installed; the historical run results below are unchanged.

## 2026-11-01T04:35:57

- hyperqwen: **rejected-revision-not-retried**; upstream `f382342d7496`.
- sglang: **rejected-revision-not-retried**; upstream `d61ded5b9e2d`.
- strata-qwen: **rejected-production-preserved**; upstream `c62d5e3a15b4`.
- maya-glm: **rejected-production-preserved**; upstream `3589d6f12a3f`.
- maya-deepseek: **rejected-production-preserved**; upstream `3589d6f12a3f`.
- strata-deepseek: **production-failed-skipped**; upstream `c62d5e3a15b4`.

## 2026-10-31T04:22:50

- hyperqwen: **rejected-production-preserved**; upstream `f382342d7496`.
- sglang: **rejected-production-preserved**; upstream `d61ded5b9e2d`.
- strata-qwen: **production-failed-skipped**; upstream `870aedd9e1eb`.
- maya-glm: **rejected-production-preserved**; upstream `cd48762b6d48`.
- maya-deepseek: **rejected-production-preserved**; upstream `cd48762b6d48`.
- strata-deepseek: **production-failed-skipped**; upstream `870aedd9e1eb`.

## 2026-10-30T06:30:08

- hyperqwen: **unchanged**; upstream `ce9615c4f230`.
- sglang: **deferred-machine-not-idle**; upstream `d61ded5b9e2d`.
- strata-qwen: **deferred-machine-not-idle**; upstream `870aedd9e1eb`.
- maya-glm: **deferred-machine-not-idle**; upstream `cbaaec5d70fd`.
- maya-deepseek: **deferred-machine-not-idle**; upstream `cbaaec5d70fd`.
- strata-deepseek: **deferred-machine-not-idle**; upstream `870aedd9e1eb`.

## Installed October 29, 2026

The updater is scheduled for 03:00 host local time, America/Toronto on this workstation. Missed nights are skipped; there is no daytime catch-up. No engine was updated during installation. The read-only discovery check found HyperQwen unchanged and newer source revisions available for the other five components. Discovery is not qualification or promotion.

See [schedule, gates and recovery](DAILY-ENGINE-UPDATE-POLICY.md). Nightly results are prepended here; raw requests, build logs, telemetry and preimages stay in private ignored local data.
