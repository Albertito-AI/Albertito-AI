# External reference reading paths

These paths use primary resources issued by SGX, the IFRS Foundation, the Thai
SEC, NIST, the OECD and W3C. They are external authors' and institutions' work.
They are included to support visitors' research and evaluation; they are not
Albert Tan's publications or endorsements of the lab.

The ten records are maintained in
[`config/library_references.json`](../config/library_references.json).
Each linked identifier below is the exact catalogue item ID and opens its
official source. Source inspection was completed on **29 October 2026 at
00:00:46 UTC**. The review covered the sections described in each record, not
every provision or linked document. `source_inspected` records AI source
inspection and does not mean independent human approval.

## Path 1: Build a defensible sustainability-reporting comparison

**Useful question:** Which instrument supports each reporting proposition, and
which questions remain outside that source?

1. Open SGX
   [reference-sgx-mainboard-711a](https://rulebook.sgx.com/rulebook/711a)
   and [reference-sgx-mainboard-711b](https://rulebook.sgx.com/rulebook/711b).
   Write separate propositions about report timing and report content. Record
   the Mainboard scope and the version shown. The inspected pages display the
   version from 1 January 2026; an analysis of an earlier period needs the
   appropriate historical text.
2. Use
   [reference-ifrs-s1](https://www.ifrs.org/issued-standards/ifrs-sustainability-standards-navigator/ifrs-s1-general-requirements/)
   to identify the standard's disclosure objective. Then ask which domestic
   instrument makes a requirement applicable to the issuer being studied.
   Keep the standard, its public overview and local implementation separate.
3. Open
   [reference-thai-sec-one-report](https://www.sec.or.th/TH/Pages/LawandRegulations/OneReport.aspx)
   and locate the actual notification and form needed for the comparison.
   The hub contains material associated with different amendments. Record
   the selected document's identifier, date and language before extracting a
   substantive proposition.
4. For each proposition, retain an exact provision or paragraph and a short
   original explanation of why it supports the claim. Identify any omitted
   cross-reference, transition rule or translation issue.
5. Test the comparison: have you shown a disclosure duty, an enforcement
   power, a private remedy, or only a research lead? Obtain separate authority
   for each additional proposition.

**Produce:** a small authority matrix with these columns:

| Question | Exact source and pinpoint | Version and language | Supported proposition | Further check |
| --- | --- | --- | --- | --- |
| What is the reporting timetable? | Selected Rule 711A text | Record the relevant version | Write only what that text supports | Issuer facts and related provisions |
| What must the report address? | Selected Rule 711B provisions | Record the relevant version | Separate each component | Referenced guidance and applicability |
| What is the Thai comparator? | Selected notification and form | Record identifier and language | Leave blank until inspected | Translation and period of application |

A useful result may contain an unresolved cell. Filling a gap with an assumption
would obscure the next research task. The lab's RegNav exercise can help organise
such a record, but these reading paths do not establish its legal conclusions.

## Path 2: Turn an AI principle into an observable evaluation

**Useful question:** What evidence would justify a particular claim about one
AI-assisted feature?

Start with a fictional feature: an assistant proposes citations for a research
note about sustainability reporting. Define its input, intended users, output
and the decisions it must leave to a reviewer.

- Read
  [reference-oecd-ai-2019](https://oecd.ai/assets/files/OECD-LEGAL-0449-en.pdf)
  as the original 2019 policy text. Choose an accountability or transparency
  question to investigate. The
  [official instrument record](https://legalinstruments.oecd.org/en/instruments/OECD-LEGAL-0449)
  is the route for checking later amendments. Its text required JavaScript
  during this inspection, so no current amended wording is reproduced here.
- Use
  [reference-nist-ai-rmf-1](https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-ai-rmf-10)
  to organise responsibility, context, measurement and the response to a
  failure. Start with Part 2, section 5, which describes the four Core functions.
- Consult
  [reference-nist-genai-profile](https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence).
  The official PDF's section 2.2 discusses confabulation. Suggested action
  MS-2.5-003 addresses checking generated sources and citations; MS-2.5-001
  cautions against broad capability claims from narrow assessments.

**Prepare and then run a bounded evaluation:**

1. Select a small, declared set of public questions. Include an ambiguous
   question and a source that has changed. Record why this set was chosen.
2. Retain the exact model or system version, inputs and outputs.
3. Check whether each proposed source exists, whether the pinpoint is correct
   and whether the passage supports the proposition. Record these as separate
   outcomes.
4. Retain missing citations, unsupported propositions and reviewer disagreement.
   Do not replace failed examples with more favourable ones.
5. Define an owner and next action for each failure, such as narrowing the
   feature's claim or requiring a source check before its output is used.

**Produce:** an evaluation record containing the task boundary, sample selection,
observations, remaining uncertainty and a justified next decision. This exercise
is a proposed method. It supplies no completed test results, certification or
claim of general system safety.

## Path 3: Separate provenance, credential integrity and trust

**Useful question:** What does a recorded chain or verified credential actually
allow a reader to conclude?

1. Read the core structures in
   [reference-w3c-prov-dm](https://www.w3.org/TR/2013/REC-prov-dm-20130430/).
   Sketch a fictional source capture, an analysis activity, the resulting note
   and the actor responsible for that activity. Give a corrected note its own
   identity and preserve its relation to the earlier note.
2. Use the starting-point vocabulary in
   [reference-w3c-prov-o](https://www.w3.org/TR/2013/REC-prov-o-20130430/)
   to compare that sketch with an exchangeable provenance model. Document
   proposed mappings and any relationship your local schema cannot express.
   No PROV conformance is claimed for the lab's projects.
3. Read the ecosystem overview, verification definition and trust-model
   discussion in
   [reference-w3c-vc-2](https://www.w3.org/TR/2025/REC-vc-data-model-2.0-20250515/).
   For a fictional course credential, identify the issuer, holder, verifier,
   assessment claim, securing mechanism and relevant status checks.
4. Ask two further questions: what evidence supports the issuer's assessment,
   and why should this verifier accept that issuer for this purpose? Credential
   verification does not settle the truth of the underlying assessment claim.

**Produce:** three separate notes: a lineage sketch, a proposed credential
structure and a trust decision with its reasons. For example, recording who
created an assessment file, checking a credential's protection against alteration
and deciding whether the assessment demonstrates competence are distinct tasks.

Use fictional identities and results for this exercise. It neither issues a
credential nor records an actual learner's performance.

## Citation, rights and maintenance

Use the citation attached to the source you actually consulted. Institutional
attribution identifies the external issuer; follow the source record for named
authors and editors. The catalogue keeps publication, adoption, amendment and
inspection dates distinct. Unknown publication dates remain empty.

The records provide links, bibliographic metadata and brief original
descriptions. Public access does not itself grant reuse rights. Follow the
source's terms before reproducing material.

Before relying on a changing rule or policy, reopen the source, select the
relevant version and record what was inspected. An updated catalogue date
records an actual inspection, not a guarantee that every linked source is
current or applicable.

