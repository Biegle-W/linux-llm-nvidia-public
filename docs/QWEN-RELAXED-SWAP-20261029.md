# Qwen mapped experts with bounded swap allowance — October 29, 2026

Selected reduced-RAM configuration: original IQ3_XXS, 32,768 context, both GPUs [0,1], automatic layer split and plain `--mmap-experts`. Qwen alone permits 128 MiB/s swap writes and 160 MiB/s combined swap reads/writes over the existing 30-second window. Every other model retains 1 MiB/s writes and 8 MiB/s combined.

The 10% full-memory-pressure stop, missing/counter-discontinuous telemetry handling, 2 GiB host floor, 44/48 GiB cgroup limits, native VRAM policy, 82°C temperature guard, swappiness 60, concurrency one and idle 600 seconds remain unchanged. Swap occupancy remains allowed under the existing host capacity; active I/O remains bounded.

## Qualification

- Twelve swap-policy unit tests passed, including Qwen-only scope, rate limits and retained pressure enforcement.
- JSON, arithmetic, image and uncached 29,450-token retrieval passed under the selected swap policy. The following numbered response completed 2,542 output tokens over 43.72 seconds with no guard violation; it ended naturally before the harness's 90-second target. That trial peaked at 48.41 MiB/s writes.
- A separate fresh process with a long-prose prompt completed 8,192 output tokens over 139.52 seconds of continuous generation: 58.71 client decode tokens/s. This workload-specific measurement does not replace the historical three-request benchmark.
- The extended trial peaked at 12.02 MiB/s swap writes, 0.066 MiB/s reads and 0.388 GiB worker swap occupancy. Minimum host available RAM was 35.74 GiB; peak GPU temperature 66°C. No cgroup high/max/OOM events or guard violation occurred.
- A distinct fresh-process reload passed JSON arithmetic. Both workers were unloaded and the router returned idle; router and DSH services were preserved.

Earlier 32 and 64 MiB/s write allowances stopped at 34.40 and 64.49 MiB/s. Different cache/reclaim histories mean these runs do not establish a deterministic minimum threshold. This policy tolerates substantially more swap I/O, which can increase latency and storage traffic. The bounded qualification does not establish multi-hour reliability.

The selected canonical preset now retains mapped experts and the Qwen-specific policy. Historical full-RAM benchmarks and all other model settings remain unchanged. This remains a temporary reduced-RAM configuration; full-RAM cache restoration requires explicit confirmation of restored hardware and capacity verification.
