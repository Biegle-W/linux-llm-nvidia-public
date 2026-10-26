# Native validation - October 26, 2026

Ubuntu 26.04 runs the RTX 3080 Ti / RTX 3080 pair on distribution NVIDIA driver
595.99.02. CUDA toolkit 12.4 and GCC 13 built llama.cpp at
`caa8191df159f764fb0160e3d2fc6be008948aee` for architecture 86.
Thirty-one focused FP32/FP16/BF16 matrix tests passed on each GPU. A short
two-GPU inference check and authenticated streamed API check passed. The small
installation-test model was subsequently removed at the user's request.

The initial setup completed successful authenticated API smoke checks for
Strata Qwen3.8-Flash-Next IQ3_XXS, Maya GLM-5.3-Flash S24, Strata DeepSeek
IST-DAS 2.00 bpw and Maya DeepSeek Maya-S. These are installation checks;
they do not establish full-context quality or sustained throughput.

## Shared DeepSeek weights

Strata engine 0.1.51 successfully loaded the existing
DeepSeek-V4.1-Flash-1017 Maya-S GGUFs through a separate Strata index.
The pack check found every referenced file present and long enough, with no
unsupported GPU tensor types. It references only Maya's model directory and
its adjacent drafter and vision files; no weight copy or conversion was needed.

Strata rejected unauthenticated requests and completed streamed generation.
Additional deterministic checks passed:

- `37 + 58` returned `95`.
- A JSON-only addition request returned `{"sum": 12}`.
- A conversation reference-code request returned `MAPLE-731`.

The shared Strata profile uses both GPUs, all six routed experts per token,
an 8192-token allocated context and 2048 MiB VRAM reserve per GPU. Drafting and
vision are disabled in that profile. The checked prompts were short; the full
allocated context, image handling, drafting, tool calls and sustained thermals
have not been validated by these checks.

After these tests the separate IST-DAS weight set (256.82 GB) and its old index
were removed. Verified hashes, source revision, original paths and retired
settings were retained in ignored private data. Strata then passed a fresh
restart and authenticated streamed generation with the separate files absent;
Maya independently passed its authenticated streamed generation check afterward.
Raw output remains in `data/`
and `logs/`. Compute unlock, P2P-driver changes and reboots were not performed.
