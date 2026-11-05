# Maintained model, quantization and engine settings

## Unused Qwen GGUF target/drafter deleted — November 4, 2026

The unconfigured Qwen3.8-27B Q4_K_M target and its MTP-only GGUF drafter were deleted at the user's request: 19.450 GB of weights. All nine configured entries, the selected TensorFold DFlash2 drafter and every maintained checkpoint/runtime remain unchanged. No inference or regression suite was repeated; unchanged-catalog/checkpoint and API/DSH checks verify preservation. Historical results remain dated evidence. [Removal record](UNUSED-QWEN-GGUF-REMOVAL-20261104.md).

## Retired AWQ Bolt assets deleted — November 4, 2026

The user requested deletion of the retired AWQ setup. Its55.33 GB weights, dedicated vLLM environment, manifest, launch/supervision/offload code and AWQ-only tests are removed. Native IQ2 remains selected under compatibility ID`bolt-vllm`; all nine profiles, both DSH modes, defaults, guards and shared runtimes are preserved.423 remaining CPU tests passed;33 obsolete adapter tests were retired. Native runtime hashes/dependencies and API/DSH health passed; no model benchmark was repeated. Historical benchmark records and small private source/configuration preimages remain, but the old checkpoint/runtime are no longer installed. [Removal verification](BOLT-AWQ-REMOVAL-20261104.md).

## Current: native IQ2 Bolt replaces AWQ in API/DSH — November 4, 2026

Bolt now selects the official native IQ2 text model on pinned llama.cpp11909, both GPUs, 384 MiB fit targets and unchanged 163,840-token allocation. The historical `bolt-vllm` ID remains for compatibility; API metadata and both DSH display names now identify native IQ2/llama.cpp. Normal-router actual DSH read/result/exact follow-up and owned unload passed: 502.58 prefill tok/s, 12.870 s client TTFT and 68.05 decode tok/s. All nine entries remain, with unrelated routes/defaults and all guards preserved. 456 CPU tests passed; workers finish idle and updates stay paused. Older AWQ measurements and candidate-only status below are dated history. [Selected entry, guards and AWQ slowdown research](BOLT-IQ2-ENTRY-20261104.md).

## Native IQ2 Bolt tested on both GPUs — November 4, 2026

The isolated official native IQ2 Bolt candidate passed an actual DSH read/result/exact-follow-up and owned unload at163,840 context on pinned llama.cpp11909. The minimum tested passing fit margin384 MiB/card retains89.4% of weight-buffer bytes on the GPUs with2.18 GiB CPU-mapped weights:506.46 prefill tok/s,12.744 s client TTFT and67.49 decode tok/s, versus the retained same-day AWQ217.35 /29.320 /0.361. The256 MiB fit arm hit the unchanged256 MiB VRAM floor during prefill and is rejected;512 MiB also passed. These are short complete-configuration observations, not an equal-quality or sustained-speed claim.451 CPU checks passed. Both GPUs finish idle, no reservation remains and API/hub/DSH are healthy. All nine selected entries and defaults remain; IQ2 is a separate qualified candidate, not a replacement entry. [Results, guard/placement evidence and failed arms](BOLT-NATIVE-IQ2-20261104.md).

## Current: all nine restored with two-GiB headroom — November 4, 2026

The corrected boot passed early GPU unlock and current-boot host-staged transport. Linux sees 91.76984787 GiB usable RAM. All nine normal-router DSH read/result/exact-follow-up and owned-unload checks passed; all entries are enabled and workers finish idle. The six RAM-heavy profiles now use 87.76984787/89.76984787 GiB high/hard limits, leaving exactly 2 GiB outside the hard cap as requested. Dense profiles retain 32/36 GiB; the independent 2 GiB available-memory stop and all other guards remain. 446 CPU tests passed. Larger supported caches are selected; runtime pins, contexts and defaults are preserved, and daily updates remain paused. This supersedes earlier preparation/waiting and temporary 32 GB operational descriptions below; historical measurements retain their dates and hardware. [All nine benchmarks, exact guard tables and resource evidence](RAM96-RESTORATION-20261104.md).

## Larger RAM verified; restoration prepared, GPU checks awaiting firmware — November 4, 2026

Linux now sees 91.77 GiB usable RAM. Nine larger-RAM candidate definitions and cache configurations are prepared: dense 32/36 GiB worker caps, RAM-heavy 84/86 GiB, and a new 90 GiB minimum measured-capacity gate.445 CPU tests passed. Five paused profiles remain disabled; no GPU benchmark or restoration qualification has run. Secure Boot is enabled again, early GPU unlock health failed and its dependent current-boot transport proof is missing. The human chose preparation first and will correct Secure Boot/reboot later. No guard was bypassed; other policies, engine pins, contexts and defaults are preserved. API/hub/DSH remain healthy and GPU workers are idle. Earlier benchmark rows retain their measured 32/64 GB scope. [Prepared settings, forum/pinning research and continuation](RAM96-PREPARATION-20261104.md).

