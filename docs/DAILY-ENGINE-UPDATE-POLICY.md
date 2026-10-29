# Daily NVIDIA engine updater

## Schedule and scope

`nvidia-daily-engine-update.timer` runs every day at **03:00 host local time**. This host uses America/Toronto. `Persistent=false` skips missed nights and `RandomizedDelaySec=0` adds no delay. It is a local systemd job, with no model-powered scheduled agent.

The six selected model/engine profiles are covered exactly once:

| Component | Selected profile | Upstream | Retained context |
|---|---|---|---:|
| HyperQwen/vLLM | qwen27b-hyperqwen | syv-ai/HyperQwen default HEAD, with its pinned vLLM wheel and patch series | 56,320 |
| Heterogeneous SGLang | qwen27b-sglang | efschu/htsglang default HEAD, with the local CT/W4A8/MTP compatibility patch | 32,768 |
| Strata Qwen | flash-next-strata | Niko1221/Strata default HEAD | 32,768 |
| Maya GLM | glm-maya | mw00/project-maya default HEAD | 65,536 |
| Maya DeepSeek | deepseek-maya | mw00/project-maya default HEAD, retaining the bounded-file-cache patch | 32,768 |
| Strata DeepSeek | deepseek-strata | Niko1221/Strata separate DeepSeek native target | 131,072 |

No model weights, quantization, model coverage, drivers, kernel or firmware are automatically upgraded. Source revisions and initial production provenance references are in `config/daily-update-versions.json`. Runtime binary/environment paths and exact private receipts stay local. HyperQwen follows its own upstream's vLLM pin, not an arbitrary newest vLLM wheel; SGLang follows the selected fork, not a different engine architecture.

## Nightly procedure

1. Read upstream immutable commit IDs. A previously rejected revision is not retried until upstream changes. Discovery/network errors leave production untouched.
2. Wait until the router and native frontends have been idle for at least 20 minutes, with no queued/loading request or existing GPU reservation. Stop waiting for admission at 06:30. Take an exclusive reservation and recheck request state before stopping an idle owned worker. Unrelated processes/reservations are preserved.
3. Build each candidate in a separate project-local directory. Unlike the AMD reference, NVIDIA also waits for idle **before compilation**, avoiding build RAM pressure on an active inference job. Build processes use two jobs and a separate 6/8 GiB systemd memory budget; model workers retain their existing budgets.
4. Copy HyperQwen's environment before changing wheels, retain the selected SGLang dependencies and apply the exact compatibility patch, and compile native CUDA targets for both SM86 cards. Patch drift is a failure, not permission to drop a patch. The Maya cache-controller CPU eviction/concurrent-reread test must pass.
5. Run a fresh production baseline through the normal guarded worker launch path. Failure skips that component; it does not justify installing a candidate. Run registered native correctness tests on each GPU while holding the reservation.
6. Save durable rollback preimages before provisionally selecting the candidate. Native builds use immutable project-local paths, preserving shared Strata component packages. The fixed-path Maya cache-bound binary and its hash manifest are replaced transactionally together. Candidate SGLang package selection remains hash-pinned; the HyperQwen environment uses a reversible directory swap.
7. Repeat the same tests and fixed fixtures through the same guarded launch path. Compare only matched hardware, selected settings, context, input/output counts and fixtures.
8. Commit the runtime selection only after all applicable gates pass. Otherwise restore the old files/environment and require a normal guarded JSON smoke on restored production. Release only this job's reservation; no fallback model is loaded automatically.
9. Record sanitized outcomes and source pins, then commit and push explicit ledger/pin files and reviewed public exports. Unrelated staged/working changes defer publication. Private/public histories remain independent. Publication failure never turns failed qualification into a promotion.

A component already being tested can finish after 06:30; further components are deferred. The oneshot has a ten-hour start timeout and graceful stop/recovery. Preimages and rejected artifacts remain available; staging refuses less than 40 GiB free disk space.

## Promotion gates

Both production and candidate must pass:

- One warmup plus three fixed 128-output-token speed requests, with cache reuse checked. Prefill uses native timing/metrics, TTFT uses the client stream and decode uses first-to-last content timestamps.
- JSON, arithmetic and three-marker retrieval using more than 85% of the selected context. Actual backend input counts must confirm coverage.
- Supported image checks for the selected native vision profiles and parsed tool-call checks for the dense profiles.
- At least 90 seconds of continuous generation and a distinct fresh-process reload with JSON arithmetic.
- Owned worker/cgroup telemetry, expected memory budgets, selected host headroom, GPU inventory/headroom and temperature, no memory-limit/OOM events or active guard stop. Missing/invalid evidence blocks promotion.
- Candidate prefill and decode must each be at least **95% of the fresh production baseline**. TTFT must be no greater than **max(1.25 × baseline, baseline + 0.05 seconds)**, matching the AMD acceptance envelope. Context/settings/model precision cannot be reduced to make a candidate pass.

Existing guards are not weakened: host floor 2 GiB, selected native VRAM reserves, dense free-VRAM floor 512 MiB, temperature 82°C, memory-pressure and telemetry checks, concurrency one, swappiness 60 and idle 600 seconds. Qwen Flash-Next retains its separately approved 128 MiB/s write / 160 MiB/s combined swap allowance; other profiles retain 1/8 MiB/s. These are runtime I/O limits, not SSD-endurance budgets.

The missing RAM stick remains temporary. Increased available RAM or the timer does not authorize restoring full-RAM caches. That restoration still requires explicit hardware confirmation and Linux capacity verification.

## Interruption and recovery

Before activation, the updater writes and fsyncs a private transaction journal and each preimage. A restart restores uncommitted artifacts; committed, fully qualified artifacts remain selected. A user recovery service runs before the router and also after updater shutdown. It preserves foreign/live owners and refuses to overwrite external runtime edits. An unrecoverable preimage, active unknown work or failed restored-runtime smoke leaves a visible failure and reservation rather than silently opening admission.

The router has a recovery dependency and exposes `idle_for_s` on its authenticated health endpoint. Normal clients cannot bypass the reservation. Only the exact live updater PID, process start time and nonce can launch the normal guarded workers inside its reservation. Source/config/runtime changes detected before activation abort the candidate.

## Operations and validation

```bash
python3 scripts/install_daily_engine_update.py
systemctl --user list-timers nvidia-daily-engine-update.timer
systemctl --user status nvidia-daily-engine-update.service
journalctl --user -u nvidia-daily-engine-update.service
python3 scripts/daily_engine_update.py --check-only
```

`--check-only` discovers upstream revisions without builds, GPU use, promotion or publication. `--manual` permits an operator-requested run outside the nightly admission window but still requires idle and ownership checks. Do not run a second updater to bypass a held reservation. Completed GPU qualifications are not repeated merely to write documentation.

Installation validation: all 198 CPU regressions passed, including paired promotion rejection, interrupted file/environment rollback, external-edit preservation, reservation ownership, router admission and existing runtime/resource guards. A read-only six-component upstream discovery completed. No new engine candidate or speed benchmark was run during installation; the first scheduled run performs those gates before any update can be promoted.
