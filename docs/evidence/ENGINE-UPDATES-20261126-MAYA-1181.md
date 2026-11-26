# Maya 1.1.81 installed by hand — November 26, 2026

Project Maya was updated from 1.1.78 (`1016876a387e`) to 1.1.81 (`4a0ce6e86e18`) in the hands-on update run that started on November 25, for `glm-maya`, `deepseek-maya` and `hy4-flash-maya`. Like the Strata install, it waited for the owner's reboot into kernel 7.0.0-44; the unlock check read VERIFIED first.

## Review before the install

Release notes and the commit list were read first. What applies here:

- **GLM (`glm-maya`):** a wider sample when timing GLM's CPU lane.
- **Tool calls:** the loop guard now catches longer loops of repeated tool calls.
- **Setting change:** `MAYA_GLM_NO_REUSE=0` now means off. Nothing on this server sets it.
- The rest of the range is for Inkling, which this server does not run on Maya.

## Build

Both local patches (`maya-ds4-file-cache-target-v1173.patch`, `maya-qualification-v1178.patch`) applied unchanged. Staged under `runtimes/maya-manual/v1.1.81-20261125/`; the install kept the 355 private files. The source commit and binary hashes moved in `config/maya-glm-runtime.json`, `config/maya-unsloth-runtime.json` and `config/maya-hy4-runtime.json`. Pre-images and `rollback.sh`: `data/maya-update-20261125/`.

## Checks

Short DSH check (one real tool call, tool result and follow-up, owned unload) and the gBench chat-template check, one profile at a time, GPUs at 1 MiB before and after. gBench passed 6/6 on every run below. Single runs; "before" on kernel 7.0.0-43 (November 25), "after" on 7.0.0-44 (November 26).

| Profile | Version | Prompt reading (tok/s) | First token (s) | Generation (tok/s) |
|---|---|---:|---:|---:|
| `glm-maya` | 1.1.78 | 542.9 | 10.21 | 13.7 |
| `glm-maya` | 1.1.81 | 543.0 | 10.21 | 13.8 |
| `deepseek-maya` | 1.1.78 | 184.3 | 32.13 | 8.4 |
| `deepseek-maya` | 1.1.81 | 189.8 | 31.28 | 8.1 |
| `hy4-flash-maya` | 1.1.78 | 50.8 | 109.3 | 16.1 |
| `hy4-flash-maya` | 1.1.81 | 45.6 | 121.8 | 13.4 |

- GLM and DeepSeek run at the same speed.
- **Warning, `hy4-flash-maya`:** generation 17% lower (13.4 against 16.1 tok/s), prompt reading 10% lower and first token 12.5 s later on one run each; gBench warm-up 430 s against 353 s. This entry has varied this much before (generation 13.5, 15.6 and 16.1 tok/s in the November 24-25 checks; 13.4 is just below the earlier low), and it is inside the promotion rule (a break is under half the speed or over 3x the first-token time). The first start passed its owned unload this time.

## Decision

**Promoted** under the promotion rule: all three profiles load, call tools, follow up, pass gBench and unload. Rollback: `data/maya-update-20261125/rollback.sh` (router idle) restores 1.1.78 for all three entries.
