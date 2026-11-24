# Linux LLM NVIDIA — public reference

A home LLM server on native Linux with two consumer GPUs: an **RTX 3080 Ti (12 GB)** and an **RTX 3080 (10 GB)**, no peer-to-peer link between them, 92 GiB of RAM, an NVMe system drive and a SATA SSD for model weights. One authenticated, OpenAI-compatible router serves **nine text models**, loading one at a time on demand. Large mixture-of-experts models run by keeping the busy parts on the GPUs and the rest in RAM or streamed from SSD. RAM, VRAM, swap, memory-pressure and temperature guards stop a worker when it starts to starve the machine. Engine updates are researched, installed and checked by hand before they are kept. ComfyUI adds image and video generation.

This repository is the curated public export of the private operational repository. Everything here is kept current with the live server: models, engines, test results and the procedures used to produce them.

**Start here:** [docs/CURRENT-STATE.md](docs/CURRENT-STATE.md) (what is live now) · [docs/README.md](docs/README.md) (all documents) · [docs/HISTORY.md](docs/HISTORY.md) (dated change log)

## Models on the router

Speeds are from the latest short check through the router: one real tool call from the web client, a 5.6-7K-token prompt, load time excluded. Generation is tokens per second while writing; prompt reading is tokens per second while reading the prompt.

| API id | Model and weights | Engine | Context | Prompt reading (tok/s) | First token (s) | Generation (tok/s) |
|---|---|---|---:|---:|---:|---:|
| `qwen27b-hyperqwen` | Qwen3.8 27B, AutoRound INT4 | HyperQwen (vLLM 0.33.0) | 86,016 | 2,092 | 2.8 | 62.6 |
| `qwen27b-sglang` | same weights | SGLang | 57,344 | 2,130 | 2.9 | 60.1 |
| `flash-next-strata` | Qwen3.8 Flash Next 125B-A6B, IQ3_XXS (default Flash-Next) | Strata 0.2.21 + MTP | 131,072 | 1,270 | 4.5 | 69.0 |
| `inkling-strata` | Inkling 2 Mini 26B, Strata SQ-10, both cards | Strata 0.2.21 (`strata-inkling`) | 131,072 | 2,129 | 3.4 | 66.9 |
| `glm-maya` | GLM-5.3 Flash 320B-A18B, Maya-S24 | Maya 1.1.78 | 65,536 | 541 | 10.2 | 14.2 |
| `deepseek-maya` | DeepSeek V4.1 Flash, Unsloth UD-IQ1_S | Maya 1.1.78 | 32,768 | 180-211 | 29-33 | 7.7-9.0 |
| `deepseek-unsloth-strata` | same weights | Strata 0.2.13 (frozen: later Strata dropped DeepSeek) | 32,768 | 87 (cold; 28 with prompt reuse) | 65.6 (6.0) | 12.0 |
| `hy4-flash-strata` | Tencent Hy4-Flash 220B-A12B, SQ-96 | Strata 0.2.21 (Hy4 engine) | 131,072 | 213 | 26.4 | 23.7 |
| `hy4-flash-maya` | Tencent Hy4-Flash, Maya-L, both cards | Maya 1.1.78 (Hy4 engine) | 131,072 | 26 | 209 | 15.6 |

Weights, drives and sizes per entry are in [docs/CURRENT-STATE.md](docs/CURRENT-STATE.md); the registry itself is [config/maintained-profiles.json](config/maintained-profiles.json).

## Test results

**Short tool-use test** (run once for every new model or new weights). 49 tool-calling items in 15 minutes for smaller models, 55 items in at most an hour for larger ones. One run is accurate to about ±17 points (smaller) or ±13 (larger), so neighbouring scores are not a reliable order. [How it works](docs/QUALITY-FAST-TEST-PLAN.md)

