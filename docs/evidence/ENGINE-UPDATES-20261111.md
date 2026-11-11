# Engine updates installed by hand — November 11, 2026

Daily check (`--check-only`) found two engines with new upstream commits and one pinned component with a newer release.

| Engine | From | To | Result |
|---|---|---|---|
| Maya | `00655481ce2b` (1.1.57) | `f4067232fa59` (1.1.58, released November 10) | **promoted** |
| HyperQwen | `80cf05935949` | `3d6c9543292e` | **pin moved**, nothing rebuilt |
| ComfyUI | pinned | `v0.45.0` available | not installed (pinned, monitor only) |

SGLang, Strata and llama.cpp had no new commits. Raylight, the mesh and GGUF nodes are pinned and current.

## Maya 1.1.58

Built in isolation under `runtimes/maya-manual/v1.1.58-20261111/` with the two local patches (`maya-ds4-file-cache-target-v1153.patch`, `maya-qualification-v1156.patch`). Every hash in the build receipt matched before the install: the four files to be replaced, the four candidates and 354 protected private files.

Upstream changes that touch what runs here: a change to the DeepSeek one-GPU decode path, a loop-guard fix, a Responses API fix, and a faster CPU-lane decode for GLM that is on by default. The rest is for the 744B GLM pack and features that are off here.

The launch settings are unchanged. The engine still reads the checkpoint interval adopted on November 10 (`MAYA_GLM_CKPT_EVERY`, read as `STRATA_GLM_CKPT_EVERY` in both versions).

Short DSH check (load, one short answer through the app path, tool call, unload), one profile at a time, GPUs unlocked and idle:

| Profile | Version | Result | Prompt reading (tok/s) | Time to first token (s) | Generation (tok/s) |
|---|---|---|---:|---:|---:|
| `glm-maya` | 1.1.57 | pass | 546.8 | 10.14 | 14.7 |
| `glm-maya` | 1.1.58 | pass | 547.9 | 10.12 | 14.1 |
| `deepseek-maya` | 1.1.57 | pass | 189.4 | 31.59 | 8.6 |
| `deepseek-maya` | 1.1.58 | pass | 186.9 | 32.02 | 8.1 |

Speeds are the same within run-to-run spread. The CPU-lane change did not show up as faster generation in this short check. No long-context or sustained run was made on 1.1.58.

Rollback: `data/maya-update-20261111/rollback.sh` restores the four files and the 1.1.57 source tree from `data/maya-update-20261111/preimages/`.

## HyperQwen `3d6c954`

Thirteen upstream commits. None changes anything this server installs or runs: the patch series, the KVarN patches, the requirements, the Dockerfile and the attention kernels are byte-identical to `80cf059`. The changes are README and docs, a wording change in the two `start_qwen.sh` scripts, a shard check in `docker/prepare.sh`, and a new opt-in `opt-170hx/` folder for a different GPU. This server launches `runtimes/env-hyperqwen/bin/vllm` directly and uses none of those files.

A rebuild would produce the same environment, so the pin was moved without a rebuild and without a GPU check. The clone reviewed is at `runtimes/hyperqwen-manual/3d6c954-20261111/source`.

## ComfyUI

`v0.45.0` is available. ComfyUI is pinned and only monitored by the daily check, so it was not installed.
