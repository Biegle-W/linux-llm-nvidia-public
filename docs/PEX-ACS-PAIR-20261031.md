# Scoped PEX ACS/routing diagnosis — October 31, 2026

Status: prepared; administrator-authenticated audit/trial pending. No ACS correction has passed yet. Preserve the verified automatic tensor unlock on all three cards independently.

CUDA capability inspection confirms that the dynamic driver enables only RTX 3080 Ti ↔ RTX 3080. All four directions involving the motherboard-connected RTX 3060 report no peer access. All three GPUs are in identity IOMMU domains. The two GA102 devices share a Broadcom PEX880xx fabric with multiple nested bridges; the 3060 is on a separate chipset root port.

The prepared audit resolves the actual GA102 pair by model IDs, walks their current sysfs ancestry and selects only Broadcom 1000:c010 bridge functions on those paths. It explicitly rejects overlap with the 3060 path and never writes CPU-root or GPU endpoint registers. It records extended ACS capabilities/control words, memory-window metadata and preimages. It checks for active compute work before testing.

Temporary trials clear the standard ACS request/completion redirection and egress-control bits first (mask 0x2c). If necessary, a second trial clears the standard ACS controls (mask 0x7f), following NVIDIA's PLX troubleshooting approach while preserving reserved bits. Every trial restores original controls. A 64 KiB read-only probe must pass before the full 16 MiB bidirectional read/write correctness test is allowed. Both tests expose only the two approved GPU UUIDs to CUDA; the 3060 is excluded.

Only a successful full correctness trial permits installation of a root-owned, model-scoped boot service. It re-resolves the same switch path each boot, requires the qualified driver srcversion, leaves the motherboard path alone and restores saved controls on stop. The full test is repeated after enabling that service; failure removes the policy and restores originals. No global ACS override, bridge reset, BIOS update, driver replacement or reboot is part of this trial.

Three CPU tests passed: extended-capability traversal, restoring controls after a failed read, and refusing writes to a 3060 endpoint. Actual bridge-control findings and GPU correctness remain pending OS administrator authentication.

Source: [NVIDIA NCCL GPU/ACS troubleshooting](https://docs.nvidia.com/deeplearning/nccl/archives/nccl_2312/user-guide/docs/troubleshooting/gpu_troubleshooting.html). The official recommendation discusses ACS and PLX switches; it does not establish the cause on this machine before inspection.
