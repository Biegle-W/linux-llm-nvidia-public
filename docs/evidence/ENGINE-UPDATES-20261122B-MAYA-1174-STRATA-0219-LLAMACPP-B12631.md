# llama.cpp b12631, Maya 1.1.74 and Strata 0.2.19 installed by hand — November 22, 2026 (second run)

Scheduled daily update run, the second of the day. The upstream check found three new releases since the morning run.

| Engine | From | To | Result |
|---|---|---|---|
| llama.cpp (`bolt-llamacpp`) | release `b12628` (`8a97fa98ab1a`) | release `b12631` (`e300919cc704`) | **promoted** |
| Maya (`glm-maya`, `deepseek-maya`) | `f9a053dcb5a9` (1.1.73) | `e8d4f297f434` (1.1.74) | **promoted** |
| Strata (`flash-next-strata`, `flash-next-iq4xs-strata`) | `6e38f588a646` (v0.2.18, control and engine 0.1.64) | `c6f6427d9de9` (v0.2.19, control and engine 0.1.65) | **promoted** |
| Strata Hy4 engine (`hy4-flash-strata`) | `strata-hy4` 0.1.64 | unchanged | no newer CUDA 13 package in 0.2.19; passes under control 0.1.65 |
| Strata DeepSeek (`deepseek-unsloth-strata`) | v0.2.13 | unchanged | frozen; passes |

HyperQwen and SGLang had no new commits. Raylight, the mesh and GGUF nodes are pinned and current. ComfyUI `v0.46.0` is available (installed: `v0.45.0`); pinned, not installed.

## Review before the install

Read from the release notes, the commit lists and the file lists of each range, and from the staged packages. Nothing was run during the review. Upstream figures are upstream's.

**llama.cpp `b12628` to `b12631` (3 commits, 11 files).** An OpenCL kernel set for Adreno phones and two WebGPU changes. Nothing in the CUDA backend, the server or the model code Bolt uses; the build here is CUDA 13 for sm_86 as before.

**Maya 1.1.73 to 1.1.74 (32 commits, 45 files).**
- *Applies here, GLM:* the fix for upstream issue 1026 now covers GLM. The engine measures what the start and the requests allocate after the expert pool is placed, records the shortfall in the pack's `vram-late.txt` and keeps that much more free from the next start; a start found short is restarted once by the server.
- *Applies here, DeepSeek:* the same logic moved into a shared file (`src/core/vram_late.hpp`) with the same arithmetic and file format. Two new settings are opt-in and not set here (`MAYA_DS4_AR2_DECODE=2`, and an AMD-only kernel).
- *Not for this server:* Inkling 2 Mini on Windows, on two GPUs, long context and parallel answers (the Inkling entry here runs on the Unsloth llama.cpp build); Hy4-Flash tensor-parallel windows and MiniMax copy fixes (Hy4 here runs on Strata; MiniMax is not installed); dashboard changes.
- *Local patches:* `maya-qualification-v1165.patch` and `maya-ds4-file-cache-target-v1173.patch` both applied with line offsets only, no rejected hunk.

