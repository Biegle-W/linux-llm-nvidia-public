# OpenAI-compatible API reliability — October 30, 2026

Follow-up: [OpenCat Responses endpoint compatibility](OPENCAT-RESPONSES-20261030.md).

The reported error, `Native worker state is unavailable; active work was preserved.`, was traced to worker lifecycle reconciliation. The repaired router is deployed. Real chat-completion requests passed over loopback and the configured Tailscale address without restarting the loaded worker. [Numeric verification](validation-results/20261030-api-reliability.json).

## Failure mechanism

A guarded native worker could be running while the router's cached active model was empty or stale, for example after an external launch or an interrupted loading request. The router then entered its switch/reload path instead of reusing that worker. A direct diagnostic request completed in about 0.5 seconds, while the routed request unnecessarily restarted the same model and timed out at the diagnostic client's 15-second limit.

During early initialization of the affected Strata worker, the service is running but its native status endpoint is not yet available. A subsequent retry could reach the guarded unload check, which correctly refused to stop a worker whose active state was unknown. That refusal produced the reported error. The problem was taking the switching path for an already owned launch; removing the active-work protection would not be a safe repair.

## Repair

`network/worker_manager.py` now detects the verified current worker before deciding whether to switch. A ready worker for the requested model is reused. A verified existing cold load is awaited within the existing startup timeout, including when its previous client disconnected. A different requested model waits for the known launch before following the guarded switch path.

Native ownership detection requires the expected service unit, recognized launcher and matching nonempty invocation. While waiting, invocation/state changes, new reservations, safety latches and unit exits remain fail-closed. Unknown processes are preserved. An explicitly idle-unloaded native model still follows the existing guarded reload path. A disconnected client ends its wait without cancelling or restarting the owned load.

FIFO admission, request serialization, safety latches, worker memory budgets, model settings, runtime pins, contexts, swap/pressure/thermal/telemetry guards, credentials, allowed networks and 600-second idle behavior are unchanged. This is a router lifecycle repair; no model tuning or new speed benchmark was performed.

## Verification and deployment

The new regressions reproduce the original ready-worker and interrupted-load failures against the previous code. Tests cover reattachment, interrupted waits, changed ownership, unverified ready listeners, forged unit records, reservations before/during loading, safety latches, loading timeouts, switching to another model, and native idle unload. An existing updater-reservation fixture was updated to provide a verified identity rather than rely on a cached model name. All 224 CPU regressions passed, including 39 router tests and the qualification/updater coverage.

Deployment checked that there was no active or queued router request and no native compute before restarting only the router. The loaded worker and DSH retained their invocation identities. A new visible router monitor was opened; no backend worker was forcibly restarted for deployment.

| Live chat-completion check | Result | Elapsed seconds |
|---|---|---:|
| Loopback, non-streaming | HTTP200, correct answer, completed | 0.450 |
| Loopback, streaming | HTTP200, correct answer, completed | 0.167 |
| Tailnet, non-streaming | HTTP200, correct answer, completed | 0.166 |

All live calls used the public model alias and authenticated router endpoint. Streaming completed with the expected SSE completion marker. The loaded worker invocation stayed unchanged across every call. No credential, client conversation or actual Tailscale address is included in this export.

Cold-loading can still take longer than a client's configured timeout. Streaming retains the router's existing heartbeat behavior. The repair makes retries reuse or await the existing launch; it does not make model loading instantaneous. Live verification used the already loaded model; cold-load race behavior was verified by isolated CPU tests rather than forcing another GPU reload.
