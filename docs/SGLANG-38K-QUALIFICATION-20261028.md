# SGLang 38K context qualification — October 28, 2026

**38,912-token qualification not promoted: normal reload KV capacity fell short. Current selected context: 32,768.** The user accepted proportional context/speed tradeoffs. This task completes the missing qualification gates rather than repeating the previous speed screens.

[Numeric checks, resource evidence and decision](benchmark-results/20261028-sglang-38k-qualification.json). Prior [screening report](SGLANG-CONTEXT-20261028.md) retains its original no-loss gate and measurements.

## VRAM-only models

| Model / quant | Engine / saved screen | Prefill (tok/s) | First token (s) | Decode (tok/s) | Context limit (tokens) | Storage size (GB) | Storage location |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Qwen3.8-27B / AutoRound INT4 + INT8 embedding | SGLang TP2 + MTP3 MLP W4A8 — 32K control | 1,667.87 | 1.3455 | 84.76 | 32,768 | 15.79 | Samsung SSD 870 QVO SATA: `models/engine-tests/qwen38-27b-hyperqwen-fast` |
| Qwen3.8-27B / AutoRound INT4 + INT8 embedding | SGLang TP2 + MTP3 MLP W4A8 — 38K candidate | 1,660.68 | 1.3484 | 83.32 | 38,912 | 15.79 | Samsung SSD 870 QVO SATA: `models/engine-tests/qwen38-27b-hyperqwen-fast` |

## MoE models with CPU RAM offload

None currently kept; none tested.

## MoE models with SSD streaming

Existing profiles unchanged; none tested. Reduced-RAM qualification caveats remain.

## Qualification and resource result

The initial harness rejected a correct tool-roundtrip result inside a Markdown JSON fence. The parser was aligned with the existing JSON/arithmetic convention and the saved answer verified as doubled=84. Passed retrieval/history/JSON/arithmetic checks were carried forward; a fresh guarded worker re-exercised tool grammar memory and ran only the unfinished long-input sustained check. Original failed harness completion, raw responses and engine/events remain private. The first terminal log was overwritten by the resume wrapper; its independent event/response evidence is preserved.

The saved 38K screen adds 18.75% capacity for 1.70% slower fixed-input generation. These are carried historical medians; no speed retries or new matched confirmation were run.

The forced report_number(value=42) call passed. All four target/draft KV pools back 38,912 tokens. The long-input stream ran at 22.61 observed client decode tok/s; this uses about 35K actual input and is a different workload from the 2.2K-input speed screen.
- json: passed=True, prompt/completion tokens 39/21, wall 0.20 s.
- arithmetic: passed=True, prompt/completion tokens 49/23, wall 0.24 s.
- retrieval: passed=True, prompt/completion tokens 34964/57, wall 29.18 s.
- long-history: passed=True, prompt/completion tokens 35063/57, wall 29.29 s.
- tool-roundtrip: passed=True, prompt/completion tokens 106/19, wall 0.37 s.
- long-input-continuous-generation: passed=True, prompt/completion tokens 34973/3072, wall 163.28 s.

Minimum sampled GPU free memory: 560/795 MiB (Ti/3080). Maximum temperatures: 65/51°C. Host available memory stayed at least 31.42 GiB; peak worker RAM 7.30 GiB and swap 0.00 GiB.
Isolated guard stop: none recorded. Isolated request error: none recorded.

All workers and coordinators used visible terminals. The dense reserve stayed 512 MiB, swappiness 60, RAM 30/36 GiB, host floor 8 GiB and temperature 82°C; existing active swap-churn protection stayed enabled. No CPU weight offload, runtime source, precision or shard changes were made.

Only owned trial workers were cleaned up. Normal deployment verification and final ownership state are recorded below when applicable. Raw plans, prompts, responses, terminal logs and telemetry stay private under `data/sglang-38k-qualification-20261028/`.

## Normal router verification

Isolated quality and sustained-resource checks passed, and the normal router passed 34,964-input retrieval and automatic request reload. However, that reload profiled and allocated only 37,501 tokens in each of four KV pools while advertising 38,912. Full-capacity qualification therefore failed and the rollout restored 32,768 in the maintained profile and DSH web/headless catalogs. Saved DSH defaults remain. Final router is idle, DSH active, no GPU reservation. The earlier unit-fixture failure was corrected without changing the launcher/guards; 39 CPU regressions passed. No GPU speed retries followed the capacity failure.

## Capacity attribution and next step

The normal reload log explicitly clamps max_total_tokens 38,912 to the profiled 37,501 before allocation. GPU0 pre-weight available memory was 10.43 GiB on that reload versus 10.53 GiB on the sustained trial; GPU1 was 9.27 GiB in both. The fork profiles available memory and min-reduces capacities across ranks. Startup memory variability is a plausible contributor; this is an inference, not a controlled cause isolation. There was no OOM or guard stop in the successful isolated run, and no inference speed result failed this accepted proportional policy. A future candidate needs reliable full-KV backing on normal reload while retaining 512 MiB and all other guards. Keep 32K; do not rerun completed speed screens for luck.
