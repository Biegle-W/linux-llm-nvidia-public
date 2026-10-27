# Qwen3.8-27B: mixed-Ampere vLLM and SGLang optimization

**Profile consolidation:** the current [maintained registry](MAINTAINED-PROFILES.md) keeps one setting per model, weight quant and engine. The intermediate rows below remain dated measurement evidence; their superseded launchers have been retired.

The default dense Qwen launcher now uses **HyperQwen/patched vLLM, TP2, MTP3,
32K context**, entirely in GPU memory. It measured **155.2 code / 107.7 prose
tokens/s**, compared with the previous llama.cpp profile's **88.0 / 58.6**.
A qualified SGLang choice now runs **GPU-only PP2, CUDA graphs and 16K context**
at **47.2 / 47.2 tokens/s**. There is one selected configuration per engine;
intermediate trials are benchmark evidence, not additional deployed presets.

The old 4070 12 GB + 3060 12 GB setup supplied the compact vocabulary weights,
MTP settings, MLP-only W4A8 strategy and DFlash2 comparison. Its balanced VRAM
budget cannot be copied unchanged onto the current 3080 Ti 12 GB + 3080 10 GB.

## Selected profiles

```bash
./scripts/start_model.sh qwen27b             # HyperQwen/vLLM, 32K, default
systemctl --user stop llm-test-qwen27b
./scripts/start_model.sh qwen27b sglang      # SGLang, 16K
```

Both choices use authenticated `http://127.0.0.1:10000/v1`, model ID
`qwen3.8-27b`, and the same bounded service. Stop that owned service before
changing engines. The slower IQ4_XS llama.cpp deployment and its dedicated weights
were removed at the user's request. Its dated measurements are preserved in
[the October 26 report](QWEN27B-GPU-ONLY-20261026.md). The default `qwen`
Flash-Next/MoE launcher is unchanged.

| Setting | Default HyperQwen/vLLM | SGLang choice |
| --- | --- | --- |
| Parallelism | TP2, PP1 | TP1, PP2, 32/32 decoder layers |
| Body / vocabulary | INT4 group-128 body and heads; INT8 input embedding | Same checkpoint, with local packed embedding lookup adapter |
| Activations | MLP-only INT8 Marlin; other layers retain their configured precision | W4A16 |
| Drafting | MTP3, probabilistic draft sampling, published 40,960-token draft head | None; this pinned build prohibits PP with speculation |
| KV / recurrent state | INT4 per-token-head / BF16 | BF16 / FP32 |
| Context allocation | 32,768 | 16,384 |
| Retrieval input actually tested | 29,496 tokens | 14,758 tokens |
| Prompt chunk | 128 | 512 |
| Cache allocation | Explicit 576 MiB per rank; reported token capacity 40,711 | Static fraction 0.88; reported token capacity 21,677; two Mamba slots |
| Graphs | Maximum capture size 4; compiled MTP | Decode batch size 1 |
| Active requests | 1 | 1 |
| CPU weight offload | 0 | 0 |
| Prefix reuse during measurement | Disabled | Radix/prefix caching disabled |

Thinking defaults to disabled and may be overridden per request. Both engines
retain the existing 30 GiB host-memory soft limit, 36 GiB hard limit, 1 GiB swap
limit and owned-service boundary. The launcher rejects execution outside that
bounded service, checks checkpoint metadata hashes and shard sizes, requires a
private nonempty key file, checks the expected GPU names and free memory, and
refuses an occupied port. The new balanced profiles require at least 10,240 MiB
free on the larger card and 9,728 MiB on the smaller card before CUDA startup;
these budgets correspond to the new per-card placements, rather than the GGUF
profile's heavier first-card split. No memory-balance, cache-capacity or numerical
guard was disabled. No unrelated application was stopped.

## Measured configurations

All new rows use the current 3080 Ti + 3080 machine, one active request, and
medians of three runs. Rates are client-observed streamed decode tokens/s.

| Configuration | Allocation | Short | Longer input | Code | Prose |
| --- | ---: | ---: | ---: | ---: | ---: |
| HyperQwen TP2, eager, FP32 state / BF16 KV | 4K | 24.3 | 24.3 | 24.4 | 24.1 |
| HyperQwen TP2, MTP3, FP32 state / BF16 KV | 4K | 113.8 | 108.2 | 173.9 | 102.5 |
| HyperQwen TP2, MTP3, BF16 state / INT8 KV | 12K | 114.1 | 111.5 | 168.1 | 105.6 |
| HyperQwen TP2, MTP3, BF16 state / INT8 KV | 16K | 118.2 | 112.9 | 149.5 | 101.4 |
| **Selected HyperQwen TP2, MTP3, BF16 state / INT4 KV** | **32K** | **112.1** | **97.8** | **155.2** | **107.7** |
| SGLang compact embedding, PP2, eager | 4K | 33.8 | 33.2 | 32.1 | 32.1 |
| SGLang compact embedding, PP2, graphs | 8K | 47.7 | 47.0 | 47.3 | 47.2 |
| **Selected SGLang compact embedding, PP2, graphs** | **16K** | **47.4** | **46.7** | **47.2** | **47.2** |
| Previous llama.cpp IQ4_XS, MTP2 | 32K | 68.6 | 66.4 | 88.0 | 58.6 |

