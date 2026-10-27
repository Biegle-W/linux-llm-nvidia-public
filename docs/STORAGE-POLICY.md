# Model storage policy

Effective October 27, 2026, reserve NVMe model storage for models that stream
weights from SSD during inference. Put models whose execution weights reside in
GPU memory or RAM, including unused dense trial checkpoints, on the SATA SSD.
This policy concerns model files; installed engines, builds and environments
remain on the Linux filesystem.

## Current placement

| Model group | Access during inference | Required drive | Stable checkpoint path relative to repository |
| --- | --- | --- | --- |
| Qwen3.8-27B AutoRound, shared by HyperQwen/vLLM and SGLang | GPU-resident after loading | Samsung SSD 870 QVO SATA | `models/engine-tests/qwen38-27b-hyperqwen-fast` |
| Qwen3.8-Flash-Next IQ3_XXS, Strata | SSD-streaming with GPU/RAM caches | CT1000P3PSSD8 NVMe | `models/strata/models/IQ3_XXS` |
| GLM-5.3-Flash Maya-S24, Maya | SSD-streaming with GPU/RAM caches | CT1000P3PSSD8 NVMe | `models/maya/Maya-S24` |
| DeepSeek-V4.1-Flash-1017 Maya-S, shared by Strata and Maya | SSD-streaming with GPU/RAM caches | CT1000P3PSSD8 NVMe | `models/maya/DeepSeek-V4.1-Flash-1017-GGUF/Maya-S` |

The complete `models/engine-tests` directory is a link to
`llm-models/linux-nvidia/engine-tests` on the mounted SATA SSD. It includes the
kept dense checkpoint. Superseded trial weights and preparation inputs were
removed in the [unused-model cleanup](UNUSED-MODEL-CLEANUP-20261027.md); their
benchmark evidence and provenance remain preserved.
The alias keeps existing engine, router, desktop and tooling paths stable. The
actual mount mapping and the checksum migration manifest are private local state.

The SATA filesystem is exFAT. It cannot preserve the source's shared hardlinks,
so source files that shared an inode become separate regular files there. Model
contents are verified byte for byte. No engine build or virtual environment is
moved to exFAT. If the SATA mount is missing, restore the mount before launching
Qwen; do not create a replacement dense checkpoint on NVMe.

The owner-only `data/storage-mount.json` records the local SATA UUID and mount
point. Dense preflight checks the exact mounted UUID and, when absent, attempts
`udisksctl mount --no-user-interaction` for that device. An unexpected mounted
drive is preserved and refused. Desktop authorization controls mounting: before
login or in a session without permission, mount the drive in Files/Disks before
using dense Qwen. No new system-wide boot mount is installed.

## Enforcement and future downloads

Each kept profile records its access type, required drive transport and checkpoint
alias in `config/maintained-profiles.json`. The launchers resolve actual weight
files through links and check their block-device ancestry with `findmnt` and
`lsblk`. Dense launches require SATA; the current SSD-streaming profiles require
NVMe. A wrong drive, missing checkpoint or unknown transport stops startup.
The checks run before launching the selected engine; numerical, placement,
memory, thermal and process-ownership safeguards remain unchanged.

For new checkpoints, classify the engine's actual weight access before downloading:
GPU/RAM-resident weights and dense trial downloads go directly to SATA;
SSD-streamed expert/model packs go to NVMe. Use stable local aliases where needed.
Keep auxiliary packs with their parent streamed model. Avoid staging a second
resident-model weight copy on NVMe. Keep new profile metadata consistent with the
physical location and run:

```bash
python3 scripts/storage_policy.py                 # inspect all six profiles
python3 scripts/storage_policy.py qwen27b-hyperqwen
```

Before relocating existing weights, copy to a fresh destination, verify every file
with SHA-256, stop only the owned idle worker for cutover, verify both dense engines
can load and answer, then remove the verified source copy. Never remove a source
before the destination contents and launch paths have passed validation.

## Benchmarks and migration evidence

The [latest matched benchmark](BENCHMARK-20261027-101219.md) predates the storage
move. Its NVMe storage inventory remains correct for the time of measurement.
Prefill and decode figures are preserved as historical observations, rather than
new SATA-load measurements. The relocation checks validate loading and short
responses on both dense engines without repeating the full speed suite.

Private dated migration evidence retains the original and destination paths,
per-file SHA-256, source inode/size/mtime snapshots, physical-drive checks,
cutover/restore state and smoke-test responses. The public reference contains
this policy and sanitized launcher/profile updates, without live mount paths or
model weights.

## Completed migration checks

All 263 files (104.63 GB of logical file content) passed SHA-256 comparison.
Both HyperQwen/vLLM and SGLang loaded the SATA checkpoint through their existing
router IDs and returned the expected short reply. HyperQwen was restored as the
default, the temporary reservation was removed, and the verified NVMe source copy
was deleted, releasing approximately 82.72 GiB of unique checkpoint content.
The 27 local regression tests and launcher syntax/compile checks passed.
All four streamed-engine profiles retain NVMe placement; benchmark values and
long-context qualifications were preserved.

## Unused-model cleanup

The [October 27 cleanup](UNUSED-MODEL-CLEANUP-20261027.md) removed unused model
and preparation payloads after dependency and performance review. The active
checkpoint aliases and four unique base model packages remain. Do not recreate
superseded downloads merely because a historical test references their old paths.
