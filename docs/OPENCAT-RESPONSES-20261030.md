# OpenCat Responses compatibility — October 30, 2026

OpenCat on iPhone could fetch the model catalog but its OpenAIResponses provider received `not_found: Unknown endpoint` when chatting. The router exposed Chat Completions but omitted `POST /v1/responses`. A direct request proved the installed HyperQwen backend already supported Responses. Native Responses pass-through is now deployed through the same authenticated router and guarded worker lifecycle. [Verification](validation-results/20261030-opencat-responses.json).

The Responses API has typed streaming events, including `response.created`, `response.output_text.delta` and `response.completed`, rather than Chat Completions chunks. The router preserves these native events, rewrites public model aliases in nested response lifecycle objects, and emits typed Responses errors for upstream failures. It does not convert Responses payloads into Chat Completions or replace native tool/content handling. See the [official streaming specification](https://developers.openai.com/api/docs/guides/streaming-responses).

Input messages, output-token limits, tools and other Responses fields pass through to the selected native backend. Authentication, network access rules, model selection, FIFO admission, concurrency, resource guards and idle behavior are unchanged. This exposes response creation; it does not claim every backend supports every Responses storage, hosted-tool, retrieval or cancellation feature. No model, quantization, runtime or context was changed.

## Verification

All 232 CPU regressions passed, including 47 router tests. New checks cover Responses input/tool forwarding, public aliases, typed streaming completion, typed upstream errors and credential redaction. Optional protocol diagnostics are default-off and record only HTTP method, allowlisted endpoint shape and status, never conversation content, credentials, queries or client identities. Existing CPU switch fixtures now mock detection so they cannot depend on a live GPU worker.

Live HyperQwen requests passed for loopback non-streaming, loopback streaming and Tailscale streaming. Each returned HTTP 200 and the expected answer; streaming included typed completion events. The loaded model worker was not restarted. These small synthetic checks establish API transport compatibility, not benchmark performance. Direct iPhone end-to-end confirmation remains pending the user's retry.

The API base remains the router's `/v1` base on port 10100. OpenCat's Responses provider can use `/v1/responses`; Chat Completions remains available at `/v1/chat/completions`. No change of API key is required. Native backend capabilities still apply; only HyperQwen was newly verified live for Responses in this repair.
