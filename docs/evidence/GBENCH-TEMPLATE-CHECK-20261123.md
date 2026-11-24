# gBench chat-template check added to engine updates — November 23, 2026

At the owner's request the six chat-template and tool-call cases of Google DeepMind's [gBench](https://github.com/google-deepmind/gbench) Golden Set (v0.5.0.post1) now run after the short DSH check on every engine update: `python3 scripts/gbench_template_check.py --model PROFILE`.

## What it adds

Two pairs of chat-template cases each send structured history (a replayed tool call and tool result, or a five-turn conversation) and a "twin" with the same content as one plain user message. If the structured case fails and its twin passes, the engine's chat template or message serialization is broken, not the model. All four also fail if template tokens leak into the answer. Two tool-call cases check native OpenAI `tool_calls`. The DSH check covers tool calling but cannot tell a template break from a weak answer.

## How it runs

- The router selects the profile and a warm-up request is sent first: gBench allows a fixed 30 s per request, so a cold load would fail. Warm-up time is not part of the check.
- gBench then runs the six cases against the router (`/v1`, key from the environment, Hugging Face offline) and must finish within 120 s. The verdict is PASS only if gBench exits 0 inside the limit and each case passes exactly once. The router unloads afterwards; a failed unload fails the check.
- Tokenizers (for the template-token leak check) come from each model's official Hugging Face repo at a pinned revision, under `models/tokenizers/`; gBench and `transformers` sit in `runtimes/gbench/0.5.0.post1/venv`. One-time setup: `python3 scripts/gbench_template_check.py --setup`. Settings: `config/gbench-template-check.json`.
- Results, including answer text, stay in `data/gbench-template/` and are not committed or exported. The router key is scrubbed from the saved log.
- Not used: the rest of gBench. Its agentic suite and about 25 academic suites need a Gemini key (prompts leave the machine), many need Docker or vLLM, and its stress test assumes a multi-slot server.

## Baseline (all router entries, one at a time)

| Profile | Engine | Load and warm-up (s) | gBench run (s) | Cases |
|---|---|---:|---:|---|
| `flash-next-strata` | Strata | 30.8 | 8.5 | 6/6 |
| `flash-next-iq4xs-strata` | Strata | 33.8 | 10.2 | 6/6 |
| `qwen27b-hyperqwen` | HyperQwen | 75.4 | 3.3 | 6/6 |
| `qwen27b-sglang` | SGLang | 58.9 | 3.5 | 6/6 |
| `glm-maya` | Maya | 40.8 | 17.1 | 6/6 |
| `deepseek-maya` | Maya | 25.9 | 43.2 | 6/6 |
| `deepseek-unsloth-strata` | Strata | 21.2 | 36.5 | 6/6 |
| `inkling-llamacpp` | llama.cpp | 47.7 | 16.4 | 6/6 |
| `hy4-flash-strata` | Strata | 121.5 | 26.3 | 6/6 |
| `hy4-flash-maya` | Maya | 438.9 | 32.5 | 6/6 |

No request was retried or timed out. GPUs idle and unlock VERIFIED before and after.
