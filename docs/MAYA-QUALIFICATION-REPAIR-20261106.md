# Maya qualification repair — November 6, 2026

Maya v1.1.56 initially built successfully but failed native qualification: 104 passed, four failed and ten not run. Production v1.1.53 remained selected. The original rejection and complete logs are preserved. This repair prepares one explicitly requested retry; promotion is not yet claimed.

## Causes and repairs

- Nine host-only executables were registered with CTest but excluded from the default build. Staging now reads CTest JSON and explicitly builds every missing registered target. An unknown/unbuildable target remains fatal.
- GLM fixture generation selected system Python without NumPy. CMake now selects the existing Maya environment after an import preflight; no package or system Python change.
- The graph-cache test expected invalidations from the retired single-key cache. It now requires exactly six captures, 90 replays and zero invalidations for the existing two-layer/three-plan workload. All dynamic-pointer, output parity, request accounting and abandoned-capture checks remain.
- The MiniMax mixed-quant failure was an asynchronous test upload bug, not demonstrated kernel arithmetic failure. Pageable uploads used the default stream while kernels used a nonblocking stream. CUDA memcheck and racecheck serialized enough to pass (zero reported errors/hazards), but ordinary CTest reproduced large errors. Waiting for the default-stream upload fixes ordering; the original bitwise and numerical comparisons passed three normal runs, then both-GPU focused checks. No kernel, tolerance or engine setting changed.
- PLE referenced an unavailable developer Q2 pack and unpublished block captures. The existing real 28.8GB table is reused, preserving all original table/hash vectors. A deterministic independent NumPy generator supplies synthetic Q2/BF16/F16 block weights and reference intermediates in the original fixture format. These are explicitly synthetic block fixtures, not restored real-checkpoint/ggml captures or new model-quality evidence. Every original PLE assertion/tolerance, native precision witness, capture/replay and buffer guard remains. Fixture hashes and provenance are recorded privately; no weight download or modification.

The maintained patch is applied with zero fuzz; source drift fails closed. CPU-only fixture generation uses two BLAS threads. Build caps, GPU ownership, exact cleanup, idle admission, all serving resource guards and paired short DSH promotion thresholds remain unchanged.

## Verification before retry

All fourteen originally failed/unrun tests pass on physical GPU0 and GPU1. The existing PLE executable reports zero failures with the independent fixtures. All 511 repository CPU regressions pass in the installed HyperQwen environment. An initial run in the minimal repository virtualenv had four missing-dependency import errors; the complete dependency environment run supersedes that invocation, not its recorded evidence.

No candidate was activated by these diagnostics. Their GPU reservation was released. The requested full updater retry will build a fresh candidate and run all registered native tests on both cards, fresh GLM/DeepSeek production/candidate DSH checks, and normal promotion or rollback.

## Local-only retry support

The first repaired fresh build completed all464 default targets and all nine previously omitted tests. Its external local-results wrapper was refused before baseline loading by the exact updater process-identity guard; no candidate was activated. That refusal is preserved. A supported `--manual --local-only` option now runs through the original updater entry point, saving a local report without commits, exports or pushes. It refuses pending remote publication instead of resuming it. All ownership, admission, build, correctness, paired DSH and rollback code is shared with the scheduled path.513 CPU regressions pass, including no-publication and pending-publication refusal tests. Remote publication is awaiting explicit approval after automatic approval review rejected it.
