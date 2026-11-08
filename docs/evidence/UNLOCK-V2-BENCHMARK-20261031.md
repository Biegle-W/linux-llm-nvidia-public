# GPU unlock 2.0 compute benchmark — October 31, 2026

All three cards passed the current compute screen. Compared with saved 1.0 results, the 3080 Ti changed little; the 3080 was faster, including in the FP32 control. These historical differences do not establish an unlock-version performance gain. No earlier Linux 1.0 GEMM baseline was recorded for the 3060.

## Results

Medians in TFLOPS. FP16 and BF16 use FP32 accumulation.

| GPU | Input | Unlock 1.0 | Unlock 2.0 | Historical change |
| --- | --- | ---: | ---: | ---: |
| RTX 3080 Ti | FP32 | 26.76 | 26.80 | +0.17% |
| RTX 3080 Ti | FP16_FP32acc | 121.12 | 121.53 | +0.34% |
| RTX 3080 Ti | BF16_FP32acc | 125.75 | 126.87 | +0.89% |
| RTX 3080 | FP32 | 22.40 | 23.72 | +5.85% |
| RTX 3080 | FP16_FP32acc | 114.51 | 120.95 | +5.62% |
| RTX 3080 | BF16_FP32acc | 113.13 | 121.80 | +7.66% |
| RTX 3060 | FP32 | — | 10.39 | No prior baseline |
| RTX 3060 | FP16_FP32acc | — | 49.53 | No prior baseline |
| RTX 3060 | BF16_FP32acc | — | 49.07 | No prior baseline |

## Method and comparison limits

The unchanged saved cuBLAS GEMM binary used 8192×8192 matrices, two warmups, then five timing samples of ten operations per input type. Three sequential sweeps rotated card order. Current results use 15 samples per card/type; the October 26 comparison uses five samples per card/type. Each run checked 32 deterministic output elements against a CPU reference. All 135 timing samples completed with sampled correctness passing; this is not exhaustive matrix validation. Per-sweep medians and sample ranges are in the [numeric record](benchmark-results/20261031-unlock-v2-gemm.json).

The old session used unlock 1.0, Linux 7.0.0-38-generic and NVIDIA 595.99.02; the current session uses unlock 2.0, Linux 7.0.0-42-generic and NVIDIA 615.71.09 with the qualified dynamic BAR1/P2P driver. PCIe topology also changed. The same saved benchmark executable is used, but previous cuBLAS library hashes were not recorded. Power limits for the two comparable cards remained 350/320 W; the 3060 uses 170 W. No clocks or power limits were changed. These are warm compute microbenchmarks, not model prefill/decode measurements.

The 3080 FP32 control rose 5.85%, close to its 5.62% FP16 change; this is consistent with a broader session/driver/boost effect rather than evidence for a second unlock gain. A controlled version-only comparison, especially for the 3060, would require separately qualified 1.0 and 2.0 boots on the same current driver/topology. No rollback or reboot was performed for this benchmark.

## Resource and cleanup checks

Peak sampled GPU temperatures were 40°C / 38°C / 50°C for the 3080 Ti / 3080 / 3060. Minimum sampled host available RAM was 54.20 GiB. Ownership, 82°C thermal, host-memory, free-VRAM admission and per-run timeout guards remained active; no guard stopped the tests. The reservation was released and the GPUs returned to compute-idle. Unlock health remained VERIFIED; no new NVIDIA Xid or PCIe Bus Error entries were found in the inspected benchmark interval. Existing services, models and profiles were preserved.

Prior evidence: [October 26 locked versus unlocked screen](BENCHMARK-UNLOCK-20261026.md). Raw per-sweep outputs and telemetry remain in ignored private working storage.
