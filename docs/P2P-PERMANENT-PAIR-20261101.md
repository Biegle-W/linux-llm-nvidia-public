# Permanent two-card P2P repair — November 1, 2026

Hardware is now the RTX 3080 Ti and RTX 3080 only. The RTX 3060 is permanently removed.

The old automatic early-unlock hook required exactly three GPU models. Removal of the 3060 made it skip early initialization; the matching health validator failed and the dependent scoped ACS service did not run. The current failed boot reports peer access unsupported, and HyperQwen disabled its custom collective. Earlier three-card P2P results remain historical evidence.

The repair selects exactly one 2208 and one 2206 display device using discovered PCI addresses. It generates the pair's dynamic BAR1 options before NVIDIA binds. Health supports the explicitly selected pair; legacy three-card records remain readable. The installed scoped ACS policy is adapted to the absent 3060 while retaining the qualified bridge mask, driver-version check, bridge ancestry restrictions and rollback behavior.

After early-unlock health and ACS succeed, a root-owned boot checker runs the bounded CUDA verifier: three deterministic patterns, 16 MiB remote reads and writes, both directions. It writes a current-boot report only when verification completes; failures do not pass. Every maintained model's normal worker entry point requires a root-owned, non-user-writable successful report matching the running boot and NVIDIA module before loading. Thus missing P2P cannot silently become a selected-model fallback. Driver changes invalidate qualification rather than silently relaxing checks.

All 356 CPU tests passed in 2.957 seconds, including two-card discovery, shifted addresses, duplicate/missing-card refusal, early-hook execution without a 3060, stale proof and proof ownership checks. These are preparation tests, not post-reboot hardware proof. No model or full-context benchmark was run.

Administrator staging retains root-owned preimages of the changed integration files and boot image, rebuilds the current kernel's initramfs and requires successful next-boot health. It never reloads the live display driver or reboots automatically. Actual peer correctness must be confirmed after the user-controlled reboot; until then the repair is pending activation.

## Post-reboot result

**PASS after the November 1 reboot.** The early hook selected only the discovered RTX 3080 Ti and RTX 3080. GPU unlock health is VERIFIED. The scoped ACS service applied its policy and completed the seeded 16 MiB remote-read/write check with three patterns in both directions. Each direction passed correctness and measured 13.082 GB/s peer-copy throughput. NVIDIA reports peer reads and writes OK for both directions.

The root-owned proof is mode 0644 and matches the current boot and loaded NVIDIA module. Running the same proof gate used by the maintained workers succeeded. No model was loaded, no full-context test ran, and both worker services remained inactive. This verifies hardware peer access and boot persistence; it does not claim that every engine selected a particular collective or establish new model-speed results.
