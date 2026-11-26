# Strata 0.2.22 installed by hand — November 26, 2026

Strata was updated from v0.2.21 to v0.2.22 (`b28ca95e3e68`, signed feed sequence 136) in the hands-on update run that started on November 25. The install waited for a reboot: an unattended Ubuntu update installed kernel 7.0.0-44 at 18:26 on November 25, which left the GPU unlock check at "PENDING REBOOT VERIFICATION". The owner rebooted the server; the unlock check read VERIFIED on 7.0.0-44 before any GPU work.

| Component | From | To | Result |
|---|---|---|---|
| Control (serves every Strata entry) | 0.1.67 | 0.1.69 | **promoted**; the local idle-reservation patch applies to the new `server.py` |
| `strata-inkling` (`inkling-strata`) | 0.1.67 | 0.1.69 (`a5bfe0369bfb`) | **promoted** |
| `strata-hy4` (`hy4-flash-strata`) | 0.1.67 | unchanged | the release ships the same Hy4 engine 0.1.67; passes under control 0.1.69 |
| Qwen engine (`flash-next-strata`) | 0.1.65 | 0.1.69 tried, **kept at 0.1.65** | 0.1.69 generates 13-17% slower on two runs, as 0.1.66 and 0.1.67 did |
| DeepSeek on Strata | v0.2.13 | unchanged | frozen; passes under control 0.1.69 |

## Review before the install

Release notes and the commits v0.2.21..v0.2.22 were read first. What applies here:

- **Inkling 2 Mini (`inkling-strata`):** with the model split across two cards, a peer card's expert budget was read from the wrong card (#7093, fixed in `strata-inkling` 0.1.69). In control's server, a request that sends no sampling settings now gets the model card's temperature 1.0 instead of greedy decoding (#7092), and thinking budgets are capped (#7133). The router passes sampling settings through unchanged, so web-client requests that send none now sample at temperature 1.0 on this entry; requests that set their own sampling, as the quality tests do, are unaffected.
- **Flash-Next with MTP:** control's server now applies the greedy default under `--mtp` only to Qwen3.6; Flash-Next keeps the model card's sampling for requests that send none (1e5070f73). This is in control, so `flash-next-strata` gets it on control 0.1.69 whichever Qwen engine it runs.
- **Parked-conversation cache:** its default size now grows with free RAM. The RAM guards here are tight, so memory use is watched on the large entries.
- **App host:** its own `/api` refuses requests from other web pages (#7130); the router's `/v1` calls do not go through it.
- **Hy4:** no new engine in this release.

All packages were verified against the signed feed with upstream's signing code and staged under `runtimes/strata-manual/0.2.22-20261125/`. Pre-images and `rollback.sh`: `data/strata-update-20261125/`. The install changed only the planned preset fields (the Flash-Next working folder and the Inkling program path); the Hy4 preset hash is unchanged.

## Checks

Short DSH check (one real tool call, tool result and follow-up, owned unload) and the gBench chat-template check, one profile at a time, GPUs at 1 MiB before and after. gBench passed 6/6 on every run below except the final Flash-Next recheck and the second Qwen 0.1.69 run, which were speed checks only (the same configuration passed gBench in the after-run). Single runs. The "before" runs were taken on November 25 on kernel 7.0.0-43, the "after" runs on November 26 on 7.0.0-44.

| Profile | Version | Prompt reading (tok/s) | First token (s) | Generation (tok/s) |
|---|---|---:|---:|---:|
| `flash-next-strata` | 0.2.21 (control 0.1.67, engine 0.1.65) | 1,247.4 | 4.64 | 69.0 |
| `flash-next-strata` | control 0.1.69, engine 0.1.65 | 1,257.4 | 4.58 | 67.2 |
| `flash-next-strata` | control and engine 0.1.69 (two runs) | 1,169.2 / 1,164.1 | 4.96 / 4.98 | 56.1 / 58.2 |
| `flash-next-strata` | control 0.1.69, engine 0.1.65 (kept, recheck) | 1,271.8 | 4.54 | 67.2 |
| `inkling-strata` | 0.1.67 | 2,140.7 | 3.43 | 67.0 |
| `inkling-strata` | 0.1.69 | 2,132.7 | 3.43 | 67.0 |
| `hy4-flash-strata` | control 0.1.67 (engine 0.1.67) | 206.7 | 27.20 | 27.6 |
| `hy4-flash-strata` | control 0.1.69 (engine 0.1.67) | 212.9 | 26.43 | 27.9 |
| `deepseek-unsloth-strata` | control 0.1.67 (engine 0.1.59) | 28.6 (prompt reuse) | 6.12 | 9.8 |
| `deepseek-unsloth-strata` | control 0.1.69 (engine 0.1.59) | 28.3 (prompt reuse) | 6.18 | 12.2 |

- **Flash-Next on Qwen engine 0.1.69:** passes, but generation is 13-17% lower on two runs (56.1 and 58.2 against 67.2 tok/s) and prompt reading 7-8% lower, the same pattern as 0.1.66 and 0.1.67. Engine 0.1.65 under control 0.1.69 runs at the old speed on two runs, so the preset stays on the 0.2.19 Qwen package. Holding the Qwen engine back is the standing practice for this entry since 0.2.20 (runbook: try each new Qwen engine before moving the preset), not a promotion-rule break: 0.1.69 passes every check.
- **DeepSeek on Strata:** the 9.8 tok/s before-run is the low outlier; this entry measured 12.2-12.3 tok/s on November 24, so its speed is unchanged.
- Inkling and Hy4 run at the same speed.
- The first Qwen 0.1.69 smoke attempts were refused with "Missing exact updater reservation" because the script was started by a relative path; the updater checks its own command line for the absolute script path. Started with the absolute path, it ran normally. No lock was left behind.
- Serving left idle and unloaded, both GPUs at 1 MiB, unlock VERIFIED.

## Decision

**Promoted** under the promotion rule: every Strata entry loads, calls tools, follows up, passes gBench and unloads, at the same speed. `flash-next-strata` keeps Qwen engine 0.1.65. Rollback: `data/strata-update-20261125/rollback.sh` (router idle) restores 0.2.21.
