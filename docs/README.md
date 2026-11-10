# Documentation index

Start with [CURRENT-STATE.md](CURRENT-STATE.md) and the root [AGENTS.md](../AGENTS.md).

## Reference (kept current)

| Doc | What it covers |
|---|---|
| [CURRENT-STATE.md](CURRENT-STATE.md) | What is live now: models, engines, contexts, speeds, open items. Start here. |
| [HISTORY.md](HISTORY.md) | Dated change log, newest first. Evidence only; older entries are often superseded. |
| [MAINTAINED-PROFILES.md](MAINTAINED-PROFILES.md) | The model registry and how entries are selected, changed and retired. |
| [ENGINE-UPDATE-RUNBOOK.md](ENGINE-UPDATE-RUNBOOK.md) | How engine updates are checked and installed by hand (since Nov 9). |
| [DAILY-ENGINE-UPDATE-POLICY.md](DAILY-ENGINE-UPDATE-POLICY.md) | Promotion rule; the retired 03:00 updater's gates. |
| [DAILY-ENGINE-UPDATES.md](DAILY-ENGINE-UPDATES.md) | Engine update ledger, newest first (hand-written since Nov 9). |
| [BENCHMARK-REPORTING.md](BENCHMARK-REPORTING.md) | Required benchmark metrics, table layout and wording. |
| [BENCHMARK-HISTORY.md](BENCHMARK-HISTORY.md) | Benchmark ledger (dated sections, newest first). |
| [CLI-SHORT-MODEL-TESTS.md](CLI-SHORT-MODEL-TESTS.md) | Short CLI model checks. |
| [FUTURE-MODEL-TEST-PLAN.md](FUTURE-MODEL-TEST-PLAN.md) | Procedure for testing a new model. |
| [STORAGE-POLICY.md](STORAGE-POLICY.md) | Which drive holds which weights (dated sections on top, current placement below). |
| [INFERENCE-SWAP-POLICY.md](INFERENCE-SWAP-POLICY.md) | RAM/swap/pressure guard policy and its history. |
| [OPERATIONAL-LIFECYCLE.md](OPERATIONAL-LIFECYCLE.md) | Idle unload, lifecycle telemetry, manual candidate staging. |
| [GPU-UNLOCK-HEALTH.md](GPU-UNLOCK-HEALTH.md) | GPU unlock health service and checks. |
| [LOCAL-SETUP.md](LOCAL-SETUP.md) | Dependencies, builds and local setup notes. |
| [PUBLIC-SYNC.md](PUBLIC-SYNC.md) | Exporting to the public mirror. |
| [REPOSITORY-MAP.md](REPOSITORY-MAP.md) | Repository family and retirement policy. |
| [CODEX-CONTEXT-HANDOFF.md](CODEX-CONTEXT-HANDOFF.md) | Codex context monitor policy (read by `scripts/codex_context_monitor.py`). |

## Evidence (`evidence/`)

Each file records one piece of work and is not updated afterwards, so later work may supersede it. Raw measurements are in `evidence/benchmark-results/` and `evidence/validation-results/`. New evidence goes here as `TOPIC-YYYYMMDD.md`; add it to this index and, if public, to `FILES` in `scripts/sync_public.py`.

### Storage and drives

- [STORAGE-STATUS-20261108.md](evidence/STORAGE-STATUS-20261108.md): Storage status and unused-weights audit — November 8, 2026

### Retirements, removals and cleanups

