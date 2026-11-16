# MiniMax H3 Image added to the image models — November 15, 2026

At the owner's request, with the choice of quantization researched first by the council of agents (codex, hermes, kimi, agy and a Claude worker; every research note was checked by a second member).

| Part | File | Size | Where it runs |
|---|---|---:|---|
| Denoiser | `MiniMax-H3-Image-AD-Q3_K.gguf` (`AtomicChat/MiniMax-H3-Image-GGUF` @ `5da8538f0b9a`) | 8.73 GB | fully on the RTX 3080 Ti (cuda:0) |
| Text encoder | `qwen3vl_32b_minimax_h3_int8_convrot.safetensors` (`Comfy-Org/MiniMax-H3-Image` @ `0bb149f51e31`) | 27.14 GB | **system RAM, streamed through the RTX 3080 (cuda:1)** |
| VAE | `minimax_h3_image_vae_fp16.safetensors` (same repo) | 1.17 GB | fully on the RTX 3080 (cuda:1) |

Entry id `minimax-h3-image`; launcher "ComfyUI MiniMax H3 Image"; files in `models/comfy-images` (SATA), 37.04 GB, SHA-256 checked against the publishers' values at download and again before every start.

## What the research found

- The model is `MiniMaxAI/MiniMax-H3-Image` (released November 10): a 33.1B-parameter image transformer with a Qwen3-VL-32B text encoder and its own VAE. It is not the older H3 video model, not PrunaAI's P-H3-Image, and shares no file with Qwen-Image or FLUX 3 Klein.
- ComfyUI 0.45.0 at the installed commit supports it natively. No upgrade was needed.
- **Denoiser.** The official files do not fit a 12 GB card (int8 20.98 GB; W4A8 12.55 GB leaves 64 MiB). A 3-bit GGUF does. AtomicChat's files carry the model's step configuration in the header and load with the ComfyUI-GGUF commit already on this server; several other GGUF sets are built for stable-diffusion.cpp and fail in ComfyUI. The publisher's own comparison against the full-precision model (40 captions at 2048², lower is closer): Q4 0.254, **Q3 0.334**, Q2 0.379. The 4-bit file is 2.65 GiB larger than the 3-bit one, and the 3-bit one leaves 2.09 GiB free here at 1024², so 4-bit cannot fit and was not downloaded.
- **Text encoder.** No published encoder fits the 10 GB card. The smallest standard file is 13.30 GB. The 2-bit GGUF encoders were checked from their headers and the loader source: each ends up over 10 GiB once loaded (the loader always builds the vision tower and expands the token table), and they need a forked GGUF node.
- **Owner decision (November 15):** run the text encoder from system RAM for this model. This is an exception to `cpu_weight_offload: false`, limited to this one encoder.
- Settings: 6 steps, CFG 1, euler, simple, no shift node, no negative prompt. The model is rated for 4 to 20 megapixels and is tuned for 2048² and above; 1024² is below its rated range.
- **Licence:** MiniMax-H3-Image Community License Agreement. It excludes the US, EU, UK and South Korea from its territory and needs written permission for a hosted service to third parties or above US$1M annual revenue. The owner was told before the install.

## How it is wired

- `scripts/comfy_nodes/__init__.py` has two new nodes. `NvidiaResidentDenoiserGGUF` loads the GGUF with ComfyUI-GGUF's own loader (imported privately, the GGUF custom node itself stays off in the image runtime) and fully loads it on cuda:0; it passes the same placement audit as the other denoisers. `NvidiaH3RAMEncoder` keeps the encoder's weights in RAM, streams them through cuda:1 for each encode and releases the card afterwards.
- The audit exception is per object: only the encoder that node registers may have weights on the CPU, and only for the `minimax-h3-image` launcher. Every other model, and the H3 denoiser and VAE, keep the all-on-GPU checks. Clones, LoRA patches and mixed loads of that encoder fail closed.
- The image environment gained one package, `gguf==0.19.0` (`config/comfy-requirements.lock`). No launch flag changed.
- A read-only study of the ComfyUI and ComfyUI-GGUF source by Codex (gpt-6.1-sol) produced the loader design; it was implemented and tested by hand.

## Measurements

`scripts/comfy_run.py --model minimax-h3-image --size N`, two seeds each, GPUs unlocked and idle (1 MiB) before and after. Lowest free VRAM is from the 2-second guard samples, so short peaks can be missed.

| Size | Result | Text encoding (s) | Sampling, 6 steps (s) | VAE decode (s) | Lowest free VRAM, 3080 Ti / 3080 (MiB) |
|---|---|---:|---:|---:|---:|
| 1024² | pass, 2 images | 13.3 | 6.1 (1.0 s/step) | 0.4 / 0.1 | 2,089 / 6,962 |
| 2048² | pass, 2 images | 9.3 | 13.5 (2.25 s/step) | 0.7 / 0.5 | 1,961 / 6,962 |
| 4096² | pass, 2 images | 9.2 | 58.1 and 58.8 (9.7 s/step) | 2.1 / 2.0 | 521 / 6,962 |

- First image at 1024² took 24.4 s from the request, including loading all three parts; the second, with the same prompt, 7.1 s. At 4096² the two images took 73.8 and 62.7 s.
- The text encoder runs once per prompt; ComfyUI reuses the result while the prompt is unchanged. During an encode nothing of it stays resident on the card (the log reports 25.9 GiB kept in RAM and a 4.45 GiB transfer buffer). Lowest host memory available was 59.7 GiB.
- 4096² leaves 521 MiB on the 12 GB card, above the 256 MiB floor but not by much.
- The fox test images at 1024² and 2048² were looked at: correct subject and composition, sharp fur and snow detail, natural colour, no artefacts seen. This is one prompt; no comparison against a larger quant was made.
- Regression: FLUX 3 Klein and Qwen-Image 2.1 Turbo at 1024² give byte-identical images and the same times as on November 11 and 12 with the changed loader code.
- Serve mode, one session, three requests at 1536x1024 with the prompt changed each time (through the HTTP API, graph from `config/comfy-workflows/minimax-h3-image.api.json`): all succeed, 40.7 s for the first (with loading) and 12.0 s for each of the next two. Re-encoding a new prompt takes 3.7 s once the encoder file is in memory (14.9 s the first time). A sign prompt rendered its two words correctly. The session stopped cleanly and released the GPUs.
- A read-only review of the new loader code by Codex found no defect; it noted that the new unit tests cover the placement checks only, not the load and release life cycle (that part rests on the runs above).
- `--check-ui` passes. The saved workflow (`config/comfy-workflows/minimax-h3-image.json`, 2048² by default) was written by hand and has not been opened in the browser UI.

## Not done

- No image-editing (reference picture) run; that path uses the encoder's vision tower and more memory.
- One non-square size only (1536x1024), no long session, no quality comparison with other quants, no prompt-enhancer model.
- The CPU-only encoder mode exists in the node (`mode: cpu`) but was not run.
