# P2P driver preparation — October 30, 2026

Status: built, NOT installed; administrator/security approval pending. No driver, GRUB, IOMMU or model setting changed.

The current topology exposes the switched RTX 3080 Ti and RTX 3080 at x8 each; the switch uplink is Gen4 x16. The motherboard-connected RTX 3060 is x4. GPU link speeds were sampled idle. Direct CUDA checks return no peer access on NVIDIA 595.99.02; the visible correctness-test baseline exited 3 at the capability check, before transfer allocation.

## Prepared candidate

Ubuntu NVIDIA 615.71.09 userspace and matching aikitoria open kernel modules, pinned to `c8bff5400e2fc8bda4cb9a141fb596aad607a35f` on branch `615.71.09-p2p`. Both larger GPUs have 16 GiB BAR1 apertures. The isolated module build initially failed on the known Linux 7 CXL header issue, then passed with the two CXL structure/member guards changed from header presence to `NV_CXL_INIT_SUPPORTED`. All five module versions report 615.71.09. SHA256 manifests are retained privately.

The prepared installation uses Ubuntu precompiled stock 615 modules as fallback, places patched modules in a separate kernel-specific directory with explicit depmod selection, updates the tensor-unlock target PCI addresses, rebuilds boot images through the existing transactional helper, and adds Intel IOMMU passthrough. It does not unload the active desktop driver or reboot automatically. Rollback removes the trial module selection and passthrough drop-in, retaining Ubuntu 615 and the corrected tensor-unlock addresses. This is a current-kernel trial, not qualification for future kernel/driver updates.

## Approval blocker

Automatic approval review rejected installation because it replaces the system-wide 595 stack and enables IOMMU passthrough, reducing DMA isolation. The installation terminal did not start. Explicit human approval of those concrete changes is required before retrying; do not bypass the rejection by indirect execution.

## Remaining verification

After approved installation and reboot: verify the selected patched modules and userspace versions, early tensor unlock, all three GPUs, BAR1 and lane widths. Run the prepared bounded CUDA test in a visible terminal: three deterministic patterns of actual remote reads/writes in both directions, 16 MiB allocations and peer-copy timing. A timeout or correctness failure is not success; topology labels alone are insufficient. P2P success has NOT been established.

Sources: [P2P source](https://github.com/aikitoria/open-gpu-kernel-modules/tree/615.71.09-p2p), [NVIDIA CXL build issue](https://github.com/NVIDIA/open-gpu-kernel-modules/issues/1433).