- [FLASH-IQ1M-RETIREMENT-20261108.md](evidence/FLASH-IQ1M-RETIREMENT-20261108.md): Flash-Next IQ1_M retired — November 8, 2026
- [IQ1S-WEIGHT-REMOVAL-20261105.md](evidence/IQ1S-WEIGHT-REMOVAL-20261105.md): Retired IQ1_S weights removed — November 5, 2026
- [UNUSED-QWEN-GGUF-REMOVAL-20261104.md](evidence/UNUSED-QWEN-GGUF-REMOVAL-20261104.md): Unused Qwen GGUF files removed — November 4, 2026
- [BOLT-AWQ-REMOVAL-20261104.md](evidence/BOLT-AWQ-REMOVAL-20261104.md): Retired Bolt AWQ deleted — November 4, 2026
- [NEMOTRON-SUPER-REMOVAL-20261101.md](evidence/NEMOTRON-SUPER-REMOVAL-20261101.md): Nemotron Super removed — November 1, 2026
- [DSH-ROUTER-CLEANUP-20261101.md](evidence/DSH-ROUTER-CLEANUP-20261101.md): DSH router entries and harness compatibility — November 1, 2026
- [UNUSED-MODEL-CLEANUP-20261027.md](evidence/UNUSED-MODEL-CLEANUP-20261027.md): Unused model and preparation cleanup — October 27, 2026

### ComfyUI image and video

- [WAN1080-FIX-20261105.md](evidence/WAN1080-FIX-20261105.md): Wan 1080p VRAM and Raylight repair — November 5, 2026
- [COMFY-VIDEO-HD-ENTRIES-20261105.md](evidence/COMFY-VIDEO-HD-ENTRIES-20261105.md): 720p and 1080p video entries and desktop actions — November 5, 2026
- [COMFY-VIDEO-720P1080P-20261105.md](evidence/COMFY-VIDEO-720P1080P-20261105.md): GPU-only video benchmarks at 720p and 1080p — November 5, 2026
- [COMFY-DUAL-GPU-20261105.md](evidence/COMFY-DUAL-GPU-20261105.md): ComfyUI dual-GPU image setup — November 5 UTC / November 4 local, 2026
- [COMFY-VIDEO-ENTRIES-20261104.md](evidence/COMFY-VIDEO-ENTRIES-20261104.md): Maintained ComfyUI video entries — November4,2026
- [COMFY-VIDEO-DUAL-GPU-20261104.md](evidence/COMFY-VIDEO-DUAL-GPU-20261104.md): Guarded two-GPU video trials — November 4, 2026
- [COMFY-2K4K-20261104.md](evidence/COMFY-2K4K-20261104.md): ComfyUI native2K/4K tests — November4,2026 (America/Toronto)
- [UNSLOTH-COMFY-DESKTOP-20261030.md](evidence/UNSLOTH-COMFY-DESKTOP-20261030.md): Unsloth and Comfy Desktop installation — October 30, 2026

### GPU unlock, P2P and hardware

- [POWERLOSS-RECOVERY-20261105.md](evidence/POWERLOSS-RECOVERY-20261105.md): Power-loss recovery verified — November 5, 2026
- [Z690-13900KS-MIGRATION-20261103.md](evidence/Z690-13900KS-MIGRATION-20261103.md): Z690 / 13900KS hardware migration — November 3, 2026
- [UNLOCKED-VRAM-ONLY-20261103.md](evidence/UNLOCKED-VRAM-ONLY-20261103.md): Unlocked VRAM-only results — November 3, 2026
- [HEADLESS-VRAM256-20261102.md](evidence/HEADLESS-VRAM256-20261102.md): Headless-server free-VRAM guard — November 2, 2026
- [P2P-PERMANENT-PAIR-20261101.md](evidence/P2P-PERMANENT-PAIR-20261101.md): Permanent two-card P2P repair — November 1, 2026
- [UNLOCK-V2-BENCHMARK-20261031.md](evidence/UNLOCK-V2-BENCHMARK-20261031.md): GPU unlock 2.0 compute benchmark — October 31, 2026
- [PEX-ACS-PAIR-20261031.md](evidence/PEX-ACS-PAIR-20261031.md): Scoped PEX ACS/routing correction — October 31, 2026
- [P2P-POSTBOOT-20261031.md](evidence/P2P-POSTBOOT-20261031.md): P2P post-boot verification — October 31, 2026
- [P2P-DYNAMIC-UNLOCK-20261031.md](evidence/P2P-DYNAMIC-UNLOCK-20261031.md): Dynamic BAR1 and address-independent unlock candidate — October 31, 2026
- [THREE-GPU-PREPARATION-20261030.md](evidence/THREE-GPU-PREPARATION-20261030.md): Three-GPU hardware-change preparation — October 30, 2026
- [P2P-DRIVER-PREPARATION-20261030.md](evidence/P2P-DRIVER-PREPARATION-20261030.md): P2P driver preparation — October 30, 2026
- [HARDWARE-TUNING-QUALIFICATION-20261030.md](evidence/HARDWARE-TUNING-QUALIFICATION-20261030.md): Hardware tuning qualification — October 30, 2026
- [HARDWARE-TUNING-RESEARCH-20261029.md](evidence/HARDWARE-TUNING-RESEARCH-20261029.md): Hardware tuning research — October 29, 2026
- [UNLOCK-IMPACT-20261027.md](evidence/UNLOCK-IMPACT-20261027.md): Unlock impact on the current profiles
- [UNLOCK-SETUP-20261026.md](evidence/UNLOCK-SETUP-20261026.md): Two-card unlock preparation — October 26, 2026
- [BENCHMARK-UNLOCK-20261026.md](evidence/BENCHMARK-UNLOCK-20261026.md): Unlocked versus stock benchmark — October 26, 2026

