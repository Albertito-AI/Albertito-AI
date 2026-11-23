# IBOL MCP bundle release

The MCPB 0.4 bundle uses the documented UV runtime. A supporting host needs UV support; a generic MCPB 0.3 host may not run it. Python dependencies are resolved from the included uv.lock with --frozen. The package contains the read-only MCP server, CLI, optional explicit PDF fetch utility and original teaching data. It excludes the published PDF, caches, credentials and build environment.

Source implementation: scripts/ibol and site/ibol/data. Code is MIT and original teaching data CC BY 4.0; RIGHTS.md explains the publisher book's separate CC BY-NC-ND 4.0 licence.

A release request fixes version and source-input SHA-256. Changing that request on reviewed main starts the release workflow; ordinary companion edits do not publish. Manual dispatch also requires main and the same request checks. Release creation and official registry submission have separate evidence. Existing release tags/assets are never overwritten. The publication job uses a GitHub Actions identity, with no stored personal token.

Build locally with `python scripts/ibol/package_mcpb.py --output /absolute/output/path`. Tests include deterministic packaging, rejection of altered release inputs, and an actual MCP handshake from an extracted bundle. Validate the manifest with the official `@anthropic-ai/mcpb@2.1.2` CLI. The workflow installs UV 0.13.5, tests the frozen runtime and validates registry metadata using mcp-publisher v1.8.8. Its Linux amd64 archive SHA-256 was read from the official GitHub release metadata on 7 November 2026.

Primary specifications: https://github.com/modelcontextprotocol/mcpb/blob/main/MANIFEST.md ; https://modelcontextprotocol.io/registry/package-types ; https://modelcontextprotocol.io/registry/github-actions .

## Version 1.0.1 security maintenance

This source prepares MCP bundle 1.0.1 with the official MCP Python SDK 1.30.0.
The SDK remains on its maintained 1.x line. The other resolved dependencies
retain their existing versions and hashes. The server continues to expose six
read-only tools over stdio, without HTTP listeners or OAuth credentials.

The release request binds these updated inputs. Merging that request to main
starts the existing publication workflow for a new `ibol-mcp-v1.0.1` release and
an official Registry version. Version 1.0.0, its tag, assets and historical
verification records remain unchanged. Read the dated
[security assessment](https://github.com/Albertito-AI/Albertito-AI/blob/main/docs/IBOL_SECURITY_2026-11-22.md) before release.

## Version 1.0.2 contact and canonical website update

This metadata patch gives the bundle Albert’s public contact address, [info@alberttansinhon.com](mailto:info@alberttansinhon.com), and the canonical [alberttansinhon.com](https://alberttansinhon.com/) website. The companion’s public record and Registry website use the same domain.

The six read-only tools, runtime contract and dependency versions remain unchanged. The package version and reviewed source-input digest advance together. Versions 1.0.0 and 1.0.1, their release tags, assets and historical evidence remain intact.