## Flash-Next IQ1_S entry enabled — November 4, 2026

`flash-next-iq1s-llamacpp` is now the fourth enabled API/DSH entry: the same verified Unsloth v3.1 IQ1_S checkpoint, llama.cpp11909, 12,288 context and lazy NVMe n-gram table. Normal-router actual DSH read/result/exact-follow-up and owned unload passed:88.79 prefill tok/s,66.292 s client TTFT and31.10 decode tok/s. RAM26/28 GiB, host2 GiB, GPU256 MiB/card, swap128/160 MiB/s over30 s,15% active full PSI, thermal82 C and all ownership/telemetry guards remain. All441 CPU checks passed. The five older profiles stay disabled, defaults are preserved and workers finish idle. Earlier isolated-candidate descriptions are dated history; this is the current operational state. [Entry and guard evidence](FLASH-IQ1S-ENTRY-20261104.md); [all current and historical entry benchmarks](ALL-ENTRY-BENCHMARKS-20261104.md).

## Worker RAM raised to 26/28 GiB; requested reruns passed — November 4, 2026

All eight profile definitions now use 26/28 GiB soft/hard worker limits. HyperQwen, SGLang, TensorFold DFlash2/copies and the isolated Flash-Next IQ1_S SSD-table candidate each passed one fresh actual DSH tool/result/exact-follow-up and owned unload; 438 CPU regressions passed. The other five profiles remain disabled. Host2 GiB, VRAM256 MiB/card, thermal82 C, swap/PSI/transport/ownership guards, contexts, weights and defaults remain unchanged. Flash-Next measured93.35 prefill tok/s,63.238 s client TTFT and 28.23 decode tok/s; sampled swap483 MiB and soft-limit reclaim persisted, so larger limits showed no speed improvement in this single run. All workers are stopped, GPUs1 MiB each, API/hub/DSH active and no reservation remains. This supersedes earlier24/26 GiB operational descriptions; historical results retain their original guards. [Results, comparison and guard tables](RAM26-28-RERUN-20261104.md).

## TensorFold DFlash2/copies entry enabled — November 4, 2026

The user-requested `qwen27b-tensorfold` entry is enabled alongside HyperQwen and SGLang, with the same tested EXL3 2.0bpw target, 4-bit DFlash2 drafter, automatic copies and 12,288 context. The normal-router actual DSH tool/result/exact-follow-up and owned unload passed: 581.98 prefill tok/s, 10.019 s TTFT and 183.92 decode tok/s on a short speculative tool burst. Single GPU0 plus host-mapped embeddings; native 1 GiB reserve and all resource guards remain. API/DSH show three entries; defaults are preserved and workers finish idle. The separately requested Flash-Next IQ1_S passed an isolated actual DSH tool/result/exact-follow-up and owned unload with its n-gram table lazily mapped on NVMe: 101.50 prefill tok/s, 58.113 s client TTFT and 29.14 decode tok/s at 12K. All three publisher hashes and native/process mapping proof passed; no guard violation. Soft RAM reclaim and287 MiB sampled swap are recorded, with bounded active rates. It remains an isolated candidate; the enabled menu has three entries and older disabled RAM profiles stay disabled. This update supersedes earlier same-day candidate-only and two-enabled-entry descriptions. [Configuration, guards and results](TENSORFOLD-ENTRY-AND-FLASH-IQ1S-20261104.md).

## TensorFold candidate and Unsloth v3.1 assessed — November 4, 2026

Experimental TensorFold1.2.2 Qwen27B EXL3 2.0bpw passed actual DSH read/result/exact-follow-up and owned unload: plain16K measured584.6 prefill /9.982s TTFT /34.40 decode; DFlash2-4bit12K measured576.6 /10.108s /180.38tok/s on a short tool-argument burst. Single GPU0 and host-mapped embeddings, lower precision/context, no production promotion. Failed8K client-budget and16K drafted-memory admissions are retained; no guard was relaxed. All test workers are stopped, GPUs idle, reservation released, API/hub/DSH preserved. Unsloth's new IQ1_S plus SSD-mapped n-gram table is a plausible separate candidate; no Flash-Next weights downloaded or disabled profile restored. [Evidence and limits](TENSORFOLD-AND-UNSLOTH-ASSESSMENT-20261104.md).

## Requested enabled-model checks passed — November 3, 2026

