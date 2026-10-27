# Two-card unlock preparation — October 26, 2026

The pinned [Zagitta gpu-unlock source](https://github.com/Zagitta/gpu-unlock/tree/af28cbbfd3d922a659227ecfb7369adfd924cf03)
(version 1.0.0) was built and installed through DKMS for kernel 7.0.0-38-generic.
Only the detected RTX 3080 Ti and RTX 3080 were selected. After a user-controlled restart, both selected cards reported successful unlock
before NVIDIA loaded. Per-card compute and numerical correctness passed. See the
[unlocked-versus-stock model comparison](BENCHMARK-UNLOCK-20261026.md).

## Initramfs repair

On this Ubuntu installation, `update-initramfs` invokes dracut. The original
helper assumed initramfs-tools hooks; its image check correctly failed and
rolled back activation when the module was missing. The repaired helper detects
the wrapper implementation and fails closed for an unknown builder.

For dracut it writes an owned `force_drivers` configuration, which requests
`gpu_unlock` through `rd.driver.pre` before udev can bind NVIDIA. It verifies the
module, every declared firmware file, the early-load request and pre-udev service
in the generated image before updating GRUB. The initramfs-tools path retains its
owned early hook. Inactive helper-owned hooks are removed transactionally;
rollback and disable cover both builders. Fifteen host-only tests pass.

The repaired configuration and boot image were generated and verified. Driver,
power limits and firmware security settings were preserved. No live driver
unload, manual module unlock or automatic reboot was performed.

## Baseline and post-boot verification

Five 8192-cubed cuBLAS GEMM samples per input type used FP32 accumulation; sampled
output values passed deterministic CPU-reference checks. These are stock-clock
session measurements, not sustained thermal tests or predicted inference gains.

| GPU | FP32 TFLOPS | FP16 / FP32 accumulation TFLOPS | BF16 / FP32 accumulation TFLOPS |
| --- | ---: | ---: | ---: |
| RTX 3080 Ti | 26.76 | 75.82 | 75.21 |
| RTX 3080 | 22.81 | 61.12 | 61.86 |

Another 759 focused llama.cpp matrix correctness tests passed per card before
activation. [The stock model benchmark](BENCHMARK-20261026.md) remains the inference
baseline. Raw compute samples, image checks, addresses and installation logs are
retained privately.

After restart, successful per-card unlock logs preceded NVIDIA driver binding.
Both GPUs remained available without NVIDIA Xid errors in the inspected log.
Another 759 focused matrix tests per card passed, and sampled GEMM outputs
matched CPU references. FP16 throughput rose about 60% on the Ti and 87% on the
3080; BF16 rose about 67% and 83%. The model comparison retains cache/restart
caveats and separates prefill, TTFT and decode. Compute unlock does not establish P2P.

For recovery, remove `gpu_unlock.targets=...` once in the GRUB editor and boot
normally, then run `sudo python3 scripts/native_linux_gpu_unlock.py disable` from
the repository. The helper removes its own boot configuration and rebuilds the
images; the installed packages remain. Let the user control the next power cycle.
