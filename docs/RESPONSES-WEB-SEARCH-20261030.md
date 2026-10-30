# Local Responses web search — October 30, 2026

**OpenCat follow-up:** The phone was observed to send an empty tool list. Select `qwen27b-hyperqwen-search` to opt into server-side search; see [the verified compatibility repair](OPENCAT-SEARCH-MODEL-20261030.md).

**Implemented, deployed and live-tested with free keyless search.** The router
uses Mwmbl's anonymous public API, supplies untrusted result snippets to the
selected local model, and returns a `web_search_call`, a generated answer,
clickable links and URL citation annotations. Inference stays local. This is
a local Responses compatibility implementation, separate from OpenAI's hosted
search service.

All **250 CPU tests pass**. Live HyperQwen requests passed over loopback in
nonstreaming and streaming modes, and over Tailscale in streaming mode. Each
searched the real anonymous API, correctly described SearXNG from the retrieved
snippets, and returned valid citations to those results. The measured request
times were **1.981 s**, **1.506 s**, and **2.176 s**, respectively. Source-domain
filters also passed. DSH and the existing worker service invocation were
preserved. Direct confirmation from the OpenCat iPhone UI remains pending.

## OpenCat usage

Keep the same router base URL, model and local bearer credential. Enable the
web-search tool in OpenCat so its Responses request includes `web_search` or
`web_search_preview`. No search API key, signup or payment is needed. Dated
variants `web_search_2025_08_26` and `web_search_preview_2025_03_11` work too.

```json
{
  "model": "qwen27b-hyperqwen",
  "input": "SearXNG",
  "tools": [{"type": "web_search"}],
  "tool_choice": "auto",
  "include": ["web_search_call.action.sources"],
  "stream": true,
  "store": false
}
```

With a search tool enabled, `auto`, `required` and an explicit search tool
choice perform one search of the latest user text, normalized and capped at
512 characters. This implementation does not do model-directed multi-step
browsing. `tool_choice: "none"`, a forced function tool choice, or requests
without a search tool perform no search. Remaining function tools and explicit
inference options survive; the search tool is removed before native generation.

`search_context_size` selects up to 3/5/8 snippets for low/medium/high.
`filters.allowed_domains` accepts bare domains and their subdomains and is
enforced locally on Mwmbl results. No unsupported `site:` operator is sent to
Mwmbl. `include: ["web_search_call.action.sources"]` exposes the returned
source URLs. Actual model `[n]` citation markers map to retrieved sources with
text offsets; out-of-range markers do not get invented URL annotations. The
model is instructed to include clickable Markdown links and acknowledge when
snippets do not answer the question. Valid citation URLs do not prove every
generated claim.

Stored conversation IDs, location-specific search, blocked-domain filters,
offline/cache-only search and unknown search-tool options return a clear 400.
Inline conversation input is accepted, but only the latest user text is sent
to search. Native Responses capabilities still depend on the chosen backend;
live verification here used HyperQwen, not every maintained engine.

## Free provider and availability

Mwmbl's documented anonymous allowance is **1,000 requests/month per IP** and
**one request/second**, with no key or signup. The router spaces its Mwmbl
requests by at least 1.05 seconds. It uses one fixed HTTPS endpoint, a 15-second
timeout, a 512 KiB response cap and at most eight returned sources. It never
retries a quota failure in a loop or switches to a paid API automatically.

Mwmbl has a smaller independent index and short snippets; some questions will
have limited coverage, stale results or no matching source after filtering.
Quota exhaustion, unavailable search and empty matching results produce an
explicit `web_search_unavailable` error, not an invented search-backed answer.
There is no promise of unlimited searches or comprehensive real-time coverage.

The default and installed local configuration are:

```json
{"provider":"mwmbl"}
```

The installed selection lives in ignored `data/router/web-search.json` and is
read per request; `config/web-search.example.json` documents the default.
The existing DuckDuckGo provider remains available as an explicit alternative,
but its bot challenges made it unsuitable for the current default. The earlier
Brave implementation is unselected, has no credential configured, and has made
no paid request. The current selected setup needs no search credential.

## Streaming and safeguards

Streaming emits typed lifecycle/search events and then relays native model
tokens. A stable response ID, increasing sequence numbers and shifted output
indices account for the inserted search item. Annotation events and completed
message content agree on citation URLs and character ranges. A native stream
ending before a terminal event produces an explicit error. Provider failure
uses HTTP 503 for nonstreaming requests, or a typed SSE `error` after streaming
headers have been sent.

Authentication, network restrictions, FIFO admission, one execution slot,
worker ownership, resource guards, model settings, contexts and idle policy
are preserved. Search happens inside the admitted operation. Ordinary native
Responses and Chat Completions retain their transport. Deployment reloaded only
the idle router; the worker and DSH service invocations remained unchanged.
No model benchmark, cache change or resource-guard change was performed.

Only the latest query and explicit anonymous provider headers are sent to
Mwmbl. Prior messages, instructions, images, client cookies, the local API key
and client headers are not sent. Redirects are disabled. Result pages are not
fetched, snippets are marked as untrusted model input, and no persistent
query/result cache is added.

## Verification history

The first implementation passed 247 CPU tests and one live DuckDuckGo
nonstreaming search. Repeated DuckDuckGo challenges then blocked streaming.
The user explicitly selected a free service without a key. Mwmbl replaced
DuckDuckGo as the default, three additional provider tests passed, and all
three real router/network checks then succeeded. The earlier challenge results
remain historical evidence and are not relabeled as successful tests.

Remaining user-facing confirmation: retry a web-search conversation in OpenCat
on the iPhone. API/network verification is complete; phone UI behavior has not
been observed directly.

Sources: [Mwmbl anonymous API and limits](https://developer.mwmbl.org/),
[Responses web-search protocol](https://developers.openai.com/api/docs/guides/tools-web-search).
See [numeric verification](validation-results/20261030-responses-web-search.json).