After the user confirmed RAM is not yet upgraded, HyperQwen and SGLang each passed one short actual DSH read/tool-result/exact-follow-up, normal owned unload and GPU release. Fresh single-call prefill/TTFT/decode observations are 2077.9 tok/s / 2.821 s / 62.53 tok/s and 2137.9 tok/s / 3.044 s / 60.20 tok/s respectively. Tool calls and follow-ups passed; both test workers are inactive and both GPUs returned to 1 MiB used. API/hub/DSH remain active; no GPU reservation remains. Settings/guards are unchanged; all five RAM/offload profiles remain disabled. No full-context or sustained test. See [results, guard tables and loading-transient limits](REQUESTED-TWO-MODEL-CHECKS-20261103.md).

## Current operation and DSH repair — November 3, 2026

DSH uses an explicit headless service mode; desktop launches retain their required visible monitor. The API and private hub remain independent. The current host has **temporary 32 GB RAM**; only **HyperQwen 86,016** and **SGLang 57,344** are enabled. Both retain 24/26 GiB worker budgets, the 2 GiB host reserve, **256 MiB per-GPU free-VRAM floor**, swappiness 60 and idle 600 seconds. Unlock and current-boot host-staged transport are verified; the native-output buffering repair remains deployed. RAM/offload profiles remain disabled until explicit hardware confirmation, measured capacity and guarded requalification. Daily updates remain paused.

See [the current repair and remaining work](DSH-STARTUP-REPAIR-20261103.md). Older dated status paragraphs and benchmark numbers retain their historical hardware/guard scope; they do not override this current state. Standing instructions remain applicable. No new model benchmark was run.

## Provider abort repaired: unbuffered native channel evidence — November 3, 2026

Longer normal client use exposed a remaining false transport-guard stop: one NCCL rank buffered SHM channel logs until exit. Dense launchers now force PYTHONUNBUFFERED=1 through engine/rank startup; the transport deadline and all resource guards remain unchanged. Live SHM proof and two normal completed SSE responses from the same invocation, separated by 36 seconds, pass. 98 focused CPU checks include a real C-stdout visibility regression. Earlier short speed observations do not establish sustained behavior. The user's selected HyperQwen worker remains loaded; RAM/offload profiles remain temporarily disabled. [Repair evidence](PROVIDER-ABORT-BUFFERING-20261103.md).


## Verified unlocked VRAM-only operation; RAM models temporarily disabled — November 3, 2026

After reboot, Secure Boot is disabled, ordered GPU unlock is VERIFIED, and the direct CPU PCIe4 x8/x8 host-staged proof passes with CUDA peers unavailable both ways. The iGPU runs the desktop. Only Qwen3.8-27B HyperQwen/vLLM and SGLang remain enabled; both pass real tool/result/follow-up and owned unload on temporary 32 GB RAM. Bolt and all four streaming/offload profiles are temporarily blocked pending the RAM upgrade, with definitions/weights preserved. The overlooked P2P-only runtime guards are corrected to require disabled P2P and bidirectional SHM with bounded startup-log grace; all memory/swap/temperature guards remain. 97 focused CPU checks pass. Do not restore RAM profiles/caches until explicit hardware confirmation, capacity measurement and guarded qualification. [Current evidence](UNLOCKED-VRAM-ONLY-20261103.md).


## Z690 / 13900KS / temporary 32 GB migration — November 3, 2026

The current host is the MSI Z690 Carbon WiFi DDR5 / i9-13900KS with temporary 32 GB RAM while awaiting the planned upgrade, Intel UHD 770 desktop and direct CPU PCIe4 x8/x8 RTX 3080 Ti/3080. The external PCIe switch and Crucial NVMe are removed. Stock signed NVIDIA 615.71.09 is loaded; actual CUDA peer capability is zero both ways. Maintained launches disable P2P/custom all-reduce, and the switch ACS service is disabled. All worker budgets are 24/26 GiB with bounded cache preparation; other resource guards remain. 77 focused CPU checks pass. The subsequent reboot verified unlock and both enabled VRAM-only engines; RAM/offload requalification is deferred pending the RAM upgrade. Preboot preparation below remains historical evidence. Startup requires the new root-owned current-boot host-staged proof and successful early unlock. Do not demand a switched-P2P proof on this host, re-enable the switch driver/ACS policy, restore 64 GB caches, or relabel historical benchmarks as new-host results. Headless physical-input activation remains unchanged. [Status and remaining checks](Z690-13900KS-MIGRATION-20261103.md).


## GLM engine 1.1.50 selected; 256 MiB reruns — November 3, 2026

