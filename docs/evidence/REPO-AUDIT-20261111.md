# Repository audit and cleanup — November 11, 2026

The whole repository (490 tracked files) was read for stale documents, dead code, test problems, stale registry text and export hygiene. 85 findings were raised and each was checked a second time: 80 held, 5 were wrong. This change fixes the ones that are safe to fix without changing how anything is served. Nothing was deleted, and no model, engine, launch setting or guard value changed.

## Fixed

**A unit test wrote into the live router folder.** `tests/test_api_gateway.py` replaced the router's root folder for the test but not its worker state path, so every test run wrote a made-up worker record to `data/router/worker.json`. The router ignored it (the record never matches a real worker), but it was wrong. The test now uses its temporary folder. The leftover file was moved to `data/audit-20261111/`.

**The updater installer would have turned the retired nightly timer back on.** `scripts/install_daily_engine_update.py` no longer enables or starts the timer. It still writes the unit files and installs the recovery service. The policy doc no longer lists the installer as a routine command.

**Code that pointed at old things.**

- `scripts/inference_policy.py` checked the idle markers in the Strata 0.1.51 control files. It now checks `terminal/current` (0.1.59.1 today), which carries the same markers. The matching test path was updated.
- `scripts/benchmark_models.py` sorted entries with a fixed list that lacked `bolt-llamacpp` and `deepseek-unsloth-strata` and would have stopped with an error. Unknown ids now sort last.
- Unused imports removed from two scripts and six tests. One test class renamed so two test files no longer share a class name.

**Documents that described an older system.**

- `DAILY-ENGINE-UPDATE-POLICY.md`: the current promotion rule is stated first (a break is under half speed or over three times the time to first token; smaller differences are warnings). Everything about the nightly script is under one "retired" heading. Retired ids and old RAM figures are gone.
- `LOCAL-SETUP.md`, `REPOSITORY-MAP.md`, `OPERATIONAL-LIFECYCLE.md`, `CODEX-CONTEXT-HANDOFF.md`: a note at the top says which date the old sections describe; statements that could be checked against the registry were corrected (contexts, RAM budget, "prepared, not deployed").
- `INFERENCE-SWAP-POLICY.md`: a "Current values" section matches the guard code. Three sections that were exact copies of `BENCHMARK-HISTORY.md` were replaced by a pointer.
- `CURRENT-STATE.md`: the DeepSeek weight set is 233 GB across NVMe and SATA, not 122 GB on NVMe.
- `BENCHMARK-REPORTING.md`, `STORAGE-POLICY.md`, `MAINTAINED-PROFILES.md`, `network/README.md`, `README.md`, `AGENTS.md`: retired names, a broken link target, the "daily updater" wording and a stale test count.
- `docs/README.md`: the row for the private Codex handoff note is inside the private markers, so the public index no longer links a file that is not published.

**Registry text that nothing reads.** `hardware_capacity` said 32 GiB, temporary, upgrade pending; it now says 96 GiB. Six `context_validation` notes said the entry was disabled pending the RAM upgrade. Two notes pointed at a moved document. `config/daily-update.json` describes its schedule as retired.

**Housekeeping.** `.gitignore` covers more key, checkpoint and editor file types. `.gitattributes` covers the top-level `patches/` folder. Both repositories were repacked (3,544 loose objects into one pack of about 28 MiB each).

Checks: 536 unit tests pass on the server; no file appears under `data/router/` after a test run.

## Left for the owner

These change what is served, what is published or what is kept, so they were not done.

- **Public export checks** could be stricter, and `tests/test_flash_next_strata_split.py` plus the 15 tests in `scripts/test_native_linux_gpu_unlock.py` (not run by the suite today) are not in the export list.
- **Registry revisions** recorded for Strata and Maya were not refreshed by the November 9 hands-on updates. The four `selected_settings.reason` notes still say "qualification pending"; they are part of the settings fingerprint, so editing them needs care. `deepseek-maya` names a different runtime manifest than the updater uses.
- **Disk:** about 8 GB of unused or duplicate weight files, about 60 GB of old runtime copies and about 40 GB of old trial folders under `data/` could be removed. Root drive has 388 GB free, so nothing is urgent.

## Follow-up, same day: unused files and the retired id removed

The owner approved the first two items that were left open. 536 unit tests pass afterwards.

Removed from the repository and from the public copy (git history keeps them):

- Scripts: `bolt_iq2_trial.py`, `boot_peer_verify.py`, `verify_pair_p2p.cu`, `build_maya_file_cache_bound.py`, `check_local_api.py`, `comfy_download.py`, `install_codex_context_monitor.py`, `test_sglang_quantized_embedding.py`.
- Patches with no reference anywhere: `sglang-int8-embedding-sm86.patch`, `sglang-gpu-placement-audit.patch`, `vllm-dflash-meta-share.patch`, `vllm-draft-placement-audit.patch`.
- Config: `config/bolt-iq2-trial.json`.
- The retired id `deepseek-strata`: its branches in `scripts/serve_router_moe.py` and `scripts/update_builders.py`, its entry in the swap guard's streaming list, and one clause in `scripts/inference_swap_guard.py` that could not be reached. The swap-guard test now covers `deepseek-unsloth-strata` in its place.
- `tests/test_bolt_iq2_trial.py` was renamed `tests/test_bolt_iq2_worker.py`; it always tested the worker.

Kept on purpose:

- `sglang-hetero-ct-w4a8-mtp.patch`, `sglang-mlp-w4a8-sm86.patch` and `llama-demand-mmap-prefault.patch`: not applied today, but dated evidence docs link them as the record of what was built.
- `patches/maya-ds4-file-cache-target.patch`: `config/maya-cachebound-runtime.json` still names it.
- `config/maya-cachebound-runtime.json`, `config/web-search.example.json`, `config/model-catalog.example.json`, the two hardware config files, the ComfyUI workflow files and `tooling/codex-context/AMD-SOURCE.json`: each is still read, tested or installed on the host.

Three links in dated evidence docs now point at removed files: two in `BOLT-NATIVE-IQ2-20261104.md` (the trial coordinator and its manifest) and one in `MAYA-DEMAND-CACHE-20261029.md` (the isolated builder). Those docs are left as written.
