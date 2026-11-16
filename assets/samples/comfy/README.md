# Generated ComfyUI benchmark samples

Selected AI-generated outputs from the November4–5,2026 tests: one seed27001 first-request sample per image model/resolution and successful video setup. These are existing test outputs, not new generations. Embedded ComfyUI workflow metadata was removed. PNG pixels and decoded video/audio content were verified identical to the originals; videos were remuxed without re-encoding. Poster PNGs show each clip's first frame.

## Images

| Qwen Image2.1 Turbo INT8 | FLUX3 Klein INT8 |
|---|---|
| ![Qwen Turbo1K fox in snow](qwen-turbo-1k.png) | ![FLUX Klein1K fox in snow](flux-klein-1k.png) |
| [Native1024PNG](qwen-turbo-1k.png) · [Native2048PNG](qwen-turbo-2k.png) | [Native1024PNG](flux-klein-1k.png) · [Native2048PNG](flux-klein-2k.png) |

Qwen uses8Euler steps; FLUX uses16er_sde steps. Both use CFG1 and the same fox/snow/pine/sunrise caption. The2K images are native generations, not enlarged1K images. [1K setup and benchmarks](../../../docs/evidence/COMFY-DUAL-GPU-20261105.md) · [2K results and failed4K arms](../../../docs/evidence/COMFY-2K4K-20261104.md).

## Videos

| Setup | Preview | Download / play |
|---|---|---|
| Wan2.2 TI2V5B FP16 regular baseline | ![Wan baseline first frame](wan-baseline-poster.png) | [MP4:512x288,33frames,16fps](wan-baseline.mp4) |
| Wan2.2 TI2V5B FP16 Raylight FSDP+Ulysses2 | ![Wan Raylight first frame](wan-raylight-poster.png) | [MP4:512x288,33frames,16fps](wan-raylight.mp4) |
| LTX2.3 distilled1.1 Q4_0 Mesh, phased GPU reuse | ![LTX Mesh first frame](ltx-mesh-poster.png) | [MP4 with audio:512x288,33frames,24fps](ltx-mesh.mp4) |

Wan uses20Euler steps/CFG5. LTX uses8distilled Euler steps/CFG1 and the tested28/20-block split, ending the owned back-half server before GPU VAE decoding. The clips show a fox in a winter scene. [Video protocol, timings, patches and resource limits](../../../docs/evidence/COMFY-VIDEO-DUAL-GPU-20261104.md).

The workloads and quantization differ; these samples are visual evidence of the bounded tests, not a controlled quality ranking. [Manifest](manifest.json) records dimensions, seeds, original/output hashes, byte sizes and benchmark references. Only the reviewed metadata-free sample bytes are allowed through the public exporter; raw logs, original embedded workflows, credentials and local runtime files stay private.

## 720p /1080p video samples — November5

| Setup | Preview | Download / play |
|---|---|---|
| Wan regular720p | ![Wan720p first frame](wan-baseline-720p-poster.png) | [MP4:1280x720,33frames,16fps](wan-baseline-720p.mp4) |
| LTX Mesh720p | ![LTX720p first frame](ltx-mesh-720p-poster.png) | [MP4 with audio:1280x720,33frames,24fps](ltx-mesh-720p.mp4) |
| LTX Mesh1080p | ![LTX1080p first frame](ltx-mesh-1080p-poster.png) | [MP4 with audio:1920x1080,33frames,24fps](ltx-mesh-1080p.mp4) |

These are native padded-latent generations cropped to exact output dimensions, with no upscaling. [HD benchmark protocol, results and limits](../../../docs/evidence/COMFY-VIDEO-720P1080P-20261105.md).

## Repaired Wan1080p — November5

| Setup | Preview | Download / play |
|---|---|---|
| Wan native16/14 GPU split | ![Wan native1080p first frame](wan-baseline-1080p-poster.png) | [MP4:1920x1080,33frames,16fps](wan-baseline-1080p.mp4) |
| Wan Raylight, deterministic guidance | ![Wan Raylight1080p first frame](wan-raylight-1080p-poster.png) | [MP4:1920x1080,33frames,16fps](wan-raylight-1080p.mp4) |

