# Daily NVIDIA engine updater

## Current schedule and coverage — November5,2026

The restored timer runs at **03:00 America/Toronto**, skips missed runs (`Persistent=false`) and adds no random delay. It is a local systemd maintenance job. The current short-test policy supersedes the former long-context/sustained update pipeline.

| Automatic component | API/DSH profiles | Selection |
| --- | --- | --- |
| HyperQwen | `qwen27b-hyperqwen` | Default branch; compatible vLLM pin, complete upstream series and KVarN patches |
| Heterogeneous SGLang | `qwen27b-sglang` | Default `fix/851-consolidated`; selected dependency pins and current local compatibility patch |
| Maya | `glm-maya`, `deepseek-maya` | Latest stable tag; grouped control/binaries/manifests, bounded-cache patch |
| Strata | `flash-next-strata`, `deepseek-unsloth-strata` | Latest stable tag; signed feed, control and CUDA13 engine packages |
| llama.cpp | `bolt-vllm`, `flash-next-iq1s-llamacpp` | Latest stable tag; one shared runtime, both manifests qualified together |

TensorFold remains a hash-pinned native package and receives a daily stable-release check. ComfyUI/Raylight stable releases and Mesh/GGUF default heads are also checked daily; newer versions are reported for separate image/video workflow and GPU-residency qualification. They are not silently installed through the text-model qualifier. No model weights, contexts, precision, driver, kernel, firmware or resource guards are automatically changed.

## Admission, staging and promotion

1. Discover immutable source commits. Stable-tag discovery dereferences annotated tags and excludes prereleases. A changed SGLang default branch requires patch review. Rejected revisions remain recorded; an already installed qualified revision is recognized before that rejection list.
2. Require **20 minutes idle**, no queued/loading/admitted request and no existing reservation. Normal scheduled admission ends at06:30. Reserve atomically and recheck before stopping only an idle owned worker. Compilation also waits for admission, uses two jobs and retains the updater's6/8GiB systemd budget.
3. Stage outside production. HyperQwen starts from a clean compatible wheel before applying the full series/KVarN; orphan patched modules cannot survive wheel replacement. SGLang uses the manifest-selected patch, including its timing initialization repair. Maya retains private launch settings and the interpreter; native CUDA headers/runtime/cuBLAS match the installed CUDA13SDK. Strata verifies the signed feed's archive hashes and both engine manifests with upstream trusted keys and safe extraction. No inherited trust override is accepted.
4. Qualify one fresh production short DSH read/tool-result/exact follow-up per affected entry, capturing metrics during the first tool generation and unloading afterward. Run registered native correctness checks on both cards where applicable. A failed baseline leaves production unchanged.
5. Write durable preimages, then provisionally select the candidate. Grouped engines update every affected manifest and frontend together. Existing preimage slots cannot be overwritten. File artifacts are installed before a containing staged directory moves, so receipt paths remain valid.
6. Repeat one short DSH check per affected entry using the **same private workspace/proof fixture**. Require equal model/settings/context/hardware/fixture hashes, prompt/output counts and zero prompt-cache reuse. Missing native metrics, failed tool/follow-up/unload, bad resource evidence or mismatched counts reject promotion. Prefill and decode must each be at least95% of baseline; TTFT must be at mostmax(1.25×baseline,baseline+0.05s). Single short calls are a conservative screen, not a statistical speed study.
7. Commit selection only after all entries pass. Otherwise restore preimages and verify restored production through the same short DSH protocol before releasing the reservation. Unknown/live owners, external edits, missing telemetry and failed recovery retain blocking evidence. Never clear another task's reservation or force a fallback model.
8. Save dated observations/source pins and sanitized outcomes; publish explicit owned records through independent private/public commits and normal pushes. Validate the hash-allowlisted binary media without UTF-8 decoding. Unrelated working/staged edits or a dirty public checkout defer publication, and owned publication paths persist for retry.

There is **no full-context retrieval, sustained generation, repeated reload or timed-idle suite** in scheduled qualification. The legacy long-test flag is rejected; such work needs a separate explicit request. Contexts remain allocated limits with their existing historical qualification scope.

## Ownership, visibility and guards

Owned-worker cleanup retries only the three recognized transient busy/unknown states, with the existing120-second deadline and2-second interval; ownership errors are never retried or bypassed. Receipt file targets and directory-swap targets must be disjoint after resolving aliases, including metadata targets. Validate before baseline loading and enforce the same rule in both transaction operation orders.

Post-rollback verification always uses private captured logs, independently of candidate visibility permission or a usable terminal. SIGHUP, SIGTERM and SIGINT share the interruption/rollback path; baseline interruption aborts the run rather than continuing to another component.

The updater owns its reservation by exact live PID/start time/nonce. Its DSH child validates that owner and worker invocation on every forwarded request. It connects only to the already selected private backend through a local timing proxy; normal API clients remain blocked by the reservation. This avoids adding a maintenance bypass to the public API. The parent owns unload and reservation release.

Scheduled runs are configured for guarded headless qualification when no graphical desktop is available. Their logs remain private and all model/admission/resource guards remain mandatory. A foreground desktop terminal is used when available; operator-driven CLI tests retain their foreground TTY. This scheduled exception does not authorize hidden manual benchmarks.

Preserved limits:2GiB host available; dense worker32/36GiB and heavy workers87.76984787/89.76984787GiB; per-card free-VRAM256MiB where applicable plus selected native reserves/fit targets;100C temperature stops; existing three-bad-sample2-second hysteresis, fail-closed telemetry, PSI/swap windows, swappiness60, concurrency1 and idle600s. Active swap limits remain1/8MiB/s for dense/Bolt and128/160MiB/s for streaming entries over30s, with unlimited occupancy. [Per-profile guard table](ALL-ENTRY-BENCHMARKS-20261105.md).

## CUDA profiler-header preflight

Maya host C++ targets include the profiler API before the runtime API. The isolated CUDA13SDK must contain its own `cuda_profiler_api.h`; otherwise a system CUDA12header can be selected first and introduce incompatible type guards. Native Maya staging now checks for the SDK-local header and syntax-checks both includes before compilation. The matching build-tools dependency is `nvidia-cuda-profiler-api==13.0.85`, installed only in the isolated engine-tools environment. Driver, weights and model guards are unchanged. [NVIDIA package](https://pypi.org/project/nvidia-cuda-profiler-api/13.0.85/).

## Operations

```bash
python3 scripts/install_daily_engine_update.py
systemctl --user list-timers nvidia-daily-engine-update.timer
systemctl --user status nvidia-daily-engine-update.service
journalctl --user -u nvidia-daily-engine-update.service
python3 scripts/daily_engine_update.py --check-only
```

Use a foreground terminal for `--manual` or `--smoke-current PROFILE`. Updates retain the20-minute idle gate. The current-only diagnostic requires serving to be idle and already unloaded; it never stages or promotes an update and may verify a repair immediately after cleanup. Both modes retain exclusive ownership and all resource guards. `--check-only` never builds, uses GPUs, promotes or publishes. Installation archives replaced project-owned units, verifies them, reloads systemd and restores the timer without restarting API, hub, DSH or any model.

[Restoration validation](DAILY-UPDATER-RESTORATION-20261105.md). Earlier daily ledger entries retain their original long-suite scope and failures; they do not describe the new scheduled protocol.

A requested single-component comparison can use `--manual --components strata`. This restricts candidate updates to Strata while preserving full catalog-coverage validation,20-minute idle admission, resource guards, paired short DSH checks, rollback and independent publication. The scheduled command without this filter still covers every maintained component.
