# DSH headless startup repair — November 3, 2026

The optional DSH loopback web service was restarting because `dsh/run web` unconditionally required a desktop monitor before starting Node. A headless user manager has no display environment, so the monitor refused startup. API and model-hub services were healthy; no model load was needed to diagnose this failure.

The managed DSH unit now explicitly sets `NVIDIA_DSH_HEADLESS=1`. Only that explicit mode skips the desktop monitor. Ordinary desktop web launches still fail if their required monitor cannot open. The optional-client installer reproduces the unit, including the existing owner-only startup log used by the desktop shortcut. Loopback binding, `--no-open`, private credentials, `UMask=0077`, `NoNewPrivileges=true` and the 2 GiB service cap remain. No display session is started and the physical-input desktop activation policy is unchanged.

All 19 focused CPU checks pass, including an actual shell/Node fixture without a display, desktop-monitor failure with no hidden fallback, generated-unit safeguards, existing provider/selection preservation, headless API service policy, inference policy and model availability. Live browser-token/cookie authentication returns HTTP 200 and the application HTML; unauthenticated access returns HTTP 401. DSH has zero restarts since the final deployment and its invocation is stable; API/hub invocations are unchanged. Initial readiness probes incorrectly assumed the root URL was public and treated its expected HTTP 401 as lack of readiness. The final check uses the actual browser handshake and private startup log. No inference, speed benchmark, full-context or sustained model test was run.

## Current project state

The host has temporary 32 GB RAM pending an upgrade. Only HyperQwen (86,016 tokens) and SGLang (57,344 tokens) are enabled. Both use 24/26 GiB worker RAM limits, a 2 GiB host reserve and the 256 MiB per-GPU free-VRAM stop floor. Swappiness remains 60; idle unload remains 600 seconds. All independent ownership, RAM, VRAM, temperature, swap, pressure, telemetry and transport guards remain. Early unlock and the root-owned current-boot host-staged proof pass; CUDA peers are disabled both ways. The later native-output buffering repair remains deployed.

Bolt, Flash-Next, GLM and both DeepSeek profiles remain temporarily disabled. Their preserved contexts/caches are definitions, not qualification on this host. Re-enabling requires explicit RAM installation confirmation, measured capacity and guarded qualification. Prior GLM/Bolt short-tool gaps and DeepSeek/Maya sustained-swap limitations remain dated evidence for future requalification. The old SGLang 38K reload failure is historical; it is not a pending task for the already allocated 57,344-token profile. Daily engine updates remain paused.

The registry now states temporary RAM status, current enabled-profile context evidence and deferred checks for disabled profiles. Current-state entry points and the network catalog point to this state; historical benchmark numbers, failed trials and their original guard attribution are preserved. No model/cache/context/guard setting changed.

Sanitized verification: [20261103-dsh-startup.json](validation-results/20261103-dsh-startup.json).
