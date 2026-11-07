# NVIDIA model router, Tailscale and DeepSeek Harness

## Retired IQ1_S weights deleted; IQ1_M table preserved — November5,2026

At the human's explicit request, removed the old IQ1_S checkpoint and its obsolete n-gram filename, reclaiming37.58GB exclusive storage. The active IQ1_M28.8GB table kept the same inode and full verified SHA256; only its hardlink count changed2to1. No model configuration or guard changed and no inference benchmark was repeated. Prior rollback-retention statements are superseded. [Removal receipt and preserved dependencies](../docs/IQ1S-WEIGHT-REMOVAL-20261105.md).

## Flash-Next IQ1_M replaces IQ1_S — November5,2026

Qualified `flash-next-iq1m-strata` replaces the IQ1_S llama.cpp entry in API/DSH and the Strata desktop selector, with both GPUs,128K allocation and existing MTP. Actual read/tool-result/exact follow-up, guards and owned unload passed;506 CPU regressions passed. The IQ3_XXS entry and global default remain. All RAM/VRAM/thermal/swap guards are preserved; IQ1_S weights were subsequently removed by explicit request; IQ1_M retains its28.8GB table. Idle API/hub were reloaded to load the previously changed RAM validator, and DSH selections migrated. No active jobs, reservations or pending transaction/publication remain; next action is normal use. [Benchmarks, guards and retirement](../docs/FLASH-IQ1M-STRATA-20261105.md).

## Unused Qwen GGUF target/drafter deleted — November 4, 2026

The unconfigured Qwen3.8-27B Q4_K_M target and its MTP-only GGUF drafter were deleted at the user's request: 19.450 GB of weights. All nine configured entries and every maintained checkpoint/runtime remain unchanged. No inference or regression suite was repeated; unchanged-catalog/checkpoint and API/DSH checks verify preservation. Historical results remain dated evidence. [Removal record](../docs/UNUSED-QWEN-GGUF-REMOVAL-20261104.md).

## Retired AWQ Bolt assets deleted — November 4, 2026

The user requested deletion of the retired AWQ setup. Its55.33 GB weights, dedicated vLLM environment, manifest, launch/supervision/offload code and AWQ-only tests are removed. Native IQ2 remains selected under compatibility ID`bolt-vllm`; all nine profiles, both DSH modes, defaults, guards and shared runtimes are preserved.423 remaining CPU tests passed;33 obsolete adapter tests were retired. Native runtime hashes/dependencies and API/DSH health passed; no model benchmark was repeated. Historical benchmark records and small private source/configuration preimages remain, but the old checkpoint/runtime are no longer installed. [Removal verification](../docs/BOLT-AWQ-REMOVAL-20261104.md).

## Current: native IQ2 Bolt replaces AWQ in API/DSH — November 4, 2026

Bolt now selects the official native IQ2 text model on pinned llama.cpp11909, both GPUs, 384 MiB fit targets and unchanged 163,840-token allocation. The historical `bolt-vllm` ID remains for compatibility; API metadata and both DSH display names now identify native IQ2/llama.cpp. Normal-router actual DSH read/result/exact follow-up and owned unload passed: 502.58 prefill tok/s, 12.870 s client TTFT and 68.05 decode tok/s. All nine entries remain, with unrelated routes/defaults and all guards preserved. 456 CPU tests passed; workers finish idle and updates stay paused. Older AWQ measurements and candidate-only status below are dated history. [Selected entry, guards and AWQ slowdown research](../docs/BOLT-IQ2-ENTRY-20261104.md).

## Native IQ2 Bolt tested on both GPUs — November 4, 2026

The isolated official native IQ2 Bolt candidate passed an actual DSH read/result/exact-follow-up and owned unload at163,840 context on pinned llama.cpp11909. The minimum tested passing fit margin384 MiB/card retains89.4% of weight-buffer bytes on the GPUs with2.18 GiB CPU-mapped weights:506.46 prefill tok/s,12.744 s client TTFT and67.49 decode tok/s, versus the retained same-day AWQ217.35 /29.320 /0.361. The256 MiB fit arm hit the unchanged256 MiB VRAM floor during prefill and is rejected;512 MiB also passed. These are short complete-configuration observations, not an equal-quality or sustained-speed claim.451 CPU checks passed. Both GPUs finish idle, no reservation remains and API/hub/DSH are healthy. All nine selected entries and defaults remain; IQ2 is a separate qualified candidate, not a replacement entry. [Results, guard/placement evidence and failed arms](../docs/BOLT-NATIVE-IQ2-20261104.md).