### RAM, VRAM and guard limits

- [ALL-MODEL-RAM-CEILINGS-20261105.md](evidence/ALL-MODEL-RAM-CEILINGS-20261105.md): All model RAM ceilings — November 5, 2026
- [RAM96-RESTORATION-20261104.md](evidence/RAM96-RESTORATION-20261104.md): 96 GB restoration and two-GiB headroom — November 4, 2026
- [RAM96-PREPARATION-20261104.md](evidence/RAM96-PREPARATION-20261104.md): Larger-RAM restoration preparation — November 4, 2026
- [RAM26-28-RERUN-20261104.md](evidence/RAM26-28-RERUN-20261104.md): 26/28 GiB RAM policy and requested reruns — November 4, 2026
- [VRAM256-OPTIMIZATION-20261103.md](evidence/VRAM256-OPTIMIZATION-20261103.md): 256 MiB reruns and continued optimization — November 3, 2026
- [API-SWITCH-VRAM-20261101.md](evidence/API-SWITCH-VRAM-20261101.md): API model switch startup VRAM — November 1, 2026
- [WORKER-RAM-64GB-20261031.md](evidence/WORKER-RAM-64GB-20261031.md): Restored 64GB worker RAM policy — October 31, 2026
- [QWEN-RELAXED-SWAP-20261029.md](evidence/QWEN-RELAXED-SWAP-20261029.md): Qwen mapped experts with bounded swap allowance — October 29, 2026
- [QWEN-CURRENT-GUARDS-20261029.md](evidence/QWEN-CURRENT-GUARDS-20261029.md): Current Qwen/Flash-Next Strata fails the reduced-RAM loading guard
- [MOE-VRAM512-20261029.md](evidence/MOE-VRAM512-20261029.md): MoE 512 MiB reserves and dense RAM-cap removal — October 29, 2026
- [MAYA-DS4-VRAM512-FOLLOWUP-20261029.md](evidence/MAYA-DS4-VRAM512-FOLLOWUP-20261029.md): DeepSeek/Maya did not qualify at 512 MiB after three cache follow-ups
- [FULL-RAM-RESTORATION-20261029.md](evidence/FULL-RAM-RESTORATION-20261029.md): Full-RAM restoration — October 29, 2026
- [BENCHMARK-SSD-SWAP-64GB-20261029.md](evidence/BENCHMARK-SSD-SWAP-64GB-20261029.md): SSD-streaming swap-policy benchmark on 64GB — October 29, 2026
- [BENCHMARK-PRESSURE-GUARD-64GB-20261029.md](evidence/BENCHMARK-PRESSURE-GUARD-64GB-20261029.md): Two-profile memory-pressure adjustment and 64GB benchmark — October 29, 2026
- [ALL-PROFILES-HOST-RESERVE2-20261029.md](evidence/ALL-PROFILES-HOST-RESERVE2-20261029.md): All six profiles: host-RAM reserve 2 GiB — October 29, 2026
- [REDUCED-RAM-20261028.md](evidence/REDUCED-RAM-20261028.md): Four SSD-streaming profiles with reduced RAM — October 28, 2026
- [QWEN-HOST-RESERVE2-20261028.md](evidence/QWEN-HOST-RESERVE2-20261028.md): Qwen/Strata host-RAM reserve lowered to 2 GiB — October 28, 2026

