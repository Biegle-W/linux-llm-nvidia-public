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

| Model / weight quant | Engine | Selected setting | Allocated context | Retrieval-tested input |
| --- | --- | --- | ---: | ---: |
| Qwen3.8-27B / AutoRound INT4 body and heads, INT8 embedding | HyperQwen/vLLM | TP2, MTP3, MLP W4A8, BF16 state, INT4 KV, 128-token chunks, graphs | 32,768 | 29,496 |
| Same prepared Qwen3.8-27B quant | SGLang | PP2, packed embedding lookup, FP32 state, BF16 KV, 512-token chunks, decode graphs | 16,384 | 14,758 |
| Qwen3.8-Flash-Next / IQ3_XXS | Strata | Existing `qwen-flash-next` preset, MTP, INT8 KV, automatic expert cache | 32,768 | Not established |
| GLM-5.3-Flash / Maya-S24 | Maya | S24, drafting, automatic GPU cache/prefill, 40 GiB expert RAM, on-demand CPU vision | 32,768 | 10,908 |
| DeepSeek-V4.1-Flash-1017 / Maya-S | Strata | Shared weights, `deepseek-maya-s`, drafting/vision off, prefill 4096, 42 GB LFU cache, 2 GiB GPU reserve | 65,536 | 58,969 |
| Same DeepSeek Maya-S weights | Maya | Shared weights, `maya-ds4.json`, drafting off, 4096-token chunks, 8 GB expert warming, 2 GiB GPU reserve | 32,768 | 9,674 |

[Strata DeepSeek now has a 64K allocation](DEEPSEEK-STRATA-CONTEXT-20261027.md),
with three-marker retrieval passed at 58,969 input tokens under the earlier
setting. The optimized cache also passed 9,673-input retrieval; its current speed
measurements and the earlier full-window evidence remain separately dated.

The other streamed-model 32K allocations passed installation/startup and short API
checks. GLM and Maya DeepSeek now pass recorded multi-chunk retrieval near 10K
input. Their full windows have not been retrieval-validated. Earlier speed
tests used an **8K benchmark allocation** and remain historical.
The latest table measures the current allocations with roughly 2.2K input tokens;
it does not qualify full-window quality. No model tests or context qualification
were repeated for the profile consolidation. The subsequent Strata DeepSeek context expansion used
new 32K/64K configurations and preserved the completed 8K measurements.

The router keeps Qwen tool-call parsers. The latest MoE optimization uses the
selected bounded cache budgets, including 40 GiB GLM expert RAM and on-demand
CPU vision; the previous 32 GiB cap remains dated evidence.

## Latest matched speed evidence

[GLM/DeepSeek optimization](MOE-OPTIMIZATION-20261027.md) retested those three
profiles at unchanged context limits with the same approximately 2.2K-token,
128-output-token fixture and three measured requests. Dense/Flash rows retain
their unchanged [October 27 measurements](BENCHMARK-20261027-101219.md).
Sizes count base checkpoint weights; locations are current; shared rows use one
physical checkpoint. See [reporting conventions](BENCHMARK-REPORTING.md).

### VRAM-only models

| Model / quant | Engine | Prefill (tok/s) | Time to first token (s) | Decode (tok/s) | Context limit (tokens) | Storage size (GB) | Storage location |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Qwen3.8-27B / AutoRound INT4 / INT8 embedding | HyperQwen-vLLM | 1,385.5 | 1.613 | 89.01 | 32,768 | 15.79 | Samsung SSD 870 QVO SATA: `models/engine-tests/qwen38-27b-hyperqwen-fast` |
| Qwen3.8-27B / AutoRound INT4 / INT8 embedding | SGLang | 2,606.3 | 0.852 | 46.71 | 16,384 | 15.79 | Samsung SSD 870 QVO SATA: `models/engine-tests/qwen38-27b-hyperqwen-fast` |

### MoE models with CPU RAM offload

None currently kept. RAM tiers in streamed profiles are caches, not full-model RAM residency.

### MoE models with SSD streaming

| Model / quant | Engine | Prefill (tok/s) | Time to first token (s) | Decode (tok/s) | Context limit (tokens) | Storage size (GB) | Storage location |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Qwen3.8-Flash-Next / IQ3_XXS | Strata | 609.6 | 3.648 | 105.64 | 32,768 | 75.84 | CT1000P3PSSD8 NVMe: `models/strata/models/IQ3_XXS` |
| GLM-5.3-Flash / Maya-S24 | Maya | 64.5 | 36.247 | 4.73 | 32,768 | 94.70 | 10,908 |
| DeepSeek-V4.1-Flash-1017 / Maya-S | Strata | 32.4 | 67.527 | 2.87 | 65,536 | 339.48 | CT1000P3PSSD8 NVMe: `models/maya/DeepSeek-V4.1-Flash-1017-GGUF/Maya-S` |
| DeepSeek-V4.1-Flash-1017 / Maya-S | Maya | 49.6 | 44.017 | 4.08 | 32,768 | 339.48 | CT1000P3PSSD8 NVMe: `models/maya/DeepSeek-V4.1-Flash-1017-GGUF/Maya-S` |

The registry retains older `benchmark` fields as historical measurements and
records this run under `latest_benchmark`. Earlier code/prose and short-input
fixtures have different workloads. Historical reports remain available:
[dense optimization](DENSE-ENGINE-OPTIMIZATION-20261027.md),
[stock/unlock comparison](BENCHMARK-UNLOCK-20261026.md), and
[64K DeepSeek retrieval](DEEPSEEK-STRATA-CONTEXT-20261027.md).

The 4K HyperQwen MTP trial had faster code decode (173.9 tok/s), while the
selected 32K trial measured 155.2 tok/s and faster prose (107.7 versus 102.5).
The retained choice preserves the larger validated window. SGLang's 8K and 16K
graph trials had essentially identical decode; the retained 16K setting doubles
the allocation, with observed longer-input TTFT of 0.865 versus 0.791 seconds.
These explicit tradeoffs are why the shorter trials are historical evidence,
not additional maintained presets.

## Launching

```bash
python3 scripts/profile_catalog.py
./scripts/start_model.sh qwen27b             # default: HyperQwen, 32K
./scripts/start_model.sh qwen27b sglang      # SGLang, 16K
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
