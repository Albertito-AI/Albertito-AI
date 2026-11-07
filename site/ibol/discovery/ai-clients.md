# Use IBOL with an AI client

The IBOL companion provides six read-only Model Context Protocol tools for Albert Tan Sin Hon's *Insurance-Backed Offshore Liquidity* (University of Groningen Press, 2026). The tools return edition-specific metadata, citations, teaching guides and formative questions. Full-book search requires an explicitly downloaded and verified local publisher-PDF cache. The legal cut-off is 1 August 2026.

## Choose an installation route

| Client | Route described below | Verification in this campaign |
| --- | --- | --- |
| Claude Desktop | Import the versioned MCPB 0.4 UV bundle | Official instructions checked; desktop installation not performed. |
| VS Code | Extracted bundle; portable Copilot or VS Code JSON | Schema checked; client session not performed. |
| Cursor | Extracted bundle; project or personal JSON | Schema checked; client session not performed. |
| Goose | Extracted bundle; YAML extension entry | Schema checked; client session not performed. |
| Gemini CLI | Extracted bundle; user or project JSON | Schema checked; client session not performed. |

The shared frozen server command was exercised through the MCP Python SDK. Client and model-provider access requirements remain separate from the companion server, which needs no account or API key. Configuration examples are templates: replace the absolute folder path and merge entries without overwriting existing settings.

## Verified release

Checked on 7 November 2026:

