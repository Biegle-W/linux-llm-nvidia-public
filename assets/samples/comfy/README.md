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
