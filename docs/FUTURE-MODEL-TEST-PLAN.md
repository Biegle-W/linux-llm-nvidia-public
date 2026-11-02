# Future model short harness test plan

Standing default, November 2, 2026. Apply to each newly requested model/quant/engine profile. This plan does not itself launch or replay existing models.

## Sequence

1. Record model, quantization, engine/version, selected configuration, hardware, checkpoint size/location and intended context. Verify current-boot P2P proof, resource guards, telemetry and available capacity. Inspect active requests, workers, reservations and locks; defer to independent work. Preserve configuration preimages before candidate changes.
2. Select one profile through the normal guarded router/API path. Record worker ownership and invocation, loading/readiness outcome, advertised context and native KV backing when available. Loading is excluded from inference speed measurements.
3. Run one short real tool-call round trip through the supported client harness (DSH for maintained profiles). Use a harmless local read fixture with a known marker. Require a parsed tool name and valid arguments, actual harness execution, the matching tool-call ID/result, and a correct short follow-up that uses the result. Save request-scoped evidence; a model merely printing a tool call is insufficient. Exercise streaming tool arguments where that is the normal supported path.
4. During the first tool-call generation, capture input/output token counts including tool arguments, cached/reused tokens, native prefill/decode timings and client timestamps. Report prefill tok/s, time to first generated token and decode tok/s. Account for parser/SSE buffering. Exclude loading and the follow-up answer. Do not derive token rates from chunk counts or total round-trip duration. If instrumentation is incomplete, mark the metric unavailable and repair measurement before claiming a benchmark.
5. Monitor RAM, per-GPU VRAM, swap occupancy/I/O, pressure, temperature and telemetry throughout the short run. Preserve every enforced guard. Record sampled usage separately from guard thresholds, including sampling interval and coverage. A short run is not sustained-swap or full-context qualification.
6. Unload only the worker owned by this test through the normal lifecycle. Confirm the matching invocation stopped and GPU allocations were released against baseline; record unload duration/result. Preserve router/API/client services and unrelated work. If ownership changes or release cannot be established, stop the sequence and investigate without force cleanup.
7. Only after unload/release passes, select the next requested profile and repeat. Log the source/destination profile and switch outcome. After the last profile, leave the test-owned worker unloaded; do not preload a fallback.

## Acceptance and failures

Pass requires guarded readiness, a valid actual tool/result/follow-up round trip, no guard violation, and verified owned unload/resource release. Record tool success, load/unload outcomes, total tool duration and measurement method independently of speed metrics. Retain failed attempts and exact triggers/thresholds; a guard-stopped run is not a qualified operating benchmark. Do not silently retry for a better number. Missing timing does not invalidate a proven tool round trip but leaves benchmark reporting incomplete.

Default scope is one short observation per requested profile. Full-context retrieval, sustained stress, repeated reloads, repeated speed suites and timed idle-unload validation require a separate request. Configured context must not be described as tested full-window capacity.

## Required report

Use the categories and definitions in [benchmark reporting conventions](BENCHMARK-REPORTING.md). Preserve historical benchmark attribution and identify the date, hardware, exact tested token lengths, cache reuse and single-observation status.

| Model / quant | Engine | Prefill (tok/s) | Time to first token (s) | Decode (tok/s) | Context limit (tokens) | Storage size (GB) | Storage location |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |

Add this companion table for every reported profile in chat, saved reports and machine-readable evidence:

| Model / quant | Engine | RAM guards | VRAM guards | Swap guards |
| --- | --- | --- | --- | --- |

- RAM: effective worker soft/high and hard/max GiB, host available-memory reserve, loading/inference PSI thresholds and consecutive-sample stop rules; explicitly label unlimited limits.
- VRAM: each GPU's active free-memory floor, model-specific exceptions, sample/hysteresis rules, and separate startup admission requirements. Distinguish native cache allocation reserves from enforced free-memory stop floors.
- Swap: occupancy cap (including unlimited), write and combined read+write MiB/s limits, averaging window, violation rule and phase-specific enforcement.

Read effective deployed policy and kernel cgroup values used by that run. Never substitute defaults for profile exceptions. Report observed RAM/swap peaks and VRAM minima separately, or explicitly say not measured; sampled extrema are not guaranteed absolute peaks. Historical rows retain the guards applied at measurement time. Do not rerun models merely to add guard documentation.

Keep raw evidence and selected-setting records, update maintained documentation, and review public exports for private paths, credentials and session material before publishing.
