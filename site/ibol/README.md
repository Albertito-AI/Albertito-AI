# IBOL Open Learning Companion

[Use the companion on Albert Tan Sin Hon’s official website](https://www.alberttansinhon.com/ibol/) · [Read the published book](https://books.ugp.rug.nl/ugp/catalog/book/300) · [GitHub Pages mirror](https://albertito-ai.github.io/Albertito-AI/ibol/)

This companion supports *Insurance-Backed Offshore Liquidity: Financial Law, Trust Governance and Regulatory Visibility at the PRC-Hong Kong Interface*, published by University of Groningen Press on 6 November 2026, DOI [10.21827/6ac3948159a9e](https://doi.org/10.21827/6ac3948159a9e).

## Use it

- **Read:** start with the preface, introduction and Chapter 1 in the publisher PDF.
- **Teach:** use the [eight seminar plans](teaching-guide.md), [lecture slides](slides.html) and [public question bank](quiz-answer-key.md).
- **Play:** open `index.html` for 32 practice questions, six evidence cases and the three-record sorting challenge. The page needs JavaScript but no server or account.
- **Catalogue:** use the [library packet](library-kit.md) and [citation exports](metadata/).
- **Connect an agent:** follow [agents.md](agents.md) for the local CLI and MCP server. Static JSON and Markdown require no SDK.

The classroom ZIP includes the site and executable agent source in `scripts/`. Open its `index.html` in a browser. Online links, publisher downloads and copying through the clipboard may depend on your browser and connection. Most teaching activities remain usable offline.

## Maintain it

The source content is in `data/`. Run `python scripts/ibol/build.py` **from the parent GitHub repository** to regenerate Markdown, metadata, `content.js` and the download. This build program is intentionally not included in the classroom ZIP. Review source references and licences before changing content. See [verification](VERIFICATION.md).

The book remains CC BY-NC-ND 4.0. New companion teaching materials are CC BY 4.0 and companion software is MIT. [Read the scope](RIGHTS.md). No other repository content is relicensed. All cases are fictional, and the supplement is AI-assisted work commissioned by the author, not a publisher-reviewed edition. Legal cut-off: 1 August 2026.
