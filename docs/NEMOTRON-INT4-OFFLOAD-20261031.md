# Nemotron INT4 offload startup checks — October 31, 2026

Neither candidate reached inference on the tested installed engines and guarded configurations. No quality pass, tokens-per-second result, or production selection is established. CPU offload is possible in principle; these failures concern the selected checkpoints, loader behavior, parallel layout and bounded memory allocation, rather than weight size alone.

## Test boundary

Hardware: restored 64 GB RAM (61.3013 GiB usable), 3080 Ti 12 GiB and 3080 10 GiB used for TP2; the motherboard 3060 12 GiB and unrelated desktop processes were preserved. Installed vLLM 0.31.0 and the pinned SGLang heterogeneous source at `62271fd7c8aa8fe9edebf04e00a414b7fbf64388` were used. Context 2,048, concurrency one, eager execution, no speculative draft. vLLM initialization was text-only.

The trial worker hard cap remained 48 GiB. Soft thresholds were 44 GiB, then one 46 GiB trial, within the existing budget validator's high <= max - 2 and max <= 48 bounds. Host reserve 2 GiB, GPU reserve 512 MiB, temperature 82 C and swappiness 60 were retained. Active swap thresholds stayed 1 MiB/s writes / 8 MiB/s combined over 30 seconds, with the default 10% active pressure threshold. A separate conservative trial loading stop used full-memory PSI avg10 above 15% on three readings. Loading failures are not active-inference swap failures.

## Bolt 74B-A9B AWQ INT4

Checkpoint: [cyankiwi AWQ INT4](https://huggingface.co/cyankiwi/NVIDIA-Nemotron-3.5-Bolt-74B-A9B-AWQ-INT4), revision `3df8bd99af5d58abe5f052ef81127dff092f26b4`; 55,332,700,488 weight bytes. All checkpoint files were downloaded to SATA using the Hub client; sizes were checked against pinned metadata. No separate full-file SHA pass was performed.

The installed vLLM configuration resolves the native Nemotron class. Unmodified quantization metadata first fails the fused-MoE same-scheme check: its regex names up/down projections, while the helper also inspects an unused gate projection. A launch-only mapping adding that virtual gate name cleared the check and selected Marlin INT4 kernels. Original checkpoint files and engine source were unchanged.

Real-weight startup attempts with 17.5 and 16 GiB CPU offload per rank at the 44 GiB soft threshold stopped under loading pressure. A 16 GiB/rank trial with the 46 GiB soft threshold advanced further, logged 16.03 GiB offloaded for one rank, and then hit the GPU reserve guard. The 10 GiB GPU had only 33 MiB free in the failing sample, while the host still had about 8.87 GiB available. There was no readiness or generated reply. This brackets a RAM/VRAM loading problem in the tested generic offloader; it is not a proof that every offload engine or configuration is impossible.

Local safetensors headers account for 35.614 GiB routed-expert storage, 14.335 GiB other language weights, and 1.569 GiB vision/other weights. Non-expert replication matters when considering data/expert parallel alternatives.

SGLang's registry selected its generic Transformers fallback. Actual startup failed because the remote model requires `mamba-ssm`, which could not be imported. A successful native or fallback SGLang implementation was not established.

## Super VL 120B-A12B mixed INT4

Checkpoint: [halt95 Merlin W4A16](https://huggingface.co/halt95/Nemotron-3.5-Super-VL-120B-A12B-W4A16-Merlin), revision `835d4cc7c9cc95f6dff9b1e4db2d5c520e847148`; 72,888,191,872 weight bytes. This is mixed INT4/INT8/BF16, not uniformly INT4. The full checkpoint was not downloaded; these were metadata and dummy-weight initialization gates, not real-weight inference or speed tests. Resumable partial data was retained.

vLLM TP2 initialization rejected 1,344-wide local MoE partitions against 128-wide quantization groups. Enabling expert parallelism cleared that alignment check and selected Marlin; initialization then reached sustained loading pressure within the 44/48 GiB budget and was stopped before readiness. The checkpoint author's Merlin fork was researched, but was not installed or tested here.

Actual SGLang startup explicitly rejected the model: no native SGLang implementation, and the Transformers implementation is incompatible with SGLang. Further large weight downloads cannot by themselves resolve that loader rejection.

## Parallelism, harness and disposition

Installed native vLLM rejects pipeline parallelism for this model class. Ordinary TP3 cannot divide 32 attention heads. DP3 plus expert parallelism was considered, not run; replication of non-expert weights prevents treating the 34 GiB total as a single freely pooled device.

The initial in-cgroup watcher stalled behind memory.high throttling. It was moved outside the bounded worker for subsequent attempts, with bounded unit shutdown and owned-only forced cleanup after a guard stop. Console windows launched, but the window manager did not acknowledge foreground activation; no foreground-verification pass is claimed.

All owned workers and downloads are stopped and the GPU reservation is released. Existing Qwen profiles, maintained runtime pins, hardware setup, router/DSH and unrelated jobs were preserved. No profile was promoted. The next substantive step requires an isolated compatible loader/runtime with a lower-overhead expert-offload path; do not repeat these stopped settings for a passing result.

Machine-readable evidence: [startup outcomes](validation-results/20261031-nemotron-int4-offload.json). Private raw logs, model Python review copies and trial harnesses are retained locally, outside the public export.