The new default is about **1.76x faster for code and 1.84x for prose** than the
previous deployed GGUF configuration. These are complete-configuration results:
quantization, recurrent precision, speculation and engine differ.

| Selected profile | Short first-token latency | Longer-input first-token latency |
| --- | ---: | ---: |
| HyperQwen 32K | 0.156 s | 1.643 s |
| SGLang 16K | 0.102 s | 0.865 s |
| Previous llama.cpp 32K | 0.490 s | 1.902 s |

The short fixtures contain 168–171 input tokens and the longer fixtures
2,199–2,209, with 128 output tokens, temperature zero and thinking disabled.
Code and prose use the two archived prompts, 256 output tokens, temperature 0.6,
top-p 0.95 and seed 42. One warmup is excluded. Decode is calculated as
`(output_tokens - 1) / (last_content_time - first_content_time)`; speculative
bursts affect that metric. First-token latency includes the frontend and first
output step and is not an isolated prefill rate. Cold compilation is not a
steady-state latency measurement. SGLang's first sampled code request required
an additional approximately 40-second kernel compilation in the initial eager
trial; that is preserved in raw evidence, not reported as warmed prefill speed.
Three repeats are not confidence intervals or broad accuracy evaluation.

## Comparison with the old 4070 + 3060

| Configuration | Code | Prose |
| --- | ---: | ---: |
| Old 4070 + 3060, HyperQwen MTP3 | 108.3 | 66.8 |
| Old 4070 + 3060, HyperQwen DFlash2, seven draft tokens | 170.1 | 67.3 |
| Current 3080 Ti + 3080, selected HyperQwen MTP3 | 155.2 | 107.7 |

