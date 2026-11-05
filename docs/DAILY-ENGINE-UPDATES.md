# NVIDIA daily engine updates

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
