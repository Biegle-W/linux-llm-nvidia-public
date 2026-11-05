# ComfyUI dual-GPU image setup — November 5 UTC / November 4 local, 2026

## Installed setting

ComfyUI 0.44.0, source commit `7ad7adb38f6cbb6c2b0713d3bd44c3fb2b9c8ebe`,
is installed under `runtimes/ComfyUI`, with its own Python 3.13.17 environment
under `runtimes/env-comfy`. PyTorch is 2.13.0+cu130; all dependency versions are
recorded in `config/comfy-requirements.lock` and checked before startup. The
existing NVIDIA 615.71.09 driver, GPU unlock, LLM environments and nine LLM
profiles are preserved. Comfy Desktop 1.1.8 remains a separate installed app;
this qualification uses the isolated local web backend.

The i9-13900KS host has 91.76985 GiB usable RAM, RTX 3080 Ti 12 GiB as GPU0
and RTX 3080 10 GiB as GPU1, connected through CPU PCIe4 x8/x8 with no CUDA
peer access. The denoiser stays on GPU0; encoder and VAE stay on GPU1. Both
GPUs participate through component placement, rather than denoiser tensor
parallelism. No unified 22 GiB allocator or twofold speedup is claimed.

## No CPU weight offload

The small project extension `scripts/comfy_nodes` provides explicit resident
loaders. Load and offload devices are the same CUDA device. Dynamic VRAM and
asynchronous offload are disabled; full loading is forced. The memory manager
retains resident components rather than partially unloading them based on
conservative activation estimates. Insufficient VRAM must fail instead of
streaming weights through RAM. Every load audits all currently loaded models'
parameter devices and rejects CPU weights, wrong-GPU placement or partial
loading. Ordinary checkpoint loading buffers, tokenization, orchestration and
PNG serialization still use the CPU; they are not CPU neural inference.

Only this reviewed extension is enabled. ComfyUI runs offline on loopback
port8188, with partner nodes/online features disabled and Manager not enabled.
The wrapper verifies current-boot unlock/transport proof, idle workers, no other
CUDA process, physical SATA checkpoint storage, publisher hashes, source commit
and dependency pins. The exclusive `data/GPU-LOCK` blocks LLM selection while
ComfyUI owns the cards. Unrelated workers and reservations are preserved.

## VRAM-only diffusion results

These are image metrics, not LLM prefill/decode measurements. Qwen's denoiser is
the requested official INT8 ConvRot Turbo file; its separate encoder is the
official W4A8 file to leave GPU1 capacity for the VAE. Checkpoints and publisher
SHA256 values are pinned in `config/comfy-runtime.json`.

| Model / quant | Engine | Prefill (tok/s) | First token (s) | Decode (tok/s) | Context (tokens) | Storage GB | Storage location |
| --- | --- | --- | --- | --- | --- | ---: | --- |
| Qwen-Image2.1 Turbo INT8 / W4A8 encoder / BF16 VAE | ComfyUI0.44.0 | N/A, image model | N/A | N/A | N/A | 14.244 | SATA `/dev/sda1`, `models/comfy-images/{diffusion_models,text_encoders,vae}` |
| FLUX3Klein INT8 / INT8 encoder / FP16 VAE execution | ComfyUI0.44.0 | N/A, image model | N/A | N/A | N/A | 11.023 | Same SATA folders |

| Model | Image / batch | Steps / CFG / sampler | Fresh-process first request | Warm request | Denoising, first / warm |
| --- | --- | --- | ---: | ---: | ---: |
| Qwen Turbo | 1024x1024 /1 | 8 /1 /Euler, official Turbo manual sigmas | 7.133s | 4.086s | 3.218 /3.074s |
| FLUX3Klein | 1024x1024 /1 | 16 /1 /er_sde, simple schedule | 7.130s | 5.091s | 4.181 /4.065s |

Two seeds,27001/27002, use the same detailed fox-in-snow scene caption. The
first request includes graph/model loading after backend readiness; checkpoint
file cache is warm because hash verification precedes startup. The second
request changes the seed and reuses cached text conditioning. Server execution
was6.87/3.60s; client wall includes one-second history polling. These two samples
are not a median or a general performance/quality comparison. VAE decode was
0.457/0.387s. Both PNGs have valid1024x1024 output; visual inspection confirms
a coherent fox, snow, pine tree and sunrise composition.

