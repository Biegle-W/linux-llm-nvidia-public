# Maintained ComfyUI video entries — November4,2026

Two video entries and Desktop-only launchers are installed alongside the existing image workflows. The user selected ComfyUI entries and launchers; the nine text API/DSH entries remain unchanged. `config/comfy-runtime.json` points to the selected video registry in `config/comfy-video-entries.json`.

| Entry | Desktop launcher | Selected execution | Clip |
|---|---|---|---|
| `wan22-5b` | **ComfyUI Wan 2.2 5B** | Wan2.2 TI2V5B FP16, GPU0 denoiser / GPU1 VAE |512x288,33frames,16fps; silent|
| `ltx23-mesh` | **ComfyUI LTX 2.3 Mesh** | LTX2.3 distilled1.1 Q4_0, Mesh28/20-block split |512x288,33frames,24fps; audio|

Wan selects the faster regular path from the [matched trial](COMFY-VIDEO-DUAL-GPU-20261104.md); Raylight remains a dated experimental alternative. Both entries use the same pinned video environment, reviewed source patches, publisher-verified SATA checkpoints and GPU-only execution as the trials. Higher resolutions/longer clips remain unqualified and are not exposed as controls.

## Use

1. Double-click the desired Desktop launcher and wait for readiness in its foreground terminal.
2. Open `http://127.0.0.1:8188`, then select its named workflow in the ComfyUI Workflows library.
3. Edit the prompt and seed, then click **Run**. The standard Save Video node previews and saves the MP4. LTX includes audio.
4. Use Ctrl+C in that foreground terminal before starting another ComfyUI/LLM worker. The shared reservation prevents concurrent GPU owners.

Only the selected model is allowed in that session. A fixed seed/prompt can reuse ComfyUI's normal graph cache; change the seed or its after-generation control for another sample. Prompts are limited to4000characters, and LTX additionally rejects tokenized captions above the qualified256-token encoder budget. Its text-only256-token minimum padding and separate GPU1 projection are preserved.

Saved clips are under `data/comfy-output/<entry-id>/`. Installed editable workflows are under `data/comfy-user/<entry-id>/default/workflows/`; existing user edits are preserved. Reviewed defaults and matching API-format ComfyUI graphs live in `config/comfy-workflows/`. The image launchers retain their existing commands and workflows.

## Generation lifecycle and guards

The UI is a lightweight ComfyUI process. Each selected video node launches a job inside the same owned systemd cgroup: first a fresh GPU text encoder phase, then a fresh render phase. The encoder process ends before denoising, and each request gets private conditioning activations and audit logs. GPU neural weights never offload to CPU; ordinary checkpoint initialization, saved conditioning activations and raw activation transport can use host memory.

LTX starts its back-half server on GPU1 per request, stops it only after all sampling steps finish, then reuses GPU1 for VAE decoding. The next request automatically starts a new server. The parent Save Video node receives the resulting clip. The direct phase loaders reject use from the frontend; requests must pass through the selected video entry. Internal phase servers bind only localhost8189; Mesh binds localhost7777. A port lifecycle issue exposed by the first repeat-request check was fixed without terminating any independent listener.

Owned job children inherit a dedicated job process group. ComfyUI interruption terminates that group; normal phase cleanup touches only the Popen objects created by that job. Unit shutdown retains KillMode=control-group. All workers share the original32/36GiB RAM high/max,2GiB host floor,256MiB free per GPU,100C stop, three bad2s samples, swap writes1MiB/s and combined8MiB/s over30s, active PSI10%/loading15%, fail-closed telemetry, serial execution and idle600s unload. No guard or production engine pin was relaxed.

## Validation

Both entries completed two consecutive frontend requests, seeds27001and27002, with fresh GPU prompt preparation for each request and valid512x288x33-frame MP4 output. LTX audio decoded to63,840samples per clip. These request times include encoding, fresh encoder/render process startup, model loading, Mesh startup where applicable, rendering and saving. They differ from the earlier render-only/prepared-conditioning trials and are not warm-model measurements.

| Entry | Request1 / request2 | Lowest sampled free VRAM GPU0/GPU1 | Maximum GPU0/GPU1 temperature | Swap |
|---|---:|---:|---:|---:|
| Wan |20.253 /19.223s|1530/6096MiB|55/42C|0|
| LTX Mesh |35.427 /35.407s|1260/1331MiB|59/45C|0|

Wan produced1,602 audited neural-module records across four phase processes; LTX7,086 across six. Private CUDA-UUID-backed evidence proves both physical cards participated; no CPU/meta execution parameters or resource violations were recorded. Both repeat tests ended with workers inactive and the reservation released. The original trial and public sample results remain dated evidence. [Validation record](validation-results/20261104-comfy-video-entries.json).

Both persistent frontend HTTP/node checks passed, with each session exposing only its selected entry. Both installed video desktop files passed desktop-file-validate, and the image shortcuts retained identical content. All455 CPU tests passed. Final workers are stopped, the reservation is released, and normal API/hub/DSH health checks pass.
