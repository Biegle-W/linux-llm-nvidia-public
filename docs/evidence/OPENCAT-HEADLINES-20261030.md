# OpenCat headline content repair — October 30, 2026

The user reported a model response saying that specific headline details were
unavailable in the provided search results. A representative query, `latest news
headlines today`, reproduced a source-quality problem: Mwmbl returned mostly
generic news landing pages with short, empty or stale snippets. A successful
search request alone did not establish that the model had usable headline data.
The user's exact original question was requested but was not available during
this verification; the tests below use representative headline requests.

The selected free search implementation now routes explicit headline/current-news
queries to bounded RSS retrieval. General/world headlines use BBC's World feed,
with Google News RSS as an availability fallback. Topic-specific current-news
queries use Google News RSS search with a one-day search window. Ordinary
questions such as `SearXNG` continue through Mwmbl. Static questions such as
`What is Hacker News?` are not routed as current-news requests.

The model receives **actual story titles, feed descriptions, publication times,
publisher names where supplied, and source links**. It is instructed to report
available headline details and cite them, while avoiding article facts absent
from the feed. This supplies usable content rather than merely changing the
wording of an access refusal.

## Use in OpenCat

Continue using **`qwen27b-hyperqwen-search`** in the existing Responses provider.
No new connection setting, search key, account or payment is needed. For example,
ask `Today's top 3 headlines` or `latest Canada news`.

The regular HyperQwen entry still does not search unless the client requests a
search tool. The search entry still resolves to the same guarded HyperQwen
profile, and the phone's empty-tool request shape remains supported.

## Verification

- The full **259-test CPU suite passed**. Four additional tests cover headline
  intent versus ordinary search, feed titles/descriptions/dates, freshness,
  duplicates, domain filtering, fixed provider hosts, anonymous headers,
  bounded failures and topical query normalization.
- After a final small normalization change for common request words and
  apostrophes, all **22 targeted search tests passed**; these are not counted
  again toward the 259 total.
- Real nonstreaming Responses with inline input and `tools: []` returned at
  least three exact fetched headline titles, valid citation annotations and
  clickable sources in **2.845 seconds**.
- Real streaming over Tailscale returned at least three exact fetched titles
  with citations in **3.192 seconds**, with a stable response ID and ordered
  events. Neither answer contained the generic access-refusal phrases checked
  by the test. These were actual feed/network/model calls, not mocked search.
- A further live streaming request included the reported earlier access refusal in the conversation history. It still returned three actual headline titles with citations in **3.685 seconds**, rather than repeating the refusal.
- A separate topical provider check returned three fresh dated Google News RSS
  records for `latest Canada news`, without an API key.
- Existing worker and DSH service invocations and the access configuration
  were preserved. Only the idle router was reloaded. No benchmark, model
  setting, context allocation, resource guard or credential changed.

Direct confirmation of the user's exact question on the iPhone remains pending.
The live checks establish representative headline behavior through the same
router and tailnet connection, not direct observation of the phone UI.

## Bounds and limits

Each RSS attempt has a 12-second timeout and a 512 KiB response cap. General
headlines have at most two fixed feed attempts; topical news uses one fixed
Google News host. No arbitrary result page is fetched and redirects are
disabled. Invalid XML, empty/missing dates, duplicate links, nonpublic URLs,
records older than 48 hours and records over five minutes in the future are
discarded. Allowed-domain filters still apply to returned citation URLs.
Some Google News citation links point to its aggregator; restrictive publisher
domain filters can therefore yield no matching results.

Publication timestamps are supplied explicitly. A recent feed record is not a
guarantee of breaking news or that it was published during the user's local
calendar day. Topic matching, publisher coverage and public-feed availability
are limited. General feed selection is a source's headline ordering, not an
independent ranking of the world's most important events. Unavailable or empty
fresh feeds return a clear `web_search_unavailable` error rather than replacing
them with generic landing-page text and calling it current news.

Feeds provide headlines and short descriptions, **not full articles or a full
website crawl/audit**. The model must not invent additional details. Snippets
and feed records are untrusted data; no site-provided text is executed. No
persistent query or result cache was added, and no paid fallback is selected.

Sources: [BBC World RSS](https://feeds.bbci.co.uk/news/world/rss.xml),
[Google News RSS](https://news.google.com/rss),
[existing search/model entry](OPENCAT-SEARCH-MODEL-20261030.md).
See [numeric verification](validation-results/20261030-opencat-headlines.json).
