# Agent entry point

Private operational repo for the NVIDIA LLM server. Read this file, then [docs/CURRENT-STATE.md](docs/CURRENT-STATE.md). Older dated notes are in [docs/HISTORY.md](docs/HISTORY.md); use them as evidence only, since much of it is superseded.

## Owner rules (still in force)

- Write everything in English: replies, docs, code comments, commits.
- Before any startup or GPU work, run `gpu-unlock-health status --brief` and require `VERIFIED`.
- Do not create `data/GPU-LOCK` unless the owner asks. If one exists, respect it; it blocks router load/unload for anyone but its owner.
- Engine updates: always promote unless the update breaks something (failed DSH/lifecycle check, invalid comparison, missing resource evidence, or a severe slowdown: under half the speed or over 3x TTFT). Small slowdowns, token-count and cache differences are warnings. Implemented in `scripts/update_policy.py` `compare_short`.
- Validation is a short real DSH tool-call round trip plus owned unload. No long stress or full-context runs unless asked. Report: model/quant, engine, prefill tok/s, TTFT s, decode tok/s, context, storage GB and location; label cache state and single-run results honestly.
- Run test/benchmark coordinators in a visible terminal: `python3 scripts/visible_terminal.py run --title "Name" -- /abs/command args`.
- After a test, unload and leave the router idle. Do not preload or reload a fallback model.
- Permanent deletion of weights or data needs the owner's explicit yes. Keep edited-file pre-images under `data/<task>-<date>/`.
- Context increases are a proportional tradeoff (report % context gained vs % speed lost) and need quality/resource qualification before promotion.
- Never print, commit or export `data/local-api-key` or launch presets (they contain the key). Nonpersonal commits. Push routine work without asking (engine updates that pass, doc and record updates, fixes): private repo first, then the public export. Ask the owner first only when something big changed: an engine rolled back or a real break, a model/profile added, retired or swapped, weights or data deleted, router/serving/guard behaviour changed, or anything touching keys, privacy or what the public export includes. Never force-push.
- Do not touch other agents' uncommitted work.

## How the server is put together

- **Hardware:** RTX 3080 Ti 12 GB (PCI 01:00.0, index 0) + RTX 3080 10 GB (02:00.0, index 1), no P2P between them; i9-13900KS; ~91.8 GiB RAM. Models on SATA (dense) or NVMe (SSD-streaming MoE), see [storage policy](docs/STORAGE-POLICY.md).
- **Router** `nvidia-model-router.service`: authenticated OpenAI-compatible API on port 10100 (loopback + Tailscale), key in `data/local-api-key`. One model worker at a time; requesting a model id loads it, idle workers unload after 600 s. `POST /router/select`, `POST /router/unload`, `/health`, `/v1/models` all need the key. Code: `network/`.
- **Private model hub** `nvidia-model-hub.service` on 127.0.0.1:10101; workers listen privately on port 10000.
- **Registry:** `config/maintained-profiles.json` is the single source of truth for each entry's model, quant, engine, context, RAM budget and storage. `scripts/profile_catalog.py` loads it; the router re-reads it on each call.
- **Launchers:** dense Qwen via `scripts/supervise_dense.py`; MoE/native via `scripts/serve_router_moe.py` (Strata, Maya, llama.cpp). `scripts/start_model.sh` and the desktop shortcuts go through the router.
- **Guards:** RAM/swap/pressure/GPU-free/temperature watch in `scripts/inference_swap_guard.py`; shared idle and lifecycle policy in `config/inference-policy.json`.
- **DSH** (DeepSeek Harness web client) `nvidia-dsh.service`, local port 3080. Regenerate its model list with `python3 dsh/configure.py`; it picks the change up on restart.
- **Engine updates are hands-on** (since Nov 9, 2026): the 03:00 timer `nvidia-daily-engine-update.timer` is **disabled**; do not re-enable it. Check upstream with `python3 $PWD/scripts/daily_engine_update.py --check-only`, then install by hand per [ENGINE-UPDATE-RUNBOOK.md](docs/ENGINE-UPDATE-RUNBOOK.md), using `--smoke-current PROFILE` (absolute script path) before and after each swap. Promotion policy: [DAILY-ENGINE-UPDATE-POLICY.md](docs/DAILY-ENGINE-UPDATE-POLICY.md).
- **Strata Flash-Next preset** lives outside the repo at `~/.local/state/strata/launch/qwen-flash-next.json`; the router refuses it if its GPU order, layer split or stage trim drift from the registry.
- **Public mirror** `~/Desktop/linux-llm-nvidia-public`: export with `scripts/sync_public.py` (allowlist `FILES`, `RETIRED_FILES`, privacy scan; text between `<!-- private-codex-context:start/end -->` markers is stripped). Add new public docs to `FILES`.

## Working in the repo

- Tests: `python3 -m unittest discover -s tests -q` (pytest is not installed; 516 tests as of Nov 8).
- Ignored, never committed: `data/` (keys, logs, trial evidence, pre-images), `models/`, `runtimes/`, `logs/`.
- When you change something that matters, update [docs/CURRENT-STATE.md](docs/CURRENT-STATE.md) (replace stale facts, do not append a dated log) and add a dated evidence doc `docs/evidence/TOPIC-YYYYMMDD.md` (raw numbers in `docs/evidence/validation-results/` or `benchmark-results/`), list it in [docs/README.md](docs/README.md), and add a one-paragraph entry at the top of [docs/HISTORY.md](docs/HISTORY.md). If it should be public, add it to `FILES` in `scripts/sync_public.py`.
- Retiring an entry touches: registry, `config/daily-update.json`, `serve_router_moe.py`, `update_builders.py` / `update_native_builders.py`, `inference_swap_guard.py`, `cli_short_models.py`, `start_model.sh`, `dsh/configure.py` (`MODEL_REPLACEMENTS`), `sync_public.py` (`RETIRED_FILES`) and tests. See commit `b517776` (IQ1_M) as an example.

## Quick commands

```bash
gpu-unlock-health status --brief                     # must say VERIFIED
K=$(cat data/local-api-key)                          # never echo it
curl -s --noproxy '*' -H "Authorization: Bearer $K" http://127.0.0.1:10100/v1/models
curl -s --noproxy '*' -H "Authorization: Bearer $K" -H 'Content-Type: application/json' \
  -X POST http://127.0.0.1:10100/router/unload -d '{}'
nvidia-smi --query-gpu=index,memory.used --format=csv,noheader   # idle = 1 MiB each
systemctl --user is-enabled nvidia-daily-engine-update.timer   # expect: disabled (updates are hands-on)
python3 scripts/weights_tracker.py                   # per-drive storage + unused weights (read-only)
journalctl --user -u nvidia-daily-engine-update.service --since today
python3 "$PWD/scripts/daily_engine_update.py" --check-only       # read upstream revisions only
```

If the retired script is ever run with `--manual`: it refuses to start engine work while either repo (private or public checkout) has uncommitted tracked edits, and it only pushes commits it made itself, so push your own commits first or the nightly push is deferred. A deferral is a WARNING in the journal and the run still exits 0; while a push is held the next run also skips engine work, and after 3 held runs in a row the run fails on purpose (`last_deferral` in `data/daily-update/state.json` shows the reason). Rejected engine revisions are remembered in `data/daily-update/state.json` under `rejected` and are not retried until removed from there (log the removal in `rejection_history`).

## Docs layout

`docs/` holds the reference docs that are kept current; `docs/evidence/` holds dated, frozen evidence and raw results. Index: [docs/README.md](docs/README.md).
