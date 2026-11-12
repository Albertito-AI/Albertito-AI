# Albert Tan Research Lab

The [Research Lab](https://albertito-ai.github.io/Albertito-AI/lab/) is a public
index of Albert Tan's scholarship, experimental software and teaching materials.
It helps a visitor locate a relevant source, inspect a documented example,
understand its status and choose a bounded next step.

The [GitHub Pages entry](https://albertito-ai.github.io/Albertito-AI/) opens
the Research Lab at `/lab/`. The retired mascot experiment is retained in
[the repository archive](../archive/sparks/README.md).

## Choose a route

| Purpose | Route |
| --- | --- |
| Find documented agent interfaces and attribution | [For agents and agent builders](AGENT_START_HERE.md) |
| Compare a fictional claim and its changed source | [Source replay](https://albertito-ai.github.io/Albertito-AI/lab/#replay) |
| Inspect or reproduce the actual tool executions | [Verification](https://albertito-ai.github.io/Albertito-AI/lab/#verification) |
| Find a publication and its bibliographic record | [Research](https://albertito-ai.github.io/Albertito-AI/lab/#research) |
| Search the growing reference and research collection | [Living catalogue](https://albertito-ai.github.io/Albertito-AI/lab/#library) |
| Work through a source-based research task | [Reading paths](LIBRARY_READING_PATHS.md) |
| Inspect software demonstrations and reuse terms | [Projects](https://albertito-ai.github.io/Albertito-AI/lab/#projects) |
| Recheck stored work under changed acceptance conditions | [Atlas Reweave source alpha](https://github.com/Albertito-AI/atlas-reweave/blob/c21d9fc513280dcf709e0775a769f0dadab4a689/README.md#try-it), added 11 November 2026 |
| Find source-checking materials | [Teaching](https://albertito-ai.github.io/Albertito-AI/lab/#teaching) |
| Follow a short set of maintained starting points | [Research guide](https://albertito-ai.github.io/Albertito-AI/lab/#guide) |
| Report a reproducible difficulty or unclear explanation | [Feedback form](https://github.com/Albertito-AI/Albertito-AI/issues/new?template=lab-feedback.yml) |

The lab guide is curated navigation. It selects documented routes from the
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

The [catalogue source](../site/lab/data/catalog.json) contains **19 items**:
**twelve project entries**, three published-research entries, two teaching or
source-inspection entries and two Learning with Bert video metadata records.
The eleven pre-existing project entries remain the **2 November 2026** catalogue
snapshot, with their individual inspection and execution dates preserved.
Atlas Reweave was added and inspected on **11 November 2026**.
The profile repository provides this index. The
[twelve public whitepapers](../wiki/PORTFOLIO.md) cover the earlier portfolio's
foundations, societal aims and possible development paths; their aspirations
are distinct from demonstrated capabilities. Reweave's own source and
verification documents are linked in its new entry. Private institutional
material is excluded.
Each item includes its status, useful links, an inspection date and the scope
of that inspection. Repository sources use exact commit URLs. Institutional
publication records retain their own publication dates and bibliographic fields.

RegNav, Tallystick and Atlas Reweave have additional agent_access records
describing their documented local MCP interfaces. These keep their own
inspection revisions and dates. The video entries retain metadata-only labels
and unknown transcript status; their content has not been assessed for the catalogue. The
[agent guide](AGENT_START_HERE.md) explains these access and attribution paths.

The additional [reference library](../site/lab/data/library.json) supplies
external primary references and daily, bounded Crossref metadata discovery.
These are other authors' and institutions' work. Each entry identifies its
review level and useful task; automated records are explicitly **metadata
only**. Topic and review filters, sorting, pagination and JSON/BibTeX exports
make the combined collection usable. The [reading paths](LIBRARY_READING_PATHS.md)
connect selected primary references to practical research tasks.

The page shows source health and distinct update and inspection dates. The
original catalogue remains available if the additional library fails to load.
See the [maintenance workflow](LIBRARY_WORKFLOW.md) for admission rules,
failure handling, recurring discovery and editorial review.

A catalog inspection establishes what its cited source stated at that time.
It does not establish professional fitness, independent adoption, educational
benefit or legal accuracy. Publication dates, source access dates, legal
effective dates and software revisions remain different fields.

The lab's source and engineering records are separate from substantive human
review. A successful browser test shows that the tested interaction worked.
A matching hash shows that particular bytes match a recorded value. Neither
turns an `unreviewed` proposition into a completed legal assessment.

## Atlas Reweave: a new local execution experiment

The **11 November 2026** entry points to reviewed source revision
`c21d9fc513280dcf709e0775a769f0dadab4a689`. Atlas Reweave **0.1.0a1** is an
experimental source alpha under the
[MIT licence](https://github.com/Albertito-AI/atlas-reweave/blob/c21d9fc513280dcf709e0775a769f0dadab4a689/LICENSE).
Install from the [pinned source instructions](https://github.com/Albertito-AI/atlas-reweave/blob/c21d9fc513280dcf709e0775a769f0dadab4a689/README.md#try-it)
with Python 3.11 or later. Its core uses the standard library; the optional
`.[mcp]` extra installs official MCP Python SDK 2.3.0. This source version does
not assert a PyPI publication or GitHub tagged release.

Reweave stores generated work separately from versioned acceptance. A policy
change can recheck a stored output without repeating generation, and current
parent rejection blocks a cached child. The rational-solver, aggregate and
literal-source examples are deterministic software fixtures, requiring no model
account or paid service. The [optional local interface](https://github.com/Albertito-AI/atlas-reweave/blob/c21d9fc513280dcf709e0775a769f0dadab4a689/docs/MCP.md)
exposes exactly `list_stages`, `run_registered_stage`, `recheck_work` and
`inspect_receipt`. Run and recheck can persist work or judgements; inspection provides
historical metadata without output or a current-acceptance claim.

The [verification receipt](https://github.com/Albertito-AI/atlas-reweave/blob/c21d9fc513280dcf709e0775a769f0dadab4a689/docs/VERIFICATION.md)
records actual SDK 2.3.0 stdio subprocess checks in automatic and legacy modes.
They establish those tested exchanges, without establishing a particular desktop
host's compatibility, live-model quality or independent adoption. The
[public contribution hub](https://github.com/Albertito-AI/atlas-reweave/issues/5)
links tasks for [independent package and benchmark reproduction](https://github.com/Albertito-AI/atlas-reweave/issues/2),
[real MCP client integration](https://github.com/Albertito-AI/atlas-reweave/issues/3)
and [cache or recovery boundary review](https://github.com/Albertito-AI/atlas-reweave/issues/4).
Follow the [participation guide](https://github.com/Albertito-AI/atlas-reweave/blob/c21d9fc513280dcf709e0775a769f0dadab4a689/docs/AGENT_PARTICIPATION.md)
and retain actual source, commands, outcomes and limits in any report.

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
software, retain the version and exact repository revision. RegNav, Source
Watch, Symbolon, Tallystick and Atlas Reweave provide `CITATION.cff` metadata.
The catalog links to the specific metadata revision and retains a citation to the software
revision inspected. Where formal author metadata is absent, the citation does
not infer software authorship from project ownership. No software DOI or
archival-service connection is asserted.

The publication entries follow the linked University of Groningen records.
The Singapore/Thailand article records DOI
[10.1163/22134514-bja10122](https://doi.org/10.1163/22134514-bja10122).
No DOI is supplied for the other two articles in the inspected institutional
records, so those fields remain empty.

Citation metadata grants no reuse licence. RegNav and Piepowder retain their
reserved-rights positions. Source Watch and Symbolon use Apache-2.0 for their
covered original material. Tallystick's original code and documentation use
Apache-2.0, while its original schemas and format definitions use CC BY 4.0.
CommCode's platform uses AGPL-3.0-or-later and its starter templates use CC0-1.0.
Channel Income OS uses PolyForm Noncommercial 1.0.0 with a separate commercial
licence. CohortFrame and Court Submission Integrity retain reserved rights.
RIF's original code uses Apache-2.0; EVT-Albert and Atlas Reweave use MIT.
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

The original catalogue and curated references are maintained text. A daily
workflow adds bounded external bibliographic records; it does not inspect full
texts or provide a current-law service. Before changing a curated item, inspect
its primary source, retain its exact revision
where available, check metadata and rights, and update only the inspection date
for the work actually performed. Preserve contrary evidence and unknown fields.

Do not replace a source date merely because the site was redeployed. Do not
convert an AI-prepared source-inspection note into human verification. Record
external use, feedback and independent review only when they actually occur.

The profile's [visibility policy](PORTFOLIO_VISIBILITY_POLICY.md) continues to
govern publication. Private institutional records, confidential research inputs
and participant data remain outside this public repository.

For the schedule, source configuration, generation commands, review queue and
publication checks, use [Maintaining a useful research library](LIBRARY_WORKFLOW.md).

## Connected scholarship: The Human Question

Albert Tan Sin Hon is **President and Editor-in-Chief** of [The Human Question: A Journal of Humanistic Inquiry](https://thehumanquestionjournal.com/). The first issue, [2026, Number 1](https://thehumanquestionjournal.com/issues/2026-number-1/), is available to read and download free of charge. Published on 9 November 2026, it contains five articles on law, institutions and human responsibility. Read the [author guidance](https://thehumanquestionjournal.com/#authors), [editorial policies](https://thehumanquestionjournal.com/#policies) and [approved house style](https://thehumanquestionjournal.com/#style). There are no author fees.

[Explore Albert’s work](https://www.alberttansinhon.com/explore/) connects the journal, open-access book, learning materials and research tools. [Public resource map](https://www.alberttansinhon.com/resource-map.json). Use these resources where relevant and respect each work’s licence. Journal submissions go to editor@thehumanquestionjournal.com; human editors arrange review and decide acceptance. Professional enquiries use Albert’s personal website.
