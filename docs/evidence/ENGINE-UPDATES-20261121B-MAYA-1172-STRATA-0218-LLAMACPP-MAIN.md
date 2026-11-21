# Maya 1.1.72, Strata 0.2.18 and llama.cpp main installed by hand — November 21, 2026 (second update of the day)

The owner asked for a daily update run that makes the backends support Inkling 2 Mini. The upstream check found new Maya and Strata releases a few hours after the morning install, and a third Maya release came out during the work.

| Engine | From | To | Result |
|---|---|---|---|
| Maya (`glm-maya`, `deepseek-maya`) | `b6632a0b11df` (1.1.70) | `a906b01ff0ec` (1.1.71), then `cce2de0ed73b` (1.1.72) | **promoted**, both steps |
| Strata (`flash-next-strata`, `flash-next-iq4xs-strata`) | `12d491da4a69` (0.2.17; control and engine 0.1.63) | `6e38f588a646` (0.2.18; control and engine 0.1.64) | **promoted** |
| Strata (`deepseek-unsloth-strata`) | 0.2.13, DSV4.1 engine 0.1.59 | unchanged | frozen at 0.2.13 |
| llama.cpp (`bolt-llamacpp`) | `b1b770d90d94` (1.0.0) | `19bc41dbb41e` (main, 1.0.0-dev build 12622) | **promoted**; ahead of the stable release |

HyperQwen and SGLang had no new commits. Raylight, the mesh and GGUF nodes are pinned and current. ComfyUI `v0.46.0` is available (installed: `v0.45.0`); pinned, not installed.

**What this does for Inkling 2 Mini:** llama.cpp now loads and runs it on this server (trial only, not a router model), at the same low speed as the trial build. Maya 1.1.72 has a much faster Inkling engine, but as released it refuses this server. Strata does not run it. Details: [INKLING2-MINI-TRIAL-20261121.md](INKLING2-MINI-TRIAL-20261121.md).

## Review before the install

Each version was reviewed against the upstream repository at the exact tags by one agent and checked by a second one; both worked from source, release notes and the GitHub API, and nothing was run during the review. Speed figures in this section are upstream's.

### llama.cpp 1.0.0 to main (`19bc41d`)

The stable release is still 1.0.0 (November 13). Inkling 2 Mini support (architecture `inkling2_loop`) exists only on the main branch: upstream pull requests 32694 (the model), 32704 (loop slots shared after the scale pass) and 32669 (scale tensors applied for every MoE model) were merged on November 20 and 21, and `19bc41d` is the first commit that holds all three. Its CUDA build and CUDA kernel checks were green upstream; one server test for another model family fails on every main commit since November 20 and needs a debug switch this build does not set.

263 commits since 1.0.0. For `bolt-llamacpp`:

- Every flag and environment setting the launcher passes still exists with the same meaning; the placement lines and server fields the checks read are unchanged. No launcher change.
- The build now needs the NVML header (`nvml.h`); this server has it in `/usr/include`. Library version numbers stay 1.0.0, so only the hashes in `config/bolt-iq2-runtime.json` changed.
- Auto-fit code is unchanged. The scheduler can split graphs differently where weights sit in RAM (pull request 31775), which could have moved placement; the check shows the same speed.
- Read from the Bolt file's header: its expert weights are IQ2_XXS with no scale tensors, so the scale change (32669) and a removed shortcut in a fallback kernel do not touch Bolt's path.
- A new environment variable, `LLAMA_MOE_RANDOM_ROUTING`, makes output invalid when set. It is not set here.
- The upstream check keeps following stable releases and reports 1.0.0 as current. The pin records `19bc41d`; the next stable release that contains Inkling support replaces it in the normal way.

### Maya 1.1.71 and 1.1.72

1.1.71 is mostly Hy4-Flash (not installed here). What applies:

- **GLM:** an expert just moved from VRAM to RAM is read from its old VRAM slot and no longer waits for the copy (upstream calls the waiting a regression since 1.1.53). `MAYA_GLM_DRAIN_WAIT=1` restores the old path.
- **DeepSeek on two GPUs:** the second card no longer waits for a full stream sync when the expert cache is on. It is a changed code path on this pair of cards with no switch back; upstream reports unchanged answers.
- The "first start measures your PC once (1-4 minutes)" step exists only in the Hy4-Flash engine.

1.1.72 adds an experimental Inkling 2 Mini engine, `maya-ik2` (upstream: 124.6 tok/s generation and 2,542 tok/s prompt reading on one RTX 3090). The GLM and DeepSeek engine sources are byte-identical to 1.1.71. The image-encoder recompile named in the release notes only happens in upstream's setup, which this server does not use. Why `maya-ik2` does not run here is in the trial document.

Both local patches from 1.1.65 applied to both versions with line offsets only (no fuzz, no rejects).

### Strata 0.2.18

