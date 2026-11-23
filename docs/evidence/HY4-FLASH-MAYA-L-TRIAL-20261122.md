# Hy4-Flash 220B on Project Maya's engine (Maya-L), both cards: trial — November 22, 2026

**Status: trial only, not adopted. `hy4-flash-strata` stays the Hy4 entry.** The owner asked for Maya's Hy4-Flash engine to be tried on both cards, to see whether it frees RAM and VRAM and lifts the context limit of the Strata entry.

## Result in one table

| | Maya-L on Maya 1.1.74, both cards | SQ-96 on Strata, 12 GB card only (the entry) |
|---|---:|---:|
| Generation, 2,000-token answers | 11.0-12.8 tok/s | 18.6-22.0 tok/s |
| Generation, short follow-ups | 14-21 tok/s | 26-31 tok/s |
| Prompt reading, 8K tokens | 201 tok/s (91 with a 1,024-token chunk) | 279 tok/s |
| Prompt reading, 16K tokens | 263 tok/s (129) | 270 tok/s |
| Prompt reading, 127.9K tokens at 128K context | 163 tok/s (789 s) | 272 tok/s (471 s) |
| Follow-up after a long prompt | 0.9-2.3 s | 0.7-0.9 s |
| Routed experts held on the GPUs | 1-9% of 20,992 | cache on one card |
| Memory used by the model | 80-83 GiB, as file cache of the mapped model file | 79.6 GiB |
| Start to ready | 12-14 minutes observed (the load itself 24-49 s) | 25-40 s |
| VRAM | 19.9-20.3 GB over both cards; 0.6-1.0 GB free on each | 11.2-11.4 GB on card 0 |

Maya on two cards is slower at writing on this server, does not free RAM, and starts far more slowly. It does hold 128K context without the Strata entry's picture limit being tested (pictures were off in this trial).

## Why it is not faster here

- **The second card adds little.** Maya splits the layers (0-21/23 on the 3080 Ti, the rest on the 3080). After the dense parts, context memory and prompt buffers, the two cards together hold only 1-9% of the routed experts. Everything else is computed on 24 CPU threads.
- **RAM is not freed.** Maya maps the 89.5 GB model file and computes the CPU experts from the file cache. With 91.8 GiB of RAM the mapped file takes 80-83 GiB, the same as Strata's copy in RAM. The 63.4 GB table is read from the SATA SSD a row at a time.
- **The CPU path is the limit.** Generation stayed at 11-12 tok/s with a 1,024, 2,048 or 4,096-token prompt chunk and with 1%, 4% or 9% of the experts in VRAM. Maya's faster 4-bit CPU copies exist only for its 2-bit build (Maya-XS), not for Maya-L.

## Files and setup

- **Files** (Hugging Face `peasantsmith/Hy4-Flash-Maya-GGUF`, the revision and hashes pinned in Maya's `tools/hy4/download.json`), in `models/engine-tests/hy4-flash-maya-l/` on the SATA SSD, 162.5 GB: model 89.51 GB, table 63.36 GB, picture file 0.78 GB, DFly2 drafter 0.90 GB, MTP block 7.49 GB. All five matched the pinned sizes and SHA-256.
- **Engine:** `maya-hy4` from the installed Maya 1.1.74 build (`runtimes/project-maya/build/`), no rebuild. The index of the files (4.8 MB) is in `data/hy4-maya-20261122/pack`; it points at the files in place.
- **Server:** Maya's own `serve/server.py` on port 10053 as a transient unit, router idle, measurement and state files kept under `data/hy4-maya-20261122/state/`. Pictures off, drafting off, thinking off unless asked.
- A source review by Codex (GPT-6.2 Astra) prepared the launch; its memory estimate (68-70 GiB of experts on the CPU side) matched what was seen.

## Runs

| Run | Settings | Notes |
|---|---|---|
| a32k | 32K, chunk 1,024, soft memory cap 87.77 GiB | 9% of experts in VRAM. The mapped file pressed on the soft cap (5,901 throttle events). Generation 11.3-12.8 tok/s, 8K prompt at 91 tok/s. |
| b32k | 32K, Maya's defaults (chunk 4,096), no soft cap | 1% of experts in VRAM, no throttling. Generation 11.0-11.7 tok/s, 8K prompt 201 tok/s, 16K prompt 263 tok/s. Ready after 852 s. |
| c128k | 128K, defaults (chunk 2,048), no soft cap | 4% of experts in VRAM. Generation 11.5-12.0 tok/s; 127,867-token prompt read at 163 tok/s with both hidden codes returned; 0.7-0.8 GB free on each card throughout. Ready after 724 s. |

Arithmetic, JSON, a tool call with follow-up, thinking on request and prompt reuse between turns all worked in every run.

## Not done

- Pictures, the MTP and DFly2 drafters, Maya-M or Maya-XS (smaller, lower quality), a single-card Maya run, the short tool-use test.
- The long start times were not broken down; the first start includes a one-time route measurement (152-301 s), and the server restarted the engine during two starts.
- The 162.5 GB of Maya-L files are still on the SATA SSD. Removing them is the owner's decision.
