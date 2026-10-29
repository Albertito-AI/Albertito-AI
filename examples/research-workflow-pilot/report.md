---
title: "Two-document research pilot"
subtitle: "Native PDF extraction, source grounding and citation publishing"
author: "Prepared for Albert Tan Sin Hon; AI-assisted pilot"
date: "29 October 2026"
lang: en
link-citations: true
geometry: margin=22mm
fontsize: 10pt
colorlinks: true
urlcolor: blue
---

## Result

A working local workflow processed two official public PDFs, preserved source
identifiers, exported citation data and published this report with Pandoc.
The combined Docling and pdfplumber workflow passed **16 of 16 selected content
and location checks**. Docling native alone recovered all selected content but
passed 14 of 16 location checks. These are development-set results on six pages,
not a general document-accuracy benchmark.

## Sources and historical context

The Singapore release is an advance GDP estimate issued on 2 January 2025.
The Thai release records a monetary-policy decision issued on 26 February 2025.
Their figures are historical statements, not current economic estimates or
today's interest rate. [@sg-mti-advance-gdp-2024; @th-bot-mpc-2025-1]

- **Ministry of Trade and Industry, Singapore**: 4 PDF pages; issued 2025-01-02; source SHA-256 starts `d2c0b07a1fe09dc2`.
- **Bank of Thailand**: 2 PDF pages; issued 2025-02-26; source SHA-256 starts `0bffa74beced7f50`.

The original Singapore document names the Ministry of Trade and Industry.
Its official landing page has since migrated to the METI domain; the citation
retains the original issuing author. Full URLs, download timestamps, byte sizes
and SHA-256 hashes are recorded in `sources.json`.

## Measured results

| Extraction and grounding route | Content | Location | Both |
|:--|--:|--:|--:|
| Docling native | 16/16 | 14/16 | 14/16 |
| pdfplumber | 16/16 | 16/16 | 16/16 |
| Docling + word boxes | 16/16 | 16/16 | 16/16 |

The reference set contains eight selected table cells and eight paragraph or
date regions. V1 targets were manually defined from rendered source pages and
frozen before evaluation. After reviewing the outcomes, v2 replaced one
answer-bearing date selector with a structural lookup. Both versions and hashes
are preserved; **v2 was not frozen before all observation**.

**Content** means exact selected table values or ordered paragraph tokens/cues.
It does not mean complete transcription or semantic equivalence. **Location**
means the correct physical PDF page and the returned box's centre inside the
manually marked region. It does not measure exact box overlap. Semantic locators
receive v2 row/column labels, paragraph cues or a corporate-signature role,
without the expected target values, pages or boxes.

## What the pilot exposed

Docling's native pipeline merged several adjacent numeric cells into one text
box for references SG08 and SG09. The correct values were present, but their boxes
were too broad to satisfy the selected-cell location check. The combined route
retains Docling's value and finds a unique matching pdfplumber word inside the
original box. An ambiguous match is rejected.

The first pass scored **13/16** jointly for Docling and **15/16** for pdfplumber.
Both routes initially merged the Thai issued-date line with nearby contact
information. A generic standalone-date rule corrected that locator. Original
results remain in `results-first-pass.json`, and the earlier corrected v1 results
remain in `results-v1-final.json`.

An independent code review then found that TH06's v1 selector contained the very
date being tested, making that content check answer-bearing. V2 locates a generic
standalone date immediately after the issuing organisation's signature. It
contains no target date, page or coordinates. The expected targets remain
unchanged, but the selector was revised after outcomes. A synthetic changed-date
check confirms that the locator returns the new input date; removing the
signature correctly makes the lookup fail. See `EVALUATION_HISTORY.md`.
All corrections were developed on this same small set; the final numbers are
not held-out performance.

Three negative controls substituted a wrong number, wrong page and wrong cell
region. All were rejected. This checks that the evaluator distinguishes content
recovery from source-location correctness.

## Tools, spending and boundaries

The pilot ran on **Linux with Python 3.12**. The executed parser was
**docling-slim 2.144.0**, using NativePdfPipeline with
docling-parse 7.24.1 and docling-core 2.105.0. Its native mode uses no OCR, layout
or table model. It emitted zero structured tables; table lookup was performed by
this pilot's original deterministic code. The pdfplumber baseline was also run.
The native option is described in the
[official Docling documentation](https://docling-project.github.io/docling/usage/advanced_options/#extract-the-native-content-of-a-pdf).

No model API calls, AI-model downloads, paid services, subscriptions or private
GitHub Actions were used. Source retrieval and isolated package installation
used network access; extraction ran with network access blocked by an audit hook.
Existing local compute was used. This does not establish zero operating cost
for future unattended hosting.

`references.csl.json` and `references.bib` contain two source records in standard
citation formats. Pandoc actually consumed the CSL JSON via citeproc. These are
**Zotero-compatible exports**; Zotero application import, account integration and
cloud sync were not performed. Pandoc 3.1.3 produced this PDF and a standalone
HTML report. Full source PDFs, page images and full extraction text are excluded
from the public package.

## Practical conclusion

The small workflow is useful for reproducible, source-linked notes from digital
PDFs. On these references, pdfplumber alone was sufficient; the test provides no
evidence that adding Docling improves accuracy. Docling supplies a common document
representation, while fine location claims still require checking. Before wider
adoption, test unseen documents, scanned pages and Thai-language body text. A
single assistant annotated and evaluated this pilot; no independent annotation
or statistical confidence estimate is claimed.

## References

::: {#refs}
:::
