# Maintained model, quantization and engine settings

`config/maintained-profiles.json` is the current registry: **six selected
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

### VRAM-only models

| Model / quant | Engine | Prefill (tok/s) | Time to first token (s) | Decode (tok/s) | Context limit (tokens) | Storage size (GB) | Storage location |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Qwen3.8-27B / AutoRound INT4 / INT8 embedding | HyperQwen-vLLM | 1,491.7 | 1.499 | 89.10 | 56,320 | 15.79 | Samsung SSD 870 QVO SATA: models/engine-tests/qwen38-27b-hyperqwen-fast |
| Qwen3.8-27B / AutoRound INT4 / INT8 embedding | SGLang | 1,667.9 | 1.346 | 84.76 | 32,768 | 15.79 | Samsung SSD 870 QVO SATA: models/engine-tests/qwen38-27b-hyperqwen-fast |

### MoE models with CPU RAM offload

None currently kept. Expert RAM tiers in streamed profiles are caches.

### MoE models with SSD streaming

| Model / quant | Engine | Prefill (tok/s) | Time to first token (s) | Decode (tok/s) | Context limit (tokens) | Storage size (GB) | Storage location |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Qwen3.8-Flash-Next / IQ3_XXS | Strata | 593.2 | 3.753 | 97.09 | 32,768 | 75.84 | CT1000P3PSSD8 NVMe: models/strata/models/IQ3_XXS |
| GLM-5.3-Flash / Maya-S24 | Maya | 49.3 | 44.703 | 2.59 | 65,536 | 94.70 | CT1000P3PSSD8 NVMe: models/maya/Maya-S24 |
| DeepSeek-V4.1-Flash-1017 / Maya-S | Strata | 33.6 | 65.220 | 1.88 | 131,072 | 339.48 | CT1000P3PSSD8 NVMe: models/maya/DeepSeek-V4.1-Flash-1017-GGUF/Maya-S |
| DeepSeek-V4.1-Flash-1017 / Maya-S | Maya | 49.6 | 44.017 | 4.08 | 32,768 | 339.48 | CT1000P3PSSD8 NVMe: models/maya/DeepSeek-V4.1-Flash-1017-GGUF/Maya-S |


These table rows use current selected measurements; rejected screens remain in
the dated study and do not replace qualified results.

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
