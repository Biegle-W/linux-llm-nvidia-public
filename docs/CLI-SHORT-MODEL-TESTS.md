# Short maintained-model checks from a Codex CLI terminal

Use your existing foreground terminal. No Codex desktop chat, browser, XTerm window or desktop-thread API is needed for the harness. The explicit CLI-terminal instruction allows a real foreground CLI TTY to satisfy harness visibility. It does not authorize invisible detached tests or disabling resource/ownership checks. API model workers remain headless as already deployed.

From the NVIDIA checkout:

```sh
cd /path/to/linux-llm-nvidia
python3 scripts/visible_terminal.py foreground --title "Maintained model short checks" -- /usr/bin/python3 scripts/cli_short_models.py
```

For one maintained profile, append `--profiles qwen27b-hyperqwen` after `cli_short_models.py`. Use a new output directory with `--output /absolute/path` if desired. Default evidence is private under `data/short-cli-tests/`; the foreground wrapper also retains a private transcript and exit receipt.

If launched by Codex CLI through a sandboxed shell tool, approve running this exact foreground command with host access when prompted. It needs access to the current user's systemd bus, NVIDIA devices and localhost ports 10100/10000. Do not use `sudo` for the model test, do not disable the Codex sandbox globally, and do not remove the guard or ownership checks. If host approval is unavailable, the agent must report that restriction. Missing desktop-thread tools are irrelevant to this terminal workflow.

The runner requires a real stdin/stdout TTY, a passing current-boot transport proof (qualified P2P or explicitly disabled-P2P host staging), VERIFIED unlock, idle admission, no GPU reservation and inactive model workers. Unknown/inaccessible service state fails closed. Existing independent work is preserved; the runner neither clears reservations nor stops an initial worker.

Each current selected profile is loaded through the authenticated router, uses one short real DSH read tool with matching fixture result, collects prefill/TTFT/native decode in the same call and requests owned unload. The next model is selected only after the previous worker is verified inactive. This checks sequential model-selection/unload boundaries; it does not claim a busy-inference switch test. The first tool/guard/unload failure stops the sequence with retained evidence; no automatic repeated reload or forced cleanup of unknown work is attempted.

The selected profile's RAM high/max and host reserve, free-VRAM floor or native cache reserve, startup admission, swap occupancy/I/O windows and PSI rules accompany numeric results in state.json. Resource enforcement remains in the production guarded launch paths. Limits are not reported as measured peaks. Model settings, guard thresholds, credentials and saved DSH selections are preserved. Keys and authentication transcripts must never be printed.

No full-context, sustained stress, repeated-reload or timed-idle suite is included. The enabled HyperQwen and SGLang profiles passed the [November 3 requested checks](evidence/REQUESTED-TWO-MODEL-CHECKS-20261103.md) at their selected contexts. The runner does not silently reduce context or enable a temporarily disabled RAM profile to obtain a pass. Historical benchmarks stay dated evidence. Use the normal benchmark-reporting conventions for any final table, including model/quant, engine, prefill, TTFT, decode, configured context, decimal-GB storage/location and companion RAM/VRAM/swap guard table.
