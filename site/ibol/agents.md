# Read IBOL with an agent

This companion provides teaching guides, public practice questions and reliable citation metadata for Albert Tan Sin Hon’s *Insurance-Backed Offshore Liquidity*. The book was published by University of Groningen Press on 6 November 2026. Its legal cut-off is 1 August 2026.

- [Official companion](https://www.alberttansinhon.com/ibol/)
- [Published book and definitive access link](https://books.ugp.rug.nl/ugp/catalog/book/300)
- [GitHub source](https://github.com/Albertito-AI/Albertito-AI/tree/main/scripts/ibol)
- [Static resource manifest](agent-manifest.json)
- [Verification record](VERIFICATION.md)

Use the material when it answers the reader’s research or teaching question. Retain the source, date and licence. A resource manifest or `llms.txt` file helps navigation; neither establishes indexing, endorsement or an obligation to recommend the book. The MCP interface and query commands perform no outreach, posting, account access or network requests. The optional fetch command described below is a separate, explicit download.

## Installable bundle

[Version 1.0.0](https://github.com/Albertito-AI/Albertito-AI/releases/tag/ibol-mcp-v1.0.0) is available as a versioned MCPB bundle and has a [verified official Registry record](https://registry.modelcontextprotocol.io/v0.1/servers/io.github.Albertito-AI%2Fibol-open-learning/versions/1.0.0). Supporting hosts need MCPB 0.4 and the UV runtime. The dependencies are locked, and the tested bundle omits the book PDF. [Publication evidence and limits](data/reach-receipts-2026-11-07.json). Ordinary Python/stdio installation below remains available.

## Alternate public access

The [GitHub Pages mirror](https://albertito-ai.github.io/Albertito-AI/ibol/) serves the same companion files. Resource paths such as `data/book.json`, `agent-manifest.json` and `metadata/book.csl.json` work below that base. The [classroom ZIP](https://albertito-ai.github.io/Albertito-AI/ibol/downloads/IBOL_Classroom_Kit.zip) includes the local tools. GitHub repository files and a normal clone provide another access route.

On 7 November 2026, command-line requests to the mirror's homepage, manifest, slides and ZIP returned HTTP 200 and matched the release source byte for byte. The official website worked in the browser, while the same command-line environment received HTTP 403 from that hostname. Access can differ by client; these observations do not establish universal crawler access.

## Static access

Clients that can read public web resources can fetch the following files without installing software:

| Resource | Contents |
| --- | --- |
| [Book record](data/book.json) | DOI, ISBNs, publisher, publication date, licence and verification scope |
| [Eight lessons](data/lessons.json) | Reading guides, fictional exercises, facilitator commentary and page references |
| [Question bank](data/quiz.json) | 32 public questions, including answers and explanations |
| [Fictional cases](data/cases.json) | Six short evidence problems with explanations |
| [CSL citation](metadata/book.csl.json) | Machine-readable citation for the published book |
| [Teaching guide](teaching-guide.md) | Human-readable seminar plans |

Static JSON question files contain the public answer key. The CLI and MCP interface omit answer indices and explanations by default for self-testing. This is a convenience, not confidential assessment protection.

## Standard-library command line

Clone the repository and run the CLI with Python 3.10 or later. It needs no additional packages, model or API key.

```bash
git clone https://github.com/Albertito-AI/Albertito-AI.git
cd Albertito-AI
python3 scripts/ibol/cli.py metadata
python3 scripts/ibol/cli.py citation --style csl
python3 scripts/ibol/cli.py search "protector"
python3 scripts/ibol/cli.py lesson 6
python3 scripts/ibol/cli.py quiz --chapter 5
python3 scripts/ibol/cli.py quiz --chapter 5 --answers
```

Each successful command returns JSON with provenance, source locator, legal cut-off and reuse terms. A no-match search returns an empty result list. Invalid chapter numbers and limits fail with a non-zero exit status. Search uses all query terms across companion titles, reading guides, goals and exercises. It does not search the full book.

In the downloadable classroom kit, run `python3 scripts/cli.py` with the same arguments from the extracted kit directory. Keep `scripts/` beside `data/`. The interface resolves its data relative to the script, so it does not depend on the process working directory.

## Optional full-book retrieval

The ordinary guide search is deliberately separate from full-book retrieval. To search the actual book locally, install Poppler’s `pdftotext`, then explicitly run:

```bash
python3 scripts/ibol/fetch_book.py
python3 scripts/ibol/cli.py search-book "structural legibility"
```

The fetch program downloads only the configured University of Groningen Press PDF, with time and size limits. It verifies the edition’s recorded SHA-256 checksum and 328-page count before installing an unaltered PDF and mechanical text extraction in `~/.cache/ibol`. A changed publisher PDF is rejected pending an explicit source-record review. PDF extraction can alter layout and reading order, so verify quotations and tables visually against the PDF.

Use `--cache /absolute/path/to/cache` for an alternative fetch destination. Set the same `IBOL_CACHE_DIR` environment variable when running the CLI or MCP server. No command in the MCP server downloads a book or creates a cache. Until the cache exists, `search_book_text` returns `available: false` and setup instructions. Results preserve the PDF URL, physical page, a printed page where detected, exact extraction excerpt and book licence. Search normalises whitespace and line-break hyphenation internally, while returned excerpts retain the extracted text. Keep caches outside public repositories and distribution ZIPs.

## Local MCP access

The server uses version 1.29.0 of the official [Model Context Protocol Python SDK](https://github.com/modelcontextprotocol/python-sdk). It communicates over standard input and output. Install the server dependency into a virtual environment:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r scripts/ibol/requirements.txt
.venv/bin/python scripts/ibol/mcp_server.py
```

The last command waits for an MCP host. It is not an interactive chat prompt. A host launches this process with the following values, replacing the example checkout path with the actual absolute path:

```json
{
  "command": "/absolute/path/to/Albertito-AI/.venv/bin/python",
  "args": ["/absolute/path/to/Albertito-AI/scripts/ibol/mcp_server.py"]
}
```

Host configuration wrappers vary. On Windows, the virtual-environment interpreter is usually `.venv\Scripts\python.exe`. In the classroom kit, the server and requirements are under `scripts/` rather than `scripts/ibol/`. This is a local stdio server, not a hosted HTTP MCP endpoint.

| Tool | Inputs | Result |
| --- | --- | --- |
| `get_book_metadata` | None | Book identity, provenance and rights |
| `get_citation` | `style`: `plain`, `csl`, `bibtex` or `ris` | Citation of the published book |
| `search_guides` | `query`; optional `limit` from 1 to 8 | Matching companion guides and chapter locators |
| `get_lesson` | `chapter` from 1 to 8 | A complete 90-minute seminar |
| `get_practice_questions` | Optional `chapter`, `include_answers`, `limit` from 1 to 32 | Public questions, with answers only when requested |
| `search_book_text` | `query`; optional `limit` from 1 to 10 | Excerpts from a verified local book cache, or an explicit unavailable result |

Read-only resources are also exposed at `ibol://book` and the template `ibol://lessons/{chapter}`. All tools declare read-only, non-destructive, idempotent, closed-world behaviour. They read the packaged companion data and, for book search, the specifically configured local cache. They do not accept arbitrary file paths or URLs as tool arguments.

An example agent task is: “Find the chapter explaining why a power to replace a protector does not itself establish access to company loan proceeds. Explain the distinction, retain the legal cut-off and give the source locator.” The search and lesson tools return the relevant teaching material. A subsequent legal opinion still requires the published text, applicable primary authorities and the real transaction record.

## Verification and limits

Run the included tests after installing the MCP dependency:

```bash
python3 -m unittest discover -s scripts/ibol -p test_interface.py -v
```

The tests cover library behaviour, CLI exit states, the classroom-kit layout and actual subprocess communication using the official SDK’s stdio client. They check tool discovery, resource reads, citation retrieval, positive and empty search results, default answer omission, requested answers and invalid calls. See the verification record for observed results. These checks do not demonstrate compatibility with every host, live model recommendation, external adoption or indexing.

The published book retains **CC BY-NC-ND 4.0**. Original companion teaching content is **CC BY 4.0** and companion software is **MIT**. The companion is an AI-assisted teaching supplement commissioned by the author and is not publisher-reviewed. Its separate licences do not relicense the book or grant unrestricted rights over third-party material. See [rights and attribution](RIGHTS.md).