GLM selects the normal 1.1.50 engine at unchanged 65,536 context after two passing short matched pairs: tool-call decode improved 17–24%, with mixed prefill. Versioned binary/profile/hash pin and normal-router tool/unload passed; 19 focused CPU checks passed. HyperQwen and SGLang MTP remain memory-blocked under the 256 MiB floor; Bolt pinning still hits oomd and prefetch-two offered no material gain; DeepSeek retains 1.1.46 because new arms did not improve overall and its quant prevents new P2P all-reduce. Other guards and Strata prefill 512 remain unchanged. [Full evidence and limits](VRAM256-OPTIMIZATION-20261103.md).

## Headless-server VRAM floor — November 2, 2026

The selected free-VRAM stop floor is now **256 MiB per card**, including SGLang. Other guards, contexts and native cache allocations remain unchanged.54 focused CPU checks passed; no new inference qualification. Earlier448/512 MiB results retain their historical guard attribution. [Policy and validation](HEADLESS-VRAM256-20261102.md).

## Confirmed Strata prefill improvement — November 2, 2026

DeepSeek/Strata selects prefill chunk512 at unchanged32K context after two guarded baseline/candidate pairs: uncached prefill improved25.6%/27.5%, with passing tool/result/follow-up and unload. Normal-router tool/unload and15 focused tests passed. Other settings remain selected; negative confirmations and guarded startup failures are retained. All guards remain unchanged. [Results and limits](COMMUNITY-OPTIMIZATION-20261102.md).

## SGLang 56K with scoped 448 MiB floor — November 1, 2026

SGLang uses 57,344 tokens with a 448 MiB free-VRAM floor; short tool/unload and native KV checks passed with 469 MiB minimum sampled free. HyperQwen remains 86,016 tokens / 512 MiB floor. Other guards are unchanged. No full-context test. [Evidence](SGLANG-56K-448MIB-20261101.md).

## Qwen27B context increased further — November 1, 2026

HyperQwen now uses 86,016 tokens; SGLang 55,296. Native KV capacity, short DSH read tools, sampled VRAM floor and owned unload passed. SGLang 57,344 was rejected after a 469 MiB transient. Guards remain unchanged; no full-context qualification. [Results](QWEN-LARGER-CONTEXT-20261101.md).

## Qwen27B engines increased to 48K — November 1, 2026

HyperQwen and SGLang now both use 49,152 tokens, backed by native KV allocation and passing short DSH tool/unload checks. Guards are unchanged; no new full-context quality claim. [Settings, VRAM and timings](QWEN-48K-CONTEXT-20261101.md).

## Nemotron Super removed — November 1, 2026

All installed Nemotron Super weights, dedicated runtime and active profile/launcher support have been removed at the user’s request. Seven maintained profiles remain, including Bolt. Both retired Super IDs return HTTP 404; workers are idle. Historical Super results below are dated evidence only. [Removal and validation](NEMOTRON-SUPER-REMOVAL-20261101.md).

## API-only router all-model check — November 1, 2026

Seven maintained profiles passed measured short DSH read-tool calls and owned unload. Super/vLLM failed its unchanged loading-pressure guard before readiness; no new speed result. Final workers inactive, no GPU reservation; current-boot unlock/P2P checks pass. See [new-router results](NEW-ROUTER-BENCHMARKS-20261101.md). Older successful measurements remain historical.

## Current short-tool observations — November 1

The eight retained profiles now have prefill, TTFT and decode observations measured during actual short DSH read calls, with successful matching tool results and owned unload. DeepSeek/Maya and DeepSeek/Strata share the existing Unsloth UD-IQ1_S checkpoint; the older Maya-S Strata profile is retired. Current configured contexts are 40K HyperQwen, 32K SGLang, 128K Flash-Next, 64K GLM, 32K both DeepSeek engines, 160K Bolt and 64K Super. These calculated windows were not subjected to a new full-context test. [Table, cache state and measurement limits](SHORT-TOOL-BENCHMARKS-20261101.md).

## Latest: restored 64GB worker budgets applied — October 31

All six MoE profiles now use 56 GiB soft / 58 GiB hard worker limits. Both GPU-resident Qwen profiles retain their explicitly uncapped RAM setting. Linux sees 61.3 GiB usable; the independent 2 GiB host-available stop and all VRAM,swap,pressure and temperature guards remain active. Contexts and other model settings are unchanged. All eight actual kernel cgroup settings and 321 CPU tests passed; no inference job was interrupted. [Policy and verification](WORKER-RAM-64GB-20261031.md).

