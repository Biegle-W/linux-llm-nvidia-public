# Agent entry point

Read [README.md](README.md) first; it remains the canonical policy.
Then read the [AMD parity handoff](docs/AMD-PARITY-HANDOFF-20261027.md),
[current profiles/results](docs/MAINTAINED-PROFILES.md) and
[network handoff](network/README.md).

The user requested takeover-ready notes for agents on the NVIDIA server to
address the documented gaps. Check current Git changes, completed evidence,
live ownership and GPU reservation before implementing work. Runtime validation
belongs on the NVIDIA host. Optional model downloads and new schedules require
the choices described in the handoff; AMD-owned items are references, not an
instruction to modify the other server.

Keep both NVIDIA repos, README/AGENTS, benchmark Markdown/results, selected
registry and handoff current after relevant changes. Preserve dated results
and private evidence; record actual blockers, active work/locks and the next
step before yielding. Review sanitization and verify both publications.
Do not repeat completed GPU tests merely to refresh documentation.
