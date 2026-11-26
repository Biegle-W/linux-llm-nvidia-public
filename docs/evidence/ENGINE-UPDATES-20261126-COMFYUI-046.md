# ComfyUI 0.46.0 installed by hand — November 26, 2026

The owner asked for ComfyUI `v0.46.0`, which had been pinned and only monitored since November 18.

| Component | From | To | Result |
|---|---|---|---|
| ComfyUI | `989d93d0d968` (`v0.45.0`) | `a277b5bf213e` (`v0.46.0`, released November 18) | **promoted** |

Upstream also has tags `v0.46.1` to `v0.46.3` (November 19-24) without GitHub releases. They sit on a release branch (`release/v0.46`) that mostly adds and fixes cloud Partner Nodes (paid API nodes that the `--offline` launch blocks), newer workflow templates (0.11.118) and one small video-input helper, so `v0.46.0`, the latest release, was installed as asked.

## Review before the install

54 upstream commits, 82 files. Four read-only reviews (image stack, video stack, environment and defaults, release notes and open issues) compared the upstream diff with the local nodes (`scripts/comfy_nodes`, `scripts/comfy_video_nodes`, `scripts/comfy_video_hook`), the patched Raylight and Mesh nodes, the GGUF loader, the launcher and both Python environments; a second reader tried to refute each finding. Result:

- **No model, sampler or quantization code used by the image or video entries changed.** Samplers, `comfy/ldm` for Qwen Image, FLUX/FLUX3, MiniMax, Wan and LTX, `quant_ops.py`, `server.py`, `folder_paths.py` and the feature-flag registry have an empty diff. Shared code that every job runs did change, with no effect on CUDA without the new flags: the removal of DirectML in `model_management.py`, `cast_bias_weight` (below), embedded-tokenizer support in `sd.py`/`sd1_clip.py` (none of the text encoders here carries an embedded tokenizer), and an opt-in `--force-output-rerun` hook in `execution.py`. `CreateVideo` (trial stages) gained a "none" chroma option; its default is unchanged. The rest is new model families that are not served here (SenseNova, PAN2), a video deflicker node, small node options (APG at cfg 1, image-channel split, PNG channels, Concatenate Video frame-rate conforming) and a fix in the dynamic-VRAM model patcher, which every launch here switches off (`--disable-dynamic-vram`).
- **One change touches quantized layers** ("Fix dynamo", upstream PR 17808): `cast_bias_weight` now takes the compute dtype from the input tensor. For the int8 and convrot weights here the input is not quantized and the value is the same, so this is a no-op; the identical images below confirm it.
- **Packages:** `requirements.txt` moves only the bundled web page and its extras: `comfyui-frontend-package` 1.58.5 → 1.59.6, `comfyui-workflow-templates` 0.11.105 → 0.11.111 and `comfyui-embedded-docs` 0.5.16 → 0.5.17. With the template sub-packages this moves six packages in each environment; a dry run in both showed nothing else moving. PyTorch stays at 2.13.0 (image) and 2.11.0 (video), both CUDA 13, so the new "PyTorch CUDA below 13" warning does not appear.
- **Launcher:** no new argument is needed; the two sign-in options switched off for 0.45.0 still exist with the same defaults and stay off.
- **Open upstream issues** checked: a queue and cancel hang in the browser page after the first job with frontend 1.59.6 on one Windows portable install (issue 17922, open; reported with MiniMax H3 and FIBO 2, so it may affect MiniMax H3 here; the reporter says frontend 1.59.13 did not help and 1.57.4 did). The checks below queue jobs through the API, not the browser page, so they do not test it. Also text-encoder memory not released on Qwen Image (issue 17905), which already applies to 0.45.0 and has no fix in any 0.46 tag.

## Install

