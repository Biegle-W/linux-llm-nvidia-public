# Current state — November 22, 2026

Snapshot of what is live. Replace facts here when they change; dated detail goes in evidence docs and [HISTORY.md](HISTORY.md).

## Enabled models (`/v1/models`)

| API id | Model / quant | Engine | Context | Weights (location, size) |
|---|---|---|---:|---|
| `qwen27b-hyperqwen` | Qwen3.8-27B AutoRound INT4 (fast heads, INT8 embedding) | HyperQwen-vLLM (vLLM 0.33.0) | 86,016 | `models/engine-tests/qwen38-27b-hyperqwen-fast`, SATA, 16 GB (shared with SGLang) |
| `qwen27b-sglang` | same checkpoint | SGLang | 57,344 | same as above |
| `flash-next-strata` | Qwen3.8-Flash-Next GSQ-RCO IQ3_XXS | Strata 0.2.18 (engine 0.1.64) + MTP; layers 0-28 on the 3080, 29-47 + head on the 3080 Ti, stage-trimmed | 131,072 | `models/strata/models/IQ3_XXS`, NVMe, 76 GB |
| `flash-next-iq4xs-strata` | Qwen3.8-Flash-Next Unsloth UD-IQ4_XS-v31 | same Strata engine as `flash-next-strata` + MTP; automatic split (layers 0-19 on the 3080, 20-47 on the 3080 Ti), KV streaming | 131,072 | `models/strata/models/unsloth-UD-IQ4_XS-v31`, NVMe, 94 GB |
| `glm-maya` | GLM-5.3-Flash Maya-S24 | Maya 1.1.72 | 65,536 | `models/maya/Maya-S24`, NVMe, 98 GB |
| `deepseek-maya` | DeepSeek-V4.1-Flash-1017 UD-IQ1_S (Unsloth Dynamic3.1) | Maya 1.1.72 | 32,768 | `models/unsloth/deepseek-v41-1017-dynamic31-8a6ec9cf/UD-IQ1_S`, NVMe shards 1-4 (122 GB) + SATA shard 5 (symlinked), 233 GB total (shared) |
| `deepseek-unsloth-strata` | same checkpoint | Strata 0.2.13 (engine 0.1.59, DSV4.1 build); frozen, later Strata versions do not run DeepSeek | 32,768 | same as above |
| `bolt-llamacpp` | NVIDIA Nemotron-3.5 Bolt 74B-A9B native IQ2 | llama.cpp main `19bc41d` (1.0.0-dev), 8 GiB RAM prompt cache | 163,840 | `models/engine-tests/bolt-iq2`, SATA |

Every entry runs under 87.77 GiB soft / 89.77 GiB hard worker RAM with 2 GiB host reserve. ComfyUI image (Qwen Turbo, FLUX3 Klein, MiniMax H3 Image) and video (Wan 2.2 5B, LTX 2.3 Mesh) entries run from desktop launchers; see [COMFY-VIDEO-HD-ENTRIES-20261105.md](evidence/COMFY-VIDEO-HD-ENTRIES-20261105.md).

Last long-prompt speeds for `flash-next-strata` (Nov 7 on Strata 0.2.11, no cache reuse; later engines have short-check figures only): ~5.7K-token tool prompt 1,243 prefill / 146 decode tok/s; ~24K prompt 2,375 / 108; writing ~124 tok/s. Strata 0.2.12 qualification (Nov 8, single short ~5.6K-token DSH tool call, old to new): `flash-next-strata` 934 to 1,046 prefill, 68 to 86 decode tok/s, TTFT 6.5 to 5.5 s; `deepseek-unsloth-strata` 83 to 86 prefill, 11.8 to 11.7 decode tok/s, TTFT 68 to 66 s (DeepSeek speed not strictly comparable: prompt cache reuse). Both answered a router smoke check correctly afterwards. Other entries: [ALL-MODELS-RERUN-20261105.md](evidence/ALL-MODELS-RERUN-20261105.md).

## Measured quality (November 10–18)

