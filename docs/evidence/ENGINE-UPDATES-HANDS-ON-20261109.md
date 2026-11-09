# Hands-on engine updates — November 9, 2026

The owner retired the nightly updater after it rejected three good releases over its own harness bugs and told the agent to install updates by hand from now on ([runbook](../ENGINE-UPDATE-RUNBOOK.md)). The timer `nvidia-daily-engine-update.timer` is disabled. All three updates were installed one at a time with the server idle. Each profile got a single short DSH tool-call check (`daily_engine_update.py --smoke-current`), on production before the swap and on the new version after it. All passed and all three were kept. Rollback scripts and pre-images are in `data/{strata,hyperqwen,maya}-update-20261109/`.

| Profile | Engine (old → new) | Prefill tok/s | TTFT s | Decode tok/s |
| --- | --- | --- | --- | --- |
| `flash-next-strata` | Strata 0.2.12 → 0.2.13 (`d2f0964`) | 1020.5 → 1022.6 | 6.01 → 5.99 | 77.1 → 77.5 |
| `deepseek-unsloth-strata` | same | 27.8 → 28.1 | 6.07 → 6.13 | 12.1 → 12.2 |
| `qwen27b-hyperqwen` | `6ab9bd0` (vLLM 0.32.0) → `9268d8d` (vLLM 0.33.0) | 2082.6 → 2105.8 | 2.81 → 2.78 | 62.3 → 62.6 |
| `glm-maya` | Maya 1.1.56 → 1.1.57 (`0065548`) | 548.8 → 550.1 | 10.10 → 10.08 | 14.8 → 15.0 |
| `deepseek-maya` | same | 185.5 → 177.3 | 32.1 → 33.5 | 7.1 → 7.7 |

Single short runs, so differences of a few percent are noise. The `deepseek-maya` prefill dip (−4%) is a warning only.

## What the old script got wrong, and what was done instead

- **Strata 0.2.13** is a hotfix release: the control package is 0.1.59.1 while the engine and dsv41 packages are 0.1.59, and the release still carries the superseded control 0.1.59 asset. The script picked packages by name pattern and assumed control and engine versions match. Packages were instead selected from the signed `strata-feed.json` (sequence 124) and verified with upstream `strata_control` signing. `ENGINE_VERSION` and the runtime manifest use the engine version 0.1.59. The first DeepSeek check after the swap measured 66.6 s TTFT (85.8 prefill tok/s), a one-time first-load cost; the repeat run (in the table) is at parity. Flash-Next's launch cfg now runs the qwen package from `runtimes/strata-manual/0.2.13-20261109/packages/qwen`.
- **HyperQwen**: pip writes `#!/bin/sh` + `'''exec' <env>/bin/python` trampolines for long paths; the script only rewrote `#!<env>` shebangs, so relocated console scripts pointed at the deleted staging folder. All staging-path references in `bin/` were rewritten and checked to be gone. All repo patches and the KVarN patch set applied to vLLM 0.33.0 (some at an offset).
- **Maya 1.1.57**: the script ran upstream tests without `STRATA_PYTHON`, `STRATA_GGUF_PY` or `STRATA_GLMD_FIXTURES` and with a 120 s timeout, so 19 tests failed. Re-run with that environment on the 3080 Ti, 14 of the 18 that apply to sm_86 pass. Remaining warnings: `glmd_mmq_ids_test` (Q4_K/Q5_K/IQ2 grouped MMQ about 5-6e-4 from the host q8_1 reference), `glmd_mv_parity` (one f16 mat-vec job refused), `glmd_mv_parity_sm70` (Volta), `glm_dsa_pack_fast_test` (two warm-order checks that need the RAM tier, empty on a single-GPU run). `ple_parity` passed. The build staged by the failed run was installed from its receipt after checking every target, candidate and protected file hash.