## Current: all nine restored with two-GiB headroom — November 4, 2026

The corrected boot passed early GPU unlock and current-boot host-staged transport. Linux sees 91.76984787 GiB usable RAM. All nine normal-router DSH read/result/exact-follow-up and owned-unload checks passed; all entries are enabled and workers finish idle. The six RAM-heavy profiles now use 87.76984787/89.76984787 GiB high/hard limits, leaving exactly 2 GiB outside the hard cap as requested. Dense profiles retain 32/36 GiB; the independent 2 GiB available-memory stop and all other guards remain. 446 CPU tests passed. Larger supported caches are selected; runtime pins, contexts and defaults are preserved, and daily updates remain paused. This supersedes earlier preparation/waiting and temporary 32 GB operational descriptions below; historical measurements retain their dates and hardware. [All nine benchmarks, exact guard tables and resource evidence](../docs/RAM96-RESTORATION-20261104.md).

## Larger RAM verified; restoration prepared, GPU checks awaiting firmware — November 4, 2026

Linux now sees 91.77 GiB usable RAM. Nine larger-RAM candidate definitions and cache configurations are prepared: dense 32/36 GiB worker caps, RAM-heavy 84/86 GiB, and a new 90 GiB minimum measured-capacity gate.445 CPU tests passed. Five paused profiles remain disabled; no GPU benchmark or restoration qualification has run. Secure Boot is enabled again, early GPU unlock health failed and its dependent current-boot transport proof is missing. The human chose preparation first and will correct Secure Boot/reboot later. No guard was bypassed; other policies, engine pins, contexts and defaults are preserved. API/hub/DSH remain healthy and GPU workers are idle. Earlier benchmark rows retain their measured 32/64 GB scope. [Prepared settings, forum/pinning research and continuation](../docs/RAM96-PREPARATION-20261104.md).

## Flash-Next IQ1_S entry enabled — November 4, 2026

`flash-next-iq1s-llamacpp` is now the fourth enabled API/DSH entry: the same verified Unsloth v3.1 IQ1_S checkpoint, llama.cpp11909, 12,288 context and lazy NVMe n-gram table. Normal-router actual DSH read/result/exact-follow-up and owned unload passed:88.79 prefill tok/s,66.292 s client TTFT and31.10 decode tok/s. RAM26/28 GiB, host2 GiB, GPU256 MiB/card, swap128/160 MiB/s over30 s,15% active full PSI, thermal82 C and all ownership/telemetry guards remain. All441 CPU checks passed. The five older profiles stay disabled, defaults are preserved and workers finish idle. Earlier isolated-candidate descriptions are dated history; this is the current operational state. [Entry and guard evidence](../docs/FLASH-IQ1S-ENTRY-20261104.md); [all current and historical entry benchmarks](../docs/ALL-ENTRY-BENCHMARKS-20261104.md).

## Worker RAM raised to 26/28 GiB; requested reruns passed — November 4, 2026

All eight profile definitions now use 26/28 GiB soft/hard worker limits. HyperQwen, SGLang and the isolated Flash-Next IQ1_S SSD-table candidate each passed one fresh actual DSH tool/result/exact-follow-up and owned unload; 438 CPU regressions passed. The other five profiles remain disabled. Host2 GiB, VRAM256 MiB/card, thermal82 C, swap/PSI/transport/ownership guards, contexts, weights and defaults remain unchanged. Flash-Next measured93.35 prefill tok/s,63.238 s client TTFT and 28.23 decode tok/s; sampled swap483 MiB and soft-limit reclaim persisted, so larger limits showed no speed improvement in this single run. All workers are stopped, GPUs1 MiB each, API/hub/DSH active and no reservation remains. This supersedes earlier24/26 GiB operational descriptions; historical results retain their original guards. [Results, comparison and guard tables](../docs/RAM26-28-RERUN-20261104.md).

## Current operation and DSH repair — November 3, 2026

