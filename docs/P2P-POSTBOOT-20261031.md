# P2P post-boot verification — October 31, 2026

Result: FAILED correctness. Do not treat advertised peer capability as working P2P. No model throughput benchmark or production P2P enablement was performed.

NVIDIA 615.71.09 is loaded on all three cards. The boot command line contains `intel_iommu=on iommu=pt`. Both 3080 links are x8; the 3060 link is x4. NVIDIA topology reports peer access OK, and CUDA reports peer access supported, but the actual 16 MiB remote-read verification returned `REMOTE READ MISMATCH` and exit code 4 before bandwidth measurement. The test stopped; neither direction has passed full qualification. No active compute job was present before that test.

Only the RTX 3060 has confirmed pre-NVIDIA tensor-unlock success in this boot. The switched RTX 3080 Ti and RTX 3080 moved from PCI addresses 09:00.0 and 11:00.0 to 0a:00.0 and 12:00.0. Their explicit kernel unlock targets therefore missed them. The root-owned health check correctly reports failure. PCI target selection must be made robust to switch enumeration changes before claiming persistent three-GPU unlock.

The final preboot audit did succeed, updated the root health configuration for the then-present addresses, and performed the authorized reboot. Earlier failure on recovery-menu entry validation was an audit bug, not evidence that normal GRUB generation failed. This successful preboot audit is superseded by the actual failed post-boot correctness and identity checks above.

The prepared fallback removes the patched module override and passthrough drop-in while keeping stock Ubuntu 615 modules. Driver/mapping diagnosis and another authenticated boot-preparation change are required before all requested behavior can be confirmed. Avoid multi-GPU workloads until the incorrect peer-memory path is corrected or disabled. Do not rerun broad performance trials to mask this correctness failure.
