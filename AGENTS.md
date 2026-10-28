# Agent entry point

Read [README.md](README.md) for standing policy, then
[the current takeover state](docs/CURRENT-STATE.md) before acting. The registry is
`config/maintained-profiles.json`; historical measurements are evidence, not live
settings. Update these entry points, the benchmark ledger and both NVIDIA repos
after meaningful changes so another agent can resume without chat history.

An active context benchmark is in progress. Do not launch competing GPU work or
repeat completed measurements. The current-state document identifies the exact
coordinators, raw evidence, accepted tradeoffs and remaining steps.

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