The additional Unsloth Dynamic3.1 UD-IQ1_S DeepSeek/Strata profile is selected at
**32,768 tokens**. It appears separately in the Strata shortcut menu and uses
`deepseek-unsloth-strata` through the router. Existing seven profiles are unchanged.
It reuses the already downloaded 232.98 GB GGUF, with core shards on NVMe and Engram
on SATA. Its context screen and stream observations are not a matched benchmark
against the older Maya-S quant; see [the qualification](DEEPSEEK-UNSLOTH-CONTEXT-20261031.md).

## Historical selected speed evidence (October 31 composite runs)

These separate screens are not a matched comparison. Six earlier rows use one warmup and three 128-output requests; Bolt uses one 128-output stream after correctness/retrieval, without a dedicated fixture warmup. Loading is excluded. Native prefill and client SSE first-to-last-content decode methods are retained. See [scope and reliability](BOLT-MAYA-RELIABILITY-20261031.md).

### VRAM-only models

| Model / quant | Engine | Prefill (tok/s) | TTFT (s) | Decode (tok/s) | Context (tokens) | Base weights (GB) | Storage |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Qwen3.8-27B / AutoRound-INT4-fast-heads-INT8-embedding | HyperQwen-vLLM | 2516.49 | 0.891 | 112.140 | 56,320 | 15.79 | SATA: models/engine-tests/qwen38-27b-hyperqwen-fast |
| Qwen3.8-27B / AutoRound-INT4-fast-heads-INT8-embedding | SGLang | 2778.24 | 0.804 | 95.864 | 32,768 | 15.79 | SATA: models/engine-tests/qwen38-27b-hyperqwen-fast |

### MoE models with CPU RAM offload

| Model / quant | Engine | Prefill (tok/s) | TTFT (s) | Decode (tok/s) | Context (tokens) | Base weights (GB) | Storage |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| NVIDIA-Nemotron-3.5-Bolt-74B-A9B / AWQ-INT4 | vLLM-offload | 253.66 | 11.427 | 0.451 | 8,192 | 55.33 | SATA: models/bolt-awq-int4 |

### MoE models with SSD streaming

| Model / quant | Engine | Prefill (tok/s) | TTFT (s) | Decode (tok/s) | Context (tokens) | Base weights (GB) | Storage |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Qwen3.8-Flash-Next / IQ3_XXS | Strata | 695.20 | 3.199 | 98.416 | 32,768 | 75.84 | NVME: models/strata/models/IQ3_XXS |
| GLM-5.3-Flash / Maya-S24 | Maya | 74.10 | 29.837 | 6.389 | 65,536 | 94.70 | NVME: models/maya/Maya-S24 |
| DeepSeek-V4.1-Flash-1017 / Maya-S | Strata | 30.80 | 70.845 | 3.271 | 131,072 | 339.48 | NVME: models/maya/DeepSeek-V4.1-Flash-1017-GGUF/Maya-S |
| DeepSeek-V4.1-Flash-1017 / Maya-S | Maya | 46.70 | 46.835 | 1.887 | 32,768 | 339.48 | NVME: models/maya/DeepSeek-V4.1-Flash-1017-GGUF/Maya-S |
| DeepSeek-V4.1-Flash-1017 / UD-IQ1_S (Unsloth Dynamic3.1) | Strata | — | — | — | 32,768 | 232.98 | NVMe core / SATA Engram |

Storage uses decimal GB of base weights. Qwen engines share base weights, as do the two maintained DeepSeek engines; count each base once. Prepared packs/caches are excluded. Earlier evidence remains historical.

## Latest: qualified bounded DeepSeek/Maya cache — October 29

DeepSeek/Maya passed at **512 MiB native VRAM reserve and unchanged 32,768-token context** on the 45.55 GiB reduced-RAM host. The selected temporary configuration combines a 16 GiB model-file cache target with a native 12 decimal GB pinned hot-expert cache. JSON, arithmetic, image, 29,467-input-token retrieval, 426.5s continuous generation, a fresh isolated process reload and two normal guarded loads all passed. Observed worker swap occupancy and swap read/write rates were zero.

The saved three-request screen measured **1.23 decode tok/s**, 42.5 prefill tok/s and 51.491s TTFT. Earlier full-RAM/historical rates remain preserved; no fresh paired 2,048 MiB control was produced, because the earlier reduced-RAM configuration failed its swap guard.

This supersedes the earlier unresolved DeepSeek/Maya reduced-RAM status only for
this qualified configuration. Other five selected settings/results remain unchanged;
Flash/Strata's earlier reduced-RAM failure remains unresolved. Native warming limits
did not bound demand mmap residency; the new controller targets clean model-file
residency, with overshoot possible between scans. Its qualified binary is hash-pinned.

