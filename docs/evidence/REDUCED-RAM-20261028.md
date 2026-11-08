# Four SSD-streaming profiles with reduced RAM — October 28, 2026

2 of the four tested SSD-streaming profiles passed reduced-RAM qualification and
normal guarded router loading with one 16 GiB DIMM removed (45.55 GiB usable).
Their model IDs, quantization, engines and context allocations are unchanged.
Only qualified temporary cache settings were applied; all existing resource/ownership guards,
worker budgets, swappiness 60, concurrency 1 and the 600-second idle policy remain.
No fallback model was restored. The router finished idle and DSH was preserved.

This is bounded qualification under the recorded desktop load, not a guarantee
of multi-hour operation or arbitrary additional host-memory demand. Historical
full-RAM comparisons use saved matched fixtures and method; the RAM stick was not
reinserted for a fresh paired control. Small differences can include run variation.

Hardware: i5-13600KF, RTX 3080 Ti 12 GB plus RTX 3080 10 GB, native Linux,
one 16 GiB DIMM removed. Driver/source fingerprints are in the numeric evidence.

## Current kept results

Only the GLM/Maya and DeepSeek/Strata rows are new reduced-RAM measurements.
Flash/Strata and DeepSeek/Maya retain historical full-RAM measurements. Dense rows
carry their latest qualified measurements (HyperQwen October 27, SGLang October 28)
and were not retested in this study. Rates use three measured requests, 128 output tokens each, about 2.2K
input tokens, temperature 0, top_p 1 and the saved benchmark fixtures. One 64-token
warm-up is excluded. Model loading is excluded; OS file cache is not flushed.
Prefill is native engine prompt timing; decode is client-observed SSE
(completion_tokens−1)/(last-content−first-content), consistently across rows.

### VRAM-only models

| Model / quant | Engine | Prefill (tok/s) | Time to first token (s) | Decode (tok/s) | Context limit (tokens) | Storage size (GB) | Storage location |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Qwen3.8-27B / AutoRound INT4 / INT8 embedding | HyperQwen-vLLM | 1,491.7 | 1.499 | 89.10 | 56,320 | 15.79 | Samsung SSD 870 QVO SATA: `models/engine-tests/qwen38-27b-hyperqwen-fast` |
| Qwen3.8-27B / AutoRound INT4 / INT8 embedding | SGLang / htsglang TP2 + MTP3, MLP W4A8 | 1,667.9 | 1.346 | 84.76 | 32,768 | 15.79 | Samsung SSD 870 QVO SATA: `models/engine-tests/qwen38-27b-hyperqwen-fast` |

### MoE models with CPU RAM offload

None currently kept. Expert RAM tiers below are caches within SSD-streamed profiles.

### MoE models with SSD streaming

| Model / quant | Engine | Prefill (tok/s) | Time to first token (s) | Decode (tok/s) | Context limit (tokens) | Storage size (GB) | Storage location |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Qwen3.8-Flash-Next / IQ3_XXS | Strata | 593.2 | 3.753 | 97.09 | 32,768 | 75.84 | CT1000P3PSSD8 NVMe: `models/strata/models/IQ3_XXS` |
| GLM-5.3-Flash / Maya-S24 | Maya | 46.8 | 47.061 | 2.11 | 65,536 | 94.70 | CT1000P3PSSD8 NVMe: `models/maya/Maya-S24` |
| DeepSeek-V4.1-Flash-1017 / Maya-S | Strata | 32.2 | 68.049 | 1.80 | 131,072 | 339.48 | CT1000P3PSSD8 NVMe: `models/maya/DeepSeek-V4.1-Flash-1017-GGUF/Maya-S` |
| DeepSeek-V4.1-Flash-1017 / Maya-S | Maya | 49.6 | 44.017 | 4.08 | 32,768 | 339.48 | CT1000P3PSSD8 NVMe: `models/maya/DeepSeek-V4.1-Flash-1017-GGUF/Maya-S` |

Sizes count base GGUF/safetensors checkpoints in decimal GB, excluding auxiliary
packs, draft assets and caches. HyperQwen/SGLang share one SATA checkpoint;
Strata/Maya DeepSeek share one NVMe checkpoint. Each shared group counts once
physically. Storage placement is unchanged.

## Cache choices and historical performance change

| Profile | Qualified cache choice | Decode change | Prefill change | TTFT change |
| --- | --- | ---: | ---: | ---: |
| `glm-maya` | `MAYA_GLM_RAM_GB=24` | -56.1% | -28.5% | +39.5% |
| `deepseek-strata` | `DS4_STORE_GB=24` | -39.2% | -3.3% | +3.4% |