| API id | Group | Score |
|---|---|---:|
| `qwen27b-hyperqwen` | smaller | 66.0 |
| `deepseek-unsloth-strata` | larger | 64.7 |
| `deepseek-maya` | larger | 63.5 |
| `qwen27b-sglang` | smaller | 61.7 |
| `glm-maya` | larger | 60.4 |
| `inkling-strata` | smaller | 59.3 |
| `hy4-flash-strata` | larger | 57.9 |
| `hy4-flash-maya` | larger | 43.3 (stopped by the memory-pressure guard at minute 30) |
| `flash-next-strata` | smaller | 40.6 |

**Trials not on the router:** Kolibri 1.1 (Aleph Alpha, 75B MoE with 3.4B active) in Q5_K_M on a llama.cpp build from the unmerged pull request 32891, both cards with 10 layers of experts on the GPUs and the rest in RAM, 131,072 context. Short tool-use test 41.8 with thinking off (60.0 at medium thinking), generation 44 tok/s on short prompts falling to 11 tok/s at 111K tokens, prompt reading 1,030-1,230 tok/s, long-context recall correct up to 119K tokens. [Details](docs/evidence/KOLIBRI-1.1-TRIAL-20261124.md)

**390-item quality test** (November 10-18; MMLU-Pro, AIME 2025, LiveCodeBench, BFCL single- and multi-turn; thinking off as served). Macro score: DeepSeek on Strata 73.0%, DeepSeek on Maya 72.4%, Qwen 27B on SGLang 68.1% and on HyperQwen 68.0%, Flash-Next UD-IQ4_XS 65.5% (entry retired November 24), Flash-Next IQ3_XXS 62.0%, GLM 57.2%. Entries added later have the short test only; the Inkling 2 Mini trial outside the router scored 60.0% with thinking on. [Full results](docs/evidence/QUALITY-BENCHMARK-20261111.md)

**Checks on every engine update**, one entry at a time:
1. a short check through the web client before and after the swap: a real tool call and follow-up, with prompt-reading, first-token and generation speed;
2. right after it, the six chat-template and tool-call cases of Google DeepMind's gBench Golden Set, after a warm-up, within 120 s. A structured case failing while its plain twin passes points to a broken chat template or message serialization. All entries passed 6/6 at baseline ([details](docs/evidence/GBENCH-TEMPLATE-CHECK-20261123.md)).

A new version is kept unless it really breaks something: a failed load, check or unload, invalid output, less than half the speed or more than three times the wait for the first token. Smaller slowdowns are recorded as warnings. [Runbook](docs/ENGINE-UPDATE-RUNBOOK.md) · [update log](docs/DAILY-ENGINE-UPDATES.md)

## How it works

- **Router** (`network/`, port 10100 on loopback and Tailscale): authenticated OpenAI-compatible API (Chat Completions with streaming and tool calls). The model id selects model, weights and engine together. One request runs at a time, up to eight wait in order; a request for an unloaded model loads it first. Idle models unload after 10 minutes. [network/README.md](network/README.md)
- **Engines:** HyperQwen (a patched vLLM) and SGLang for the dense Qwen 27B; Strata for Flash-Next, Inkling, Hy4 and the frozen DeepSeek build; Maya for GLM, DeepSeek and Hy4. Each engine version, binary hash and local patch is pinned in `config/`.
- **Memory layout:** Qwen 27B and Inkling 2 Mini fit entirely in VRAM across both cards. The large MoE models keep attention and part of the experts on the GPUs and the rest in RAM or streamed from NVMe/SATA (`hy4-flash-strata` runs on the 12 GB card with all experts in RAM). Flash-Next uses a hand-tuned layer split between the 12 GB and 10 GB cards; other two-card entries use the engine's automatic split. No entry needs a GPU-to-GPU link.
- **Guards:** every worker runs in a systemd scope with a RAM budget (87.77 GiB soft, 89.77 GiB hard, 2 GiB host reserve; `hy4-flash-maya` has its soft cap at the hard limit). It is stopped on sustained swap writes, full memory pressure above the entry's limit (10-15%), too little free VRAM (per-entry floor, 256 MiB for most) or GPU temperature. [Swap and pressure policy](docs/INFERENCE-SWAP-POLICY.md)
- **GPU unlock health:** a boot and package-update service checks that the GPU unlock is still in place after kernel or driver changes. Inference work starts only when it reads VERIFIED. [GPU-UNLOCK-HEALTH.md](docs/GPU-UNLOCK-HEALTH.md)
- **Web client:** DeepSeek Harness (`dsh/`) lists the router's models. Selections of retired entries move to their replacement.
- **Storage:** weights live on the NVMe (streamed MoE models) or the SATA SSD. `scripts/weights_tracker.py` reports what every file is used by. When a new model needs room, weights of retired entries go first. [STORAGE-POLICY.md](docs/STORAGE-POLICY.md)
- **Images and video:** ComfyUI entries for Qwen Image 2.1 Turbo, FLUX.3 Klein and MiniMax H3 Image, plus Wan 2.2 5B and LTX 2.3 video, run from desktop launchers. Generated samples are in [assets/samples/comfy](assets/samples/comfy/README.md).

