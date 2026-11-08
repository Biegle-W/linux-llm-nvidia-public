# DeepSeek Maya-S / Strata context expansion — October 27, 2026

The maintained DeepSeek-V4.1-Flash-1017 Maya-S Strata profile now allocates
**65,536 context tokens**, increased from 8,192. Startup and an authenticated JSON
check passed at both 32K and 64K. At 64K, a **58,969-token input** retrieved
three exact markers placed near the beginning, middle and end. This qualifies the
recorded input length; it does not establish correctness for every 65,536-token
conversation or any larger allocation.

## Selected setting

The existing Strata DeepSeek engine and shared Maya-S GGUF weights are unchanged.
Control/engine version is 0.1.51; bundled Control source is pinned to
`562a0c2ed7169ff6373f893b162106d55a828297`. Hardware remains the i5-13600KF,
64 GB DDR5, RTX 3080 Ti 12 GB and RTX 3080 10 GB.

- Context 65,536, one request, thinking disabled by default.
- Both GPUs; TP2 requested with the engine's original layer-group fallback.
- All six routed experts; drafting and vision disabled.
- CPU support threads 14, prefill chunk 4096, expert mmap enabled.
- 2048 MiB VRAM reserve per GPU; automatic expert RAM cache.
- One canonical `deepseek-maya-s` profile; the former 8K setting is retired.

The engine already accepts `--max-context`; no engine rebuild, extra model download,
quant change, rope scaling or firmware change was needed. The upstream
[DeepSeek guide](https://github.com/Niko1221/Strata/blob/main/docs/DEEPSEEK41.md)
describes 8192 as the checked default and supports requesting more context.

## New context qualification

| Allocation | Check | Result |
| --- | --- | --- |
| 32,768 | Authenticated JSON response, 16 input / 6 output tokens | Passed |
| 65,536 | Authenticated JSON response, 16 input / 6 output tokens | Passed |
| 65,536 | Three-marker retrieval, 58,969 input / 43 output tokens | Passed |

The retrieval archive used 3169 deterministic filler records and exact marker
values near 3%, 50% and 97% of the archive. Temperature 0, seed 271026, thinking
off, output cap 128, zero cached prompt tokens, one request and one retrieval run.
Its user text contained 58,950 tokens; chat framing accounts for the remaining
input tokens. Each fresh process started from a private copy of the saved
October 26 Strata expert profile. The 64K JSON check was recovered from its saved
result when the retrieval helper switched to Strata's bundled Python; it was not
repeated. The initial helper error was a missing `regex` module in system Python,
not an engine or context failure.

| 64K retrieval measurement | Value |
| --- | ---: |
| Native prefill | 60.6 tok/s |
| Native decode | 1.5 tok/s |
| Client first-token latency | 972.54 s |
| Total client time | 1000.68 s |
| Cached input tokens | 0 |

This is a context/retrieval qualification, not a repeated standard speed benchmark.
Its structured answer and long input differ from the prior prose-generation
fixture. Long inputs incur substantial prefill time on streamed experts. The
worker's automatic RAM store was about 26.2 GB, versus 42.5 GB in the historical
unlocked benchmark; cache size and worker limits also prevent attributing speed
differences solely to context.

## Preserved speed baseline

The completed [October 26 unlocked benchmark](BENCHMARK-UNLOCK-20261026.md)
remains unchanged: at an **8K benchmark allocation** and approximately 2.2K input
tokens, Strata DeepSeek measured median **34.8 prefill / 2.7 decode tok/s**, with
62.58 s TTFT across three repetitions. Those are historical 8K measurements and
must not be relabeled as 64K throughput. No completed 8K benchmark was repeated.

## Resource checks and limitations

Tests ran in owned systemd workers with MemoryHigh 30 GiB, MemoryMax 36 GiB and
MemorySwapMax 1 GiB. Monitoring would stop below 8 GiB available host memory or
at 82 C on a GPU. Sampled GPU peaks were 62/48 C; minimum available host memory
was 26.4 GiB and maximum host swap use was 0.31 MiB. Startup left approximately
2 GiB VRAM free per GPU. No memory or thermal guard was relaxed.

No allocation above 64K, broad long-context quality, tool use, images, drafting or
multi-request concurrency was qualified. The shared Maya DeepSeek profile and all
other retained profiles are unchanged. The normal Qwen default is restored after
the context tests.

## Evidence and launch

Private raw requests, streamed events, exact configurations, tokenizer counts,
telemetry, original-file hashes, helper error and recovered results are preserved
under `data/deepseek-context-20261027/`. Credentials and machine-specific paths are
excluded from this reference. The former configuration is preserved in the private
retirement archive, batch `linux-nvidia/2026-10-27-deepseek-strata-context`,
commit `9390945`.

The canonical runtime launch plan was checked after promotion and resolves to
65,536 tokens. The API credential is unchanged, and its expert-cache file is
initialized from the same saved seed used by the context trials.

Start the maintained profile after stopping any existing worker on port 10000:

```bash
./scripts/start_model.sh strata-deepseek
```