DSH uses an explicit headless service mode; desktop launches retain their required visible monitor. The API and private hub remain independent. The current host has **temporary 32 GB RAM**; only **HyperQwen 86,016** and **SGLang 57,344** are enabled. Both retain 24/26 GiB worker budgets, the 2 GiB host reserve, **256 MiB per-GPU free-VRAM floor**, swappiness 60 and idle 600 seconds. Unlock and current-boot host-staged transport are verified; the native-output buffering repair remains deployed. RAM/offload profiles remain disabled until explicit hardware confirmation, measured capacity and guarded requalification. Daily updates remain paused.

See [the current repair and remaining work](../docs/DSH-STARTUP-REPAIR-20261103.md). Older dated status paragraphs and benchmark numbers retain their historical hardware/guard scope; they do not override this current state. Standing instructions remain applicable. No new model benchmark was run.

## NVIDIA API-only server — November 1, 2026

The authenticated client API remains on port **10100** with the existing key. It forwards to a separate private model hub on **127.0.0.1:10101**; guarded model backends retain their private port and launch paths. The hub owns model selection, FIFO admission and the 600-second idle policy. Restarting the API does not restart the hub or its model workers.

API services and API-launched backends are headless. DSH is a separate client under **NVIDIA server**; optional desktop/client installation uses `network/install.py --with-clients`. Plain HyperQwen and explicit Responses/function-tool support are retained. RAM, VRAM, swap, temperature, P2P and telemetry guards remain enforced.

All **130 focused API/transport/launch-policy checks passed**, including chat/Responses streams, tool forwarding, disconnections and authentication. The full Torch-enabled CPU run passed **415/417**; two unchanged baseline checks still fail (updater catalog coverage and an obsolete Super swap-limit expectation). Live authentication/catalog/context checks passed and the active worker invocation was preserved.

## Latest: Unsloth and Comfy desktop installation — October 30

Official Unsloth Desktop 0.1.913-beta and Comfy Desktop 1.1.8 stable are installed per-user with **Unsloth** and **ComfyUI** Desktop/menu shortcuts. Unsloth's isolated backend setup completed all 17 stages; Python 3.13.17, backend 2026.10.11 and PyTorch 2.13.0+cu130 see both CUDA GPUs. AppImage/native-library/shortcut checks pass. Comfy's installed launcher now uses its documented per-app `--no-sandbox` compatibility option and passed an offscreen 15-second startup check; system-wide sandbox settings are unchanged. The initial sandboxed failure is retained as historical evidence. Existing LLM environments/settings are preserved; no model, training or generation job started. Comfy's ordinary first-run choices remain. See [installation status](../docs/UNSLOTH-COMFY-DESKTOP-20261030.md) and [verification](../docs/validation-results/20261030-unsloth-comfy-desktop.json).

## Latest: official Strata desktop app linked to existing Q3 — October 30

The official Strata 0.2.8 Linux desktop app and its matching 0.1.54 CUDA engine are installed separately, with a new **Strata Official** Desktop/menu shortcut. Its real desktop host recognizes the existing Qwen3.8-Flash-Next IQ3_XXS at 32K with no missing files. Existing GGUF shards and prepared packs are reused; no model weights were downloaded, moved or copied. App state/components and the app-local profile are separate, the router credential was omitted, and the original selector, runtime pins, profiles and guards are preserved. Official binary/help and desktop-host inventory checks passed; the owned host stopped afterward. No model was loaded or benchmarked, and native GUI interaction/inference were not tested. See [installation and use](../docs/STRATA-OFFICIAL-APP-20261030.md) and [verification](../docs/validation-results/20261030-strata-official-app.json).

## Latest: actual headline content for OpenCat search — October 30

Headline/current-news queries now retrieve actual dated RSS story titles and descriptions rather than sparse generic news-site search snippets. General headlines use BBC World with a Google News fallback; topical current news uses Google News RSS search. Ordinary search remains free anonymous Mwmbl. All 259 CPU tests passed, followed by 22 targeted checks after final normalization. Real nonstreaming and Tailscale streaming responses included three exact fetched headlines with citations (2.845/3.192 seconds), without generic access refusals. Continue selecting `qwen27b-hyperqwen-search`. Worker/DSH, access configuration, model settings and resource guards are preserved. The user's exact original question and direct iPhone confirmation remain pending. See [repair and limits](../docs/OPENCAT-HEADLINES-20261030.md) and [verification](../docs/validation-results/20261030-opencat-headlines.json).

