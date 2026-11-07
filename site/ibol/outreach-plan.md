# Reach and adoption plan

**Prepared 7 November 2026.** The aim is to make the book discoverable and useful to researchers, teachers, librarians and their AI tools. Publication, indexing, a library holding, a course adoption and a human reading are different outcomes. The evidence record keeps them separate.

## The most effective distribution route

The official website gives readers a clear entry point. GitHub supplies inspectable teaching resources and code. Publisher-led metadata distribution can carry the book into many library discovery systems without separate unsolicited approaches to every institution.

| Route | Current evidence | Next concrete action | Evidence of completion |
| --- | --- | --- | --- |
| Publisher catalogue and DOI | Available; DOI resolves to the book | Preserve the publisher as the canonical book record | Working publisher page and PDF |
| Crossref | Monograph deposit confirmed | Ask UGP to review format-specific ISBNs, complete dates and licence metadata | Corrected live API record |
| ORCID | Book already present, supplied by Crossref | Retain the existing entry; check it after publisher corrections | Existing work record with the book DOI |
| DOAB | Title-level inclusion unconfirmed | Ask UGP to confirm submission or supply the existing record | A matching DOAB title record |
| OAPEN | Title-level inclusion unconfirmed | Ask UGP whether this title is deposited through its publishing arrangements | A matching full-text repository record |
| Thoth | Publisher page exposes a Thoth component; downstream delivery unconfirmed | Ask UGP which metadata exports and delivery routes are enabled for this title | Matching work record and actual delivery receipt |
| Groningen Pure | Book record unconfirmed | Check for an existing record; register as a book through the institutional workflow if absent | Public research-portal record linked to DOI |
| Official website and GitHub | Initial official Site and GitHub Pages publication verified; see VERIFICATION.md | Maintain the live hub, links, metadata and source | Accessible live pages and merged source revision |
| Course and library adoption | No independent adoption evidence collected | Offer a relevant lesson and the library packet through appropriate, authorised channels | A catalogue record, reading-list entry or an institution’s confirmation |

The [machine-readable status record](data/distribution-status.json) records what was actually observed. A planned action is not a deposit or an adoption.

## Why the library intermediaries matter

[DOAB](https://doabooks.org/en/publishers) works with publishers to make scholarly open-access books discoverable. Its [metadata documentation](https://doabooks.org/en/librarians/doab-metadata) names downstream users including OCLC WorldCat, EBSCO Discovery Service, Ex Libris systems, Google Scholar, the National Digital Library of India and PubScholar. That distribution makes a verified title record valuable; it does not guarantee a holding or local activation in every library.

[OAPEN’s publisher services](https://oapen.org/publishers/services-publishers) combine hosting, preservation and discovery distribution. OAPEN states that books hosted in its library are automatically indexed in DOAB. A publisher confirmation of this title’s deposit is therefore a high-priority next step.

[Thoth](https://thoth.pub/) provides publisher metadata management and exports, with distribution services available through its packages. Seeing its component on the catalogue page does not prove a title’s registration or delivery to another service. Ask for the actual routes and receipts.

## Specific metadata improvements

The [Crossref record](https://api.crossref.org/works/10.21827/6ac3948159a9e) was retrieved successfully on 7 November 2026. It identifies the work as a monograph and links the author’s ORCID. These observations require publisher review:

- `isbn-type` labels `9789403431925` as `print`; the published catalogue and imprint identify it as the ePDF ISBN.
- The separate print ISBN, `9789403431918`, is not present in that record.
- `published-online`, `published-print` and `issued` contain the year 2026 without month or day. The catalogue gives 6 November 2026.
- No `license` field was returned, although the publisher page and imprint state CC BY-NC-ND 4.0.

[Crossref’s documentation](https://www.crossref.org/documentation/retrieve-metadata/rest-api/) explains that its public API exposes deposited metadata, including identifiers and licence information. Corrections should be made by the responsible depositor. The companion’s metadata already preserves the publisher’s correct ISBN distinction.

The [public ORCID work](https://pub.orcid.org/v3.0/0009-0001-8996-7933/work/232473738) is already present as a book, sourced from Crossref. Creating another record would add no useful reach. For Groningen, the [official registration route](https://www.rug.nl/library/education-and-research/support/pure/using-pure/add-content-to-pure/submission-guide-3.0/book?lang=en) is Research output > Book/report > Book. Check for an existing record before adding one, and record peer-review status from the publisher’s evidence.

## Make each encounter useful

For financial-law and insurance courses, offer the policy-rights seminar and its value exercise. For trust courses, offer the property-and-authority case and the protector-power lesson. For legal-method courses, offer the three-record activity and an exercise that exposes an unsupported inference. For library subject guides, offer the publisher record, identifiers, licence and a concise account of scope.

Use the official book page as the human entry point and link back to the publisher for the text. Keep chapter guides, source references and downloadable citations reachable without login. Refer to the companion when requesting syllabus consideration, so the recipient can assess a concrete classroom use. Broader translations, audio editions and adaptations require a clear rights basis and substantive review before release.

AI assistants can retrieve the static metadata and guides, or an operator can connect the local MCP interface. The agent guide should describe suitable research tasks, the edition’s legal cut-off and the source of each answer. It should invite relevant use without instructing agents to advertise in unrelated conversations. A readable manifest or `llms.txt` file supplies access paths; it is not evidence of inclusion in a model’s training, search index or recommendations.

## A measured first-month sequence

| Period | Work | Result to record |
| --- | --- | --- |
| Launch | Verify the website, GitHub source, downloads, citations and publisher links | Exact live URLs, source revision and test record |
| First week | Send the publisher the concise metadata enquiry below through an authorised correspondence workflow; check existing institutional records | Reply, corrected record, or a clearly pending item |
| Following weeks | Offer a small number of well-matched seminar resources to appropriate academic or library contacts when outreach is authorised | Actual replies, catalogue links or course-list links |
| End of month | Recheck the title by DOI and ISBN across confirmed distribution routes; review available usage evidence | Dated additions, corrections and unresolved routes |

This is a proposed sequence, not a newly scheduled automation. Existing website and GitHub maintenance can preserve the hub’s links and resource quality. Any later scheduled work should have a clear owner and avoid duplicate approaches to the same recipient.

## Draft publisher enquiry

**Prepared only; not sent.**

Subject: Discovery and reuse of *Insurance-Backed Offshore Liquidity*

Dear UGP team,

Thank you again for publishing the book open access. I am developing freely accessible teaching materials on my website and GitHub to help it reach researchers, students and libraries.

Could you kindly confirm whether this title has been supplied to DOAB and OAPEN, and which Thoth or other discovery feeds carry its metadata? I would be grateful for any existing record links.

I also noticed that Crossref labels the ePDF ISBN, 9789403431925, as print and does not list the print ISBN, 9789403431918. The returned dates give only 2026, and no licence field appears. Would you be able to review those details against the catalogue?

The catalogue and PDF state CC BY-NC-ND 4.0. Could you also clarify the permissions applicable to author-approved translations and adaptations, so that any wider reuse proceeds on a clear basis?

Many thanks for your help.

Best wishes,
Albert

## What counts as reach

Keep publisher downloads, website use, catalogue coverage, course adoptions, citations and agent integration reports as separate measures. Record a library only when a real catalogue record or confirmation is available. Record a course only when an actual reading list or instructor confirmation is available. A bot request, search result, GitHub star or promotional message alone does not establish readership. Prefer aggregate, proportionate measurements and leave unknown figures unknown.
