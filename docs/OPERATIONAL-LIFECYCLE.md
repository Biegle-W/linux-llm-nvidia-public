# Inference lifecycle controls

Deployment checkpoint, October 27: guarded 600-second idle release and bounded
private lifecycle logging are enabled; both native adapters are applied with
hash-verified preimages. Manual candidate staging is available without activation.
All six normal launch paths passed JSON, supported images, context metadata and
actual RAM/swap readbacks. Actual GLM/dense 600-second expiry and normal reload passed; Strata passed an
isolated 30-second idle/reload proof while production remains 600. See the
documented intentional-shutdown false-latch fix in CURRENT-STATE.md. Context rollout
is partial: four qualified upgrades deployed; Maya sustained-swap qualification
remains unresolved. See CURRENT-STATE.md.

## Ten-minute idle release

The deployed private router setting is `idle_timeout_s: 600`. Dense engines use
the router's request/switch lock, an exclusive GPU reservation and a final direct
request-gauge check. Unknown backend state defers unload. Native Maya and Strata
use their existing request FIFO, with the narrow `native_idle_policy.py` adapter
adding a matching GPU reservation around teardown. Native busy/loading state and
router activity both defer expiry. Encoder loading and active image computation
are distinguished, and both defer switching; active encoding uses the swap guard. Catalog and health polling do not reset it. Manual unload also refuses native
loading, queued work and active image computation; unknown state preserves the
worker.

The adapter is hash-reviewed and preserves a before/after source snapshot.
It also stops Maya's lazy CPU vision process before releasing its text engine;
the encoder can start again for the next image. Only matching reservation owners
remove locks. Router, DSH, other programs and benchmark reservations are preserved.
CPU tests cover boundary timing, request races, FIFO behavior, missing telemetry,
vision teardown order and ownership. Actual GLM idle expiry and fresh-image reload passed. Strata passed isolated
short-timeout expiry and fresh-image reload; its production timeout stays 600.
No measured power saving is claimed.

## Private lifecycle telemetry

The deployed private flag is `lifecycle_telemetry: true`. Normal guarded dense
and MoE supervisors record start, loading/idle/inference samples and stop. A
background collector avoids putting optional sensor queries in the safety loop.
Records include GPU temperatures, clocks, utilization, memory, power, fan duty,
P-state and an optional raw limiter mask; host RAM/swap, CPU frequency range,
available board temperature/fan/power sensors and CPU throttle counters. Owned
cgroup memory limits/events and block-I/O counters permit worker write attribution
through loading and unload; they are distinct from system-wide device totals.
Unavailable readings remain null/absent, and sensor errors are recorded.

Logs stay under ignored `data/telemetry/<profile>/`, mode 600. Each profile keeps
one 10 MiB log plus two rotated files. This bounded logging does not change GPU
clocks, fan settings, power limits or thermal guards. A raw limiter mask alone
does not establish a performance cause. Swap monitoring is independently required;
see INFERENCE-SWAP-POLICY.md. Normal-launch sensor coverage is verified for all six profiles: two GPUs, six
hwmon devices and owned cgroup counters in owner-only logs. Automatic unload/reload evidence is complete with the shutdown-fix qualification
described in CURRENT-STATE.md.

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

Intentional SIGTERM now ends supervisor sampling before the backend disappears.
This prevents a false missing-telemetry safety latch on ordinary shutdown.
Unexpected telemetry loss remains fail closed; four regression cases and 74 CPU
checks pass. Dense 600-second expiry was measured before this fix; subsequent
real normal stop and automatic API reload validated the corrected shutdown path.

## SGLang idle evidence clarification — October 28

The current router still uses idle_timeout_s=600, checks native request gauges
under the switch lock and refuses to unload busy/loading/reserved workers.
Health/catalog polling does not refresh the deadline. Saved idle-unloaded events
verify automatic 600-second expiry for HyperQwen; they do not establish a timed
expiry for the newly deployed heterogeneous SGLang fork.

For that SGLang invocation, the last request was around 01:07:02 and owned phase
telemetry remained idle through 01:16:51. The context-study coordinator then
explicitly unloaded it after about 9 minutes 49 seconds, before the 600-second deadline.
The study's own workers were also explicitly stopped. Therefore their GPU release
must not be described as proof of automatic SGLang idle expiry. The rule is enabled
and idle detection was observed; a full 600-second automatic-expiry observation for
the new SGLang runtime remains unverified. The router is currently idle after
explicit study cleanup. No new GPU load or timed idle test was launched for this
read-only status check.
