# Shared inference policy — October 28, 2026

All six maintained profiles and four engines use **600-second automatic idle unload** through their managed Desktop, CLI, router and DSH launch paths. The canonical source is [config/inference-policy.json](../config/inference-policy.json). [Validation evidence](validation-results/20261028-all-engine-policy.json).

| Model ID | Engine | Idle timeout | Mechanism |
| --- | --- | ---: | --- |
| `qwen27b-hyperqwen` | HyperQwen-vLLM | 600 seconds | Router lock + final request-gauge check + owned dense service stop |
| `qwen27b-sglang` | SGLang | 600 seconds | Router lock + final request-gauge check + owned dense service stop |
| `flash-next-strata` | Strata | 600 seconds | Native FIFO + activity timestamp + exclusive idle reservation |
| `glm-maya` | Maya | 600 seconds | Native FIFO + activity timestamp + exclusive idle reservation |
| `deepseek-strata` | Strata | 600 seconds | Native FIFO + activity timestamp + exclusive idle reservation |
| `deepseek-maya` | Maya | 600 seconds | Native FIFO + activity timestamp + exclusive idle reservation |

Active replies, queued work, model/vision loading, image computation, reservations and unknown state defer idle teardown. Health and catalog polling do not refresh inactivity. Only the owned model is unloaded; the router, DSH, unrelated apps and terminals remain. Native control/web processes may remain alive with weights unloaded. The next normal request reloads the selected model.

## Enforced launch behavior

The router reads the canonical timeout rather than an optional private field defaulting to zero. Native Strata/Maya launches always inject the timeout, activity path and GPU reservation, overriding stale disabled runtime settings; missing installed idle adapters fail closed. Their existing adapters are audited but not rewritten. The lifecycle logger uses the same required shared policy.

The installer now persists the timeout and telemetry flag when generating private access metadata, fixing loss of policy on reinstall. Normal dense CLI starts now enter the router, so they cannot escape its idle ownership/tracking. The router marks its internal worker launch to avoid recursion and retains the original storage/setup-queue/port preflight and bounded resource controls. Desktop filenames, provider/model IDs, contexts and numerical settings are unchanged.

## Actual verification

The visible SGLang test waited the real 600-second production interval without shortening it or manually unloading. Automatic `idle-unloaded` evidence recorded timeout 600; the observer saw completion after 610.1 seconds, including checks and teardown. Router/DSH stayed active and the GPU reservation was released.

A separate final check activated the preserved-preflight launcher, submitted a normal authenticated Chat Completions request after automatic expiry, verified model reload/JSON output, then explicitly cleaned up that smoke test. This later explicit cleanup is separate from the earlier automatic expiry proof. Final router state is idle, with no automatic HyperQwen restoration.

Shared-policy, idle/FIFO/race, router, supervisor, MoE and lifecycle regressions passed in visible terminals. Coverage includes all six profile mappings and both native adapters. Full 600-second automatic expiry was newly observed for SGLang; do not claim six fresh physical timer tests. Prior HyperQwen/GLM live and Strata short-timeout evidence remains historical. Large MoE models were not loaded on reduced RAM.

## Other standing policy

The user accepts proportional context/performance tradeoffs across models/engines: compare percentage capacity gain against measured generation slowdown and report prefill/TTFT too. Quality, full allocated context and resource qualification remain required. No fixed acceptable-loss percentage was invented and no context was automatically expanded. SGLang 38K remains pending qualification.

Keep swappiness 60, the 512 MiB dense VRAM reserve, selected MoE RAM/cache limits and uncapped guarded dense RAM, the user-approved 2 GiB host reserve across all six profiles, 82°C thermal stop and active swap/pressure/telemetry guards. Model loading and parked swap remain allowed. Required visible terminals are unchanged. Model performance results were not rebenchmarked.

Six exact prior source files were hash-verified and preserved in the private retirement archive at 8ca025e. Raw console/test/coverage/idle evidence is private under `data/all-engine-policy-20261028/`.

October 29: [all-profile 2 GiB reserve](ALL-PROFILES-HOST-RESERVE2-20261029.md) is verified by 41 CPU checks; earlier 8 GiB settings remain historical.


October 29: [dense RAM cap removal and MoE reserve qualification](MOE-VRAM512-20261029.md) supersedes earlier dense 30/36 GiB limits; other guards remain.


## DeepSeek/Maya demand-cache qualification — October 29

DeepSeek/Maya passed at **512 MiB native VRAM reserve and unchanged 32,768-token context** on the 45.55 GiB reduced-RAM host. The selected temporary configuration combines a 16 GiB model-file cache target with a native 12 decimal GB pinned hot-expert cache. JSON, arithmetic, image, 29,467-input-token retrieval, 426.5s continuous generation, a fresh isolated process reload and two normal guarded loads all passed. Observed worker swap occupancy and swap read/write rates were zero.

The saved three-request screen measured **1.23 decode tok/s**, 42.5 prefill tok/s and 51.491s TTFT. Earlier full-RAM/historical rates remain preserved; no fresh paired 2,048 MiB control was produced, because the earlier reduced-RAM configuration failed its swap guard.

This supersedes the earlier unresolved DeepSeek/Maya reduced-RAM status only for
this qualified configuration. Other five selected settings/results remain unchanged;
Flash/Strata's earlier reduced-RAM failure remains unresolved. Native warming limits
did not bound demand mmap residency; the new controller targets clean model-file
residency, with overshoot possible between scans. Its qualified binary is hash-pinned.

The host 2 GiB floor, 46/48 GiB MoE worker budget, dense 512 MiB free-VRAM stop,
82 C thermal limit, owned swap/PSI/telemetry guards, swappiness 60, concurrency one
and idle 600s remain. Original native source/binary and archived preimages remain;
weights, precision and mathematical kernels are unchanged. Router idle, owned
workers stopped, no GPU reservation, DSH preserved and no fallback.

After explicit human RAM-restoration confirmation, verify Linux capacity, restore
appropriate full-RAM cache/prefill choices from preimages while preserving the
qualified VRAM reserve and guards, then verify normal guarded load/reload.
No timer or MemAvailable trigger.

See [demand-cache qualification and six selected results](MAYA-DEMAND-CACHE-20261029.md)
and [numeric evidence](benchmark-results/20261029-maya-demand-cache.json).