[Fixes, timings and GPU-only qualification](../../../docs/evidence/WAN1080-FIX-20261105.md).

## MiniMax H3 Image — November 15

| Fox caption, 2048x2048 | Text rendering, 1536x1024 |
|---|---|
| ![MiniMax H3 Image 2K fox in snow](minimax-h3-2k.png) | ![MiniMax H3 Image sign reading OPEN SUNDAY](minimax-h3-sign-1536x1024.png) |
| [Native 1024 PNG](minimax-h3-1k.png) · [Native 2048 PNG](minimax-h3-2k.png) · [Native 4096 PNG](minimax-h3-4k.png) | [Native 1536x1024 PNG](minimax-h3-sign-1536x1024.png) |

MiniMax H3 Image with the 3-bit GGUF denoiser (AD-Q3_K) and the int8 text encoder streamed from system RAM: 6 Euler steps, CFG 1. The fox images use the same caption and seed 27001 as the other image models and are native generations at each size; the model is tuned for 2048x2048 and above, so 1024 is below its rated range. The sign image comes from the serve-mode check (seed 31001). These are existing test outputs with the embedded workflow metadata removed; the compressed pixel data is unchanged. Every MiniMax H3 image generated on November 15 is kept here: the second seed of each fox run ([1024](minimax-h3-1k-seed27002.png) · [2048](minimax-h3-2k-seed27002.png) · [4096](minimax-h3-4k-seed27002.png)) and the two lighthouse images from the serve-mode check ([seed 31000](minimax-h3-lighthouse-1536x1024-seed31000.png) · [seed 31002](minimax-h3-lighthouse-1536x1024-seed31002.png)). [Research, setup and measurements](../../../docs/evidence/MINIMAX-H3-IMAGE-20261115.md).

## All other outputs of the November 4-5 runs and later repeats — added November 16

At the owner's request every remaining generated image and clip from the test runs is kept here too, not only the selected first-request samples above. They are existing outputs: second seeds, repeated runs and the interactive-entry runs. Clips whose decoded frames and audio are identical to a sample already kept were not added twice. Metadata was removed the same way as above; no poster frames were made for these.

| Image | Size | Seed |
|---|---|---:|
| [Qwen Image2.1 Turbo INT8](qwen-turbo-1k-seed27002.png) | 1024x1024 | 27002 |
| [FLUX3 Klein INT8](flux-klein-1k-seed27002.png) | 1024x1024 | 27002 |
| [Qwen Image2.1 Turbo INT8](qwen-turbo-2k-seed27002.png) | 2048x2048 | 27002 |
| [FLUX3 Klein INT8](flux-klein-2k-seed27002.png) | 2048x2048 | 27002 |

