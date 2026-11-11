# Router, model hub, DSH and desktop launchers

Reference for the network side of the server. What is live right now (models, versions, speeds) is in [docs/CURRENT-STATE.md](../docs/CURRENT-STATE.md); the dated log this file used to carry is archived in [NETWORK-README-LOG-THROUGH-20261108.md](../docs/evidence/NETWORK-README-LOG-THROUGH-20261108.md).

## Components

| Unit | Code | Listens on | Role |
|---|---|---|---|
| `nvidia-model-router.service` | `network/` | 10100 (loopback + Tailscale) | Authenticated OpenAI-compatible API; loads one worker at a time |
| `nvidia-model-hub.service` | `network/` | 127.0.0.1:10101 | Private model hub used by the router |
| model worker (one at a time) | `scripts/supervise_dense.py`, `scripts/serve_router_moe.py` | private port 10000 | The engine process for the selected entry; its own web UI is on this port |
| `nvidia-dsh.service` | `dsh/` | local port 3080 | DeepSeek Harness web client; lists the router models |

## Using the API

Base URL `http://127.0.0.1:10100/v1` (or the server's Tailscale address) with `Authorization: Bearer <key>`; the key is `data/local-api-key` and is never printed, committed or exported. `/v1/models` is the authoritative list; the model id picks model, quantization and engine together.

- Chat Completions with streaming and tool calls; dense engines also expose legacy Completions.
- The first request to an unloaded model waits for the load (tens of seconds; DeepSeek prefill can take minutes), so use long client timeouts. Streams receive keep-alive comments while waiting.
- `POST /router/select {"model": "<id>"}` preloads; `POST /router/unload {}` unloads an idle worker (refused while a reply or switch is active). `/health` shows in-flight and queued counts. All endpoints need the key.
- Admission: one active request, up to 8 waiting in FIFO order (`network/request_admission.py`); a full queue returns 429 with `Retry-After: 5`. Same-model concurrency is off because every engine runs one sequence.
- Idle workers unload after 600 s (`config/inference-policy.json`). Unknown or retired ids return 404 and never start a worker.
- The router stops only its own systemd units; an unmanaged listener on port 10000 blocks loading instead of being killed. `data/GPU-LOCK`, if present, blocks load/unload for anyone but its owner.

## Guards

Every entry runs under the per-entry worker RAM budget in the registry (`worker_memory_gib`; currently 87.77 GiB soft / 89.77 GiB hard for all), with a 2 GiB host-available floor and GPU temperature and pressure/swap watches in `scripts/inference_swap_guard.py`. Until November 9, 2026 the nightly updater printed the effective guard values at the end of each entry in [DAILY-ENGINE-UPDATES.md](../docs/DAILY-ENGINE-UPDATES.md); current values are in the registry and [ALL-ENTRY-BENCHMARKS-20261105.md](../docs/evidence/ALL-ENTRY-BENCHMARKS-20261105.md). Policy background: [INFERENCE-SWAP-POLICY.md](../docs/INFERENCE-SWAP-POLICY.md).

## Desktop shortcuts and commands

- Shortcuts: **HyperQwen vLLM**, **SGLang**, **Strata** (pick Flash-Next or DeepSeek, then open Strata's web UI on port 10000), **Maya** (pick GLM or DeepSeek, same port), **DeepSeek Harness**. All go through the router. Icon sources: [assets/icons/README.md](../assets/icons/README.md).
- PATH commands: `llm-hyperqwen`, `llm-sglang`, `llm-strata`, `llm-maya` (accept `--model <id>`; Strata/Maya accept `--web`) and `dsh`.
- `scripts/start_model.sh qwen | qwen27b [hyperqwen|sglang] | glm | maya-deepseek | strata-deepseek | bolt` loads an entry through the router.
- Native UI setting changes only affect the private generated run config; maintained settings live in the registry.

## Install and maintenance

```bash
python3 dsh/configure.py          # regenerate DSH's model list from the registry
python3 network/install.py        # install/refresh user services, commands and shortcuts
systemctl --user status nvidia-model-router nvidia-model-hub nvidia-dsh
python3 -m unittest discover -s tests -q
```

DSH is pinned to `@deepseek-ai/dsh@0.2.1-rc.2` with its lockfile under `runtimes/deepseek-harness/` (Node.js 22.22.1; `npm ci --ignore-scripts`, then rebuild `node-pty`, `koffi` and `@deepseek-ai/dsh-subprocess-local`). DSH picks up a regenerated model list when `nvidia-dsh` restarts. The installer refuses to replace unrelated commands, shortcuts or services and does not touch Tailscale ACLs, SSH or firewall rules; user lingering keeps services running after logout. The router re-adopts its running worker after a restart.
