# Native 2-bit Bolt with minimum tested CPU offload — November 4, 2026

The official native IQ2 Bolt text checkpoint passed on both RTX3080Ti/3080 cards at **163,840 context**, using the existing pinned llama.cpp11909. The least CPU offload that passed among the tested fit targets 256/384/512 MiB uses a **384 MiB fit target per card**: CPU-mapped weight buffers total **2.18 GiB**, with **89.4%** of native weight-buffer bytes on the GPUs. This is a qualified isolated candidate; all nine existing API/DSH entries, AWQ configuration and defaults are preserved. No engine update or automatic promotion ran.

## Same-day AWQ comparison

| Model / quant | Engine / fit target | Prefill tok/s | TTFT s | Decode tok/s | Context tokens | Storage GB | Storage location |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Bolt 74B-A9B / AWQ INT4 | vLLM CPU-offload | 217.35 | 29.320 | 0.36 | 163,840 | 55.333 | SATA SSD |
| Bolt 74B-A9B / Native IQ2; 512 MiB | llama.cpp11909 / 512 MiB | 482.97 | 13.341 | 67.88 | 163,840 | 22.018 | SATA SSD |
| Bolt 74B-A9B / Native IQ2; 384 MiB | llama.cpp11909 / 384 MiB | 506.46 | 12.744 | 67.49 | 163,840 | 22.018 | SATA SSD |

The 384 MiB native configuration gives **186.9x** the AWQ short-call decode throughput, **2.33x** prefill and **56.5% lower** client TTFT. This compares complete engine/quantization/placement configurations, not the isolated effect of bit depth. Native and AWQ first tool prompts were 6,380/6,369 tokens, with 45/41 output tokens and zero native prompt-cache reuse. Native decode timing covers a short tool-argument generation, not sustained throughput. Loading and follow-up are excluded. Client TTFT includes parser/SSE buffering. OS file caches were not dropped; this is not a cold-SATA comparison. Correct tool execution and an exact nonce follow-up passed, not a broad quality evaluation. Allocated context was preserved, not newly full-window stress-tested.

## Fit qualification and actual placement

| Fit target per card | CPU weight buffers GiB | CUDA0 / CUDA1 weight buffers MiB | Result |
| --- | ---: | --- | --- |
| 512 MiB | 2.440 | 10123.69 / 8368.61 | Tool, exact follow-up and owned unload PASS |
| 384 MiB | 2.180 | 10123.69 / 8634.88 | Tool, exact follow-up and owned unload PASS |
| 256 MiB | 1.637 | 10516.33 / 8798.11 | Rejected: GPU0 fell to 223 MiB for 3 samples during prefill |

The engine's fitter chooses a layer split and partial tensor/experts overflow while keeping the explicit context fixed. No global CPU-expert offload, drafter, projector, forced tensor split or lower context was used. The 256 MiB arm started at 257/332 MiB free, then fell below the unchanged 256 MiB independent floor during prefill and was stopped. It produced no benchmark result. The 384 MiB result is the smallest offload that passed these tested fit margins, not proof of an optimum over every possible tensor placement. CPU-mapped weights are not total process RAM: cgroup memory also includes mapped file-cache charging, runtime and buffers. Shared clean pages may have been charged outside this worker during earlier reads, so its charged-memory sample can be smaller than its CPU weight-buffer size.

## Guards and sampled resources

Both native configurations retain AWQ's **87.76984787/89.76984787 GiB** high/hard worker caps, unlimited swap occupancy, 2 GiB available-host floor, 256 MiB per-GPU free floor, 82 C stop and three bad two-second resource samples. Exact effective kernel caps are 94,242,156,544/96,389,640,192 bytes, leaving 2 GiB outside the hard cap. Active swap writes/combined remain 1/8 MiB/s over 30 s; active full PSI 10% for 3 bad samples, loading PSI 15% for 3. Native processing and deferred-request gauges are required; telemetry fails closed. Unlock and current-boot host-staged proof passed. No memory, transport or telemetry guard was relaxed.

