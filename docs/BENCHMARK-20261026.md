# Local model speed benchmark - October 26, 2026

Measured on the native i5-13600KF / 64 GiB DDR5 / RTX 3080 Ti 12 GiB + RTX 3080 10 GiB workstation, with Ubuntu 26.04 and NVIDIA driver 595.99.02. Stock driver and power limits remained unchanged.

Twenty-four measured streamed API requests passed: three short and three longer prompts for each of four model/engine combinations. Every measured request generated exactly 128 tokens, had thinking disabled, and reported zero reused prompt tokens. Four 64-token warm-ups were excluded. Rates were independently recomputed from raw API timing counters and summaries cross-checked.

## Results

Values are medians of three requests. Generation ranges are observed minima and maxima, not confidence intervals. TTFT is client-observed time to first nonempty generated content; generation and prompt rates use engine timings.

| Model / engine | Input case | Actual input tokens | Generation tok/s (range) | Prompt tok/s | TTFT seconds | Total seconds |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Qwen3.8-Flash-Next IQ3_XXS / Strata | short | 168-171 | 108.4 (91.1-116.1) | 133.6 | 1.29 | 2.46 |
| Qwen3.8-Flash-Next IQ3_XXS / Strata | long | 2199-2209 | 106.1 (91.6-112.1) | 625.2 | 3.53 | 4.73 |
| GLM-5.3-Flash S24 / Maya | short | 160-163 | 7.1 (5.2-7.2) | 11.0 | 15.62 | 34.36 |
| GLM-5.3-Flash S24 / Maya | long | 2191-2201 | 7.8 (6.6-8.0) | 81.2 | 26.97 | 43.32 |
| DeepSeek Maya-S / Strata | short | 151-154 | 2.5 (2.3-2.6) | 3.0 | 51.68 | 104.94 |
| DeepSeek Maya-S / Strata | long | 2171-2190 | 2.6 (2.5-2.7) | 34.2 | 63.66 | 112.60 |
| DeepSeek Maya-S / Maya | short | 151-154 | 3.9 (3.4-4.7) | 5.0 | 30.67 | 63.17 |
| DeepSeek Maya-S / Maya | long | 2171-2190 | 4.0 (3.7-4.1) | 53.6 | 40.66 | 72.06 |

## DeepSeek comparison

On the same Maya-S GGUF files, Maya's median generation rate was 56% higher for short prompts and 54% higher for longer prompts. Longer-prompt processing was 57% faster; TTFT and total completion time were each about 36% lower.

## Method and versions

- One engine at a time; one fresh process and one warm-up per condition. Temperature 0, seed 261026, top-p 1, one request slot, and 8192 allocated context tokens. Tested inputs were about 150-171 or 2171-2209 tokens; full 8K input performance was not tested.
- Identical prompt text across engines for each repetition. Unique early tags prevented prefix reuse. The stimulus was synthetic reference-word notes followed by a request for a detailed community-garden guide. Three repetitions used different notes.
- Qwen and GLM retained their drafting settings; the measured draft counters confirmed drafting was active. Cross-model rates therefore describe these configurations, rather than an isolated architecture comparison.
- DeepSeek used the same shared Maya-S weights, all six routed experts, GPUs 0 and 1, drafting off, vision off, 2048 MiB reserve per GPU, 14 CPU threads, 4096-token prefill chunks, and mmap expert access. Both began from copies of the same expert-cache seed. Requested tensor parallelism 2 fell back to one GPU per layer group on both engines; both GPUs still held layers.
- Native expert-cache implementations differed: Strata used its RAM store; Maya used its mmap/page-cache and adaptive CPU/PCIe path. These native differences were retained. OS page cache was not flushed.
- Test order: Qwen/Strata, GLM/Maya, DeepSeek/Strata, DeepSeek/Maya. Desktop/Codex/browser applications were preserved. Hardware-level cache state and background activity were not tightly controlled; cache warming affected some run times.
- Qwen used packaged Strata engine 0.1.50; DeepSeek used packaged Strata engine 0.1.51 (CUDA 13 package). Maya 1.1.29 was built natively with CUDA 12.4 and GCC 13. Exact source revisions and redacted configurations are retained in the raw record.
- The highest sampled GPU temperatures across the benchmark were 67 C on the Ti and 49 C on the 3080. This was a bounded speed test, not a full thermal, quality, tool-use or long-context evaluation.

## Evidence

Private raw records are in `data/benchmarks/20261026-173730/`: `protocol.json`, `prompts.json`, `requests.jsonl`, individual raw API events, `summary.csv`, `summary.json`, `independent-summary.json`, `validation.json`, redacted configs, engine logs and resource telemetry. Credentials remain in private config files and are omitted from the redacted copies.

The previously running Qwen profile was restored after measurement. Installed serving profiles were not changed by the temporary benchmark configurations.
