# SGLang context study — October 28, 2026

Later follow-up: under the accepted proportional policy, [38K passed isolated quality/resource checks but failed full KV coverage on normal reload](SGLANG-38K-QUALIFICATION-20261028.md). The 32K deployment remains. Original screening measurements and gate below are preserved.

**Keep the deployed 32,768-token profile.** No screened larger setting passed the user’s no-generation-loss condition. The source/runtime, TP2/MTP3 W4A8, BF16 state/KV and production settings are unchanged. Dense reserve 512 MiB, swappiness 60 and all other guards remained enabled. All tests used visible terminals.

[Numeric trials, exact settings, samples, resources and failures](benchmark-results/20261028-sglang-context.json). [Deployed runtime](SGLANG-DEPLOYMENT-20261028.md).

## VRAM-only models

| Model / quant | Engine / trial | Prefill (tok/s) | First token (s) | Decode (tok/s) | Context limit (tokens) | Storage size (GB) | Storage location |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Qwen3.8-27B / AutoRound INT4 + INT8 embedding | SGLang TP2 + MTP3 MLP W4A8 — 32,768, fresh qualified control | 1,667.87 | 1.3455 | 84.76 | 32,768 | 15.79 | Samsung SSD 870 QVO SATA: `models/engine-tests/qwen38-27b-hyperqwen-fast` |
| Qwen3.8-27B / AutoRound INT4 + INT8 embedding | SGLang TP2 + MTP3 MLP W4A8 — 38,912, screen only; speed gate failed | 1,660.68 | 1.3484 | 83.32 | 38,912 | 15.79 | Samsung SSD 870 QVO SATA: `models/engine-tests/qwen38-27b-hyperqwen-fast` |
| Qwen3.8-27B / AutoRound INT4 + INT8 embedding | SGLang TP2 + MTP3 MLP W4A8 — 36,864, screen only; speed gate failed | 1,661.09 | 1.3507 | 83.50 | 36,864 | 15.79 | Samsung SSD 870 QVO SATA: `models/engine-tests/qwen38-27b-hyperqwen-fast` |

## MoE models with CPU RAM offload

None currently kept; none tested.

## MoE models with SSD streaming

Existing profiles are unchanged; none tested. Reduced-RAM MoE qualification remains unresolved.

## Decisions

The fresh 32K control reached 84.76 decode tok/s and passed a parsed tool call, JSON, arithmetic and 29,434-input retrieval. This replaces the older 82.79 tok/s value as the latest measured control for the same deployed configuration; that original qualification and deployment evidence is preserved.

- 40,960: rejected before timing. Error: Allocated KV pool does not cover the configured context. Actual KV pools: [40760, 40760, 40760, 40760]. The worker advertised 40,960 but backed only 40,760 tokens; it was not treated as a qualified 40K allocation. No OOM or throughput result is claimed.
- 38,912: 83.32 decode tok/s, -1.70% versus the fresh control. Initial speed gate failed; tool/long-window qualification was not run. This is not a deployable candidate.
- 36,864: 83.50 decode tok/s, -1.49% versus the fresh control. Initial speed gate failed; tool/long-window qualification was not run. This is not a deployable candidate.

The predeclared sequence tried 40K, 38K and 36K, stopping at the first initial candidate that passed speed and quality. No candidate passed, so the planned late 32K/candidate confirmation was not run. The generation criterion was a three-request median at least equal to the fresh control, with no retrospective tolerance. Prefill and TTFT were reported separately. Small 1.5–1.7% changes may include run-to-run/client-stream variation; these results do not prove that larger contexts must always be slower. They do not establish the no-loss condition required for promotion.

## Method, capacity and limits

Only context_length/max_total_tokens changed. The pinned source/interpreter, decoder MLP W4A8, MTP3, BF16 state/KV, one Mamba slot, chunk 384, rank budgets 11,008/8,960 MiB, base ratio 9:8 and MLP ratio 10:7 remained the same. Existing caches were reused. All four target/draft KV pools had to back the advertised context, independently of the API model limit. The 40K failure reflects the configured allocation/admission budget; other budgets were not tested.

Each measured setting reused the same saved approximately 2.2K-input/128-output code/prose requests and 64-output warmup, temperature 0, thinking disabled, no prefix cache. Native prefill deltas select one TP replica; decode uses client SSE first-to-last content intervals. Loading is excluded. This comparison concerns the maximum allocation with identical actual prompts, not a guarantee that generating against longer actual inputs is free.

The forced tool check precedes the quality suite to exercise normal grammar/tool memory overhead. It ran for the control; rejected speed candidates were stopped without extra qualification work. Their successful short screens do not validate full-window retrieval or resource safety for all workloads. Source hash/version and GPU-placement audits used the deployed normal launcher implementation with an isolated catalog override and private audit output. No production file was changed to run the study.

All guards stayed at their selected values. No CPU weight offload, precision reduction, driver/unlock change, clock change, swap-file change or global VM change was used. The owned workers stopped and GPU-LOCK was released; cleanup finished idle without automatically restoring HyperQwen or SGLang. The router continues offering the unchanged 32K SGLang profile on request.

Raw plans, per-request/native metrics, terminal logs, audits, retrieval fixtures and guard telemetry are private under `data/sglang-context-20261028/`. Earlier numeric reports are unchanged.
