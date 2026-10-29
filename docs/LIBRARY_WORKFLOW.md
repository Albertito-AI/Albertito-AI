# Maintaining a useful research library

The [Research Lab catalogue](https://albertito-ai.github.io/Albertito-AI/lab/#library)
combines Albert Tan's research, project, teaching and selected video records with
external primary references and a bounded stream of research metadata. Its
purpose is to help someone find a source, understand what it can support and
take a useful next step. A growing record count alone does not establish value.

## What visitors can use

- Search titles, authors, publishers, topics and the task a reference supports.
- Filter by type, topic and review level; sort by addition date, publication
  date or title; browse twelve records per page.
- Inspect source links, dates, limitations, rights information and citations.
- Export every matching record as JSON or BibTeX, including matches on other
  results pages. BibTeX uses conservative `@misc` records; check the source and
  the required citation style before submitting a bibliography.
- Follow one of the [three reading paths](LIBRARY_READING_PATHS.md): build a
  sustainability-reporting comparison, design an observable AI evaluation, or
  distinguish provenance, credential integrity and trust.
- [Suggest a source or correction](https://github.com/Albertito-AI/Albertito-AI/issues/new?template=library-source.yml).
  Suggestions become public issues only when their author submits them. They
  are not automatically admitted to the catalogue.

External works retain their actual authors and issuing institutions. Inclusion
does not represent them as Albert Tan's publications or imply endorsement.

## Two publication routes

| Route | Admission evidence | What its label means |
| --- | --- | --- |
| Curated primary reference | Inspect the original source; record its identity, exact version where available, actual inspection scope, useful task, limitations and rights link | **Source inspected** records the inspection described on that entry. Initial references are AI-prepared source inspections, not independent professional approval. |
| Automated research discovery | Crossref bibliographic fields, required authors/title/publisher/DOI/date, allowed record type, configured title or subject matches, duplicate and update-notice checks | **Metadata only** is a research lead. The pipeline has not read the article, visited its DOI landing page, certified peer review or confirmed free access. |
| An entry with an unresolved issue | Detected publisher update, failed admission checks on a previously indexed record, or overdue curated inspection | **Needs review** retains the record and explains the outstanding question. |

The original records remain in [`catalog.json`](../site/lab/data/catalog.json).
Additional records are generated into
[`library.json`](../site/lab/data/library.json). The browser loads these
independently. Failure to load the additional library does not remove the
original catalogue or the separate source-replay exercise.

## Selected YouTube resources

The manually maintained original catalogue can include individual videos from
the existing Bert Chan and Learning with Bert channel and collections. This is
a bounded editorial route; the Crossref workflow below does not ingest YouTube.

Record the canonical video URL and ID, actual uploading channel, creator or
curator role, available date, topic, useful question, rights and inspection
scope. Public title or description metadata supports a metadata-only lead.
Keep transcript availability unknown until checked. Do not invent a summary,
timestamp, quotation, chapter or underlying source from a video title.

For a content-reviewed record, inspect the recording or an authorised
transcript, verify quotations and timestamps, identify underlying sources, and
state the actual scope. Keep original content and curated third-party work
separately attributable. Transcript or excerpt republication must respect the
applicable rights. Caption access and a public video link are different matters.

Use stable video IDs for deduplication and retain unavailable-item history.
Coordinate this curation with the existing Daily Website Resource Refresh;
channel-wide ingestion and native YouTube edits require their own implemented,
authorised access. The two records added on 29 October 2026 are metadata-only.

## Daily discovery and publication

The [Research library refresh workflow](../.github/workflows/library-refresh.yml)
is scheduled for **08:23 Asia/Singapore every day**, which is `00:23 UTC`.
GitHub can delay scheduled runs. Maintainers can also select **Run workflow**;
changes to source configuration or the ingestion implementation trigger a run
on `main`.

1. Run the offline ingestion tests, then query the public Crossref Works API
   for the three collections in
   [`library_sources.json`](../config/library_sources.json): ESG disclosure
   and accountability, AI governance and agent evaluation, and legal evidence
   and provenance.
2. Check recently indexed metadata and advance a bounded historical discovery
   scan. Discovery state and pending candidates are retained between runs so
   the process can move beyond the same first results page. The query windows,
   page sizes and retained-candidate bounds are explicit configuration or code,
   not a claim to cover all research.
3. Apply deterministic admission rules. Admit at most **three new records per
   collection and nine in total per Singapore calendar day**. Rerunning a job
   does not reset that budget. Repeated chapters from the same book are bounded
   to avoid filling a day's collection from one volume. A run can add zero
   records when none qualifies.
4. Deduplicate normalised DOI and canonical source URL against both existing
   collections. Keep stable IDs and original addition dates. Retain qualified
   pending candidates within the configured bound rather than treating a
   daily admission cap as a quality rejection.
5. Recheck up to six previously indexed DOI records per run. Detected
   correction, withdrawal or retraction information produces a review flag.
   Crossref coverage and publisher deposits are incomplete, so absence of a
   flag does not establish that a work is unaffected.
6. Validate the library and prepare the editorial queue and history before
   writing them. Commit only those three generated JSON files with the workflow's
   repository token. Refuse to overwrite a concurrently advanced `main`.
7. Call the Pages workflow explicitly for the new commit, verify the published
   bytes and run the browser journeys. A token-created data commit alone does
   not start a second push-triggered workflow. A newer change to the site's
   content prevents an older deployment; unrelated profile-only changes do
   not block identical site content.

The retrieval uses Python's standard library and the public Crossref API. It
requires no model subscription or additional API key. Network requests are
bounded by time, response size and retry count and restricted to the fixed
Crossref HTTPS endpoint, including redirects. The outputs do not retain or
republish abstracts or full articles. DOI rechecks may receive additional
registry fields, which are discarded. The workflow does not retrieve full
articles, private repositories or user documents.

The metadata API and GitHub Actions are external services. This design provides
recurring attempts and visible outcomes, not a guarantee of uninterrupted
availability or a complete scholarly index.

## Failure, freshness and recovery

The public library records each collection's attempt, successful retrieval
time, accepted count and failure. A failed request retains earlier records and
their actual dates. A partially successful run is **degraded**; a completely
failed retrieval is **failed**. Neither is reported as a fully successful
refresh. A failure does not turn an empty response into a destructive reset.

The site shows the latest attempt, last successful source refresh, most recent
recorded curated inspection and original catalogue date separately. A success
more than **48 hours** old displays as overdue, using the visitor's browser
clock. Individual cards retain their own dates and inspection scope; an overall
recent update does not mean every item has just been checked.

A valid degraded snapshot may still be published so visitors can see the
problem. The final source-health job then fails visibly in Actions. If
validation, concurrent changes or deployment prevents publication, the last
published site remains available. Its age indicator and the Actions run are
the evidence of the outstanding refresh, rather than an invented success date.

To recover, inspect the
[workflow runs](https://github.com/Albertito-AI/Albertito-AI/actions/workflows/library-refresh.yml),
resolve the actual error, and rerun from current `main`. Do not reset timestamps
or delete the previous collection to make a check pass. The rolling public
[history](../site/lab/data/library-history.json) retains up to 365 run records;
commits provide the longer change history.

## Weekly editorial work

Automated discovery supplies candidates. A weekly editorial pass should turn
one worthwhile candidate into a more useful reference or resolve an important
existing defect. There is no obligation to publish a weak addition to meet a
quota. Start with the
[review queue](../site/lab/data/library-review-queue.json), prioritising update
flags, stale sources and the three supported reader tasks.

For a candidate, read the accessible original primary source. Record what was
actually inspected and its precise location, who issued or authored it, the
relevant date or version, one practical question it helps answer, the source's
limits and a permitted route to access it. Write a brief original description
and a concrete `use_for` sentence. Do not infer claims from a title, copy a
restricted text, or promote a metadata check into substantive source inspection.

Add the reviewed record to
[`library_references.json`](../config/library_references.json), preserving its
existing ID and DOI if it is already indexed. Changing its origin to a curated
reference must retain the original addition date and truthful inspection
history. Link it to an existing reading path when the relationship helps a
reader perform that task. A source removed from active configuration is retained
and flagged until an explicit editorial decision resolves it.

Source inspections older than the configured **90-day** interval are flagged
for review. A legal or policy source may need checking sooner for the actual
question being answered. No catalogue label establishes current applicability
or supplies a legal conclusion.

Use a pull request for editorial changes. Check for overlapping work, run the
offline tests and validation, inspect the diff and browser results, then merge
and verify the publication. The daily workflow owns generated metadata files;
editorial work changes the source configuration and explanations.

## Reproduce and maintain

From a checkout with Python 3.12:

```sh
python -m unittest discover -s tests -p 'test_library*.py' -v
python scripts/library/refresh.py --check
python scripts/library/refresh.py --refresh
```

The first two commands use no network. The last makes bounded public metadata
requests and regenerates the three JSON outputs. After editing curated
references, `--curated-only` rebuilds those records without claiming a new
source retrieval. `--check` validates an existing snapshot; it does not update
it. Review all generated changes before publishing.

The [research-lab checks](../.github/workflows/research-lab.yml) exercise the
combined catalogue, filters, exports, pagination, failure recovery and existing
source replay. The [Pages workflow](../.github/workflows/sparks-pages.yml)
compares every published site file to its checkout and repeats the browser
journey on the public URL. These are engineering checks, distinct from
independent scholarly or usability review.

## How to judge whether the library helps

Review the recorded evidence, not an automatic growth target:

| Question | Evidence available now | Further evidence needed |
| --- | --- | --- |
| Is the pipeline operating? | Last success, per-source outcomes, Actions and public history | Observe subsequent scheduled runs |
| Is discovery relevant and varied? | Topic matches, source identity, review queue and admission reasons | Editorial assessment of actual candidate usefulness |
| Can someone find and reuse a source record? | Search/filter/export journeys and source links | A reader completing a declared research task |
| Does the material support better research or teaching? | Scoped reading paths and transparent limits | Actual observations under the [usability protocol](LAB_EVALUATION.md) |

No visitor-count, educational-benefit or independent-adoption claim is inferred
from passing tests. Use real feedback to refine the collections and reading
paths. Add another provider or topic only when it fills a demonstrated gap and
its access, attribution, preservation and review rules are defined.

## Upstream implementation references

- [Crossref REST API use and synchronisation guidance](https://www.crossref.org/documentation/retrieve-metadata/rest-api/tips-for-using-the-crossref-rest-api/)
- [GitHub workflow triggering and repository-token behaviour](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow)
- [GitHub reusable workflows and permission rules](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows)

The repository's [visibility policy](PORTFOLIO_VISIBILITY_POLICY.md) applies to
every change. Public bibliographic access does not grant a full-text reuse
licence. Personal data, client material, private manuscripts and credentials
remain outside this library.
