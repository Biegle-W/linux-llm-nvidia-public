# Maya 1.1.65 and Strata 0.2.14 installed by hand — November 15, 2026

Daily update at the owner's request. From this run on the owner wants the upstream fixes and speed changes of a new version researched before it is installed; that review is the first section.

| Engine | From | To | Result |
|---|---|---|---|
| Maya (`glm-maya`, `deepseek-maya`) | `f66a913c628c` (1.1.61) | `c81fab6c9d63` (1.1.65) | **promoted** |
| Strata (`flash-next-strata`) | `d2f096475817` (0.2.13; control 0.1.59.1, engine 0.1.59) | `09b603886925` (0.2.14; control 0.1.60.1, engine 0.1.60) | **promoted** |
| Strata (`deepseek-unsloth-strata`) | 0.2.13, DSV4.1 engine 0.1.59 | unchanged | **frozen at 0.2.13**: upstream no longer runs DeepSeek |

HyperQwen, SGLang and llama.cpp had no new commits; ComfyUI, Raylight, the mesh and GGUF nodes are pinned and current.

## Review before the install

Sources: the upstream release notes and changelogs, the signed Strata feed, and the staged source trees. A read-only review by Codex (gpt-6.1-sol) covered the diffs and the issue trackers; its claims that decide anything here were checked against the staged source. Speed figures in this section are upstream's, measured on other hardware.

### Maya 1.1.62 to 1.1.65 (125 commits, 97 files)

Applies to this server:

- **DeepSeek decode on several GPUs** (1.1.64, upstream issue 956). Since 1.1.58 a layer split could keep the PCIe expert lane on when it gained nothing; the reporters lost about 4-5% decode (two RTX A4000, UD-Q8_K_XL). The lane now turns off on several GPUs unless it measures faster. New setting `DS4_STREAM_TIE=keep|off`; the first start measures again.
- **Engine faults are reported as errors** (1.1.65, issue 827). An answer the engine stops on a GPU fault used to end as `length`. A streamed answer now ends with an error event and no `finish_reason`; other requests get HTTP 422 with type `engine_error` and the partial text. Clients that only look at `finish_reason` will see this differently.
- **GLM drafting stall report** (1.1.65, issue 860, still open). A drafting step over 20 s prints a `glm stall:` line (`MAYA_GLM_STALL_S`). It only reports; the hang itself, reported on unequal NVIDIA cards under Windows, is not fixed.
- **Tests** (1.1.65). Upstream fixed `glm_layer_graph_test` itself and moved the parity test, so both local patches needed a refresh (below).

Does not apply: the AMD APU + NVIDIA pairing and its speed-ups (1.1.62 to 1.1.65), Windows build and pinning fixes, MiniMax checksum checks, Qwen GGUFs with mixed expert formats.

No launch setting, build option, binary name or manifest name changed. Open upstream reports to keep in mind: a 3% decode loss against 1.1.43 on one Blackwell card under Windows (issue 998), and older reports of split imbalance (733).

### Strata 0.2.14 (902 commits, 2,263 files)

- **DeepSeek is gone.** `docs/DEEPSEEK41.md` at the tag says 0.2.13 was the last version that set up and started DeepSeek V4.1-Flash, and `serve/server.py` stops a DeepSeek config before the engine starts. The signed feed (sequence 126) still lists the DSV4.1 package, but it is the 0.2.13 file (0.1.59, byte-identical to the installed binary). So `deepseek-unsloth-strata` cannot move to 0.2.14 and stays on its own 0.2.13 runtime, which shares nothing with the Flash-Next install.
- **Prompt reading on Strata's own kernels** instead of code taken from llama.cpp. Upstream: 4-8% faster long prompts on an RTX 4090 with IQ3_S, 15% at 32,000 tokens on an RTX 5090. Two-card PCs were not measured against 0.2.13. Answers can differ from 0.2.13 in some words. The first long prompt may pay a one-time kernel preparation (measured upstream on a Mac only).
- **Fixes for a model split across cards:** values shared between GPU stages could cross when cards work at once without peer access (now per thread); the last card's cache could take room the MTP draft head needs at start; freed conversation memory is returned to Linux so parked conversations are accepted again.
- **Each card keeps only its own dense weights** by default. This server's Flash-Next preset already sets stage trim, so nothing changes here.
- No new drafting default for these cards; the preset keeps MTP.

Does not apply: AMD, Windows, Mac, Intel Arc and DGX Spark items. Open upstream reports to keep in mind: non-finite logits on sm_86 with IQ3_XXS (issue 6019) and boolean tool arguments returned as strings (5979); whether they persist in 0.2.14 is not known.

## Build and install

