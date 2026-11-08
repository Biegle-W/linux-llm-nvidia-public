# Context setup and short harness verification — November 1, 2026

Set context from the engine's calculated KV token capacity, host RAM budget, GPU memory and required reserves. Keep independent RAM, VRAM, swap-I/O, pressure, temperature, telemetry and idle-unload guards active. Calculated capacity is not a full-context quality guarantee.

The default check is one short real DSH tool-call round trip using a tiny local fixture, followed by owned unload. Do not run near-full-window retrieval, long generation stress, repeated reload or a timed idle soak unless explicitly requested. Preserve earlier benchmark and context-validation evidence under its original date and settings.

For Super, the normal loader reported 81,477 KV tokens with 384 MiB BF16 KV per GPU. The configured 65,536-token context retains calculated capacity headroom. Its earlier isolated full suite is historical evidence under its original 32/64 swap policy. The later normal-router 64/96 suite was cancelled under this short-test policy; it must not be reported as a completed full suite.

The legacy daily GPU qualifier now refuses to start under this policy without the explicit `--allow-full-context-tests` opt-in. Read-only revision checks and recovery remain available. The daily timer stays disabled; this opt-in must not be added to its service implicitly.