| Clip | Size, frames, fps | Seed | Audio | Run (result) |
|---|---|---:|---|---|
| [wan22-5b-entry-512x288-seed27002](wan22-5b-entry-512x288-seed27002.mp4) | 512x288, 33, 16 | 27002 | no | 015857-wan22-5b-entry (pass) |
| [ltx23-mesh-entry-512x288-seed27001](ltx23-mesh-entry-512x288-seed27001.mp4) | 512x288, 33, 24 | 27001 | yes | 020033-ltx23-mesh-entry (pass) |
| [ltx23-mesh-entry-512x288-seed27002](ltx23-mesh-entry-512x288-seed27002.mp4) | 512x288, 33, 24 | 27002 | yes | 020033-ltx23-mesh-entry (pass) |
| [wan22-5b-raylight-raylight-512x288-seed27001](wan22-5b-raylight-raylight-512x288-seed27001.mp4) | 512x288, 33, 16 | 27001 | no | 020316-wan22-5b-raylight-raylight (pass) |
| [wan22-5b-raylight-raylight-512x288-seed27002](wan22-5b-raylight-raylight-512x288-seed27002.mp4) | 512x288, 33, 16 | 27002 | no | 020316-wan22-5b-raylight-raylight (pass) |
| [wan22-5b-raylight-raylight-512x288-seed27002-run211656](wan22-5b-raylight-raylight-512x288-seed27002-run211656.mp4) | 512x288, 33, 16 | 27002 | no | 211656-wan22-5b-raylight-raylight (pass) |
| [ltx23-mesh-mesh-512x288-seed27001](ltx23-mesh-mesh-512x288-seed27001.mp4) | 512x288, 33, 24 | 27001 | yes | 211835-ltx23-mesh-mesh (pass) |
| [ltx23-mesh-mesh-512x288-seed27001-run212011](ltx23-mesh-mesh-512x288-seed27001-run212011.mp4) | 512x288, 33, 24 | 27001 | yes | 212011-ltx23-mesh-mesh (pass) |
| [ltx23-mesh-entry-512x288-seed27001-run212214](ltx23-mesh-entry-512x288-seed27001-run212214.mp4) | 512x288, 33, 24 | 27001 | yes | 212214-ltx23-mesh-entry (pass) |
| [ltx23-mesh-entry-512x288-seed27002-run212214](ltx23-mesh-entry-512x288-seed27002-run212214.mp4) | 512x288, 33, 24 | 27002 | yes | 212214-ltx23-mesh-entry (pass) |
| [ltx23-mesh-entry-512x288-seed27001-run213602](ltx23-mesh-entry-512x288-seed27001-run213602.mp4) | 512x288, 33, 24 | 27001 | yes | 213602-ltx23-mesh-entry-seed27001 (pass) |
| [ltx23-mesh-entry-512x288-seed27001-run233930](ltx23-mesh-entry-512x288-seed27001-run233930.mp4) | 512x288, 33, 24 | 27001 | yes | 233930-ltx23-mesh-entry (pass) |
| [ltx23-mesh-entry-512x288-seed27002-run233930](ltx23-mesh-entry-512x288-seed27002-run233930.mp4) | 512x288, 33, 24 | 27002 | yes | 233930-ltx23-mesh-entry (pass) |
| [wan22-5b-raylight-baseline-1280x720-seed27002](wan22-5b-raylight-baseline-1280x720-seed27002.mp4) | 1280x720, 33, 16 | 27002 | no | 000955-wan22-5b-raylight-baseline-720p (pass) |
| [ltx23-mesh-mesh-1280x720-seed27002](ltx23-mesh-mesh-1280x720-seed27002.mp4) | 1280x720, 33, 24 | 27002 | yes | 001506-ltx23-mesh-mesh-720p-seed27002 (pass) |
| [ltx23-mesh-mesh-1920x1080-seed27002](ltx23-mesh-mesh-1920x1080-seed27002.mp4) | 1920x1080, 33, 24 | 27002 | yes | 001756-ltx23-mesh-mesh-1080p-seed27002 (pass) |
| [wan22-5b-raylight-raylight-1920x1080-seed27002](wan22-5b-raylight-raylight-1920x1080-seed27002.mp4) | 1920x1080, 33, 16 | 27002 | no | 011545-wan22-5b-raylight-raylight-1080p (pass) |
| [wan22-5b-raylight-baseline-1920x1080-seed27002](wan22-5b-raylight-baseline-1920x1080-seed27002.mp4) | 1920x1080, 33, 16 | 27002 | no | 012227-wan22-5b-raylight-baseline-1080p (pass) |
| [ltx23-mesh-entry-1280x720-seed27001](ltx23-mesh-entry-1280x720-seed27001.mp4) | 1280x720, 33, 24 | 27001 | yes | 014152-ltx23-mesh-entry-720p-seed27001 (pass) |
| [ltx23-mesh-entry-1920x1080-seed27001](ltx23-mesh-entry-1920x1080-seed27001.mp4) | 1920x1080, 33, 24 | 27001 | yes | 014258-ltx23-mesh-entry-1080p-seed27001 (pass) |
| [ltx23-mesh-entry-1280x720-seed27001-run213832](ltx23-mesh-entry-1280x720-seed27001-run213832.mp4) | 1280x720, 33, 24 | 27001 | yes | 213832-ltx23-mesh-entry-720p-seed27001 (pass) |
| [ltx23-mesh-entry-1920x1080-seed27001-run213940](ltx23-mesh-entry-1920x1080-seed27001-run213940.mp4) | 1920x1080, 33, 24 | 27001 | yes | 213940-ltx23-mesh-entry-1080p-seed27001 (pass) |
