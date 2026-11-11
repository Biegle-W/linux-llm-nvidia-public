# Maya 1.1.59 installed by hand — November 11, 2026 (midday)

Second engine update of the day. The midday check (`--check-only`) found one maintained engine with a new upstream release and the same pinned ComfyUI release as in the morning.

| Engine | From | To | Result |
|---|---|---|---|
| Maya | `f4067232fa59` (1.1.58) | `027992cb1f09` (1.1.59, released November 11) | **promoted**, with a speed warning on `glm-maya` |
| ComfyUI | pinned | `v0.45.0` available | not installed (pinned, monitor only) |

HyperQwen, SGLang, Strata and llama.cpp had no new commits. Raylight, the mesh and GGUF nodes are pinned and current.

## What changed upstream

Two commits after 1.1.58; the release commit touches 365 files. Most of it is a rename: the engine's settings are now read as `MAYA_X`, and an older `STRATA_X` in the environment is copied to `MAYA_X` at program start when `MAYA_X` is not set. This server's launcher already sets the `MAYA_` names (`MAYA_GLM_CKPT_EVERY`, `MAYA_GLM_NO_MTP`, `MAYA_GLM_RAM_GB`), so the launch settings are unchanged. The `DS4_` settings were not renamed.

Changes that touch what runs here: a fair-slice fix for `--parallel`, a DeepSeek fix for a failed RAM copy, and a DeepSeek two-GPU all-reduce setting that is reachable again (not set here). The rest is setup recommendations, a Turbo setting for the 744B GLM, refusal-ablation files and a dashboard change, none of which is used or switched on here.

## Build and install

Built in isolation under `runtimes/maya-manual/v1.1.59-20261111/` with the two local patches (`maya-ds4-file-cache-target-v1153.patch`, `maya-qualification-v1156.patch`); both applied with line offsets only and no fuzz. The build log has no errors. The build options are still passed under their `STRATA_` names and are accepted; the one unused-option notice (`STRATA_BUILD_DSV41`) was the same in the 1.1.58 build, and `maya-ds4` is built and linked against CUDA 13.

Every hash in the build receipt matched before the install: the four files to be replaced, the four candidates, the two binaries and 354 protected private files. The four files were copied to `data/maya-update-20261111b/preimages/`, `rollback.sh` was written, and only then were the files replaced and `runtimes/project-maya` swapped.

## Short DSH check

Load, one short answer through the app path, tool call, unload; one profile at a time, GPUs unlocked and idle (1 MiB each) before and after. Single short runs.

| Profile | Version | Result | Prompt reading (tok/s) | Time to first token (s) | Generation (tok/s) |
|---|---|---|---:|---:|---:|
| `glm-maya` | 1.1.58 | pass | 544.5 | 10.18 | 14.4 |
| `glm-maya` | 1.1.59 | pass | 539.3 | 10.29 | 13.2 |
| `glm-maya` | 1.1.59 (repeat) | pass | 511.6 | 10.86 | 12.3 |
| `deepseek-maya` | 1.1.58 | pass | 178.1 | 33.59 | 8.1 |
| `deepseek-maya` | 1.1.59 | pass | 186.0 | 32.25 | 8.2 |

**Warning, `glm-maya`:** generation was 8% slower on the first run and 15% slower on the repeat; the repeat also read the prompt 6% slower and reached the first token 7% later. The promotion rule rejects only under half the speed or over three times the time to first token, so this is a warning and 1.1.59 stays installed. Earlier short checks of the same engine version have differed by about 4% (14.7 and 14.1 tok/s on 1.1.57/1.1.58 this morning), so part of this may be run-to-run spread, but both 1.1.59 runs are below every 1.1.57/1.1.58 run. The cause was not investigated. `deepseek-maya` is the same within spread.

No long-context or sustained run was made on 1.1.59.

## Rollback

`data/maya-update-20261111b/rollback.sh` restores the four files and the 1.1.58 source tree from `data/maya-update-20261111b/preimages/`. The morning's 1.1.57 pre-images remain under `data/maya-update-20261111/`.

## Notes on the run

The visible test terminal could not be opened from the SSH session (no desktop session reachable), so the checks ran headless, detached on the server, with their output in `data/maya-update-20261111b/`. The SSH link dropped several times; nothing was interrupted because the build and the checks were detached and polled.
