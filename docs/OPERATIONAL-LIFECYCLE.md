# Inference lifecycle controls

Implementation checkpoint, October 27: the swap policy is applied to subsequent
guarded launches. Idle unload and lifecycle logging are implemented and CPU-tested,
but their private access flags remain disabled until the context rollout finishes.
The native adapter has not yet been applied. See CURRENT-STATE.md for live status.

## Ten-minute idle release

The intended private router setting is `idle_timeout_s: 600`. Dense engines use
the router's request/switch lock, an exclusive GPU reservation and a final direct
request-gauge check. Unknown backend state defers unload. Native Maya and Strata
use their existing request FIFO, with the narrow `native_idle_policy.py` adapter
adding a matching GPU reservation around teardown. Native busy/loading state and
router activity both defer expiry. Catalog and health polling do not reset it.

The adapter is hash-reviewed and preserves a before/after source snapshot.
It also stops Maya's lazy CPU vision process before releasing its text engine;
the encoder can start again for the next image. Only matching reservation owners
remove locks. Router, DSH, other programs and benchmark reservations are preserved.
CPU tests cover boundary timing, request races, FIFO behavior, missing telemetry,
vision teardown order and ownership. Actual idle expiry/reload remains pending.
No measured power saving is claimed.

## Private lifecycle telemetry

The intended private flag is `lifecycle_telemetry: true`. Normal guarded dense
and MoE supervisors record start, loading/idle/inference samples and stop. A
background collector avoids putting optional sensor queries in the safety loop.
Records include GPU temperatures, clocks, utilization, memory, power, fan duty,
P-state and an optional raw limiter mask; host RAM/swap, CPU frequency range,
available board temperature/fan/power sensors and CPU throttle counters.
Unavailable readings remain null/absent, and sensor errors are recorded.

Logs stay under ignored `data/telemetry/<profile>/`, mode 600. Each profile keeps
one 10 MiB log plus two rotated files. This bounded logging does not change GPU
clocks, fan settings, power limits or thermal guards. A raw limiter mask alone
does not establish a performance cause. Swap monitoring is independently required;
see INFERENCE-SWAP-POLICY.md. Hardware coverage and normal-launch lifecycle
verification remain pending at this checkpoint.

## Manual candidate staging

`scripts/stage_engine_candidate.py` provides two explicit operations:

```sh
python3 scripts/stage_engine_candidate.py stage --source <local-source-repo> \
  --revision <reviewed-full-commit> --profile <maintained-profile-id> \
  --name <unique-candidate-name> --fixture <saved-code-request.json> \
  --fixture <saved-prose-request.json>
python3 scripts/stage_engine_candidate.py evaluate data/engine-candidates/<name> \
  --baseline <evidence-folder/baseline.json> --candidate <evidence-folder/candidate.json>
```

Staging writes an immutable-name source snapshot, exact commit/archive hash,
saved fixture hashes and the current profile/catalog snapshot into private data.
It excludes uncommitted source edits. It rejects escaping archive paths/links and
does not copy models, replace runtimes, install packages or activate anything.
Build into a separate candidate environment manually. Preserve patch hashes and
build commands alongside the manifest; use a fresh owned guarded worker and GPU
reservation for evaluation. Never label a production-runtime run as a candidate.

The evaluator requires raw evidence paths/hashes and matched profile, hardware,
model/quant, fixture bytes, actual input counts and output length. Each side needs
at least three requests and 128 output tokens, positive timings, JSON/arithmetic,
near-window retrieval at 85% or more, image qualification when enabled, and owned
RAM/host/GPU/thermal/active-swap guard evidence with no guard stops. Context may
not shrink, prefill/decode may not decline and TTFT may not rise. Missing proof
fails closed. Field names are defined in `evidence()` and the CPU fixture tests.

A passing report is a manual-review recommendation. Review raw records and build
provenance, preserve old settings, prepare a deployment diff and verify rollback
before promotion. Evidence declarations are not independent hardware attestation.
There is no automatic activation, recurring update job or new model coverage.
The current 2.2K/128 benchmark protocol remains unchanged; portable code/prose
fixtures must be separately named and their actual tokenizer counts recorded.
