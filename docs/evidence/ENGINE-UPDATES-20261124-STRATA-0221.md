# Strata 0.2.21 installed by hand — November 24, 2026

Strata was updated from v0.2.20 to v0.2.21 (`d46f5f268f8e`, signed feed sequence 133) in the scheduled hands-on update run.

| Component | From | To | Result |
|---|---|---|---|
| Control (serves every Strata entry) | 0.1.66 | 0.1.67 | **promoted**; the local idle-reservation patch applied unchanged (one block) |
| `strata-inkling` (`inkling-strata`) | 0.1.66 | 0.1.67 (`eada4591cef1`) | **promoted** |
| `strata-hy4` (`hy4-flash-strata`) | 0.1.66 | 0.1.67 (`4da72cca05cc`) | **promoted** |
| Qwen engine (`flash-next-strata`) | 0.1.65 | 0.1.67 tried, **kept at 0.1.65** | 0.1.67 generates 11-12% slower on two runs, as 0.1.66 did |
| DeepSeek on Strata | v0.2.13 | unchanged | frozen; passes under control 0.1.67 |

## Review before the install

Release notes and the 292 commits v0.2.20..v0.2.21 were read first. What applies here:

- **Inkling 2 Mini (CUDA):** auto prefill chunk sized by free memory and slots; growing the global K/V no longer ends the engine, the host tail covers the rest of the context (#6905, a long-conversation crash); 64-token-tile prefill MoE for sm_80..89 with identical results; the K/V window reserve is back to v0.2.20's; Q8_0 expert layers of GGUF files use a faster grouping. The DSpark drafter changes do not apply (`inkling-strata` runs with the drafter off).
- **Qwen:** one accuracy fix in prompt reading (#6776; the order of one sum changes, so answers can differ after a few tokens) and the fix for "layer 0 never rang" on RTX 30-series (#6713), which is what broke the since-retired UD-IQ4_XS entry on engine 0.1.66.
- **Hy4:** upstream reports the same output as 0.2.20.
- **Control:** an engine that dies three times in 10 minutes is no longer restarted. No changed defaults that reach the presets used here; the preset hashes were recorded before and after the install.

All four packages were verified against the signed feed with upstream's signing code and staged under `runtimes/strata-manual/0.2.21-20261124/`. Pre-images and `rollback.sh`: `data/strata-update-20261124/`.

## Checks

Short DSH check (one real tool call, tool result and follow-up, owned unload) and the gBench chat-template check, one profile at a time, GPUs at 1 MiB before and after. gBench passed 6/6 on every run below. Single runs, no prompt-cache reuse unless noted.

| Profile | Version | Prompt reading (tok/s) | First token (s) | Generation (tok/s) |
|---|---|---:|---:|---:|
| `flash-next-strata` | 0.2.20 (control 0.1.66, engine 0.1.65) | 1,260.1 | 4.59 | 65.5 |
| `flash-next-strata` | control and engine 0.1.67 (two runs) | 1,167.0 / 1,171.6 | 4.97 / 4.94 | 57.8 / 58.7 |
| `flash-next-strata` | control 0.1.67, engine 0.1.65 (kept, two runs) | 1,269.4 / 1,270.5 | 4.55 / 4.54 | 69.0 / 66.8 |
| `inkling-strata` | 0.1.66 | 1,970.7 | 4.85 | 66.0 |
| `inkling-strata` | 0.1.67 | 2,129.3 | 3.44 | 66.9 |
| `hy4-flash-strata` | 0.1.66 | 212.2 | 26.53 | 24.0 |
| `hy4-flash-strata` | 0.1.67 | 213.3 | 26.41 | 23.7 |
| `deepseek-unsloth-strata` | control 0.1.66 (engine 0.1.59) | 28.0 (prompt reuse) | 5.92 | 12.2 |
| `deepseek-unsloth-strata` | control 0.1.67 (engine 0.1.59) | 28.3 (prompt reuse) | 5.98 | 12.3 |

- **Inkling:** prompt reading 8% faster and first token 1.4 s sooner; generation unchanged.
- **Flash-Next on engine 0.1.67:** passes, but generation is 11-12% lower and prompt reading 7% lower on two runs, the same pattern as 0.1.66. Engine 0.1.65 under control 0.1.67 runs at the old speed, so the preset stays on the 0.2.19 Qwen package. The #6713 fix matters only for the retired UD-IQ4_XS entry; the #6776 accuracy fix is not taken for now.
- Serving left idle and unloaded, both GPUs at 1 MiB, unlock VERIFIED.