The host 2 GiB floor, 46/48 GiB MoE worker budget, dense 512 MiB free-VRAM stop,
82 C thermal limit, owned swap/PSI/telemetry guards, swappiness 60, concurrency one
and idle 600s remain. Original native source/binary and archived preimages remain;
weights, precision and mathematical kernels are unchanged. Router idle, owned
workers stopped, no GPU reservation, DSH preserved and no fallback.

After explicit human RAM-restoration confirmation, verify Linux capacity, restore
appropriate full-RAM cache/prefill choices from preimages while preserving the
qualified VRAM reserve and guards, then verify normal guarded load/reload.
No timer or MemAvailable trigger.

See [demand-cache qualification and six selected results](MAYA-DEMAND-CACHE-20261029.md)
and [numeric evidence](benchmark-results/20261029-maya-demand-cache.json).


`config/maintained-profiles.json` is the current registry: **eight selected
profiles**, with one entry for each `(model, weight quantization, engine)`.
The dense launchers read their arguments directly from this file. Strata and
Maya entries identify their single canonical private runtime setting; credentials
stay outside the exported registry.

A weight quantization identifies model weights. KV precision, activation
precision, speculative-token count, prompt chunk size and context allocation are
tuning choices within that group. They do not justify parallel speed/long-context
presets for the same weight quant and engine.

## Storage

[The storage policy](STORAGE-POLICY.md) puts GPU-resident Qwen27B and all dense
trial weights on SATA. Flash-Next, GLM and DeepSeek keep their SSD-streaming
weights on NVMe. The registry records the required transport; stable aliases
keep both shared-checkpoint engine pairs working.

## Selection rule

Keep a qualified configuration that is not dominated on prefill/first-token
latency, decode and safe validated context. When speed and capacity trade off,
prefer the largest locally validated safe allocation with competitive speed,
then use prefill/TTFT and decode to resolve ties. Preserve memory, numerical,
quality, thermal and owned-process safeguards. This is a best-known balanced
selection from saved tests, not a claim that one setting maximizes every metric
or that untested larger contexts work.

## The six retained profiles

HyperQwen and SGLang no longer have the 30/36 GiB per-worker RAM caps.
Their normal guarded launches passed JSON and actual MemoryHigh/MemoryMax
infinity readbacks (cgroup memory.high/memory.max=max). Ownership enforcement,
host-available floor 2 GiB, dense free-VRAM floor 512 MiB, temperature 82 C,
active owned-worker swap/PSI/telemetry stops, swappiness 60, concurrency one and
idle unload 600 seconds remain. MoE worker RAM budgets are unchanged.
Forty-two CPU guard/ownership/budget/runtime checks passed; no dense speed or
context measurements were repeated.

GLM and both DeepSeek engines were tested with 512 MiB native VRAM allocation
reserves on the current reduced-RAM machine. Only profiles passing isolated
quality, near-window retrieval, sustained generation, fresh-process reload and
normal guarded loading were applied:

- deepseek-maya: 512 MiB candidate not applied; original 2,048 MiB reserve retained.
- glm-maya: 512 MiB reserve qualified and applied.
- deepseek-strata: 512 MiB reserve qualified and applied.

Native allocation reserves and the dense minimum-free-VRAM stop are different
controls. All model/cache/context choices were preserved, and prior benchmark
values remain historical evidence. Only applied candidates have new selected
measurements. The two early GLM/Strata connection failures occurred before engine
loading because the router cached the old dense-budget validator; corrected
trials supersede those setup failures. One idle router reload loaded the new
validator with no worker interrupted; DSH was preserved.

Final router idle, owned workers stopped and no GPU reservation; no fallback
restored. Next action: after explicit human DIMM-restoration confirmation, verify
Linux capacity, restore appropriate full-RAM cache values and verify guarded
loading. Preserve the separately approved dense cap removal, host reserve and
qualified VRAM selections unless the human revises them. No timer trigger.

See [qualification and current results](MOE-VRAM512-20261029.md) and
[numeric evidence](benchmark-results/20261029-moe-vram512.json).

October 29: all six profiles explicitly select a 2 GiB host reserve. Dense/MoE
supervisors and the benchmark monitor share this selection; 41 CPU checks passed.
Model/cache/context choices and all table measurements are unchanged. See
[all-profile policy verification](ALL-PROFILES-HOST-RESERVE2-20261029.md).

The human-approved host reserve is now **2 GiB across all six profiles**. The 2 GiB pageable retest still failed the active swap guard, so its model/
cache setup and 53.29 tok/s rejected screen were not promoted. Current table values
remain unchanged. See [guard change and evidence](QWEN-HOST-RESERVE2-20261028.md).

