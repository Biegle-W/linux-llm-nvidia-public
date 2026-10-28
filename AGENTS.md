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

## SGLang pipeline and recurrent-state study

The user-approved 34/30 and 36/28 pipeline splits failed the unchanged 1 GiB
GPU-headroom requirement. BF16 on 32/32 passed the tested quality checks but
showed only +0.9% decode with slightly slower prefill/TTFT. No candidate was
promoted. Retain 32/32 FP32 and HyperQwen as default; do not repeat these
completed settings or weaken the guard. See docs/SGLANG-TUNING-20261027.md.

## Isolated SGLang W4A8 study and temporary RAM maintenance

The user subsequently approved an isolated MLP-only W4A8 patch test. The final
compressed-tensors adapter activated exactly 128 decoder MLP projections and
passed 18 standalone GPU kernel checks plus JSON, arithmetic and 29,434-input
retrieval. Prefill improved 21.6% and TTFT 17.5%, but decode regressed 1.4%;
no production promotion. The first AutoRound-loader attempt was rejected by its
zero-activation audit before benchmarking; preserve that diagnostic evidence.
Retain the existing W4A16 SGLang package and HyperQwen default. See
docs/SGLANG-W4A8-20261027.md; candidate source/cache is private evidence.

One RAM stick is temporarily removed; Linux currently sees 45.55 GiB usable.
This dense study used fresh controls and retained all guards at swappiness 60.
MoE profiles have not been qualified on reduced RAM; check capacity and budgets
before any future MoE work. GPU unlock health reports VERIFIED after reboot.

## Heterogeneous TP2/MTP follow-up — October 28

The user accepted the W4A8 tradeoff and authorized an isolated heterogeneous
TP2/MTP study. The earlier decode regression is not a reason to reject that
accepted tradeoff. This authorization does not silently promote the fork.
The pinned fork, separate native runtime, reproducible local compatibility patch,
all startup failures and completed controls are recorded in
[the study report](docs/SGLANG-HETERO-MTP-20261028.md). That study used a
1 GiB GPU-free guard (superseded by the user-approved 512 MiB floor below), 8 GiB host floor, 30/36 GiB worker limits, active swap-churn
protection and swappiness 60. No generic CPU weight offload is permitted.
The benchmark metric reader now counts one canonical TP replica after the final
PP stage; seven regression tests cover parallel-rank accounting. Do not recompute
historical measurements or repeat completed variants because the reader changed.

Final outcome: MTP3 qualified at 16K (84.63 decode tok/s, +32.51% over its
matched TP2 control; 14,686-input retrieval). Corrected MTP1/MTP3 failed 32K
GPU-headroom qualification. HyperQwen and normal worker were restored; no
experimental coordinator or GPU-LOCK remains. See CURRENT-STATE.md for details.

## Visible terminals and test cleanup — user direction, October 28

All backend and harness launches must have visible desktop terminals so the user
can monitor progress. Guarded services keep their resource limits; live terminal
consoles display their journals and redirected engine logs. Dense bounded launches,
router MoE launches, router startup and DSH web startup open consoles automatically.
A failed visible-console handshake must not silently fall back to a hidden launch.
Closing a console leaves the guarded service running; its stop command is printed.

Run every future benchmark/test coordinator through the visible foreground wrapper:
`python3 scripts/visible_terminal.py run --title "Test name" -- /absolute/command args`.
For custom worker units, open a console with `visible_terminal.py open --title
"Backend" --unit NAME.service --log /absolute/engine.log` before starting them.
Preserve dated logs/results as well as visible output. Do not run new harnesses
silently through detached API commands. Completed terminal harnesses retain their
exit code and wait for Enter so results remain visible.

Do not automatically reload HyperQwen after an isolated experiment. Unload the
owned test worker, release its reservation and report the idle state unless the
user explicitly requests a backend to be left running. HyperQwen's existing
catalog/default metadata is not permission to repeatedly reload it after tests.

## Standing repository publication authorization — October 28 clarification

The user explicitly authorized publication of all pending reports, handoffs,
experimental patches and visible-terminal changes to
`Biegle-W/linux-llm-nvidia-public`, and reaffirmed that both repositories and
Markdown documentation must always stay updated. Routine publication of reviewed, sanitized project reports, handoffs,
reference code and experimental patches is included in that standing direction;
do not ask for a separate approval after every study or implementation change.
Continue the existing export allowlist, privacy review, nonpersonal commits and
independent pushes. A platform automatic-review rejection is an external tool
restriction, not a user-requested approval policy. Describe it accurately and
never attribute that restriction to the user or bypass a rejection.

## Dense VRAM reserve update — October 28

The user explicitly lowered the dense GPU free-memory guard from 1,024 MiB to
512 MiB and authorized a visible-terminal TP2/MTP3 32K retest. The normal dense
supervisor and isolated retest share DENSE_GPU_FREE_MIB=512. Normal workers stop
after three low-headroom checks; isolated trials also require at least 512 MiB
at readiness. Swappiness stays 60; host reserve 8 GiB, worker RAM 30/36 GiB,
temperature 82°C, unlimited swap occupancy and active swap-churn guards are unchanged.
Earlier 1 GiB failures remain historical evidence under their original guard.
This approval does not promote the experimental fork or change the selected
engine settings. Future tests still run visibly and finish idle after cleanup.

The [512 MiB retest](docs/SGLANG-MTP3-512MIB-20261028.md) passed at 32K: 82.79
decode tok/s, JSON/arithmetic and 29,434-input retrieval, minimum sampled free
VRAM 802/997 MiB. No production fork promotion; prior 1 GiB failures are preserved.
The visible test finished idle, with no automatic HyperQwen restoration.

## Desktop shortcut names — October 28

Managed Desktop shortcuts are named HyperQwen vLLM, SGLang, Strata and Maya,
without an LLM prefix. Their filenames omit that prefix too; the installer migrates
only project-owned legacy entries. Preserve DSH and unrelated shortcuts. CLI
llm-* command names remain unchanged. See network/README.md for current routing:
DSH/API model IDs select fixed engine profiles; the experimental TP2/MTP3 fork
now backs the maintained qwen27b-sglang profile after verified deployment.

## Latest: SGLang production deployment — October 28

The user explicitly deployed the fastest tested SGLang generation architecture:
TP2 + MTP3, decoder MLP W4A8, BF16 state/KV, one Mamba slot, 32K. It now backs
the existing qwen27b-sglang ID, shortcut and DSH provider. Earlier PP2/FP32 and
“no promotion” statements describe historical stages; do not restore PP2 as the
normal profile. Source/dependency pins are in config/sglang-runtime.json; the
normal launcher verifies hashes, import location and versions. env-sglang is still
an active general-dependency fallback; do not delete it. Source/caches are in
stable `runtimes/` paths, not dated trial folders. Previous source/settings were
archived privately at 733820f; keep only the retirement pointer in the active registry.

Fifty CPU regressions, normal-router streaming JSON/tool call, 29,434-input
retrieval, a 4,096-output, 39.62 s continuous check and a normal unload/reload check
passed. Four complete active swap windows had zero owned swap I/O. Keep the
512 MiB dense reserve, swappiness 60, all other guards and visible terminals.
The router supplies non-thinking defaults while preserving explicit overrides.
The original 82.79 tok/s qualification median is carried forward, not remeasured.
SGLang is intentionally selected after deployment; the ordinary 10-minute idle
unload still applies. HyperQwen was not restored and saved DSH defaults were not
changed. See docs/SGLANG-DEPLOYMENT-20261028.md and CURRENT-STATE.md.
