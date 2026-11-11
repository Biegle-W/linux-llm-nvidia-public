# Linux LLM NVIDIA — public reference

Native Linux setup for a two-GPU (RTX 3080 Ti 12 GB + RTX 3080 10 GB) local LLM server. One authenticated OpenAI-compatible router serves several model/quant/engine entries, loading one at a time, with RAM/VRAM/swap/temperature guards and engine updates that are qualified by hand before promotion.

- **Current state, models and settings:** [docs/CURRENT-STATE.md](docs/CURRENT-STATE.md)
- **Operating rules and architecture for agents:** [AGENTS.md](AGENTS.md)
- **Network API, DSH client and desktop launchers:** [network/README.md](network/README.md)
- **All documentation:** [docs/README.md](docs/README.md); dated change log in [docs/HISTORY.md](docs/HISTORY.md)

## Using the API

Base URL `http://127.0.0.1:10100/v1` (or the server's Tailscale address), with `Authorization: Bearer <local key>`. `/v1/models` lists the enabled entries; the model id selects model, quantization and engine together. Chat Completions with streaming and tool calls are supported. First requests wait for the model to load, so use generous client timeouts.

```python
import os
from openai import OpenAI

client = OpenAI(base_url="http://100.x.y.z:10100/v1", api_key=os.environ["LOCAL_LLM_API_KEY"], timeout=7200)
reply = client.chat.completions.create(model="flash-next-strata", messages=[{"role": "user", "content": "Hello"}])
print(reply.choices[0].message.content)
```

## Layout

| Path | Contents |
|---|---|
| `config/` | Model registry (`maintained-profiles.json`), runtime pins, engine-update and inference policy |
| `scripts/` | Launchers, guards, engine-update check tools, benchmarks, public export |
| `network/` | Router, private model hub, worker manager, installer |
| `dsh/` | DeepSeek Harness client registration and launcher |
| `tests/` | CPU unit tests: `python3 -m unittest discover -s tests -q` |
| `docs/` | Current state and policies; dated evidence in `docs/evidence/` |
| `patches/`, `tools/`, `tooling/`, `assets/` | Engine patches, small native tools, vendored tooling, icons and samples |

`data/`, `models/`, `runtimes/` and `logs/` are local only and never committed.

## Repositories

| Build | Private operational repository | Public reference |
|---|---|---|
| Linux NVIDIA | [linux-llm-nvidia](https://github.com/Biegle-W/linux-llm-nvidia) | [linux-llm-nvidia-public](https://github.com/Biegle-W/linux-llm-nvidia-public) |
| Linux AMD | [linux-llm-amd](https://github.com/Biegle-W/linux-llm-amd) | [linux-llm-amd-public](https://github.com/Biegle-W/linux-llm-amd-public) |
| Windows NVIDIA | [windows-llm-nvidia](https://github.com/Biegle-W/windows-llm-nvidia) | [windows-llm-nvidia-public](https://github.com/Biegle-W/windows-llm-nvidia-public) |
| Retired settings | [retired-llm-setting](https://github.com/Biegle-W/retired-llm-setting) | Private only |

Public references are curated exports with independent history; private history is never merged into them. See [docs/REPOSITORY-MAP.md](docs/REPOSITORY-MAP.md).
