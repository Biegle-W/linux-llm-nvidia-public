# Bolt API ID renamed to `bolt-llamacpp` — November 6, 2026

At the humans request, the Bolt entrys ID changed from `bolt-vllm` to `bolt-llamacpp`. The old ID dated from the retired AWQ/vLLM setup; the entry has served the official native IQ2 checkpoint on pinned llama.cpp since November 4 ([entry](BOLT-IQ2-ENTRY-20261104.md), [AWQ removal](BOLT-AWQ-REMOVAL-20261104.md)).

## What changed

- `config/maintained-profiles.json`, `config/daily-update.json` and every script, router, worker-manager, swap-guard and updater reference use `bolt-llamacpp`. CLI: `./scripts/start_model.sh bolt` is unchanged.
- Compatibility: `network/router.py` maps `bolt-vllm` to `bolt-llamacpp` in `LEGACY_MODEL_ALIASES`. Requests, `/router/select` and `GET /v1/models/bolt-vllm` keep working, and responses echo the alias the client sent. `GET /v1/models` lists only the new ID.
- DSH: `dsh/configure.py` lists `bolt-vllm` in `MODEL_REPLACEMENTS`. Re-registration drops the old router entry and migrates saved router selections to the new ID; providers on other base URLs keep their entries.

## What did not change

Weights, runtime manifest, llama.cpp pin, 163,840-token allocation, fit targets, KV types, RAM/VRAM/swap/thermal guards, defaults and the other eight entries are unchanged. No inference benchmark was repeated; the rename does not alter request handling.

Dated evidence, benchmark JSON and log/telemetry directories keep the `bolt-vllm` name they were recorded under. New guard-stop latches, telemetry and engine logs use the new ID. No Bolt guard-stop latch existed at the time of the rename.

## Verification

All 519 CPU regressions pass (516 before the change, plus new checks for the router alias and DSH replacement). The router alias check fails when the alias is removed.
