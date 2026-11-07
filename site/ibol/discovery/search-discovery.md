# Search discovery and evidence

This record explains how the IBOL companion is made available for search and retrieval. Publication, crawler access, indexing, ranking and independent use are separate outcomes. A local successful request demonstrates that request only.

## OpenAI crawling and retrieval

The [official OpenAI crawler documentation](https://developers.openai.com/api/docs/bots), checked on 7 November 2026, distinguishes three relevant agents:

| Agent | Documented purpose | Practical implication |
| --- | --- | --- |
| `OAI-SearchBot` | Discovery for ChatGPT search | Keep intended public pages accessible under the site's robots rules and network controls. OpenAI recommends permitting its published search-crawler IP ranges. |
| `GPTBot` | Crawling material that may be used in model training | Its robots setting is independent of search. Search discovery does not require agreeing to training through this separate setting. |
| `ChatGPT-User` | Some visits initiated by a person's ChatGPT request | It is not the automatic search crawler. OpenAI says robots rules may not apply to these user-initiated requests. |

OpenAI states that search systems may take about 24 hours to adjust after a robots change. Allowing access does not establish that a page has been indexed, included in an answer or used for training.

## Observed robots scope

On 7 November 2026, a direct HTTPS request to [the official site's root robots file](https://www.alberttansinhon.com/robots.txt) returned HTTP 200 and matched the source:

```text
User-agent: *
Allow: /

Sitemap: https://www.alberttansinhon.com/sitemap.xml
```

This file governs the official hostname; it does not set policy for the publisher's domain or the GitHub mirror. The mirror lives below `/Albertito-AI/`, while a request to `https://albertito-ai.github.io/robots.txt` returned HTTP 404 in this check. No ineffective project-subdirectory robots file was added.

This check inspected the public robots response, not verified crawler-origin traffic or hosting firewall logs. An earlier request to the official host's IndexNow proof file returned HTTP 403. The different results concern different requests and do not establish a universal block or universal access. No crawler policy or hosting protection was changed in this audit.

For agents using the companion directly, see the [client installation guide](ai-clients.md) and [source-aware agent guide](../agents.md). These are voluntary integration paths; they do not instruct unrelated agents to promote the book or override a person's task.

## Google Search AI features

[Google's official guidance](https://developers.google.com/search/docs/appearance/ai-features), checked on 7 November 2026, applies ordinary Search requirements to AI Overviews and AI Mode. A supporting page must be indexed and eligible for a search snippet. Google calls for accessible crawling, internal links, useful textual content and structured data that agrees with what people can read. It specifies no additional AI file, special markup or special schema for inclusion, and does not guarantee crawling, indexing or display.

For this companion, `llms.txt` and the MCP tools serve navigation and voluntary use. Their presence is not proof of Google eligibility or inclusion. Googlebot controls Search crawling; Google points to Google-Extended for certain separate training and grounding uses.

The source audit checked the hub's title, author, publisher, publication date, DOI, book licence and free-access statement against its visible text and embedded book metadata. Those core claims agree. The hub links directly to all eight complete seminar pages, so the written lessons are reachable without running the interactive lesson selector. The metadata consistently identifies the publisher's book and keeps the teaching supplement's licence separate.

Both ISBNs and the author ORCID are now visible alongside the hub citation in the reviewed source, following the audit recommendation. Source checks do not replace Google's fetched-page inspection. A verified owner can use Search Console's URL Inspection and performance reports to investigate actual indexing and search traffic; no authenticated Search Console result was obtained in this campaign.

## Bing and IndexNow

[IndexNow's protocol](https://www.indexnow.org/documentation) requires a publicly retrievable UTF-8 ownership key on the submitted host. A key in a subdirectory covers the corresponding path scope and must be identified through `keyLocation`. Notifications concern added, changed or deleted URLs. One participating endpoint shares the notification with other participants, so parallel submissions to every endpoint add no necessary distribution step. HTTP 202 means receipt with key validation pending; HTTP 200 alone also does not prove indexing.

The [IndexNow FAQ](https://www.indexnow.org/faq) advises meaningful-change notifications and avoiding repeated unchanged submissions. [Bing's implementation guide](https://www.bing.com/indexnow/getstarted) recommends checking receipt through Bing Webmaster Tools and explicitly distinguishes notification from crawling or indexing. These primary sources were checked on 7 November 2026.

### Receipts inspected

| Route | Observed event | What it establishes |
| --- | --- | --- |
| GitHub mirror, 10 existing companion URLs | Global IndexNow endpoint returned HTTP 202 on 7 November 2026 at 10:15:39 UTC | Notification received, with key validation pending at that response. |
| Official host, first attempt | Ownership-proof request returned HTTP 403 at 10:13:48 UTC | Local preflight failed; no IndexNow notification was sent. |
| Official host, later proof recheck | Ownership-proof request returned HTTP 403 at 11:04:18 UTC | Preflight still failed; no notification was sent. |

Evidence: [original release and notification receipts](../data/reach-receipts-2026-11-07.json) and [campaign distribution record](../data/campaign-distribution.json). The HTTP 403 responses came from the proof-file requests, not from a submitted IndexNow notification. No duplicate submission was made during this audit. No authenticated Bing Webmaster Tools report, confirmed indexing or downstream readership was obtained.

The present notification script limits requests to the reviewed hub, slides and eight seminar URLs. It defaults to a dry run, verifies exact public proof-file contents before posting, records each outcome and performs no automatic retry. New activity routes should enter a separately reviewed notification set only after publication and verification.
