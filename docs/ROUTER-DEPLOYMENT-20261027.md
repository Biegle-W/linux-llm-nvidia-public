# NVIDIA router and native-app deployment — October 27, 2026

Deployed an authenticated catalog router and DeepSeek Harness, following the
read-only AMD reference at `381085f68984e5f6c5430e7a7625169435532cb2`. No AMD
repository, runtime or machine configuration was modified.

## Delivered behavior

- Six maintained model/quant/engine profiles appear in OpenAI `/v1/models`.
  A Chat Completions request selects and starts the profile by its ID.
- Router API: explicit loopback and this host's Tailscale IPv4, port 10100.
  Both require the existing local API key. Worker port 10000 stays loopback-only.
- Independent enabled user services for the router and DSH; lingering was already
  enabled. Restarting either service leaves managed workers independent.
- DSH 0.2.1-rc.2, with the AMD reference lockfile, runs under Node.js 22.22.1.
  Four NVIDIA engine providers expose all six profiles. The default is HyperQwen.
  Web and headless settings reference the key through an environment variable.
- Five Desktop/menu entries have official artwork: HyperQwen/vLLM, SGLang,
  Strata, Maya and DSH. HyperQwen uses vLLM's official mark because the fork has
  no separate logo. [Artwork sources](../assets/icons/README.md).
- Strata and Maya shortcuts select a model in their launcher, wait for readiness,
  and open their own native Chat/Monitor page. DSH stays a separate web app.
- Exact owned-unit switching, serialized requests, native-web busy-status checks,
  and optional GPU reservations protect ongoing inference. No blanket process
  killing is used. Desktop GPU contexts are preserved.

[Connection, model IDs, installation and commands](../network/README.md) are the
operational handoff. Live addresses, API keys and browser startup tokens stay
outside tracked documentation.

## Verification

| Check | Result |
| --- | --- |
| Loopback and Tailscale host-self authenticated catalog | Six expected IDs |
| Missing/wrong API key on both listeners | HTTP 401 |
| HyperQwen streamed JSON via model router | Passed |
| SGLang streamed JSON via model router | Passed |
| Strata Flash-Next streamed JSON via model router | Passed |
| Maya GLM streamed JSON via model router | Passed |
| Strata DeepSeek 64K profile streamed JSON via model router | Passed |
| Maya DeepSeek streamed JSON via model router | Passed |
| DSH file-tool task through HyperQwen/router | Returned the file's verification marker; two model steps |
| Native Strata HTML from managed worker | HTTP 200, title `Strata` |
| Native Maya HTML from managed worker | HTTP 200, title `Project Maya` |
| CPU router tests | 13 passed |
| Desktop entries | Five executable entries; valid icon files; native-web flags on Strata/Maya |
| Default restoration | HyperQwen selected and serving after checks |

CPU tests cover authentication, framing, unknown models, response aliases,
streamed function arguments, unsupported endpoints, serialized switching,
failed-load lock release, preservation of desktop GPU contexts, native reply
observation, reservation-protected unload and refusal to stop an unrecognized
unit. Integration requests used a short JSON fixture; their elapsed times include
loading and are not speed benchmarks. Completed pre-deployment benchmarks were
not repeated or relabeled.

An independent device test could not be run because the chosen tailnet peer did
not accept this host's SSH credentials. Network checks therefore establish
host-self access over the Tailscale address, rather than a separately verified
remote client. The listener is bound to the real Tailscale interface; existing
Tailscale ACLs still govern peer access. No ACL, firewall, SSH or Funnel changes
were made.

## Resolved deployment issues and retained limits

The first HTTP streaming adapter collided with the handler's socket attribute;
renaming that adapter fixed actual stream forwarding. An early check also raced
a service restart; no model test had run in that attempt. NVIDIA's compute-app
query includes desktop GPU contexts, so resource release now tracks the actual
owned worker cgroup PIDs rather than requiring every desktop context to disappear.

The initial generic 36 GiB MoE limit could not hold Flash-Next's existing
39.97 GiB expert arena. GLM's automatic RAM allocator reads host MemAvailable,
rather than its cgroup budget, and stalled against the generic limit. Flash-Next
and GLM now have a 44 GiB soft / 48 GiB hard production budget. GLM additionally
sets **`MAYA_GLM_RAM_GB=32`** in its single canonical config to bound the total
expert RAM tier. This changes cache residency, with all routed experts still
available through the existing MoE streaming path. Its prior automatic-RAM speed
results remain historical, not measured performance for the capped setting.
The former config is credential-free in private retirement batch
`linux-nvidia/2026-10-27-router-deployment`, commit `ac78657`.

Dense and DeepSeek workers keep 30/36 GiB RAM bounds. All managed workers retain a
1 GiB swap cap. MoE supervisors sample RAM and GPU temperature every two seconds,
stopping after three samples below 8 GiB available host RAM or at/above 82 C.
Owned stalled loading attempts were stopped during recovery; DSH and unrelated
applications were preserved. GPU reserves and dense placement/checkpoint guards
remain. Qwen's `qwen3_coder` tool-call parser is now enabled in both dense engines;
weight quantization, speculation, context, KV precision and numerical tuning are
unchanged. Historical numerical speed measurements predate this frontend addition.

Maya's direct foreground server defaults to a mock backend and port 8095; the
managed wrapper explicitly selects its real engine and port 10000. The successful
Maya checks used that corrected invocation. The first DSH legacy-settings import
attempt used its official provider before the custom profile was initialized;
the initialized profile passed the local tool task. Web/headless providers are
now written directly into their profile patch files.

The router observes native busy status before switching, but direct native clients
remain outside its request lock; a native request arriving between that status
check and shutdown is not an atomic reservation. Avoid starting a different model
while a native web conversation is answering. Router requests share one serialized
lock, so router-managed replies drain before switching. Native worker pages follow
the currently loaded single worker; launch the desired engine shortcut again to
return to it. Native pages may ask for the existing API key once in each browser.

## Evidence

Raw API events, deployment checks, DSH test session/projection, original config,
CPU test output, desktop/icon hashes and native page checks are retained privately
under `data/router-deployment-20261027/`. Generated keyed configs and worker state
are in `data/router/`; DSH sessions and its private startup URL remain in ignored
`data/dsh/` and `data/dsh-web.log`. Sanitized source, lockfiles, official artwork
and this report are exported to the matching public repository.

## Later shortcut preference

The user subsequently requested Desktop shortcuts only. The five managed
application-menu entries were removed; Desktop launchers and their official
artwork remain. The installer preserves this preference and removes only its
own older menu entries.
