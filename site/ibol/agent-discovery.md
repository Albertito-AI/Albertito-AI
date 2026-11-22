# Find and use IBOL with an AI assistant

**Resource routes checked on 7 November 2026; security installation guidance updated on 22 November 2026.** Albert Tan Sin Hon’s *Insurance-Backed Offshore Liquidity* is available from [University of Groningen Press](https://books.ugp.rug.nl/ugp/catalog/book/300). Its DOI is [10.21827/6ac3948159a9e](https://doi.org/10.21827/6ac3948159a9e). The companion supplies structured teaching resources and a local, read-only Model Context Protocol interface.

## Security maintenance package

Security version **1.0.1** updates the official MCP Python SDK to 1.30.0. Check its [publication workflow](https://github.com/Albertito-AI/Albertito-AI/actions/runs/45002490558), [GitHub release](https://github.com/Albertito-AI/Albertito-AI/releases/tag/ibol-mcp-v1.0.1) and [official MCP Registry record](https://registry.modelcontextprotocol.io/v0.1/servers/io.github.Albertito-AI%2Fibol-open-learning/versions/1.0.1) before installation. Confirm that the release bundle and Registry package identify SHA-256 `dfd76e65bfb5d70ad07b62bb14f2734914b7f483bd021fc8f08f5d095437ed6e`. The [security assessment](https://github.com/Albertito-AI/Albertito-AI/blob/main/docs/IBOL_SECURITY_2026-11-22.md) records the source review and 65 passing companion tests. A queued workflow does not establish completed publication; the current source installation is available while publication is pending.

The original version 1.0.0 publication is retained in the [7 November delivery receipts](data/reach-receipts-2026-11-07.json). Those historical results remain unchanged. Current installation instructions use the security maintenance version.

The bundle requires a host supporting **MCPB 0.4 and the UV runtime**. Its exact launch command and SDK calls were tested; desktop GUI installation remains untested. The source and ordinary stdio configuration remain available for other hosts. Registry publication does not establish inclusion in every downstream directory or use by an independent assistant.

## Use the resources now

An assistant with web retrieval can start with the [resource manifest](https://albertito-ai.github.io/Albertito-AI/ibol/agent-manifest.json), [book record](https://albertito-ai.github.io/Albertito-AI/ibol/data/book.json), [seminar guide](https://albertito-ai.github.io/Albertito-AI/ibol/teaching-guide.md) or [citation data](https://albertito-ai.github.io/Albertito-AI/ibol/metadata/book.csl.json). A host supporting local stdio servers can use the [installation instructions](agents.md). The [source repository](https://github.com/Albertito-AI/Albertito-AI/tree/main/scripts/ibol) and [classroom download](https://albertito-ai.github.io/Albertito-AI/ibol/downloads/IBOL_Classroom_Kit.zip) are public access routes.

Useful requests include:

- Locate the chapter on trust property and company authority, then explain the distinction with the edition’s page references.
- Prepare a 90-minute seminar on policy collateral using the published chapter and original companion exercise.
- Retrieve a book citation, or practise four chapter questions with the answers withheld initially.
- After explicitly installing the verified publisher-PDF cache, search the book text and check each excerpt against its linked PDF page.

Keep the book’s legal cut-off of 1 August 2026, provenance and separate reuse terms with the result. The source-linked material helps answer relevant research and teaching questions. A public page or manifest does not itself establish that a model has indexed, installed or recommended it.

## Client setup and discovery evidence

The [client guide](discovery/ai-clients.md) gives documentation-verified setup routes for Claude Desktop, VS Code, Cursor, Goose and Gemini CLI. It records exact runtime checks separately from untested application installation. The client guide uses checksum-pinned version 1.0.1. GitHub's separate immutable-release setting was reported as disabled on 7 November 2026; that historical observation is not a current settings check.

The [search guide](discovery/search-discovery.md) explains ordinary search and AI retrieval requirements. The [catalogue guide](discovery/catalogues.md) and [library routes](discovery/library-routes.md) identify eligible academic discovery paths. The [campaign ledger](discovery/campaign.html) records the work and its limits.

The Registry stores metadata for downstream discovery. Its [package documentation](https://modelcontextprotocol.io/registry/package-types) explains MCPB distribution, and its [authentication guide](https://modelcontextprotocol.io/registry/authentication) explains namespace ownership. Confirm the exact IBOL version and package fields using the linked Registry record. Other directory listings and independent use require their own evidence.
