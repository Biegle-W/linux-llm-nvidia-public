# Maya qualification repair — November 6, 2026

## Current selected state: explicit reviewed acceptance

Maya1.1.56 is selected for both GLM and DeepSeek after explicit human acceptance of the measured8.19% prefill/6.10% decode slowdown. The preserved tested binaries, reconstructed patched source and354 protected assets verified before transactional activation. All516 CPU regressions pass; prior118/118 native tests on each GPU and both short DSH tool/result/follow-up checks remain the qualification evidence. The one-time exception applies only to this run; scheduled5% gates and all guards remain unchanged. Active binary hashes and API/hub/DSH health pass; GPUs are idle, the03:00 timer is active, and no pending transaction/publication or reservation remains. No inference benchmark was repeated. Next action is normal use.

The historical rejection and rollback below remain evidence of the automatic gate. The human subsequently accepted this exact slowdown and requested implementation. `--manual --accept-tested-maya-slowdown` rechecks the original run/revision and exact observed rates, all other quality/resource/latency gates, current hardware/settings, recorded artifact hashes and rollback completeness. It uses the existing exact-owner idle reservation and durable transaction. Future measurements or other failures cannot use this exception.

## Earlier automatic rejection and repair record

**The native qualification failures are fixed. All118 native tests pass on each GPU and513 CPU regressions pass. Maya1.1.56 was nevertheless rejected by the unchanged DeepSeek performance gate; verified Maya1.1.53 remains selected.** Both restored-production DSH checks and binary hashes pass, serving is healthy, GPUs are idle, and no pending transaction or reservation remains. The human explicitly approved repair/result publication after the initial automatic-review rejection.

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

## Completed updater retry

The full fresh build applied the maintained patch and built all registered targets. Native correctness passed118/118 on GPU0 in393.10s and118/118 on GPU1 in391.56s, with no failed, skipped or unrun tests. Both candidate actual DSH read/result/exact follow-up checks passed with matching prompt/output counts. GLM passed all paired gates; DeepSeek failed only prefill and decode regression thresholds.

| Profile | Runtime | Prefill tok/s | Client TTFT s | Decode tok/s | Prompt/output tokens |
| --- | --- | ---: | ---: | ---: | --- |
| GLM | production1.1.53 |550.3|10.058|15.5|5437/25|
| GLM | candidate1.1.56 |551.0|10.050|15.2|5437/25|
| DeepSeek | production1.1.53 |186.8|31.833|8.2|5701/60|
| DeepSeek | candidate1.1.56 |171.5|34.569|7.7|5701/60|

DeepSeek prefill regressed8.19% and decode6.10%, beyond the unchanged5% gates. No repeated timing run, tolerance relaxation or partial grouped promotion was used. These are single short calls, not statistical or sustained claims. The transaction rolled back both Maya profiles; both rollback DSH verifications passed. Installed binaries match the original1.1.53 manifest hashes.

Effective unchanged guards:87.76984787/89.76984787GiB worker high/max,2GiB host reserve,100C stops with three bad2-second samples,1024MiB native reserve per card, unlimited swap occupancy with128/160MiB/s write/combined over30seconds, GLM/DeepSeek active full PSI10%/15%, swappiness60, one request and600-second idle unload. Contexts remain65,536/32,768.

The failed revision is cached again. Normal nightly runs will not repeat it until a new revision or a separately justified explicit retry. Next action is normal production use; further DeepSeek performance diagnosis is distinct from these repaired native-test failures. [Sanitized results](validation-results/20261106-maya-qualification-repair.json).