390 public-benchmark items per entry, thinking off as served, one generation per item. All eight text entries are measured; `flash-next-iq4xs-strata` was added on November 18 from its trial run outside the router. No entry is separated from the one next to it; the two Qwen 27B engines score the same, and so do the two DeepSeek engines. Full result list with speeds and guards: [QUALITY-BENCHMARK-20261111.md](evidence/QUALITY-BENCHMARK-20261111.md).

| Rank | API id | Macro (95% interval) | MMLU-Pro | AIME 2025 | LiveCodeBench | BFCL single | BFCL multi |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | `deepseek-unsloth-strata` | 73.0% (67.3–78.4) | 86.7% | 76.7% | 55.0% | 90.0% | 56.7% |
| 2 | `deepseek-maya` | 72.4% (66.8–77.9) | 88.6% | 80.0% | 51.7% | 88.3% | 53.3% |
| 3 | `qwen27b-sglang` | 68.1% (62.3–73.9) | 85.7% | 66.7% | 50.0% | 91.7% | 46.7% |
| 4 | `qwen27b-hyperqwen` | 68.0% (62.3–73.7) | 81.9% | 60.0% | 40.0% | 91.7% | 66.7% |
| 5 | `flash-next-iq4xs-strata` | 65.5% (60.2–70.8) | 87.6% | 80.0% | 58.3% | 78.3% | 23.3% |
| 6 | `flash-next-strata` | 62.0% (56.5–67.5) | 85.2% | 73.3% | 58.3% | 73.3% | 20.0% |
| 7 | `glm-maya` | 57.2% (52.1–62.3) | 86.2% | 6.7% | 55.0% | 91.7% | 46.7% |
| 8 | `bolt-llamacpp` | 53.9% (48.7–59.4) | 76.2% | 50.0% | 33.3% | 90.0% | 20.0% |

## Recent changes (newest first)

