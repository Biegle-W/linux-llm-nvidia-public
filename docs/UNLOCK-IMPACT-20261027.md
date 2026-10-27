# Unlock impact on the current profiles

This assessment uses saved results and read-only configuration/source review.
**No GPU, model or unlock benchmark was rerun for this assessment.**

The measured compute unlock works on both cards. Saved five-sample large-GEMM
medians with FP32 accumulation improved FP16/BF16 throughput by **59.8% / 67.2%**
on RTX 3080 Ti and **87.3% / 82.9%** on RTX 3080. FP32 throughput did not improve.
Sampled output checks and 759 focused matrix correctness tests per card passed
in the qualified boot. [Original evidence and limitations](BENCHMARK-UNLOCK-20261026.md).

## What the model evidence establishes

The saved stock/unlocked comparison used older **8K** MoE settings, identical
approximately 2.2K-input / 128-output prompts and three requests, across a reboot.
It did not hold every cache condition constant. These are observed changes,
not isolated causal gains for today's settings:

| Model / engine | Longer-input prefill change | Native decode change | TTFT stock → unlocked |
| --- | ---: | ---: | ---: |
| Flash-Next IQ3_XXS / Strata | +2.0% | -4.1% | 3.53 → 3.47 s |
| GLM S24 / Maya | +3.4% | -3.8% | 26.97 → 26.09 s |
| DeepSeek Maya-S / Strata | +1.8% | +3.8% | 63.66 → 62.58 s |
| DeepSeek Maya-S / Maya | -0.2% | +10.0% | 40.66 → 40.66 s |

The streamed models spend substantial time on CPU experts, RAM, SSD and transfers.
Unlock does not increase VRAM capacity, memory bandwidth, SSD speed, CPU throughput
or PCIe bandwidth. Small mixed token-rate differences therefore do not demonstrate
the large proportional gain seen in compute-bound GEMMs. Their newer caches,
contexts and vision policies were not tested stock; today's exact unlock benefit
cannot be quantified from these older observations.

HyperQwen and SGLang have **no stock baseline for their current prepared quant and
settings**. GPU-resident prefill can plausibly use the extra FP16/BF16 FP32-accumulate
capacity, but that is an inference, not a measured token-rate gain. HyperQwen's
selected MLP-only W4A8/INT8 path differs from the unlocked floating-point path;
other layers and attention retain their configured arithmetic. SGLang's W4A16
prefill may use more of that floating-point capacity. Small-batch decode still
depends on memory access, recurrent/attention work, speculation and communication.

The pinned [unlock upstream](https://github.com/Zagitta/gpu-unlock/tree/af28cbbfd3d922a659227ecfb7369adfd924cf03)
identifies the FP/BF16 issue-rate change and distinguishes INT8 and bandwidth-bound
decode. This explains why a working unlock does not guarantee faster token rates
for every engine. It is reasonable to retain the already validated unlock;
the saved evidence does not support claiming a large current-model speedup or
that the current setup would perform identically without it.
