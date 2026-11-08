# Flash-Next IQ1_M retired — November 8, 2026

At the owner's explicit request, `flash-next-iq1m-strata` (Unsloth v3.1 UD-IQ1_M on Strata) was retired and its weights deleted. `flash-next-strata` (GSQ-RCO IQ3_XXS, K=29 trimmed split) remains the only Flash-Next entry.

## Why

Same-day, same-router comparison at temperature 0 with each entry in its production setup (`data/flash-quality-20261107/results.json`, `results2.json`; no request errors, no prompt-cache reuse in speed runs):

| Check | IQ3_XXS | IQ1_M |
|---|---|---|
| Tool calls / long-context retrieval | 8/8, 4/4 | 8/8, 4/4 |
| GSM8K (50) | 49 | 49 |
| HumanEval 1-40 | 40 | 39 |
| MATH-500 level 4-5 integer answers (80) | 58 | 62 |
| HumanEval 41-164 (124) | 118 | 116 |
| ~5.7K tool prompt, prefill / decode tok/s | 1,243 / 146 | 1,322 / 149 |
| ~24K prompt, prefill / decode tok/s | 2,375 / 108 | 2,215 / 113 |
| 400-token write, decode tok/s | 124 | 124 |

Per-item paired differences were 5 vs 7 (noise). Speed was within ~7% either way. Published fidelity favors IQ3_XXS (GSQ-RCO IQ3_XXS ~99.4% of BF16 task average; Unsloth UD-IQ1_M top-1 agreement 79.7%, mean KLD 0.31 versus ~0.17 for IQ3_XXS-class quants). IQ1_M gave no speed advantage for 69.6 GB of storage.

## What changed

- Registry, daily updater (Strata component profiles, publication files, launch-preset refresh), router launch branch, swap/pressure guards, CLI guard table and `start_model.sh flash-iq1m` removed. `config/flash-iq1m-strata-runtime.json`, `scripts/flash_iq1m_strata_runtime.py` and its test were deleted and moved to the public export's retired list.
- DSH: `flash-next-iq1m-strata` (and the older IQ1_S id) now migrate to `flash-next-strata`; both DSH profile patches were regenerated (7 enabled models). The running DSH web service picks this up on its next restart.
- Maya qualification build: its PLE parity test needs the real 28.8 GB n-gram/PLE table, which it previously read from IQ1_M shard 3. It now reads IQ3_XXS shard 2. Byte comparison showed the two files differ in exactly 2 bytes (offsets 45 and 70, the GGUF `split.no`/`split.count` header values); the table tensor data is identical.
- Deleted: `models/unsloth/flash-next-iq1m-v31` (3 shards, 68,007,094,938 bytes) and `models/strata/packs/unsloth_iq1m_v31` (1,548,108,441 bytes). Pre-delete checks: worker inactive, GPUs idle, no open handles, link count 1, sizes matched the pinned manifest. Filesystem free space grew by 69,555,245,056 bytes. The private launch preset and all edited files' pre-images are kept under `data/iq1m-retire-20261108/` (not published). The 556 KB expert profile in `data/flash-next-iq1m-20261105/` is kept as history.

## Verification

516 unit tests passed (5 IQ1_M runtime tests removed, 2 retirement tests added). `/v1/models` lists 7 entries without IQ1_M; a request for `flash-next-iq1m-strata` returns 404. `flash-next-strata` loaded in 37 s through the router, answered a short check correctly, and unloaded to 1 MiB on both GPUs. No Maya build was rerun; the next daily update exercises the new table path. Restoring IQ1_M would require downloading it again.
