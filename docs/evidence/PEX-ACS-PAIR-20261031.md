# Scoped PEX ACS/routing correction — October 31, 2026

Status: **PASS in the current boot**, with a root-owned boot policy enabled. P2P is limited to RTX 3080 Ti ↔ RTX 3080. The motherboard-connected RTX 3060 has no CUDA peer access in either direction. All three GPUs retain verified pre-NVIDIA tensor unlocks.

## Cause and correction

The extended-configuration audit found 64-bit prefetchable windows throughout the selected switch paths. Four Broadcom downstream bridges had ACS control 0x1d: request and completion redirection were enabled. The scoped trial cleared those bits, leaving control 0x11. Source validation and upstream-forwarding controls were preserved; the broader all-standard-controls-clear trial was unnecessary. The three intervening upstream functions had no ACS capability to change.

Only the Broadcom bridges in the two GA102 devices' shared switch path were modified. CPU-root ports, endpoints and the separate motherboard/3060 path were excluded. All devices use identity IOMMU domains. The first audit stopped before writes because an overly broad work guard counted a terminal on the 3060; the corrected guard filters the two target GPU identities and preserved that unrelated process.

## Actual verification

The 64 KiB read-only probe passed, followed by the full 16 MiB seeded remote-read/write test in both directions. The full test passed again after persistent policy activation. Each full run checked three deterministic data patterns per direction, then measured peer-copy throughput.

| Measurement | Scoped trial | Persistent-policy confirmation |
| --- | ---: | ---: |
| 3080 Ti to 3080 copy | 13.081 GB/s | 13.084 GB/s |
| 3080 to 3080 Ti copy | 13.083 GB/s | 13.079 GB/s |
| Bidirectional remote read/write correctness | PASS | PASS |

These are small-transfer CUDA copy measurements, not LLM token rates or a sustained workload benchmark. Both switched cards remain x8; the motherboard 3060 is x4. Final CUDA capability checks show only the GA102 pair enabled, with all four 3060 peer directions disabled. GPU unlock health reports VERIFIED for all three, and no NVIDIA Xid or PCIe AER error was observed in the checked boot log.

## Persistence and rollback

The root-owned `local-llm-acs-pair.service` is enabled and active. It runs after successful GPU-unlock boot health and before the display manager, resolves the approved pair and its Broadcom ancestry on each boot, and checks the qualified NVIDIA module srcversion. It clears only the tested ACS mask on those paths. Stop/disable restores saved controls for the current boot. The policy does not execute user-writable test code at boot. Private root-owned preimages and reports are retained. The October 31 reboot subsequently verified automatic ACS application with changed GPU addresses. The post-boot seeded remote-read/write check passed both directions at 13.081/13.085 GB/s, with unlock 2.0 VERIFIED on all three GPUs.

The model-ID early-unlock hook remains separate: it requires exactly one approved 3080 Ti, 3080 and 3060 and already passed a real boot with changed PCI addresses. NVIDIA 615.71.09 uses the qualified dynamic BAR1 candidate for the GA102 pair; the 3060 is not opted into that peer path. Model profiles and their existing NCCL settings were not changed by this hardware correction.

Four ACS safety tests passed, including rollback after failed reads, rejecting a 3060 endpoint write, and ignoring unrelated 3060 work. Attention-terminal focus tests also passed; the actual authenticated retry opened in the foreground as requested.

Source: [NVIDIA NCCL GPU/ACS troubleshooting](https://docs.nvidia.com/deeplearning/nccl/archives/nccl_2312/user-guide/docs/troubleshooting/gpu_troubleshooting.html). The correctness and bandwidth results above are local measurements.