**Maya.** Built in isolation under `runtimes/maya-manual/v1.1.65-20261115/`. Both local patches failed on the first attempts and were refreshed; the old files stay for the retired updater's reviewed-revision check.

- `patches/maya-ds4-file-cache-target-v1165.patch`: upstream added an include line next to the one the patch inserts. Same added and removed lines as `v1153`.
- `patches/maya-qualification-v1165.patch`: the `glm_layer_graph_test` hunk is dropped (fixed upstream) and the parity-test hunk is re-anchored; the CUDA upload-ordering hunk is unchanged.

The third build has no rejects. Before the install every hash in the receipt matched: four files, four candidates, two binaries and 354 private files. The four files were copied to `data/maya-update-20261115/preimages/`, `rollback.sh` was written, and only then were the files replaced and `runtimes/project-maya` swapped. `config/maya-unsloth-runtime.json` now names the refreshed cache patch.

**Strata.** Packages were taken from the signed feed (sequence 126): control 0.1.60.1 and the cuda13 engine 0.1.60. Feed signature, package digests and the engine's signed manifest were verified with upstream's own `strata_control` code. Control went to `runtimes/strata-terminal/terminal/0.1.60.1` with the idle adapter applied to `serve/server.py`, `current` was repointed, and the Flash-Next preset now starts the engine in `runtimes/strata-manual/0.2.14-20261115/packages/qwen`. The preset was saved to `data/strata-update-20261115/preimages/` and `rollback.sh` written first. Nothing under `runtimes/strata-unsloth-029` or in `config/deepseek-unsloth-runtime.json` was touched.

## Short DSH check

Load, one short answer through the app path, tool call, unload; one profile at a time, GPUs unlocked and idle (1 MiB each) before and after.

| Profile | Version | Result | Prompt reading (tok/s) | Time to first token (s) | Generation (tok/s) |
|---|---|---|---:|---:|---:|
| `flash-next-strata` | 0.2.13 | pass | 1017.8 | 5.62 | 87.1 |
| `flash-next-strata` | 0.2.14 (run 1) | pass | not kept | not kept | not kept |
| `flash-next-strata` | 0.2.14 (run 2) | pass | 1063.9 | 5.37 | 79.4 |
| `flash-next-strata` | 0.2.14 (run 3) | pass | 1059.5 | 5.40 | 84.4 |
| `flash-next-strata` | 0.2.14 (run 4) | pass | 1056.4 | 5.41 | 82.0 |
| `deepseek-unsloth-strata` | 0.2.13, before | pass | 84.2 | 67.81 | 11.7 |
| `deepseek-unsloth-strata` | 0.2.13, after (untouched) | pass | 27.8 | 5.97 | 12.1 |
| `glm-maya` | 1.1.61 | pass | 553.2 | 10.02 | 14.3 |
| `glm-maya` | 1.1.65 (run 1) | pass | 555.9 | 9.97 | 14.0 |
| `glm-maya` | 1.1.65 (run 2) | pass | 545.9 | 10.17 | 14.3 |
| `glm-maya` | 1.1.65 (run 3) | pass | 541.5 | 10.25 | 14.2 |
| `deepseek-maya` | 1.1.61 | pass | 190.1 | 31.29 | 7.9 |
| `deepseek-maya` | 1.1.65 (run 1) | pass | 192.2 | 30.99 | 8.2 |
| `deepseek-maya` | 1.1.65 (run 2) | pass | 184.8 | 32.21 | 8.2 |

Reading the numbers:

- **Flash-Next:** prompt reading is 4-5% faster on all three kept runs, in line with the new prompt kernels. Generation measured 79.4 to 84.4 tok/s against 87.1 before (3-9% lower, a warning under the promotion rule). The same check gave 77.1 and 77.5 tok/s on November 9, so single short runs spread this far; runs 3 and 4 also ran while Maya was compiling with two jobs. Whether 0.2.14 generates slower here is not settled by these runs. Run 1 passed, but its numbers were overwritten by run 2 (same file name).
- **DeepSeek on Strata** was not changed. Its first run was the first load after a reboot at 21:06 and shows the known one-time start cost (67.8 s to first token); the later run is the usual 6 s.
- **Maya:** both profiles are the same as 1.1.61 within run-to-run spread. `deepseek-maya` generation reads 8.2 against 7.9 tok/s, which fits the upstream multi-GPU decode fix but is inside the spread of earlier days (7.1 to 8.1). `glm-maya` called the tool in all three runs; the skipped tool call seen once on 1.1.61 did not repeat.

No long-context or sustained run was made on either new version.

Rollback: `data/maya-update-20261115/rollback.sh` restores Maya 1.1.61; `data/strata-update-20261115/rollback.sh` restores Strata 0.2.13 for Flash-Next.
