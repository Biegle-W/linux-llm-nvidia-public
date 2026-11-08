# Qwen/Strata lcz.me setup on reduced RAM — October 28, 2026

**Failed qualification; not applied.** Two isolated candidates tested the pageable
expert-RAM configuration from [the lcz.me 48 GB setup](https://lcz.me/topic/2042)
on the current 45.55 GiB usable NVIDIA machine. The canonical Qwen launch config,
maintained registry and all guard/router/policy source hashes are unchanged.

This follow-up tests settings absent from the previous 17-attempt study; it does
not repeat or relabel those measurements. The forum used a single RX 7900 XTX,
Strata v0.1.34 and different expert placement. Here the existing dual RTX 3080 Ti
12 GB / RTX 3080 10 GB CUDA engine 0.1.50, IQ3_XXS weights, MTP and INT8 KV remain.
The forum result is a setup lead, not a performance control for this hardware.

## Settings tested

Both candidates used these settings, with existing model/pack/MTP paths:

```text
--max-context 32768 --kv int8 --prefill 4096
--pool-workers 7 --spec 4 --spec-min-p 0.5
--expert-cache auto --adapt-every 0 --pcie-frac 0
--vram-reserve-mib 1536 --conversation-cache-mib 0
--mmap-experts --resident-cpu-experts --vision
STRATA_RESIDENT_PIN=0
```

The deployed 32K context and 600-second idle unload were retained. AMD-specific
HIP switches and the forum's disabled idle timer were not copied. The explicit
1,536 MiB native VRAM reserve exceeds the previous 700 MiB default. No GPU reserve
was lowered. Dense reserve remains 512 MiB. Swappiness 60, host available 8 GiB,
temperature 82 C, 44/48 GiB worker RAM limits, unlimited swap occupancy and the
unchanged owned-worker churn/pressure/telemetry stops remained in force. Tests
ran serially in minimized visible terminals with isolated ownership.

## Results

| Candidate | Result | Application |
| --- | --- | --- |
| Full pageable resident CPU experts | Native startup refusal: 31.88 GiB complement exceeded 38.51 GiB available minus 8 GiB headroom (30.51 GiB) | Not applied |
| Pageable 28 GiB resident budget | Loaded; warm-up and one measured request completed; active swap-churn guard stopped inference | Not applied |

The second candidate additionally used `--resident-budget-gib 28` and
`STRATA_RESIDENT_HEADROOM_GIB=8`. The explicit headroom preserves the full-resident
mode's native safety allowance. Its engine log confirmed 28.00 GiB pageable,
0.00 GiB pinned, prefill 4096 and adaptive expert swaps off. Adaptive expert-cache
exchanges and operating-system swap I/O are separate: disabling the former did
not prevent the latter.

The stopping window observed **92.35 MiB/s owned-worker swap reads**,
0.00 MiB/s writes over 30.43 seconds. Sampled minimum
host available was 9.76 GiB; peak worker cgroup
memory was 40.90 GiB, peak worker swap
4.57 GiB, and maximum sampled GPU temperature
52 C. These samples do not establish instantaneous
extremes. Cgroup memory includes file cache.

The planned protocol required one warm-up, three matched 128-output-token
benchmark requests, JSON/arithmetic/image checks, near-window retrieval, at least
90 seconds of continuous generation, a fresh-process reload and normal guarded
routing before acceptance. Neither candidate completed it. The 28 GiB screen's
single measured request is retained in the numeric evidence; it is not a median,
a reliable operating speed or a qualified performance-loss percentage. Quality,
sustained generation and reload checks were not reached. Normal-route validation
and promotion were not attempted after isolated qualification failed.

## Final state and restoration policy

The owned test worker is stopped, GPU reservation released, router idle and DSH
ownership unchanged. No fallback model was restored. Qwen remains unqualified on
reduced RAM; the previously deployed temporary GLM and Strata DeepSeek cache
choices are untouched. All six maintained profiles and previous benchmark history
remain. No new engine/runtime, quantization, context or production config change
was applied.

The missing DIMM remains temporary. Restore appropriate full-RAM cache values
only after explicit human confirmation plus Linux capacity verification, then
verify normal guarded loading and update selected metadata. Preserve unrelated
router/Desktop changes, credentials and benchmark attribution. MemAvailable and
timers never trigger restoration.

[Machine-readable evidence](benchmark-results/20261028-qwen-strata-lcz.json).
[Prior reduced-RAM study and all six maintained result rows](REDUCED-RAM-20261028.md).
Raw configs, credentials, telemetry and ownership/session data remain private.
