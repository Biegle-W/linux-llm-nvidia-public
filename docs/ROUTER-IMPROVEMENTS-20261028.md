# NVIDIA router admission and transport — October 28

The router now separates authenticated HTTP handling, loopback backend transport
and worker lifecycle management. It retains one service, the same port and model
IDs, and all desktop/native UI launch paths. No extra gateway process or listening
port is required. The design adopts the AMD reference's separation of transport
from lifecycle and its explicit request-state reporting.

## Request admission

`network/request_admission.py` replaces the unfair execution mutex with a bounded
FIFO gate: one active operation and up to eight waiting operations. Ordering is
by entry into the admission queue after HTTP parsing, not by TCP arrival time.
An earlier model switch cannot be overtaken by later same-model API requests.
Explicit selection shares the gate; explicit unload still refuses a busy system
if it cannot enter within one second. Automatic idle teardown uses nonblocking
admission and cannot overtake queued requests.

Full queues produce `router_queue_full`: HTTP 429 with `Retry-After: 5` for ordinary
requests. Streaming headers are sent before admission/loading, so streamed errors
carry the status and code in an SSE error event followed by `[DONE]`. Clients must
inspect those events even when the HTTP status is 200. The existing one-hour
request wait budget remains; expired waiters return `request_queue_timeout` (504).
Detected streaming disconnects and failed progress checks remove their queue
entries. This is a bound on lifecycle admission, not a limit on every HTTP socket.

Authenticated `/health` adds `inflight`, `queued`, `max_inflight`, `max_queued`,
`admission_active`, `same_model_concurrency` and `idle_timeout_seconds`. Existing
fields and model catalog/selection/unload APIs remain available. Inflight counts
an admitted request or selection, including its loading work; direct native UI
activity is still handled by backend telemetry and native guards.

`network/backend_proxy.py` handles only local backend transport. It translates
model aliases and preserves nonstream backend response status/content type,
including plain-text errors. Streamed backend errors retain a bounded diagnostic
and original status. Backend error text redacts the local key. Incoming cookies,
client headers and query strings are not forwarded. The backend still receives
its required local credential.

## Same-model concurrency decision: keep disabled

The source/configuration audit found no currently qualified multi-request profile:

| Backend | Maintained execution limit |
| --- | --- |
| HyperQwen/vLLM | `--max-num-seqs 1` |
| SGLang | `max_running_requests=1`, `max_mamba_cache_size=1`, decode graph batch limit 1 |
| Strata and Maya, all four profiles | Normal launcher sets `parallel=1` |

Allowing several HTTP requests into these backends would add another queue, not
establish safe parallel execution. Increasing those engine limits would alter
qualified memory/state capacity. No such change was made. The router advertises
`max_inflight=1` and `same_model_concurrency=false`; there is no automatic capacity
promotion. This audit does not prove that a separately tuned concurrent profile
could never work. Such a candidate would need its own near-window quality,
state-isolation, cancellation, VRAM/RAM/swap and sustained-load qualification.
No concurrent GPU experiment was run merely to rediscover explicit one-slot limits.

Native web clients retain their existing backend FIFO and native activity checks.
They do not enter the API admission queue. This change does not claim global FIFO
ordering between native UI clients and API clients.

## Preserved controls

The exact owned-service/invocation checks, GPU reservations, protected harnesses,
native busy/queued/loading/vision checks, guard-stop latches and backend-only viewer
cleanup remain. Engine launchers, profile registry and guard/runtime settings are
byte-identical to the pre-change versions. Dense reserve remains 512 MiB, host
swappiness 60, idle release 600 seconds, with existing per-profile RAM budgets,
host-memory/thermal and active swap/telemetry guards. Selected SGLang remains 32K.
The minimized non-focus-stealing launch path and DSH saved selections are unchanged.

## Validation and deployment

- 94 CPU regressions passed, zero failures/errors/skips. These include threaded
  admission/fairness, one-slot same-model bursts, overload, cancellation cleanup,
  backend error/key handling, switching/ownership, idle, native vision, minimized
  terminals, guards, staging, telemetry and pinned SGLang runtime checks.
- Deployment used an exclusively created temporary maintenance reservation,
  rechecked an idle/unloaded router, and restarted only the router. The owned
  reservation was released by exact-content comparison. DSH's PID and invocation
  remained unchanged; no existing worker or harness was stopped.
- Live authentication rejection, unknown-model rejection and six-model catalog
  passed. `/health` reports the new admission policy and 600-second idle setting.
- Two sequential normal SGLang requests, each capped at 32 output tokens, passed
  nonstream and SSE content/model-alias checks. The streaming path reached `[DONE]`.
  This is a transport smoke test, not a performance benchmark, context retest or
  concurrency qualification. SGLang was left ready for normal 600-second idle
  release; no fallback model was loaded.
- The first harness final-health assertion ran before asynchronous stream cleanup
  released admission. All request assertions had passed. A read-only follow-up
  verified cleanup; the harness now polls for that boundary. The two successful
  inference requests were not repeated. Original evidence is retained privately.

[Machine-readable summary](validation-results/20261028-router-improvements.json).
Private raw evidence remains outside the public export. Prior speed, 38K quality
and normal-reload capacity findings are preserved; no completed benchmark was rerun.
