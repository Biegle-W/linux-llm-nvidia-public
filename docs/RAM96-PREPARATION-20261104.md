# Larger-RAM restoration preparation — November 4, 2026

**Superseded after reboot:** unlock/transport passed and all nine larger-RAM profiles passed their requested tool/follow-up/unload checks. The user subsequently selected exact 2 GiB hard-limit headroom (87.76984787/89.76984787 GiB); 446 CPU checks passed. [Current restoration and results](RAM96-RESTORATION-20261104.md). The preparation and firmware blocker below are retained as dated history.

Linux now reports **96,227,652 KiB / 91.77 GiB usable RAM**, consistent with a96 GB-class installation. This is measured MemTotal, not merely an increase in free RAM. DIMM sizes/speed were not read because administrative DMI access requires authentication; no memory-frequency, timing or voltage claim is made.

The human requested restoration, larger RAM caches, forum research and benchmarks for all nine profiles, then explicitly chose **prepare the settings first; reboot later** after the firmware issue was identified. Preparation and 445 CPU tests are complete. **No GPU benchmark or restored-profile qualification has run on this installation.** Five paused profiles remain paused. Four previously enabled entries remain in the catalog, but every model start still requires the existing boot proofs.

## Prepared settings

Private preimages preserve the previous32 GB configuration and saved pre-migration64 GB policy. The larger choices below are candidates for guarded qualification, not measured optima. Contexts, quantizations, model files, runtime hash pins, GPU placement, sampling and default model selections are unchanged.

| Profile | Worker RAM high/max GiB | Prepared RAM/cache setting | Context tokens |
| --- | ---: | --- | ---: |
| HyperQwen | 32/36 | GPU-only inference; larger bounded loading/file-cache headroom; no new CPU weight offload | 86,016 |
| SGLang | 32/36 | GPU-only inference; larger bounded loading/file-cache headroom; no MTP increase | 57,344 |
| TensorFold Qwen27B | 32/36 | Same EXL3 target,4-bit DFlash2/copies and native host-mapped embeddings | 12,288 |
| Flash-Next IQ1_S / llama.cpp | 84/86 | Same lazy NVMe n-gram mapping; room for a larger OS file cache without forcing the whole table to be pinned | 12,288 |
| Flash-Next IQ3 / Strata — paused | 84/86 | Saved resident non-GPU-cache-complement mode restored in its config | 131,072 |
| GLM/Maya — paused | 84/86 | Native expert RAM tier cap64 decimal GB, previously16; saved64 GB-machine cap was40 | 65,536 |
| DeepSeek/Maya — paused | 84/86 | File-cache target64 GiB; startup warm cap56 decimal GB; decode warm8 decimal GB | 32,768 |
| Bolt — paused | 84/86 | Larger CPU-offload/loading headroom; retained previously qualified unpinned prefetch adapter | 163,840 |
| DeepSeek/Strata — paused | 84/86 | Bounded CPU expert store64 decimal GB, previously16; saved full-RAM value was36 | 32,768 |

84/86 GiB leaves about 5.77 GiB outside the hard worker limit on this boot. The independent **2 GiB host-available floor** remains. The three dense profiles do not need an84 GiB allowance: their weights execute on the GPU and their current context/drafter limits are VRAM-bound. Giving them all available RAM would not establish a larger usable context. A new measured-capacity gate requires **at least90 GiB Linux MemTotal** before these96 GB-class settings can start, independently of MemAvailable. Returning to 32/64 GB cannot silently retain these larger settings.

Other guards remain: 256 MiB per-card free-VRAM floor where enforced, existing native reserves/fit targets,82 C, existing two-second resource checks and three-sample hysteresis, unlimited swap occupancy with bounded active I/O/PSI windows, authenticated loopback backends, exact worker ownership, current-boot transport proof, swappiness60, parallel1 and idle600. Per-profile swap limits and pressure exceptions were not changed. Daily engine updates remain paused.

## Forum research and pinning decisions

- Community measurements disagree with blanket advice to enable resident mode. One same-quant comparison reported faster prefill but slower decode and greater pinned RAM in resident mode. That is a hardware/version-specific observation, not a transferable speedup. The saved locally qualified Flash-Next resident-complement configuration is the starting point now that more RAM is available. [Community discussion](https://www.reddit.com/r/LocalLLM/comments/1x5i1cc/qwen38_flash_next_low_quant_vs_27b_q5_is_strata/).
- Strata reports explain why a limited resident budget may leave prompt-lent slots backed by disk; a separate older AMD report describes resident-pool plus mapped-page duplication. These justify bounded allocation and actual load telemetry rather than disabling safeguards or pinning every file. Neither report proves the same behavior on this pinned NVIDIA build. [Lend-region report](https://github.com/Niko1221/Strata/issues/1683), [duplication report](https://github.com/Niko1221/Strata/issues/3734).
- Maya documents a fixed native RAM-tier cap and retained system headroom. Its newer DeepSeek pin/copy knobs are version-dependent. No support was found for the proposed newer `DS4_LENT_RAM_GB`/copy-pin controls in the pinned local file-cache binary, so those flags were not blindly enabled and no engine upgrade was performed. GLM uses its engine-managed pinned tier; DeepSeek/Maya retains the already qualified bounded cache controller with larger budgets. [Maya settings](https://github.com/mw00/project-maya/blob/main/docs/SETTINGS.md).
- Bolt's earlier pinned-host experiment failed under the 64 GB setup. More capacity makes a future bounded comparison plausible, but does not establish safety or benefit. The prepared restoration preserves its existing unpinned setting rather than selecting that failed arm without a new test. Global `--mlock`, swap disabling, arbitrary CPU affinity, BIOS/XMP changes and huge-page reservation were not added.

The choices use supported controls in existing pinned runtimes. They are research-informed candidates; no external tok/s figure or claimed universal best setting is imported into this server's benchmark history.

## Firmware blocker and continuation

This boot reports **Secure Boot enabled** and kernel integrity lockdown. `gpu-unlock-health` fails with missing successful pre-NVIDIA unlock evidence. The required root-owned transport-proof file is absent because its service depends on successful unlock health. These guards were not bypassed; drivers were not unloaded and no synthetic proof was written.

When the human is ready: disable Secure Boot in UEFI again and reboot into the same Linux installation. First verify early unlock and current-boot host-staged transport, then measured RAM capacity and idle worker/admission state. The prepared continuation will requalify all nine serially through the normal router: guarded load, one actual short DSH read, matching executed result, exact follow-up, timing/resource capture and owned unload. Previously paused entries are admitted individually for qualification; a failed new profile remains disabled. No fallback preload, full-context stress or automatic polling/reboot schedule is configured.

The complete CPU run passed **445 tests**, including the new installed-capacity gate and 64 GB bounded expert-store support. An initial CPU run exposed an asynchronous test race: receiving the last HTTP response byte can precede the handler's admission-release finally block. The test now waits for the actual release event with a bounded timeout; production admission/response ordering was not weakened. No model speed test was retried or fabricated.

The idle model hub was refreshed to load the prepared budget validator; API/hub/DSH are healthy and no GPU worker or reservation is active. Existing benchmark reports remain dated32/64 GB evidence. Fresh larger-RAM benchmark tables and full restoration are **pending the corrected boot and guarded GPU qualification**.
