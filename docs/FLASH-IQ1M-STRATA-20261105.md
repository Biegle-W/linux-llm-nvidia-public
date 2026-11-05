# Flash-Next IQ1_M selected in Strata — November 5, 2026

**Flash-Next Unsloth Dynamic3.1 IQ1_M /Strata replaces the IQ1_S /llama.cpp entry.** The new ID is `flash-next-iq1m-strata`, with both GPUs, automatic layer split, existing MTP drafter/spec4, INT8 KV and131,072-token allocation. The separate IQ3_XXS `flash-next-strata` entry and global default remain unchanged. Native logs confirmed a two-GPU20/28-layer split and the131,072 context setting. This is an allocation and short functional check, not full-window quality qualification.

The authenticated API, both DSH profiles and the existing Strata desktop selector expose the replacement. Local DSH selections of the retired ID migrate to the new ID; unrelated providers/routes are preserved. The old API ID returns404. CLI: `./scripts/start_model.sh flash-iq1m`.

## Short actual DSH observation

One uncached first tool generation per listed configuration, with parsed read-tool arguments, actual execution/result, exact proof follow-up and owned unload. Loading and follow-up are excluded from these timings. Zero prompt-cache reuse was reported; OS file caches were not dropped. The previous row is dated evidence, not a fresh paired baseline. Quantization, engine, context and token counts differ, so these numbers do not establish equal output quality or isolate the cause of the gain.

| Model / quant | Engine | Prefill tok/s | First token s | Decode tok/s | Context | Prompt/output tokens | Checkpoint GB / location |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Flash-Next UD-IQ1_M +MTP | Strata0.2.11/engine0.1.57 |1092.5|5.267|78.2|131,072|5592/38|68.007 /NVMe|
| Retired Flash-Next UD-IQ1_S | llama.cpp stable v0.9.0 |120.73|48.463|36.86|12,288|5824/39|66.379 /NVMe|

Observed generation is about2.12times faster, prefill9.05times faster and first-token latency9.20times shorter. MTP accepted28 of35 proposed tokens in the first call. This short burst does not establish sustained throughput. All tool/result/follow-up and resource checks passed on the first actual GPU trial; the owned worker unloaded and GPU resources were released.

## Effective guards

Configured limits, not observed usage. Both retain2GiB host available floor, unlimited swap occupancy,100C stops, fail-closed telemetry, three bad2-second resource samples, concurrency1, swappiness60 and idle600s. Swap rates are averaged over30seconds; active full PSI15% requires three bad samples after its window; there is no separate loading PSI threshold for these two profiles. Short calls may not fill the30-second window.

| Profile | Worker RAM high/max GiB | GPU policy | Swap write/combined MiB/s over30s |
| --- | ---: | --- | ---: |
| Selected IQ1_M /Strata |87.76985/89.76985|256MiB free/card floor;1024MiB native cache reserve/card|128/160|
| Historical IQ1_S /llama.cpp |87.76985/89.76985|256MiB free/card after ready;1536MiB fit targets|128/160|

Nine lifecycle samples at median5.07s captured peak charged worker RAM56.15GiB, zero worker swap, host available at least50.89GiB, minimum free VRAM730/857MiB and peak GPU temperatures43/37C. Memory high/max/OOM events were zero. These are sampled extrema, not guaranteed peaks; cgroup-charged file cache does not equal total model working set. Native logs reported31.36GiB resident expert RAM: this is the existing MoE host-expert caching design, not a fully VRAM-resident model.

## Downloads, preparation and replacement

All three checkpoint shards match the exact published size/SHA256 pins at Unsloth revision`d96201194f103c906994f283f504209dc8d2a10c`. The28.800GB n-gram shard is byte-identical to IQ1_S and is shared by a verified hardlink; only39.207GB of new checkpoint bytes were added. The native pack uses upstream `iq_pack.py --compat-bf16`: small compatibility tensors are converted to the engine form; expert and n-gram checkpoint bytes remain unchanged. The separate preset is bound to its own pack/tokenizer and complete canonical argument hash. The selected engine passed official signature and full-file verification.

The old IQ1_S checkpoint is retained for rollback, outside the active entries. Its37.568GB model shard plus10.947MB metadata are now inactive; the28.800GB table remains actively shared by IQ1_M. No complete checkpoint was deleted. Earlier IQ1_S deletion savings must account for this sharing.

The daily Strata group now qualifies IQ3_XXS, DeepSeek and IQ1_M together; it updates both Qwen presets and IQ1_M runtime hash pins transactionally. llama.cpp maintenance now qualifies Bolt only.506 CPU regressions passed, including wrong pack/tokenizer/device/argument rejection, bounded swap/native status checks, retired DSH selection migration, and future signed updater refresh of both presets without changing pack/argument pins.

An admission preflight stopped before any GPU loading because the persistent API/hub retained the older RAM validator after the earlier ceiling change. With all inference units inactive, no native endpoint or reservation, those two owned idle services were reloaded; health and model listing passed. This was not a failed GPU trial. DSH was reloaded after the passing replacement. Final workers are unloaded, no reservation or pending updater transaction/publication remains, and the03:00America/Toronto timer is unchanged.

[Sanitized verification and observations](validation-results/20261105-flash-iq1m-strata.json). [Upstream supported quantizations](https://github.com/Niko1221/Strata/releases/tag/v0.2.11).