The selected current MTP profile is approximately 43% faster for code and 61%
faster for prose than the old MTP profile. It is approximately 9% slower for code
and 60% faster for prose than the old DFlash profile. The old allocation was 64K,
with different body weights, cache reservations, recurrent precision and runtime
revision. These are saved system configurations, not an isolated GPU ranking.
The matching archived prompts and 256-output method are retained. The historical
source is the private retirement repository; previously published context is in
[the benchmark history](https://github.com/Biegle-W/linux-llm-amd/blob/main/hardware/BENCHMARK-HISTORY.md).

## Why these changes work

HyperQwen's compact INT4 output/MTP heads and INT8 embedding make the target fit.
TP2 plus compiled MTP removes the previous non-drafting PP2 limitation. The old
profile's MLP-only W4A8 controls were reused, with explicit speculative-attention
settings and probabilistic draft sampling. They were tested together; this run
does not isolate the independent benefit of W4A8, graphs or MTP.

The previous TP trial combined FP16 recurrent state and INT4 KV and failed one
arithmetic check. This run preserves that failure and tests BF16 recurrent state
with INT4 KV separately. The final 32K configuration passes all the qualification
checks. It does not establish that every earlier precision combination is safe.

The pinned SGLang model constructed an unquantized embedding even though the
checkpoint stores packed INT8 rows. The local adapter passes its quantization
config and prefix into the embedding, installs the group-128 INT8 lookup method,
and dequantizes only requested rows on GPU. It never expands the whole table
into a resident dense copy. Its kernel is adapted from the installed vLLM
Apache-2.0 implementation and tested bit-exactly against a direct reference in
FP16 and BF16 on both GPUs. The adapter explicitly rejects other quantization
schemes. CUDA graphs improve this working PP route by roughly 47% over eager
execution on the code/prose fixtures.

## Guarded failures and fork coverage

- **SGLang TP2** still rejects unequal available memory: the smaller rank had
  9.273 GiB versus 10.363 GiB on the larger rank, just below the 90% criterion.
  That check remains enabled. GPU-only PP2 is the qualified route.
- **SGLang PP with MTP/DFlash** is prohibited by the pinned server's explicit
  compatibility assertion. No speculative speed is claimed for that route.
- **MTP with the original 384 MiB reservation** failed the capacity check:
  0.47 GiB required versus 0.35 GiB usable. Increasing the pool produced a valid
  higher-precision 4K comparison. The selected quantized-cache profile has its
  own successful 32K capacity and retrieval checks.
- **DFlash2, seven drafts** was attempted with the old meta-sharing optimization,
  after verifying that the drafter owns no embedding or output-head tensors.
  Loading completed, but the cache check required approximately 0.82 GiB versus
  0.36 GiB usable in the reserved pool. Headroom before that cache allocation was
  only about 1 GiB on the smaller card. It was rejected without a throughput claim
  or a larger unsafe reservation. MTP is the selected deployment.
- Loader allocation retries occurred while repacking on the 10 GB card. The
  successful MTP configurations subsequently completed load, capacity checks,
  graph capture, generation and retrieval. Those retries are not hidden as
  clean first-allocation success, nor are recovered retries counted as failed
  inference runs.

[HyperQwen](https://github.com/syv-ai/HyperQwen) supplies the tested patched vLLM
runtime. The vLLM rows here are not a second, independently benchmarked unpatched
installation. [The dual-3080 SGLang patch](https://github.com/kk-pcl/sglang-qwen38-dual-3080-patch)
was rechecked as a reference; its DFlash/KV changes do not remove this machine's
TP guard failure. [club-3090's W4A8 patch](https://github.com/noonghunna/club-3090/blob/master/models/qwen3.8-27b/sglang/patches/sglang-autoround-w4a8-v0.5.19/README.md)
targets a different pinned version and was not transplanted blindly. The installed
[qwen-serve recipe](https://github.com/sybil-solutions/qwen-serve/tree/main/qwen3.8/3090-sglang)
was reviewed as a larger-VRAM reference, not presented as another measured engine.
These distinctions matter when comparing fork coverage.

## Validation, source pins and artifacts

The final HyperQwen and SGLang choices each passed five arithmetic checks, strict
JSON-schema generation, twelve additional arithmetic/string/ordering regressions,
conversation recall, authenticated streaming and rejection of unauthenticated
completion requests. GPU audits found no non-CUDA target parameters; HyperQwen's
MTP parameters were also audited, including shared vocabulary modules. Shared
parameters must not be counted twice as independent VRAM allocations. The default
32K retrieval check recovered exact start/middle/end markers from 29,496 input
tokens in 28.96 seconds; SGLang recovered them from 14,758 tokens in 7.20 seconds.
Those are capacity/retrieval checks, not repeated long-context speed benchmarks.

The selected HyperQwen run retained approximately 1.2 GiB free on the smaller
GPU during generation. SGLang retained roughly 1 GiB after its long-input and
sampling workspaces were exercised; idle readings were higher. The rejected
16K HyperQwen INT8-KV trial retained only about 0.66 GiB and is not a deployed
preset. No driver, firmware, power-limit or reboot changes were made. The current
boot's two compute unlocks were confirmed. Both profiles disable custom all-reduce
and NCCL P2P; the second GPU operates at PCIe 4.0 x4. The desktop is on the larger
GPU in this boot. Sustained thermal stress, concurrent users, tools, vision and
broad reasoning quality are not established by these bounded checks.

- HyperQwen source: `ce9615c4f2309be727407918a6c979bd67968069`, patched vLLM 0.31.0.
- SGLang source: `4cb5aebfe08fa0abbd5fbcf84b29ad3d541bd5d3`; locally generated package label 0.5.22.
- Body: `dbirks/Qwen3.8-27B-W4A16-AutoRound`, revision `1f05c441c4e64ae0549de44fa9ea5a6d43610314`.
- Fast heads: `syvai/qwen3.8-27b-3090-fast-variant`, revision `124c14e7e8c7d2f5402933b9af368e772a9fcf0c`.
- Attempted DFlash2: `syvai/Qwen3.8-27B-DFlash2-W4A16`, revision `4d30ec736ffc6b8688dc2ae2b502d9b48bdec279`; 1,280,633,960-byte weight file, publisher-verified SHA256 `ec26996e6a0745ab5edb857117220ce1e219ad524f71e6e149b703804947d8e7`.

The selected launcher is `scripts/serve_qwen27b_engines.py`. It requires the
existing prepared checkpoint and isolated runtime environments; source exports
are not a model installer. Reference patches under `scripts/patches/` retain the
SGLang embedding adapter, optional read-only GPU audits and opt-in DFlash meta
construction. The DFlash patch is experimental evidence, not enabled by the
maintained profile. Audit hooks are opt-in through `LOCAL_GPU_WEIGHT_AUDIT_DIR`.
Dry reverse-application checks passed against the installed files. The embedding
reference check is `scripts/test_sglang_quantized_embedding.py`, run with the
SGLang environment in a bounded test service. It requires two accessible GPUs.

Raw settings, requests, qualification results, placement audits, provenance,
telemetry and failure logs remain in ignored private `data/optimization-20261027/`.
Only the reviewed source and this sanitized summary are exported to the public
repository. Credentials, user paths, GPU identifiers and raw logs are excluded.
