# Benchmark reporting conventions

The user's standing format, recorded October 27, 2026, applies to every future
benchmark result list in chat and repository summaries. Include every kept
model/weight-quant/engine entry once, with one selected setting per group.

## Categories, in order

1. **VRAM-only models**: all execution weights, including any active draft model,
   stay in GPU memory during inference. Loading from SATA does not change this
   classification. Ordinary host loading buffers and control work are allowed.
2. **MoE models with CPU RAM offload**: expert/model weights outside VRAM remain
   resident in host RAM during inference; SSD is only the checkpoint/load source.
   State whether CPU executes experts or RAM supplies weights to GPU kernels when
   known. A startup/load test alone does not establish RAM residency.
3. **MoE models with SSD streaming**: the engine reads model/expert weights from
   SSD during inference. GPU and CPU RAM caches do not move this profile into the
   RAM-offload category. Classify the selected setting, rather than the model name
   or engine brand alone.

Show all three categories, including a clear "None currently kept" for an empty
category. An unverified future profile must be marked unclassified pending
runtime evidence, rather than assigned by guesswork.

## Required table layout

| Model / quant | Engine | Prefill (tok/s) | Time to first token (s) | Decode (tok/s) | Context limit (tokens) | Storage size (GB) | Storage location |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |

Use these six metric/location columns in exactly this order. Identify the engine
or fork explicitly and retain the quantization. Report the measured prefill phase
separately from end-to-end first-output latency. State whether decode is native
engine timing or observed client stream throughput, with the same definition
across comparable rows. Use "Not measured" for missing values.

State benchmark date, hardware, input/output lengths, repetitions and aggregation,
cache warmth, and whether model loading is included. The context limit column is
the kept configured total window; distinguish it from tested input length and
full-window retrieval/quality qualification. Preserve raw and superseded results.

Storage size uses decimal GB and must state its scope: the current reference
counts base checkpoint GGUF/safetensors weights. Identify separate auxiliary
packs, draft assets, caches and duplicate trial files if reporting their extra
space; do not silently include them in one row and exclude them in another.
Shared checkpoints have the same size on each engine row but count only once in
physical-storage totals. Storage location must identify both the actual drive
and folder. In local chat, provide the resolved path or a clickable path with the
mount mapping. In public exports, use sanitized relative paths plus drive type
and the shared-weight relationship; keep live user/mount details private.

## Current classification

- VRAM-only: Qwen3.8-27B AutoRound INT4/INT8 on HyperQwen/vLLM and SGLang;
  shared checkpoint on SATA.
- MoE with CPU RAM offload: none currently kept as a fully RAM-resident offload
  configuration.
- MoE with SSD streaming: Qwen3.8-Flash-Next IQ3_XXS on Strata, GLM-5.3-Flash
  Maya-S24 on Maya, and shared DeepSeek-V4.1-Flash-1017 Maya-S on Strata and Maya;
  streaming weights on NVMe. GLM's selected RAM tier is a cache within its streaming
  profile, not evidence that all experts are RAM-resident.

The [maintained result tables](MAINTAINED-PROFILES.md#latest-matched-speed-evidence)
use this format. The [storage policy](STORAGE-POLICY.md) reserves NVMe for
SSD-streaming models and puts GPU/RAM-resident checkpoints on SATA. New results
must update both repositories while preserving dated benchmark evidence.
