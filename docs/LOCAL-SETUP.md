# Native setup

The initial runtime is llama.cpp at commit
`caa8191df159f764fb0160e3d2fc6be008948aee`, built for Ampere CUDA architecture 86.
The small Qwen2.5 installation-test model and its dedicated launcher were removed
at the user's request after the initial smoke checks. Historical test evidence
remains in ignored `data/` and `logs/`.

## Dependencies and build

On Ubuntu, install these packages:

```bash
sudo apt-get install -y --no-install-recommends gh cmake ninja-build \
  python3-venv libcurl4-openssl-dev nvidia-cuda-toolkit gcc-13 g++-13
./scripts/build_native_llama.sh
```

GCC 13 is selected explicitly for the distribution's CUDA 12.4 toolkit.
The driver-reported CUDA version is its compatibility ceiling; it is not the
installed toolkit version. This build uses layer splitting without NCCL.

The initial setup does not enable compute unlock, install a P2P driver, change
boot arguments, mount model storage, or configure remote access. Follow the
migration handoff after retaining a stock baseline. The user controls reboots.
Raw local inventory, hashes, build logs and smoke-test results belong in ignored
`data/` and `logs/`.

## Requested large-model setup

The October 26 setup queue completed all four initial API checks and left Qwen
as the default. DeepSeek now uses one shared Maya-S weight set with separate
engine indexes. Read the actual stage and individual API-check results:

```bash
python3 data/show-setup-status.py
cat data/model-setup-state.json
```

| Engine | Model | Selected pack | Approximate download |
| --- | --- | --- | ---: |
| Strata | Qwen3.8-Flash-Next | ISTA-DASLab IQ3_XXS, MTP and CPU vision | 82 GB |
| Maya | GLM-5.3-Flash | Maya-S24 | 95 GB plus vision |
| Strata and Maya | DeepSeek-V4.1-Flash-1017 | Shared Maya-S | 339 GB plus drafter and vision, downloaded once |

Strata's small index points directly to Maya's existing GGUFs, drafter and vision
files. Maya keeps its own index. The separate 256.82 GB IST-DAS set was removed
after Strata passed streaming, authentication, arithmetic, JSON and conversation
checks on Maya-S. Its verified hashes and retired settings are retained privately
in `data/retired-strata-ista-20261026/`.

Both DeepSeek configurations stream experts from NVMe because the full expert
banks exceed this machine's RAM.
The distribution driver remains installed. Compute unlock is now verified on
both cards; P2P is not enabled. See the
[unlock setup](UNLOCK-SETUP-20261026.md).

After setup finishes, start a configured model with one of:

```bash
./scripts/start_model.sh qwen
./scripts/start_model.sh glm
./scripts/start_model.sh strata-deepseek
./scripts/start_model.sh maya-deepseek
```

Each uses the same authenticated localhost port 10000 and the key from
`data/local-api-key`. The launcher refuses a second worker while that port is
occupied or while the setup queue is active. Stop Qwen with
`runtimes/bin/strata launch --stop --preset qwen-flash-next`. Stop Strata DeepSeek
with `runtimes/bin/strata runtime stop --profile deepseek-maya-s`.
Stop a foreground Maya server with Ctrl+C.
The initial allocated contexts are 32K for Qwen and Maya, and 8K for Strata
DeepSeek. Short API smoke checks do not validate those full input lengths or
establish sustained performance, output quality, image handling or tool use.
The shared Strata DeepSeek profile currently disables drafting and vision;
their file formats being recognized does not establish those features work.

## Speed measurements

[The October 26 benchmark](BENCHMARK-20261026.md) records three short and three
longer requests per model/engine, with 128-token outputs and an 8K context
allocation. DeepSeek used the same Maya-S weights and matched requested settings
on Strata and Maya. Temporary benchmark configs left the installed profiles
unchanged, and Qwen was restored afterward. Raw timing events and resource samples
are retained under ignored `data/benchmarks/`.

[The unlocked-versus-stock comparison](BENCHMARK-UNLOCK-20261026.md) records the
repeated protocol after successful per-card unlock and correctness checks.

[CUDA engine qualification](ENGINE-TESTS-20261026.md) records mixed-card
compatibility failures, HyperQwen CPU-offload timings, and the memory-pressure
incident. Run future experimental workers through `scripts/run_bounded_test.sh`
to give them a separate process group and a hard host-memory limit.
