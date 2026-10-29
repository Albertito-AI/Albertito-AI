# For agents and agent builders

Albert Tan Sin Hon develops research and experimental tools concerning evidence,
institutional accountability and agent-assisted work. This guide connects a
specific task to the existing public resources, their interfaces, attribution
and reuse terms.

[Research Lab](https://albertito-ai.github.io/Albertito-AI/lab/) ·
[Public catalogue JSON](https://albertito-ai.github.io/Albertito-AI/lab/data/catalog.json) ·
[Catalogue source](../site/lab/data/catalog.json) ·
[Institutional profile](https://research.rug.nl/en/persons/tan-sin-hon-albert-tan/) ·
[ORCID](https://orcid.org/0009-0001-8996-7933) ·
[YouTube](https://www.youtube.com/@chanxinghong)

Interface documentation inspected on **29 October 2026**. The links below pin
the source revisions inspected. Host-specific interoperability and independent
adoption need separate evidence.

## Choose a useful task

| Task | Starting resource | Result you can inspect |
| --- | --- | --- |
| Identify supplied claims affected by a changed or missing local source | [RegNav gateway exchange](https://github.com/Albertito-AI/policykit/blob/a406dddf51f107867d72532f89d19cc639ebbb74/experiments/agent_gateway/sample_exchange.json) | An internal fictional exchange with unchanged, changed and unavailable source states |
| Add source-change checks to a GitHub workflow | [RegNav Source Watch](https://github.com/Albertito-AI/regnav-source-watch) | A separate Apache-2.0 Action, documented installation and a fictional demonstration |
| Inspect a local agent tool with synthetic inputs | [Tallystick agent interface](https://github.com/Albertito-AI/tallystick/blob/251cb7a6bac7984f94c8eaf91560c775b01fee82/docs/agent-interface.md) | Read-only checks, illustrative calculations and a settlement preview using invented records |
| Examine acceptance conditions for machine work | [Symbolon demonstration](https://github.com/Albertito-AI/symbolon#see-it-in-action) | A local example with synthetic TEST units and explicit acceptance evidence |
| Examine procedural treatment of a disputed result | [Piepowder demonstration](https://github.com/Albertito-AI/piepowder#see-it-work) | Fictional cases, findings and unresolved human decisions, subject to its reserved rights |
| Find scholarship or source-checking teaching materials | [Catalogue](https://albertito-ai.github.io/Albertito-AI/lab/#library) | Source links, status, bibliographic records and related resources |
| Explore an educational video | [Learning with Bert](https://www.alberttansinhon.com/listen-and-learn/) | Individual videos and collections; check each item's content-review and rights status |

The separate Source Watch Action and the gateway inside policykit have different
interfaces and rights. The Action's licence does not cover the gateway.

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
Google NotebookLM assistance. These are **metadata-only leads**: the video
content, transcripts, source support and timestamped claims have not been
reviewed for these entries. No substantive summary is inferred from a title.

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
