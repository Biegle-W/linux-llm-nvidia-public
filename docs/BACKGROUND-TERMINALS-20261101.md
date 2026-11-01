# Background terminal focus protection — November 1, 2026

Automated tests and backend viewers now enforce background behavior at the terminal executable boundary. This also covers services that already imported an older launcher, without restarting their inference work. A verified wrapper starts those windows iconic, clears inherited activation tokens, disables bell urgency and output-driven window operations, and applies non-input window-manager hints with zero user time before starting the child command. Ownership is checked against the project terminal class.

Explicit `--attention` tasks and user selectors keep normal mapped windows and confirmed activation. Authentication and choice prompts remain foreground tasks. The change does not alter system-wide terminal or window-manager settings, close unrelated windows, or stop inference jobs. Existing background viewers were verified inactive and minimized.

A live current-launcher test emitted twelve bell, deiconify and raise requests: all 24 samples stayed iconic and inactive, with input disabled and user time zero. A separate test loaded the pre-change launcher and routed it through the verified execution boundary: all 25 samples stayed iconic and inactive, with input disabled. Both test windows exited normally. Sixteen backend-console regressions and four execution-boundary and seven presentation regressions passed; live attention tests were deliberately avoided during user work.

The evidence establishes the tested launch and output paths; it does not identify the exact historical activation event. [Machine-readable results](validation-results/20261101-background-terminals.json).