Qwen/Strata follow-up: the lcz.me pageable full-resident setup was refused for
insufficient RAM headroom; a 28 GiB pageable adaptation hit swap-churn protection.
Neither was applied. Qwen remains unqualified on reduced RAM. Current settings
and numeric table rows below are unchanged by this follow-up; see
[the tested configuration and evidence](QWEN-STRATA-LCZ-20261028.md).

2 of the four SSD-streaming profiles now have bounded qualification with one 16 GiB
DIMM removed (45.55 GiB usable): unchanged contexts, JSON/arithmetic, near-window
retrieval, supported images, sustained generation, fresh-process reload and normal
router loading. Qualified cache choices are deployed temporarily. This supersedes earlier
reduced-RAM caveats only for these selected settings and this
bounded workload; it does not establish multi-hour reliability or an exhaustive
cache optimum. Dense measurements were carried forward without retesting.

- `glm-maya`: 2.11 decode tok/s (-56.1% against saved full-RAM fixtures), 65,536 context; 231.1s continuous generation and fresh-process reload passed.
- `deepseek-strata`: 1.80 decode tok/s (-39.2% against saved full-RAM fixtures), 131,072 context; 381.1s continuous generation and fresh-process reload passed.

Comparisons use saved historical full-RAM fixtures, not a fresh paired full-RAM
control. Preserve swappiness 60, 512 MiB dense reserve, native MoE GPU reserves,
host floor 2 GiB across all six profiles, 82 C temperature limit, unchanged MoE worker budgets, uncapped dense RAM and active
swap/churn/pressure/telemetry guards, concurrency one and 600-second idle unload.
Normal validation finished idle; router and DSH ownership were preserved and no
fallback was restored. Original credential-redacted settings are archived privately
with hashes; raw credentials and study evidence stay local.

Restore the appropriate full-RAM cache settings only after explicit human
confirmation that the DIMM is restored and Linux capacity verification, followed
by normal guarded loading checks and selected-setting metadata updates. A rise
in MemAvailable or elapsed time does not trigger restoration. Preserve unrelated
router/desktop improvements, credentials, guards and independent speed history.

See [qualification and all six current results](REDUCED-RAM-20261028.md) and
[machine-readable evidence](benchmark-results/20261028-reduced-ram.json).

Unresolved on reduced RAM: `deepseek-maya`, `flash-next-strata`. Their original cache settings and historical full-RAM table values are retained; they may stop at the unchanged guards. No passing reduced-RAM operating configuration or reliable slowdown percentage was established for them.

HyperQwen uses 704 MiB KV/rank and 256-token chunks. SGLang now uses the
[deployed TP2/MTP3 W4A8 runtime](SGLANG-DEPLOYMENT-20261028.md), BF16 state/KV,
one Mamba slot and 384-token chunks at 32K, with a 512 MiB free-VRAM floor.
This generation-first selection supersedes PP2 FP32; other profiles are unchanged.
See [context decisions and trials](CONTEXT-EXPANSION-20261027.md). Initial benchmark
and retrieval runs keep their actual legacy/new swap-policy attribution.

Older speed measurements are retained in dated reports and registry benchmark history. The current table is at the top of this page.

## Launching

```bash
python3 scripts/profile_catalog.py
./scripts/start_model.sh qwen27b             # default: HyperQwen, 56,320 tokens
./scripts/start_model.sh qwen27b sglang      # SGLang, 32K
./scripts/start_model.sh qwen                # Flash-Next / Strata
./scripts/start_model.sh glm                 # GLM / Maya
./scripts/start_model.sh strata-deepseek
./scripts/start_model.sh maya-deepseek
```

These commands are alternatives, not a sequence to run concurrently. Only one
worker may occupy authenticated port 10000. MoE commands require the installed
router service. Existing stop commands, memory
boundaries, credential permissions and GPU checks remain in force. The registry
rejects duplicate model/weight-quant/engine groups and launch selections. Dense
context metadata must match engine arguments, and unqualified CPU weight offload
is rejected.

Strata's launch preset, generated runtime file and runtime wrapper are one
launch chain, not three independently tuned profiles. The duplicate DeepSeek
alias `launch-deepseek-strata` has been retired; `deepseek-maya-s` remains the
canonical runtime profile. Maya retains one private configuration per model/quant.
Vendor example files inside installed upstream source trees are not maintained
workstation presets and were not modified.

## Retired settings and retained evidence

Before removal, twelve source/configuration files were copied and hash-verified
in the private `Biegle-W/retired-llm-setting` repository, batch
`linux-nvidia/2026-10-27-profile-consolidation`, commit
`7c8d543`. Its manifest records paths, modes, SHA256 values, dates, reasons and
source commits where the originals were tracked. Ignored/external settings are
identified as local state rather than falsely assigned a Git blob revision.

