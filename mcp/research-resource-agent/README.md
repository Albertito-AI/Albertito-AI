# Albert Tan Sin Hon Research Resource Agent: Registry publication

This directory describes a remotely hosted, read-only research resource service
provided by Albert Tan Sin Hon. Its public MCP endpoint is:

<https://albert-agent-network.travelingbert.chatgpt.site/api/mcp>

The service searches a dated catalogue of public resources and retrieves source
records and IBOL teaching lessons. Results carry contributor credit, source
links, rights and available limitations. It performs deterministic retrieval; it
does not provide general legal advice or execute arbitrary tasks. Read the
[public connection guide](https://alberttansinhon.com/for-agents/) for scope and
current access information. Enquiries: <info@alberttansinhon.com>.

Version 1.1.1 describes the service's financial law, insurance, trust governance
and teaching scope and declares the existing public PNG icon. Its reviewed
snapshot contains 32 catalogue records and eight IBOL companion lessons.
Individual tool arguments explain their inputs, and the resource-record tool
distinguishes a lesson summary from the full companion teaching guide. The
service does not retrieve or search the published book's full text.

## Metadata scope

`server.json` uses the official MCP Registry remote schema, namespace
`io.github.Albertito-AI/research-resource-agent`, and the `streamable-http`
transport. It declares no package, API key or OAuth requirement. Hosting-layer
restrictions can still affect particular clients and must be reported honestly.

This repository contains the publication metadata and verification workflow.
The optional Registry `repository` field is deliberately omitted because that
field represents the MCP service implementation's source repository. No private
source location or credentials are published here.

## Reviewed publication process

The GitHub Actions workflow runs only for this repository's `main` branch when
the reviewed `release-request.json` changes, or when manually dispatched on
`main`. That file binds the exact metadata bytes by SHA-256 and requires both
MCP 2026-07-28 and the legacy 2025-11-25 compatibility check. Its
`expected_snapshot` also records the exact reviewed catalogue and lesson counts;
the live check rejects a different, missing or invalid count.

Before publication, the workflow:

1. Verifies the metadata hash and runs focused failure-case checks.
2. Downloads official `mcp-publisher` 1.8.8 and verifies its pinned SHA-256 before
   running the publisher's schema validation.
3. Requires the deployed health response and MCP identity to report the exact
   Registry version, and the health response to match both reviewed snapshot
   counts. The official MCP 2.3.0 client discovers and exercises all
   three tools, including the IBOL author's credit, DOI and book licence.
4. Checks legacy `initialize`, its HTTP 202 empty notification response, and
   tool discovery, which some directory health checks still use.
5. Reads the exact Registry name/version. An identical active record is a
   successful no-op. Only HTTP 404 at the exact version URL permits a new
   publication. Redirects, conflicting metadata, a non-active record, access
   denial or another error stop the run.
6. Authenticates with GitHub OIDC, publishes only when absent, and verifies the
   public readback. Temporary publisher credentials are cleared afterwards.

The workflow has `contents: read` and `id-token: write` permissions only. It does
not create a GitHub release, install a GitHub App, provision infrastructure, pay
for a directory or send community messages.

## Local checks

From the repository root:

```sh
uv sync --frozen --project mcp/research-resource-agent
python scripts/research_resource/check_registry.py --metadata-only
uv run --frozen --project mcp/research-resource-agent python -m unittest discover -s scripts/research_resource -p 'test_*.py' -v
```

The read-only live check requires the reviewed version to be publicly deployed:

```sh
uv run --frozen --project mcp/research-resource-agent python scripts/research_resource/check_remote.py --output /tmp/research-resource-live-check.json
```

A Registry entry can be imported by independent directories under their own
rules. Publication, ingestion and a protocol test are distinct from independent
use, endorsement or a guarantee of recommendation.

## Primary specifications

- [Official Registry schema](https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json)
- [Registry metadata requirements](https://github.com/modelcontextprotocol/registry/blob/main/docs/reference/server-json/official-registry-requirements.md)
- [Official publisher release](https://github.com/modelcontextprotocol/registry/releases/tag/v1.8.8)
- [Glama connector import and health checks](https://glama.ai/mcp/faq)
