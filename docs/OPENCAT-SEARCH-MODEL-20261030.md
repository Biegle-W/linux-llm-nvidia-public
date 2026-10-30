# OpenCat search model entry — October 30, 2026

OpenCat's phone request reached `POST /v1/responses` with streaming enabled,
inline input items, **`tools: []`** and `tool_choice: "auto"`. No search tool or
search-options field was present. The router therefore forwarded an ordinary
native request, and the model replied without searching. Earlier tests that
explicitly supplied `web_search` verified the API feature, but did not reproduce
this phone request shape.

The router now exposes an explicit opt-in catalog entry:

**`qwen27b-hyperqwen-search` — HyperQwen + Web Search (free)**

In OpenCat, refresh the model list and select this ID in the existing provider.
Keep the current base URL, local API credential and Responses API setting. This
model entry inserts the web-search tool on the server when the client supplies
an empty tool list. It uses the selected free anonymous Mwmbl service and returns
normal Responses search events, answer text, source links and citation annotations.
No search-provider API key, signup or payment is needed.

The regular `qwen27b-hyperqwen` entry keeps its current behavior. Search-enabled
and regular entries resolve to the **same existing HyperQwen worker/profile**;
there is no duplicate worker, context allocation, model load or profile setting.
The catalog now has seven entries backed by six maintained profiles. Responses
retain the requested public model ID, while admission and worker ownership use
the original profile ID. This preserves same-worker queueing and guards.

An explicit `tool_choice: "none"` still disables search. Forced non-search
function choices are respected. The search entry requires `/v1/responses`;
requesting it through Chat Completions returns a clear unsupported-endpoint error.
Other maintained backends have no new search alias and were not GPU-tested here.

## Verification

All **255 CPU tests passed**. Five new checks cover catalog discovery/context,
the phone's empty-tools input shape with streaming and nonstreaming, public alias
rewriting, base worker acquisition, search opt-out, regular-entry behavior,
endpoint rejection before acquisition and explicit model selection.

Real anonymous web search through the new model entry also passed:

| Network | Mode | Time | Result |
| --- | --- | ---: | --- |
| Loopback | Nonstreaming | 1.719 s | Completed; grounded answer and citations |
| Loopback | Streaming | 1.810 s | Typed search events, native text deltas and citations |
| Tailscale | Streaming | 2.613 s | Completed; stable response ID, ordered events and citations |

These requests used inline user input, **an empty client tool list** and automatic
tool choice, matching the relevant observed phone fields. The router injected
the tool because the new model ID opted in. The live question asked what SearXNG
is; returned snippets supported the generated metasearch explanation. The alias
was discoverable in `/v1/models`. Worker and DSH service invocations stayed
unchanged; only the idle router was reloaded.

The temporary trace recorded endpoint/tool-option shapes only, without message
text, instructions, credentials or client identifiers. It had an expiry, passed
privacy/expiry checks, and was removed from the production source afterward.
The original access configuration was restored byte-for-byte, with diagnostics
off. No model benchmark or resource-setting change was made.

Direct iPhone confirmation **after selecting the new model entry** remains
pending. The observed missing-tool problem is now covered by CPU and live API
tests; the phone UI itself has not been controlled or observed directly.

The selected provider's free quota, smaller index, short snippets and failure
behavior remain documented in [Responses web search](RESPONSES-WEB-SEARCH-20261030.md).
This feature performs search, not a full website crawl or comprehensive audit.
See [numeric verification](validation-results/20261030-opencat-search-model.json).
