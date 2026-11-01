# Primary-source research register

Consulted 1 November 2026. These are product-design references, not an exhaustive
legal opinion, implemented rule pack or claim of court endorsement. No publisher
PDF is redistributed in this package. Author interpretation is separated from
what the source says. Recheck operative versions before deployment.

| Source | Version and pinpoint | Relevance and limit |
| --- | --- | --- |
| Singapore Courts, Guide on the Use of Generative Artificial Intelligence Tools by Court Users | Applies from 1 October 2024; paras 3(2), 5(1), 5(3)(c)-(e); printed p 3 / physical PDF p 4 for para 5 | Requires source/proposition and quotation verification; another generative system's confirmation is insufficient. This supports source-grounded review, not delegating responsibility to this program. |
| Tajudin bin Gulam Rasul and another v Suriaya bte Haja Mohideen [2025] SGHCR 33 | 29 September 2025, paras 2-3, 37-38 | Addresses fictitious authority, accuracy and judicial/counterparty resources. It does not quantify our product's likely impact. |
| Ayinde v London Borough of Haringey; Al-Haroun v Qatar National Bank [2025] EWHC 1383 (Admin) | 6 June 2025, paras 3, 6-8, 36 | Identifies unchecked false material and independent authoritative-source checking; para 36 illustrates a valid neutral citation assigned to the wrong case. It does not authorise automated filing refusal. |
| Singapore Courts, Production of documents (from 1 April 2022) | Court guidance displayed update 5 March 2026; sections “What production means” and “Affidavits of evidence-in-chief before production of documents” | Helps separate document-production duties from legal-argument checking. The actual governing rule and case-specific order must be checked before operational use. |
| Judiciary Times, September 2026 | “Hackathon for a Better World”, printed p 9 / physical PDF p 6 | Reports CiteCheck SG's citation-validation proposal. Evidence of an adjacent initiative, not independent verification of that product's accuracy or live deployment. |
| Council of Europe, CEPEJ European Ethical Charter on AI in judicial systems | Adopted December 2018; five principles, particularly transparency and user control | Ethical design reference; not treated as identical binding law worldwide. |
| OASIS LegalXML Electronic Court Filing committee / standards index | ECF 5.01, Committee Specification 01, 29 September 2023; also lists ECF 5.0 (2019) | Committee and standards-index versions inspected; direct 5.01 specification fetch failed. No conformance or universal court compatibility is claimed. |

## Exact source URLs

- Singapore guide: https://www.judiciary.gov.sg/docs/default-source/news-and-resources-docs/guide-on-the-use-of-generative-ai-tools-by-court-users.pdf
- Singapore judgment: https://www.elitigation.sg/gd/s/2025_SGHCR_33
- England and Wales judgment: https://www.judiciary.uk/wp-content/uploads/2025/06/Ayinde-v-London-Borough-of-Haringey-and-Al-Haroun-v-Qatar-National-Bank.pdf
- Document production: https://www.judiciary.gov.sg/civil/civil-claims-(from-1-april-2022)/prepare-a-civil-case-for-trial-(from-1-april-2022)/production-of-documents-(from-1-april-2022)
- Judiciary Times: https://www.judiciary.gov.sg/docs/default-source/publication-docs/judiciary-times---sep-2026.pdf
- CEPEJ Charter page: https://www.coe.int/en/web/cepej/cepej-european-ethical-charter-on-the-use-of-artificial-intelligence-ai-in-judicial-systems-and-their-environment
- OASIS committee: https://www.oasis-open.org/committees/tc_home.php?wg_abbrev=legalxml-courtfiling
- OASIS standards index: https://www.oasis-open.org/standards/
- pypdf extraction documentation: https://pypdf.readthedocs.io/en/stable/user/extract-text.html (consulted for extraction limitations, including resource use; installed test parser was 5.9.0)

## Design decision

Keep source availability, pinpoint/text matching, substantive support, factual
truth and human review as distinct states. Implement a report of concrete findings
and unresolved questions, not a single credibility or truth score. This is our
engineering choice informed by the sources, not a judicially approved method.