Maya's original adaptive cache / 8 GB warming was also tested, rather than assumed
unusable. The comparison and selection rule are recorded in the numeric evidence.
The original-cache result and any further source-supported cache reductions are
recorded separately. No failed cache setting is promoted.

Unresolved on reduced RAM: `deepseek-maya`, `flash-next-strata`. Their table rows retain historical full-RAM measurements, not newly qualified reduced-RAM results. Original cache settings remain unchanged and may stop at the existing guards. No reliable reduced-RAM performance-loss percentage can be assigned from failed screens.

Negative throughput change means slower; positive TTFT change means a longer wait.
These are fixed-fixture historical comparisons, not near-window throughput ratios.
GLM's RAM-tier setting and Flash's resident budget use GiB; DS4 store/warm limits
use decimal GB. These are qualified, bounded choices, not an exhaustive cache optimum.

## Quality, memory and sustained operation

| Profile | Tested retrieval input | Continuous generation (s) | Minimum sampled host available (GiB) | Peak worker cgroup (GiB) | Peak worker swap (GiB) | Max GPU temp (C) | Fresh process + normal router |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `glm-maya` | 58,986 | 231.1 | 9.65 | 38.58 | 0.000 | 62 | Passed |
| `deepseek-strata` | 117,866 | 381.1 | 13.53 | 39.03 | 0.000 | 63 | Passed |

Every selected candidate passed JSON, arithmetic and three-marker near-window
retrieval; images passed wherever the maintained profile enables them. Strata
DeepSeek remains text-only. Retrieval targets approximately 90% of the configured
window; this is not a claim that the exact maximum input was retested. Sustained
requests exercised the unchanged owned-worker 30-second swap/pressure windows.
Cgroup memory includes reclaimable file cache and is not equivalent to anonymous
resident RAM. Sampled minima/peaks do not establish every instantaneous extreme.
Fresh-process tests do not imply a cold OS disk cache.

The production swap policy remains unlimited occupancy with its existing active
churn/pressure/telemetry stops. Host available 8 GiB and temperature 82 C thresholds,
hysteresis, GPU reserves, exact owned units/invocations, reservations and all other
guards were preserved. Seventeen existing CPU budget/swap-guard regressions passed. No guard was
weakened to obtain a passing result. Dense reserve remains 512 MiB; SSD profiles retain their own native GPU reserve settings.

## Rejected attempts and limitations

Flash's original full expert arena hit the existing host-memory guard during
loading. Two initial resident probes were rejected before engine loading because
Flash's mmap switch takes no value; corrected resident-budget variants supersede
them. All failed evidence is retained. Corrected Flash and all Maya candidates hit the
unchanged active owned-worker swap-churn guard. The 4 GiB and 1 GiB Flash candidates
passed 29,450-input retrieval before stopping during sustained generation. Disabling
Flash conversation parking and speculative prefetch also failed. These partial
passes do not establish a reliable reduced-RAM operating point.

- `deepseek-maya-original-warm8`: guard stop.

- `deepseek-maya-warm0-read128-ahead0`: guard stop.

- `deepseek-maya-warmcap16-warm0`: guard stop.

- `deepseek-maya-warmcap20-warm0`: guard stop.

- `deepseek-maya-warmcap24-warm4`: guard stop.

- `flash-next-strata-resident1-v3`: guard stop.

- `flash-next-strata-resident14-v2`: guard stop.

- `flash-next-strata-resident18-v2`: guard stop.

- `flash-next-strata-resident22-v2`: guard stop.

- `flash-next-strata-resident4-conv0-prefetch0`: guard stop.

- `flash-next-strata-resident4-v3`: guard stop.

- `flash-next-strata-resident8-v3`: guard stop.

Selected cache values are pinned in the maintained registry and canonical launch
configs. Normal API selection verified effective cache values, unchanged contexts,
worker memory limits, infinite swap occupancy allowance and correct JSON responses.
Only owned test/worker instances were stopped; router and DSH ownership remained.
Reduced-RAM cache choices are temporary. Restore appropriate full-RAM cache
settings only after explicit human confirmation that the DIMM is restored and
Linux capacity verification, then verify normal guarded loading and update
selected-setting metadata. MemAvailable changes and timers never trigger this.
Preserve unrelated router/desktop improvements, credentials, guards and benchmark
attribution. Original full-RAM settings are archived privately with provenance/hashes. Runtime
API keys were redacted before Git archival; exact local rollback copies remain
owner-only. Restoring full-RAM settings later requires the matching hardware/state
review, rather than automatic fallback restoration.

[Machine-readable results](benchmark-results/20261028-reduced-ram.json).
Raw requests, native logs, source snapshots and live ownership remain private.
