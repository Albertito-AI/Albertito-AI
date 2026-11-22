# PDF dependency maintenance | 22 November 2026

Two retained examples declare older optional PDF parsers. This maintenance
raises the historical Court Submission Integrity copy's `pdf` extra to
`pypdf>=7.1.1,<8` and the research-workflow pilot's exact pin to `pypdf==7.1.1`.
The dedicated [Court Submission Integrity repository](https://github.com/Albertito-AI/court-submission-integrity)
is the location for continuing project development. Earlier source, validation
results and publication records remain available in Git history.

## Why the declarations changed

The previous court range, `pypdf>=5.9,<7`, excluded upstream fixes. The pilot
pinned 6.10.0. The maintainer's
[cross-reference stream advisory](https://github.com/py-pdf/pypdf/security/advisories/GHSA-59jv-x5x2-gg4c)
affects versions below 7.0.0; the
[image memory-allocation follow-up](https://github.com/py-pdf/pypdf/security/advisories/GHSA-fhff-j4m8-439h)
affects versions below 7.0.1. The [7.1.1 release](https://pypi.org/project/pypdf/7.1.1/)
includes subsequent parser limits and remains compatible with Python 3.10+.

The court intake copy reads supplied PDFs. The pilot's `validate.py` uses
pypdf to inspect its locally generated report PDF; that is a narrower exposure
than an unrestricted document-ingestion service. No compromise or exploit
was demonstrated. In particular, text extraction alone does not establish
reachability of the image-specific advisory.

## Verification and limits

Using a fresh Linux/CPython 3.12.14 virtual environment and the official pypdf
7.1.1 wheel, all 87 existing tests in the historical court copy passed without
skips. Its adverse, matched, unknown and TXT-intake examples also completed,
retaining their unresolved review and no-filing-decision states. The wheel's
SHA-256 matched PyPI's release metadata:
`04c5680d4b4cfa04ab505b09393fc949860c34a4dad6565284d11a2f5c3ce8b1`.

The pilot's full Docling/pdfplumber/Pandoc pipeline was not rerun. Its original
measured outputs and historical dependency receipts have not been presented as
new results. No model, source-download, publication or account operation was
performed by these checks. An installed environment requires an explicit
upgrade; changing a manifest does not update installed packages. Current
advisories, resolved dependency integrity and hostile-input isolation remain
separate operational checks.
