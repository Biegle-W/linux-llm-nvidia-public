# Short API switch checks — November 1, 2026

These are the original switch outcomes. Later SGLang defaults and bounded Super policy fixes passed; the current eight-profile timing observations and unload results are in [the short-tool report](SHORT-TOOL-BENCHMARKS-20261101.md). Original failures are preserved below.

All eight current profiles reached readiness through API selection and were released after the sequence. Six completed an actual DSH read call and matching tool result. Checks used a tiny file and 128-output cap, stopped at the tool result. No full-context, sustained or timed-idle tests were run. Weight loading time is separate from tool timing.

| Profile | Tool result | Tool-check seconds | Final worker |
|---|---|---:|---|
| HyperQwen | pass | 4.24 | stopped |
| SGLang | failed: claimed existing fixture missing without tool call | — | stopped |
| Flash-Next Strata | pass | 10.48 | stopped |
| GLM Maya | pass | 62.13 | stopped |
| Unsloth DeepSeek Strata | pass | 41.31 | stopped |
| Unsloth DeepSeek Maya | pass | 135.36 | stopped |
| Bolt | pass | 135.05 | stopped |
| Super | failed: swap-churn guard during inference | — | stopped |

Super's30.47-second swap window measured51.46MiB/s reads and56.12MiB/s writes, combined107.58MiB/s against its96MiB/s combined limit. The safety latch remains; this is not a passing configuration under the observed workload. Other resource guards remain enabled.

The Bolt-to-Super switch initially returned409 because backend work was still pending after router admission cleared. API switching now waits for vLLM running/queued metrics to clear before the existing final owned-worker stop check, matching the native wait behavior. The resumed transition succeeded. A regression covers this wait for both Bolt and Super;52router and7request-state regressions passed. Earlier completed tests were not rerun to hide failures.
