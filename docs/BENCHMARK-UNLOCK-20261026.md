# Unlocked versus stock benchmark — October 26, 2026

Both RTX 3080 Ti and RTX 3080 reported successful gpu-unlock activation before NVIDIA loaded after a user-controlled restart. NVIDIA driver 595.99.02, kernel 7.0.0-38-generic and power limits of 350 W / 320 W were unchanged. No NVIDIA Xid errors were found in the inspected boot log.

## Per-card compute

Five 8192-cubed cuBLAS GEMM samples per input type used FP32 accumulation and the same benchmark binary before and after the restart. Values below are medians. Deterministic sampled outputs passed CPU-reference checks in both sessions; 759 focused llama.cpp matrix correctness tests also passed per card after unlock.

| GPU | Input / accumulation | Stock TFLOPS | Unlocked TFLOPS | Change |
| --- | --- | ---: | ---: | ---: |
| RTX 3080 Ti | FP32 | 26.76 | 26.76 | +0.0% |
| RTX 3080 Ti | FP16_FP32acc | 75.82 | 121.12 | +59.8% |
| RTX 3080 Ti | BF16_FP32acc | 75.21 | 125.75 | +67.2% |
| RTX 3080 | FP32 | 22.81 | 22.40 | -1.8% |
| RTX 3080 | FP16_FP32acc | 61.12 | 114.51 | +87.3% |
| RTX 3080 | BF16_FP32acc | 61.86 | 113.13 | +82.9% |

## Model comparison

Three short and three longer streamed requests were repeated for each model/engine combination. Every measured request produced 128 output tokens with no reasoning output and zero reused prompt tokens. Values are medians of three requests. Generation and prompt rates come from native engine timings; TTFT is measured by the local client.

| Model / engine | Input | Stock generation tok/s | Unlocked generation tok/s | Change | Stock prompt tok/s | Unlocked prompt tok/s | Change | Stock TTFT s | Unlocked TTFT s |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Qwen3.8-Flash-Next IQ3_XXS / Strata | short | 108.4 | 98.8 | -8.9% | 133.6 | 142.0 | +6.3% | 1.29 | 1.21 |
| Qwen3.8-Flash-Next IQ3_XXS / Strata | long | 106.1 | 101.7 | -4.1% | 625.2 | 637.6 | +2.0% | 3.53 | 3.47 |
| GLM-5.3-Flash S24 / Maya | short | 7.1 | 7.2 | +1.4% | 11.0 | 11.9 | +8.2% | 15.62 | 13.75 |
| GLM-5.3-Flash S24 / Maya | long | 7.8 | 7.5 | -3.8% | 81.2 | 84.0 | +3.4% | 26.97 | 26.09 |
| DeepSeek Maya-S / Strata | short | 2.5 | 2.7 | +8.0% | 3.0 | 3.1 | +3.3% | 51.68 | 49.87 |
| DeepSeek Maya-S / Strata | long | 2.6 | 2.7 | +3.8% | 34.2 | 34.8 | +1.8% | 63.66 | 62.58 |
| DeepSeek Maya-S / Maya | short | 3.9 | 3.4 | -12.8% | 5.0 | 4.6 | -8.0% | 30.67 | 32.96 |
| DeepSeek Maya-S / Maya | long | 4.0 | 4.4 | +10.0% | 53.6 | 53.5 | -0.2% | 40.66 | 40.66 |

## DeepSeek after unlock

Using the same shared Maya-S weights, Maya generated 63.0% faster than Strata on the longer-input case (4.4 versus 2.7 tok/s).

## Method and interpretation

- Automatic expert RAM allocation differed: Strata DeepSeek used 43.6 GB stock versus 42.5 GB unlocked; Maya read-ahead used 47.8 GB stock versus 46.8 GB unlocked. This further limits attributing model-rate differences solely to unlock.
- The [stock benchmark](BENCHMARK-20261026.md) documents the prompt fixture, versions and native cache differences. The repeated run used identical prompts, input token counts, engine revisions, requested configuration, and initial DeepSeek expert-cache seed. Temperature 0, seed 261026, one concurrent request, thinking disabled and 8192 allocated context tokens were preserved. Inputs were about 150–171 or 2171–2209 tokens, not a full 8K input test.
- Qwen and GLM retained drafting; both DeepSeek engines kept drafting and vision off. All six routed DeepSeek experts, the shared GGUFs, 14 CPU threads, 4096-token prefill chunks and 2048 MiB reserve per GPU were preserved. Both GPUs participate through the original layer-group fallback.
- This is a before/after observation across a restart, not a randomized unlock-only experiment. OS page cache, background desktop activity and cache warming were not held constant. Test order remained Qwen/Strata, GLM/Maya, DeepSeek/Strata, DeepSeek/Maya. Native engine cache implementations differ. Three repetitions do not establish statistical confidence intervals; small changes may be run variation.
- Per-card GEMM changes establish improved measured compute with passing sampled correctness; they do not predict proportional decode gains. The model task is synthetic text generation and does not establish broad output quality, tool use, P2P, full-context behavior or sustained thermal limits.

## Evidence

The stock record is retained privately under `data/benchmarks/20261026-173730/` and the repeated run under `data/benchmarks/20261026-195450/`. Raw API events, request fixtures, protocol, resource samples, independent summaries, validation and comparison records are retained. Per-card samples and boot proof remain in ignored private data. Credentials and machine identifiers are excluded from this reference.

The normal Qwen serving profile was restored after measurement. Temporary benchmark configurations did not replace the installed serving profiles.
