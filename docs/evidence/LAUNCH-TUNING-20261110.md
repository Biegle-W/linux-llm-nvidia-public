# Launch tuning: Strata direct table reads, Maya GLM 64K checkpoint interval — November 10, 2026

Two launch settings suggested by forum posts (lcz.me) were tested on this server and adopted on the owner's instruction. Full rows: [`20261110-launch-tuning.json`](validation-results/20261110-launch-tuning.json).

| Profile | Setting | Before | Now |
| --- | --- | --- | --- |
| `glm-maya` (Maya 1.1.57) | `MAYA_GLM_CKPT_EVERY` (environment) | unset: a checkpoint every 16,384 fresh prompt tokens | `65536` |
| `flash-next-strata` (Strata 0.2.13) | `--ple-io` | unset: Strata's residency policy copied the 26.8 GiB table into RAM | `direct` |

Method: each run is one load through the router, one cold long prompt built from the project docs with a unique first line, one short follow-up, then unload. Arms were alternated. Time to first token is measured by the client; prefill and decode come from the engine log.

## Maya GLM: checkpoint interval

Cold 37,240-token prompt, 64 tokens generated.

| Setting | Time to first token | Decode tok/s |
| --- | --- | --- |
| before (16,384), 2 runs | 38.4 s, 38.2 s | 17.6, 17.8 |
| `MAYA_GLM_CKPT_EVERY=65536`, 3 runs (the last after adoption) | 30.7 s, 30.8 s, 30.5 s | 17.9, 17.8, 17.7 |

- By default Maya read the prompt as separate pieces of 16,384 + 16,384 + about 4,450 tokens. With the interval at 65,536 it reads the same 37,217 or 37,218 fresh tokens (the first line differs per run) in one pass (1,294 tok/s in the engine log).
- Prompts under 16,384 tokens are unchanged. The checkpoint at the end of the prompt is still saved, and the follow-up turn reused it as before (about 1.3 s to first token either way).
- Trade-off: no intermediate checkpoints during a long first read, so a read cancelled partway keeps less.
- The same value given as `--prompt-cache-every 65536` in the config args had no effect (38.0 s, still read in 16,384-token pieces). Only the environment variable works with this launcher.
- Short DSH check after adoption: pass.

## Strata Flash-Next: direct table reads

Cold 18,467-token prompt, 300 tokens generated.

| Setting | Load | Time to first token | Prefill tok/s | Decode tok/s |
| --- | --- | --- | --- | --- |
| before (table in RAM), 2 runs | 40.6 s, 40.6 s | 10.1 s, 10.1 s | 1,972, 1,973 | 89.9, 88.7 |
| `--ple-io direct`, 3 runs (the last after adoption) | 30.4 s each | 9.6 s each | 1,952, 1,950, 1,956 | 92.3, 92.6, 87.3 |

- Kept for the load time (about 10 s faster) and because the 26.8 GiB table no longer takes RAM. Prefill is 1% slower. Decode is within run-to-run noise: the first two direct runs were about 3% faster, the third was not.
- The forum's reason does not apply here. Strata already kept its 8,192-token prompt chunk and a 96-slot ring with the table in RAM, and planned no drive reads for a 32K prompt; the chunk is the same with direct reads.
- Short DSH check: pass before, during the trial and after adoption (first-turn decode 77.8, 92.0 and 85.4 tok/s over about 40 tokens, so not a reliable comparison).
- Not changed: Strata reports that it could not lock the table in RAM because the worker's memory-lock limit is 8 MiB. With direct reads the table is no longer held in RAM.

## Where the settings live

- `config/maintained-profiles.json`: `glm-maya` `selected_settings.environment.MAYA_GLM_CKPT_EVERY`, and `flash-next-strata` `selected_settings.ple_io`.
- `scripts/serve_router_moe.py` refuses a Flash-Next launch when `--ple-io` in the private launch settings differs from the registry in either direction, and a Maya launch when a registry environment value is missing or different in the private config. `tests/test_flash_next_strata_split.py` covers the Flash-Next check.
- The private launch settings themselves are not in this repository. Their pre-change copies are in `data/trial-20261110/` on the server. To go back: remove the two registry values and the matching private settings. Nothing checks for a Maya environment value that is left in the private config after its registry value is removed, so remove that one by hand.
