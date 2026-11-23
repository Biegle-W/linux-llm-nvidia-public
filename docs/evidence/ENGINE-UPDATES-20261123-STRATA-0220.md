# Strata 0.2.20 installed by hand; Inkling 2 Mini retested on its new engine — November 23, 2026

At the owner's request Strata was updated from v0.2.19 to v0.2.20 (`a34979fc94f3`, signed feed sequence 132) and Inkling 2 Mini on Strata's own engine was tested again.

| Component | From | To | Result |
|---|---|---|---|
| Control (serves every Strata entry) | 0.1.65 | 0.1.66 | **promoted**; the local idle-reservation patch applied unchanged (one block) |
| `strata-hy4` (`hy4-flash-strata`) | 0.1.64 | 0.1.66 (`2e87c08db18a`) | **promoted** |
| Qwen engine (`flash-next-strata`, `flash-next-iq4xs-strata`) | 0.1.65 | 0.1.66 tried, **kept at 0.1.65** | 0.1.66 broke `flash-next-iq4xs-strata` and slowed `flash-next-strata`; both run engine 0.1.65 under control 0.1.66 |
| `strata-inkling` | 0.1.65 | 0.1.66 installed for the trial | no router entry (owner's decision) |
| DeepSeek on Strata | v0.2.13 | unchanged | frozen |

## Review before the install

A source review of v0.2.19..v0.2.20 (codex) found: fused Unsloth IQ3_XXS/IQ4_XS expert paths and sm_86 fixes for the Qwen engine; a new adaptive expert-cache policy; Linux startup that keeps the PLE shard in page cache; for Hy4 a new KV planner (the explicit 131,072-slot reservation still wins) and CPU/PCIe miss sharing; for Inkling a CUDA layer split that works without P2P (`--layer-split auto`, `[cuda-ls N stages]`), host KV offload (`--kv-offload`) and the fix for the expert-parallel crash seen on November 22. The local idle patch was dry-run on the new `serve/server.py` first. All four packages were verified against the signed feed with upstream's signing code and staged under `runtimes/strata-manual/0.2.20-20261123/`. Pre-images and rollback: `data/strata-update-20261123/`.

## Short DSH checks

One profile at a time, GPUs idle before and after.

| Profile | Version | Prompt reading (tok/s) | First token (s) | Generation (tok/s) |
|---|---|---:|---:|---:|
| `flash-next-strata` | 0.2.19 | 1,268.8 | 4.55 | 67.5 |
| `flash-next-strata` | control and engine 0.1.66 (two runs) | 1,167.1 / 1,168.3 | 4.96 / 4.95 | 59.2 / 57.8 |
| `flash-next-strata` | control 0.1.66, engine 0.1.65 (kept) | 1,273.3 | 4.53 | 69.5 |
| `flash-next-iq4xs-strata` | 0.2.19 | 967.1 | 6.42 | 44.2 |
| `flash-next-iq4xs-strata` | control and engine 0.1.66 | fails | | |
| `flash-next-iq4xs-strata` | control 0.1.66, engine 0.1.65 (kept) | 988.6 | 6.29 | 43.5 |
| `hy4-flash-strata` | control 0.1.65, engine 0.1.64 | 205.8 | 27.25 | 27.0 |
| `hy4-flash-strata` | control and engine 0.1.66 | 211.9 | 26.53 | 25.5 |

- **IQ4_XS on engine 0.1.66:** the first start, right after `flash-next-strata`, was ended by systemd-oomd during loading (52 GB peak). The second start loaded, then failed on the first prompt: `verify: layer 0 never rang (operation not supported on global/shared address space)`. Engine 0.1.65 under control 0.1.66 passes. The new Unsloth IQ4_XS CUDA path (commit `3d69a1d3b`) is the likely cause; not reported upstream yet.
- **`flash-next-strata` on engine 0.1.66:** 12-14% slower generation on two runs and 8% slower prompt reading, so it stays on 0.1.65 with IQ4_XS (both presets must use the same engine).
- **Hy4:** generation 5.6% lower on one run, within the promotion rule.

## Inkling 2 Mini on `strata-inkling` 0.1.66

SQ-10 pack (10.47 GB, re-downloaded from the pinned revision `04996a1e`, SHA-256 matched), trial server on port 10054, drafter off, one slot, text only. The test prompt mirrors the web client: a 9.5K-token system prompt with 25 tools and `max_tokens` 4,096. Scripts and logs: `data/inkling-strata-20261123/`.

| Setting | Web-client request (9.5K prompt + tools) | Long recall | Generation | Lowest free VRAM (3080 Ti / 3080) |
|---|---|---|---:|---|
| 3080 Ti alone, 16K, `--kv-offload auto` | tool call and follow-up correct | 15.5K correct | 41-47 tok/s long, 81 short | 349 MiB / — |
| both cards, `--layer-split auto`, 16K | correct | 15.5K correct | 65-71 | 4,421 / 4,036 MiB |
| both cards, 32K and 64K | correct | 20.2K correct | 65-71 | 4,197 / 4,004 MiB |
| both cards, 128K | — | 59.8K and 120.6K correct | 62 and 55 | 1,509 / 3,620 MiB |

- Both cards load as `[cuda-ls 2 stages]`, experts 1,152 + 1,920 on the GPUs, none in RAM; the context memory grows in 8K steps as needed. Prompt reading 1,890-1,990 tok/s at 9-20K, 1,595 at 60K and 1,286 at 120K (94 s).
- This beats `inkling-llamacpp` (41-44 tok/s at 32K) by about 1.5x in generation and 2x+ in prompt reading, at four times the context.
- Not done: the router's own checks, the real web-client short check and the short tool-use quality test need a router entry, which the owner decides on.
