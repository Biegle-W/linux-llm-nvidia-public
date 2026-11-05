# Engine refresh and weight sharing — November 5, 2026

Subsequent November5 selection: [IQ1_M /Strata replaces IQ1_S /llama.cpp](FLASH-IQ1M-STRATA-20261105.md). The earlier refresh/audit below is historical. The retired IQ1_S files were subsequently deleted by explicit request, reclaiming37.58GB exclusive body/metadata while preserving the active IQ1_M28.8GB table. [Deletion receipt](IQ1S-WEIGHT-REMOVAL-20261105.md).

Removed the single abandoned Qwen `.incomplete` download: **3,418,357,760 bytes (3.418 GB)**. Its identity, link count and absence of open owners were checked before removal. No completed checkpoint was deleted and no new model weights were downloaded.

## Selected versions

“Latest” here means the latest stable release, or the current default branch for maintained forks without a stable release, checked November 5. Experimental/nightly releases are excluded. Dependency versions follow each engine's compatible pins; packages were not indiscriminately upgraded across environments.

| Engine | Selected version | Result |
| --- | --- | --- |
| [HyperQwen](https://github.com/syv-ai/HyperQwen) | `6ab9bd05cb84`, vLLM 0.32.0, Torch 2.13.0 | Updated; local INT4 KV patches retained |
| [Heterogeneous SGLang](https://github.com/efschu/htsglang) | `d61ded5b9e2d`, default `fix/851-consolidated` | Updated; group128 embedding, W4A8/MTP patches retained |
| [Maya](https://github.com/mw00/project-maya/releases/tag/v1.1.53) | 1.1.53, `7c4aa56ed7fa` | Both GLM and DeepSeek updated; bounded file cache retained |
| [Strata](https://github.com/Niko1221/Strata/releases/tag/v0.2.10) | app 0.2.10, control and engines 0.1.56 | Both Qwen and DeepSeek updated; signed package manifests verified |
| [llama.cpp](https://github.com/ggml-org/llama.cpp/releases/tag/v0.9.0) | stable v0.9.0, `cd959bae99ff` | Shared Bolt/Flash runtime updated |
| [TensorFold](https://github.com/ashhart/TensorFold/releases/tag/v1.2.2) | 1.2.2 | Already latest stable; unchanged |
| [ComfyUI](https://github.com/Comfy-Org/ComfyUI/releases/tag/v0.44.0) | 0.44.0 | Already latest stable; unchanged |
| [Raylight](https://github.com/komikndr/raylight/releases/tag/1.11.0) | 1.11.0 | Already latest stable; unchanged |
| [ComfyUI Mesh](https://github.com/shootthesound/comfyui-mesh) | `3804156b4b39` | Already current default-branch head |
| [ComfyUI GGUF](https://github.com/city96/ComfyUI-GGUF) | `6ea2651e7df6` | Already current default-branch head |

Native builds target SM86 and use matching CUDA 13.0.88 headers/runtime/cuBLAS, without changing the driver or kernel. Failed relocation and mixed CUDA12-library candidates were rolled back; the selected shared libraries resolve correctly. Existing compatibility directory names may contain older version numbers; manifests above identify their actual contents.

## Validation and fixes

All **eight changed text entries** passed normal-router actual DSH read/tool-result/exact follow-up, retained resource guards and owned unload. **469 CPU regressions passed**. Contexts, weights, cache choices and launch defaults remain selected. The unchanged TensorFold and diffusion engines were not rerun. There was no full-context, sustained-generation or timed-idle suite. Daily automatic updates remain paused; this manual refresh does not qualify the older unattended update pipeline for resumption.

The public reference has no installed private runtimes. Its full discovery ran451 tests with12 missing-runtime errors and4 skips (Maya/Strata control sources and the private xterm binary are intentionally absent). All39 public runtime-integrity checks and5 public sample/privacy checks passed. The469-test installed-project suite above passed in full. This is an export portability limitation, not a failed live model check.

SGLang metadata readiness preceded its native startup warmup. The short harness now waits for that warmup before taking counter baselines. The new upstream HTTP startup imported Prometheus before its multiprocess directory existed, hiding tokenizer timing counters. The patch initializes its startup timer after the engine establishes that directory. A corrected short call returned native prefill, TTFT and inter-token counters; earlier incomplete captures are excluded from the current table.

The newer Maya idle loop honors managed600-second deadlines while preserving upstream behavior outside managed launches. Request-scoped CPU vision-encoder cleanup is retained; current text profiles still disable vision. Independent transaction journals now refuse an existing preimage slot instead of overwriting rollback evidence. Private preimages and failed-candidate evidence are retained.

[Current nine-entry observations and per-profile guard table](ALL-ENTRY-BENCHMARKS-20261105.md); [sanitized versions, metrics and audit receipt](validation-results/20261105-engine-refresh.json).

## Shared weights and deletion suggestions

The managed-store audit found **45 physical large weight files and zero byte-identical duplicate groups**. It deduplicated inode aliases and fully hashed same-size files on distinct inodes. This covers completed GGUF/safetensors/bin weights of at least100MB, not every small support file on every disk.

| Model/assets | Current sharing | Cleanup implication |
| --- | --- | --- |
| Qwen27B AutoRound,15.792GB | HyperQwen and SGLang read the same checkpoint | Already shared; retain |
| Qwen27B EXL3 target9.673GB +DFlash2 drafter3.849GB | TensorFold uses a different format/quant and a separate draft model | AutoRound cannot replace these selected TensorFold weights |
| DeepSeek UD-IQ1_S,232.980GB | Maya and Strata share all five checkpoint shards | Already shared; retain |
| DeepSeek last shard,110.595GB | Project path aliases its SATA allocation | Symlink, not another110.595GB copy; deleting the target breaks both engines |
| Flash-Next IQ1_S66.379GB /IQ3_XXS75.840GB | Different quants, each selected by an entry | Optional retirement of one entry, not duplicate-file cleanup |
| Wan native /Raylight | Same checkpoint, encoder and VAE | Already shared; retain |
| ComfyUI Qwen/FLUX/LTX encoders and VAEs | Model-specific architectures and representations | Similar names do not make them interchangeable |

**Historical cleanup suggestion, superseded by the IQ1_M replacement and verified deletion above: Flash-Next IQ1_S, originally66.379GB**, if retaining only the faster selected IQ3_XXS Strata entry is preferable. This would remove the IQ1_S llama.cpp option and its lower-bit alternative. Current single short observations are120.73/36.86tok/s prefill/decode forIQ1_S versus943.8/58.8 forIQ3_XXS; contexts and precision differ. No complete weights were removed without that retirement decision. Conversely, retiring IQ3_XXS saves75.840GB but loses the faster128K option. Do not delete both or a shared checkpoint simply because two engines name it.
