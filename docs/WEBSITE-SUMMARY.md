# NVIDIA LLM server results

Last updated: 2026-11-26

This file supplies the NVIDIA tables on the biegle.ca test-results page. Models are ranked by the short tool-use test (owner's decision, 2026-11-24); the 390-item test is archived. It is updated in the same commit as any change to the router or results. The AMD repository reports results on different test items, so the two sets are not comparable.

## Enabled routes

| Route | Model | Quant | Engine | Engine version | Context (tokens) | Weight size (GB) | Disk | Placement |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| qwen27b-hyperqwen | Qwen3.8-27B | AutoRound-INT4-fast-heads-INT8-embedding | HyperQwen-vLLM | vLLM 0.33.0 (pin 3d6c9543292e) | 86016 | 15.792 | SATA | VRAM only |
| qwen27b-sglang | Qwen3.8-27B | AutoRound-INT4-fast-heads-INT8-embedding | SGLang | d61ded5b9e2d | 57344 | 15.792 | SATA | VRAM only |
| flash-next-strata | Qwen3.8-Flash-Next | IQ3_XXS | Strata | 0.2.22 (control 0.1.69, Qwen 0.1.65) | 131072 | 75.840 | NVMe | streamed from SSD |
| glm-maya | GLM-5.3-Flash | Maya-S24 | Maya | 1.1.81 | 65536 | 94.702 | NVMe | streamed from SSD |
| deepseek-maya | DeepSeek-V4.1-Flash-1017 | UD-IQ1_S (Unsloth Dynamic3.1) | Maya | 1.1.81 | 32768 | 232.97960842 | NVMe + SATA | streamed from SSD |
| deepseek-unsloth-strata | DeepSeek-V4.1-Flash-1017 | UD-IQ1_S (Unsloth Dynamic3.1) | Strata | 0.2.13 (DSV4.1 0.1.59, control 0.1.69) | 32768 | 232.97960842 | NVMe + SATA | streamed from SSD |
| inkling-strata | Inkling 2 Mini 26B | SQ-10 | Strata | 0.2.22 (control 0.1.69, Inkling 0.1.69) | 131072 | 10.4715264 | NVMe | VRAM only |
| kolibri-llamacpp | Kolibri 1.1 | Q5_K_M | llama.cpp | PR 32891 build (5f4d2228), pinned | 131072 | 53.394217408 | SATA | partly in system memory |
| hy4-flash-strata | Tencent Hy4-Flash 220B-A12B | SQ-96 | Strata | 0.2.22 (control 0.1.69, Hy4 0.1.67) | 131072 | 158.096740352 | NVMe | partly in system memory |
| hy4-flash-maya | Tencent Hy4-Flash 220B-A12B | Maya-L | Maya | 1.1.81 | 131072 | 152.87284608 | SATA | streamed from SSD |

Weight sizes are decimal GB of served checkpoint files. The two dense Qwen routes share one checkpoint, as do the two DeepSeek routes. Hy4 on Strata uses the 3080 Ti with all experts in RAM and reads its Engram table from NVMe. Hy4 on Maya maps experts into the file cache, caches a fraction on both cards and reads table rows from SATA. Kolibri keeps the experts of 10 of its 48 MoE layers on the two cards and the rest in RAM, memory-mapped from SATA.

Maya 1.1.81 and Strata 0.2.22 (control 0.1.69) are serving since November 26; `flash-next-strata` keeps Qwen engine 0.1.65 (see docs/evidence/ENGINE-UPDATES-20261126-STRATA-0222.md and docs/evidence/ENGINE-UPDATES-20261126-MAYA-1181.md).

Sources include config/maintained-profiles.json, config/daily-update-versions.json, config/sglang-runtime.json, docs/CURRENT-STATE.md, docs/DAILY-ENGINE-UPDATES.md, docs/evidence/QUALITY-BENCHMARK-20261111.md and the Hy4 trial records below.

## Speed (standard short tool-call check)

One short DSH web-client tool call on a roughly 5.6K–7K-token prompt, followed by the tool result, a follow-up and an owned unload. Rates and first-token time refer to the first call and exclude model load. Each row uses one passing run on the serving build, selected by fastest decode within the current engine and control combination.

| Route | Prefill (tok/s) | Time to first token (s) | Decode (tok/s) | Prompt tokens | Date | Engine version measured | Source | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| qwen27b-hyperqwen | 2094.6 | 2.80 | 62.7 | not recorded | 2026-11-09 | vLLM 0.33.0 (80cf059) | docs/evidence/ENGINE-UPDATES-20261109-HYPERQWEN-80cf059.md (80cf059) | First load after rebuild. Later pin moved without a rebuild or speed check. |
| qwen27b-sglang | 2219.46 | 2.785 | 60.135 | 6095 | 2026-11-05 | d61ded5b9e2d | docs/evidence/ALL-ENTRY-BENCHMARKS-20261105.md (d61ded5b9e2d) | Zero native cached tokens. |
| flash-next-strata | 1271.8 | 4.54 | 67.2 | not recorded | 2026-11-26 | 0.2.22 (control 0.1.69, Qwen 0.1.65) | docs/evidence/ENGINE-UPDATES-20261126-STRATA-0222.md (b28ca95e3e68) | Recheck on the retained Qwen engine; both runs gave 67.2. Qwen engine 0.1.69 gave 56.1 and was not kept. |
| glm-maya | 543.0 | 10.21 | 13.8 | not recorded | 2026-11-26 | 1.1.81 | docs/evidence/ENGINE-UPDATES-20261126-MAYA-1181.md (4a0ce6e86e18) | Single run. |
| deepseek-maya | 189.8 | 31.28 | 8.1 | not recorded | 2026-11-26 | 1.1.81 | docs/evidence/ENGINE-UPDATES-20261126-MAYA-1181.md (4a0ce6e86e18) | Single run. |
| deepseek-unsloth-strata | 28.3 | 6.18 | 12.2 | not recorded | 2026-11-26 | 0.2.13 (DSV4.1 0.1.59, control 0.1.69) | docs/evidence/ENGINE-UPDATES-20261126-STRATA-0222.md (b28ca95e3e68) | Prompt reuse. |
| inkling-strata | 2132.7 | 3.43 | 67.0 | not recorded | 2026-11-26 | 0.2.22 (control 0.1.69, Inkling 0.1.69) | docs/evidence/ENGINE-UPDATES-20261126-STRATA-0222.md (b28ca95e3e68) | Single run on Inkling a5bfe0369bfb. |
| kolibri-llamacpp | 541.9 | 10.82 | 36.2 | 5707 | 2026-11-24 | PR 32891 build (5f4d2228) | docs/evidence/KOLIBRI-1.1-ROUTER-ENTRY-20261124.md | First of two passing checks. The web-client prompt runs in five batches at checkpoint boundaries; a plain 6.1K-token prompt reads at 1,316 tok/s. |
| hy4-flash-strata | 212.9 | 26.43 | 27.9 | not recorded | 2026-11-26 | 0.2.22 (control 0.1.69, Hy4 0.1.67) | docs/evidence/ENGINE-UPDATES-20261126-STRATA-0222.md (b28ca95e3e68) | Single run on Hy4 4da72cca05cc. |
| hy4-flash-maya | 45.6 | 121.8 | 13.4 | not recorded | 2026-11-26 | 1.1.81 | docs/evidence/ENGINE-UPDATES-20261126-MAYA-1181.md (4a0ce6e86e18) | Single run; first start passed its owned unload. Generation 16.1 on 1.1.78 the day before (warning). |

The SGLang token count comes from docs/evidence/validation-results/20261105-engine-refresh.json. On the frozen DeepSeek engine with earlier control, the first load after reboot measured 84.2 tok/s prefill, 67.81 s to first token and 11.7 tok/s decode on 2026-11-15 (docs/evidence/ENGINE-UPDATES-20261115-MAYA-1165-STRATA-0214.md).

## Retired or removed routes

| Route | Model / quant | Engine | Retired (date) | Replaced by | Weights kept or deleted | Source |
| --- | --- | --- | --- | --- | --- | --- |
| flash-next-iq4xs-strata | Qwen3.8-Flash-Next / UD-IQ4_XS-v31 | Strata | 2026-11-24 | flash-next-strata | Deleted 2026-11-25 | docs/evidence/FLASH-NEXT-IQ4XS-RETIRED-20261124.md |
| inkling-llamacpp | Inkling 2 Mini / UD-Q4_K_M | Unsloth llama.cpp | 2026-11-24 | inkling-strata | Deleted 2026-11-25 | docs/evidence/INKLING2-MINI-STRATA-ENTRY-20261124.md |
| bolt-llamacpp | Nemotron-3.5-Bolt-74B-A9B / native IQ2 | llama.cpp | 2026-11-23 | qwen27b-hyperqwen (saved selections) | Deleted | docs/CURRENT-STATE.md |
| inkling-strata (single-card 8K version) | Inkling 2 Mini / SQ-10 | Strata | 2026-11-23 | inkling-strata (two-card reintroduction 2026-11-24) | Original weights deleted | docs/evidence/INKLING2-MINI-STRATA-TRIAL-20261122.md |
| flash-next-iq1m-strata | Qwen3.8-Flash-Next / UD-IQ1_M | Strata | 2026-11-08 | flash-next-strata | Deleted | docs/evidence/FLASH-IQ1M-RETIREMENT-20261108.md |
| qwen27b-tensorfold | Qwen3.8-27B / EXL3-2.0bpw | TensorFold | 2026-11-06 | qwen27b-hyperqwen (saved selections) | Deleted | a1386c1 (README.md and dsh/configure.py) |
| bolt-vllm (native IQ2 version) | Nemotron-3.5-Bolt-74B-A9B / native IQ2 | llama.cpp | 2026-11-06 | bolt-llamacpp (rename) | Kept at rename, deleted 2026-11-23 | docs/evidence/BOLT-ID-RENAME-20261106.md |
| flash-next-iq1s-llamacpp | Qwen3.8-Flash-Next / UD-IQ1_S | llama.cpp | 2026-11-05 | flash-next-iq1m-strata | Deleted, shared table retained for IQ1_M | docs/evidence/IQ1S-WEIGHT-REMOVAL-20261105.md |
| bolt-vllm (AWQ INT4 version) | Nemotron-3.5-Bolt-74B-A9B / AWQ INT4 | vLLM | 2026-11-04 | bolt-vllm (native IQ2) | Deleted | docs/evidence/BOLT-AWQ-REMOVAL-20261104.md |
| deepseek-strata | DeepSeek-V4.1-Flash-1017 / Maya-S | Strata | 2026-11-01 | deepseek-unsloth-strata | Deleted | docs/evidence/MAYA-UNSLOTH-20261101.md |
| super-vllm | Nemotron-3.5-Super-VL-120B-A12B / W4A16-Merlin | vLLM | 2026-11-01 | qwen27b-hyperqwen (saved selections) | Deleted | docs/evidence/NEMOTRON-SUPER-REMOVAL-20261101.md |
| super-strata-trial | Nemotron-3.5-Super-VL-120B-A12B / UD-Q4_K_XL | Strata | 2026-11-01 | qwen27b-hyperqwen (saved selections) | Deleted | docs/evidence/NEMOTRON-SUPER-REMOVAL-20261101.md |
| qwen27b-llama | Qwen3.8-27B / IQ4_XS | llama.cpp | 2026-10-27 | qwen27b-hyperqwen | Deleted | docs/evidence/QWEN27B-GPU-ONLY-20261026.md |

## Quality ranking (short tool-use test)

| Rank | Model | Quant | Engine | Route | Score | 95% interval | Single turn | Parallel calls | No tool fits | Plain calls | Multi-turn episodes | Other engines/quants (with scores) | Tie note | Date | Source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | DeepSeek-V4.1-Flash-1017 | UD-IQ1_S | Maya | deepseek-maya | 70.3 | 53.1–87.4 | 34/40 | 13/15 | 12/15 | 9/10 | 5/9 | Strata 67.8 (50.4–85.2) | interval does not overlap Inkling 2 Mini 26B or Qwen3.8-Flash-Next, but only just (Flash-Next by 0.1 point; Inkling because its own interval is too narrow); not separated from the rest | 2026-11-24 rerun (earlier: 63.5 (stored answers of 2026-11-12)) | docs/evidence/SHORT-TEST-RERUN-20261124.md |
| 2 | Qwen3.8-27B | AutoRound INT4 | SGLang | qwen27b-sglang | 67.2 | 50.3–84.1 | 36/40 | 13/15 | 14/15 | 9/10 | 4/9 | HyperQwen-vLLM 66.0 (49.0–83.0) | not separated from any other model (all 95% intervals overlap) | 2026-11-24 rerun (earlier: 61.7 (stored answers of 2026-11-12)) | docs/evidence/SHORT-TEST-RERUN-20261124.md |
| 3 | Tencent Hy4-Flash 220B-A12B | SQ-96 | Strata | hy4-flash-strata | 58.5 | 40.8–76.1 | 29/40 | 9/15 | 13/15 | 7/10 | 4/9 | Maya (Maya-L weights) 48.1 (36.4–59.7) | not separated from any other model (all 95% intervals overlap) | 2026-11-24 rerun (earlier: 57.9 (2026-11-22)) | docs/evidence/SHORT-TEST-RERUN-20261124.md |
| 4 | GLM-5.3-Flash | Maya-S24 | Maya | glm-maya | 49.3 | 37.8–60.8 | 35/40 | 13/15 | 12/15 | 10/10 | 1/9 | none | not separated from any other model (all 95% intervals overlap) | 2026-11-24 rerun (earlier: 60.4 (stored answers of 2026-11-11)) | docs/evidence/SHORT-TEST-RERUN-20261124.md |
| 5 | Inkling 2 Mini 26B | SQ-10 | Strata | inkling-strata | 47.5 | 44.1–50.9 | 38/40 | 15/15 | 14/15 | 9/10 | 0/9 | retired llama.cpp UD-Q4_K_M 40.0 (2026-11-22, cut, 1 of 9 episodes reached) | interval does not overlap DeepSeek-V4.1-Flash-1017; not separated from the rest. Its interval is too narrow: 0 of 9 episodes has no spread in the normal approximation | 2026-11-24 rerun (earlier: 59.3 (2026-11-24, cut with 7 of 9 episodes reached)) | docs/evidence/SHORT-TEST-RERUN-20261124.md |
| 6 | Kolibri 1.1 | Q5_K_M | llama.cpp (PR 32891 build) | kolibri-llamacpp | 41.8 | 29.4–54.2 | 29/40 | 5/15 | 14/15 | 10/10 | 1/9 | thinking at medium (not as served) 60.0 (2026-11-24, 3 of 5 scored episodes) | not separated from any other model (all 95% intervals overlap) | 2026-11-24 rerun (earlier: 41.8 (2026-11-24, trial server)) | docs/evidence/SHORT-TEST-RERUN-20261124.md |
| 7 | Qwen3.8-Flash-Next | IQ3_XXS | Strata | flash-next-strata | 40.6 | 28.1–53.0 | 28/40 | 9/15 | 10/15 | 9/10 | 1/9 | retired UD-IQ4_XS-v31 47.4 (stored answers of 2026-11-10) | interval does not overlap DeepSeek-V4.1-Flash-1017, by 0.1 point; not separated from the rest | 2026-11-24 rerun (earlier: 40.6 (stored answers of 2026-11-10)) | docs/evidence/SHORT-TEST-RERUN-20261124.md |

Score = 50 × (single-turn accuracy on 40 items + pass rate on the 9 common multi-turn episodes), the same 49 items for every model. Every enabled route was rerun live through the router on 2026-11-24/25, one at a time, on the engines now serving (owner's request); all 49 items were scored for every route, with no timeouts. Larger models also ran 6 extra episodes in their 1-hour limit; those are in the source file but not used for the ranking. The 95% interval is the normal approximation over both parts. Thinking as served (off, or hidden for Inkling). Single turn splits into 15 parallel-call items, 15 items where no tool fits and 10 plain calls (BFCL v4).

One row per model, best route shown; the other route of the same model is in the other-engines column. One run is about ±17 points per model at 95%, so read the order as a rough guide. Between runs a route moved by up to 12 points, almost all of it in the 9 episodes. The 390-item results below are archived and no longer rank models. AMD results use other items and are not comparable.

## Archived: 390-item test (not the ranking)

| Rank | Model | Quant | Engine | Score (macro %) | 95% interval | MMLU-Pro | AIME 2025 | LiveCodeBench | BFCL single | BFCL multi | Other engines/quants (with scores) | Tie note | Date |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | DeepSeek-V4.1-Flash-1017 | UD-IQ1_S (Unsloth Dynamic3.1) | Strata | 73.0 | 67.3–78.4 | 86.7% | 76.7% | 55.0% | 90.0% | 56.7% | Maya 72.4% | Tied with Maya and Qwen 27B | 2026-11-11 |
| 2 | Qwen3.8-27B | AutoRound-INT4-fast-heads-INT8-embedding | SGLang | 68.1 | 62.3–73.9 | 85.7% | 66.7% | 50.0% | 91.7% | 46.7% | HyperQwen-vLLM 68.0% | Tied with HyperQwen, DeepSeek and Flash-Next | 2026-11-12 |
| 3 | Qwen3.8-Flash-Next | IQ3_XXS | Strata | 62.0 | 56.5–67.5 | 85.2% | 73.3% | 58.3% | 73.3% | 20.0% | Strata UD-IQ4_XS-v31 65.5% (retired) | Tied with IQ4_XS, Qwen 27B and GLM | 2026-11-11 |
| 4 | GLM-5.3-Flash | Maya-S24 | Maya | 57.2 | 52.1–62.3 | 86.2% | 6.7% | 55.0% | 91.7% | 46.7% | None | Tied with Flash-Next IQ3_XXS | 2026-11-11 |

Kept for reference only; the ranking is the short tool-use test above (owner's decision, 2026-11-24). Rank orders the best enabled route for each scored model. Dates identify the dated results. The first five routes ran over 2026-11-10 to 2026-11-11. Qwen on SGLang and DeepSeek on Maya ran on 2026-11-12. The larger Flash-Next quant ran over 2026-11-17 to 2026-11-18.

Each route answered the same 390 items with thinking off as served and one generation per item. The macro score weights five benchmarks equally. MMLU-Pro contributed 210 items, AIME 2025 contributed 30, LiveCodeBench contributed 60, and BFCL v4 contributed 60 single-turn items and 30 multi-turn episodes.

A tie means the paired 95% interval includes zero. No adjacent entries in the original ranking separated. Neither same-checkpoint engine pair separated on any individual benchmark. DeepSeek exceeded both Flash-Next quants and GLM. The two Flash-Next quants tied (paired difference −2.0 to +8.9 points).

Inkling 2 Mini on inkling-strata, Kolibri 1.1 on kolibri-llamacpp and Hy4-Flash on both routes are **not tested** on this benchmark. The separate Inkling llama.cpp trial used thinking on. Sources are docs/evidence/QUALITY-BENCHMARK-20261111.md and docs/CURRENT-STATE.md.

## Trials (not router entries)

| Model | Quant | Engine | Date | Status | Key results | Source |
| --- | --- | --- | --- | --- | --- | --- |
| Nemotron-3.5-Bolt-74B-A9B | AWQ INT4 | vLLM and SGLang startup trials | 2026-10-31 | trial, not for the website | see source | docs/evidence/NEMOTRON-INT4-OFFLOAD-20261031.md |
| Nemotron-3.5-Super-VL-120B-A12B | W4A16-Merlin | vLLM and SGLang startup trials | 2026-10-31 | trial, not for the website | see source | docs/evidence/NEMOTRON-INT4-OFFLOAD-20261031.md |
| Nemotron-3.5-Bolt-74B-A9B | AWQ INT4 | vLLM pageable offload | 2026-10-31 | trial, not for the website | see source | docs/evidence/GPU-PAIR-AUX-OPTIMIZATION-20261031.md |
| Nemotron-3.5-Bolt-74B-A9B | AWQ INT4 | vLLM compact prefetch | 2026-10-31 | trial, not for the website | see source | docs/evidence/BOLT-MAYA-RELIABILITY-20261031.md |
| Nemotron-3.5-Bolt-74B-A9B | native IQ2 | llama.cpp 11909 offload screen | 2026-11-04 | trial, not for the website | see source | docs/evidence/BOLT-NATIVE-IQ2-20261104.md |

The two Nemotron startup screens ended before inference. Super used dummy weights. The pageable Bolt trial hit its reserve guard. The isolated compact-prefetch run measured 0.452 tok/s decode. Native IQ2 with a 384 MiB fit target later reached 67.49 tok/s decode. The retirement table records the eventual router deployments.

## Hardware and measurement conditions

| Component | Results measured on | Source |
| --- | --- | --- |
| CPU | Intel Core i9-13900KS | docs/evidence/Z690-13900KS-MIGRATION-20261103.md |
| Motherboard | MSI MPG Z690 Carbon WiFi DDR5 (MS-7D30) | docs/evidence/Z690-13900KS-MIGRATION-20261103.md |
| Installed RAM | 96 GB DDR5 | docs/evidence/RAM96-RESTORATION-20261104.md |
| Usable RAM | 91.76984787 GiB | docs/evidence/RAM96-RESTORATION-20261104.md |
| GPU 0 | NVIDIA GeForce RTX 3080 Ti 12 GB | README.md |
| GPU 1 | NVIDIA GeForce RTX 3080 10 GB | README.md |
| PCIe links | PCIe 4.0 x8 per GPU | docs/evidence/Z690-13900KS-MIGRATION-20261103.md |
| GPU transport | Host-staged, no P2P | docs/HISTORY.md |
| System drive | NVMe | README.md |
| SATA drive | Samsung SSD 870 QVO | docs/STORAGE-POLICY.md |
| OS | Ubuntu 26.04 | docs/evidence/VALIDATION-20261026.md |
| Kernel | 7.0.0-43 | docs/HISTORY.md |
| NVIDIA driver | 615.71.09 (stock signed open modules) | docs/evidence/Z690-13900KS-MIGRATION-20261103.md |

| Date | Change in measurement conditions | Source |
| --- | --- | --- |
| 2026-10-26 | Original i5-13600KF host with 64 GB DDR5 and NVIDIA 595.99.02 | docs/evidence/BENCHMARK-20261026.md |
| 2026-10-26 | Both GPUs tensor-unlocked on kernel 7.0.0-38-generic | docs/evidence/BENCHMARK-UNLOCK-20261026.md |
| 2026-10-27 | GPU-resident dense weights moved to SATA, SSD-streaming profiles kept on NVMe | docs/STORAGE-POLICY.md |
| 2026-10-28 | One DIMM removed, leaving 45.55 GiB usable | docs/evidence/REDUCED-RAM-20261028.md |
| 2026-10-29 | 64 GB restored, 61.3013 GiB usable on kernel 7.0.0-42-generic | docs/evidence/FULL-RAM-RESTORATION-20261029.md |
| 2026-10-31 | NVIDIA 615.71.09 with a custom P2P driver and an external switch | docs/HISTORY.md |
| 2026-10-31 | Unlock 2.0.0 verified on both RTX 3080-series GPUs and the RTX 3060 | docs/evidence/UNLOCK-V2-BENCHMARK-20261031.md |
| 2026-11-01 | RTX 3060 permanently removed, switched pair P2P verified | docs/evidence/P2P-PERMANENT-PAIR-20261101.md |
| 2026-11-02 | Headless configuration adopted a 256 MiB free-VRAM floor per GPU | docs/evidence/HEADLESS-VRAM256-20261102.md |
| 2026-11-03 | Z690 and i9-13900KS installed with temporary 32 GB RAM and UHD 770 desktop | docs/evidence/Z690-13900KS-MIGRATION-20261103.md |
| 2026-11-03 | Switch and Crucial NVMe removed, stock signed 615.71.09 restored on direct x8/x8 without P2P | docs/evidence/Z690-13900KS-MIGRATION-20261103.md |
| 2026-11-04 | 96 GB RAM qualified with verified early GPU unlock and host-staged transport | docs/evidence/RAM96-RESTORATION-20261104.md |
| 2026-11-09 | Launchers enforce host staging and clear the native P2P flag | docs/HISTORY.md |
| 2026-11-12 | Reboot onto kernel 7.0.0-43, GPU unlock verified again | docs/HISTORY.md |