## Latest: OpenCat empty-tools search compatibility — October 30

The phone trace showed Responses requests with an empty tool list, so the existing entry did not search. A new opt-in `qwen27b-hyperqwen-search` catalog entry enables free web search on the server while reusing the same guarded HyperQwen worker. Refresh OpenCat's model list and select this ID; keep the existing connection and Responses settings. All 255 CPU tests and real empty-tools nonstreaming/streaming/Tailscale requests passed (1.719/1.810/2.613 seconds), with grounded answers and citations. Original model entries, profiles and resource guards are preserved. Temporary diagnostics were removed and the access configuration restored exactly. Phone confirmation after selecting the new entry remains pending. See [repair](../docs/OPENCAT-SEARCH-MODEL-20261030.md) and [verification](../docs/validation-results/20261030-opencat-search-model.json).

## Latest: free keyless Responses web search live-verified — October 30

The router uses Mwmbl's free anonymous API for `web_search`/`web_search_preview`, with typed streaming search events, untrusted snippets, clickable source links and URL citation annotations. All 250 CPU tests pass. Real nonstreaming, streaming and Tailscale streaming Responses passed in 1.981/1.506/2.176 seconds, including source-domain filtering and stable event ordering. No search key, signup or paid request was used. The documented anonymous allowance is 1,000 requests/month per IP at one request/second; unavailable/quota-limited searches return explicit errors. Model settings, guards and worker/DSH service invocations are preserved. Direct iPhone UI confirmation remains pending. See [implementation and limits](../docs/RESPONSES-WEB-SEARCH-20261030.md) and [verification](../docs/validation-results/20261030-responses-web-search.json).

## Latest: OpenCat Responses API exposed — October 30

The router now exposes native POST /v1/responses alongside Chat Completions, fixing OpenCat's OpenAIResponses “Unknown endpoint” failure. Typed streaming events, model aliases and upstream errors are preserved through the same authentication, queueing and worker guards. All 232 CPU tests passed; live HyperQwen Responses passed in streaming/non-streaming modes over loopback and Tailscale without restarting the model. Direct iPhone confirmation is pending. Optional protocol diagnostics remain default-off and exclude content and credentials. See [compatibility](../docs/OPENCAT-RESPONSES-20261030.md) and [verification](../docs/validation-results/20261030-opencat-responses.json).


## Latest: OpenAI-compatible request retries repaired — October 30

The router now reuses a verified running worker and waits for its existing cold load after a client disconnect, avoiding repeated reloads and the reported “Native worker state is unavailable” error. Ownership, active-work and resource guards remain intact. All 224 CPU tests passed. Live loopback streaming/non-streaming and Tailscale requests completed in under half a second without restarting the worker. Only the router was restarted; the loaded worker and DSH were preserved. See [repair](../docs/API-RELIABILITY-20261030.md) and [verification](../docs/validation-results/20261030-api-reliability.json).


The authenticated API listens on loopback and the configured Tailscale address at port **10100**, with the private model hub on **127.0.0.1:10101** and guarded workers on their private port. DSH is an optional separate loopback client at **3080**. Install it with `network/install.py --with-clients`; its explicit headless service mode needs no graphical session. The desktop shortcut still opens its monitor and private startup URL when the user activates the desktop. Daily engine updates are paused; resume only on an explicit request.

## Select a model and engine

Use the router base URL `http://127.0.0.1:10100/v1`, or from a tailnet device
`http://100.x.y.z:10100/v1` with this computer's actual Tailscale address. Both
require `Authorization: Bearer <local-key>`. The existing owner-only key is in
`data/local-api-key`; it is never published. `/v1/models` is the authoritative
catalog. Requesting its ID selects the model, quantization and engine together:

| Enabled API model ID | Engine | Context allocation |
| --- | --- | ---: |
| `qwen27b-hyperqwen` | HyperQwen/vLLM | 86,016 |
| `qwen27b-sglang` | SGLang | 57,344 |
| `flash-next-iq1s-llamacpp` | Flash-Next Unsloth v3.1 IQ1_S / llama.cpp + lazy SSD table | 12,288 |