| Passed arm | Peak charged RAM GiB | Peak swap MiB | Minimum host available GiB | Minimum nonloading GPU free MiB (0/1) | Max GPU C (0/1) |
| --- | ---: | ---: | ---: | --- | --- |
| 512 MiB | 1.39 | 0.0 | 86.36 | 621/724 | 49/38 |
| 384 MiB | 1.20 | 0.0 | 86.39 | 621/458 | 52/38 |

Samples can miss peaks. These short native calls did not fill a complete 30-second active swap window; zero sampled swap is not sustained-window qualification. The failed arm and its guard stop remain in the numeric record. The collected failed unit was verified inactive with MainPID0, its owned processes gone and both GPUs back at baseline before releasing its exact reservation. No unknown job was stopped.

## Provenance and reproduction

Official checkpoint revision`e0fecb69cb3e5e4c5e8a056fa2aec98c78e91246`, file`NVIDIA-Nemotron-3.5-Bolt-74B-A9B-24GB.gguf`,22,018,326,528 bytes, publisher SHA256`91d63363e782c8a3d5f4be42816eba8e0d42dd2530bd07a7d0d2dc440599af75`, verified after download. The file lives on SATA according to the resident-checkpoint policy. The projector is separate and was not downloaded. Native tensor types include IQ2_XXS, NVFP4, Q8_0 and F32: native 2-bit describes the trained mixed-precision model, not every tensor having two bits. [NVIDIA model card](https://huggingface.co/nvidia/NVIDIA-Nemotron-3.5-Bolt-74B-A9B-24GB-GGUF), [AWQ publisher](https://huggingface.co/cyankiwi/NVIDIA-Nemotron-3.5-Bolt-74B-A9B-AWQ-INT4).

The existing binary/source pin and ten shared-library hashes are retained in [the trial manifest](../config/bolt-iq2-trial.json). Source commit`caa8191df159f764fb0160e3d2fc6be008948aee`; runtime files were verified before loading. K/V cache types are Q8_0, batch/ubatch 256/128, threads 8, one slot, layer split, mmap with lazy mode off, reasoning off and deterministic sampling. Both GPUs use the existing host-staged transport with P2P disabled. There is no vision or speculative-decoding claim.

The reusable [coordinator](../scripts/bolt_iq2_trial.py) and [guarded worker](../scripts/bolt_iq2_worker.py) use a dedicated unit/port 10002 and exact reservation/invocation ownership, without changing the normal model hub. A local work directory needs the manifest as `pins.json` and its separately verified download receipt as `download-receipts.json`; each trial output directory must be fresh. Run only after verifying all other GPU work is idle:

```bash
python3 scripts/visible_terminal.py foreground --title 'Native IQ2 Bolt trial' -- \
  /usr/bin/python3 scripts/bolt_iq2_trial.py data/bolt-iq2-20261104 --foreground-backend
```

The explicit foreground option shares loader/worker output with the user-visible coordinator terminal. It is not a hidden fallback. An initial desktop-monitor refusal, a native token-log decoding refusal before inference, and a stale stopped transient-unit refusal were preserved. Log decoding now replaces invalid UTF-8 bytes while keeping strict ASCII context/two-GPU proof and numerical request telemetry checks; transient units are collected. These were harness/startup failures, not model throughput results. The final CPU run exposed an existing streamed-response test race: its busy assertion could run before the handler released admission. The test now waits for the actual release event with a bounded timeout; production routing is unchanged. 451 CPU regressions passed, including deferred-request protection, invalid native gauges, AWQ swap policy, fixed-context fitter constraints and non-UTF8 two-GPU proof handling.

All candidate workers finish unloaded, GPUs return to 1 MiB each, no reservation remains and API/hub/DSH stay healthy. Existing nine selected entries and engine/default settings are preserved. [Sanitized numeric results, failed arm and resources](benchmark-results/20261104-bolt-native-iq2.json); [same-day AWQ baseline](RAM96-RESTORATION-20261104.md).
