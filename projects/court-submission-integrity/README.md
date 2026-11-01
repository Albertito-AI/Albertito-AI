# Court Submission Integrity

**An inspectable preflight report for submissions, not an automated judge.**

A standalone program prepared for **Albert Tan Sin Hon**, with AI-assisted
implementation. Research alpha `0.1.0a1`, 1 November 2026. Working title, not a
cleared brand. No court affiliation, endorsement, operational approval or adoption
is claimed. [Authorship](AUTHORS.md) · [Rights](RIGHTS.md) · [Validation](docs/VALIDATION.md)

## Public source location

This independently runnable project is hosted in the public research hub at
`Albertito-AI/Albertito-AI`, under `projects/court-submission-integrity`.
It is not part of RegNav and has no runtime dependency on another portfolio project.
A separate `Albertito-AI/court-submission-integrity` repository has **not** been
created. The hub is the publication location because the available connection
can publish files and commits but cannot create a repository. No main-profile
presentation, existing application code, licence or scheduler is changed.

This is publication of a research source snapshot, **not** a tagged formal release,
a hosted service, an authenticated court integration or a production deployment.
See the [publication record](docs/PUBLICATION.md).

## Run the program

Download or clone this repository and change into this project directory:

```sh
cd projects/court-submission-integrity
python -m unittest discover -s tests -v
python -m court_integrity examples/adverse.json --output demo-adverse
python -m court_integrity.intake examples/intake_submission.txt --sources examples/intake_sources.json --jurisdiction FICTIONAL --output demo-intake
```

Open `demo-adverse/report.html` or `demo-intake/report.html` in a browser. Each
report also has a JSON representation. Output directories must not already exist;
the parent directory must exist. A successful CLI exit means that a report was
written, **not** that a submission is accurate, admissible or fit to file.

The core and text/Markdown/DOCX intake use Python's standard library. No API key,
model call, network connection or paid service is needed. Python 3.10+ is the
compatibility target; the actual local tests used **CPython 3.13.5 on Linux**.
PDF input needs an already installed optional `pypdf` parser. No installation is
performed by the program. Without it, the two PDF tests are explicitly skipped.

Other fictional checks:

```sh
python -m court_integrity examples/matched.json --output demo-matched
python -m court_integrity examples/unknown.json --output demo-unknown
```

Even `matched.json` remains `HUMAN_REVIEW_REQUIRED`. The absent-source example
preserves uncertainty rather than treating unavailable material as fabrication.

## What is implemented

| Area | Implemented check | Boundary |
| --- | --- | --- |
| Document intake | TXT/Markdown, bounded DOCX, optional text-bearing PDFs; selected SG/UK neutral-citation candidates | No OCR, exhaustive citation recognition or automatic source retrieval |
| Pinpoints | Explicit paragraph, section, physical PDF-page and printed-page locators against supplied text | Locator types remain distinct; source transcription is not authenticated |
| Quotations | Whitespace-only quotation comparison and matches elsewhere in the supplied source | Textual matching does not establish legal support, context or truth |
| Evidence linkage | Missing sources, absent passages, incomplete extraction and unanchored annotations | Detailed review requires explicit annotations; not all claims are extracted |
| Consistency | Conflicting annotated values within the same context, party position, scenario and unit | Opposing accounts and alternative pleadings are kept separate |
| Arithmetic and chronology | Explicit decimal sums and declared date ordering | No automatic factual verification or legal deadline calculation |
| Argument structure | Missing references/premises and cycles in an explicit dependency graph | Not a general evaluator of coherence, logical validity or legal merits |
| Document production | Declared requests, responses and linked document records | No privilege, proportionality or disclosure-duty decision |
| Reporting | Escaped local HTML, JSON, input digests, itemised findings and explicit unknowns | No truth percentage, credibility score or automatic filing decision |

This is **not** an upload-any-document factuality or hallucination detector. It
identifies bounded discrepancies in supplied material and makes the next review
questions visible. No allegation is declared false merely because a source is
missing, and no person is recorded as having reviewed a claim without such evidence.

## Examples and reproducibility

All fixtures are original fictional exercises. This source publication includes
TXT and JSON inputs and the generators. Bulky generated reports, historical
machine-specific logs and the prebuilt DOCX/PDF demonstration binaries remain in
the owner's preserved original archive; they are not necessary to run the program
or its 87-test suite. Reports are generated by the commands above.

The optional demonstration generator `examples/make_intake_documents.py` creates
DOCX/PDF versions when the developer-only `python-docx` and `reportlab` packages
are already available. Invoke it from this directory with
`python -m examples.make_intake_documents`. These packages are not core runtime
requirements. The generator does not download or install anything.

## Development direction and safeguards

Read the [product brief](docs/PRODUCT_BRIEF.md), [input contract](docs/INPUT_CONTRACT.md),
[integration design](docs/INTEGRATION_DESIGN.md), [global roadmap](docs/GLOBAL_ROADMAP.md),
[research references](docs/RESEARCH_SOURCES.md) and [threat model](docs/THREAT_MODEL.md).

The next substantive gates are permitted authoritative-source resolution,
independently labelled accuracy evaluation, source-grounded semantic review and
jurisdiction-specific profiles. Court adapters, human authentication, production
security, accessibility and real-user efficiency remain unverified or unimplemented.
A court should not automatically reject, sanction or rank a litigant using this alpha.

Use only fictional or independently cleared inputs in a trusted local environment.
Never commit real court submissions, privileged or sealed documents, client or
student records, credentials or generated reports containing private information.
Public inspectability is not an open-source licence. [RIGHTS.md](RIGHTS.md) remains
unchanged, and no other repository's licence is imported into this project.