The other five retained profiles are temporarily disabled and hidden from the picker pending the RAM upgrade and guarded qualification. `/v1/models` is authoritative for enabled choices. Context allocations are not new full-window qualification claims.

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

## Fair admission and backend transport

The API retains one active request/selection and now accepts up to eight waiting
operations in FIFO order. A waiting switch cannot be overtaken by later same-model
API calls. A full queue returns HTTP429 with Retry-After:5; streaming requests report
the error's status/code in SSE because their HTTP headers have already been sent.
`/health` exposes inflight/queued counts, capacity and the600-second idle policy.
Backend status and error messages are preserved, with local credentials redacted.

Same-model concurrency remains disabled after auditing actual engine limits:
HyperQwen max-num-seqs1, SGLang one running request/Mamba slot, native parallel1.
No qualified engine setting or guard was raised. Native UIs retain their own FIFO
and activity protection. See [the design, safety decision and validation](../docs/ROUTER-IMPROVEMENTS-20261028.md).

## Native apps and desktop shortcuts

Desktop shortcuts are installed for:

- **HyperQwen vLLM** and **SGLang**: start their selected dense profile.
- **Strata**: select Flash-Next or DeepSeek, then open Strata's own Chat/Monitor
  web app at `http://127.0.0.1:10000/`.
- **Maya**: select GLM or DeepSeek, then open Maya's own Chat/Monitor web app
  at the same worker address.
- **DeepSeek Harness (DSH)**: reopen the separately running DSH web app using its
  private startup URL. It lists the two enabled profiles under NVIDIA server.

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


## Latest: automatic engine switch closes only its backend — October 28

Normal model/engine selection drains an active API reply, stops the previous
recognized guarded worker, verifies resources released and starts the new one.
Backend consoles now follow the worker invocation and close on stop/switch;
completed Desktop selection launchers no longer remain waiting for Enter.
Only the registered backend viewer is signaled after path/mode/unit validation.
Router, DSH, harness/review consoles and unrelated processes remain. Protected
GPU-LOCK owners block selection; their reservations are never removed by switching.

A real SGLang 32K→HyperQwen 56,320 switch completed a 512-token active stream first,
closed old worker/viewer, opened the new backend console and passed API JSON.
Router/DSH invocations stayed unchanged. Normal unload closed the replacement
backend/viewer; final router idle, DSH active, no GPU-LOCK or coordinator. 53 engine/ownership
CPU regressions cover native busy/loading/vision, unknown state, ownership changes,
viewer PID reuse and protected harnesses. No new MoE loads or benchmarks.
Keep 512 MiB reserve,swappiness 60, 600s idle and all other guards; SGLang remains 32K.
See [engine switching verification](../docs/ENGINE-SWITCHING-20261028.md). Next action: follow the next user task;
do not repeat completed GPU qualification or restore a fallback automatically.


## Latest: all project terminals start minimized — October 28

The user requires engines, router, DSH/harnesses, selectors and test tasks to remain
visible in the taskbar but start minimized without taking focus. The shared
launcher now uses a SHA256-pinned project-local XTerm runtime with native-iconic
startup. There is no focus-then-minimize race or global desktop focus-policy change.
System packages and inference environments were not modified. Setup is reproduced
with scripts/install_visible_terminal_runtime.py and config/terminal-runtime.json.

All four engine shortcuts use Terminal=false and the shared minimized selector,
avoiding a foreground default-terminal window. Successful selectors close after
readiness; failures remain available for inspection. Native engine readiness prints
a web URL instead of activating a browser. Explicit UI opening remains user-controlled.
Backend-only auto-close and protected router/harness ownership rules remain.

A live window-manager audit verified initial Iconic,hidden and not-active state for
the test harness, router, DSH and actual SGLang backend. The real SGLang Desktop
shortcut passed API JSON; router/DSH invocations stayed unchanged during selection.
The DSH service was not restarted when its viewer was migrated. Router was activated
once while idle to load the launcher change. 53 engine/ownership regressions passed;
no benchmark, driver, precision, budget or context change. Final router idle, DSH active,
no GPU-LOCK. Dense 512 MiB, swappiness 60, 600s idle and other guards remain unchanged.
See [switching and minimized-window evidence](../docs/ENGINE-SWITCHING-20261028.md).
