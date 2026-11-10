# HyperQwen `9268d8d` → `80cf059` — November 9, 2026 (evening)

Second hands-on install of the day ([runbook](../ENGINE-UPDATE-RUNBOOK.md)). Upstream moved 35 commits, almost all RTX 20-series (Turing, sm75) work. vLLM stays 0.33.0 and `docker/requirements.txt` is unchanged, so no dependency moved. The patch series grows from 58 to 65 patches plus the same 4 KVarN patches; all 69 applied (some at an offset, none failed).

| `qwen27b-hyperqwen` | Short DSH | Prefill tok/s | TTFT s | Decode tok/s |
| --- | --- | --- | --- | --- |
| before (`9268d8d`) | pass | 2091.2 | 2.80 | 62.9 |
| after, first load (`80cf059`) | pass | 2094.6 | 2.80 | 62.7 |
| after, repeat | pass | 2092.0 | 2.80 | 62.6 |

Kept. Parity within run-to-run noise. Rollback script and the previous environment: `data/hyperqwen-update-20261109b/`.

## Review before the swap

Three read-only reviewers read the upstream diff and the production launch, and each finding was re-checked by a second reviewer.

- The seven new patches are inert on these cards as launched: `flashinfer-sm75-optin`, `flashinfer-sm75-spec-graphs` and `gdn-sm75-cuda-prefill` need an environment switch and (for two of them) exactly sm75; `dflash2-fp16-residual-scale` and `spec-attn-fp16` only act on an fp16 model (this profile runs bf16); `terminal-request-progress` needs `VLLM_TERMINAL_PROGRESS=1`; `vllm-pr66026-gather-draft-sampled-no-specialize` only touches the speculative-decoding draft kernel, and this profile runs without speculative decoding.
- Production runs `runtimes/env-hyperqwen/bin/vllm` directly with arguments from `config/maintained-profiles.json`. It uses none of the upstream launchers, so the launcher, Docker and `SPEC`/`CTX` default changes do not apply. Nothing besides the environment and the pin needed updating.
- Four new environment variables enter vLLM's compile-cache key, so the reviewers expected one cold compile on the first load. The first check after the swap showed no measurable slowdown.
