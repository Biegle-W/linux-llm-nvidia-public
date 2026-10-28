# Automatic engine switching and console ownership — October 28,2026

Selecting a different maintained engine/model closes the previous owned backend
before starting the new one. Active API replies finish first; native queued/loading/
vision work and unknown state continue to defer teardown. The router, DSH,protected
test harnesses and unrelated processes/terminals remain separate.

## What changed

Backend viewers for `llm-test-qwen27b.service` and `llm-router-worker.service` now
follow the worker invocation. They close when that backend stops or is replaced.
Before opening a new viewer, the launcher retires only a matching registered viewer
from this project; PID reuse,another script or another terminal type is preserved.
Viewer cleanup checks its marker ownership and never terminates the terminal app.
A pending backend viewer also closes if no worker starts within 30 seconds.
Router/DSH and benchmark/review consoles do not inherit backend auto-close behavior.

Worker switching rechecks invocation ownership before stopping the exact guarded
unit. Dense backend titles identify SGLang or HyperQwen. A successful Desktop
selection launcher exits while the dedicated backend console remains visible;
it no longer waits for Enter and looks like a second inference engine. The CLI
reports a router reservation error clearly rather than printing a traceback.

All normal Desktop/CLI and DSH/API paths still select existing fixed profiles
through the same serialized router. Same-model requests retain their existing
reuse logic. No broad Python/GPU kill commands,driver changes or guard bypasses
were added. A protected GPU-LOCK reservation blocks engine selection; it is never
removed or stolen by a new launch. No model is restored after owned test cleanup.

## Verification

[Sanitized verification](validation-results/20261028-engine-switching.json) records
53 engine/ownership CPU regressions plus a genuine normal SGLang 32K→HyperQwen-vLLM 56,320
switch. A 512-token SGLang stream completed while a new HyperQwen selection waited.
Then the old worker and viewer exited, a new worker invocation and viewer became
ready, and HyperQwen answered JSON through the API. Router and DSH invocation IDs
were unchanged during the switch. Normal unload closed the HyperQwen worker and
its backend viewer. The independent visible test/review console remained.

A live test-owned reservation refused selection and preserved its exact owner.
CPU tests also cover idle native/MoE stop ownership, busy/loading/vision and unknown
state preservation,worker invocation replacement, reused viewer PIDs and protection
of router/harness viewers. Large MoE models were not reloaded while RAM is reduced.
No throughput benchmark or context qualification was repeated.

Final state: router idle, DSH active, no GPU-LOCK or test coordinator. SGLang remains
32,768 because 38K failed full KV coverage on a normal reload. Dense reserve 512 MiB,
swappiness 60, 600-second idle policy and all RAM/thermal/swap guards are unchanged.
Raw test logs/receipts stay private under data/engine-switch-visibility-20261028/.


## Non-interrupting terminal startup

All project consoles now request native iconic startup: router, DSH, backend, selector
and test harness. Pinned XTerm 407-1ubuntu1 plus libutempter 1.2.1-4build1 are unpacked
under runtimes/visible-terminal; binary/library and package SHA256 values live in
config/terminal-runtime.json. No global package installation or terminal preference
was changed. Run scripts/install_visible_terminal_runtime.py to reproduce setup.

A window-manager check confirmed initial Iconic, WM_STATE Iconic,hidden and not-active
for the live test harness, router, DSH and SGLang backend. Because initial state is
set before mapping, the implementation does not briefly focus then minimize a window.
All four Desktop engine selectors use Terminal=false and the minimized wrapper.
Native engine readiness prints its UI URL without opening a browser automatically.
Existing unrelated windows and completed review terminals are not forcibly closed.
The evidence JSON includes the actual minimized-window checks and final idle state.
