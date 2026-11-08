# Daily updater restoration — November5,2026

## Cleanup and target-layout review follow-up — November 5

Both parts of review finding **#3** are fixed. Short-check cleanup and the coordinator now share the same exact-owner retry helper: transient `backend_busy`, `resources_busy` and `backend_state_unknown` states use the existing120-second deadline and2-second interval. Ownership conflicts and other errors still propagate immediately; no reservation or guard is bypassed.

Before baseline loading, receipt validation resolves file/directory targets and rejects a file target inside or equal to a swapped directory, including symlink aliases and the updater's metadata targets. The transaction methods repeat the guard in both operation orders. This prevents a later directory swap from hiding an earlier file update. Existing disjoint Maya/Strata/llama.cpp receipts remain supported.

**494 CPU regressions passed**, including transient cleanup during qualification failure, timeout/ownership refusal, preflight rejection without baseline or mutation, and reversible rejection of nested targets in either order. No GPU benchmark or serving restart was needed; the03:00Toronto schedule is unchanged.

## Recovery review follow-up — November5

Review findings **#1** and **#2** are fixed. Both interrupted-transaction recovery and in-process rollback explicitly mark restored-production verification. That short DSH check always captures private logs without relying on a TTY or scheduled candidate-headless permission. Normal candidate qualification still requires its selected visibility policy, and all ownership/resource guards remain.

The coordinator now handles **SIGHUP**, SIGTERM and SIGINT through the same interruption path. A terminal hangup during provisional activation rolls back, verifies restored production, and clears pending state only after success. Interruption during baseline propagates instead of being mistaken for an ordinary quality failure.

**488 CPU regressions passed**, including a real process-level SIGHUP during a provisional file transaction, restored checks under graphical-only policy with absent/closed terminals, and continued rejection of unauthorized headless candidate checks. These are CPU lifecycle fixtures; no extra model benchmark or live production rollback was needed. All85 focused public checks also passed. The timer was restored only after those checks; its next run remains November6 at03:00EST.

The updater is migrated to the current guarded short-DSH policy and its03:00 America/Toronto schedule is enabled. It covers all nine text entries exactly once: eight automatically qualified entries across five grouped components, plus one pinned entry with release monitoring. ComfyUI, Raylight, Mesh and GGUF also receive version checks; automatic image/video replacement remains outside the text qualification protocol.

## Repairs

- Stable release tags replace unreleased Maya/Strata/llama.cpp HEAD selection; annotated tags resolve to commits. The SGLang fork's actual default branch is checked explicitly.
- Fresh HyperQwen wheels receive the complete current series and KVarN patches; copied orphan modules cannot survive. SGLang uses its selected manifest patch and native timing initialization fix.
- Maya updates its shared control, both fixed binaries and manifests together while preserving launch settings, interpreter, cache controller and matching CUDA13libraries. Shared llama.cpp updates Bolt and Flash manifests together.
- Strata uses official signed feed/package verification, archive digests and safe extraction, preserving existing model packs and checkpoints. Both maintained entries qualify before its grouped update commits.
- Each baseline/candidate uses one actual DSH read/result/exact follow-up and owned unload with a shared fixed fixture. Native metrics are captured during the tool generation. No full-context or sustained suite runs.
- Recovery uses the same short DSH protocol. Preimages are collision-protected; unrelated edits/owners remain blocking. Public binary sample files are verified as bytes, and pending publication ownership/hashes survive a failed push.
- The coordinator owns its foreground terminal; model workers are API-only and retain their independent guards. A desktop terminal's transient unit receives the6/8GiB build caps as well as the parent scheduled unit. Installation preserves old managed units and does not restart serving.

[Full operating policy, scope and commands](../DAILY-ENGINE-UPDATE-POLICY.md). [Per-profile model guards](ALL-ENTRY-BENCHMARKS-20261105.md).

## Validation

**485 CPU regressions passed**. The exact-owner SGLang DSH check passed its real read/result/exact follow-up, six resource samples and owned unload. The timer is active, with the next run **November6 at03:00EST**; user lingering is enabled, and the updater service is currently inactive. API/hub/DSH were not restarted. Detailed verification and installed timer status are recorded in the [sanitized restoration receipt](validation-results/20261105-daily-updater-restoration.json). Read-only discovery recognized current HyperQwen, SGLang, Strata and llama.cpp; it found the newly published stable **Maya1.1.54**. That discovery alone does not promote a runtime. The other monitored engines were current.

The host currently has SSH/TTY sessions but no graphical desktop display. Scheduled runs are configured for **guarded headless tests with private logs**, preserving the20-minute idle admission, all resource/ownership guards and rollback. When a desktop is available the coordinator can use its foreground terminal. Manual CLI qualification retains its foreground TTY.
