# Maya 1.1.70 and Strata 0.2.17 installed by hand — November 21, 2026

Scheduled daily check. The upstream check found two updates.

| Engine | From | To | Result |
|---|---|---|---|
| Maya (`glm-maya`, `deepseek-maya`) | `56b5216ab446` (1.1.67) | `b6632a0b11df` (1.1.70) | **promoted** |
| Strata (`flash-next-strata`, `flash-next-iq4xs-strata`) | `c77572806996` (0.2.15; control 0.1.61, engine 0.1.60) | `12d491da4a69` (0.2.17; control 0.1.63, engine 0.1.63) | **promoted**, with a generation-speed warning on `flash-next-strata` |
| Strata (`deepseek-unsloth-strata`) | 0.2.13, DSV4.1 engine 0.1.59 | unchanged | frozen at 0.2.13 |

HyperQwen, SGLang and llama.cpp (1.0.0) had no new commits. Raylight, the mesh and GGUF nodes are pinned and current. ComfyUI has a new release, `v0.46.0` (installed: `v0.45.0`); it is pinned and was not installed.

## Review before the install

Sources: the upstream release notes for Maya 1.1.68 to 1.1.70 and Strata 0.2.16 and 0.2.17, the Maya changelog diff between the two tags (188 commits, 122 files), the signed Strata feed (sequence 129), the new Strata server code and the open Maya issues. Speed figures in this section are upstream's, measured on other hardware.

### Maya 1.1.68 to 1.1.70

Most of the three releases is a new model, Hy4-Flash, with its own engine binary; it is not installed here. What applies to this server:

- **DeepSeek no longer hangs right after the load on two NVIDIA GPUs** (1.1.70, upstream PR 1006), and the engine recovers after a failed peer all-reduce (PR 1059).
- **DeepSeek's RAM copy of the experts no longer asks Linux for transparent huge pages by default** (1.1.70, PR 1042), because with a full page cache the kernel could spend minutes compacting memory at the start. `MAYA_DS4_ARENA_THP=1` asks for them again. A changed default; not set here.
- Request statistics count every engine call after a tool call or a resumed answer (PR 1058); a new picture in a long DeepSeek chat no longer re-reads the chat; with `--parallel`, a resent request finds its own conversation (not used here: one request at a time).
- For developers: a stalled GLM drafting step says what it waits for. No GLM behaviour change on NVIDIA under Linux.

Does not apply: everything for Hy4-Flash, AMD and Halo, Windows, Blackwell cards, the dashboard and the setup.

No launch setting, binary name or manifest name this server uses changed. Open upstream reports to keep in mind, none on this hardware and model: a DeepSeek hang after a chunked prompt on two Radeon cards (issue 1086), and DeepSeek sending short turns through the slower windowed path after one long prompt (issue 1074, 2.7-8.3 s against 1.2-3.6 s per turn on the reporter's PC).

### Strata 0.2.16 and 0.2.17

This is the first engine change since 0.2.14: the engine goes from 0.1.60 to 0.1.63 (there is no 0.1.61 engine; from 0.1.62 control and engine share one number).

- **The engine runs on Strata's own code** (0.2.16), with no ggml and no llama.cpp matrix kernels. Upstream reports the same tokens as 0.2.15 on its test prompts on most cards. The picture reader is new as well (its file went from 126 MB to 1.2 MB in the Linux package).
- **The route tail skip is off by default** (0.2.17). It skipped experts that every token routes at rank 7 or lower; upstream turned it off after reports of quality loss. Engine 0.1.60 ran it at rank 7 on NVIDIA when nothing was set, which was the case for `flash-next-strata`. The new server sets `STRATA_ROUTE_TAIL_SKIP=0` for every start unless the preset names the variable. Upstream's figures: generation 47.0 against 50.8 tok/s on two RTX A4000 and 73.4 against 94.5 on an RTX 5090, with answers closer to exact routing. `flash-next-iq4xs-strata` already had the variable set to 0 in its preset, so nothing changes for it. To turn it back on for `flash-next-strata`, add `"env": {"STRATA_ROUTE_TAIL_SKIP": "7"}` to its preset.
- **On a layer split of two CUDA cards the CPU takes a share of prompt reading by default** (0.2.17): prompts of 32 to 2,048 tokens took 0.39 to 0.61 of the time on upstream's two-card PC, generation unchanged, and the text of a two-card run can differ from 0.2.16. `STRATA_SPLIT_CPU_SHARE=0` turns it off. Both Flash-Next entries are this case.
- **Before the engine starts, the server gives back the page cache that still holds the model's files** (0.2.16, a fix for Ubuntu's memory guard ending a load). On this server that can make a reload read from the SSD again. The short check does not measure load time.
- Tool calls: eight more malformed forms are read (0.2.17), and a call the client refused is not declared again from the history. Request errors are 400 or 500 with a name, not a Python error. `/v1/models` carries `max_model_len`, `context_length` and `max_context_length`.
- 21 engine crash and wrong-output fixes, among them stalls in the verify window and a watchdog beat in the PLE reader.
- "Setup leaves 17 GB of RAM free, not 24" is a setup rule; this server starts from its own presets, and neither preset was rewritten by the first starts (file hashes compared before and after the checks).

