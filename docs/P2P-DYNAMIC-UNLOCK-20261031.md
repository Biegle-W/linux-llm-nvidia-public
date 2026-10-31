# Dynamic BAR1 and address-independent unlock candidate — October 31, 2026

Status: built and CPU-tested, not yet activated or GPU-qualified. The previous static BAR1 candidate failed a real remote-read correctness check; preserve that failure in P2P-POSTBOOT-20261031.md.

## P2P candidate

The replacement uses the Ampere-specific dynamic BAR1 implementation from noon-at-cgn/3080-20g-p2p, commit `cbb4fce1b4e75158b7923d076a147d1f19e9fce3`, matching installed NVIDIA 615.71.09 userspace. It maps individual peer allocations rather than assuming static framebuffer offsets. The same two Linux 7 CXL declaration guards were corrected. All five modules built successfully. SHA256 and srcversion manifests are private. No firmware flash or PCI BAR resize is performed; the existing firmware-assigned 16 GiB BAR apertures are retained. This upstream implementation was qualified on modified 20GB cards, so correctness on this stock 3080/3080 Ti pair still requires the local post-boot test.

The two GA102 cards receive `RMForceStaticBar1=0` via dynamically generated per-device options. The 3060 is not opted into the dynamic peer path. Driver Resizable BAR remapping stays disabled and UVM HMM is disabled for this candidate as prescribed by its implementation. Stock Ubuntu 615 modules remain the fallback.

## Unlock independent of PCI addresses

A root-owned dracut pre-udev hook scans NVIDIA display functions and requires exactly one device each of 2208 (3080 Ti), 2206 (3080), and 2503 (3060). It passes their actual addresses to the existing pinned gpu_unlock 1.0.0 module before NVIDIA binds. It does not select additional GPU models. The opt-in becomes `local_llm_gpu_unlock=auto`; fixed `gpu_unlock.targets=` arguments and the old force-load are removed. The same hook generates the two GA102 BAR1 option addresses, avoiding a second stale-address dependency.

The root-owned health checker resolves the same approved identities, verifies the installed early hook against the boot image and requires per-card unlock success before NVIDIA initialization. Auto-mode fingerprints use approved identities rather than transient bus addresses. Original explicit-target mode remains covered by its tests. The firmware-unlock module and its reviewed source pin are unchanged.

## Validation and installation boundary

All 33 CPU tests passed, including shifted PCI addresses, missing/duplicate-model refusal, synthetic early-hook execution and stable identity-based fingerprints. The candidate driver build passed. These are preparation results, not proof of working GPU P2P or tensor throughput.

The prepared administrator-authenticated transaction snapshots previous modules, boot files and health configuration, stages the candidate, rebuilds the boot image, verifies preboot health plus the embedded core-module hash, then performs the authorized reboot only after success. Staging failure restores preimages. A visible post-login test checks loaded module srcversions, actual remote reads/writes in both directions, peer-copy timing and all-three-GPU unlock health. Keep model placement and NCCL production settings unchanged until that passes.

Sources: [dynamic driver](https://github.com/noon-at-cgn/3080-20g-p2p), [original tensor unlock](https://github.com/Zagitta/gpu-unlock).

## First staging attempt and packaging correction

The first authenticated staging transaction passed automatic-unlock preboot health but failed the final raw embedded-module hash comparison. It restored its preimages and did not reboot. Dracut strips debug data from unsigned modules with `strip -g`; the corrected verifier accepts only the exact original candidate or its exact debug-stripped form and additionally requires the embedded module srcversion to match. A fresh transaction directory is used for the retry. Neither the failed staging attempt nor these packaging checks establish working P2P.
