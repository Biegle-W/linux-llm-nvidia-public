# Model storage policy

## Kolibri 1.1 weights — November 24, 2026

The Q5_K_M GGUF of Kolibri 1.1 (53.4 GB, `models/engine-tests/kolibri-1.1-gguf`, SATA, hash-verified) was downloaded for a trial and now serves `kolibri-llamacpp`. Its experts are read into RAM from the memory-mapped file, so it belongs on SATA. `config/weights-inventory.json` attributes it to the router entry.

## Flash-Next UD-IQ4_XS weights unused — November 24, 2026

`flash-next-iq4xs-strata` was retired. Its UD-IQ4_XS-v31 checkpoint (`models/strata/models/unsloth-UD-IQ4_XS-v31`, about 88 GB) and Strata pack (`models/strata/packs/unsloth-ud-iq4_xs-v31`, 1.4 GB), both on NVMe, are kept unused and are the largest candidates under the rule below. The MTP head and vision projector stay with `flash-next-strata`.

## Inkling llama.cpp weights unused — November 24, 2026

`inkling-llamacpp` was retired; its UD-Q4_K_M GGUF and picture projector (17.25 GB, `models/engine-tests/inkling2-mini-trial`, SATA) are kept and are the first candidates under the rule below. `inkling-strata` uses the SQ-10 pack on NVMe (10.5 GB).

## Standing rule: free space from retired weights first — November 23, 2026

When a new model does not fit on either drive, the maintaining agent may delete weights that no router, Comfy or updater entry uses any more (retired or dropped entries, as listed under "Unused or duplicate weights" by `scripts/weights_tracker.py`) without asking again, owner's standing approval of November 23, 2026. Delete only as much as the new model needs, and record each deletion here with its size and path. Weights of current entries still go to the owner first (lowest-ranked suggested).

## Unused Qwen GGUF target/drafter deleted — November 4, 2026

The unconfigured Qwen3.8-27B Q4_K_M target and its MTP-only GGUF drafter were deleted at the user's request: 19.450 GB of weights. All nine configured entries and every maintained checkpoint/runtime remain unchanged. No inference or regression suite was repeated; unchanged-catalog/checkpoint and API/DSH checks verify preservation. Historical results remain dated evidence. [Removal record](evidence/UNUSED-QWEN-GGUF-REMOVAL-20261104.md).

## Retained weights without a router entry

At the owner's request `bolt-llamacpp` was retired on November 23, 2026. Its 22.0 GB IQ2 GGUF (`models/engine-tests/bolt-iq2`, SATA) was deleted the same day at the owner's request.

## Unsloth DeepSeek split-storage profile — October 31

The additional `deepseek-unsloth-strata` profile has an explicit per-file policy:
its first four GGUF shards, including metadata, stay on NVMe; its final Engram
shard stays on SATA. The checker resolves each file link, requires the declared
five-file set and rejects the wrong physical transport or missing shards.
This is a narrow split-storage exception; existing profiles keep their original
transport requirements. No weights were moved or downloaded for menu integration.

Effective October 27, 2026, reserve NVMe model storage for models that stream
weights from SSD during inference. Put models whose execution weights reside in
GPU memory or RAM, including unused dense trial checkpoints, on the SATA SSD.
This policy concerns model files; installed engines, builds and environments
remain on the Linux filesystem.

## Current placement

One entry uses a profile-specific placement from its November 22 trial: `hy4-flash-maya` maps its first GGUF shard and reads table rows from the second on the SATA SSD. Its storage preflight checks SATA ancestry and non-rotational media.

Per-drive usage and unused weights: run `python3 scripts/weights_tracker.py` (report in
`data/weights-tracker/latest.md`); last audit in [STORAGE-STATUS-20261108.md](evidence/STORAGE-STATUS-20261108.md).

| Model group | Access during inference | Required drive | Stable checkpoint path relative to repository |
| --- | --- | --- | --- |
| Qwen3.8-27B AutoRound, shared by HyperQwen/vLLM and SGLang | GPU-resident after loading | Samsung SSD 870 QVO SATA | `models/engine-tests/qwen38-27b-hyperqwen-fast` |
| Qwen3.8-Flash-Next IQ3_XXS, Strata | SSD-streaming with GPU/RAM caches | CT1000P3PSSD8 NVMe | `models/strata/models/IQ3_XXS` |
| Kolibri 1.1 Q5_K_M, llama.cpp | experts of 38 layers RAM-resident (memory-mapped), the rest GPU-resident | Samsung SSD 870 QVO SATA | `models/engine-tests/kolibri-1.1-gguf` |
| GLM-5.3-Flash Maya-S24, Maya | SSD-streaming with GPU/RAM caches | CT1000P3PSSD8 NVMe | `models/maya/Maya-S24` |
| DeepSeek-V4.1-Flash-1017 UD-IQ1_S, shared by Strata and Maya | SSD-streaming with GPU/RAM caches | NVMe shards 1-4; SATA shard 5 (symlinked) | `models/unsloth/deepseek-v41-1017-dynamic31-8a6ec9cf/UD-IQ1_S` |
| ComfyUI images (Qwen Image 2.1 Turbo, FLUX3 Klein, MiniMax H3 Image) | GPU-resident after loading; the MiniMax H3 text encoder (27 GB) stays in system RAM | Samsung SSD 870 QVO SATA | `models/comfy-images` |
| ComfyUI video (Wan 2.2 5B, LTX 2.3 Mesh) | GPU-resident after loading | Samsung SSD 870 QVO SATA | `models/comfy-video` |

The complete `models/engine-tests` directory is a link to
`llm-models/linux-nvidia/engine-tests` on the mounted SATA SSD. It includes the
kept dense checkpoint. Superseded trial weights and preparation inputs were
removed in the [unused-model cleanup](evidence/UNUSED-MODEL-CLEANUP-20261027.md); their
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
`lsblk`. Dense launches require SATA; SSD-streaming profiles default to
NVMe, with the per-file DeepSeek and SATA SSD Hy4 placements described above. A wrong drive, missing checkpoint or unknown transport stops startup.
The checks run before launching the selected engine; numerical, placement,
memory, thermal and process-ownership safeguards remain unchanged.

For new checkpoints, classify the engine's actual weight access before downloading:
GPU/RAM-resident weights and dense trial downloads go directly to SATA;
SSD-streamed expert/model packs go to NVMe. Use stable local aliases where needed.
Keep auxiliary packs with their parent streamed model. Avoid staging a second
resident-model weight copy on NVMe. Keep new profile metadata consistent with the
physical location and run:

```bash
python3 scripts/storage_policy.py                 # inspect every profile
python3 scripts/storage_policy.py qwen27b-hyperqwen
```

Before relocating existing weights, copy to a fresh destination, verify every file
with SHA-256, stop only the owned idle worker for cutover, verify both dense engines
can load and answer, then remove the verified source copy. Never remove a source
before the destination contents and launch paths have passed validation.

## Benchmarks and migration evidence

The [October 27 matched benchmark](evidence/BENCHMARK-20261027-101219.md) predates the storage
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

The [October 27 cleanup](evidence/UNUSED-MODEL-CLEANUP-20261027.md) removed unused model
and preparation payloads after dependency and performance review. The active
checkpoint aliases and four unique base model packages remain. Do not recreate
superseded downloads merely because a historical test references their old paths.