- [Official MCP Registry record](https://registry.modelcontextprotocol.io/v0.1/servers/io.github.Albertito-AI%2Fibol-open-learning/versions/1.0.0): `io.github.Albertito-AI/ibol-open-learning`, version `1.0.0`, status `active`.
- [GitHub release](https://github.com/Albertito-AI/Albertito-AI/releases/tag/ibol-mcp-v1.0.0): published on 7 November 2026, neither a draft nor a prerelease.
- [Download the MCPB bundle](https://github.com/Albertito-AI/Albertito-AI/releases/download/ibol-mcp-v1.0.0/ibol-open-learning-1.0.0.mcpb): 47,498 bytes; SHA-256 `5a4cea2a291fb180a7818a356e15118315737f330eab5d48ce2b162774383b77`.
- [Published checksum file](https://github.com/Albertito-AI/Albertito-AI/releases/download/ibol-mcp-v1.0.0/SHA256SUMS): matched both the downloaded bytes and the Registry digest in this check.

The bundle uses MCPB manifest version 0.4 and the UV runtime, with Python 3.12 and locked dependencies. A host must support that runtime. The release workflow protects existing assets against replacement; GitHub's separate immutable-release setting was reported as `false` at this check. The pinned checksum is therefore the integrity reference.

Registry publication establishes that the package is discoverable through the Registry API. It does not establish installation, recommendation or use by any particular AI provider or reader.

## Source and rights

[Server documentation](../agents.md) describes all six tools and the optional local book cache. [Source code](https://github.com/Albertito-AI/Albertito-AI/tree/main/scripts/ibol) is MIT; original teaching material is CC BY 4.0. The publisher book remains CC BY-NC-ND 4.0 and is not included in the bundle. See [rights and attribution](../RIGHTS.md).

## Claude Desktop

**Documentation-verified instructions; this particular bundle has not been installed in Claude Desktop during this check.** The [official UV example](https://github.com/modelcontextprotocol/mcpb/blob/main/examples/hello-world-uv/README.md) documents host-managed Python dependencies. IBOL requires MCPB 0.4 UV support; a successful download alone does not establish host compatibility.

1. Download version 1.0.0 above and compare its SHA-256 with the pinned value. On Windows PowerShell, run `Get-FileHash .\ibol-open-learning-1.0.0.mcpb -Algorithm SHA256`; on macOS, run `shasum -a 256 ibol-open-learning-1.0.0.mcpb`.
2. In Claude Desktop, open Settings, Desktop app, then Manage beside Extensions. Older layouts use Settings, Extensions. Under Advanced settings, choose Install Extension and select the `.mcpb` file. Organisational policy may restrict custom extensions.
3. Inspect the installed server's connection status and tools. Ask it to call `get_book_metadata`, then `get_citation` with `style` set to `csl`. The returned DOI should be `10.21827/6ac3948159a9e`.
4. If installation fails, inspect the local MCP logs and check runtime support. Do not treat an installed entry without a successful tool response as a working connection.

Package tests exercise the extracted server and its exact frozen UV launch; they do not exercise Claude Desktop's interface. This package is listed in the official MCP Registry, and no Claude extension-directory listing is claimed.

Source checked 7 November 2026: [Claude's local MCP installation guide](https://support.claude.com/en/articles/10949351-getting-started-with-local-mcp-servers-on-claude-desktop), and the [MCPB manifest specification](https://github.com/modelcontextprotocol/mcpb/blob/main/MANIFEST.md).

## Prepare a local command for other clients

The following examples use the same versioned bundle, extracted into a local folder, with its locked dependencies. They do not require a hosted MCP endpoint. Keep the whole extracted folder together because the server resolves its teaching data relative to its own file.

Install [UV from its official documentation](https://docs.astral.sh/uv/getting-started/installation/). Verify the bundle checksum above, then extract it as a ZIP archive. For example, with Python installed:

```sh
python -m zipfile -e ibol-open-learning-1.0.0.mcpb ibol-bundle
```

Replace `/ABSOLUTE/PATH/ibol-bundle` in each example with that folder's absolute path. On Windows, JSON paths may use forward slashes, for example `C:/Users/YourName/ibol-bundle`. If the client cannot find `uv`, replace the command with UV's absolute executable path.

The launch command is:

```sh
uv run --frozen --directory "/ABSOLUTE/PATH/ibol-bundle" scripts/mcp_server.py
```

This exact argument pattern was exercised through the official MCP Python SDK from an unrelated working directory on 7 November 2026: initialisation succeeded, six tools were discovered, and `get_citation` returned the expected DOI. This verifies the server command, not any client's graphical interface. UV creates a local environment and may download Python or dependencies at first launch.

## VS Code

Open **Chat: Open Customizations**, choose **MCP Servers**, then **Add Server (+)**. Choose a command using standard input/output and supply the launch command above. Select the intended harness and configuration scope. The current documentation distinguishes portable Copilot configuration (`mcpServers`) from VS Code configuration (`servers`). For a Copilot user configuration at `~/.copilot/mcp-config.json` unless `COPILOT_HOME` specifies another location, merge this entry without replacing existing servers:

```json
{
  "mcpServers": {
    "ibol": {
      "command": "uv",
      "args": ["run", "--frozen", "--directory", "/ABSOLUTE/PATH/ibol-bundle", "scripts/mcp_server.py"]
    }
  }
}
```

For the VS Code format in `.vscode/mcp.json`, use top-level `servers` instead and add `"type": "stdio"` to the `ibol` object. The current guided flow labels this older destination deprecated while retaining compatibility.

Start the configured server, request `get_book_metadata`, and inspect the actual tool response for DOI `10.21827/6ac3948159a9e`. A plausible model answer without a tool call is insufficient. VS Code host installation was not performed here.

Sources checked 7 November 2026: [Add MCP servers](https://code.visualstudio.com/docs/agent-customization/mcp-servers) and [configuration reference](https://code.visualstudio.com/docs/agents/reference/mcp-configuration).

## Cursor

Prepare the extracted bundle and UV as above. Merge this entry into project `.cursor/mcp.json`, or into `~/.cursor/mcp.json` for personal use across projects:

```json
{
  "mcpServers": {
    "ibol": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "--frozen", "--directory", "/ABSOLUTE/PATH/ibol-bundle", "scripts/mcp_server.py"]
    }
  }
}
```

Replace the absolute path and preserve existing server entries. In Cursor's Customize area, enable the server and inspect its available tools. Ask for `get_citation` with `style: "csl"`; expand the tool response and check the DOI. The local command above needs no OAuth configuration or API key. If startup fails, open the Output panel and select MCP Logs.

This uses Cursor's documented local standard-input/output configuration with the previously exercised frozen IBOL command. No Cursor installation, tool call from Cursor or marketplace listing has been verified. Team policies can restrict local MCP servers.

Source checked 7 November 2026: [Cursor's MCP documentation](https://cursor.com/docs/mcp), including configuration locations, standard-input/output fields and MCP logs.

## Goose

Prepare UV and the extracted bundle first. In Goose's configuration file, merge this entry under `extensions`, preserving the chosen model provider and other extensions:

```yaml
extensions:
  ibol:
    name: ibol
    type: stdio
    enabled: true
    cmd: uv
    args:
      - run
      - --frozen
      - --directory
      - /ABSOLUTE/PATH/ibol-bundle
      - scripts/mcp_server.py
    env_keys: []
    envs: {}
    timeout: 300
```

Default configuration locations are `~/.config/goose/config.yaml` on macOS/Linux and `%APPDATA%\Block\goose\config\config.yaml` on Windows. Replace the example path; quote a Windows path using forward slashes. Restart Goose after editing, then request the IBOL citation and inspect the returned DOI and provenance. Goose's provider configuration remains separate from this unauthenticated local server.

The YAML fields and standard-input/output route were checked against the maintained [Goose configuration reference](https://github.com/aaif-goose/goose/blob/main/documentation/docs/guides/config-files.md) on 7 November 2026. The frozen server command has been tested through the MCP SDK; no Goose application invocation or extension-directory listing is claimed.

## Gemini CLI

After preparing UV and the extracted bundle, merge this server into `~/.gemini/settings.json` for user scope, or the project's `.gemini/settings.json`. Preserve other settings and replace the absolute path:

```json
{
  "mcpServers": {
    "ibol": {
      "command": "uv",
      "args": ["run", "--frozen", "--directory", "/ABSOLUTE/PATH/ibol-bundle", "scripts/mcp_server.py"],
      "trust": false
    }
  }
}
```

Run `gemini mcp list`, or `/mcp` inside an interactive session, to inspect connection and tools. The documented client only tests local standard-input/output servers in a trusted folder; review the intended folder before granting that trust. Request `get_book_metadata` and verify the returned DOI and legal cut-off. Leaving `trust` false retains tool-call confirmations.

The configuration was checked against [Gemini CLI's official MCP reference](https://geminicli.com/docs/tools/mcp-server/) on 7 November 2026. It reuses the frozen IBOL command tested through the MCP SDK. Gemini CLI itself was not configured or exercised here. Its provider authentication requirements are separate from IBOL, which requires no server credential. No Gemini extension-directory listing is claimed.
