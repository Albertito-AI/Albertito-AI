# Court integration design | proposal, not implemented service

## Product position

A court-controlled submission-integrity service: produce specific, inspectable
review questions before substantive judicial consideration. The shared engine is
international; law, procedure, document type, language, source rights and court
interfaces require separate validated profiles. A citation recogniser is not a
jurisdictional approval.

There are three distinct use modes. A filer-facing preflight tool helps a person
correct or explain defects before filing. A registry-side shadow tool produces
flags without delaying or deciding acceptance. A judicial-staff review workspace
presents source passages and unresolved issues. These modes require different
access controls and must not leak private filer drafts or one party's privileged
material to another party or to judicial staff.

## Proposed service boundary

Court interface -> permitted document store -> quarantined extraction worker ->
versioned review engine -> source-linked report -> authorised human disposition.

The court's existing platform remains authoritative for identity, case permissions,
filing receipt, service, docket status and case-management decisions. GitHub stores
source code and fictional fixtures, not operational case material. The alpha has
no live server, authenticated API, docket-write permission or deployed adapter.

A future adapter should accept an authenticated envelope identifying submission
version, document hashes, court/proceeding/document type, language, rules-pack
version and a permitted source-policy version. The identifier of an uploaded
file must not itself give permission to retrieve another case's evidence.

The response should carry input and engine versions, extraction/source coverage,
findings by code, exact submission/source spans, reasons, source freshness,
unresolved questions and no automated disposition. Repeat requests with identical
versions should be idempotent. Updated submissions or source versions require a
new report, with the earlier input/report preserved under the court's retention
policy. A report hash alone is not an authenticated audit trail.

## Independent source verification

Do not authenticate an authority from a filer-provided excerpt, URL or hash.
A governed resolver should use approved official/appropriately licensed sources,
record exact versions and retrieval provenance, validate identity and reconcile
legitimate citation variants. Restrict egress and redirects, bound retrieval,
isolate parsers and never follow arbitrary document URLs. Report unavailable,
not found within the searched corpus, conflicting identity and incomplete
coverage separately. Current-law/treatment checking requires its own reliable
coverage and legal review. Matching a real citation is not good-law certification.

## Semantic review remains review assistance

A later semantic layer may propose issue maps, evidence links, omitted premises,
contextual quotation warnings and coherence questions, each attached to passages
that a human can inspect. Preserve alternatives, allegations, opposing accounts,
exceptions and adverse evidence. Never infer dishonesty from language style,
source unavailability or a model disagreement. Do not rank parties or lawyers.

Provider choice, model/prompt version, input rights, data handling, confidentiality,
resource limits and independent evaluation must precede model activation. An
internal second model is not an independent authoritative source or a human reviewer.
The current code has no model provider or budget commitment.

## Justice and operational gates

Do not automatically refuse, delay, penalise or deprioritise a filing based on
machine-generated flags. Preserve original receipt times, urgent/manual routes,
correction and challenge mechanisms, and accountable human decisions. Do not
make a weakly supported allegation in a pleading into an automatic documentary
failure where that procedural stage does not require proof of every allegation.

Before real use: court permission, exact local legal/procedural review, source
licences, approved confidentiality and hosting arrangements, isolation of sealed
and privileged records, authenticated roles, encryption, controlled audit history,
retention/deletion, incident handling and independent security testing. Whether
additional AI regulation applies depends on jurisdiction and actual function;
this design is not a jurisdiction-wide compliance opinion.

Use a read-only shadow pilot only after a permitted independent test corpus has
established useful performance and acceptable false-alarm rates. Measure the whole
workflow, including filer corrections, registry review, escalation and support.
A larger number of flags or passing unit tests is not evidence of backlog reduction.

OASIS LegalXML ECF is an interoperability reference, not a universal court API.
The OASIS committee lists ECF 5.01 (2023) as well as 5.0 (2019). Verify the actual
platform's supported version and interfaces before implementing any adapter.
No conformance to either specification is claimed by this alpha.
