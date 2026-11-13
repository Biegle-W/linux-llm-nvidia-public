# Current state — November 11, 2026

Snapshot of what is live. Replace facts here when they change; dated detail goes in evidence docs and [HISTORY.md](HISTORY.md).

## Enabled models (`/v1/models`)

| API id | Model / quant | Engine | Context | Weights (location, size) |
|---|---|---|---:|---|
| `qwen27b-hyperqwen` | Qwen3.8-27B AutoRound INT4 (fast heads, INT8 embedding) | HyperQwen-vLLM (vLLM 0.33.0) | 86,016 | `models/engine-tests/qwen38-27b-hyperqwen-fast`, SATA, 16 GB (shared with SGLang) |
| `qwen27b-sglang` | same checkpoint | SGLang | 57,344 | same as above |
| `flash-next-strata` | Qwen3.8-Flash-Next GSQ-RCO IQ3_XXS | Strata 0.2.13 (engine 0.1.59) + MTP; layers 0-28 on the 3080, 29-47 + head on the 3080 Ti, stage-trimmed | 131,072 | `models/strata/models/IQ3_XXS`, NVMe, 76 GB |
| `glm-maya` | GLM-5.3-Flash Maya-S24 | Maya 1.1.60 | 65,536 | `models/maya/Maya-S24`, NVMe, 98 GB |
| `deepseek-maya` | DeepSeek-V4.1-Flash-1017 UD-IQ1_S (Unsloth Dynamic3.1) | Maya 1.1.60 | 32,768 | `models/unsloth/deepseek-v41-1017-dynamic31-8a6ec9cf/UD-IQ1_S`, NVMe shards 1-4 (122 GB) + SATA shard 5 (symlinked), 233 GB total (shared) |
| `deepseek-unsloth-strata` | same checkpoint | Strata 0.2.13 (engine 0.1.59, DSV4.1 build) | 32,768 | same as above |
| `bolt-llamacpp` | NVIDIA Nemotron-3.5 Bolt 74B-A9B native IQ2 | llama.cpp 1.0.0, 8 GiB RAM prompt cache | 163,840 | `models/engine-tests/bolt-iq2`, SATA |

Every entry runs under 87.77 GiB soft / 89.77 GiB hard worker RAM with 2 GiB host reserve. ComfyUI image (Qwen Turbo, FLUX3 Klein) and video (Wan 2.2 5B, LTX 2.3 Mesh) entries run from desktop launchers; see [COMFY-VIDEO-HD-ENTRIES-20261105.md](evidence/COMFY-VIDEO-HD-ENTRIES-20261105.md).

Latest measured speeds for `flash-next-strata` (Nov 7 on Strata 0.2.11, no cache reuse): ~5.7K-token tool prompt 1,243 prefill / 146 decode tok/s; ~24K prompt 2,375 / 108; writing ~124 tok/s. Strata 0.2.12 qualification (Nov 8, single short ~5.6K-token DSH tool call, old to new): `flash-next-strata` 934 to 1,046 prefill, 68 to 86 decode tok/s, TTFT 6.5 to 5.5 s; `deepseek-unsloth-strata` 83 to 86 prefill, 11.8 to 11.7 decode tok/s, TTFT 68 to 66 s (DeepSeek speed not strictly comparable: prompt cache reuse). Both answered a router smoke check correctly afterwards. Other entries: [ALL-MODELS-RERUN-20261105.md](evidence/ALL-MODELS-RERUN-20261105.md).

## Measured quality (November 10–12)

390 public-benchmark items per entry, thinking off as served, one generation per item. All seven text entries are measured. No entry is separated from the one next to it; the two Qwen 27B engines score the same, and so do the two DeepSeek engines. Full result list with speeds and guards: [QUALITY-BENCHMARK-20261111.md](evidence/QUALITY-BENCHMARK-20261111.md).

| Rank | API id | Macro (95% interval) | MMLU-Pro | AIME 2025 | LiveCodeBench | BFCL single | BFCL multi |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | `deepseek-unsloth-strata` | 73.0% (67.3–78.4) | 86.7% | 76.7% | 55.0% | 90.0% | 56.7% |
| 2 | `deepseek-maya` | 72.4% (66.8–77.9) | 88.6% | 80.0% | 51.7% | 88.3% | 53.3% |
| 3 | `qwen27b-sglang` | 68.1% (62.3–73.9) | 85.7% | 66.7% | 50.0% | 91.7% | 46.7% |
| 4 | `qwen27b-hyperqwen` | 68.0% (62.3–73.7) | 81.9% | 60.0% | 40.0% | 91.7% | 66.7% |
| 5 | `flash-next-strata` | 62.0% (56.5–67.5) | 85.2% | 73.3% | 58.3% | 73.3% | 20.0% |
| 6 | `glm-maya` | 57.2% (52.1–62.3) | 86.2% | 6.7% | 55.0% | 91.7% | 46.7% |
| 7 | `bolt-llamacpp` | 53.9% (48.7–59.4) | 76.2% | 50.0% | 33.3% | 90.0% | 20.0% |