- **Nov 22:** quality testing moved to a short tool-use test: 49 items in 15 minutes for smaller models, 55 items in 1 hour at most for larger ones, run only for new models and new weights. Existing entries are scored on it from their stored records, with no reruns: Qwen 27B 66.0 and 61.7, DeepSeek 64.7 and 63.5, GLM 60.4, Bolt 53.6, Flash-Next 47.4 and 40.6 (out of 100; one run separates only differences of 20-25 points). The 390-item ranking above stays as measured and is no longer extended. [QUALITY-FAST-TEST-PLAN.md](QUALITY-FAST-TEST-PLAN.md)
- **Nov 22:** the Inkling 2 Mini quality rerun on Unsloth's build with larger token limits was stopped by the owner at 111 of 390 items; the first run stands. On those 111 MMLU-Pro items the rerun had 97 correct against 82 in the first run. [INKLING2-MINI-TRIAL-20261121.md](evidence/INKLING2-MINI-TRIAL-20261121.md)
- **Nov 21 (afternoon):** second update of the day, asked for so the backends support Inkling 2 Mini: Maya 1.1.71 and then 1.1.72, Strata 0.2.18 and llama.cpp main `19bc41d` installed by hand. All 15 short checks pass at unchanged speed. `bolt-llamacpp` now runs a main-branch commit ahead of the stable release 1.0.0, because Inkling support exists only there. [ENGINE-UPDATES-20261121B-MAYA-1172-STRATA-0218-LLAMACPP-MAIN.md](evidence/ENGINE-UPDATES-20261121B-MAYA-1172-STRATA-0218-LLAMACPP-MAIN.md)
- **Nov 21:** Inkling 2 Mini (Thinking Machines, 26B looped MoE) trial measured; it is not a router model. Quality: 60.0% macro on the 390 items with thinking on (cannot be turned off), which would sit seventh of nine, between `flash-next-strata` and `glm-maya`; 95 of 131 misses are answers cut off at the token limit, nearly all while still reasoning, so it is not like for like and not in the ranking table. Speed: 24-27 tok/s on production llama.cpp (12.8 after a 19.6K prompt), 41-44 tok/s on Unsloth's llama.cpp build, 57-71 on short answers with its DSpark drafter but 38 on free writing. [INKLING2-MINI-TRIAL-20261121.md](evidence/INKLING2-MINI-TRIAL-20261121.md)
- **Nov 21:** Maya 1.1.70 and Strata 0.2.17 installed by hand. All five affected profiles pass. Maya is unchanged in speed. Strata brings a new engine (0.1.63, Strata's own code) to both Flash-Next entries: prompt reading is 9% faster, and **`flash-next-strata` generates about 20% slower in the short check (64.5-67.5 against 81-85 tok/s)** because upstream now leaves the route tail skip off for quality; `"env": {"STRATA_ROUTE_TAIL_SKIP": "7"}` in its preset would turn it back on (owner's decision, not made). ComfyUI `v0.46.0` is available and not installed. [ENGINE-UPDATES-20261121-MAYA-1170-STRATA-0217.md](evidence/ENGINE-UPDATES-20261121-MAYA-1170-STRATA-0217.md)
- **Nov 18:** Maya 1.1.67 installed by hand for `glm-maya` and `deepseek-maya`. Both pass at the same speed. It fixes GLM silently computing an expert with another expert's weights when part of the experts sit in RAM (this server's case), so `glm-maya` answers can differ from 1.1.65; DeepSeek's drafter experts are now placed by use. [ENGINE-UPDATES-20261118-MAYA-1167.md](evidence/ENGINE-UPDATES-20261118-MAYA-1167.md)
- **Nov 18:** `flash-next-iq4xs-strata` added: Flash-Next in the larger Unsloth UD-IQ4_XS-v31 quant, next to the IQ3_XXS entry (owner's choice to keep both; `flash-next-strata` is unchanged and stays the default). On 390 quality items it scored 65.5% against 62.0% for IQ3_XXS, a lead that is not statistically established, and it is slower: about 1,600 against 2,200 tok/s reading a 20K-token prompt and 81-94 against 109-128 tok/s writing on short prompts. Through the router it passed the short checks, a 113K-token retrieval, the DSH tool round trip and a fresh reload. Launch: `./scripts/start_model.sh qwen-iq4xs`. [FLASH-NEXT-IQ4XS-PROFILE-20261118.md](evidence/FLASH-NEXT-IQ4XS-PROFILE-20261118.md), [FLASH-NEXT-IQ4XS-TRIAL-20261117.md](evidence/FLASH-NEXT-IQ4XS-TRIAL-20261117.md)
- **Nov 16:** Strata 0.2.15 installed by hand for `flash-next-strata` (control 0.1.61; the engine stays 0.1.60). Same speed. It brings two server fixes: boolean tool arguments are returned as booleans, and requests arriving during a shutdown are refused cleanly. Also from Nov 16: every generated image and clip is now kept in `assets/samples/comfy/`. [ENGINE-UPDATES-20261116-STRATA-0215.md](evidence/ENGINE-UPDATES-20261116-STRATA-0215.md)
- **Nov 15:** MiniMax H3 Image added as a third image model (`minimax-h3-image`, launcher "ComfyUI MiniMax H3 Image"): 3-bit GGUF denoiser fully on the 3080 Ti, VAE on the 3080, and the 27 GB text encoder kept in system RAM and streamed through the 3080. That last part is an owner-approved exception to the all-on-GPU rule, for this model's encoder only. 1024², 2048² and 4096² pass (6, 13.5 and 58 s of sampling). The licence has territory limits. [MINIMAX-H3-IMAGE-20261115.md](evidence/MINIMAX-H3-IMAGE-20261115.md)
- **Nov 15:** Maya 1.1.65 and Strata 0.2.14 installed by hand after a review of the upstream fixes. All four profiles pass. Flash-Next reads prompts 4-5% faster; its generation measured 79-84 tok/s against 87 before (warning, inside the spread of earlier days). **Strata 0.2.14 no longer runs DeepSeek**, so `deepseek-unsloth-strata` stays on its 0.2.13 runtime and gets no further Strata updates. [ENGINE-UPDATES-20261115-MAYA-1165-STRATA-0214.md](evidence/ENGINE-UPDATES-20261115-MAYA-1165-STRATA-0214.md)

Entries before November 15 are in [HISTORY.md](HISTORY.md).

## Open items

- **Inkling 2 Mini trial** is measured but undecided. Unsloth's llama.cpp build runs it at 41-44 tok/s, 1.7 to 3.2 times production llama.cpp, from a trial folder only; serving it would mean a second llama.cpp runtime or waiting for mainline to catch up. Untested: full quality on that build (a rerun with larger token limits was stopped at 111 items), the mainline two-GPU placement fix, Maya's unsupported two-GPU switch. The trial weights (33 GB) are in `models/engine-tests/inkling2-mini-trial`. Keeping it as a router model or deleting it is the owner's call. [INKLING2-MINI-TRIAL-20261121.md](evidence/INKLING2-MINI-TRIAL-20261121.md)
- **`bolt-llamacpp` runs llama.cpp main `19bc41d`**, not a tagged release. Move it to the next stable release that contains Inkling 2 Mini support; until then the upstream check reports 1.0.0 as current, which is older than what is installed.
- **MiniMax H3 Image** has only the short square-image checks: no image editing, one non-square size, and the saved workflow has not been opened in the browser UI. 4096² leaves about 0.5 GiB on the 3080 Ti. [MINIMAX-H3-IMAGE-20261115.md](evidence/MINIMAX-H3-IMAGE-20261115.md)
- **`deepseek-unsloth-strata` is frozen on Strata 0.2.13.** Upstream dropped DeepSeek in 0.2.14, so this profile gets no more engine fixes; `deepseek-maya` runs the same checkpoint on an engine that is still updated. Keeping or retiring the Strata profile is the owner's call. [ENGINE-UPDATES-20261115-MAYA-1165-STRATA-0214.md](evidence/ENGINE-UPDATES-20261115-MAYA-1165-STRATA-0214.md)
- **`glm-maya`** skipped the tool call once in four short checks on Maya 1.1.61; on 1.1.65 it called the tool in 3 of 3 on 1.1.67 in 2 of 2 on 1.1.70 in 1 of 1, on 1.1.71 in 1 of 1 and on 1.1.72 in 1 of 1. Keep watching in the daily checks. Maya 1.1.67 fixes wrong expert weights on this kind of setup; its quality score has not been re-run on the fixed engine.
- **ComfyUI 0.45.0** has only the short 1024² image and 512x288 video checks for the earlier image and video models; their 2048², 720p and 1080p sizes were not re-run. MiniMax H3 Image was measured on 0.45.0 at 2048² and 4096². The Raylight trial stage gives a different clip than on 0.44.0 (valid, same speed; cause not investigated). [ENGINE-UPDATES-20261112-MAYA-1160-COMFYUI-045.md](evidence/ENGINE-UPDATES-20261112-MAYA-1160-COMFYUI-045.md)
- **Strata 0.2.18, Maya 1.1.72, llama.cpp main `19bc41d`, HyperQwen vLLM 0.33.0** have only short-check numbers; no long-context or sustained run yet. The Nov 7 Flash-Next figures above are still from 0.2.11. Strata 0.2.17 changed the engine and turned the route tail skip off for `flash-next-strata`, so only its short-check speed has been re-measured since (same speed); its long-prompt speed figures and its quality score (measured on engine 0.1.60 with the skip on) have not.
- **DSH web app** still lists `flash-next-iq1m-strata` until `nvidia-dsh.service` restarts (its config is already regenerated; the router returns 404 for that id).
- **`flash-next-iq4xs-strata`** has one near-window request (113K tokens) and a 53-second writing run; nothing at the very top of the window and no multi-hour run. It must be updated together with `flash-next-strata` on every Strata engine update (the launch is refused if the two presets name different engines). Its first router session swapped 1.7 GiB while loading; the second did not.
- **Quality benchmark gaps:** none of the eight ranked entries was run with thinking on (only the Inkling 2 Mini trial, which cannot turn it off); samples are screening-size. From November 22 new models get only the short tool-use test, which does not measure knowledge, maths or coding, and has not yet been run live. [QUALITY-FAST-TEST-PLAN.md](QUALITY-FAST-TEST-PLAN.md)
- **`data/`** holds many private trial and evidence directories (all gitignored). Pruning them needs the owner's OK.
- Possible follow-up from Nov 7 research: the DeepSeek entries still use the automatic layer split and might gain from the same hand-set split sweep that helped Flash-Next.

## Idle state

Router idle, no worker loaded, both GPUs at 1 MiB, no `data/GPU-LOCK`, GPU unlock VERIFIED.
