# Structured input contract v0.1

The JSON examples are complete runnable fixtures. Field names are strict;
unsupported fields and duplicate JSON keys are rejected. JSON Schema
meta-validation is not claimed: the implementation uses a custom strict validator.
The report is not a signature, an authenticity proof or an official court record.

## Top level

Required: `schema_version` (exactly `0.1`), `profile`, `submission`, `sources`,
`claims`. Optional lists: `arithmetic`, `chronology`, `arguments`, `requests`,
`responses`. Identifiers must be unique within each collection. Unknown IDs
referenced by a valid structure produce an itemised finding rather than a silent
match. Maximum input is 5 MiB; collections and per-source locators are limited
to 1,000 items, and evidence links to 100 per claim.

`profile` has `id`, `version`, `jurisdiction`, `stage`, `status`. Status may be
`fictional` or `unvalidated` only. It selects descriptive scope, not a hidden legal
rule engine. No court-approved profile exists in this alpha.

`submission` has `id`, `title`, `jurisdiction`, `stage`, `blocks`. Each block has
an `id` and non-empty `text`. Blocks retain the original supplied text. Claim
annotations must match a whitespace-normalised substring of their stated block.
That limited anchor check does not validate all of an annotation's interpretation.

## Source and citation records

Each source has `id`, `kind` (`authority` or `exhibit`), `title`, `citation`
(possibly empty), `jurisdiction`, `version`, `origin`, `completeness`
(`complete`, `partial`, `unreadable`) and `locators`. Origins are display-only
metadata: the program does not open file paths or URLs supplied inside JSON.

`locators` maps explicitly typed location strings to supplied text. Examples:
`para:42`, `pdf-page:5`, `printed-page:iv`, `section:12(2)`. Physical PDF pages and
printed pages must be mapped separately by the future ingestion layer. A source
labelled complete is only a supplied declaration of transcription coverage.

Optional `expected_text_digest` is a lowercase SHA-256 of `canonical_bytes(locators)`.
The canonicalisation is specific to this program: UTF-8, sorted JSON object keys,
compact separators, no non-finite numbers and non-ASCII characters retained.
This pins a transcription; it is not a digital signature or provenance validation.

Each claim has `id`, `block_id`, `text`, `kind` (`fact`, `allegation`,
`legal_argument`, `inference`) and an `evidence` list. Each reference has
`source_id`, `locator`, `quotation`, and optional `cited_as`. An empty quotation
is allowed for a paraphrase but is explicitly not quotation-checked. A citation
metadata mismatch can be a legitimate variant and requires checking.

Matching normalises whitespace only. It does not repair OCR, punctuation, case,
translation, ellipses or citation style. A quotation matched at a different
location is flagged, never silently reassigned. Matching a substring does not
establish that omitted qualifications are immaterial.

## Bounded logic and coherence annotations

Optional claim `assertion` has six strings: `key`, `context`, `position`,
`scenario`, `unit`, `value`. Different values are compared only within identical
first-five-field groups. This is an inconsistency candidate, not proof of falsity.
Names, dates, scopes, alternative cases and party positions must be mapped by the
operator; the alpha does not infer them from prose.

Each arithmetic record has `id`, `block_id`, `components`, `total`, `unit`.
Amounts are bounded decimal strings, not binary floats. Only addition in one
declared unit is supported. The operator must map the numbers and their meaning;
no currency conversion, tax, interest or damages rule is applied.

Each chronology record has `id`, `block_id`, `description`, `earlier`, `later`.
Dates must be valid `YYYY-MM-DD`. It tests only the declared ordering, not an
independently inferred legal or causal requirement.

Each argument record has `id`, `conclusion` (claim ID), `premises` (claim IDs).
Missing IDs and dependency cycles are flagged. Cycles are not by themselves a
logical-fallacy finding, and a graph without cycles is not an argument-validity
certificate. Listed affected nodes may include descendants of a cycle.

## Document-production responses

Each request has `id`, `text`. Each response has `request_id`, `status`,
`source_ids`, `explanation`. Status is `produced`, `withheld`, `not_held`,
`objected` or `unknown`. Non-production explanations are checked for presence
only. Neither the legal sufficiency of an explanation nor waiver of privilege
is determined. Do not supply privileged contents merely to complete a field.

## Outputs and IO

The pure Python API is `check_submission(package) -> report`. The CLI adds the
SHA-256 of the exact input bytes. The pure report is deterministic for identical
input. Each report includes scope limits, findings with next actions, citation
comparisons, source digests, supplied blocks and coverage counts.

CLI exit `0`: reports generated. Exit `2`: invalid input or IO failure. These are
process outcomes, never filing outcomes. Output folders and files are created
exclusively. Cleanup after an ordinary write failure is best-effort, not atomic
transactionality. Real sensitive files are not approved inputs for this alpha.
