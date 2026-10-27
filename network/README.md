# NVIDIA model router, Tailscale and DeepSeek Harness

The deployment follows the AMD repository's catalog/on-demand switching design,
adapted to the six selected NVIDIA profiles. Only one inference worker runs at a
time. The authenticated router listens on loopback and this computer's explicit
Tailscale IPv4 address at port **10100**, preserving the original worker's private
loopback port **10000**. DSH remains a separate loopback service at **3080**.

## Select a model and engine

Use the router base URL `http://127.0.0.1:10100/v1`, or from a tailnet device
`http://100.x.y.z:10100/v1` with this computer's actual Tailscale address. Both
require `Authorization: Bearer <local-key>`. The existing owner-only key is in
`data/local-api-key`; it is never published. `/v1/models` is the authoritative
catalog. Requesting its ID selects the model, quantization and engine together:

| API model ID | Engine | Context allocation |
| --- | --- | ---: |
| `qwen27b-hyperqwen` | HyperQwen/vLLM | 32,768 |
| `qwen27b-sglang` | SGLang | 16,384 |
| `flash-next-strata` | Strata | 32,768 |
| `glm-maya` | Maya | 32,768 |
| `deepseek-strata` | Strata | 65,536 |
| `deepseek-maya` | Maya | 32,768 |

```python
import os
from openai import OpenAI

client = OpenAI(base_url="http://100.x.y.z:10100/v1",
                api_key=os.environ["LOCAL_LLM_API_KEY"], timeout=7200)
for chunk in client.chat.completions.create(
    model="qwen27b-hyperqwen",
    messages=[{"role": "user", "content": "Hello"}], stream=True,
):
    if chunk.choices:
        print(chunk.choices[0].delta.content or "", end="", flush=True)
```

The router supports OpenAI Chat Completions, including streaming and tool-call
transport. Dense engines also expose legacy Completions. This does not claim
that every model's tool-call quality or every OpenAI endpoint is supported.
Model aliases are translated to worker IDs and translated back in responses.
Streaming connections receive comments while loading or waiting for inference.
Long model loads and long DeepSeek prefills require generous client timeouts.

`POST /router/select` with `{"model":"<id>"}` preloads without generating.
`POST /router/unload` with `{}` unloads an idle managed worker; it refuses an
active reply/switch. `/health`, model listing and selection require the same key.
Switches wait for the previous reply; unknown/retired IDs never start a worker.
The router stops only its exact owned systemd units, never unrelated GPU jobs,
DSH, the gateway, browsers or terminals. GPU-resource release tracks owned PIDs;
desktop programs can appear in NVIDIA's compute-app query and are preserved.

## Native apps and desktop shortcuts

Desktop and application-menu entries are installed for:

- **LLM HyperQwen vLLM** and **LLM SGLang**: start their selected dense profile.
- **LLM Strata**: select Flash-Next or DeepSeek, then open Strata's own Chat/Monitor
  web app at `http://127.0.0.1:10000/`.
- **LLM Maya**: select GLM or DeepSeek, then open Maya's own Chat/Monitor web app
  at the same worker address.
- **DeepSeek Harness (DSH)**: reopen the separately running DSH web app using its
  private startup URL. It lists four engine providers and all six profiles.

Strata/Maya selection happens in the launcher terminal; closing it leaves the
managed worker running. Their web apps may request the existing local API key
on first use and keep it in that browser. Native settings edits affect the
private generated run config, rather than promote a new qualified setting.
Keep maintained context/settings in the registry and canonical source config.
The web page on port 10000 follows whichever single worker is currently running.
Official project icons and their sources are recorded in
[artwork attribution](../assets/icons/README.md). HyperQwen uses vLLM's mark.

PATH commands: `llm-hyperqwen`, `llm-sglang`, `llm-strata`, `llm-maya`, and `dsh`.
The engine commands accept `--model <id>`; Strata/Maya accept `--web`. Running
`dsh` alone opens its current UI; arguments invoke the pinned DSH CLI.
DSH defaults to HyperQwen and stores sessions privately under `data/dsh/`.
Refresh providers with `python3 dsh/configure.py`; saved selections are preserved.

## Install and service management

DSH uses the AMD reference's pinned `@deepseek-ai/dsh@0.2.1-rc.2` and its lockfile.
Node.js 22.22.1 is used here. Existing qualified engines and weights stay in place.
After installing the tracked DSH package/lockfile into `runtimes/deepseek-harness/`,
run `npm ci --ignore-scripts`, review native install hooks, then rebuild
`node-pty`, `koffi` and `@deepseek-ai/dsh-subprocess-local`. Run:

```bash
python3 dsh/configure.py
python3 network/install.py
systemctl --user status nvidia-model-router nvidia-dsh
python3 -m unittest discover -s tests -v
```

The installer refuses unrelated command/desktop/service replacements. It creates
enabled user services and explicit Tailscale/loopback listeners. User lingering
allows services to survive logout. It neither exposes wildcard/public listeners
nor changes Tailscale ACLs, SSH access, firewall rules or another computer.
The native worker UIs and DSH UI remain local; the authenticated model API is
available across Tailscale. Existing Tailscale network ACLs still apply.

Dense and DeepSeek workers retain the 30 GiB soft / 36 GiB hard RAM and 1 GiB swap
bounds. Flash-Next and GLM's already-selected automatic RAM arenas need a separate
44/48 GiB production limit. GLM additionally uses the documented
`MAYA_GLM_RAM_GB=32` total expert-RAM cap, since its automatic allocator reads host
RAM rather than the worker cgroup budget. Applying the dense 36 GiB cap to those arenas was
rejected during deployment. MoE workers monitor host available RAM and GPU
temperatures every two seconds and stop after three samples below 8 GiB available
or at/above 82 C. GPU reserves, both-GPU selection, dense checkpoint/placement
preflights and numerical engine settings remain in force. Qwen's tool-call
parsers are enabled for DSH; prior speed measurements remain dated evidence.

The router adopts an owned running worker after restart. It leaves worker units
running when the router/DSH restarts. An unmanaged listener on worker port 10000
blocks new loading rather than being killed. Optional `data/GPU-LOCK` reserves
the GPUs against new launches. Runtime settings, keys, logs, session data and live
addresses are ignored; only sanitized source, reports and artwork are exported.
