# IBOL SDK security maintenance, 22 November 2026

## Change and release scope

This change prepares MCP bundle **1.0.1**, replacing the official MCP Python SDK
1.29.0 with **1.30.0** in the source requirements and frozen UV lock. The project,
bundle manifest and reviewed release request all identify 1.0.1. The other
resolved dependency versions and hashes are unchanged. The current source guide
and the live classroom ZIP carry the new SDK pin. The ZIP has 78 members; only
`agents.md` and `scripts/requirements.txt` change, and all other member contents
remain byte-identical.

The existing `ibol-mcp-v1.0.0` tag, GitHub release assets and historical
verification records are preserved. This document records preparation and
local validation. Publication and official Registry acceptance require their
own later receipts.

## Verified advisory scope

The upstream [1.30.0 release notes](https://github.com/modelcontextprotocol/python-sdk/releases/tag/v1.30.0)
identify this as maintenance of the 1.x line. Official PyPI metadata for
[1.29.0](https://pypi.org/pypi/mcp/1.29.0/json) and
[1.30.0](https://pypi.org/pypi/mcp/1.30.0/json) have identical `Requires-Dist`
requirements and support Python 3.10 or newer. IBOL retains its existing Python
3.12 requirement.

| Maintainer advisory | Issue and fixed-version condition | IBOL exposure assessment |
| --- | --- | --- |
| [GHSA-5h93-6whr-6q8j](https://github.com/modelcontextprotocol/python-sdk/security/advisories/GHSA-5h93-6whr-6q8j), CVE-2026-116685 | HTTP client redirects could forward custom headers and bodies to another origin. 1.30.0 restricts redirects. | The shipped server uses stdio; no HTTP MCP client transport is configured. |
| [GHSA-84m7-p3x7-pcfv](https://github.com/modelcontextprotocol/python-sdk/security/advisories/GHSA-84m7-p3x7-pcfv), CVE-2026-59951 | Stateful Streamable HTTP sessions could accumulate without a limit. 1.30.0 adds default expiry and a session cap. | The shipped server has no Streamable HTTP listener. |
| [GHSA-qx49-fqc8-xw99](https://github.com/modelcontextprotocol/python-sdk/security/advisories/GHSA-qx49-fqc8-xw99), CVE-2026-115563 | OAuth client issuer and credential binding. 1.30.0 supplies fixes, but pre-provisioned client providers also need an explicit `issuer`; old stored registrations need migration. | IBOL configures no OAuth client or credentials. An upgrade alone would not make a future OAuth integration correct. |
| [GHSA-rwrf-2pqf-9j8j](https://github.com/modelcontextprotocol/python-sdk/security/advisories/GHSA-rwrf-2pqf-9j8j), CVE-2026-116686 | Client result validation could fetch external schema references over any transport. 1.30.0 resolves references within the supplied schema only. | Server-only applications are outside the advisory's affected scope. IBOL's test clients connect only to its own controlled server. |
| [GHSA-w4fh-qvv9-3v23](https://github.com/modelcontextprotocol/python-sdk/security/advisories/GHSA-w4fh-qvv9-3v23), CVE-2026-116684 | HTTP bearer audience validation. 1.30.0 adds an opt-in check; users must set `validate_token_resource=True` and return the verified audience as `AccessToken.resource`, or validate the audience themselves. | IBOL uses no HTTP bearer-token authentication. Upgrading alone does not enable this check. |

All five advisories name 1.30.0 as a patched 1.x version; none requires a 2.x
migration. The assessment does not demonstrate exploitation of IBOL, and it is
not a guarantee against unknown defects. Keep the stdio and read-only scope
unless a separate review covers any transport, authentication or tool changes.

## Local verification

Validation used Linux, CPython 3.12.14 and the workflow's pinned **UV 0.13.5**.
Only locked registry wheels were installed in an isolated environment, with
source builds and project installation disabled. No repository install hook,
private credential or external model service was used.

- `uv sync --locked --offline --no-build --no-install-project` accepted the
  coherent project and lock without changing them.
- All **65 existing companion tests passed**, without skips. These include real
  stdio handshakes from source and an extracted MCPB, all six read-only tools,
  missing-cache behaviour, invalid arguments, citation identity and default
  answer omission.
- The extracted bundle launched through its manifest's `uv run --frozen`
  command using UV 0.13.5. A local wrapper supplied an already verified cache,
  disabled network access and prohibited source builds. The server's actual
  stdio handshake and tool calls succeeded.
- Deterministic bundle packaging, changed-input rejection and release
  tag/asset overwrite rejection tests passed. The live classroom ZIP passed
  CRC validation, and all 76 unaffected members retained their original bytes.
- The official `@anthropic-ai/mcpb@2.1.2` CLI accepted the MCPB manifest.
  The validator was installed outside the repository with npm lifecycle
  scripts disabled.
- The official MCP publisher 1.8.8 accepted the generated `server.json` through
  the official Registry validation endpoint. The publisher archive SHA-256
  matched both the pinned workflow and its official GitHub release metadata.
  Validation did not authenticate or publish a Registry version.
- OSV-Scanner 2.7.1 matched the updated UV lock against locally downloaded
  PyPI advisories with `--offline --no-resolve`: 30 package entries, zero
  reported matches. This is limited to that database snapshot and supported
  advisory coverage; it does not establish that every package is safe.

The first frozen-launch attempt failed because the UV 0.13.5 cache lacked a
wheel previously selected by UV 0.13.9. Populating the cache with the exact
workflow UV version resolved that environment issue; the complete suite then
passed. The SDK, repository tests and release controls were not weakened.

Verified SDK 1.30.0 wheel SHA-256:
`666edb5009503e1047c9d60346a756f94b261f05cc2625f23d41c728ffc484d0`.
The source distribution SHA-256 is
`445414625fce5c295faa505bb11bacece661ab6f4028d57c935db57820b7a3e4`.
Both hashes were read from official PyPI metadata and retained in `uv.lock`.

## Required release decision and side effects

The existing [release instructions](../mcp/ibol/README.md) require a reviewed
main release request. The request binds the distribution and publisher inputs
by SHA-256, including `.github/workflows/ibol-registry.yml`. A subsequent change
to a bound input requires a fresh review and digest.

Merging this release-request change into main automatically starts that
workflow. There is no separate environment approval configured in it. After
its tests, MCPB validation and registry-schema validation, the publication job
creates the new `ibol-mcp-v1.0.1` tag and immutable GitHub release assets, obtains
an official MCP Registry publishing identity through GitHub Actions OIDC, and
publishes and reads back the version metadata. It uses job-scoped
`contents: write` and `id-token: write` permissions. It does not overwrite
version 1.0.0. Manual dispatch is also restricted to the same reviewed main
request.

Review the complete candidate and the applicable hosted checks before that
merge decision. Local test success is not evidence of desktop GUI installation,
third-party host interoperability, official Registry acceptance or independent
adoption. No release publication was triggered during preparation.
