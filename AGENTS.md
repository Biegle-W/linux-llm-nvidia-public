# Agent entry point

Read [README.md](README.md) for standing policy, then
[the current takeover state](docs/CURRENT-STATE.md) before acting. The registry is
`config/maintained-profiles.json`; historical measurements are evidence, not live
settings. Update these entry points, the benchmark ledger and both NVIDIA repos
after meaningful changes so another agent can resume without chat history.

Four qualified context upgrades and the approved lifecycle controls are deployed.
All six normal launch paths passed functional/limit checks. Actual GLM/dense idle
expiry and normal reload, plus isolated Strata idle/reload, are verified. No test
coordinator remains active. Maya sustained-swap qualification remains unresolved;
retain its guarded 32K setting and do not relabel short API success as qualification.
Do not repeat completed measurements. CURRENT-STATE.md records exact evidence.

The user accepted GLM 65,536 and Strata DeepSeek 131,072 despite the recorded
speed tradeoffs. Resource and near-window quality qualification still applies.
Other context changes retain their matched no-speed-loss selection requirement.
The AMD repository is read-only reference for the requested gap audit; ask before
filling optional cross-repository feature/model gaps. No new unlock tests or
hardware changes are authorized by that audit.

The user approved three operational additions after context rollout: guarded
ten-minute idle unload, full lifecycle telemetry and manual candidate staging.
Do not ask again for those additions. Model coverage stays unchanged.

Read the [additional AMD parity task background](docs/AMD-PARITY-HANDOFF-20261027.md)
as a dated backlog. CURRENT-STATE.md is authoritative for live jobs and completion.

The user approved unlimited worker swap occupancy with active churn protection.
The maintained guarded paths implement this; preserve RAM/GPU limits and consult
[the policy and rollout evidence](docs/INFERENCE-SWAP-POLICY.md).

The latest user instruction supersedes the earlier VM10 trial approval: keep host
swappiness at 60. Do not launch or persist swappiness10. Continue remaining
qualification and deployment at 60 with the existing worker swap/churn guards.

## GPU unlock persistence after updates

As part of every kernel or NVIDIA driver update, automatically check that the
existing GPU unlock remains installed and configured for the next boot. Also
perform this check when resuming on a different kernel/driver version. Follow
[the update verification procedure](docs/UNLOCK-SETUP-20261026.md#required-checks-after-kernel-or-nvidia-driver-updates).
Verify DKMS for the target kernel, GRUB targets and early initramfs loading; after
the user's next reboot, confirm successful unlock on both selected GPUs before
NVIDIA binds and record the running kernel/driver and boot evidence. Do not call
next-boot preparation post-boot verification. Keep incomplete/failed checks visible
in CURRENT-STATE.md. The user controls reboot; this requirement does not authorize
driver updates, new unlock benchmarks, firmware changes or switching unlock source.

The user subsequently requested OS-level automatic checks independent of agents.
The [health checker](docs/GPU-UNLOCK-HEALTH.md) is installed and enabled. Boot and
package-update events run root-owned services without an agent. Initial boot and
update-hook audits passed. Inspect `gpu-unlock-health status --brief`, root-written
results and failed units rather than relying on this reminder. Preserve the
root-owned installed copy and event hooks; agents must not silently substitute
user-writable service code. Actual updates/reboots remain user-controlled.
