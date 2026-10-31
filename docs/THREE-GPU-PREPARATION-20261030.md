# Three-GPU hardware-change preparation — October 30, 2026

Planned topology: RTX 3080 Ti 12GB and RTX 3080 10GB behind a PEX88096 switch; RTX 3060 12GB connected directly to the motherboard. Hardware is not yet installed or qualified.

A per-user oneshot service, `three-gpu-inventory.service`, is enabled at login. It captures NVIDIA inventory, PCIe topology, link widths and reported peer-read access without loading a model or changing hardware. Private results stay under `data/three-gpu-prep/`; GPU identities are not exported.

The desktop shortcut **Prepare Three GPU Unlock** is intended for after hardware installation. It refuses to change anything unless exactly PCI device IDs 2208, 2206 and 2503 are present. It discovers their current PCI addresses and invokes the existing pinned tensor-unlock preparation helper with administrator authentication. That helper retains its transactional backup/initramfs verification and Secure Boot checks. Current GRUB/dracut configuration preimages were saved privately.

## Procedure

1. Shut down fully before installing hardware. Connect both larger GPUs to the switch and the 3060 to the intended motherboard slot.
2. Boot and log in. The read-only inventory runs automatically. Existing explicit unlock addresses may no longer match after PCI enumeration changes.
3. Run **Prepare Three GPU Unlock**, authenticate in the normal Linux password prompt, and require successful completion. Then fully shut down and start again to apply the newly discovered addresses.
4. Verify all three cards, early tensor-unlock health, actual link widths and P2P correctness before launching models or changing placement. Existing two-GPU profiles may select different physical cards if enumeration changed; do not assume their numeric indices remain stable.

This preparation does not enable GeForce P2P, install a patched NVIDIA driver, alter BIOS settings, restart current workers, reboot automatically, or qualify three-GPU model placement. The tensor-core unlock and CUDA peer access are separate features. The motherboard is an ASUS TX GAMING B760M WIFI; actual slot lane sharing and switch wiring must be checked after installation.

## Verification

Python compilation, shell syntax, systemd unit verification and desktop-entry validation passed. The inventory was executed on the current two-card system: it correctly reported the expected third card absent and current unlock PCI addresses matching. The repair mutation was deliberately not executed against the old topology. Administrator authentication is required and cannot be supplied noninteractively in this session.
