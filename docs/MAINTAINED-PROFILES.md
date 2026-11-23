# Maintained profiles (model registry)

`config/maintained-profiles.json` is the single source of truth for the ten enabled text entries. The router re-reads it on each call; `scripts/profile_catalog.py` loads and validates it (`python3 scripts/profile_catalog.py` prints the catalog). The current entries and their numbers are summarized in [CURRENT-STATE.md](CURRENT-STATE.md). The dated log this file used to carry is archived in [MAINTAINED-PROFILES-LOG-THROUGH-20261108.md](evidence/MAINTAINED-PROFILES-LOG-THROUGH-20261108.md).

## What an entry records

API id, model and quantization, engine and its runtime manifest, allocated context, `worker_memory_gib` budget, weight storage path and drive, selected launch settings (for example the Flash-Next GPU order, layer split and stage trim), and the latest qualified speed measurements with their source. Until November 9, 2026 the nightly updater rewrote the measurement block when it promoted an engine build and kept the previous one as history. Hands-on updates record their numbers in the evidence doc and the update ledger instead.

The catalog rejects duplicate model/quant/engine combinations, dense context that does not match the engine arguments, and unqualified CPU weight offload. Flash-Next has two entries with separate weights, `flash-next-strata` (IQ3_XXS, the default) and `flash-next-iq4xs-strata` (UD-IQ4_XS-v31); they share the engine binary, the MTP head and the vision projector. Two pairs share one checkpoint on disk: `qwen27b-hyperqwen` / `qwen27b-sglang`, and `deepseek-maya` / `deepseek-unsloth-strata`.

Inkling 2 Mini is Thinking Machines Lab's Apache 2.0 26B looped MoE. `inkling-llamacpp` uses UD-Q4_K_M weights and an F16 picture projector on SATA. Its separate Unsloth llama.cpp build serves 32,768 tokens with thinking always on. The November 21 trial passed a tool call and follow-up. Router load, the short check and an owned unload passed on November 22.

Tencent Hy4-Flash 220B-A12B uses SQ-96 on the 12 GB card with the experts in RAM and Engram on NVMe. `hy4-flash-strata` serves text and small pictures with 131,072 tokens (context memory reserved at start; pictures of 1024 pixels and larger are refused). The trial passed a tool call and follow-up. Router load, the short check and an owned unload passed on November 22.

The text entry `hy4-flash-maya` splits Maya-L across both cards at 131,072 tokens and reads the n-gram table from the SATA SSD. It is the only entry whose soft memory cap equals its hard limit (89.77 GiB), approved by the owner on November 23 because the shared soft cap throttled its memory-mapped model into the pressure guard. It passed the router checks; its short tool-use test scored 43.3 (`hy4-flash-strata` 57.9); under that sustained load the memory-pressure guard stopped it at minute 30. A separate Inkling SQ-10 entry on Strata was tried and dropped (see the Inkling trial note).

## Selection rule

Keep a qualified configuration that no other configuration beats on prefill/TTFT, decode and safe validated context at once. When speed and context trade off, prefer the largest locally validated safe allocation with competitive speed, then break ties on prefill/TTFT and decode. Context increases are reported as % context gained against % speed lost and need quality and resource qualification before promotion ([context policy](evidence/CONTEXT-VALIDATION-POLICY-20261101.md)). Allocated context is a capacity setting, not a full-window quality claim.

## Changing or retiring an entry

- Measurements must follow [BENCHMARK-REPORTING.md](BENCHMARK-REPORTING.md); weights must follow [STORAGE-POLICY.md](STORAGE-POLICY.md).
- After editing the registry run the unit tests and `python3 dsh/configure.py`, then a short real DSH tool-call check through the router and an unload.
- Retiring an entry touches many files; the checklist is in [AGENTS.md](../AGENTS.md) and commit `b517776` is a worked example.
