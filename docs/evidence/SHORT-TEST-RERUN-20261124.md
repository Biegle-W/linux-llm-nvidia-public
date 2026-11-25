# Short tool-use test: rerun of every enabled route (November 24-25, 2026)

Owner's request: rerun the short tool-use test on every route that is set up. All ten enabled routes ran live through the router (`http://127.0.0.1:10100`), one at a time, with `quality/fast/fast.sh` and the same tier as their earlier run (smaller: 15-minute limit; larger: 1-hour limit). Before each route the driver checked `gpu-unlock-health` (VERIFIED) and that `data/GPU-LOCK` was absent; after each it checked the GPUs and unloaded the router. Run IDs `rerun-20261124` and `rerun-20261124-hy4maya` (item data not committed).

## Results (score on the 49 common items)

| Route | Tier | Score | 95% interval | Single turn | Parallel | No tool fits | Plain | Episodes (9) | Larger tier (15 episodes) | Item time (min) | Load (s) | Earlier score |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | --- |
| `deepseek-maya` | larger | 70.3 | 53.1–87.4 | 34/40 | 13/15 | 12/15 | 9/10 | 5/9 | 7/15 | 46.9 | 25 | 63.5 (stored answers of 2026-11-12) |
| `deepseek-unsloth-strata` | larger | 67.8 | 50.4–85.2 | 32/40 | 13/15 | 10/15 | 9/10 | 5/9 | 7/15 | 45.3 | 22 | 64.7 (stored answers of 2026-11-11) |
| `qwen27b-sglang` | smaller | 67.2 | 50.3–84.1 | 36/40 | 13/15 | 14/15 | 9/10 | 4/9 | not run (smaller tier) | 10.1 | 23 | 61.7 (stored answers of 2026-11-12) |
| `qwen27b-hyperqwen` | smaller | 66.0 | 49.0–83.0 | 35/40 | 12/15 | 13/15 | 10/10 | 4/9 | not run (smaller tier) | 8.5 | 75 | 66.0 (stored answers of 2026-11-10) |
| `hy4-flash-strata` | larger | 58.5 | 40.8–76.1 | 29/40 | 9/15 | 13/15 | 7/10 | 4/9 | 6/15 | 41.6 | 119 | 57.9 (2026-11-22) |
| `glm-maya` | larger | 49.3 | 37.8–60.8 | 35/40 | 13/15 | 12/15 | 10/10 | 1/9 | 4/15 | 21.2 | 38 | 60.4 (stored answers of 2026-11-11) |
| `hy4-flash-maya` | larger | 48.1 | 36.4–59.7 | 34/40 | 12/15 | 14/15 | 8/10 | 1/9 | 2/15 | 36.1 | 260 | 45.6 (2026-11-23, stopped by the memory-pressure guard at minute 30) |
| `inkling-strata` | smaller | 47.5 | 44.1–50.9 | 38/40 | 15/15 | 14/15 | 9/10 | 0/9 | not run (smaller tier) | 7.5 | 11 | 59.3 (2026-11-24, cut with 7 of 9 episodes reached) |
| `kolibri-llamacpp` | smaller | 41.8 | 29.4–54.2 | 29/40 | 5/15 | 14/15 | 10/10 | 1/9 | not run (smaller tier) | 7.3 | 138 | 41.8 (2026-11-24, trial server) |
| `flash-next-strata` | smaller | 40.6 | 28.1–53.0 | 28/40 | 9/15 | 10/15 | 9/10 | 1/9 | not run (smaller tier) | 4.9 | 37 | 40.6 (stored answers of 2026-11-10) |

Every route completed: all 40 single-turn items and all 9 core episodes scored, no item timeouts.

## Notes

- **Changes from the earlier scores are mostly in the 9 episodes.** Single-turn counts moved by at most 4 items; episode counts moved by up to 2 of 9 (22 points of the score each way). That is the run-to-run spread the ±17-point interval describes.
- **Identical reruns.** `qwen27b-hyperqwen`, `flash-next-strata` and `kolibri-llamacpp` gave the same totals as before (single-turn and episodes); for `flash-next-strata` the single-turn mix changed (parallel 11 to 9, no tool fits 9 to 10, plain 8 to 9).
- **`inkling-strata` 0 of 9 episodes.** Every episode finished in 23-56 s with an ordinary wrong end state (for example a wrong fuel level or a missed email); no errors or timeouts. The earlier run passed 2 of the 7 it reached before its 15-minute cut. With 0 of 9 the normal approximation gives the episode part no spread, so its interval is too narrow.
- **`hy4-flash-maya` load cap.** Its first attempt stopped at the runner's 3-minute load cap (setup failure, no items run): the route takes about 6.5 minutes to load from SATA. It was rerun with `--load-cap 600`; load time is not part of the score. Its run on November 23 was stopped by the memory-pressure guard at minute 30; this one completed.
- **Router unload.** After each route the model was still loaded 20 s after the run; the driver's explicit unload cleared both GPUs (1 MiB each) before the next route.

The ranking in [WEBSITE-SUMMARY.md](../WEBSITE-SUMMARY.md), the README and CURRENT-STATE now uses these runs, best route per model.
