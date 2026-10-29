# Qwen/Strata host-RAM reserve lowered to 2 GiB — October 28, 2026

**The approved Qwen host reserve is now 2 GiB. The lcz.me model setup failed the
retest and was not applied.** These are separate decisions: the human explicitly
lowered the guard reserve, while retaining application only after qualification
for the pageable cache/execution setup. Other five profiles retain 8 GiB.

## Selected guard change

`flash-next-strata` now selects `host_ram_reserve_gib=2` in the maintained registry.
The normal MoE supervisor reads the selected floor at each worker launch. Its
three-consecutive-low-reading stop, 82 C temperature stop and existing owned-worker
swap/pressure/telemetry checks remain. The catalog accepts 2 GiB only for this
Qwen/Strata profile; other profiles keep the 8 GiB default. Router and DSH needed
no restart. No other guard was lowered.

Eight new CPU checks exercised the 2 GiB boundary, 3 GiB versus the old 8 GiB floor,
invalid/out-of-scope settings and retained thermal/swap stops. Eighteen existing
worker-budget, swap-guard and MoE supervisor checks also passed: **26 total**.
The pre-change sources and registry were hash-verified and archived privately at
`728965791d824d4a6eb58901ec8bb9fe5bf6ec96` before selection. Credentials were not archived.

## Isolated reduced-RAM retest

The machine still has 45.55 GiB usable RAM. The candidate retained the lcz.me
pageable settings: fixed prefill 4096, seven CPU workers, adaptation and PCIe
sharing off, conversation cache off, native VRAM reserve 1536 MiB, INT8 KV,
MTP and images. Context stayed 32768 and idle unload 600 seconds. Swappiness 60,
44/48 GiB worker RAM limits, unlimited swap occupancy and unchanged active swap
protection remained. It ran serially in a minimized visible terminal.

Native residency used `STRATA_RESIDENT_HEADROOM_GIB=2` and
`STRATA_RESIDENT_PIN=0` through `--resident-experts`, alongside
`--mmap-experts --resident-cpu-experts`. The former switch exposes the runtime's
headroom override without rebuilding it. The test required full residency and
rejected partial-residency fallback. The engine confirmed **35.38 GiB
pageable, 0.00 GiB pinned**, with adaptive expert swaps off. The isolated host
monitor also used the explicitly approved 2 GiB floor. This is a new candidate,
not a fresh paired single-variable control against the previous 8 GiB run.

Loading and the warm-up passed. Three matched fixed-input requests, 128 output
tokens each, completed before qualification failed. Their screen medians were
437.4 prefill tok/s, 5.078 seconds TTFT and
53.29 client decode tok/s, with approximately 2.2K input.
Prefill uses native timing; TTFT and decode use client SSE timing under the same
saved fixture method. These are **rejected-candidate screen results**, not a
qualified operating speed or a replacement for the selected historical benchmark.
No fresh full-RAM paired control was run.

During quality checks the unchanged owned-worker swap guard stopped inference:

| Stopping window | Swap reads | Swap writes | Combined |
| ---: | ---: | ---: | ---: |
| 30.46 s | 76.90 MiB/s | 18.81 MiB/s | 95.71 MiB/s |

Sampled minimum host available was 3.39 GiB,
peak worker cgroup memory 41.58 GiB, peak worker swap
4.45 GiB and maximum GPU temperature
53 C. Cgroup memory includes file cache;
sampled minima and peaks do not establish instantaneous extremes. Lower headroom
allowed this candidate to load but did not eliminate active swap I/O.

Near-window retrieval, sustained generation, fresh-process reload and normal-route
setup validation were not reached. The required quality/resource protocol did not
pass, so no lcz.me model/cache/execution settings were promoted. The canonical
native launch file and current benchmark fields are unchanged. Adaptive expert
cache exchanges and operating-system swapping are separate mechanisms.

## Final state and next action

The owned test worker is stopped, GPU reservation released, router idle and DSH
ownership preserved. No fallback was restored. The normal Qwen host floor is now
2 GiB on its next launch; this guard selection does not make the existing Qwen
model configuration qualified on reduced RAM. Other profiles retain 8 GiB, and
the earlier temporary GLM/Strata DeepSeek cache choices remain untouched.

The missing DIMM is temporary. After explicit human restoration confirmation,
verify Linux capacity, restore appropriate full-RAM cache values and verify normal
guarded loading. Preserve the separately approved reserve selection, unrelated
router/Desktop changes, credentials and independent benchmark history unless the
human changes that direction. No timer or MemAvailable trigger.

[Numeric evidence](benchmark-results/20261028-qwen-host-reserve2.json).
[Previous 8 GiB pageable tests](QWEN-STRATA-LCZ-20261028.md).
[All six maintained result rows](MAINTAINED-PROFILES.md).
Raw credentials, telemetry and session/ownership state remain private.
