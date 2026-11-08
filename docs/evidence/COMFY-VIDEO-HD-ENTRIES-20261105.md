# 720p and 1080p video entries and desktop actions — November 5, 2026

Both maintained ComfyUI video entries now offer **512×288, 720p (1280×720), and 1080p (1920×1080)** with the same prompt and seed controls. Clips remain 33 frames: Wan 16 fps, LTX 24 fps with audio. The ordinary desktop launch retains the 512×288 default.

## Use

Right-click **ComfyUI Wan 2.2 5B** or **ComfyUI LTX 2.3 Mesh** on the desktop and select **720p video** or **1080p video**. The existing visible terminal starts the guarded entry and prints its selected workflow name. After readiness, open `http://127.0.0.1:8188` and load the matching preset from **Workflows**:

| Entry | 720p preset | 1080p preset |
|---|---|---|
| Wan | `wan22-5b-720p` | `wan22-5b-1080p` |
| LTX | `ltx23-mesh-720p` | `ltx23-mesh-1080p` |

The **resolution** dropdown on the video node can change resolution without restarting the entry. The launcher action also sets the default resolution for newly added video nodes. A previously open or user-edited canvas retains its saved values; use the named preset or dropdown to change it. Existing saved workflows are preserved. New HD presets are installed separately, and the two image launchers retain identical commands/content.

Only one entry owns the GPUs at a time. Stop the current launcher with Ctrl+C before starting another. Prompt preparation and rendering run serially in fresh GPU-only child processes within the same guarded cgroup; LTX's owned back-half process ends before VAE decoding and starts afresh for the next request.

## Selected engines and memory

Wan uses the faster tested **native ComfyUI path**, rather than Raylight. At 720p its denoiser runs on GPU0 and VAE on GPU1. At 1080p the tested 16/14-block GPU-resident split, sequential guidance passes and explicit GPU-tiled VAE are selected automatically. [Render-only Wan1080 qualification and comparison](WAN1080-FIX-20261105.md).

LTX retains the tested Q4_0 Mesh 28/20-block split, phased GPU1 reuse, GPU video/audio VAEs and tiled decoding. Native aligned grids 1280×736/1920×1088 are cropped by 16/8 bottom rows to exact 720p/1080p; no upscaling is used.

The UI coordinator loads no neural weights and runs in CPU mode so it creates no GPU compute context. **Comfy encoder/render children still run with `--gpu-only`, and the Mesh back-half uses its explicit CUDA device. There is no CPU execution-weight offload.** The GPU-forward audit remains active in the coordinator and children, rejecting CPU/meta parameter execution. A live GPU process check confirmed only the render child consumed compute VRAM. This avoids the old coordinator's extra context allocation reducing LTX 1080p's tight margin.

The shared 32/36 GiB worker limits, 2 GiB host reserve, 100°C stop, 256 MiB/card floor with three bad 2 s samples, swap/PSI/telemetry guards, serial ownership and idle 600 s cleanup remain. Brief VRAM dips within the existing grace period remain acceptable. Runtime/checkpoint pins, nine text API/DSH entries and image settings are preserved.

## End-to-end qualification

Each new model/resolution combination was tested through the actual frontend node with seed 27001. These times include fresh GPU prompt encoding, encoder/render startup, weight loading, Mesh startup, generation, saving and frontend polling. They are not comparable with the earlier prepared-conditioning render-only timings. All clips have 33 frames; LTX includes 63,840 audio samples at 48 kHz.

| Entry | Output | End-to-end request | Minimum free GPU0/GPU1 | Result |
|---|---|---:|---:|---|
| wan22-5b | 720p | 67.746s | 1176/259MiB | Valid 33-frame clip |
| wan22-5b | 1080p | 170.847s | 4438/2195MiB | Valid 33-frame clip |
| ltx23-mesh | 720p | 50.598s | 1514/758MiB | Valid 33-frame clip |
| ltx23-mesh | 1080p | 74.839s | 380/246MiB | Valid 33-frame clip |


All 465 CPU regressions passed. Both physical GPUs passed neural parameter-forward audits in every request. All four runs completed without a guard stop, workers are inactive and reservations are released. Desktop files pass desktop-file-validate; image shortcut content is unchanged.

The [numeric validation ledger](validation-results/20261105-comfy-video-hd-entries.json) retains request times, decoded dimensions, both-GPU audits, resource margins and owned cleanup. [Existing metadata-free HD samples](../../assets/samples/comfy/README.md) remain visual evidence of the same selected engines; duplicate copies of these integration outputs are not published.
