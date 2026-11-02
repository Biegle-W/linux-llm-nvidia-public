# HyperQwen stopped-worker classification and pending headroom check

Two real HyperQwen startup attempts stopped at the unchanged 512 MiB free-VRAM guard: the tighter GPU reported 499 and 504 MiB free. RAM and GPU temperature were above/below their respective safety limits. This is a resource stop, not evidence that another job stole ownership.

The reattachment path previously compared InvocationID before checking whether the unit had stopped. systemd may clear InvocationID on exit, producing the misleading message "Worker ownership changed while waiting". It now checks stopped state first and reports `launch_failed`; a live changed invocation still reports `ownership_conflict` and remains untouched. No automatic stop, retry or replacement was added.

Two CPU regressions pass: stopped worker with a cleared invocation, and live replacement preserved without launching or stopping anything. The loaded hub was started after the source fix was written, so no additional restart was needed to read this code. No GPU inference qualification is claimed by these tests.

The planned HyperQwen allocation is 77,824 tokens with a 704 MiB INT4 KV pool per GPU. It has NOT been selected or benchmarked: the previous controller deferred while preserving independent SGLang work, and the next visible-harness attempt could not start because no user graphical desktop session was logged in. Current HyperQwen remains 86,016 tokens / 768 MiB KV until a guarded candidate check succeeds. Its 512 MiB floor and all other guards remain unchanged; SGLang is unaffected.

Model testing must resume only through the required visible harness, or an explicit user-approved exception. Preserve any running work and avoid duplicate controllers. No full-context or sustained suite is implied.
