# Automatic terminal lifetime — October 29, 2026

Finished test harnesses previously waited for Enter, and failed Desktop selectors also held their windows. Router/DSH log viewers could remain after their service stopped. These completed windows now close automatically.

- Foreground harnesses and selectors close after their child command exits, including failure. There is no post-completion Enter prompt.
- Foreground output is recorded through a real child PTY using the installed util-linux `script` utility. Interactive selectors and commands that require a TTY retain it. Exit status is propagated and saved in an atomic receipt; private transcripts and receipts under `data/visible-terminals` use mode 0600.
- Service viewers close when their own service is confirmed inactive or failed. A pending viewer closes after 30 seconds if no service starts; active or unknown state is preserved. Backend viewers also follow the exact worker invocation. Router/DSH viewers stay useful across a still-active service restart.
- Backend teardown remains restricted to backend viewers. It does not stop router, DSH, active tests or unrelated terminal applications. Closing a viewer never stops its service.
- New windows retain the pinned native-iconic startup and do not request desktop focus. At most one registered viewer is reused per service. Completed output remains in transcripts, journals and existing engine logs.

This supersedes the earlier instruction to keep completed harness windows waiting for Enter. Logs provide the retained results without keeping a completed window open.

## Verification

All 207 CPU regressions passed. Real minimized terminal checks verified a successful command (exit 0), an intentional failure (exit 7), and a service viewer that remained alive while a short CPU-only service ran and closed after it stopped. Child stdin/stdout/stderr were real TTYs in both foreground cases; output and exit receipts survived closure. The outer verification harness also closed automatically.

The final host process inventory and user-service inventory showed zero project terminal windows/units. Router and DSH kept their original process/invocation identities. Model profiles, swap/pressure guards, shared inference policy, memory budgets, binary pins and minimized-terminal configuration remained byte-for-byte unchanged. No models or GPU benchmarks were launched.

## Swap and performance clarification

Swap-rate settings in this project are guard stop thresholds; they do not throttle bandwidth, allocate additional swap, or force Linux to swap. Raising a threshold permits a request to continue if it would otherwise be stopped. It does not accelerate a request that remains below the threshold. Existing expanded swap allowances and model-specific pressure settings are preserved by this terminal change. The slower historical benchmark still needs a controlled cache/I/O investigation; no performance improvement is claimed here.

[Numeric verification](validation-results/20261029-terminal-lifetime.json).
