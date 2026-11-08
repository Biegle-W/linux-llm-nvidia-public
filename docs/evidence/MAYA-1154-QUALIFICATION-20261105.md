# Maya 1.1.54 qualification attempt — November 5, 2026

**Maya 1.1.54 did not qualify. Maya 1.1.53 remains selected for GLM and DeepSeek.** The updater completed and published its rejection records; service success means the coordinator finished, not that the candidate was promoted.

The requested source is `c1670044bbc09310f35f9d00f7596c50ae8a38f1`. The retained production source is `7c4aa56ed7faea2788705d8e85dd58e892d19f4b`. Neither attempt activated 1.1.54, so its DSH tests were **not reached** and there are no 1.1.54 model-performance results.

## Attempts and results

The first isolated build failed because the CUDA13SDK lacked `cuda_profiler_api.h`, allowing an incompatible system CUDA header to be included first. Installing [NVIDIA's matching profiler component13.0.85](https://pypi.org/project/nvidia-cuda-profiler-api/13.0.85/) in the existing engine-tools environment fixed the actual compiler probe. An early SDK-local header and syntax preflight is now maintained.496 CPU regressions and25 focused public preflight tests passed; no driver or model-weight update was involved.

The corrected retry built all464 targets, verified matching CUDA13linkage and adapted the frontend successfully. Both fresh production1.1.53 DSH baselines passed actual read/tool-result/exact follow-up, resource checks and owned unload. It then ran the registered native suite on physical GPU0: **102 passed,4 failed,9 did not run,115 total**. GPU1's suite and provisional1.1.54 DSH checks were not reached because the native gate failed.

| Failed or unavailable coverage | Evidence / implication |
| --- | --- |
| Eight native CPU test executables | Registered with CTest but `EXCLUDE_FROM_ALL`; the default build did not produce them |
| GLM big fixture generation and dependent test | CMake selected a system Python without NumPy; generator failed and its dependent test did not run |
| Qwen PLE parity fixture | Its default Q2_0 development table/pack is unavailable; this is not a configured Maya Qwen entry |
| GLM layer-graph cache assertion | Test requires a positive invalidation count; the newer multi-key cache retains entries and never increments that counter |
| MiniMax mixed-quant numerical checks | Two400-row IQ2_XXS/IQ2_XS/IQ2_XS checks failed; one reported max relative error0.974. MiniMax is not configured, but the unchanged engine-wide gate still blocks promotion |

Prefill WMMA parity passed in171.35s within its upstream300s timeout. No timeout, numerical tolerance, skip policy or native promotion gate was relaxed. Setup failures and assertion failures are distinguished from the actual MiniMax numerical mismatch; these results do not establish a GLM/DeepSeek model regression.

## Production 1.1.53 baseline observations

These are **baseline observations only**, measured during the first actual short DSH tool generation. Loading and follow-up are excluded; zero prompt-cache reuse was reported. OS file caches were not dropped. No full-context or sustained model test was run.

| Production profile | Prefill tok/s | TTFT s | Decode tok/s | Prompt/output tokens | Context |
| --- | ---: | ---: | ---: | ---: | ---: |
| GLM / Maya1.1.53 | 498.9 | 11.111 | 14.6 | 5440/26 | 65,536 |
| DeepSeek / Maya1.1.53 | 182.5 | 32.647 | 6.8 | 5701/60 | 32,768 |

| Profile | Worker RAM high/max GiB | Host available floor | GPU policy | Swap write/combined MiB/s over30s | Active full PSI |
| --- | ---: | ---: | --- | ---: | ---: |
| GLM / Maya | 87.76985/89.76985 | 2GiB | 1024MiB native reserve per card | 128/160 | 10% |
| DeepSeek / Maya | 87.76985/89.76985 | 2GiB | 1024MiB native reserve per card | 128/160 | 15% |

Both retain unlimited swap occupancy,100C temperature stops, existing three-bad-sample2-second hysteresis, fail-closed telemetry, concurrency1, swappiness60 and idle600s. These are effective limits, not measured peak use; short calls may not fill every averaging window. All existing guards, contexts, caches and downloaded checkpoints remain unchanged.

## Remaining work

Build registered test executables omitted from the default build; select the existing NumPy-capable runtime interpreter for synthetic fixtures; resolve the PLE fixture requirement without fetching an unnecessary model; reconcile the graph-cache test with its new cache semantics; investigate the mixed-quant MiniMax mismatch. Failed gates must remain visible. Native correctness must pass before the updater can reach candidate DSH checks and decide on promotion.

The rejected revision is cached normally, so the daily job will not repeatedly rebuild the same failed source. The first failure and the explicitly corrected retry are retained. The enabled03:00America/Toronto timer, API/DSH entries and selected1.1.53 runtimes are preserved. [Sanitized machine-readable evidence](validation-results/20261105-maya1154-qualification.json).
