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

Keep swappiness 60, the 512 MiB dense VRAM reserve, current per-profile RAM/cache limits, 8 GiB host reserve, 82°C thermal stop and active swap/pressure/telemetry guards. Model loading and parked swap remain allowed. Required visible terminals are unchanged. Model performance results were not rebenchmarked.

Six exact prior source files were hash-verified and preserved in the private retirement archive at 8ca025e. Raw console/test/coverage/idle evidence is private under `data/all-engine-policy-20261028/`.
