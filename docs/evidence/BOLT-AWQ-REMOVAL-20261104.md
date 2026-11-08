# Retired Bolt AWQ deleted — November 4, 2026

At the user's request, the retired Bolt AWQ checkpoint, its dedicated vLLM environment and obsolete serving adapters are deleted. The selected native IQ2/llama.cpp Bolt entry remains under the compatibility ID`bolt-vllm`. All nine selected profile definitions are byte-for-byte unchanged; API and both DSH modes still identify Bolt as native IQ2. Credentials, resource guards, defaults and unrelated routes remain unchanged.

Removed the27 AWQ weight shards totaling55,332,700,488 bytes, their tokenizer/configuration files, the dedicated SATA directory and its repository symlink, and `runtimes/env-bolt-vllm-031`. Inventory totals are approximately55.36 GB for the complete model directory and8.36 GB for the dedicated runtime; they are logical inventory sizes, not guaranteed free-space changes on shared/hardlinked filesystems.

The AWQ-only manifest, launcher, supervisor, four offload-hook modules and four obsolete test modules were removed from both repositories. The exporter now explicitly retires those paths instead of recreating them. The obsolete generic vLLM-offload updater exception was removed; its coverage fixture now tests the selected native pinned Bolt runtime. Updates remain paused.

Before deletion, all selected checkpoint locations and maintained-runtime symlinks were checked for dependencies on the retired assets. No readable live process had a command, mapping or open descriptor referencing the exact retired model/runtime roots. Deletion was scoped to those verified owned roots; no job was stopped. Small source/configuration preimages and pinned-source hashes were retained privately. No replacement copy of the deleted weights or environment was made. Existing Git history and dated benchmark evidence remain available.

The native executable and all pinned library hashes still match, and its dynamic dependencies resolve after removal. The authenticated API lists nine models with native IQ2/llama.cpp Bolt, both DSH modes retain its native label and all three API/hub/DSH services are healthy.423 remaining CPU tests passed;33 AWQ-only tests were retired with the deleted adapter. No inference benchmark or fallback model load was repeated for this removal.

[Deletion and verification summary](validation-results/20261104-bolt-awq-removal.json), [selected native setup and preserved AWQ diagnosis](BOLT-IQ2-ENTRY-20261104.md), [current benchmarks](ALL-ENTRY-BENCHMARKS-20261104.md).
