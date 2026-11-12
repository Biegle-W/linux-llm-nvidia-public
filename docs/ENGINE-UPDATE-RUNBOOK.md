# Engine update runbook (hands-on)

Since 2026-11-09 engine updates are installed by hand by the maintaining agent, not by the nightly script. The timer `nvidia-daily-engine-update.timer` stays **disabled**. `scripts/daily_engine_update.py` is kept as a toolbox: its read-only discovery and its single-profile short DSH check are still the right tools, but it no longer builds, promotes or pushes on a schedule.

Why: the unattended updater rejected good upstream releases over its own harness bugs and then stopped retrying them (HyperQwen bin/ relocation, Maya test environment and timeouts, a Strata hotfix control package). Watching each step is faster than hardening the script for every upstream change.

Promotion policy is unchanged: promote unless it really breaks ([policy](DAILY-ENGINE-UPDATE-POLICY.md)). A real break is a failed load, DSH, tool call or unload, invalid output, under half the decode/prefill speed, or over 3x TTFT. Smaller slowdowns are warnings. Re-run once before rolling back on speed alone; a new engine's first load can pay a one-time cost (Strata 0.2.13 DeepSeek: 66 s first TTFT, 6.1 s on the repeat).

## Daily check

```bash
cd ~/Desktop/linux-llm-nvidia
gpu-unlock-health status --brief            # must say VERIFIED; never create data/GPU-LOCK by hand
systemctl --user is-enabled nvidia-daily-engine-update.timer   # expect: disabled
python3 $PWD/scripts/daily_engine_update.py --check-only        # read-only discovery, no GPU
```

`--check-only` may report `rejected-revision-not-retried`; that list in `data/daily-update/state.json` belongs to the retired script and does not block a hands-on install.

## Install steps (every engine)

1. **Idle.** Router idle and unloaded, both GPUs at ~1 MiB, unlock VERIFIED.
2. **Stage in isolation** under `runtimes/<engine>-manual/<rev>-<date>/` (or reuse a complete staging dir and its `build-receipt.json`). Nothing in production changes.
3. **Baseline production** with the short DSH check, one profile at a time, calling the script by **absolute path** (its reservation owner check matches its own command line):
   `python3 $PWD/scripts/daily_engine_update.py --smoke-current PROFILE`
4. **Swap with pre-images** into `data/<engine>-update-<date>/preimages/` and write a `rollback.sh` beside them before anything is replaced.
5. **Check the new version** with the same command; compare with the baseline.
6. **Keep or roll back.** Roll back only on a real break (`rollback.sh`). Leave serving idle and unloaded.
7. **Record:** pin in `config/daily-update-versions.json`, a dated entry at the top of `docs/DAILY-ENGINE-UPDATES.md`, `docs/CURRENT-STATE.md` if a version changed. Commit, export to the public checkout (`python3 scripts/sync_public.py ../linux-llm-nvidia-public`, check the diff for secrets and home paths), commit there, and push both. Hold the push and ask the owner only if something big changed (a rollback or real break, a profile added/retired, deletions, serving or guard changes, anything about keys, privacy or the public export list).

## Working over SSH

- `scripts/visible_terminal.py` cannot open a terminal from an SSH session when no desktop session is reachable (`Visible harness terminal did not start`). Run the short checks headless in that case; nothing has started when that error appears.
- The Tailscale link can drop for a minute at a time. Start the build and each check detached on the server (`setsid nohup ... &`), write a `.done` file at the end, guard against a double start with a `.started` file, and poll with short SSH calls. Do not hold one SSH session open for the whole step.

## Engine notes