## Recent changes (newest first)

- **Nov 13:** llama.cpp 1.0.0 installed by hand for `bolt-llamacpp` (from 0.9.0). The short check passes; prompt reading rose from 501.5 to 673 tok/s on two runs and generation is unchanged. No launcher flag changed. [ENGINE-UPDATES-20261113-LLAMACPP-100.md](evidence/ENGINE-UPDATES-20261113-LLAMACPP-100.md)
- **Nov 12:** `deepseek-maya` added to the quality benchmark: 72.4% macro against 73.0% for the same checkpoint on Strata (difference −5.2 to +4.0 points, not separated). All seven text entries are now measured. [QUALITY-BENCHMARK-20261111.md](evidence/QUALITY-BENCHMARK-20261111.md)
- **Nov 12:** Ubuntu installed kernel 7.0.0-43 by itself at 06:52; the GPU unlock check read "pending reboot verification" until the owner rebooted at 13:09, after which it read VERIFIED again. No GPU work was started in between.
- **Nov 12:** `qwen27b-sglang` added to the quality benchmark: 68.1% macro against 68.0% for the same checkpoint on HyperQwen (difference −6.4 to +6.3 points, not separated). [QUALITY-BENCHMARK-20261111.md](evidence/QUALITY-BENCHMARK-20261111.md)
- **Nov 11-12:** Maya 1.1.60 and ComfyUI 0.45.0 installed by hand at the owner's request. Both Maya profiles and six ComfyUI image and video checks pass at the same speed as before; the midday `glm-maya` slowdown on 1.1.59 did not repeat. Two new cloud sign-in options in the ComfyUI page are switched off in the launcher. [ENGINE-UPDATES-20261112-MAYA-1160-COMFYUI-045.md](evidence/ENGINE-UPDATES-20261112-MAYA-1160-COMFYUI-045.md)
- **Nov 11:** Maya 1.1.59 installed by hand (released the same day as the 1.1.58 install). Both Maya profiles pass the short check; `glm-maya` generation measured 13.2 and 12.3 tok/s against 14.4 on 1.1.58, a warning under the promotion rule. [ENGINE-UPDATES-20261111-MAYA-1159.md](evidence/ENGINE-UPDATES-20261111-MAYA-1159.md)
- **Nov 11:** repository audit: stale docs and registry notes corrected, a unit test stopped writing into the live router folder, the updater installer no longer enables the retired timer. Nothing served changed; removals are left for the owner. [REPO-AUDIT-20261111.md](evidence/REPO-AUDIT-20261111.md)
- **Nov 11:** Maya 1.1.58 installed by hand; both Maya profiles pass the short check at the same speed as 1.1.57. HyperQwen pin moved to `3d6c954` with no rebuild (nothing installed changed). [ENGINE-UPDATES-20261111.md](evidence/ENGINE-UPDATES-20261111.md)
- **Nov 11:** first measured quality ranking of the text entries: DeepSeek on Strata 73.0%, Qwen 27B on HyperQwen 68.0%, Flash-Next 62.0%, GLM 57.2%, Bolt 53.9% (macro over MMLU-Pro, AIME 2025, LiveCodeBench and BFCL subsets). [QUALITY-BENCHMARK-20261111.md](evidence/QUALITY-BENCHMARK-20261111.md)
- **Nov 10:** launch tuning adopted: Maya GLM checkpoint interval 65,536 (cold 37K-token prompt 38.3 s → 30.7 s to first token) and Flash-Next Strata direct table reads (load about 10 s faster, 26.8 GiB of RAM freed). [LAUNCH-TUNING-20261110.md](evidence/LAUNCH-TUNING-20261110.md)
- **Nov 9:** nightly updater retired (timer disabled); engine updates are now installed by hand with a short DSH check before and after ([runbook](ENGINE-UPDATE-RUNBOOK.md)). Installed the same day: Strata 0.2.13, HyperQwen `9268d8d` (vLLM 0.33.0), Maya 1.1.57, all at parity. [ENGINE-UPDATES-HANDS-ON-20261109.md](evidence/ENGINE-UPDATES-HANDS-ON-20261109.md). That evening HyperQwen was updated again to `80cf059` (still vLLM 0.33.0), also at parity. [ENGINE-UPDATES-20261109-HYPERQWEN-80cf059.md](evidence/ENGINE-UPDATES-20261109-HYPERQWEN-80cf059.md)
- **Nov 9:** the updater treats held pushes (someone else's unpushed commits or edits) as warnings, exit 0, instead of failures; 3 held runs in a row fail the unit. See `last_deferral` in `data/daily-update/state.json`.
- **Nov 9:** GPU peer access stays off by design: the 3080 Ti and 3080 run on the board's CPU PCIe x8/x8 bifurcation with the stock driver and no P2P. Launchers now remove `GGML_CUDA_P2P` instead of setting it to `0`, because ggml/llama.cpp treated any value, including `0`, as on. NCCL stays host-staged (`NCCL_P2P_DISABLE=1`).
- **Nov 8:** unused-weights tracker added (`scripts/weights_tracker.py`, report in `data/weights-tracker/`). NVMe 52% used (464 GB free), SATA 22% (784 GB free); 6.9 GB of unused weights, all on NVMe (build fixtures and the DeepSeek vision tower); nothing deleted. [STORAGE-STATUS-20261108.md](evidence/STORAGE-STATUS-20261108.md)
- **Nov 8:** docs reorganized: dated evidence moved to `docs/evidence/` (topic index in [README.md](README.md)); `network/README.md` and [MAINTAINED-PROFILES.md](MAINTAINED-PROFILES.md) rewritten as short reference pages, old logs archived.
- **Nov 8:** Strata 0.2.12 (`146df3c`, engine 0.1.58) promoted by a manual updater run after the owner cleared its old-gate rejection; Flash-Next ~+26% decode on the short check, DeepSeek unchanged; K=29 split kept. [DAILY-ENGINE-UPDATES.md](DAILY-ENGINE-UPDATES.md)
- **Nov 8:** repo cleanup: this file, `AGENTS.md` and `README.md` rewritten short; the old logs moved to [HISTORY.md](HISTORY.md); dead IQ1_S code removed.
- **Nov 8:** Flash-Next IQ1_M retired and deleted (69.6 GB); tied IQ3_XXS on quality and speed. Maya's PLE parity build now reads its table from IQ3_XXS shard 2. [FLASH-IQ1M-RETIREMENT-20261108.md](evidence/FLASH-IQ1M-RETIREMENT-20261108.md)
- **Nov 7:** update gate changed to "promote unless it breaks". [DAILY-ENGINE-UPDATE-POLICY.md](DAILY-ENGINE-UPDATE-POLICY.md)
- **Nov 7:** Flash-Next hand-set layer split K=29 with stage trim (~+13% decode, ~+20% long-prompt prefill). [STRATA-LAYER-SPLIT-20261107.md](evidence/STRATA-LAYER-SPLIT-20261107.md)
- **Nov 7:** Bolt 8 GiB RAM prompt cache. [BOLT-PROMPT-CACHE-20261107.md](evidence/BOLT-PROMPT-CACHE-20261107.md)

## Open items

- **ComfyUI 0.45.0** has only the short 1024² image and 512x288 video checks; 2048², 720p and 1080p were not re-run. The Raylight trial stage gives a different clip than on 0.44.0 (valid, same speed; cause not investigated). [ENGINE-UPDATES-20261112-MAYA-1160-COMFYUI-045.md](evidence/ENGINE-UPDATES-20261112-MAYA-1160-COMFYUI-045.md)
- **Strata 0.2.13, Maya 1.1.60, HyperQwen vLLM 0.33.0** have only short-check numbers; no long-context or sustained run yet. The Nov 7 Flash-Next figures above are still from 0.2.11.
- **DSH web app** still lists `flash-next-iq1m-strata` until `nvidia-dsh.service` restarts (its config is already regenerated; the router returns 404 for that id).
- **Quality benchmark gaps:** nothing was run with thinking on; samples are screening-size.
- **`data/`** holds many private trial and evidence directories (all gitignored). Pruning them needs the owner's OK.
- Possible follow-up from Nov 7 research: the DeepSeek entries still use the automatic layer split and might gain from the same hand-set split sweep that helped Flash-Next.

## Idle state

Router idle, no worker loaded, both GPUs at 1 MiB, no `data/GPU-LOCK`, GPU unlock VERIFIED.