Does not apply: Windows, Mac, AMD and Intel items, Blackwell (compute capability 12.x) speed switches, the Coder model pin, the app and the Terminal screens.

The control package keeps its folder layout (the source repository moved into `engine/`, `terminal/` and so on, which matters only for a build from a clone). The local idle adapter applied to the new `serve/server.py` without changes.

## Build and install

**Maya.** Built in isolation under `runtimes/maya-manual/v1.1.70-20261121/` (about 18 minutes, two jobs; the build has 761 steps now, against about 500, because of the Hy4 engine). Both local patches from 1.1.65 applied without changes (`maya-ds4-file-cache-target-v1165.patch` with offsets of 1 and 12 lines, `maya-qualification-v1165.patch` with a 71-line offset in `CMakeLists.txt`, no fuzz, no rejects). Before the install every hash in the receipt matched: four files, four candidates, the build artifacts and 354 private files. The four files were copied to `data/maya-update-20261121/preimages/`, `rollback.sh` was written, and only then were the files replaced and `runtimes/project-maya` swapped.

**Strata.** Control 0.1.63 and the cuda13 engine 0.1.63 were taken from the signed feed; the feed signature, both package digests and the engine manifest (signature and every file) were verified with upstream's `strata_control` code from the release commit. Staged under `runtimes/strata-manual/0.2.17-20261121/`. Control went to `runtimes/strata-terminal/terminal/0.1.63` with the idle adapter applied, `current` was repointed, and **both** Flash-Next presets were moved to the new engine binary and control folder in the same step (the UD-IQ4_XS entry refuses to start on a different engine than the IQ3_XXS entry). Both presets were saved to `data/strata-update-20261121/preimages/` and `rollback.sh` written first. Nothing under `runtimes/strata-unsloth-029` was touched.

## Short DSH check

Load, one short answer through the app path, tool call, unload; one profile at a time, GPUs unlocked and idle (1 MiB each) before and after. Baselines were taken after the Maya build had finished. Single short runs.

| Profile | Version | Result | Prompt reading (tok/s) | Time to first token (s) | Generation (tok/s) |
|---|---|---|---:|---:|---:|
| `glm-maya` | 1.1.67 | pass | 550.5 | 10.07 | 14.3 |
| `glm-maya` | 1.1.70 | pass | 543.4 | 10.21 | 14.2 |
| `deepseek-maya` | 1.1.67 | pass | 166.0 | 35.74 | 8.3 |
| `deepseek-maya` | 1.1.70 | pass | 193.2 | 30.85 | 8.2 |
| `flash-next-strata` | 0.2.15 (run 1) | pass | 1061.2 | 5.39 | 81.0 |
| `flash-next-strata` | 0.2.15 (run 2) | pass | 1055.9 | 5.42 | 84.8 |
| `flash-next-strata` | 0.2.17 (run 1) | pass | 1151.8 | 5.00 | 67.0 |
| `flash-next-strata` | 0.2.17 (run 2) | pass | 1156.6 | 4.97 | 64.5 |
| `flash-next-strata` | 0.2.17 (run 3) | pass | 1151.6 | 5.01 | 67.5 |
| `flash-next-iq4xs-strata` | 0.2.15 | pass | 767.1 | 7.47 | 49.1 |
| `flash-next-iq4xs-strata` | 0.2.17 (run 1) | pass | 833.0 | 7.29 | 46.6 |
| `flash-next-iq4xs-strata` | 0.2.17 (run 2) | pass | 863.2 | 6.68 | 47.9 |
| `deepseek-unsloth-strata` | 0.2.13 (untouched), before | pass | 29.1 | 5.81 | 12.3 |
| `deepseek-unsloth-strata` | 0.2.13 (untouched), after | pass | 26.9 | 6.07 | 12.1 |

Reading the numbers:

- **Maya** is unchanged on both profiles. The `deepseek-maya` prompt-reading difference (166.0 to 193.2) is inside the 166-209 spread this check has shown over the last week.
- **`flash-next-strata` generation is about 20% lower**: 64.5 to 67.5 tok/s on three runs against 81.0 and 84.8 before. This is a warning under the promotion rule (the break line is half the speed), and the three runs agree, so it is not a first-load effect. The expected cause is the route tail skip now being off; that was not confirmed by a run with it turned back on, because that is a preset change the owner decides. Prompt reading is 9% faster (1,152-1,157 against 1,056-1,061) and the first token arrives 0.4 s sooner.
- **`flash-next-iq4xs-strata`**, which already ran with the tail skip off, reads prompts 9-13% faster and generates at 46.6 and 47.9 tok/s against 49.1 (2-5% lower, a warning; one baseline run only).
- **`deepseek-unsloth-strata`** was not changed; its second run is inside its usual spread (26.9-29.1 prompt reading).

Whether answers changed was not measured: no quality run and no long-context or sustained run was made on the new versions. The Flash-Next quality scores in the registry are from engine 0.1.60 with the tail skip on (IQ3_XXS) and off (UD-IQ4_XS).

Rollback: `data/maya-update-20261121/rollback.sh` restores Maya 1.1.67; `data/strata-update-20261121/rollback.sh` restores Strata 0.2.15 for both Flash-Next entries.
