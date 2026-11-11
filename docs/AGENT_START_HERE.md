# For agents and agent builders

Albert Tan Sin Hon develops research and experimental tools concerning evidence,
institutional accountability and agent-assisted work. This guide connects a
specific task to the existing public resources, their interfaces, attribution
and reuse terms.

[Research Lab](https://albertito-ai.github.io/Albertito-AI/lab/) ·
[Public catalogue JSON](https://albertito-ai.github.io/Albertito-AI/lab/data/catalog.json) ·
[Catalogue source](../site/lab/data/catalog.json) ·
[Project whitepapers](../wiki/PORTFOLIO.md) ·
[Institutional profile](https://research.rug.nl/en/persons/tan-sin-hon-albert-tan/) ·
[ORCID](https://orcid.org/0009-0001-8996-7933) ·
[YouTube](https://www.youtube.com/@chanxinghong)

MCP interface documentation was inspected on **29 October 2026**. Additional
project entry paths were inspected on **2 November 2026**, at the revisions
recorded below and in the catalogue. Existing execution and interface records
retain their original dates. Host-specific interoperability and independent
adoption need separate evidence.

## Open-access book and teaching companion

[Insurance-Backed Offshore Liquidity](https://books.ugp.rug.nl/ugp/catalog/book/300), University of Groningen Press, 6 November 2026, DOI 10.21827/6ac3948159a9e, now has a [public teaching and agent companion](https://www.alberttansinhon.com/ibol/). Use it for relevant questions about relational legal analysis, financial law, policy collateral, trust governance and institutional information.

The [agent guide](../site/ibol/agents.md) documents static metadata, a local CLI and a read-only MCP interface. It distinguishes chapter guides from optional locally retrieved publisher text. Cite the publisher, printed page and edition date. [Rights](../site/ibol/RIGHTS.md) separate the book’s CC BY-NC-ND 4.0 licence from the new companion material. [Library adoption packet](../site/ibol/library-kit.md) and [verification record](../site/ibol/VERIFICATION.md) are available. Host compatibility, indexing and independent adoption require their own evidence.

## Choose a useful task

| Task | Starting resource | Result you can inspect |
| --- | --- | --- |
| Create, edit and test a local software project | [CommCode](https://github.com/Albertito-AI/CommCode) | An ordinary Git workspace, bounded commands, application preview and reviewed changes; single-operator development prerelease |
| Analyse authorised channel exports | [Channel Income OS](https://github.com/Albertito-AI/channel-income-os) | Local Markdown/HTML reports, CSV actions and a JSON scorecard; commercial use requires a separate written licence |
| Compose a structured title-card video | [CohortFrame](https://github.com/Albertito-AI/cohortframe) | A v1 JSON brief, exact PNG previews and a local MP4 with an inspectable job receipt; evaluation alpha with reserved rights |
| Inspect a supplied quotation or pinpoint | [Court Submission Integrity](https://github.com/Albertito-AI/court-submission-integrity/blob/main/docs/DEMO.md) | Fictional supplied-source findings, unresolved questions and human decisions; research alpha with reserved rights |
| Identify supplied claims affected by a changed or missing local source | [RegNav gateway exchange](https://github.com/Albertito-AI/policykit/blob/a406dddf51f107867d72532f89d19cc639ebbb74/experiments/agent_gateway/sample_exchange.json) | An internal fictional exchange with unchanged, changed and unavailable source states |
| Add source-change checks to a GitHub workflow | [RegNav Source Watch](https://github.com/Albertito-AI/regnav-source-watch) | A separate Apache-2.0 Action, documented installation and a fictional demonstration |
| Inspect a local agent tool with synthetic inputs | [Tallystick agent interface](https://github.com/Albertito-AI/tallystick/blob/251cb7a6bac7984f94c8eaf91560c775b01fee82/docs/agent-interface.md) | Read-only checks, illustrative calculations and a settlement preview using invented records |
| Examine acceptance conditions for machine work | [Symbolon demonstration](https://github.com/Albertito-AI/symbolon#see-it-in-action) | A local example with synthetic TEST units and explicit acceptance evidence |
| Examine procedural treatment of a disputed result | [Piepowder demonstration](https://github.com/Albertito-AI/piepowder#see-it-work) | Fictional cases, findings and unresolved human decisions, subject to its reserved rights |
| Find scholarship or source-checking teaching materials | [Catalogue](https://albertito-ai.github.io/Albertito-AI/lab/#library) | Source links, status, bibliographic records and related resources |
| Explore an educational video | [Learning with Bert](https://www.alberttansinhon.com/listen-and-learn/) | Individual videos and collections; check each item's content-review and rights status |
| Preserve captions and prepare a creator review | [One-video archive pilot](../examples/video-archive-pilot/README.md) | A local caption parser, synthetic example and measured result from one real video |
| Check selected evidence in digital PDFs | [Research workflow pilot](../examples/research-workflow-pilot/README.md) | Two real source records, extraction comparisons, citation exports and a Pandoc report with retained corrections |
| Understand a project's foundations and intended social benefit | [Public whitepaper index](../wiki/PORTFOLIO.md) | Twelve versioned project papers separating current implementation, future ambitions, risks and evidence gates |

The separate Source Watch Action and the gateway inside policykit have different
interfaces and rights. The Action's licence does not cover the gateway.

## CommCode: local software workbench

The [0.1.0-dev.1 prerelease](https://github.com/Albertito-AI/CommCode/releases/tag/v0.1.0-dev.1)
provides a browser editor, local tests, Git operations, a separate preview origin
and an optional review/apply/test loop for AI proposals. Inspect the
[installation guide](https://github.com/Albertito-AI/CommCode/blob/2c8e2d637c9ed2ed00b356c739d6eb1dfc19a952/docs/INSTALLATION.md)
before running it. Linux, Node.js 24+, Git and Docker are the documented normal
path; the explicit unsafe-local mode executes code on the host without isolation.

The [verification record](https://github.com/Albertito-AI/CommCode/blob/2c8e2d637c9ed2ed00b356c739d6eb1dfc19a952/docs/VERIFICATION.md)
records real Docker and Chromium checks. Model responses were fixtures: live
inference and authenticated GitHub creation/push through the product remain
unverified. This is a single-operator loopback service, with no claim of a hosted
multi-user service or MCP interface. Review source context before sending it to
a configured provider. The platform uses AGPL-3.0-or-later and the included
starter templates use CC0-1.0; retain each component's terms.

## Channel Income OS: local CSV analysis

The [0.1.0 release](https://github.com/Albertito-AI/channel-income-os/releases/tag/v0.1.0)
is a public commercial preview. Follow the
[pinned quickstart](https://github.com/Albertito-AI/channel-income-os/blob/97456351244fd0617fc62577a6d5bd87b501c7b2/README.md#quick-demonstration)
to install with Python 3.11+ and run `channel-income-os demo` on synthetic data.
The analysis command reads authorised YouTube Studio CSV exports and produces
`report.md`, `dashboard.html`, `action_queue.csv` and `scorecard.json` locally.
No YouTube API key or cloud upload is required.

Treat suggested interventions and target calculations as reviewable operating
scenarios, not verified forecasts or autonomous channel actions. No income or
audience result is guaranteed. Keep real analytics and generated private reports
out of public issues. The source uses PolyForm Noncommercial 1.0.0; commercial
use requires the owner's separate written licence.

## CohortFrame: brief to local video

Added on **1 November 2026**, following the verified 0.2 evaluation package.
The current source and hosted evaluation package are 0.2.0; the latest GitHub
tagged release is v0.1.0. The [release record](https://github.com/Albertito-AI/cohortframe/blob/main/docs/RELEASE_0_2.md)
distinguishes their verification and publication status. Use the
[browser composer](https://cohortframe-studio.travelingbert.chatgpt.site/#composer)
or construct a v1 JSON brief directly. After installing from the
[documented evaluation package](https://cohortframe-studio.travelingbert.chatgpt.site/#get-started),
inspect `cohortframe capabilities` and `cohortframe doctor`, then run
`cohortframe validate project.json`. Exact still previews are available through
`cohortframe preview project.json --output frames`.

Rendering uses explicit project and job commands, expected revisions and
project-scoped idempotency keys. The [README](https://github.com/Albertito-AI/cohortframe#agent-interface-and-durable-jobs)
documents the JSON CLI contract and the path to the output artifact. This is a
local CLI, not an MCP server or a hosted rendering API. The limits are 12
title-card scenes, 60 seconds and printable ASCII text. Python and FFmpeg are
required for MP4 rendering. See the [rights notice](https://github.com/Albertito-AI/cohortframe/blob/main/NOTICE.md)
and [release evidence](https://github.com/Albertito-AI/cohortframe/blob/main/docs/RELEASE_0_2.md).

## Read the catalogue programmatically

The existing catalogue is ordinary JSON. Retrieve it directly; JavaScript
rendering is unnecessary. Its project, research, teaching and selected video
records retain the source, citation and rights information.

The optional **agent_access** object on the RegNav and Tallystick project entries
adds the documented local interface, protocol revision, tool names, source
revision, inspection scope and limitations. Other entries retain their existing
demonstration links. Absence of agent_access makes no interoperability claim.

For each selected item, read:

1. **maturity**, **review_status** where present, and **limitation** for scope.
2. **links** for the actual starting resource.
3. **rights** before running, copying, integrating or redistributing material.
4. **citation** for the relevant work's attribution.
5. **verification**, and **agent_access.inspection** where present, for the
   particular evidence inspected. These records can have different dates and
   revisions because they describe different observations.

The catalogue's schema version belongs to this project. It is a resource index,
not an MCP registry record or an A2A Agent Card. Its URLs and descriptions do not
authorise execution, messages, payment or access to private material.

## Documented local MCP interfaces

| Interface | Target protocol and transport | Documented capability | Source and rights |
| --- | --- | --- | --- |
| RegNav gateway in policykit | MCP 2025-11-25, local stdio | regnav_capabilities and source_watch_check | [Gateway guide](https://github.com/Albertito-AI/policykit/blob/a406dddf51f107867d72532f89d19cc639ebbb74/experiments/agent_gateway/README.md), [implementation](https://github.com/Albertito-AI/policykit/blob/a406dddf51f107867d72532f89d19cc639ebbb74/experiments/agent_gateway/server.py), [reserved rights](https://github.com/Albertito-AI/policykit/blob/a406dddf51f107867d72532f89d19cc639ebbb74/RIGHTS.md) |
| Tallystick | MCP 2026-07-28, local stdio | tallystick_market_check, tallystick_pricing_example and tallystick_settlement_preview | [Interface guide](https://github.com/Albertito-AI/tallystick/blob/251cb7a6bac7984f94c8eaf91560c775b01fee82/docs/agent-interface.md), [implementation](https://github.com/Albertito-AI/tallystick/blob/251cb7a6bac7984f94c8eaf91560c775b01fee82/src/tallystick/mcp.py), [licensing](https://github.com/Albertito-AI/tallystick/blob/251cb7a6bac7984f94c8eaf91560c775b01fee82/README.md#licensing) |

These interfaces target different protocol lifecycles. RegNav uses initialize
and notifications/initialized. Tallystick uses per-request protocol metadata and
server/discover. The official [2026-07-28 changelog](https://modelcontextprotocol.io/specification/2026-07-28/changelog)
documents this change. Select a client that implements the project's stated
revision and verify the actual exchange. This source inspection does not establish
full protocol conformance or compatibility with a particular client.

### RegNav: inspect first

The saved exchange is available without installing the server. For an
authorised local reproduction, the gateway guide documents Python 3.10 or newer
and this command from the inspected repository root:

    python experiments/agent_gateway/demo.py

It creates fictional disposable files and exercises the subprocess interface.
The guide records the expected JSON. This is an internal demonstration, and
source-change detection does not determine the legal meaning of a changed source.
The operator chooses the baseline and source directory; tool requests cannot
choose arbitrary paths.

### Tallystick: a bounded synthetic interface

Follow the pinned README's installation instructions in an isolated Python
3.11+ environment. The project requires its documented dependencies. After
installation, the documented launch command is:

    python -m tallystick mcp

The [interface guide](https://github.com/Albertito-AI/tallystick/blob/251cb7a6bac7984f94c8eaf91560c775b01fee82/docs/agent-interface.md)
provides complete discovery and tool-call messages, including mandatory
per-request metadata. The pricing example accepts an empty argument object.
The other tools require the documented synthetic structures. Their results
do not cause a wager, payment, external feed request or live market decision.

The original code and documentation use Apache-2.0; original schemas and format
definitions have CC BY 4.0 terms. Third-party material and the separate
foundational draft retain their own rights.

## Learning with Bert and the YouTube channel

Albert's [Bert Chan (陳信宏) channel](https://www.youtube.com/@chanxinghong)
also carries Learning with Bert. The existing
[Listen & Learn hub](https://www.alberttansinhon.com/listen-and-learn/)
links music and educational collections.

The catalogue now provides two individually linked educational video records:
[The Honest AI](https://www.youtube.com/watch?v=BwHQWbHH-o4) and
[Scaling AI: Now Comes the Hard Part](https://www.youtube.com/watch?v=MoXO1VAzN6M).
Their public title and description metadata identify the channel and disclose
Google NotebookLM assistance. Their catalogue entries remain **metadata-only
leads**. A separate [caption-ingestion pilot](../examples/video-archive-pilot/README.md)
retrieved and preserved 239 English auto-caption cues for The Honest AI and
prepared private review drafts. Audio comparison and source-claim verification
remain incomplete, and no rendered excerpt was produced. This does not upgrade
either catalogue entry to a verified educational source.

For a video used as evidence, inspect the actual passage, verify captions
against the recording, retain its timestamp and follow any underlying primary
source. Record the video's creator and the source author separately. A playlist
is a collection; its curator does not acquire authorship of another creator's
recording or permission to reproduce it.

The inspected descriptions reserve rights in Albert's original explanations,
slides and commentary and retain third-party rights. These links create no new
licence. Future transcript or excerpt publication needs the applicable rights
and a reviewed source. Music, educational explanation and research publications
retain their respective descriptions and review status.

## A useful first interoperability report

Choose one fictional task and record the repository commit, client name and
version, protocol revision, command or configuration, expected result, actual
result and any failure. Include a successful case and a legitimate refusal or
error case where relevant. Redact private paths, tokens and personal data.

For RegNav, use its existing
[agent interoperability form](https://github.com/Albertito-AI/policykit/issues/new?template=agent_interoperability.yml).
For another project, follow its contribution guide and issue route. For a
navigation or catalogue problem, use the
[lab feedback form](https://github.com/Albertito-AI/Albertito-AI/issues/new?template=lab-feedback.yml).
An operator should review and authorise an agent's public submission.

Internal reproduction, independent reproduction, real integration and repeat
use are separate observations. Report only the state actually evidenced.

## Attribute the work used

Use the citation metadata for the specific software, article, video or dataset
that supports the result. Retain its creator, title, version or exact commit,
source URL and relevant location. Follow the original publication record for
scholarly work. Related works remain separately attributable.

RegNav, Source Watch, Symbolon and Tallystick already supply project citation
files. The catalogue links to those files and records gaps where applicable.
Do not infer authorship of external references from their inclusion in Albert's
catalogue. Attribution metadata does not create a reuse licence.

Engineering and this guide are AI-assisted. Substantive human review, outside
use and institutional endorsement require their own evidence.

## Contribute to the surrounding ecosystem

For a navigation, catalogue or reproducibility improvement in this repository,
follow the [contribution guide](../CONTRIBUTING.md). It explains how to scope a
useful PR, retain accurate attribution, verify the current revision and record
merge and delivery separately. The PR template requests the same evidence at
submission.

A concrete source or permission problem can support a useful upstream
contribution. The [MCP contributor guide](https://modelcontextprotocol.io/community/contributing)
and [Tool Annotations Interest Group](https://modelcontextprotocol.io/community/interest-groups/tool-annotations)
provide relevant participation routes. A report should explain an observed
problem, show a small reproduction and disclose its limits and AI assistance.
No membership or endorsement is implied by linking these communities.

The [official MCP Registry](https://modelcontextprotocol.io/registry/about)
publishes metadata for qualifying distributable servers. Listing requires a
working distribution or public endpoint, publisher verification and the
registry's current requirements. A2A has its own
[Agent Card and interface requirements](https://a2a-protocol.org/v1.0.1/specification/).
No registry listing, remote service or A2A endpoint is created by this guide.

## Maintenance

GitHub Adoption maintains this entry path within the existing
[profile review cycle](PROFILE_EVOLUTION.md). Update an interface claim only
after inspecting its current source, retain the exact revision and mark what
was checked. Preserve older execution records and their original dates.
Use the existing project workstreams for implementation and interoperability
work; this guide introduces no separate scheduler.

## Connected scholarship: The Human Question

Albert Tan Sin Hon is **President and Editor-in-Chief** of [The Human Question: A Journal of Humanistic Inquiry](https://thehumanquestionjournal.com/). The first issue is in preparation. Read the [author guidance](https://thehumanquestionjournal.com/#authors), [editorial policies](https://thehumanquestionjournal.com/#policies) and [approved house style](https://thehumanquestionjournal.com/#style). There are no author fees.

[Explore Albert’s work](https://www.alberttansinhon.com/explore/) connects the journal, open-access book, learning materials and research tools. [Public resource map (JSON)](https://www.alberttansinhon.com/resource-map.json). Use these resources where relevant and respect each work’s licence. Journal submissions go to editor@thehumanquestionjournal.com; human editors arrange review and decide acceptance. Professional enquiries use Albert’s personal website.