All21 final residency audits passed. Sampled peak used VRAM was8153/9254 MiB,
peak temperature51/38C, minimum host available85.584GiB, worker swap0 and
full-memory PSI0%. Sampling every2seconds can miss short peaks. FLUX also passed21 residency audits: sampled peak used VRAM6649/6182MiB,
peak temperature50/36C, minimum available85.213GiB, swap0 and full PSI0%.
FLUX server execution was6.96/4.37s and VAE decode0.335/0.191s. Its encoder
and VAE were on GPU1, denoiser on GPU0. Visual inspection confirms a coherent
fox/snow/pine/sunrise image. No guard stop or partial-unload log appeared in either final configuration. Owned unload and
reservation release passed. GPUs finish idle; no fallback LLM is reloaded.

## Resource guards

| Profile | Worker RAM high / max | Host available floor | Free VRAM floor | Swap policy | Pressure / thermal |
| --- | --- | --- | --- | --- | --- |
| ComfyUI resident image worker | 32 /36GiB | 2GiB | 256MiB/card throughout startup and inference | Unlimited occupancy; active writes1MiB/s, combined reads+writes8MiB/s over30s | Active full PSI10%; startup15%;82C;3 bad2s samples |

Inference is serial, idle unload600s. Missing telemetry fails closed after three
samples. A guard stop is retained locally and does not trigger an automatic
reload. Explicit launch is required to start again. Existing LLM guards and
swappiness60 are unchanged.

## MoE models with CPU RAM offload

None in this diffusion study. Existing LLM entries are unchanged; see the
[separate LLM benchmark ledger](ALL-ENTRY-BENCHMARKS-20261104.md).

## MoE models with SSD streaming

None in this diffusion study. Checkpoint files are read from SATA at loading;
the qualified diffusion execution weights remain in VRAM.

## Launch and use

Use the Desktop-only **ComfyUI Qwen Turbo** and **ComfyUI FLUX3 Klein** shortcuts, then open
`http://127.0.0.1:8188` after the terminal reports readiness. It preserves the
existing ComfyUI Desktop shortcut and application. The guarded foreground
terminal displays the backend; Ctrl+C stops only its owned service and releases
the reservation. Do not start image work alongside an independently loaded LLM.

Equivalent command, run from this repository in a real terminal:

```sh
python3 scripts/visible_terminal.py foreground --title 'ComfyUI Dual GPU' -- \
  /usr/bin/python3 scripts/comfy_run.py --model qwen-image-2.1-turbo \
  --serve --foreground-backend
```

Replace `qwen-image-2.1-turbo` with `flux3-klein` for FLUX.
The served instances use persistent `data/comfy-user/<model-id>` and
`data/comfy-output/<model-id>`.
Import the resident workflow from `config/comfy-workflows/`, or select its copied
entry in the workflow browser. The `.api.json` versions are submission graphs;
the plain `.json` files are canvas workflows. The frontend HTTP response and
availability of both workflows' node classes passed; interactive canvas import
has not been visually qualified. Use the resident loaders; replacing them with
generic CPU/offload loaders is outside this qualified setting.

The first screen attempts a separate desktop backend monitor. That handshake
was unavailable in this session, so the explicit foreground-backend option
shares logs with the visible coordinator instead. An initial missing user
directory, audit attribute and closed-port reuse check were corrected before
final qualification. Their private receipts are retained. An earlier two-image
screen emitted partial-unload bookkeeping targeting the same GPU; the final
keep-resident gate removes that behavior. Its measurements are superseded,
not counted as additional final samples.

## Verification and next work

437 CPU tests passed, including14 new residency/ownership checks. Original
source/configuration history and all nine LLM selections remain unchanged.
No editing, multi-reference, long-duration or maximum-resolution qualification
is implied. Raw logs, histories, telemetry and images remain private under
`data/comfy-qualification-20261105`; sanitized numeric evidence is in
[the result file](benchmark-results/20261105-comfy-dual-gpu.json).

Both requested profiles are installed and passed their bounded image checks.
FLUX files required the user's local Hugging Face login and publisher-term
acceptance; credentials remain outside both repositories. No remaining
benchmark or cleanup is pending. Next action: use either guarded image
launcher; future editing, multi-reference or higher-resolution work is a
separate qualification. The corresponding LLM service API/DSH remain healthy.

Sources: [official ComfyUI source](https://github.com/Comfy-Org/ComfyUI),
[Qwen weights](https://huggingface.co/Comfy-Org/Qwen-Image-2.1),
[FLUX3Klein weights](https://huggingface.co/black-forest-labs/flux-3-image-klein-comfy).
The official installed workflow templates supply Qwen's manual sigmas and the
FLUX sampler structure. A detailed caption is supplied directly, so another
prompt-enhancement LLM is not loaded alongside the image models.