**HyperQwen** (`qwen27b-hyperqwen`). Production is the environment `runtimes/env-hyperqwen`. Build a copy: copy the env, `pip install --upgrade -r docker/requirements.txt`, delete and force-reinstall the same `vllm` wheel, `patches/apply.sh` then `apply.sh --kvarn`, `compileall`. Then rewrite **every** staging-path reference in `bin/` to the production path. pip writes both `#!<env>/bin/python` shebangs and `#!/bin/sh` + `'''exec' <env>/bin/python` trampolines; the old script only fixed the first kind. Then swap the env folder. Always delete the `vllm` package folder before the reinstall: `apply.sh` refuses to run over a copied tree whose `.hyperqwen-patches` stamp still matches an older series. Check the build log for one `== ` line per patch in `patches/series` plus the 4 KVarN patches and no `FAILED`. Production runs `bin/vllm` directly from `config/maintained-profiles.json` and uses none of the upstream launchers, so launcher and Docker changes upstream do not apply here. New `VLLM_*` variables change the compile-cache key, so the first load after an update may recompile once; judge speed on the repeat run. For a second update on the same day, suffix the folder (`data/hyperqwen-update-20261109b`).

**Strata** (`flash-next-strata`, `deepseek-unsloth-strata`). Use the release's signed `strata-feed.json`: it names the control package and the cuda13 `engine` and `dsv41` packages, so pick by feed entry, not by asset-name regex (hotfix releases carry extra control assets). Verify the feed signature and every package with upstream `strata_control` signing. The control version (e.g. 0.1.59.1) may differ from the engine version (0.1.59):
- control → `runtimes/strata-terminal/terminal/<control>` with `serve/server.py` passed through `native_idle_policy.transform(..,'strata')`, then repoint `current`;
- Flash-Next launch cfg `~/.local/state/strata/launch/qwen-flash-next.json`: `exe`, `lib_dirs` → the qwen package, `cwd` → the new control folder (the file holds keys: never print it);
- DeepSeek: swap `runtimes/strata-unsloth-029/engine` (dsv41 package) and `source` (tag checkout, transformed `serve/server.py`), regenerate `config/deepseek-unsloth-runtime.json` hashes, and set `engine_version` and `ENGINE_VERSION` in `scripts/strata_unsloth_runtime.py` to the **engine** version.

**Maya** (`glm-maya`, `deepseek-maya`). Native build with the repo patches (see `scripts/update_native_builders.py`). Its upstream test suite needs `STRATA_PYTHON` (project-maya venv), `STRATA_GGUF_PY` (`build/_deps/strata_llamacpp-src/gguf-py`) and `STRATA_GLMD_FIXTURES` (a run-local folder), and per-test timeouts well above 120 s. `*_sm70` tests target Volta and do not apply to sm_86. Kernel-tolerance failures are warnings; the DSH check decides. Install = the receipt's file replacements (the two binaries and their runtime manifests) plus swapping `runtimes/project-maya`. Since 1.1.59 the engine reads its settings as `MAYA_X`; an older `STRATA_X` is copied to `MAYA_X` at start only when `MAYA_X` is not set, so set the `MAYA_` name in launch settings and never both. The CMake build options keep their `STRATA_` names.

**sglang, llama.cpp** follow the same pattern with `scripts/update_builders.py` / `update_native_builders.py` as the reference for build flags and pinned manifests. **ComfyUI, Raylight, Mesh, GGUF** are pinned and monitor-only; install one only when the owner asks.

**ComfyUI** (image and video entries). Review the upstream diff against `scripts/comfy_nodes`, `scripts/comfy_video_nodes` and the patched Raylight and mesh nodes first. Switch `runtimes/ComfyUI` and then `runtimes/ComfyUI-video` in place with `git checkout --detach <commit>`; do not move the folders (the video tree borrows the image tree's git objects). `runtimes/ComfyUI` is a partial clone: fetch from a full local clone with `git fetch --no-filter --refetch <clone> <commit>`. Install only the pins that changed in `requirements.txt` with `~/.local/bin/uv pip install --python runtimes/<env>/bin/python ...` in both `env-comfy` and `env-comfy-video` (dry-run first; PyTorch must not move, and never use `-r requirements.txt -U`). Regenerate both lock files with `uv pip freeze` and move the commit in `config/comfy-runtime.json` and `config/comfy-video-trial.json` and the release in `config/daily-update.json` in the same step, or the worker refuses to start. Check with `scripts/comfy_run.py` under a pty (`script -qefc`), before and after: both image models at 1024, both `--video-entry` models, and the Wan `prepare` and `raylight` stages. The script takes and releases its own GPU reservation.