### Router, API, DSH and clients

- [PROVIDER-ABORT-BUFFERING-20261103.md](evidence/PROVIDER-ABORT-BUFFERING-20261103.md): Provider abort repair: buffered native channel logs — November 3, 2026
- [DSH-STARTUP-REPAIR-20261103.md](evidence/DSH-STARTUP-REPAIR-20261103.md): DSH headless startup repair — November 3, 2026
- [NEW-ROUTER-BENCHMARKS-20261101.md](evidence/NEW-ROUTER-BENCHMARKS-20261101.md): All maintained models through the API-only router — November 1, 2026
- [DSH-HYPERQWEN-SEARCH-20261101.md](evidence/DSH-HYPERQWEN-SEARCH-20261101.md): DSH HyperQwen search entry — November 1, 2026
- [BACKGROUND-TERMINALS-20261101.md](evidence/BACKGROUND-TERMINALS-20261101.md): Background terminal focus protection — November 1, 2026
- [API-SWITCH-CHECKS-20261101.md](evidence/API-SWITCH-CHECKS-20261101.md): Short API switch checks — November 1, 2026
- [TERMINAL-ATTENTION-20261031.md](evidence/TERMINAL-ATTENTION-20261031.md): Terminal attention and backend focus policy — October 31, 2026
- [RESPONSES-WEB-SEARCH-20261030.md](evidence/RESPONSES-WEB-SEARCH-20261030.md): Local Responses web search — October 30, 2026
- [OPENCAT-SEARCH-MODEL-20261030.md](evidence/OPENCAT-SEARCH-MODEL-20261030.md): OpenCat search model entry — October 30, 2026
- [OPENCAT-RESPONSES-20261030.md](evidence/OPENCAT-RESPONSES-20261030.md): OpenCat Responses compatibility — October 30, 2026
- [OPENCAT-HEADLINES-20261030.md](evidence/OPENCAT-HEADLINES-20261030.md): OpenCat headline content repair — October 30, 2026
- [API-RELIABILITY-20261030.md](evidence/API-RELIABILITY-20261030.md): OpenAI-compatible API reliability — October 30, 2026
- [TERMINAL-LIFETIME-20261029.md](evidence/TERMINAL-LIFETIME-20261029.md): Automatic terminal lifetime — October 29, 2026
- [ROUTER-IMPROVEMENTS-20261028.md](evidence/ROUTER-IMPROVEMENTS-20261028.md): NVIDIA router admission and transport — October 28
- [ENGINE-SWITCHING-20261028.md](evidence/ENGINE-SWITCHING-20261028.md): Automatic engine switching and console ownership — October 28,2026
- [ROUTER-DEPLOYMENT-20261027.md](evidence/ROUTER-DEPLOYMENT-20261027.md): NVIDIA router and native-app deployment — October 27, 2026

### Daily updater and engine qualification

