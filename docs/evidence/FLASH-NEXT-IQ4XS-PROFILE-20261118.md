# Flash-Next UD-IQ4_XS-v31 added as a second router entry, November 18, 2026

The owner asked to keep both Flash-Next quants. `flash-next-iq4xs-strata` now sits next to `flash-next-strata`
(IQ3_XXS), which stays the default Flash-Next entry and is unchanged. Trial numbers and the quality comparison are in
[FLASH-NEXT-IQ4XS-TRIAL-20261117.md](FLASH-NEXT-IQ4XS-TRIAL-20261117.md).

## What the entry is

| Item | Value |
|---|---|
| API id / launch name | `flash-next-iq4xs-strata` / `./scripts/start_model.sh qwen-iq4xs` |
| Weights | `unsloth/Qwen3.8-Flash-Next-GGUF`, `UD-IQ4_XS-v31`, four shards, 93.67 GB, NVMe, `models/strata/models/unsloth-UD-IQ4_XS-v31` |
| Engine | The same Strata engine binary as `flash-next-strata` (0.1.60 today); the launch is refused if the two presets name different engines |
| Layout | Strata's automatic split: layers 0–19 on the RTX 3080, 20–47 on the RTX 3080 Ti; KV streaming with 32,768 of 131,072 cells in VRAM; 15 pool workers |
| Context | 131,072 |
| Worker RAM | 87.77 GiB soft / 89.77 GiB hard, 2 GiB host reserve (same as `flash-next-strata`) |
| Guards | SSD-streaming swap limits (128 MiB/s writes, 160 MiB/s combined over 30 s), 15% pressure, and a 256 MiB free-VRAM floor per card |
| Shared with IQ3_XXS | MTP draft head and vision projector |

Launch checks (`scripts/flash_iq4xs_strata_runtime.py`): shard sizes and the pack's file hashes against
`config/flash-iq4xs-strata-runtime.json`; the preset's card order, layout, context, KV settings and worker count against
the registry; no second way of setting any of them; same engine as the installed Flash-Next preset.
The preset itself lives outside the repo at `~/.local/state/strata/launch/qwen-flash-next-iq4xs.json`.

## Qualification through the router

All through the normal router path on port 10100, under the worker budget and guards above.

| Check | Result |
|---|---|
| Load | ready in 28–34 s, context 131,072 |
| JSON and arithmetic answers | exact, pass |
| Image (solid colour) | pass |
| Tool call with follow-up (API) | pass, no reasoning content |
| DeepSeek Harness real read-tool round trip with follow-up | pass (12.2 s): 5,598-token tool prompt read at 760 tok/s, first tool-call output after 7.6 s, 40 tokens written at 43.7 tok/s (first request after a fresh load) |
| 19,955-token cold prompt, 300 tokens written, three runs | reading 1,574–1,598 tok/s; writing 67.0 (first), 78.1, 83.2 tok/s; first token after 12.6–13.2 s |
| 113,029-token cold prompt, code word placed one seventh of the way in | correct answer; reading 2,314 tok/s; first token after 49.1 s |
| Long writing | 4,331 tokens in 52.7 s at 84.4 tok/s (the model ended the essay itself) |
| Unload and fresh reload | both cards back to 1 MiB; reload 28.3 s; answer correct |

| Resource | Measured |
|---|---|
| Lowest free VRAM while loaded (3080 Ti / 3080) | 659 MiB / 580 MiB (floor 256 MiB) |
| Worker memory peak (with file cache) | 81.6 GiB in the first session, 84.1 GiB in the second (soft limit 87.77 GiB) |
| Worker swap peak | 1.7 GiB in the first session, 0 in the second; no guard stop |
| Lowest host MemAvailable | 21.2 GiB |
| Hottest card | 67 °C |

## Limits of this qualification

- One request near the window (113K of 131K tokens); nothing at the very top of the window and no multi-hour run.
- The long-writing check lasted under a minute because the model finished early.
- The first session swapped 1.7 GiB during loading while the second did not; the cause was not investigated.
  Loading swap is not a guard violation.
- The 390-item quality score (65.5% against 62.0% for IQ3_XXS, difference not established) was measured on the trial
  service outside the router, with the same launch settings.
- A running DeepSeek Harness web app lists the new id only after `nvidia-dsh.service` restarts.

Raw results stay on the server under `data/profile-20261118/`.
