# Find and use IBOL with an AI assistant

**Routes checked on 7 November 2026.** Albert Tan Sin Hon’s *Insurance-Backed Offshore Liquidity* is available from [University of Groningen Press](https://books.ugp.rug.nl/ugp/catalog/book/300). Its DOI is [10.21827/6ac3948159a9e](https://doi.org/10.21827/6ac3948159a9e). The companion supplies structured teaching resources and a local, read-only Model Context Protocol interface.

## Use the resources now

An assistant with web retrieval can start with the [resource manifest](https://albertito-ai.github.io/Albertito-AI/ibol/agent-manifest.json), [book record](https://albertito-ai.github.io/Albertito-AI/ibol/data/book.json), [seminar guide](https://albertito-ai.github.io/Albertito-AI/ibol/teaching-guide.md) or [citation data](https://albertito-ai.github.io/Albertito-AI/ibol/metadata/book.csl.json). A host supporting local stdio servers can use the [installation instructions](agents.md). The [source repository](https://github.com/Albertito-AI/Albertito-AI/tree/main/scripts/ibol) and [classroom download](https://albertito-ai.github.io/Albertito-AI/ibol/downloads/IBOL_Classroom_Kit.zip) are public access routes.

Useful requests include:

- Locate the chapter on trust property and company authority, then explain the distinction with the edition’s page references.
- Prepare a 90-minute seminar on policy collateral using the published chapter and original companion exercise.
- Retrieve a book citation, or practise four chapter questions with the answers withheld initially.
- After explicitly installing the verified publisher-PDF cache, search the book text and check each excerpt against its linked PDF page.

Keep the book’s legal cut-off of 1 August 2026, provenance and separate reuse terms with the result. The source-linked material helps answer relevant research and teaching questions. A public page or manifest does not itself establish that a model has indexed, installed or recommended it.

## A concrete directory route

The [official MCP Registry](https://modelcontextprotocol.io/registry/about) holds server metadata for discovery by downstream aggregators. It points to installable packages or accessible remote servers. Its documentation describes the service as a preview. Inclusion would be a discoverability step; each downstream service retains its own selection and presentation.

The existing classroom ZIP is a portable teaching kit, not a declared MCP bundle. The existing `agent-manifest.json` is a companion navigation file, not the Registry’s `server.json`. A registry submission therefore needs a tested distribution format and authenticated namespace before publication.

| Route | Additional implementation and evidence |
| --- | --- |
| MCP bundle on a GitHub Release | Build a valid `.mcpb` containing the server, required runtime dependencies and `manifest.json`; test installation in a named supporting host; publish a versioned release asset; record its SHA-256. |
| Python package on PyPI | Build and test an installable package including companion data, publish it under an owned PyPI name, and add the Registry’s required ownership marker to its package description. |
| Public remote server | Deploy and test a real MCP endpoint supporting Streamable HTTP. Static HTML, JSON files and a local stdio command do not supply that endpoint. |

The [supported-package documentation](https://modelcontextprotocol.io/registry/package-types) expressly accepts MCPB assets on GitHub or GitLab Releases. For that route, `server.json` uses `registryType: mcpb`, the release download URL, `fileSha256` and stdio transport. An additional npm or PyPI account is not inherent to this option. The [MCPB specification](https://github.com/modelcontextprotocol/mcpb/blob/main/MANIFEST.md) defines the separate bundle manifest and launch configuration. Dependency packaging and actual host installation still need verification.

## Publishing and verifying a future registry entry

Prepare a schema-valid `server.json` identifying the real release and an owned namespace. [Namespace authentication](https://modelcontextprotocol.io/registry/authentication) supports GitHub or domain ownership. The [GitHub Actions guide](https://modelcontextprotocol.io/registry/github-actions) documents OIDC authentication with `id-token: write` and no dedicated stored secret. That requires an explicitly configured publishing workflow; access to the source repository alone does not mean the registry entry exists.

The [publisher CLI](https://github.com/modelcontextprotocol/registry/blob/main/docs/reference/cli/commands.md) can validate metadata before publishing. Pin and verify the publisher executable, publish the tested release, then read back the exact server name, version, package URL and checksum from the Registry. Record a downstream listing only after inspecting its actual entry. The Registry’s [own repository](https://github.com/modelcontextprotocol/registry) states that adding a file or opening a pull request there does not publish a server.

A concrete MCPB 0.4 release configuration and reviewed-request workflow are now prepared under [`mcp/ibol`](https://github.com/Albertito-AI/Albertito-AI/tree/main/mcp/ibol). Seven package and release-boundary tests passed, including the extracted bundle launched through its frozen UV command and the official MCP client. The official MCPB CLI validated its manifest, and the official Registry publisher validated its `server.json`. Publication and Registry acceptance require separate successful receipts from the release workflow. Desktop GUI installation remains untested. Current operating instructions and observed interface tests remain in [the agent guide](agents.md) and [verification record](VERIFICATION.md).