The release adds Tencent Hy4-Flash on a separate engine package (`strata-hy4`), which is fetched only when such a model is set up; it was not installed. The Qwen engine goes from 0.1.63 to 0.1.64 with only a version bump and one build-list change among existing files, and the server changes are all behind Hy4 checks. `STRATA_ROUTE_TAIL_SKIP` stays off by default, as in 0.2.17. One behaviour change: an unknown word in `chat_template_kwargs.thinking_mode` is now answered with HTTP 400 where it was ignored.

## Build and install

- **llama.cpp:** built in isolation under `runtimes/llamacpp-manual/master-19bc41d-20261121/` with the usual options (CUDA 13, sm_86, no local patches); `llama-server --version` reports `1.0.0-dev (build 12622, commit 19bc41dbb)`.
- **Maya:** 1.1.71 and 1.1.72 were each built in isolation (`runtimes/maya-manual/v1.1.71-20261121/`, `v1.1.72-20261121/`; 773 build steps for 1.1.72 because of the new engine, whose kernel test passed on both cards).
- **Strata:** control 0.1.64 and the cuda13 engine 0.1.64 were taken from the signed feed (sequence 130); the feed signature, both package digests and the engine manifest were verified with upstream's own code from the release commit. The staging script then stopped in its last line, a status print that expected a full URL where feed 130 gives a bare file name; verification and extraction were already complete. Both Flash-Next presets were moved to the new engine in one step, and their file hashes are the same after the first starts as right after the install.
- **A local adapter needed a fix for Maya 1.1.72.** The repository test suite failed one test after the install: Maya 1.1.72 reworded the line that decides when the picture encoder is stopped after a request, and `scripts/native_idle_policy.py`, which rewrites that line so the encoder is always released, skipped it without an error. With the upstream wording a CPU picture encoder would have stayed loaded after a request. The adapter now handles both wordings, and the same one-line change was made in the installed `serve/server.py`; all 549 tests pass. This was fixed after the short checks, which do not send pictures, and was not re-run on the GPUs.
- Every install checked the receipt hashes, saved pre-images and wrote a rollback script first: `data/maya-update-20261121b/` (back to 1.1.70), `data/maya-update-20261121c/` (back to 1.1.71), `data/strata-update-20261121b/` (back to 0.2.17), `data/llamacpp-update-20261121/` (back to 1.0.0). Nothing under `runtimes/strata-unsloth-029` was touched.

## Short DSH check

Load, one short answer through the app path, tool call, unload; one profile at a time, GPUs unlocked and idle (1 MiB each) before and after. Single short runs, all on the afternoon of November 21. All 15 runs pass.

| Profile | Version | Prompt reading (tok/s) | Time to first token (s) | Generation (tok/s) |
|---|---|---:|---:|---:|
| `bolt-llamacpp` | 1.0.0 | 672.9 | 9.61 | 67.3 |
| `bolt-llamacpp` | main `19bc41d` | 671.7 | 9.62 | 66.3 |
| `bolt-llamacpp` | main `19bc41d` (repeat) | 668.0 | 9.68 | 67.1 |
| `glm-maya` | 1.1.70 | 540.5 | 10.25 | 14.3 |
| `glm-maya` | 1.1.71 | 554.7 | 9.99 | 14.2 |
| `glm-maya` | 1.1.72 | 542.3 | 10.23 | 14.5 |
| `deepseek-maya` | 1.1.70 | 185.6 | 32.05 | 7.7 |
| `deepseek-maya` | 1.1.71 | 191.7 | 31.05 | 8.2 |
| `deepseek-maya` | 1.1.72 | 189.5 | 31.35 | 8.2 |
| `flash-next-strata` | 0.2.17 | 1150.5 | 5.00 | 68.6 |
| `flash-next-strata` | 0.2.18 | 1154.1 | 4.98 | 67.1 |
| `flash-next-strata` | 0.2.18 (repeat) | 1151.6 | 5.00 | 65.1 |
| `flash-next-iq4xs-strata` | 0.2.17 | 864.3 | 6.66 | 46.9 |
| `flash-next-iq4xs-strata` | 0.2.18 | 840.3 | 7.25 | 45.3 |
| `deepseek-unsloth-strata` | 0.2.13 (frozen) | 29.1 | 5.91 | 12.1 |

No profile changed speed beyond the spread of repeated runs. `flash-next-iq4xs-strata` read its prompt 3% slower and took 0.6 s longer to the first token on its single run after the update; one run each, not a finding.

## Limits

- Short checks only: no long-context or sustained run on any of the new versions, and no quality score.
- `bolt-llamacpp` now runs a main-branch commit and not a tagged release. Its quality score (53.9%) was measured on 0.9.0.
- The Maya 1.1.71 code paths that changed for this hardware (GLM reading a demoted expert from VRAM, DeepSeek's second-card flush) were exercised only by the short check.
