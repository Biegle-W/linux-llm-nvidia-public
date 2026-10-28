# AMD/NVIDIA repository gap audit — October 27, 2026

Read-only comparison during the NVIDIA context task. No AMD runtime, model,
schedule or repository was changed. This is a point-in-time feature audit;
concurrent AMD maintenance may advance its state. Private settings and hardware
recipes are not copied between machines.

| Area | AMD evidence | NVIDIA finding | Action |
| --- | --- | --- | --- |
| Authenticated model hub, engine selection, Tailscale and DSH | [Model hub](https://github.com/Biegle-W/linux-llm-amd/blob/fbb34eff9ea4c3eaaab7c8fd39f3ba429cb3ebe7/hardware/MODEL-HUB-2026-10-22.md) | Implemented by `network/router.py`, worker manager and DSH providers | Present on both; ports/defaults are machine specific. |
| Loading versus active swap | [AMD policy](https://github.com/Biegle-W/linux-llm-amd/blob/fbb34eff9ea4c3eaaab7c8fd39f3ba429cb3ebe7/hardware/LOADING-SWAP-POLICY-2026-10-27.md) | Existing NVIDIA 1 GiB occupancy cap did not detect repeated active swap I/O | User-approved phase-aware protection is applied to subsequent guarded launches with unlimited swap occupancy; original RAM/GPU safeguards remain. CPU/readback passed; normal GPU launch verification pending. |
| Idle resource release | [600-second watcher](https://github.com/Biegle-W/linux-llm-amd/blob/fbb34eff9ea4c3eaaab7c8fd39f3ba429cb3ebe7/dsh/inference_idle.py) | On-demand switching exists, but no equivalent idle timer | Optional: add guarded ten-minute unload, preserving requests, loading, jobs, GPU-LOCK, router, DSH and unrelated applications. |
| Lifecycle telemetry | [AMD thermal logging](https://github.com/Biegle-W/linux-llm-amd/blob/main/hardware/THERMAL-LOGGING.md) | Benchmarks record basic GPU/RAM telemetry; normal MoE launches guard temperature, but lack equivalent unified CPU/GPU clocks/fans/power lifecycle records | Optional: extend normal-launch telemetry without changing clocks, fans or temperature limits. |
| Candidate engine workflow | [AMD staged updates](https://github.com/Biegle-W/linux-llm-amd/blob/fbb34eff9ea4c3eaaab7c8fd39f3ba429cb3ebe7/hardware/daily-update/README.md) | NVIDIA uses pinned sources and manual guarded trials; no comparable reusable update/staging workflow | Optional: add manual candidate staging and acceptance reports. This does not authorize a recurring updater or resume AMD's paused updater. |
| Takeover and benchmark records | AMD current README/handoff and public thin AGENTS entry | NVIDIA's instruction entry, live state and dated evidence needed clearer linkage | Already requested: maintain thin `AGENTS.md`, current state, README, benchmark ledger and both NVIDIA repos. |
| Model/engine coverage | AMD catalog documents twelve profiles and additional llama.cpp/MoE choices | NVIDIA keeps six qualified profiles after requested cleanup | Hardware/qualification difference: 48 GB AMD VRAM versus 22 GB NVIDIA VRAM. Optional research may identify compatible additions; do not recreate retired weights or copy all profiles. |

The current user-requested swap and handoff work is authorized. The user selected operational gaps only: implement guarded ten-minute idle unload,
full lifecycle telemetry and manual candidate staging after context rollout. No
model-coverage expansion is authorized; preserve the current six profiles.
Measured speeds and context qualifications remain local to their hardware,
runtime, quantization and workload. More catalog entries alone do not establish
a better setup.

AMD's swap monitor documents system-wide counter attribution limits. The NVIDIA
kernel exposes owned-cgroup `pswpin`/`pswpout`, allowing the new guard to observe
its worker specifically. Porting that improvement back to AMD would first require
checking its actual kernel counters and existing concurrent agent changes.

## Continuation deployment

The user directs unchanged swappiness 60; the earlier VM10 proposal was cancelled
before execution. Guarded 600-second idle release, native adapters and bounded
lifecycle logging are deployed; normal functional and actual idle/reload checks
are pending. Four qualified contexts were promoted independently. Maya DeepSeek
sustained-swap qualification remains unresolved, with guards and 32K unchanged.
Manual candidate staging remains manual. CURRENT-STATE.md is authoritative.