- [MAYA-QUALIFICATION-REPAIR-20261106.md](evidence/MAYA-QUALIFICATION-REPAIR-20261106.md): Maya qualification repair — November 6, 2026
- [STRATA-0211-QUALIFICATION-20261105.md](evidence/STRATA-0211-QUALIFICATION-20261105.md): Strata 0.2.11 qualification — November 5, 2026
- [MAYA-1154-QUALIFICATION-20261105.md](evidence/MAYA-1154-QUALIFICATION-20261105.md): Maya 1.1.54 qualification attempt — November 5, 2026
- [ENGINE-REFRESH-AND-WEIGHT-SHARING-20261105.md](evidence/ENGINE-REFRESH-AND-WEIGHT-SHARING-20261105.md): Engine refresh and weight sharing — November 5, 2026
- [DAILY-UPDATER-RESTORATION-20261105.md](evidence/DAILY-UPDATER-RESTORATION-20261105.md): Daily updater restoration — November5,2026
- [STRATA-OFFICIAL-APP-20261030.md](evidence/STRATA-OFFICIAL-APP-20261030.md): Official Strata desktop app and existing Q3 model — October 30, 2026
- [SGLANG-38K-QUALIFICATION-20261028.md](evidence/SGLANG-38K-QUALIFICATION-20261028.md): SGLang 38K context qualification — October 28, 2026
- [ALL-ENGINE-POLICY-20261028.md](evidence/ALL-ENGINE-POLICY-20261028.md): Shared inference policy — October 28, 2026
- [ENGINE-TESTS-20261026.md](evidence/ENGINE-TESTS-20261026.md): CUDA engine qualification on mixed Ampere cards

### Benchmarks

- [ALL-MODELS-RERUN-20261105.md](evidence/ALL-MODELS-RERUN-20261105.md): All downloaded model coverage and rerun — November 5, 2026
- [ALL-ENTRY-BENCHMARKS-20261105.md](evidence/ALL-ENTRY-BENCHMARKS-20261105.md): Current entry observations — November 5, 2026
- [ALL-ENTRY-BENCHMARKS-PRE-IQ2-20261104.md](evidence/ALL-ENTRY-BENCHMARKS-PRE-IQ2-20261104.md): Historical index before native IQ2 selection — November 4, 2026
- [ALL-ENTRY-BENCHMARKS-20261104.md](evidence/ALL-ENTRY-BENCHMARKS-20261104.md): All current entry benchmarks — November 4, 2026
- [SHORT-TOOL-BENCHMARKS-20261101.md](evidence/SHORT-TOOL-BENCHMARKS-20261101.md): Short actual-tool benchmark observations — November 1, 2026
- [BENCHMARK-64GB-20261029.md](evidence/BENCHMARK-64GB-20261029.md): Six selected profiles benchmarked with 64GB RAM — October 29, 2026
- [BENCHMARK-20261027-101219.md](evidence/BENCHMARK-20261027-101219.md): Fresh kept-profile benchmark — October 27, 2026
- [BENCHMARK-20261026.md](evidence/BENCHMARK-20261026.md): Local model speed benchmark - October 26, 2026

### Models, engines and context

