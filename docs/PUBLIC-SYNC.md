# Public reference maintenance

The Linux operational repository publishes selected reviewed files to
[linux-llm-nvidia-public](https://github.com/Biegle-W/linux-llm-nvidia-public).
The Windows public repository remains the Windows reference; Linux measurements
belong in the Linux pair.

After validated changes, run `python3 scripts/sync_public.py PUBLIC_CHECKOUT` from
the private Linux repository. The explicit allowlist exports reference docs and
source helpers only. It requires a clean matching public checkout, scans for
common identity and credential patterns, and refuses a different destination.
Review the complete diff for sensitive information before committing and pushing
each repository independently. The scanner supplements human review; it cannot
prove that arbitrary prose is safe.

Keep commits nonpersonal and never force-push. Do not merge private branches or
copy private Git history. Exclude model weights, binaries, runtime environments,
credentials, raw logs, chats, machine identifiers, user paths and local state.
Benchmark summaries may include generic hardware specifications and measured
rates, with methodology and limitations. Keep raw evidence privately.

Launch helpers in the public tree are reference source: they require locally
installed engines, profiles and a private API key. Those assets are not exported.
This is a maintenance workflow, not a scheduled background publisher.

Local Codex session helpers, their workflow document/tests, raw session evidence
and private checkpoints are outside the export allowlist. Explicit
`private-codex-context` sections are removed from reference Markdown before the
privacy scan; unbalanced or reversed markers refuse export. General takeover
handoff upkeep remains part of the public maintenance policy.

Benchmark preservation and synchronization are standing requirements. Save dated
raw results privately after every run; retain prior results even when a setting or
model is retired. Update the benchmark reports and maintained-profile registry
after tests or setting changes, including failed trials and context-validation
limits. Export the sanitized summaries, review the diffs, commit and push both
repositories independently, and verify each branch matches its upstream. Do not
rerun completed benchmarks just to refresh the repositories. If synchronization
fails, preserve the results locally and report the outstanding publication step.

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
