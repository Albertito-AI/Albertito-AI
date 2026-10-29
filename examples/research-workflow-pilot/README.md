# Two-document research workflow pilot

A small, executed local pipeline for source-linked notes from digital PDFs.
It retrieves two official historical Singapore/Thailand releases, keeps source
hashes, extracts native text, checks selected evidence, exports citation records
and publishes an original report with Pandoc.

**Measured on 29 October 2026:** Docling native recovered all 16 selected content
references and passed 14/16 location checks. pdfplumber and the combined route
passed 16/16 jointly. This is a tiny development set, not a general accuracy
benchmark. No model API calls, model downloads, paid services or hosted jobs were
used. Nothing here runs perpetually or publishes automatically.

## Read the outcome

- [Original report](report.md)
- [Locally rendered HTML](output/report.html)
- [Final machine-readable results](results.json)
- [Preserved first-pass results](results-first-pass.json)
- [Corrected v2 reference set](reference_set.v2.json)
- [Preserved frozen v1 reference set](reference_set.json)
- [Evaluation history and review correction](EVALUATION_HISTORY.md)
- [Source provenance](sources.json)
- [CSL JSON citation records](references.csl.json)
- [BibTeX citation records](references.bib)

The CSL JSON and BibTeX are Zotero-compatible citation exports. Zotero application
import and cloud sync were **not** tested or configured. Pandoc's citeproc did
consume the CSL JSON and resolve both sources in HTML and PDF.

## Scope and findings

The corpus contains one four-page Singapore GDP advance-estimate release and one
two-page Bank of Thailand policy statement, both in English. Historical figures
must not be presented as current data. The Singapore author remains the Ministry
of Trade and Industry, as printed on the source, even though its landing page has
migrated to METI.

Eight table cells and eight paragraph/date regions were annotated from rendered
pages. The original v1 target hash was frozen before extraction evaluation.
An independent post-outcome review found that v1 TH06 put its exact expected date
in the selector. That v1 content check was answer-bearing. V2 replaces the
selector with a standalone-date-after-corporate-signature role, while preserving
all expected values, cues, pages and rectangles. **V2 was not frozen before all
observation.** The v2 locators use semantic/structural selectors without the
expected target values, pages or rectangles.
The evaluator checks exact selected tokens/values and page/region grounding. It
does not assess all characters, complete paragraphs, full table reconstruction,
scanned PDFs, Thai-language text or unseen documents. The same assistant both
annotated and evaluated the corpus.

Two Docling-native table boxes span several values. The combined route uses a
unique matching pdfplumber word box inside the Docling box, rejecting ambiguous
matches. A standalone-date locator was fixed after the first pass; the original
13/16 and 15/16 joint results are retained, as are the pre-review v1 final results.
The v2 selector change and both reference hashes are explicit in the history.
Three negative controls (wrong value, page and cell region) were all rejected.
Two additional structural-date checks confirm that a changed input date is
returned and that removing the signature makes the lookup fail.

**This test gives no accuracy-based reason to replace pdfplumber on these files.**
Docling's native mode offers a unified representation without AI-model runtime
cost; stronger document-structure capabilities were not tested here.

## Reproduce locally

The supported reproduction environment is **Linux with Python 3.12**. Use
Pandoc 3.1.3 (or review output changes on a newer version),
XeLaTeX and Poppler. No package installation is performed automatically by any
Python script. The normal reproduction environment can be an isolated venv:

```bash
python -m venv tmp/venv
tmp/venv/bin/python -m pip install -r requirements.txt
tmp/venv/bin/python fetch_sources.py
tmp/venv/bin/python extract.py --engine docling-native
tmp/venv/bin/python extract.py --engine pdfplumber
tmp/venv/bin/python evaluate.py
tmp/venv/bin/python build_report.py
tmp/venv/bin/python validate.py
```

The recorded pilot reused compatible installed scientific packages through an
isolated venv with `--system-site-packages`. Its 28 additional wheels totalled
approximately 16 MB; this was a one-off dependency download, not an AI-model
download. Package versions and executed-tool receipts are preserved. A clean
venv can require more download space for the scientific dependencies.

Fetching needs internet access and is restricted to the two configured public
PDF URLs. It refuses changed source hashes. All extraction uses local files and
blocks Python socket connection/name-resolution attempts. The scripts neither
read credentials nor configure any external account. No API keys are needed.

Docling native's documented limitation is important: it emits native text cells
and their provenance, not model-inferred reading order, heading hierarchy or
structured tables. This pilot supplies its own deterministic locators. If the
Docling packages are unavailable, the pdfplumber extraction command remains
usable, but the full three-route evaluator expects both receipts and will not
pretend a Docling run occurred.

## Verification and packaging

`validate.py` verifies record consistency, metric totals, negative controls,
citation resolution, both rendered outputs and the public allowlist. The report
PDF was also rendered to PNG and visually inspected. Pypdf reported recoverable
cross-reference warnings while inspecting the original Singapore PDF; both
extraction engines and Poppler completed its four pages successfully.

`public-allowlist.json` identifies original code, derived evidence, citation
metadata and the original report suitable for repository inclusion. Full source
PDFs, source page images, full extracted text, package downloads and the virtual
environment live under excluded `tmp/`. The locally generated PDF preview is
listed separately from text repository files. Nothing here changes the parent
project's licence. See [source and tool notices](SOURCE_NOTICES.md).

## Primary documentation

- [Docling native PDF mode](https://docling-project.github.io/docling/usage/advanced_options/#extract-the-native-content-of-a-pdf)
- [Docling slim dependency declaration](https://github.com/docling-project/docling/blob/main/pyproject.toml)
- [Pandoc citation processing](https://pandoc.org/MANUAL.html#citation-rendering)

These explain the selected tools. The files in `sources.json` are the actual
research inputs, not these documentation pages.
