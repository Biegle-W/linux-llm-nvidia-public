# Maya 1.1.67 installed by hand — November 18, 2026

Scheduled daily check. The upstream check found one update; everything else was current.

| Engine | From | To | Result |
|---|---|---|---|
| Maya (`glm-maya`, `deepseek-maya`) | `c81fab6c9d63` (1.1.65) | `56b5216ab446` (1.1.67) | **promoted** |

HyperQwen, SGLang, Strata (0.2.15) and llama.cpp (1.0.0) had no new commits; ComfyUI, Raylight, the mesh and GGUF nodes are pinned and current.

## Review before the install

Sources: the upstream changelog for 1.1.66 (November 17) and 1.1.67 (November 18), the diff between the two tags (41 commits, 52 files) and the open upstream issues. Speed figures in this section are upstream's, measured on other hardware.

Applies to this server:

- **GLM could compute an expert with another expert's weights** (1.1.67). Where part of GLM's experts sit in RAM, an expert could be moved into VRAM twice at once, and afterwards the engine could read a place in RAM that by then held a different expert. No error, only answers that were slightly off, more often the larger the share of experts in RAM. `glm-maya` is this case: the 98 GB Maya-S24 checkpoint against 22 GB of VRAM. Answers can differ from 1.1.65 because they are now correct; upstream says speed is unchanged. New diagnostic `MAYA_GLM_TIER_VERIFY=1` (off by default) checks the expert tables after every token.
- **DeepSeek: the drafter's experts are counted in the expert profile** (1.1.66, upstream PR 501). They used to be placed wherever room was left, which could leave VRAM unused on a second GPU. The profile fills in with use, so which experts sit in VRAM can change over the next starts and `deepseek-maya` answers can differ slightly from 1.1.65.
- **Idle sleeps are settings** (1.1.66): `MAYA_GLM_SERVICE_NAP_US`, `MAYA_GLM_SERVICE_SLEEP_MS`, `MAYA_DS4_SERVICE_NAP_US`, `MAYA_DS4_SERVICE_SLEEP_MS`. Defaults are the old lengths; not set here.
- **GLM prompt faults name the GPU and layer** (1.1.66); `MAYA_GLM_PREFILL_CHECK=1` is an optional slow diagnostic. Stopping a DeepSeek answer during a shared start no longer disturbs the next request (1.1.66).
- `MAYA_PAR_MAX` (opt-in cap on `--parallel`) is new in `serve/server.py`; not set here.

Does not apply: the GLM speed-ups on an AMD APU + NVIDIA pair (1.1.66, 1.1.67), GLM starting on one small card, the Windows unpack fix, setup menu and fit-check changes, two DeepSeek sizes side by side, EXL3 reorder tool, web chat input fix.

No launch setting, build option, binary name or manifest name changed. Open upstream reports to keep in mind, none on this hardware: GLM-5.3-Flash not finishing its load on one AMD card under Windows with 1.1.66 (issue 1035), and a CUDA out-of-memory on DeepSeek prompt reading on a 48 GB + 16 GB NVIDIA pair under Windows with 1.1.66 (issue 1038).

## Build and install

Built in isolation under `runtimes/maya-manual/v1.1.67-20261118/` (about 15 minutes, two jobs). Both local patches from 1.1.65 applied without changes (`maya-ds4-file-cache-target-v1165.patch` with a 4-line offset, `maya-qualification-v1165.patch` with a 7-line offset, no fuzz, no rejects), so no patch was refreshed.

Before the install every hash in the receipt matched: four files, four candidates, the build artifacts and 354 private files. The four files were copied to `data/maya-update-20261118/preimages/`, `rollback.sh` was written, and only then were the files replaced and `runtimes/project-maya` swapped.

## Short DSH check

Load, one short answer through the app path, tool call, unload; one profile at a time, GPUs unlocked and idle (1 MiB each) before and after. Single short runs.

| Profile | Version | Result | Prompt reading (tok/s) | Time to first token (s) | Generation (tok/s) |
|---|---|---|---:|---:|---:|
| `glm-maya` | 1.1.65 | pass | 556.5 | 9.95 | 14.0 |
| `glm-maya` | 1.1.67 (run 1) | pass | 550.9 | 10.06 | 14.2 |
| `glm-maya` | 1.1.67 (run 2) | pass | 552.9 | 10.05 | 13.6 |
| `deepseek-maya` | 1.1.65 | pass | 187.1 | 31.65 | 7.5 |
| `deepseek-maya` | 1.1.67 (run 1) | pass | 175.8 | 33.70 | 8.2 |
| `deepseek-maya` | 1.1.67 (run 2) | pass | 171.2 | 34.60 | 7.4 |
| `deepseek-maya` | 1.1.67 (run 3) | pass | 209.4 | 28.84 | 8.3 |

Reading the numbers:

- **`glm-maya`** is the same as 1.1.65 within run-to-run spread and called the tool in both runs. The short check does not show whether answers changed with the expert fix; no quality run was made.
- **`deepseek-maya`** prompt reading measured 175.8 and 171.2 tok/s against 187.1 before (6% and 8.5% lower, a warning under the promotion rule) and then 209.4 on run 3. Run 2 overlapped a repository-wide text search started by the maintaining agent on the same disks, so it is not a clean number. The three runs spread from 171 to 209, wider than the difference to 1.1.65; earlier days measured 185-192. Generation is unchanged (7.4-8.3 against 7.5).

No long-context or sustained run was made on the new version.

Rollback: `data/maya-update-20261118/rollback.sh` restores Maya 1.1.65.
