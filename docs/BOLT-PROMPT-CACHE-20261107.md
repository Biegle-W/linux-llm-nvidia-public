# Bolt RAM prompt cache enabled — November 7, 2026

The maintained `bolt-llamacpp` entry now starts llama.cpp with `--cache-ram 8192` instead of `--cache-ram 0`. When a request moves the single slot to a different prompt, llama.cpp saves the previous prompt state in host RAM (up to 8 GiB) and restores it if that prompt comes back. This mainly helps DSH and agent sessions that return to an earlier long context. Weights, the 163,840-token context, the 384 MiB fit targets, the Q8_0 KV cache and all resource guards are unchanged.

The budget is a reviewed manifest field (`cache_ram_MiB` in `config/bolt-iq2-runtime.json`). The production runtime refuses any value other than 8192. Isolated trial pins without the field keep the old `0`. The nightly llama.cpp updater keeps the field because it updates the manifest in place.

## Validation

| Check | Result |
| --- | --- |
| Guarded short actual DSH tool/result/exact follow-up and owned unload (`--smoke-current bolt-llamacpp`) | Pass: 501.09 prefill tok/s, 12.857 s TTFT, 69.17 decode tok/s (Nov 5 without cache: 500.31 / 12.899 s / 67.79) |
| A, B, A revisit through the normal router (about 14.1K tokens each, three markers per document) | A first 26.525 s TTFT; B first 21.482 s; **A revisit 0.422 s**, 14,109 of 14,113 prompt tokens restored from RAM |
| Marker retrieval | 3/3 in exact order on all three requests |
| Worker memory peak | 2.51 GiB (worker cap 87.77/89.77 GiB unchanged) |
| Cache save cost per prompt switch | about 0.22–0.25 s |
| Unload | Router unload succeeded; both GPUs back to 1 MiB |

The first-request numbers are single observations with OS file caches warm, not sustained or full-context tests. The 8 GiB budget holds roughly 50 saved prompt states of this size at about 165 MiB each; larger contexts take proportionally more. Each launch starts with an empty cache. All 514 CPU regressions passed, including new checks that production carries exactly 8192 and trials keep 0.

Source idea: an lcz.me report measuring llama.cpp `--cache-ram` on multi-document switching ([topic 2591](https://lcz.me/topic/2591)). [Numeric record](validation-results/20261107-bolt-prompt-cache.json).