- [ENGINE-UPDATES-HANDS-ON-20261109.md](evidence/ENGINE-UPDATES-HANDS-ON-20261109.md): Strata 0.2.13, HyperQwen vLLM 0.33.0, Maya 1.1.57 installed by hand — November 9, 2026
- [ENGINE-UPDATES-20261109-HYPERQWEN-80cf059.md](evidence/ENGINE-UPDATES-20261109-HYPERQWEN-80cf059.md): HyperQwen `80cf059` installed by hand, with the review of the upstream diff — November 9, 2026
- [STRATA-LAYER-SPLIT-20261107.md](evidence/STRATA-LAYER-SPLIT-20261107.md): Flash-Next Strata hand-set layer split — November 7, 2026
- [BOLT-PROMPT-CACHE-20261107.md](evidence/BOLT-PROMPT-CACHE-20261107.md): Bolt RAM prompt cache enabled — November 7, 2026
- [BOLT-ID-RENAME-20261106.md](evidence/BOLT-ID-RENAME-20261106.md): Bolt API ID renamed to `bolt-llamacpp` — November 6, 2026
- [FLASH-IQ1M-STRATA-20261105.md](evidence/FLASH-IQ1M-STRATA-20261105.md): Flash-Next IQ1_M selected in Strata — November 5, 2026
- [FLASH-IQ1S-ENTRY-20261104.md](evidence/FLASH-IQ1S-ENTRY-20261104.md): Flash-Next IQ1_S entry — November 4, 2026
- [BOLT-NATIVE-IQ2-20261104.md](evidence/BOLT-NATIVE-IQ2-20261104.md): Native 2-bit Bolt with minimum tested CPU offload — November 4, 2026
- [BOLT-IQ2-ENTRY-20261104.md](evidence/BOLT-IQ2-ENTRY-20261104.md): Native IQ2 Bolt selected in API and DSH — November 4, 2026
- [BOLT-IQ2-AND-PROMETHEVS-20261104.md](evidence/BOLT-IQ2-AND-PROMETHEVS-20261104.md): Bolt low-offload direction and Promethevs — November 4, 2026
- [SGLANG-SUPER-SHORT-FIXES-20261101.md](evidence/SGLANG-SUPER-SHORT-FIXES-20261101.md): SGLang tool default and bounded Super swap policy — November 1, 2026
- [SGLANG-56K-448MIB-20261101.md](evidence/SGLANG-56K-448MIB-20261101.md): SGLang 56K context and 448 MiB free-VRAM floor — November 1, 2026
- [QWEN-LARGER-CONTEXT-20261101.md](evidence/QWEN-LARGER-CONTEXT-20261101.md): Larger Qwen27B context with less unused VRAM — November 1, 2026
- [QWEN-48K-CONTEXT-20261101.md](evidence/QWEN-48K-CONTEXT-20261101.md): Qwen27B context increased to 48K — November 1, 2026
- [NEMOTRON-CONTEXT-20261101.md](evidence/NEMOTRON-CONTEXT-20261101.md): NVIDIA Nemotron setup and short DSH checks — November 1, 2026
- [MAYA-UNSLOTH-20261101.md](evidence/MAYA-UNSLOTH-20261101.md): Unsloth DeepSeek on Maya — November 1, 2026
- [CONTEXT-VALIDATION-POLICY-20261101.md](evidence/CONTEXT-VALIDATION-POLICY-20261101.md): Context setup and short harness verification — November 1, 2026
- [BOLT-CONTEXT-20261101.md](evidence/BOLT-CONTEXT-20261101.md): Bolt 64K context and DSH registration — November 1, 2026
- [NEMOTRON-INT4-OFFLOAD-20261031.md](evidence/NEMOTRON-INT4-OFFLOAD-20261031.md): Nemotron INT4 offload startup checks — October 31, 2026
- [DEEPSEEK-UNSLOTH-CONTEXT-20261031.md](evidence/DEEPSEEK-UNSLOTH-CONTEXT-20261031.md): Additional Unsloth DeepSeek Strata profile — October 31, 2026
- [DEEPSEEK-DYNAMIC31-20261031.md](evidence/DEEPSEEK-DYNAMIC31-20261031.md): Unsloth Dynamic3.1 DeepSeek — bounded SSD qualification, October 31, 2026
- [BOLT-TWO-GPU-LOADING-20261031.md](evidence/BOLT-TWO-GPU-LOADING-20261031.md): Bolt loading on the RTX 3080 Ti and RTX 3080 — October 31
- [BOLT-TOOL-CALLING-20261031.md](evidence/BOLT-TOOL-CALLING-20261031.md): Bolt automatic tool calling — October 31
- [BOLT-MAYA-RELIABILITY-20261031.md](evidence/BOLT-MAYA-RELIABILITY-20261031.md): Bolt and DeepSeek/Maya reliability — October 31, 2026
- [MAYA-DEMAND-CACHE-20261029.md](evidence/MAYA-DEMAND-CACHE-20261029.md): Bounded model-file residency qualifies DeepSeek/Maya at 512 MiB
- [SGLANG-MTP3-512MIB-20261028.md](evidence/SGLANG-MTP3-512MIB-20261028.md): SGLang TP2 + MTP3 at 32K with a 512 MiB reserve — October 28, 2026
- [SGLANG-HETERO-MTP-20261028.md](evidence/SGLANG-HETERO-MTP-20261028.md): Isolated SGLang heterogeneous TP2 and MTP — October 28, 2026
- [SGLANG-DEPLOYMENT-20261028.md](evidence/SGLANG-DEPLOYMENT-20261028.md): Deployed SGLang TP2 + MTP3 W4A8 — October 28, 2026
- [SGLANG-CONTEXT-20261028.md](evidence/SGLANG-CONTEXT-20261028.md): SGLang context study — October 28, 2026
- [QWEN-STRATA-LCZ-20261028.md](evidence/QWEN-STRATA-LCZ-20261028.md): Qwen/Strata lcz.me setup on reduced RAM — October 28, 2026
- [SGLANG-W4A8-20261027.md](evidence/SGLANG-W4A8-20261027.md): Isolated SGLang MLP-only W4A8 test — October 27, 2026
- [SGLANG-TUNING-20261027.md](evidence/SGLANG-TUNING-20261027.md): SGLang pipeline and recurrent-state experiments — October 27, 2026
- [MOE-OPTIMIZATION-20261027.md](evidence/MOE-OPTIMIZATION-20261027.md): GLM and DeepSeek cache optimization — October 27, 2026
- [DENSE-ENGINE-OPTIMIZATION-20261027.md](evidence/DENSE-ENGINE-OPTIMIZATION-20261027.md): Qwen3.8-27B: mixed-Ampere vLLM and SGLang optimization
- [DEEPSEEK-STRATA-CONTEXT-20261027.md](evidence/DEEPSEEK-STRATA-CONTEXT-20261027.md): DeepSeek Maya-S / Strata context expansion — October 27, 2026
- [CONTEXT-EXPANSION-20261027.md](evidence/CONTEXT-EXPANSION-20261027.md): Context-expansion tests — October 27, 2026
- [QWEN27B-GPU-ONLY-20261026.md](evidence/QWEN27B-GPU-ONLY-20261026.md): Dense Qwen3.8-27B entirely in VRAM
- [HYPERQWEN-STARTUP-REATTACH-FIX.md](evidence/HYPERQWEN-STARTUP-REATTACH-FIX.md): HyperQwen stopped-worker classification and pending headroom check