**Strata 0.2.18 to 0.2.19 (55 commits).**
- *Applies here:* `strata-engine` 0.1.65 for Qwen3.8-Flash-Next. Upstream lists Ampere (sm_86) gains measured on an RTX 3090 and on two RTX A4000: prompt reading +12% to +26% and generation +13% to +20%, bit-exact, with the route tail skip still off by default. Neither card type is this server's pair.
- *Control 0.1.65:* the server changes are all for the new Inkling engine (new modules, a `--parallel` flag); no default for the Qwen engine changed in the server or the settings register. The local server adapter (`scripts/native_idle_policy.py`) applied cleanly.
- *Hy4:* the release ships a new `strata-hy4` 0.1.65 only for Intel SYCL. The signed feed (sequence 131) still names `strata-hy4-0.1.64-linux-x86_64-cuda-cuda13.tar.gz` from the v0.2.18 release, with the manifest hash already installed, so there is nothing to install for Hy4.
- *Not for this server:* the new Inkling 2 Mini engine `strata-inkling` (not installed in this run; adding a model entry is the owner's call), AMD, Apple, Intel and Blackwell work.
- *DeepSeek:* still not run by Strata; the feed's DeepSeek package is the 0.1.59 one from v0.2.13.

## Build and install

- **llama.cpp:** built in isolation under `runtimes/llamacpp-manual/b12631-e300919-20261122/`; `llama-server --version` reports `1.0.0-dev (build 12631, commit e300919cc)`. Pre-images and rollback in `data/llamacpp-update-20261122b/` (back to `b12628`).
- **Maya:** built in isolation under `runtimes/maya-manual/v1.1.74-20261122/` (788 build steps, first attempt). Install with receipt hashes checked; 354 private files kept. Pre-images and rollback in `data/maya-update-20261122b/` (back to 1.1.73).
- **Strata:** feed signature and both packages verified with upstream's signing code; staged under `runtimes/strata-manual/0.2.19-20261122/`. Control installed as `runtimes/strata-terminal/terminal/0.1.65` with the server adapter applied, `current` repointed, and both Flash-Next presets moved to the new engine in one step. The Hy4 preset was not touched (same hash before and after). The three preset files were unchanged by the first starts. Pre-images and rollback in `data/strata-update-20261122b/` (back to 0.2.18).

## Short DSH check

Load, one short answer through the app path, tool call, unload; one profile at a time, GPUs unlocked and idle (1 MiB each) before and after. Baselines were taken before any build started. Single short runs on November 22. All 16 pass.

| Profile | Version | Prompt reading (tok/s) | Time to first token (s) | Generation (tok/s) |
|---|---|---:|---:|---:|
| `bolt-llamacpp` | `b12628` | 679.3 | 9.50 | 66.8 |
| `bolt-llamacpp` | `b12631` | 672.8 | 9.59 | 67.0 |
| `bolt-llamacpp` | `b12631` (repeat) | 672.6 | 9.59 | 67.1 |
| `glm-maya` | 1.1.73 | 553.1 | 10.02 | 14.3 |
| `glm-maya` | 1.1.74, first start | 551.5 | 10.05 | 14.5 |
| `glm-maya` | 1.1.74, second start | 544.9 | 10.19 | 14.5 |
| `deepseek-maya` | 1.1.73 | 188.2 | 31.54 | 8.3 |
| `deepseek-maya` | 1.1.74, first start | 186.5 | 31.96 | 7.7 |
| `deepseek-maya` | 1.1.74, second start | 210.5 | 28.60 | 9.0 |
| `flash-next-strata` | 0.2.18 | 1154.0 | 4.99 | 65.8 |
| `flash-next-strata` | 0.2.19 | 1157.0 | 4.98 | 68.9 |
| `flash-next-strata` | 0.2.19 (repeat) | 1153.8 | 4.99 | 68.6 |
| `flash-next-iq4xs-strata` | 0.2.18 | 864.5 | 6.66 | 47.2 |
| `flash-next-iq4xs-strata` | 0.2.19 | 850.5 | 7.20 | 44.8 |
| `hy4-flash-strata` | control 0.1.64, engine 0.1.64 | 210.3 | 26.67 | 28.5 |
| `hy4-flash-strata` | control 0.1.65, engine 0.1.64 | 210.2 | 26.69 | 28.4 |
| `deepseek-unsloth-strata` | 0.2.13 (frozen), after the install | 27.8 | 5.97 | 12.1 |

- **Warning, `flash-next-iq4xs-strata`:** generation at 95% of the baseline and first token 8% later, one run each. Inside the promotion rule (a break is under half the speed or over three times the first-token time).
- **`flash-next-strata`:** generation about 4.5% higher on both runs, prompt reading the same. Upstream's +13% to +20% for Ampere was not seen on this pair in the short check.
- **The 1026 fix acted on GLM.** After the first starts on 1.1.74 the pack's `vram-late.txt` holds a margin of 224 MiB for each card (3080 Ti and 3080). Speed did not change.

All 571 repository tests pass after the install.

## Limits

- Short checks only: no long-context or sustained run on any of the three new versions, no quality score.
- `flash-next-iq4xs-strata` was run once on 0.2.19; the small slowdown is not confirmed by a repeat.
- The GLM memory margin was seen on two starts. Its effect on long sessions, the case the upstream fix is for, was not tested.
- No picture request was made in this run.
