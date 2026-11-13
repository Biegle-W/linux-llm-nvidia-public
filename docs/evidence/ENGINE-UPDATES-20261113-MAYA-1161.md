# Maya 1.1.61 installed by hand — November 13, 2026

Second engine update of the day, at the owner's request after the llama.cpp 1.0.0 install.

| Engine | From | To | Result |
|---|---|---|---|
| Maya | `8b0a449c599f` (1.1.60) | `f66a913c628c` (1.1.61, released November 12) | **promoted**, with a warning on `glm-maya` |

## What changed upstream

Four commits, 30 files. The release notes are about other hardware and models: faster DeepSeek prompt reading and EXL3 decode on AMD Ryzen AI Max APUs, prompt lookup for MiniMax on one GPU, and a setup calibration change. One item reaches DeepSeek here but is off unless switched on: "fast prompt reading" (`fast_prefill`). It was left off. No launch setting changed.

## Build and install

Built in isolation under `runtimes/maya-manual/v1.1.61-20261113/` with the two local patches; no fuzz and no rejects. Every hash in the build receipt matched before the install: four files, four candidates, two binaries and 354 protected private files. The four files were copied to `data/maya-update-20261113/preimages/`, `rollback.sh` was written, and only then were the files replaced and `runtimes/project-maya` swapped.

## Short DSH check

Load, one short answer through the app path, tool call, unload; one profile at a time, GPUs unlocked and idle (1 MiB each) before and after.

| Profile | Version | Result | Prompt reading (tok/s) | Time to first token (s) | Generation (tok/s) |
|---|---|---|---:|---:|---:|
| `glm-maya` | 1.1.60 | pass | 556.4 | 9.97 | 14.3 |
| `glm-maya` | 1.1.61 | **fail** | | | |
| `glm-maya` | 1.1.61 (repeat 1) | pass | 563.9 | 9.65 | 14.6 |
| `glm-maya` | 1.1.61 (repeat 2) | pass | 548.9 | 10.08 | 14.3 |
| `glm-maya` | 1.1.61 (repeat 3) | pass | 568.2 | 9.76 | 12.1 |
| `deepseek-maya` | 1.1.60 | pass | 188.2 | 31.40 | 7.4 |
| `deepseek-maya` | 1.1.61 | pass | 176.0 | 33.66 | 8.1 |

**Warning, `glm-maya`:** the first check after the install failed. The model loaded and answered normally, but it replied with an invented file content (37 output tokens) instead of calling the read tool, so the check found no tool round trip. Three repeats on the same build passed. No earlier hands-on check of `glm-maya` (1.1.57 to 1.1.60) failed this way, so one failure in four is recorded as a warning, not as a break, and 1.1.61 stays installed. Whether 1.1.61 makes this more frequent is not known; four runs cannot tell.

`deepseek-maya` is the same within run-to-run spread. No long-context or sustained run was made on 1.1.61.

Rollback: `data/maya-update-20261113/rollback.sh` restores 1.1.60 from `data/maya-update-20261113/preimages/`.
