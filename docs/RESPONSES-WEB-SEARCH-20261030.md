# Local Responses web search — October 30, 2026

The router implements a bounded web-search tool for `POST /v1/responses`.
It searches the configured provider, gives the local model untrusted result
snippets, and returns a `web_search_call`, the model answer and URL citation
annotations. This is a local compatibility implementation, separate from
OpenAI's hosted search service. Inference stays on the selected local worker.

**Verification status:** CPU integration tests pass, and one live nonstreaming
HyperQwen request passed with real NASA search results, an answer about iron
oxidation, a clickable source link and a citation annotation. Subsequent live
streaming requests hit DuckDuckGo bot challenges. Streaming protocol behavior
passes with a mock search provider and worker; successful live streaming and
Tailscale search remain pending an available provider. Direct OpenCat iPhone
confirmation also remains pending. Do not describe this as reliably operational
web search until those remaining checks pass.

## Client usage

Keep the existing router base URL and local bearer credential. Enable OpenCat's
web-search tool so it sends `web_search` or `web_search_preview`. Dated variants
`web_search_2025_08_26` and `web_search_preview_2025_03_11` are accepted too.

```json
{
  "model": "qwen27b-hyperqwen",
  "input": "NASA Mars red",
  "tools": [{"type": "web_search"}],
  "tool_choice": "auto",
  "include": ["web_search_call.action.sources"],
  "stream": true,
  "store": false
}
```

When search is enabled, `auto`, `required` and an explicit search tool choice
perform one search of the latest user text, normalized and capped at 512
characters. The router does not implement model-directed multi-step browsing.
`tool_choice: "none"`, a forced function tool choice, or requests without a
search tool perform no search. Remaining function tools and explicit inference
options survive; search tools are removed before the native generation call.

`search_context_size` selects up to 3/5/8 snippets for low/medium/high.
`filters.allowed_domains` supports bare domains and their subdomains, enforced
against returned URLs. Requesting `web_search_call.action.sources` includes
retrieved result URLs. Citations map actual model `[n]` markers to those results,
with text offsets; no citation is invented for an out-of-range source marker.
The model is also instructed to use clickable Markdown links and acknowledge
insufficient snippets. Citation validity does not prove every generated claim.

Stored conversation IDs, location-specific search, blocked-domain filters,
offline/cache-only search and unknown search-tool options return a clear 400.
Inline conversation input is accepted; only its latest user text is searched.
Other native Responses capabilities still depend on the selected backend.

## Search provider configuration

With no local configuration, DuckDuckGo Lite is tried, followed by DuckDuckGo
HTML. Each attempt has a 12-second timeout and a 512 KiB response limit.
Bot challenges, empty results, oversize responses and network failures are
failures, never evidence that a search succeeded. Both failing returns
`web_search_unavailable` (HTTP 503, or a typed SSE `error` after stream headers).
This keyless option was observed to become unavailable during verification.

For a supported provider API, place an owner-only Brave Search API credential
in a private file and create the ignored local `data/router/web-search.json`:

```json
{"provider":"brave","key_file":"data/brave-search-api-key"}
```

The key file must belong to the current user and have no group/other permissions
(for example, mode 0600). Do not commit it or send it to the client. No Brave key
was configured during this verification and no paid API request was made.
Brave parsing, header isolation, domain filtering, duplicate removal and safe
credential errors are CPU-tested. Live Brave verification requires a supplied
key and remains pending. Provider configuration is read on each search request.

## Protocol and safeguards

Streaming emits typed lifecycle and search progress events, then relays native
model tokens as generated. A stable response ID, monotonic sequence numbers and
shifted output indices account for the inserted search item. Citation annotation
events and completed content contain matching URLs and character ranges. A
native stream ending without a terminal event returns an explicit error.

Authentication, network restrictions, FIFO admission, one execution slot,
worker ownership, resource guards, model profiles, contexts and idle policy are
preserved. Search occurs inside the admitted operation. Existing native
Responses requests without search and Chat Completions retain their transport.
Only an idle router is reloaded for deployment; DSH and existing worker service
invocations are preserved. Normal native idle-unloaded model weights were
reloaded by the first live request, included in its 30.280-second latency.

The search provider receives the latest query and domain operators, plus only
explicit provider headers. Prior messages, model instructions, images, client
cookies, the local API credential and client headers are not forwarded. The
Brave credential goes only to its fixed HTTPS API endpoint. Redirects are
disabled. Result pages are not fetched; snippets are marked as untrusted data
in the model context. No persistent query/result cache is added.

## Evidence and outstanding work

- All 247 CPU regressions pass, including HTTP auth/validation ordering,
  search-disabled behavior, typed stream lifecycle, citations, provider failures,
  domain filtering, bounded fallback and credential isolation.
- Live keyless provider initially returned five NASA results with snippets.
- Live nonstreaming Responses returned HTTP 200/completed, five source URLs,
  one citation annotation, a clickable source and the expected explanation.
- Live streaming attempts encountered search-provider challenges and emitted
  an explicit typed error; no false success or ungrounded answer was substituted.
- Tailscale live search and direct phone confirmation have not passed yet.
- No model benchmark or resource-setting change was made.

Next action: supply a supported provider credential, or explicitly retain the
keyless availability limitation, then finish live streaming and Tailscale
verification when search results are available.

Sources: [OpenAI web-search protocol](https://developers.openai.com/api/docs/guides/tools-web-search),
[Brave Web Search API](https://api-dashboard.search.brave.com/api-reference/web/search/get).
See [numeric verification](validation-results/20261030-responses-web-search.json).
