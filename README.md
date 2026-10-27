# Linux LLM NVIDIA — public reference

Native Linux inference on the **i5-13600KF / 64 GB DDR5 / RTX 3080 Ti 12 GB +
RTX 3080 10 GB** workstation. A later PEX88096 switch installation adds
**RTX 3060 12 GB**. The separate dual-RX-7900-XTX Linux machine has its own
repositories and must not be modified as part of this migration.

The initial Windows-side preparation did not validate native Linux operation.
Do not promote inherited Windows profiles to validated Linux settings. Follow
[the Linux-agent migration handoff](docs/MIGRATION-HANDOFF.md).

**Native setup, October 26, 2026:** Ubuntu 26.04, the RTX 3080 Ti / RTX 3080 pair
and distribution NVIDIA driver 595.99.02 are now verified. Native llama.cpp CUDA
build and a short two-GPU inference smoke test passed; 31 focused matrix tests
passed on each GPU. Those initial checks did not establish unlock, P2P or sustained thermals.
[The two-card unlock is installed and verified](docs/UNLOCK-SETUP-20261026.md);
759 matrix tests per GPU passed after activation. See the
[unlocked-versus-stock comparison](docs/BENCHMARK-UNLOCK-20261026.md).
[A bounded native speed benchmark](docs/BENCHMARK-20261026.md) now covers all three
downloaded models and compares DeepSeek's two engines on shared Maya-S weights.
API smoke checks passed for Strata Qwen3.8-Flash-Next,
Maya GLM-5.3-Flash and DeepSeek on both engines. Strata also passed arithmetic,
JSON and conversation tests using Maya-S's shared DeepSeek weights; the separate
IST-DAS weight files were removed. See [native validation](docs/VALIDATION-20261026.md) and
[local setup](docs/LOCAL-SETUP.md); raw machine details remain ignored.

**Dense Qwen3.8-27B now defaults to HyperQwen/patched vLLM:** GPU-only TP2,
MTP3, BF16 recurrent state, INT4 KV and a 32K allocation. The selected profile
measured **155 code / 108 prose tok/s** and passed 29,496-token retrieval.
The SGLang choice uses GPU-only PP2, CUDA graphs and 16K context at **47 / 47 tok/s**.
[Engine settings, comparisons and validation](docs/DENSE-ENGINE-OPTIMIZATION-20261027.md)
include the old 4070 + 3060 reference and guarded DFlash/SGLang TP failures.
Start the default with `./scripts/start_model.sh qwen27b`, or explicitly select
`./scripts/start_model.sh qwen27b sglang`. The prior
[IQ4_XS/MTP2 measurements](docs/QWEN27B-GPU-ONLY-20261026.md) remain preserved.

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

Dense models must keep model execution weights in GPU memory by default. Do not
use generic host-RAM weight offload to make them fit. An exception requires a
community fork with documented offload performance optimizations relevant to the
installed hardware; evaluate its evidence before testing, then validate locally
inside the bounded worker service. This restriction concerns dense-model weight
offload, not ordinary loading buffers or the existing MoE expert-streaming paths.

The user chooses when to reboot and switch OS. Do not repartition, flash VBIOS,
change firmware security, restore the removed Windows NVMe unlock or install a
blanket `targets=all` unlock through a documentation migration. Record fresh native
Linux baselines before unlock; test compute unlock, peer transfers and inference
independently. Adding a GPU or switch requires rediscovering topology and addresses.

Retire unused source/settings into the private archive with hashes, original path,
source repository, source commit, date and reason. Keep only a pointer in active
repositories. Preserve dated benchmark evidence and active regression fixtures.
