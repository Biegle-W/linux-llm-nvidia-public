# Maintained profiles (model registry)

`config/maintained-profiles.json` is the single source of truth for every enabled entry. The router re-reads it on each call; `scripts/profile_catalog.py` loads and validates it (`python3 scripts/profile_catalog.py` prints the catalog). The current entries and their numbers are summarized in [CURRENT-STATE.md](CURRENT-STATE.md). The dated log this file used to carry is archived in [MAINTAINED-PROFILES-LOG-THROUGH-20261108.md](evidence/MAINTAINED-PROFILES-LOG-THROUGH-20261108.md).

## What an entry records

API id, model and quantization, engine and its runtime manifest, allocated context, `worker_memory_gib` budget, weight storage path and drive, selected launch settings (for example the Flash-Next GPU order, layer split and stage trim), and the latest qualified speed measurements with their source. The daily updater rewrites the measurement block when it promotes an engine build and keeps the previous one as history.

The catalog rejects duplicate model/quant/engine combinations, dense context that does not match the engine arguments, and unqualified CPU weight offload. Two pairs share one checkpoint on disk: `qwen27b-hyperqwen` / `qwen27b-sglang`, and `deepseek-maya` / `deepseek-unsloth-strata`.

## Selection rule

Keep a qualified configuration that no other configuration beats on prefill/TTFT, decode and safe validated context at once. When speed and context trade off, prefer the largest locally validated safe allocation with competitive speed, then break ties on prefill/TTFT and decode. Context increases are reported as % context gained against % speed lost and need quality and resource qualification before promotion ([context policy](evidence/CONTEXT-VALIDATION-POLICY-20261101.md)). Allocated context is a capacity setting, not a full-window quality claim.

## Changing or retiring an entry

- Measurements must follow [BENCHMARK-REPORTING.md](BENCHMARK-REPORTING.md); weights must follow [STORAGE-POLICY.md](STORAGE-POLICY.md).
- After editing the registry run the unit tests and `python3 dsh/configure.py`, then a short real DSH tool-call check through the router and an unload.
- Retiring an entry touches many files; the checklist is in [AGENTS.md](../AGENTS.md) and commit `b517776` is a worked example.
