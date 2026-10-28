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
| `qwen27b-hyperqwen` | HyperQwen/vLLM | 56,320 |
| `qwen27b-sglang` | SGLang | 32,768 |
| `flash-next-strata` | Strata | 32,768 |
| `glm-maya` | Maya | 65,536 |
| `deepseek-strata` | Strata | 131,072 |
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

Desktop shortcuts are installed for:

- **HyperQwen vLLM** and **SGLang**: start their selected dense profile.
- **Strata**: select Flash-Next or DeepSeek, then open Strata's own Chat/Monitor
  web app at `http://127.0.0.1:10000/`.
- **Maya**: select GLM or DeepSeek, then open Maya's own Chat/Monitor web app
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

Application-menu entries are not installed. The installer removes only its own
older menu entries and preserves unrelated applications.

PATH commands: `llm-hyperqwen`, `llm-sglang`, `llm-strata`, `llm-maya`, and `dsh`.
The engine commands accept `--model <id>`; Strata/Maya accept `--web`. Running
`dsh` alone opens its current UI; arguments invoke the pinned DSH CLI.
DSH defaults to HyperQwen and stores sessions privately under `data/dsh/`.
Refresh providers with `python3 dsh/configure.py`; saved selections are preserved.

[Model storage policy](../docs/STORAGE-POLICY.md): GPU-resident Qwen checkpoints
load from SATA; the Strata/Maya SSD-streaming models remain on NVMe. Launchers
check the physical drive through the stable model aliases before starting.

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

Dense workers retain the 30 GiB soft / 36 GiB hard RAM and 1 GiB swap bounds.
Selected MoE worker budgets are recorded in `worker_memory_gib` in the registry,
with a maximum 48 GiB hard RAM, 1 GiB swap and at least 2 GiB soft/hard headroom.
The wrapper verifies exact limits; CLI, Desktop and API launches all use them.
GLM uses its selected expert-RAM cap and an on-demand CPU vision fallback.
DeepSeek's larger bounded caches retain their 32K/64K contexts and full expert
counts. Host available RAM below 8 GiB or GPU temperature at/above 82 C for three
two-second samples stops the owned worker. GPU reserves, storage and numerical
checks remain. [Measurements and settings](../docs/MOE-OPTIMIZATION-20261027.md).

The router adopts an owned running worker after restart. It leaves worker units
running when the router/DSH restarts. An unmanaged listener on worker port 10000
blocks new loading rather than being killed. Optional `data/GPU-LOCK` reserves
the GPUs against new launches. Runtime settings, keys, logs, session data and live
addresses are ignored; only sanitized source, reports and artwork are exported.

Ten-minute guarded idle release and bounded private lifecycle telemetry are now
enabled. Actual idle/reload verification passed with the shutdown-fix qualification in CURRENT-STATE.md. Host
swappiness remains 60. Maya DeepSeek 32K has unresolved sustained-swap qualification;
its active guard remains enabled.

## Current routing behavior — October 28

The request model ID selects a complete maintained model/quantization/engine
profile. DSH registers four NVIDIA engine providers, each pointing to the same
router URL; selecting a provider and one of its models changes the ID sent on the
next Chat Completions request. The router then waits for existing work, unloads
its owned prior worker and starts the requested profile in its guarded service
with a visible console. Repeated requests for the same loaded profile reuse it.
There is one active inference worker; this is serialized switching, not concurrent
multi-engine serving or automatic selection of the fastest engine.

`qwen27b-sglang` now selects the deployed pinned heterogeneous TP2/MTP3 fork,
with decoder MLP W4A8, BF16 state/KV and a 32K window. The existing DSH
`nvidia-sglang` provider and SGLang shortcut use the same ID; no new provider or
model alias was added. Runtime/patch/version pins and startup verification are in
[the deployment report](../docs/SGLANG-DEPLOYMENT-20261028.md). The normal dense
free-VRAM guard is 512 MiB and swappiness remains 60.

Chat Completions for this profile default to `enable_thinking=false` when omitted;
explicit `chat_template_kwargs` overrides remain available. Streaming, parsed
tool calls, near-window retrieval and a normal unload/reload were verified through
the router. DSH's saved default provider remains a UI choice, not an instruction
to preload HyperQwen. Isolated tests still finish idle; the requested SGLang
deployment was left selected and uses ordinary ten-minute idle release.

Desktop display names and filenames now omit the LLM prefix: HyperQwen vLLM,
SGLang, Strata and Maya. CLI commands retain their existing llm-* names. Re-running
the installer migrates only this project's managed old Desktop entries, preserving
unrelated shortcuts and avoiding application-menu entries.

## Shared policy for every maintained engine/model — October 28

../config/inference-policy.json is authoritative: automatic 600-second idle unload,
required visible terminals/lifecycle telemetry and proportional context/speed
tradeoffs requiring quality/resource qualification. Applies to all six profiles
across HyperQwen-vLLM, SGLang, Strata and Maya. Active/queued/loading/vision work,
reservations and unknown state defer teardown; health/model listing does not
refresh the timer. Next request reloads; do not preload a fallback model.

Router/native wrappers/lifecycle logger read the shared file. The installer now
preserves 600s on reinstall. Normal dense CLI enters router ownership; its marked
internal worker path avoids recursion while retaining original preflight/guards.
No contexts or model/cache settings changed. Preserve 512 MiB dense reserve,
swappiness 60, all RAM/thermal/swap guards and the reduced-RAM MoE caveats.
See ../docs/ALL-ENGINE-POLICY-20261028.md for coverage and actual idle/reload proof.


October 28 [38K qualification](../docs/SGLANG-38K-QUALIFICATION-20261028.md):
normal long-input retrieval and automatic reload succeeded, but the reload
allocated only 37,501 KV tokens per pool against 38,912 advertised. Full-capacity
verification rejected promotion. The maintained router/harness and DSH web/headless
profiles are restored to 32,768 with saved defaults preserved; final router is idle.
512 MiB reserve, swappiness 60 and all other guards remain.
