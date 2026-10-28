# Albert Tan Research Lab

The [Research Lab](https://albertito-ai.github.io/Albertito-AI/lab/) is a public
index of Albert Tan's scholarship, experimental software and teaching materials.
It helps a visitor locate a relevant source, inspect a documented example,
understand its status and choose a bounded next step.

The existing [Sparks Dance Floor](https://albertito-ai.github.io/Albertito-AI/)
retains its original address and controls. Research navigation lives under
`/lab/`; neither route replaces the other.

## Choose a route

| Purpose | Route |
| --- | --- |
| Find a publication and its bibliographic record | [Research](https://albertito-ai.github.io/Albertito-AI/lab/#research) |
| Inspect software demonstrations and reuse terms | [Projects](https://albertito-ai.github.io/Albertito-AI/lab/#projects) |
| Find source-checking materials | [Teaching](https://albertito-ai.github.io/Albertito-AI/lab/#teaching) |
| Follow a short set of maintained starting points | [Sparks guide](https://albertito-ai.github.io/Albertito-AI/lab/#guide) |
| Report a reproducible difficulty or unclear explanation | [Feedback form](https://github.com/Albertito-AI/Albertito-AI/issues/new?template=lab-feedback.yml) |

Sparks' lab guide is curated navigation. It selects documented routes from the
catalog; it does not generate legal advice or certify the linked material.
Use each project's actual demonstration and current rights statement before
planning an executable evaluation or contribution.

## Use the recorded exercise

Open [Source replay](https://albertito-ai.github.io/Albertito-AI/lab/#replay),
select a scenario, then choose a claim. The Before and After tabs show the
recorded fixture and output. Source choices preserve contrary passages rather
than silently replacing them. The scenario explanation identifies what changed
and which question the automated check can answer.

My review notes stores a practice annotation for the selected dataset, scenario
and claim in this browser. Download review JSON retains those notes; Clear this
note removes the selected annotation. Download recorded receipts exports the
original execution record unchanged. Notes are not submitted to GitHub.

The verification section provides each command, expected and observed exit
status, assertions, standard output, source revisions and file hashes.
Intended rejection cases retain their nonzero exit codes.

## Reproduce the recorded executions

The [Research lab workflow](../.github/workflows/research-lab.yml) reruns the
pinned tools and compares their output with the committed
[execution record](../site/lab/data/regnav.json). A repository maintainer can
select **Run workflow** on the main branch to repeat this check without changing
the saved record or its timestamp.

For a local reproduction, use Git, Python 3.12 and Node.js 24. These commands
use a POSIX shell, such as Linux, macOS or WSL. Start outside an existing clone:

```sh
git clone https://github.com/Albertito-AI/Albertito-AI.git
cd Albertito-AI
git clone https://github.com/Albertito-AI/policykit.git .lab-sources/policykit
git -C .lab-sources/policykit checkout 130cf41b0d59e1f72a238b0cf3c145c6ca337265
git clone https://github.com/Albertito-AI/regnav-source-watch.git .lab-sources/regnav-source-watch
git -C .lab-sources/regnav-source-watch checkout 2a6501fbbf535c58b11aeef16a8e8d0cc48148c0
python scripts/lab/export_regnav.py --policykit .lab-sources/policykit --source-watch .lab-sources/regnav-source-watch --output site/lab/data/regnav.json --verify
```

After obtaining the repositories, the example execution uses local files and
the Python standard library, Node.js and Git. It makes no model or source-URL
requests. The exporter recreates temporary fictional inputs, runs the actual
CLIs, checks their expected results, and compares semantic output and source
hashes with the saved record. It ignores timestamps and runner-specific paths
when comparing repeat executions.

The displayed commands use `$POLICYKIT`, `$SOURCE_WATCH` and `$FIXTURES` as
normalised directory labels. Temporary fixture directories are removed after
the run. Use the exporter command above to recreate them and execute the complete
sequence. The [fixture specification](../scripts/lab/regnav_fixtures.json) and
[exporter](../scripts/lab/export_regnav.py) show every transformation.

To intentionally create a new recorded execution after reviewing a source
change, omit `--verify`. This writes only the selected output file after all
assertions pass. Review the resulting diff before publishing it.

## What the catalog records

The [catalog source](../site/lab/data/catalog.json) contains five project entries,
three published-research entries and two teaching or source-inspection entries.
Each item includes its status, useful links, an inspection date and the scope
of that inspection. Repository sources use exact commit URLs. Institutional
publication records retain their own publication dates and bibliographic fields.

A catalog inspection establishes what its cited source stated at that time.
It does not establish professional fitness, independent adoption, educational
benefit or legal accuracy. Publication dates, source access dates, legal
effective dates and software revisions remain different fields.

The lab's source and engineering records are separate from substantive human
review. A successful browser test shows that the tested interaction worked.
A matching hash shows that particular bytes match a recorded value. Neither
turns an `unreviewed` proposition into a completed legal assessment.

## Research and software relationships

The public RegNav README expressly identifies the Singapore/Thailand and China
articles as part of its research direction. Its Singapore reporting case
specifically cites the distinction between reporting duties and legal
consequences. The case still has two `unreviewed` propositions. The links do
not establish that the software reproduces every argument or validates either
article.

Source Watch is a separate implementation inspired by RegNav's evidence-record
workflow. Its manifest is specific to that Action. Piepowder describes a
proposed interface with Symbolon and RegNav; the inspected README does not claim
that connector is implemented. Tallystick identifies a separately retained
foundational draft. Sharing a sports topic with the published institutional
responsibility article does not establish a software dependency.

The teaching exercise is newly written for RegNav's fictional fixtures. Its
README expressly distinguishes it from the coauthored forthcoming book
*ANSWERABLE*. It is not represented as an authorised companion to that book or
as independently evaluated teaching.

These relationships and their limits are recorded beside the relevant catalog
items, with links to the source documentation.

## Citation and reuse

Copy or export the available citation for the actual source you use. For
software, retain the version and exact repository revision. RegNav's existing
`CITATION.cff` supplies its software citation metadata. Where no CFF file was
present at the inspected revision, the catalog supplies a transparent reference
to that revision using verified metadata. No software DOI or archival-service
connection is invented.

The publication entries follow the linked University of Groningen records.
The Singapore/Thailand article records DOI
[10.1163/22134514-bja10122](https://doi.org/10.1163/22134514-bja10122).
No DOI is supplied for the other two articles in the inspected institutional
records, so those fields remain empty.

Citation metadata grants no reuse licence. RegNav and Piepowder retain their
reserved-rights positions. Source Watch and Symbolon use Apache-2.0 for their
covered original material. Tallystick's original code and documentation use
Apache-2.0, while its original schemas and format definitions use CC BY 4.0.
Third-party material keeps its own terms. Follow the exact rights link on each
project entry.

## Notes and feedback

The lab's notes and exports are for the visitor's own working record. Downloaded
notes do not become a contribution or a completed human-review declaration.
Submitting feedback is a separate action on GitHub: opening the form or using
the lab does not send a message automatically.

Use the [feedback form](https://github.com/Albertito-AI/Albertito-AI/issues/new?template=lab-feedback.yml)
for an observed navigation problem, broken link, inaccessible control or unclear
explanation. Include the page, intended task, actual result and enough
non-confidential detail to reproduce it. Public issues must not contain client
documents, student or participant identifiers, private manuscripts or credentials.

The [usability protocol](LAB_EVALUATION.md) separates actual outside observations
from internal engineering checks. External usability and educational evaluation
remain pending until real observations are collected and recorded.

## Maintenance

The catalog is maintained text, not a live scrape or a current-law service.
Before changing an item, inspect its primary source, retain its exact revision
where available, check metadata and rights, and update only the inspection date
for the work actually performed. Preserve contrary evidence and unknown fields.

Do not replace a source date merely because the site was redeployed. Do not
convert an AI-prepared source-inspection note into human verification. Record
external use, feedback and independent review only when they actually occur.

The profile's [visibility policy](PORTFOLIO_VISIBILITY_POLICY.md) continues to
govern publication. Private institutional records, confidential research inputs
and participant data remain outside this public repository.
