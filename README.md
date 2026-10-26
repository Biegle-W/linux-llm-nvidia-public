# Linux LLM NVIDIA — public reference

Sanitized native Linux preparation for the **i5-13600KF / 64 GB DDR5 / RTX 3080 Ti 12 GB**
workstation. The user is migrating this NVIDIA machine from Windows to Linux.
The next hardware stage adds **RTX 3080 10 GB**; a later PEX88096 switch installation
adds **RTX 3060 12 GB**. The separate dual-RX-7900-XTX Linux machine has its own
repositories and must not be modified as part of this migration.

**Status: prepared, not deployed.** No native NVIDIA Linux installation, driver,
unlock boot, P2P transfer or Linux inference benchmark has been verified by this
Windows-side preparation. Do not promote inherited Windows profiles to validated
Linux settings. Follow [the Linux-agent migration handoff](docs/MIGRATION-HANDOFF.md).

## Repository ownership

| Build | Private operational repository | Public reference |
|---|---|---|
| Windows NVIDIA | [windows-llm-nvidia](https://github.com/Biegle-W/windows-llm-nvidia) | [windows-llm-nvidia-public](https://github.com/Biegle-W/windows-llm-nvidia-public) |
| Linux NVIDIA | [linux-llm-nvidia](https://github.com/Biegle-W/linux-llm-nvidia) | [linux-llm-nvidia-public](https://github.com/Biegle-W/linux-llm-nvidia-public) |
| Linux AMD | [linux-llm-amd](https://github.com/Biegle-W/linux-llm-amd) | [linux-llm-amd-public](https://github.com/Biegle-W/linux-llm-amd-public) |
| Retired settings | [retired-llm-setting](https://github.com/Biegle-W/retired-llm-setting) | Private only |

The AMD repositories retain their original history and installed checkout paths;
their former GitHub names were `ubuntu-llm-amd` and `ubuntu-llm-amd-public`.
Historical settings belong only in the private retirement repository's current
tree. Previously published Git history is preserved, not rewritten.

## Contents

- `docs/MIGRATION-HANDOFF.md`: ordered migration, unlock, P2P, engine and client work.
- `scripts/native_linux_gpu_unlock.py`: pinned Ubuntu/Debian/GRUB preparation for
  the three intended GPU product IDs; explicit current Linux PCI addresses only.
- `scripts/test_native_linux_gpu_unlock.py`: host-only policy/rollback tests.
- `config/model-catalog.example.json`: disabled model inventory; no deployed profiles.
- `docs/REPOSITORY-MAP.md`: the seven-repository ownership and retirement policy.

Models go under ignored `models/`; native builds/environments under `runtimes/`;
private inventories, mount mappings, credentials, captures and validation under
`data/`. Build native executables on Linux filesystems. Existing Windows model
weights can be reused after locating and verifying their files; never copy Windows
CUDA DLLs, UEFI payloads, AMD runtime configurations or old disk identifiers.

## Maintenance instructions

This README is the sole root agent-instruction file. Keep all GitHub-facing prose,
code comments, messages and commits in English. Keep private/public repositories
current after validated changes, with nonpersonal commits and no force pushes.
Export selected sanitized files only; never export private history or state.

Use one maintained profile per model at the largest locally validated configuration.
Record allocated context separately from tested input lengths. Keep numerical,
quality, memory, thermal and owned-process protections. Stop only owned inference
workers; preserve unrelated applications. Do not relax guards merely to load a model.

The user chooses when to reboot and switch OS. Do not repartition, flash VBIOS,
change firmware security, restore the removed Windows NVMe unlock or install a
blanket `targets=all` unlock through a documentation migration. Record fresh native
Linux baselines before unlock; test compute unlock, peer transfers and inference
independently. Adding a GPU or switch requires rediscovering topology and addresses.

Retire unused source/settings into the private archive with hashes, original path,
source repository, source commit, date and reason. Keep only a pointer in active
repositories. Preserve dated benchmark evidence and active regression fixtures.
