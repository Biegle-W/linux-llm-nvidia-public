# Maya 1.1.60 and ComfyUI 0.45.0 installed by hand — November 11-12, 2026

The owner asked for both pending updates: the Maya release that appeared after the midday 1.1.59 install, and ComfyUI `v0.45.0`, which had been pinned and only monitored.

| Component | From | To | Result |
|---|---|---|---|
| Maya | `027992cb1f09` (1.1.59) | `8b0a449c599f` (1.1.60, released November 11) | **promoted** |
| ComfyUI | `7ad7adb38f6c` (0.44.0 + 6 commits) | `989d93d0d968` (`v0.45.0`, released November 10) | **promoted** |

HyperQwen, SGLang, Strata and llama.cpp had no new commits. Raylight, the mesh and GGUF nodes are pinned and current.

## Maya 1.1.60

Three upstream commits. The release notes say NVIDIA is unchanged: the speed fix is for AMD APUs, and the rest is a new DeepSeek EXL3 option in the setup, an opt-in drafter for the 744B GLM, and docs. Built in isolation under `runtimes/maya-manual/v1.1.60-20261111/` with the two local patches (line offsets only). Every hash in the build receipt matched before the install: four files, four candidates, two binaries and 354 protected private files.

Short DSH check (load, one short answer through the app path, tool call, unload), one profile at a time, GPUs unlocked and idle before and after:

| Profile | Version | Result | Prompt reading (tok/s) | Time to first token (s) | Generation (tok/s) |
|---|---|---|---:|---:|---:|
| `glm-maya` | 1.1.59 | pass | 553.2 | 10.02 | 14.0 |
| `glm-maya` | 1.1.60 | pass | 545.0 | 10.18 | 14.4 |
| `deepseek-maya` | 1.1.59 | pass | 189.8 | 31.50 | 8.7 |
| `deepseek-maya` | 1.1.60 | pass | 189.9 | 31.58 | 8.4 |

Same speed within run-to-run spread. The midday warning (`glm-maya` at 13.2 and 12.3 tok/s on 1.1.59) did not repeat: the same 1.1.59 build measured 14.0 this evening, so that reading was spread between runs, not the release. No long-context or sustained run was made on 1.1.60.

Rollback: `data/maya-update-20261111c/rollback.sh` restores 1.1.59 from `data/maya-update-20261111c/preimages/`.

## ComfyUI 0.45.0

### Review before the install

37 upstream commits, 69 files. Three read-only reviews (image stack, video stack, environment) compared the upstream diff with the local nodes (`scripts/comfy_nodes`, `scripts/comfy_video_nodes`), the patched Raylight and mesh nodes, the GGUF loader and both Python environments; a second reader re-checked each finding. Result:

- No ComfyUI internal that the image or video entries call was removed or changed in a way that reaches them. The changes in memory and device handling are in the dynamic-VRAM and async paths, which every launch here switches off.
- `requirements.txt` changes two pins: `comfy-kitchen` 0.2.40 → 0.2.41 and `comfyui-workflow-templates` 0.11.101 → 0.11.105. A dry run showed only those and three template sub-packages would move; PyTorch stays as it is in both environments (2.13.0 image, 2.11.0 video).
- The worker refuses to start unless the checkout commit, a clean tree and every lock row match, so the pins and locks had to move in the same step.
- **Two UI options now default to on:** `local_web_sso` (offers browser sign-in to the vendor's cloud on the local page) and `partner_node_token`. Neither makes the server call out by itself. The launcher in `scripts/comfy_worker.py` now passes both as `false`, so the page behaves as it did on 0.44.0.

### Install

- `runtimes/ComfyUI` and `runtimes/ComfyUI-video` were switched in place to `989d93d0d968` (the video tree shares the image tree's git objects, so the folders were not moved). The objects came from a full local clone at `runtimes/comfyui-manual/v0.45.0-20261111/source`.
- A first attempt stopped part-way because `runtimes/ComfyUI` is a partial clone and the fetch from the local clone skipped file contents; it had removed two Windows batch files from the tree and nothing else. Fetching again without the filter fixed it. Both trees are clean at the new commit and the custom-node links resolve.
- Both environments: `uv pip install comfy-kitchen==0.2.41 comfyui-workflow-templates==0.11.105`. Both lock files were regenerated from the environments; only the five expected rows differ.
- Pins moved: `config/comfy-runtime.json` (commit, version), `config/comfy-video-trial.json` (commit), `config/daily-update.json` (`installed_release`).

### Checks, before and after

Run with `scripts/comfy_run.py` under a pty, one at a time, GPUs unlocked and idle (1 MiB each) before and after, reservation released each time. Two seeds per check (27001, 27002); wall time in seconds, first / second request.

| Check | 0.44.0 | 0.45.0 | Output |
|---|---|---|---|
| Qwen-Image 2.1 Turbo, 1024² | pass, 8.11 / 4.06 | pass, 8.12 / 4.06 | both images byte-identical |
| FLUX3 Klein, 1024² | pass, 7.15 / 5.07 | pass, 8.12 / 5.10 | both images byte-identical |
| Wan 2.2 5B entry, 512x288, 33 frames | pass, 21.28 / 20.35 | pass, 20.31 / 20.25 | both clips byte-identical |
| LTX 2.3 Mesh entry, 512x288, 33 frames | pass, 38.47 / 36.45 | pass, 36.47 / 35.47 | clips differ in bytes (file sizes within 0.1%) |
| Wan prompt encoding (trial stage) | pass, 2.04 | pass, 2.04 | |
| Wan through Raylight (trial stage) | pass, 47.01 / 32.57 | pass, 46.94 / 32.56 | clips differ in bytes |

- Forward audits covered the same module counts (1,602 Wan entry, 7,086 LTX entry, 243 prompt encoding) and both GPUs. The Raylight stage audited 1,956 modules against 1,958.
- The Raylight stage is a trial path, not a served entry. Its output was the same across two runs on 0.44.0 and is different on 0.45.0, so something in its numeric path changed with the upgrade; the clip is valid and the time is the same. The cause was not investigated.
- It is not known whether the LTX entry gives the same bytes from run to run on one version, so its byte difference may or may not come from the upgrade.
- Not run: 2048² images, 720p and 1080p video, the LTX render-only stages, and the UI check.

Rollback: `data/comfyui-update-20261111/rollback.sh` checks both trees back out to `7ad7adb38f6c`, reinstalls the two old package versions and restores the six changed files from `data/comfyui-update-20261111/preimages/`.
