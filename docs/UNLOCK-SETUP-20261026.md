# Two-card unlock preparation — October 26, 2026

## Latest: unlock 2.0 and pair P2P verified after reboot — October 31

The loaded gpu_unlock module is **2.0.0** on Linux 7.0.0-42-generic with NVIDIA
615.71.09. Boot health reports **VERIFIED**, with successful unlock of the 3080 Ti,
3080 and 3060 before NVIDIA initialized and no pending reboot. The identity-based
hook handled changed PCI addresses. All 16 firmware files and the boot image
passed health checks. Patched NVIDIA module srcversions match the qualified
candidate. The scoped ACS service applied successfully on this boot; seeded
16 MiB remote reads/writes passed both directions at 13.081/13.085 GB/s peer copy.
No model-performance improvement is inferred from this hardware check.

Local scratch work/output folders are consolidated under the project's ignored
`data/work/` directory; compatibility links preserve existing paths. Cleanup
removed 2,402,957,853 logical bytes of duplicate downloads, superseded static-driver
builds and regenerable build products. Obsolete installers and retired settings
were hash-verified in the private retirement archive before removal. Maintained
runtimes, models, guards, rollback packages, source pins and benchmark evidence
remain available. Existing router and harness services remain active.

## Latest: GPU unlock 2.0 staged for all three cards — October 31

The requested upgrade installed gpu-unlock 2.0.0 from reviewed upstream commit
`7eb51bccae0a0b7e599e084d971170e9a1e82d0c`. DKMS built successfully for
7.0.0-42-generic; the target initramfs contains the matching 2.0 module/srcversion,
all declared firmware, and the unchanged model-ID-scoped pre-udev hook. Health
reports **PENDING REBOOT VERIFICATION**. The loaded module remains 1.0.0 until
the user chooses to reboot; successful 2.0 unlock on hardware is not yet claimed.
The 3080 Ti (2208), 3080 (2206), and 3060 (2503) remain the only selected targets.
NVIDIA 615.71.09, dynamic BAR1/P2P modules, early-selection hooks and boot options
were preserved; protected file hashes matched. Old 1.0 packages and boot/config
preimages are retained privately for rollback. No live GPU reload or reboot ran.
No additional performance gain over the verified 1.0 unlock is claimed.

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

## Required checks after kernel or NVIDIA driver updates

These checks are now implemented by the installed [OS health services](GPU-UNLOCK-HEALTH.md),
triggered by package updates and system boot independently of agents. Future agents
inspect their saved results and failed/pending status after authorized updates or
changed versions. This does not initiate updates/reboots. Retain the reviewed
unlock source unless the user separately authorizes a source/version change.

1. Record the running kernel, installed/loaded NVIDIA driver versions, selected
   GPU identities and PCI addresses, and the last verified boot. Distinguish the
   running kernel from a newly installed kernel awaiting reboot. Re-discover
   addresses if cards or PCIe topology changed; do not expand targets blindly.
2. Check `dkms status` and module availability for the kernel that will boot next.
   Confirm the unlock module built/installed successfully for that exact kernel.
   Verify the helper-owned GRUB target argument and dracut early-load configuration
   still exist. Inspect the generated target initramfs for the unlock module, its
   declared firmware and the pre-udev early-load request. Review update errors;
   presence of configuration files alone is not proof of a complete boot image.
3. After the user chooses to reboot, inspect that boot's kernel command line and
   kernel log. Both selected cards must report successful unlock before NVIDIA
   driver binding. Confirm both cards are available through `nvidia-smi` under
   the expected driver, and inspect relevant unlock/NVIDIA errors. A driver update
   using an unchanged kernel still requires this post-boot compatibility check;
   do not assume all future driver releases behave identically.
4. Record dated evidence in CURRENT-STATE.md: kernel and driver versions, target
   identities/addresses, DKMS/image checks, boot evidence and pass/fail/pending
   status. Before reboot, report only next-boot readiness with post-boot verification
   pending. On failure, report the exact missing/failed stage and recovery plan;
   do not silently disable the unlock, change firmware security, flash VBIOS, or
   upgrade the pinned unlock source. Preserve the user-controlled reboot policy.

These read-only persistence checks do not require rerunning completed compute or
LLM benchmarks. Module installation and boot messages do not quantify performance
on a new software stack; any additional qualification must be scoped separately.
Keep both NVIDIA repositories and their handoff current after meaningful findings.
