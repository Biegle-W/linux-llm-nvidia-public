# Six selected profiles benchmarked with 64GB RAM — October 29, 2026

Firmware reports **DDR5-4200 MT/s** across all four 16GB DIMMs (64GB installed; Linux 61.3013GiB usable). This is equivalent to a 2100MHz DDR clock. The configured-speed reading was obtained through read-only SMBIOS/DMI; no BIOS, clock, power, precision, model or guard setting was changed.

Each selected profile used one 64-output warmup and three measured 128-output requests with fixed approximately 2.2K-token reference prompts, temperature0, top_p1, seed261026 and thinking disabled. The table reports medians. Prefill uses native timing/metrics; TTFT is request-to-first-content; decode is (completion tokens−1)/(last−first content timestamp). Cache reuse was checked. Loading and warmup are excluded, and the OS file cache was not flushed.

| Model / engine | Context | Prefill tok/s | TTFT seconds | Decode tok/s |
|---|---:|---:|---:|---:|
| Qwen 27B / HyperQwen | 56,320 | 1494.29 | 1.489 | 88.55 |
| Qwen 27B / SGLang | 32,768 | 1587.90 | 1.396 | 80.87 |
| Qwen Flash-Next / Strata | 32,768 | 117.80 | 18.671 | 55.84 |
| GLM / Maya | 65,536 | 70.10 | 31.407 | 5.32 |
| DeepSeek / Strata | 131,072 | 32.60 | 67.294 | 3.12 |
| DeepSeek / Maya | 32,768 | — | — | Failed swap guard |

Five profiles completed three valid measured requests. DeepSeek/Maya completed warmup but failed during its first measured request: 5.31MiB/s swap writes and 0.37MiB/s reads over30.44seconds exceeded its1MiB/s write limit. No new speed median is reported for it; its older1.23tok/s result remains historical reduced-RAM evidence. Existing host/cgroup/GPU/thermal/swap guards remained active, and their captured outcomes are retained, including the DeepSeek/Maya guard stop. The guard was not relaxed and no failed result was promoted. Parked/loading swap is allowed by the selected policy; sampled swap peaks and observed active rate windows are preserved in the numeric evidence. Short requests may not form a complete30-second rate window. This is a fixed-fixture speed screen, not a new full-context, tool/image or long-duration reliability qualification.

Full-RAM cache choices: GLM40GiB, Strata DeepSeek42decimalGB and Maya DeepSeek8GB warming with original mapped-expert mode. Maya's newer pinned binary remains installed with the optional temporary16GiB file controller inactive. Qwen Flash-Next retains plain mapped experts on both GPUs and its Qwen-only128/160MiB/s swap allowance; other profiles retain1/8MiB/s. Native512MiB reserves, dense GPU headroom, host floor2GiB, swappiness60, concurrency1 and idle600seconds remain unchanged.

Historical measurements are retained separately. Different prior cache modes, hardware capacity, input framing and policy mean they are not paired controls for attributing a speed change to RAM alone. In particular, Qwen's earlier97.09tok/s used an older configuration; it is not the current mapped-expert result. The earlier58.71tok/s was a different long-generation workload.

The first setup attempt stopped before any measured request because it waited for an OpenAI startup counter absent from this SGLang fork. Readiness was corrected to observe the native startup completion; the measured run reused the exact saved fixtures and still validated native per-request metric counts. No completed benchmark was repeated for selection. Cleanup unloads the benchmark worker without loading a fallback model and preserves a changed worker invocation.