- `runtimes/ComfyUI` is a blobless partial clone and did not hold 82 file versions the new tree needs (`runtimes/ComfyUI-video` has no objects of its own: it borrows the image tree's through `.git/objects/info/alternates`, so repacking, pruning or deleting the image tree would break the video tree and its rollback). They were fetched from a full local clone at `runtimes/comfyui-manual/v0.46.0-20261126/source` (`git fetch --no-filter --refetch`), then both `runtimes/ComfyUI` and `runtimes/ComfyUI-video` were switched in place to `a277b5bf213e`. Both trees are clean with no missing files.
- Both environments: `uv pip install comfyui-frontend-package==1.59.6 comfyui-workflow-templates==0.11.111 comfyui-embedded-docs==0.5.17`. In each lock file exactly six rows changed.
- Pins moved in the same step: `config/comfy-runtime.json` (commit, version), `config/comfy-video-trial.json` (commit), `config/daily-update.json` (`installed_release`).

## Checks, before and after

Run with `scripts/comfy_run.py` under a pty, one at a time, reservation released each time. GPU unlock VERIFIED and both GPUs idle (at most 16 MiB) at the gates before and after the swap; 1 MiB each at the end. Two seeds per generation check (27001, 27002; the prompt-encoding stage uses 27001 only); wall time in seconds, first / second request. The page checks ran by hand after the swap.

| Check | 0.45.0 | 0.46.0 | Output |
|---|---|---|---|
| Qwen-Image 2.1 Turbo, 1024² | pass, 8.10 / 4.05 | pass, 8.11 / 4.05 | both images byte-identical |
| FLUX3 Klein, 1024² | pass, 7.10 / 5.07 | pass, 8.10 / 5.07 | both images byte-identical |
| MiniMax H3 Image, 1024² | pass, 18.20 / 7.09 | pass, 20.23 / 7.09 | both images byte-identical |
| Wan 2.2 5B entry, 512x288, 33 frames | pass, 20.23 / 19.23 | pass, 19.23 / 20.23 | both clips byte-identical |
| LTX 2.3 Mesh entry, 512x288, 33 frames | pass, 37.45 / 36.42; repeat 36.40 / 36.40 | pass, 36.42 / 36.43 | differ, as between two 0.45.0 runs |
| Wan prompt encoding (trial stage) | pass, 2.03 | pass, 2.03 | |
| Wan through Raylight (trial stage) | pass, 46.75 / 32.52; repeat 45.53 / 32.53 | pass, 46.68 / 32.56 | identical to the 0.45.0 repeat; differs from the first 0.45.0 run |
| Page and workflow nodes, image (`--check-ui`) | | pass | frontend 1.59.6 served; every image workflow node registered |
| Page and workflow nodes, Wan video entry (`--check-ui`) | | pass | entry node and resolution choices as before |

- Second requests are the same speed. First requests include loading: FLUX3 +1.0 s (November 12 saw 7.15 → 8.12 s on the same kind of step) and MiniMax +2.0 s (18.20 → 20.23 s, one run each; no earlier repeat to compare).
- **Run-to-run variation, now known:** on 0.45.0 the LTX Mesh entry and the Raylight stage already gave different bytes on two runs of the same version, so their differences are not caused by 0.46.0. The 0.46.0 Raylight clips match the second 0.45.0 run byte for byte. This answers the LTX question from the 0.45.0 install. For Raylight, two 0.44.0 runs had matched on November 12, so the variation seen now on 0.45.0 may have started with that upgrade.
- Forward audits covered the same module counts on the entries (1,602 Wan and 7,086 LTX on both GPUs; 243 prompt encoding on one GPU, as before). The Raylight stage audited 1,943 modules on 0.46.0, against 1,956 and 1,937 on the two 0.45.0 runs.
- Startup warnings are the same as on 0.45.0 (dynamic VRAM switched off by argument, torch imported early).
- Not run: 2048² images, 720p and 1080p video, the LTX render-only stages. The 1024² images are byte-identical, so the 1024² samples in `assets/samples/comfy/` still match; the larger samples were not re-made.

## Not changed, noted for later

- Issue 17922 above: MiniMax H3 in the browser page was not tried on frontend 1.59.6. If its queue hangs, pin `comfyui-frontend-package` back to 1.58.5 (lock rows and both environments together).
- Neither live tree carries the `v0.45.0` or `v0.46.0` tags (`git describe` shows `v0.44.0-97-ga277b5bf`); checks go by commit.
- The per-stage video server started by `scripts/comfy_video_job.py` (trial stages only, loopback, `--offline`) does not pass the two sign-in options as `false`, unlike the launcher. This was already so on 0.45.0 and `--offline` still blocks the cloud nodes; changing it is a separate step for the owner.

Rollback: `data/comfyui-update-20261126/rollback.sh` checks both trees back out to `989d93d0d968`, reinstalls the three old package versions and restores the five changed config files from `data/comfyui-update-20261126/preimages/`.
