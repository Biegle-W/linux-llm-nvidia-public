# DSH HyperQwen search entry — November 1, 2026

DSH web and headless profiles expose one HyperQwen choice: **Qwen3.8-27B / HyperQwen-vLLM + Web Search (free)**, using `qwen27b-hyperqwen-search`. The plain picker entry is removed. The underlying `qwen27b-hyperqwen` backend remains registered in the router; the search alias shares its worker, weights, context and resource guards.

Registration preserves custom provider settings and other models, migrates a default selection that referenced the removed plain entry, and does not recreate the duplicate when run again. The live settings were applied without restarting DSH or interrupting inference. Two focused regression tests passed, covering preservation, selection migration and repeated registration.

The initial checks above verified registration only. Later harness integration found and fixed the Chat Completions versus Responses mismatch; see [router cleanup and actual harness scope](DSH-ROUTER-CLEANUP-20261101.md).
