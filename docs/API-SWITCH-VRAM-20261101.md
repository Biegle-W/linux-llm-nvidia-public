# API model switch startup VRAM — November 1, 2026

A later 64K HyperQwen timing capture was stopped by the unchanged 512 MiB free-VRAM floor. The current 40K/448 MiB KV allocation passed native capacity and actual tool checks; see [the current report](SHORT-TOOL-BENCHMARKS-20261101.md). The startup settling wait and thresholds below remain unchanged.

A Flash-Next to HyperQwen API switch stopped at preflight because GPU1 had less than the selected 8,960 MiB startup requirement. The original error did not record actual free memory. A later idle reading showed 9,027 MiB, so transient release/desktop use is a plausible cause, not conclusively measured.

Qwen startup now waits up to20 seconds for VRAM to become available, retains the same per-profile thresholds, rejects changed GPU identities immediately, and reports actual available/required memory if the deadline expires. No application is terminated and no reserve is reduced.

Three focused CPU regressions passed: delayed release, persistent shortage, and identity mismatch. The guarded HyperQwen load then completed an actual DSH read call and matching file result in4.87seconds after readiness. No full-context or timed-idle test was run.
