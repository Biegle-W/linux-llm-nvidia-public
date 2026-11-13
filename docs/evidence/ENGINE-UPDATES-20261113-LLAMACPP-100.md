# llama.cpp 1.0.0 installed by hand — November 13, 2026

The owner pointed at the llama.cpp 1.0.0 release; the upstream check confirmed it (tag `v1.0.0`, released November 13).

| Engine | From | To | Result |
|---|---|---|---|
| llama.cpp (`bolt-llamacpp`) | `cd959bae99ff` (0.9.0) | `b1b770d90d94` (1.0.0) | **promoted** |

HyperQwen, SGLang and Strata had no new commits; ComfyUI, Raylight, the mesh and GGUF nodes are pinned and current. Maya has a newer upstream revision (`f66a913c628c`) that was not part of this update.

## Review before the install

249 upstream commits, 1,092 files. A read-only review by Codex (gpt-6.1-sol) compared the upstream changes with the Bolt launcher (`scripts/bolt_iq2_worker.py`), the build options (`scripts/update_native_builders.py`) and the fields the short check reads. Its findings, which are a reading of the source and not a test:

- Every command-line flag and environment setting the launcher passes is still accepted with the same meaning. No launcher change was needed.
- The build options still exist. The shared libraries move to version 1.0.0, so the binary and library hashes in `config/bolt-iq2-runtime.json` had to be regenerated together; the builder does that.
- Upstream changed auto-fit accounting, how prompt checkpoints are stored, quantized KV-cache state copies, CUDA address reservation and some MoE and small-batch kernels. Any of these can change placement, memory use, speed or output with unchanged flags.
- The breaking changes of the major version (removed C APIs, `--defrag-thold`, a new RPC protocol version) are not used here.
- The server fields the short check reads (streamed usage and timings, tool calls, model list, request gauges) are unchanged.

## Build and install

Built in isolation under `runtimes/llamacpp-manual/v1.0.0-20261113/` with the usual options (CUDA 13, g++-13, two jobs, no local patches); the build log has no errors and `llama-server --version` reports `1.0.0-dev (build 12359, commit b1b770d90)`. The first attempt stopped while downloading the source from GitHub (the connection dropped and the 600 s limit passed); the second attempt ran through. The receipt hashes matched before the install: the manifest to be replaced, the candidate manifest, the server binary and all 15 libraries.

`config/bolt-iq2-runtime.json` was copied to `data/llamacpp-update-20261113/preimages/`, `rollback.sh` was written, and only then was the manifest replaced and `runtimes/llama.cpp` swapped with the new tree.

## Short DSH check

Load, one short answer through the app path, tool call, unload; GPUs unlocked and idle (1 MiB each) before and after each run.

| Version | Result | Prompt reading (tok/s) | Time to first token (s) | Generation (tok/s) |
|---|---|---:|---:|---:|
| 0.9.0 | pass | 501.5 | 12.85 | 68.4 |
| 1.0.0 | pass | 672.2 | 9.61 | 66.7 |
| 1.0.0 (repeat) | pass | 673.8 | 9.60 | 67.8 |

Prompt reading is 34% faster and the first token arrives 3.2 s sooner, the same on both runs. Generation is unchanged within run-to-run spread. The cause of the faster prompt reading was not investigated. No long-context or sustained run was made on 1.0.0, and the quality benchmark score for `bolt-llamacpp` (53.9%) was measured on 0.9.0 and not re-run.

Rollback: `data/llamacpp-update-20261113/rollback.sh` restores the manifest and the 0.9.0 tree from `data/llamacpp-update-20261113/preimages/`.
