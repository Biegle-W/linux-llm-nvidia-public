# Nemotron Super removed — November 1, 2026

At the user's request, all installed Nemotron Super model variants were removed. Seven maintained profiles remain: HyperQwen, SGLang, Flash-Next/Strata, GLM/Maya, DeepSeek/Maya, DeepSeek/Strata and Nemotron Bolt. Bolt and shared router/runtime components are preserved.

Removed the W4A16-Merlin production checkpoint and symlink, the experimental UD-Q4_K_XL GGUF shards and rejected partial shard, the dedicated Super vLLM environment, processed-offload directory and exclusive experimental build/pack assets. The separate LiLiCorr model was preserved. The deletion inventory recorded **229.168 decimal GB of allocated data**; this counts filesystem allocation, not only base model weights, and is not a guarantee of the same free-space delta on filesystems with sharing or delayed reclamation.

The production profile, CLI route, supervisor, pinned runtime manifest, offload hook and Super-only tests were retired. The updater no longer lists Super as a pinned profile. DSH web/headless catalogs drop the retired IDs; saved local Super selections migrate to plain HyperQwen metadata without loading it. Unrelated custom/external routes remain. The public export policy removes retired source files instead of reintroducing them.

The live authenticated API lists exactly seven retained profiles. Explicit selection of both `super-vllm` and `super-strata-trial` returns HTTP 404. Both model worker units are inactive; no GPU reservation remains. No model benchmark or fallback load was repeated. Resource guards, credentials and all seven retained profile settings are unchanged.

Historical benchmark reports, numerical evidence and private settings preimages remain dated records. Their Super rows do not describe a currently installed model.

CPU regression validation: **402 of 403 tests passed** in the retained Torch-enabled environment. The one error is the pre-existing updater catalog-coverage mismatch; the removed obsolete Super-policy test is no longer part of the active suite. The retirement-specific catalog/selection migration regression passed.