## Using the API

Base URL `http://127.0.0.1:10100/v1` (or the server's Tailscale address), with `Authorization: Bearer <local key>`. `/v1/models` lists the enabled entries. The first request to an unloaded model waits for it to load (seconds for most, minutes for the largest), so use long client timeouts.

```python
import os
from openai import OpenAI

client = OpenAI(base_url="http://100.x.y.z:10100/v1", api_key=os.environ["LOCAL_LLM_API_KEY"], timeout=7200)
reply = client.chat.completions.create(model="flash-next-strata", messages=[{"role": "user", "content": "Hello"}])
print(reply.choices[0].message.content)
```

`POST /router/select {"model": "<id>"}` preloads a model; `POST /router/unload {}` unloads an idle one; `/health` shows in-flight and queued requests.

## Layout

| Path | Contents |
|---|---|
| `config/` | Model registry (`maintained-profiles.json`), engine and weight pins, engine-update and inference policy, gBench check settings |
| `scripts/` | Launchers, guards, runtime checks, engine-update tools, benchmarks, quality checks, public export |
| `network/` | Router, private model hub, worker manager, installer |
| `dsh/` | Web client registration and launcher |
| `tests/` | CPU unit tests: `python3 -m unittest discover -s tests -q` |
| `docs/` | Current state, policies, runbooks; one dated evidence file per piece of work in `docs/evidence/` |
| `patches/`, `tools/`, `tooling/`, `assets/` | Engine patches, small native tools, vendored tooling, icons and generation samples |

`data/`, `models/`, `runtimes/` and `logs/` hold weights, engines, keys and raw results; they stay on the server and are never committed or exported.

## Repositories

| Build | Private operational repository | Public reference |
|---|---|---|
| Linux NVIDIA | [linux-llm-nvidia](https://github.com/Biegle-W/linux-llm-nvidia) | [linux-llm-nvidia-public](https://github.com/Biegle-W/linux-llm-nvidia-public) |
| Linux AMD | [linux-llm-amd](https://github.com/Biegle-W/linux-llm-amd) | [linux-llm-amd-public](https://github.com/Biegle-W/linux-llm-amd-public) |
| Windows NVIDIA | [windows-llm-nvidia](https://github.com/Biegle-W/windows-llm-nvidia) | [windows-llm-nvidia-public](https://github.com/Biegle-W/windows-llm-nvidia-public) |
| Retired settings | [retired-llm-setting](https://github.com/Biegle-W/retired-llm-setting) | Private only |

Public references are curated exports with their own history; private history is never merged into them. See [docs/REPOSITORY-MAP.md](docs/REPOSITORY-MAP.md).