### Historical handoffs, audits and research

- [NETWORK-README-LOG-THROUGH-20261108.md](evidence/NETWORK-README-LOG-THROUGH-20261108.md): NVIDIA model router, Tailscale and DeepSeek Harness (archived log)
- [MAINTAINED-PROFILES-LOG-THROUGH-20261108.md](evidence/MAINTAINED-PROFILES-LOG-THROUGH-20261108.md): Maintained model, quantization and engine settings (archived log)
- [REQUESTED-TWO-MODEL-CHECKS-20261103.md](evidence/REQUESTED-TWO-MODEL-CHECKS-20261103.md): Requested checks of the two enabled models — November 3, 2026
- [COMMUNITY-OPTIMIZATION-20261102.md](evidence/COMMUNITY-OPTIMIZATION-20261102.md): Community optimization screens — November 2, 2026
- [GPU-PAIR-AUX-OPTIMIZATION-20261031.md](evidence/GPU-PAIR-AUX-OPTIMIZATION-20261031.md): Main GPU pair and auxiliary 3060 optimization — October 31, 2026
- [AMD-PARITY-HANDOFF-20261027.md](evidence/AMD-PARITY-HANDOFF-20261027.md): NVIDIA-server agent handoff: AMD parity gaps — October 27, 2026
- [AMD-NVIDIA-GAP-AUDIT-20261027.md](evidence/AMD-NVIDIA-GAP-AUDIT-20261027.md): AMD/NVIDIA repository gap audit — October 27, 2026
- [VALIDATION-20261026.md](evidence/VALIDATION-20261026.md): Native validation - October 26, 2026
- [VALIDATION-20261025.md](evidence/VALIDATION-20261025.md): Preparation validation — October 25, 2026
- [MIGRATION-HANDOFF.md](evidence/MIGRATION-HANDOFF.md): NVIDIA Windows-to-Linux handoff — October 25, 2026
- [FORUM-OPTIMIZATION-SOURCES.md](evidence/FORUM-OPTIMIZATION-SOURCES.md): Forum and upstream references for NVIDIA context tuning
