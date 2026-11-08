# Guarded two-GPU video trials — November 4, 2026

The initial trials below are now followed by [selected ComfyUI workflow entries and Desktop launchers](COMFY-VIDEO-ENTRIES-20261104.md). Historical candidate status and timing scopes below describe the original trials.

[Generated image and video samples](../../assets/samples/comfy/README.md). Metadata-free copies preserve the tested media content.

These are isolated candidate trials on the RTX3080Ti12GB + RTX308010GB pair. No video entry has been promoted into the production API or desktop selectors. The existing nine LLM entries and two image workflows remain unchanged.

The tested approaches are [Raylight](https://github.com/komikndr/raylight) with Wan2.2 TI2V5B FP16 and [ComfyUI Mesh](https://github.com/shootthesound/comfyui-mesh) with LTX2.3 distilled1.1 Q4_0 GGUF. Exact source commits, model revisions, file sizes and publisher SHA256 values are in `config/comfy-video-trial.json`; dependencies are in `config/comfy-video-requirements.lock`. The video environment is separate from the working image environment. All eight downloaded model files passed publisher hash verification and reside on SATA.

## Results

| Trial | First request | Warm request | Result |
|---|---:|---:|---|
| Wan5B regular GPU0 denoiser / GPU1 VAE |10.143s|7.111s|Pass, both GPUs audited|
| Wan5B Raylight FSDP + Ulysses2 |43.346s|30.539s|Pass, both physical GPUs audited;4.27/4.29times baseline latency|
| LTX2.3 Q4_0 Mesh,28/20blocks, phased GPU1 reuse |14.259s|Not measured|Pass,33video frames and63,840audio samples at48kHz|

Raylight offers no speed benefit for this small Wan workload on this host-staged pair. Its request logs reapply FSDP before the second request, so warm here does not imply zero distributed setup. This does not establish its behavior at larger resolutions or clip lengths. Mesh demonstrates capacity sharing for the larger LTX model; there is no fitting single-card LTX baseline and no claimed speedup. The LTX request starts after its back-half server is ready, so the table is not an end-to-end cross-model race. Text preparation and server startup must be included separately when budgeting a complete workflow.

| Selected arm | Lowest sampled free VRAM GPU0/GPU1 | Max temperature GPU0/GPU1 | Lowest host available | Swap |
|---|---:|---:|---:|---:|
| Wan baseline |1743/6330MiB|60/48C|85.70GiB|0|
| Wan Raylight |5393/972MiB|59/48C|71.65GiB|0|
| LTX Mesh phased |1529/1564MiB|56/41C|85.72GiB|0|

Final audits covered558 baseline modules,1,960 Raylight modules across three processes, and2,914 Mesh modules across two processes. GPU UUID-backed evidence proves both physical cards executed neural modules. No final arm recorded CPU/meta parameter execution or a resource violation. These are2s samples, not continuous peak-memory bounds. Generated MP4s decoded to the requested dimensions/frame counts; LTX's audio stream decoded successfully. Sampled frames show coherent fox scenes and motion; Wan has blown highlights. No formal quality, long-video, high-resolution or sustained/reload qualification was performed.

Two earlier LTX outputs took13.193s(tile256) and13.208s(tile128), but GPU1 dipped to20MiB and4MiB free for one sample during VAE decode. Both completed within the retained three-sample stop policy; neither is selected. Smaller tiles alone did not fix the margin. The selected graph ends the owned back-half denoiser process after all eight sampling steps and before decoding, reusing GPU1 VRAM for the VAE without CPU weight offload. This is a one-shot trial: a later render needs a fresh owned server. The selected14.259s includes this release handshake. All final workers are stopped, reservations released, API/hub/DSH healthy. All442 CPU tests passed, plus the isolated rotary-wire CPU roundtrip. No production profile was promoted.

The next useful qualification is a bounded larger LTX clip with the same phased release, then separate quality and fresh-reload checks. Keep the regular Wan path for this tested workload. Do not infer2K/4K video support from the separate image benchmarks.

[Machine-readable evidence](benchmark-results/20261104-comfy-video-dual-gpu.json).

## Protocol and scope

Wan uses512x288,33frames,16fps,20Euler/simple steps,cfg5,shift8, seeds27001/27002. Its single-denoiser baseline holds the FP16 denoiser on GPU0 and VAE on GPU1. Raylight uses two actors, FSDP, Ulysses2/ring1/cfg1/dp1, TORCH_FLASH attention and CPU offload=false. CUDA P2P is unavailable on this pair: NCCL uses host-staged shared-memory transport with P2P disabled, verified separately at boot. This is a measured capacity/speed screen, not a long-video or production-quality qualification.

Prompt preparation is measured separately and completely unloaded before rendering. Wan's INT8 UMT5 preparation took1.780s encoder time /2.038s client wall on GPU0. Both matched render arms reuse the exact saved conditioning activations; storing those small activations on CPU is not weight offload. Its activation producer used Torch2.13; matched render arms both use Torch2.11 CUDA13. Initial-request timing starts at HTTP prompt submission and includes model loading, Ray cluster/communication initialization where applicable, denoising, GPU VAE decode and MP4 saving. Warm requests reuse loaded models and cached text/latents with a new seed. Hash preflight and Comfy startup are outside request timing. Full hash verification reads each checkpoint beforehand: all render results are file-cache-warm, not cold-SATA startup measurements.

LTX uses512x288,33frames,24fps,8Euler distilled steps,cfg1, seed27001, raw transport and a28local/20remote transformer-block split. It includes audio/video latents and matching VAEs on GPU1. Its video VAE uses128px tiles/32px overlap. The owned back-half server ends after denoising before GPU1 decodes. Its Gemma3 Q4_K_M text model is on GPU0; the BF16 text projection is a separate GPU1 stage. Text-only preparation omits missing, unused vision modules and reduces minimum padding from1024to256 tokens; actual caption text is retained. It took14.001s encoding /14.381s client wall, then unloaded before sampling. This differs from Wan's workload and is not a cross-model speed comparison.

Mesh's native loader accepts safetensors. The smallest identified compatible native FP8 LTX transformer is23,163,222,368bytes, above the pair's aggregate idle free VRAM before activations or duplicate components. The local `scripts/comfy_mesh_gguf.py` adapter therefore uses the pinned City96 GGUF operations to retain only the back-half blocks on the server. The client loads a CPU-mapped checkpoint as ordinary initialization, strips remote blocks before sampling, then GPU-loads the retained weights. No CPU neural weight execution or inference offload is allowed. This adapter is experimental and not an upstream Mesh support claim.

## Residency and retained guards

Every parameter-bearing neural module is audited immediately inside forward, after FSDP pre-hooks materialize parameters. A CPU/meta parameter raises before computation. Private logs record CUDA device UUIDs so Ray's changed CUDA_VISIBLE_DEVICES labels cannot substitute for proof of two physical GPUs. Published evidence contains only card counts, never identifiers.

Retained policy: exclusive project reservation;32/36GiB worker RAM high/max;2GiB host available floor;256MiB free per GPU;100C stop;three bad2s samples; swap writes1MiB/s and combined8MiB/s over30s; active full PSI10%/loading15%; telemetry fail closed after three failures; serial execution; idle unload600s. All worker children, including Ray processes and Mesh server, stay inside the owned systemd cgroup and are stopped before releasing its reservation.

## Compatibility fixes and failed attempts

The video-only runtime uses a matched Torch2.11.0/torchvision0.26.0/torchaudio2.11.0 CUDA13 stack. Raylight requires torchaudio; a matching2.13 CUDA13 audio wheel was not published on the checked official index. Working image Torch2.13 is unchanged. Video native allocator selection avoids a startup native/async allocator mismatch introduced by early audit-hook Torch import. Ray temp paths use a private short directory to respect the107-byte UNIX socket limit.

Raylight initially left unsharded native Wan modulation parameters on CPU despite FSDP_CPU_OFFLOAD=false. The reviewed `scripts/patches/raylight-native-ignored-gpu.patch` materializes only ordinary CPU parameters on the target GPU once after state loading and before sampling; DTensor shards are untouched. The worker verifies both patch hashes/diffs and rejects other tracked source edits. An earlier audit also checked before FSDP pre-hooks; this was corrected to check actual execution state and covered by a CPU regression. Both earlier failures remain dated evidence, not successful benchmark arms.

LTX prompt preparation initially exhausted GPU0 with its combined encoder/projection and1024-token padding. Separate projection placement, text-only module removal and256-token padding passed without relaxing any guard. Mesh's standalone `protocol` module also collided with Comfy's module during GGUF imports; the adapter gives each its own module reference. A first slim-load attempt retained full48-block metadata and was stopped by systemd-oomd at33.9GiB RAM /7.5GiB swap peak; the adapter now rewrites transformer.num_layers to the retained20-block count before constructing the model, matching the native Mesh loader. No memory or swap limit was raised.

Mesh also expected legacy rotary `(cos,sin,split)` tuples while pinned Comfy now supplies `(rotation_matrix,split)`. The reviewed `scripts/patches/mesh-ltx-rotary-matrix.patch` supports both formats symmetrically in the client and server payload modules. A CPU wire test roundtrips both representations bit-exactly; actual GPU rendering is checked separately. A workflow-builder argument collision was fixed and all five graphs now build before GPU admission.

## Reproduction

Clone the exact three custom-node source pins and the separate ComfyUI core pin into the paths specified in the trial manifest. Install the video lock in its separate environment; apply both reviewed Raylight and Mesh patches. Symlink `scripts/comfy_video_nodes` as `nvidia_video`, Raylight as `raylight` and Mesh as `comfyui_mesh` in the video core's custom_nodes directory. The worker whitelists only the required nodes per stage. Download the exact pinned files to the manifest checkpoint directory on SATA; the coordinator verifies full hashes before obtaining GPUs.

Run each through `scripts/visible_terminal.py foreground --title 'Video trial' -- /usr/bin/python3 scripts/comfy_run.py --model MODEL --video-stage STAGE --foreground-backend`. Wan stages are `prepare`, `baseline`, `raylight`; LTX stages are `mesh-prepare`, `mesh`. Preparation must complete before its render stage. Video candidates reject production `--serve`. Preserve any independent GPU owner; never launch a second coordinator concurrently. Ctrl+C stops only the owned worker. Raw logs and generated clips stay private under the dated video trial directory.
