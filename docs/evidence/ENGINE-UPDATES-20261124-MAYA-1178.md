# Maya 1.1.78 installed by hand — November 24, 2026

Project Maya was updated from 1.1.74 (`e8d4f297f434`) to 1.1.78 (`1016876a387e`, 126 commits over 1.1.75-1.1.78) in the scheduled hands-on update run, for `glm-maya`, `deepseek-maya` and `hy4-flash-maya`.

## Review before the install

Release notes and the commit list were read first. What applies here:

- **DeepSeek (`deepseek-maya`):** a turn could end empty after thinking, and a tool call written inside the thinking was lost (#1206, #1207, fixed in 1.1.78); a router row with no finite score could read out of range (#1114, 1.1.77); the speed calibration could be fooled by a kept conversation (#1203). The late VRAM reserve added in 1.1.73 is capped at 1 GB (#1026, 1.1.76).
- **GLM (`glm-maya`, GLM-5.3-Flash):** on Linux the shard file mappings are dropped after loading (#1182, about 6.4 GB less memory on GLM-5.3-Flash per upstream); 1.1.75 made answers repeatable across starts (prompt reading about 2% slower per upstream). The full GLM-5.3 bug of 1.1.75-1.1.77 (#1200) does not touch this entry.
- **Hy4 (`hy4-flash-maya`):** a stop signal while the engine loads now ends the engine too (#1181); picture folders are removed at exit (#1180). Upstream speed-ups in this range are for AMD cards.
- **Build:** since 1.1.75 the build options and engine folders are named `MAYA_*`; the old `-DSTRATA_X` options are still mapped to `MAYA_X` by `cmake/maya_old_names.cmake`, so the builder's options work unchanged.

## Build

The DeepSeek file-cache patch (`maya-ds4-file-cache-target-v1173.patch`) applied unchanged. The qualification patch's `ple_parity` hunk was rejected because upstream renamed `STRATA_PLE_FIXTURE_DIR` to `MAYA_PLE_FIXTURE_DIR`; it was regenerated with the same changes on the new names as `patches/maya-qualification-v1178.patch` (dry-run with no fuzz on a clean 1.1.78 tree) and the builder points at it. Staged under `runtimes/maya-manual/v1.1.78-20261124/` (the rejected first attempt is kept beside it as `-patch-reject`); `maya`, `maya-ds4` and `maya-hy4` link CUDA 13 runtime and cuBLAS. The four private launch configs were carried over byte-identical. Pre-images and `rollback.sh`: `data/maya-update-20261124/`.

## Checks

Short DSH check (one real tool call, tool result and follow-up, owned unload) and the gBench chat-template check, one profile at a time, GPUs at 1 MiB before and after. Single runs.

| Profile | Version | Prompt reading (tok/s) | First token (s) | Generation (tok/s) | gBench |
|---|---|---:|---:|---:|---|
| `glm-maya` | 1.1.74 | 523.3 | 10.60 | 14.0 | 6/6 |
| `glm-maya` | 1.1.78 | 541.2 | 10.25 | 14.2 | 6/6 |
| `deepseek-maya` | 1.1.74 | 186.5 | 31.67 | 8.1 | 6/6 |
| `deepseek-maya` | 1.1.78 | 179.7 | 32.98 | 8.2 | 6/6 |
| `hy4-flash-maya` | 1.1.74 | 47.8 | 116.3 | 13.5 | 6/6 |
| `hy4-flash-maya` | 1.1.78, first start | tool call and follow-up pass; **owned unload failed** | | | fail (no case inside 120 s) |
| `hy4-flash-maya` | 1.1.78, re-run | 26.4 | 209.5 | 15.6 | 6/6 |

**`hy4-flash-maya` on its first 1.1.78 start.** The new engine measures a "prompt route" before the first answer (which experts outside VRAM are streamed to a GPU and which run on the CPU lane): 322-435 s on each of the four starts today. On the first start the stop signal came while that measurement was still running; the server did not end within the wrapper's 20 s, so systemd killed the worker after its 90 s stop timeout (the unload completed, GPUs back to 1 MiB, but the check counts it as a failed owned unload). The gBench run right after loaded again, answered, and stopped in 2 s, but its six cases did not finish inside gBench's 120 s window. The re-run passed everything, and three later stops ended in 2-3 s.

**Why it stays slow.** The engine logs "the prompt route not settled (the prompts go on timing it)" and writes `runtimes/project-maya/data/hy4-prompt-route.txt` only once the timing settles; the short checks never give it enough prompts, so every start measured again. First token 209.5 s against 116.3 s (1.8x) and prompt reading 26.4 against 47.8 tok/s (55%) are within the promotion rule (warnings); generation is 16% faster. Whether the route settles and is remembered in real use is not verified yet.

## Decision

**Promoted** under the promotion rule: all three profiles load, call tools, follow up, pass gBench and unload on the re-run; GLM and DeepSeek run at the same speed. Because the first `hy4-flash-maya` start failed its owned unload, and the public export gains the new patch file, this record was **committed but not pushed**, for the owner to review. Rollback: `data/maya-update-20261124/rollback.sh` (router idle) restores 1.1.74 for all three entries.
