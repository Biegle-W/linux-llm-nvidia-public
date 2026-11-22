# Maya 1.1.73 and llama.cpp b12628 installed by hand — November 22, 2026

Daily update run asked for by the owner. The upstream check found one new release.

| Engine | From | To | Result |
|---|---|---|---|
| Maya (`glm-maya`, `deepseek-maya`) | `cce2de0ed73b` (1.1.72) | `f9a053dcb5a9` (1.1.73) | **promoted** |
| llama.cpp (`bolt-llamacpp`) | main `19bc41dbb41e` (build 12622) | release `b12628` (`8a97fa98ab1a`) | **promoted**, after the owner's rule to follow the latest release (section below) |
| Unsloth llama.cpp build (`inkling-llamacpp`) | `b12588-mix-c0c3de8` | unchanged | checked by hand: still the newest release of the fork |

HyperQwen, SGLang and Strata had no new commits. Raylight, the mesh and GGUF nodes are pinned and current. ComfyUI `v0.46.0` is available (installed: `v0.45.0`); pinned, not installed.

## Review before the install

Two agents reviewed 1.1.72 to 1.1.73 from source at the exact tags (45 commits, 40 files); a second agent re-derived the main claims of each. Nothing was run during the review. Upstream figures are upstream's.

**GLM (`maya`):** no engine source changed; the binary differs only by its version string.

**DeepSeek (`maya-ds4`):** one change applies, the fix for upstream issue 1026 (out of memory after long use). The engine now measures free VRAM after the load and at the start of each request. If a card ends more than 64 MiB under the reserve, it records how much more to keep free, and the server starts the engine once more with that margin. The record is tied to the build, so this can repeat on the first start after each engine update. `MAYA_DS4_LATE_MB=0` gives the old behaviour; it is not set here. The issue is still open upstream.

**Not for this server:** issues 1084 and 1100 are fixes for Hy4-Flash, which is not installed.

**Local patches:**
- `maya-qualification-v1165.patch` applies unchanged (line offset only).
- `maya-ds4-file-cache-target-v1165.patch` **no longer applied**: the 1026 fix added a line (`late_check(false);`) at the top of `begin_request()`, exactly where the patch hooks in. It was re-anchored as `patches/maya-ds4-file-cache-target-v1173.patch`. The added lines are byte-identical; 1.1.73 with the new patch differs from 1.1.72 with the old one by exactly upstream's own change. The builder now uses the new file.
- The server adapter (`scripts/native_idle_policy.py`) finds all 14 of its source patterns the expected number of times in 1.1.73.

**Inkling 2 Mini on Maya:** the release title says "on more PCs". The engine now accepts one card from 8 GB and keeps part of the experts in RAM, but it still refuses two GPUs as released, and it cannot read the `UD-Q4_K_M` file this server serves (only `UD-Q4_K_XL`, which was deleted here on November 22). Upstream published no speed for the new RAM path. `inkling-llamacpp` stays on the Unsloth llama.cpp build.

## Build and install

- Built in isolation under `runtimes/maya-manual/v1.1.73-20261122/` (784 build steps). The first two attempts stopped at the patch step: once on the old patch, once on a first re-anchored version that GNU `patch --fuzz=0` rejected because it had more context lines before the change than after it. The third, with equal context, built.
- The builder's test pass ran on both cards and passed, including the new `ik2_off_test` and the larger `ik2_kernels_test` of the Inkling engine.
- Install with receipt hashes checked, pre-images and a rollback script: `data/maya-update-20261122/` (back to 1.1.72). 354 private files kept.

## Short DSH check

Load, one short answer through the app path, tool call, unload; one profile at a time, GPUs unlocked and idle (1 MiB each) before and after. Single short runs on November 22. All five pass.

| Profile | Version | Prompt reading (tok/s) | Time to first token (s) | Generation (tok/s) |
|---|---|---:|---:|---:|
| `glm-maya` | 1.1.72 | 563.8 | 9.84 | 14.0 |
| `glm-maya` | 1.1.73 | 550.4 | 10.08 | 14.1 |
| `deepseek-maya` | 1.1.72 | 183.2 | 32.50 | 8.0 |
| `deepseek-maya` | 1.1.73, first start | 173.0 | 34.32 | 8.2 |
| `deepseek-maya` | 1.1.73, second start | 209.0 | 28.80 | 8.8 |

**The 1026 fix did act on DeepSeek.** On the first start the engine found 854 and 853 MiB free on the two cards, short of the 1,024 MiB reserve, and recorded a margin of 192 MiB per card. On the second start it kept that margin and ended with 1,194 and 1,199 MiB free. Speed did not drop; the second start was the fastest of the three runs (one run each, so no gain is claimed).

All 558 repository tests pass after the install.

## llama.cpp: latest release instead of stable

After the Maya install the owner ruled: do not hold to the newest stable release, use the latest release that best supports the two RTX 3080-class cards. Until then the check followed the release GitHub marks as latest (1.0.0, November 13), which was already older than the installed main-branch commit.

- **Check changed.** `config/daily-update.json` now sets `"channel": "latest"` for llama.cpp, and `scripts/update_builders.py` reads the newest published release, rolling `bNNNNN` builds included (GitHub marks them as pre-releases). The other engines keep their channel; Maya and Strata have no separate pre-release line. A unit test covers the new channel.
- **Version found:** `b12628`, 6 commits after the installed `19bc41d`. Reviewed from source: none of the 6 touches the CUDA backend or the model code Bolt uses. They are two Vulkan fixes, a fix for two other model architectures, an audio-input fix, a server change for embedding-style batches, and one chat change that passes "no reasoning" to templates that support it.
- **For this hardware:** the build is made here for these cards (CUDA 13, sm_86), as before. The fix that matters most for two-card use of Inkling on mainline (upstream issue 32718, loop placement) is still open, and DSpark drafting (pull request 32218) is not merged, so `inkling-llamacpp` stays on the Unsloth build.
- **Build and install:** built in isolation under `runtimes/llamacpp-manual/b12628-8a97fa9-20261122/`; `llama-server --version` reports `1.0.0-dev (build 12628, commit 8a97fa98a)`. Pre-images and rollback in `data/llamacpp-update-20261122/` (back to `19bc41d`).

| Profile | Version | Prompt reading (tok/s) | Time to first token (s) | Generation (tok/s) |
|---|---|---:|---:|---:|
| `bolt-llamacpp` | main `19bc41d` | 669.5 | 9.64 | 67.2 |
| `bolt-llamacpp` | `b12628` | 670.5 | 9.62 | 67.0 |
| `bolt-llamacpp` | `b12628` (repeat) | 676.0 | 9.56 | 67.6 |

Same speed; all three pass.

## Limits

- Short checks only: no long-context or sustained run on 1.1.73, no quality score.
- The DeepSeek memory margin was seen on two starts. Its effect on long sessions, the case the upstream fix is for, was not tested.
- No picture request was made on either model in this run.