The batch contains eight obsolete trial launchers, the duplicate Strata alias,
the disabled Windows-origin inventory, and the two pre-consolidation dense
launcher sources. At consolidation, both dense launchers were changed to consume the selected catalog;
the old inventory is a disabled retirement pointer. Old trial launchers and the
duplicate alias have been removed from their operational locations.

Completed requests, raw settings snapshots, qualifications, regressions, failure
logs, benchmark summaries and required patch/kernel fixtures remain as dated
evidence. They are not registered as runnable presets. No weights, runtime
environments, credentials, chats or raw logs were uploaded to the archive. No
model weights were removed during that consolidation. Future result lists should show these six retained
profiles first and label all other trials historical or unqualified.


## Removed IQ4_XS deployment

The slower Qwen3.8-27B IQ4_XS llama.cpp profile was subsequently removed at the
user's request. Its catalog entry, launch selection and dedicated launcher were
removed, along with the 15,475,951,328-byte GGUF and its local download metadata.
HyperQwen and SGLang retain the shared AutoRound checkpoint. The shared llama.cpp
runtime and numerical-test tools remain installed.

The retired launcher, pre-removal catalog and publisher-verified model provenance
are hash-verified in the private retirement repository, batch
`linux-nvidia/2026-10-27-qwen27b-iq4xs-removal`, commit `e46d38c`.
The model weights were not uploaded to that archive. Historical benchmark and
retrieval results remain preserved; they no longer describe an installed model.

## Unused model artifacts

The [unused-model cleanup](UNUSED-MODEL-CLEANUP-20261027.md) removed superseded trial checkpoints and
preparation payloads after reviewing saved results and screening DSpark in both
DeepSeek engines. All six selected profiles, allocated contexts and kept benchmark
values are unchanged; historical reports are evidence rather than download lists.

## Context/lifecycle retirement checkpoint

The later 12-file replacement batch is archived privately at
`linux-nvidia/2026-10-27-context-swap-lifecycle`, commit `15e6f2e`. All 12 committed
snapshot hashes match the manifest; JSON credential fields are omitted. It holds
replaced guards, the pre-upgrade registry and two changed native settings, plus
the before-idle source adapters. The four qualified upgrades are independent of
Maya's unchanged/unresolved setting. DSH chats/settings, weights, full runtime
distributions and raw logs are excluded.

The two supervisor sources immediately before the intentional-shutdown fix are
archived separately in `linux-nvidia/2026-10-27-intentional-shutdown-fix`, commit
`0840f24`, with original/stored hashes verified. The fix prevents false missing-
telemetry latches during requested shutdown; unexpected failures remain guarded.


The later [38K qualification](SGLANG-38K-QUALIFICATION-20261028.md) passed isolated
quality/history/tools and sustained resources under the accepted proportional
policy. Normal reload backed only 37,501 of 38,912 advertised tokens, so promotion
was rejected and the selected 32K profile/speed table above remains current.
No speed screens were repeated; source/precision/budgets/guards remain unchanged.


October 29 follow-up: three additional DeepSeek/Maya 512 MiB cache candidates failed
the unchanged swap guard; selected settings and all six table results remain unchanged.

See [DeepSeek/Maya follow-up](MAYA-DS4-VRAM512-FOLLOWUP-20261029.md) and
[numeric evidence](benchmark-results/20261029-maya512-followup.json).


## Current Qwen/Flash-Next guard test — October 29

The unchanged normal Qwen/Flash-Next Strata preset was tested through the router
with the current guards. It failed during loading: native startup announced
about 47 GB of RAM experts and a 39.97 GiB expert arena; host available fell to 0.717 GiB
(free 0.408 GiB), below the 2 GiB supervisor floor. Peak temperature 42 C; no cgroup
high/max/OOM event. The RAM guard stopped it safely before readiness.

Loading swap peaked at 1.68 GiB, but this was not an active-inference swap stop:
no inference window was reached. JSON/image/retrieval/sustained/reload checks
were not reached. No speed benchmark was repeated;97.09 tok/s remains historical.

Source/cache/context settings and every guard remain unchanged. 44/48 GiB cgroup
limits and unlimited loading swap occupancy were read back. Router/DSH preserved,
worker stopped, router idle, no reservation/fallback. This is a current reduced-RAM
resident-allocation failure, not general incompatibility between Qwen and Strata.
The other five selections remain unchanged. Do not apply rejected pageable variants
or restore full-RAM settings without explicit human confirmation and Linux capacity
verification. Further cache tuning requires its own qualification.

See [current normal-profile test](QWEN-CURRENT-GUARDS-20261029.md) and
[numeric evidence](validation-results/20261029-qwen-current-guards.json).
