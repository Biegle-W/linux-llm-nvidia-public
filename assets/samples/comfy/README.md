# Generated ComfyUI benchmark samples

Seven AI-generated outputs from the November4,2026 tests: one seed27001 first-request sample per image model/resolution and selected video setup. These are existing test outputs, not new generations. Embedded ComfyUI workflow metadata was removed. PNG pixels and decoded video/audio content were verified identical to the originals; videos were remuxed without re-encoding. Poster PNGs show each clip's first frame.

## Images

| Qwen Image2.1 Turbo INT8 | FLUX3 Klein INT8 |
|---|---|
| ![Qwen Turbo1K fox in snow](qwen-turbo-1k.png) | ![FLUX Klein1K fox in snow](flux-klein-1k.png) |
| [Native1024PNG](qwen-turbo-1k.png) · [Native2048PNG](qwen-turbo-2k.png) | [Native1024PNG](flux-klein-1k.png) · [Native2048PNG](flux-klein-2k.png) |

Qwen uses8Euler steps; FLUX uses16er_sde steps. Both use CFG1 and the same fox/snow/pine/sunrise caption. The2K images are native generations, not enlarged1K images. [1K setup and benchmarks](../../../docs/COMFY-DUAL-GPU-20261105.md) · [2K results and failed4K arms](../../../docs/COMFY-2K4K-20261104.md).

## Videos

| Setup | Preview | Download / play |
|---|---|---|
| Wan2.2 TI2V5B FP16 regular baseline | ![Wan baseline first frame](wan-baseline-poster.png) | [MP4:512x288,33frames,16fps](wan-baseline.mp4) |
| Wan2.2 TI2V5B FP16 Raylight FSDP+Ulysses2 | ![Wan Raylight first frame](wan-raylight-poster.png) | [MP4:512x288,33frames,16fps](wan-raylight.mp4) |
| LTX2.3 distilled1.1 Q4_0 Mesh, phased GPU reuse | ![LTX Mesh first frame](ltx-mesh-poster.png) | [MP4 with audio:512x288,33frames,24fps](ltx-mesh.mp4) |

Wan uses20Euler steps/CFG5. LTX uses8distilled Euler steps/CFG1 and the tested28/20-block split, ending the owned back-half server before GPU VAE decoding. The clips show a fox in a winter scene. [Video protocol, timings, patches and resource limits](../../../docs/COMFY-VIDEO-DUAL-GPU-20261104.md).

The workloads and quantization differ; these samples are visual evidence of the bounded tests, not a controlled quality ranking. [Manifest](manifest.json) records dimensions, seeds, original/output hashes, byte sizes and benchmark references. Only the reviewed metadata-free sample bytes are allowed through the public exporter; raw logs, original embedded workflows, credentials and local runtime files stay private.
