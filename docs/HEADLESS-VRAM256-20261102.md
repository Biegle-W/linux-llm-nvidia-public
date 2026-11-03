# Headless-server free-VRAM guard — November 2, 2026

The human selected a minimum of **256 MiB free on each GPU** for the headless server. This supersedes the prior HyperQwen/Bolt/DeepSeek-Strata 512 MiB and SGLang 448 MiB free-memory stop thresholds. A card below 256 MiB counts as a violation; exactly 256 MiB is accepted.

The dense supervisor, Bolt supervisor, DeepSeek/Strata supervisor, short-tool checks, guard reporting and legacy qualification harness use the new floor. Bolt's compact-prefetch allocation check also requires 256 MiB remaining after its existing buffers are allocated; its hash pin is updated. Buffer dimensions and KV/cache allocation settings are unchanged.

The production resource supervisors retain their three-consecutive-sample stop rule. The qualification monitor still rejects any sampled dense-floor violation. Host RAM reserve, worker RAM high/max, swap occupancy and I/O limits, memory-pressure checks, 82°C temperature limit, telemetry failure handling, model contexts, weights, P2P/unlock requirements, ownership checks and 600-second idle unload are unchanged. Native engine cache-allocation reserves and calculated startup memory-admission budgets remain separate from this free-VRAM stop threshold.

Both model workers were inactive during the change. No model load, inference retest or new benchmark was run. Earlier guard failures and benchmark attribution remain historical evidence under their original thresholds; this policy change does not establish that SGLang MTP's CUDA OOM or Bolt's host-memory kill is resolved.

Validation: 54 focused CPU tests passed across shared floor, Bolt supervisor/runtime, swap guard, Strata runtime, CLI harness, pair telemetry and Torch prefetch-pool geometry. Boundary tests accept 256 MiB and reject 255 MiB at the supervisor; the allocation check accepts exactly 256 MiB after buffers and rejects one byte below it. The Torch allocation boundary uses mocked CUDA telemetry and CPU tensors. Changed Python modules compile and whitespace checks pass.
