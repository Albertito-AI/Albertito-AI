# Catalogue and discovery routes

This guide records practical routes for discovering Albert Tan Sin Hon’s *Insurance-Backed Offshore Liquidity* and supplying accurate bibliographic data. Checks are dated 7 November 2026. A catalogue record, local library holding, course adoption and human reading require separate evidence. No catalogue submissions or messages were sent during this review.

## Practical priorities

The priorities below are an assessment of the verified routes, not promises of inclusion. Publisher and institutional workflows can improve several downstream records while reducing duplicate approaches.

| Action | Appropriate route | Evidence needed to mark it complete |
| --- | --- | --- |
| Correct the deposited metadata and establish distribution status | One coordinated UGP enquiry covering Crossref fields, DOAB/OAPEN, WorldCat and Google Books | Corrected API fields and title-specific record links or explicit pending states |
| Establish the institutional record | Author’s authorised Pure account or Groningen library support; search before claim or creation | Validated, public book record with the exact DOI and checked full-text link |
| Offer an immediately usable teaching resource | One original CC BY seminar through OER Commons or MERLOT after duplicate checking | Submitted record, then separately its public approval/listing outcome |
| Approach a small number of relevant libraries through expressly available routes | [Cambridge’s open-access link donation](https://libguides.cam.ac.uk/cambridgeebooks/faqs) and [Radboud’s external-suggestion route](https://www.ru.nl/en/staff/services/library/retrieving-literature-or-borrowing-materials/making-a-purchase-suggestion) | Actual response or catalogue/guide permalink; consideration remains separate from acceptance |
| Improve additional catalogue coverage where a fresh check identifies a gap | Open Library work/edition workflow or a specific OpenAlex report, with verified identity and evidence | Saved catalogue record or corrected OpenAlex lookup, with no duplicate work |

Cambridge and Radboud were independently rechecked in the final cross-review. Cambridge accepts suitable open-access ebook links on stable sites, subject to collection fit, rather than files requiring hosting. Radboud explicitly permits suggestions from anyone but prioritises affiliated staff and students. Other universities in the [library-route guide](library-routes.md) have differing membership and authentication requirements. None of these routes has received a campaign request.

A public [OAPEN library-services page](https://oapen.org/librarians/services-libraries), retrieved in the final review, provides current metadata and integration guidance. Use it in place of the earlier legacy services URL. A general integration statement remains different from evidence that this particular book is present.

## Publisher identity and Crossref

The [publisher catalogue](https://books.ugp.rug.nl/ugp/catalog/book/300) and [Crossref record](https://api.crossref.org/works/10.21827%2F6ac3948159a9e) both returned HTTP 200 in direct HTTPS checks at approximately 10:54 UTC. The publisher’s visible record and citation metadata give publication on 6 November 2026. The [published PDF](https://books.ugp.rug.nl/ugp/catalog/download/300/584/1875), imprint at physical PDF page 6, distinguishes the print and ePDF ISBNs and states CC BY-NC-ND 4.0.

| Field | Authoritative publisher detail | Crossref observation | Next action |
| --- | --- | --- | --- |
| DOI | `10.21827/6ac3948159a9e` | Same DOI; type `monograph`; publisher URL supplied | Preserve this identifier |
| Author | Albert Tan Sin Hon; catalogue order Sin Hon Albert Tan | Family `Tan`, given `Sin Hon Albert`; matching ORCID | Retain the existing identity; ordering alone is not a mismatch |
| ePDF ISBN | `9789403431925` | Present, labelled `print` | Ask the responsible depositor to change its format classification |
| Print ISBN | `9789403431918` | Not returned | Ask the depositor to add the separate print ISBN |
| Publication date | 6 November 2026 | Online and print dates contain only 2026 | Request full dates where confirmed for each format; do not assume the two dates must coincide |
| Licence | CC BY-NC-ND 4.0 | No `license` field returned | Request the publisher’s licence URL in the deposit |

Crossref permits metadata updates to the existing DOI record. The depositor should submit a complete corrected record; creating another DOI would not correct these fields. Its [update guidance](https://www.crossref.org/documentation/register-maintain-records/maintaining-your-metadata/updating-your-metadata/) describes that route. Its [ISBN guidance](https://www.crossref.org/documentation/schema-library/markup-guide-metadata-segments/issn-isbn/) recommends both print and electronic identifiers where applicable.

The [existing publisher enquiry](../outreach-plan.md#draft-publisher-enquiry) is prepared but unsent. A completed correction requires a fresh read of the live Crossref record, rather than a change to this companion. Crossref metadata can support downstream matching; it does not establish a library holding or guarantee indexing by any particular service.

## Reusable evidence

Use the [library packet](../library-kit.md), [machine-readable citations](../metadata/book.csl.json), publisher DOI and exact format-specific ISBN together. Keep the publisher as the canonical book record. Cite this companion separately when describing its original teaching activities.

## DOAB: publisher submission and broad metadata distribution

**Title status: unconfirmed.** Bounded web searches by exact title and ePDF ISBN did not retrieve a matching DOAB record. Earlier direct catalogue access was blocked; no repeated blocked request was made in this round. These observations do not establish that the book is absent. PRISM supplies peer-review metadata and is not a complete substitute for a catalogue search.

DOAB’s [author FAQ](https://doabooks.org/en/researchers/faq) says that publishers submit books. An author should ask the publisher to arrange inclusion. Where a publisher already participates, DOAB can contact it after receiving the author’s title details. There is no author self-upload route to use in place of the publisher.

The [current admission requirements](https://doabooks.org/en/publishers/join-doab) cover scholarly books, independent external peer review, open online access without registration, clear licensing and ISBNs. Publisher-level requirements also apply. The publisher must confirm the title’s peer-review evidence and submission eligibility; an open-access label alone does not establish admission. The book’s actual CC BY-NC-ND 4.0 terms should remain explicit.

The [participating-publisher guide](https://doabooks.org/en/publishers/guidance) assigns responsibility for maintaining book records to publishers and supplies an administrative workflow and bulk-change template. Ask UGP for the existing DOI-matched record or a submission receipt, and for accurate format-specific ISBN and licence metadata. This request is prepared, not sent.

DOAB’s [metadata service](https://doabooks.org/en/librarians/doab-metadata) offers CC0 bibliographic feeds including MARCXML, KBART, ONIX, JSON and CSV, alongside harvesting. Its listed metadata users include WorldCat, EBSCO Discovery Service, Ex Libris systems and Google Scholar. That makes a correct DOAB record a useful distribution route; individual harvesting, local activation, holdings and readership still need separate evidence.

## OAPEN: full-text deposit, preservation and distribution

**Title deposit: unconfirmed.** OAPEN publishes a [UGP peer-review profile](https://www.oapen.org/article/16244634-university-of-groningen-press), which describes the press’s review arrangements. This publisher-level evidence does not establish a deposit of this book. A bounded DOI web search produced no matching title record; the earlier blocked direct catalogue query was not repeated.

OAPEN’s [admission route](https://oapen.org/publishers/join-oapen-library) works with academic publishers and requires information about peer review. Its [upload instructions](https://oapen.org/article/upload-instructions) allow participating publishers to submit metadata through the supplied spreadsheet or ONIX 3.0, together with PDF or EPUB files and a direct original-content link. The authenticated upload account belongs to the publisher.

Ask UGP to confirm whether it has deposited this title, provide a matching repository handle, or arrange a deposit through its existing workflow. The packet should identify the exact DOI, both format-specific ISBNs, ORCID, publication date, subject terms and CC BY-NC-ND 4.0 licence. Preserve the published text and licence; do not relabel the book under the companion’s CC BY licence. Eligibility and any arrangements or charges remain for the publisher to confirm.

OAPEN’s [publisher services](https://oapen.org/publishers/services-publishers) describe metadata distribution to library discovery platforms and automatic DOAB indexing of books hosted in its library. They also identify Portico and CLOCKSS preservation services and a publisher usage dashboard. A successful deposit could therefore support several discovery and preservation routes through one publisher action. Record the actual title handle and downstream records when available; general service integration does not prove this title has reached every platform.

UGP separately states an [archiving policy](https://www.rug.nl/research/ugp/policies-funding/?lang=en) for its books in the Koninklijke Bibliotheek’s e-Depot. That policy is useful background, while a title-specific receipt remains the stronger evidence of completed preservation. OAPEN’s separate EU-funded deposit scheme should only be used where the book’s funding actually meets its criteria; no such eligibility is asserted here.

## WorldCat: bibliographic records and library holdings

**Title record and holdings: unconfirmed in this review.** UGP’s [published policy](https://www.rug.nl/research/ugp/policies-funding/?lang=en) says its books are listed in OCLC WorldCat. That general policy supports asking UGP for this title’s OCLC number and ePDF/print record links. It does not establish that a newly published title has already arrived.

OCLC’s [author instructions](https://help.oclc.org/Discovery_and_Reference/WorldCat-org/Information_for_authors/How_can_I_add_my_work_to_WorldCat) identify an OCLC member library as a route for cataloguing a work. Its [author information](https://help.oclc.org/Discovery_and_Reference/WorldCat-org/Information_for_authors) recommends contacting the publisher or owning institution first when corrections are needed. For this book, request the existing record from UGP before proposing a new one. If none exists, an appropriate member library can consider cataloguing the resource within its selection and cataloguing procedures.

OCLC also has [content-provider partnerships for open-access material](https://www.oclc.org/en/open-access.html). An institutional repository can contribute through the [Digital Collection Gateway](https://www.oclc.org/en/digital-gateway/getting-started.html), using its OAI repository and institutional registration. These are institutional workflows, not a reason to create a new repository or represent the author’s GitHub project as a library.

| Evidence | What it can show | What still requires confirmation |
| --- | --- | --- |
| Bibliographic record with matching identifiers | The described edition has a WorldCat record | Which libraries have selected or hold it |
| Library holding attached to a record | The institution has recorded ownership or licensed access | Current user access, local discovery settings and use |
| Knowledge-base or open collection entry | The resource is represented in that discovery infrastructure | Local selection, activation and a particular library’s access |
| A local reading-list or catalogue entry | A documented local route to the book | Actual reading or teaching use |

OCLC’s [holdings guidance](https://help.oclc.org/Librarian_Toolbox/WorldCat_Holdings) explains that institutions set and maintain their own holdings through their services. Public display also depends on the library’s applicable OCLC arrangements. Agents should supply accurate metadata for a cataloguer’s consideration and never claim holdings on an institution’s behalf. No new WorldCat record, holding or library request was submitted here.

## Open Library: edition-level metadata and identity checks

**Matching book record: not established.** The [earlier same-day observations](../data/search-observations.json) recorded HTTP 404 for both exact ISBN lookups and zero matches for the exact title query at 10:00–10:01 UTC. These checks were carried forward rather than repeated. Two additional author searches at 11:03 UTC returned broad results: `Albert Tan` reported 31, with the first 20 examined, and `Sin Hon` reported 20, all examined. None of the examined records matched this book’s title or ISBNs. The broad queries also returned other people and unrelated co-author combinations. Name similarity alone cannot identify the author.

Open Library’s [contribution guide](https://openlibrary.org/help/faq/editing/getting-started-guide) permits account holders to contribute metadata. Its [book-entry guidance](https://openlibrary.org/tour/books) requires checking existing works, authors and editions before adding a record. The [editing FAQ](https://openlibrary.org/help/faq/editing) distinguishes the general work from each print or electronic edition.

For a future authorised contribution, first refresh the exact title/ISBN checks and inspect any candidate author against the publisher name and ORCID. If the work exists, add only a genuinely missing edition under it. Otherwise use Add a Book with the publisher’s title, subtitle, author, publisher, date and format-specific ISBN. Keep `9789403431925` with the ePDF edition and `9789403431918` with print. Cite the publisher record or imprint in the edit note and inspect the saved history. Do not create records for the companion’s games or software as though they were separate books.

This is a metadata contribution route; it does not require uploading the full book or changing its licence. No account, author, work or edition record was created in this campaign. An eventual record would establish catalogue presence, not borrowing, a library holding or readership.

## OpenAlex: metadata ingestion and evidence-backed corrections

**Book inclusion: unconfirmed.** The [same-day lookup record](../data/search-observations.json) reports HTTP 404 for the exact DOI endpoint at 10:00 UTC and HTTP 429 for a second filter request. The throttled request was not repeated in this round. A bounded web query did not establish a title record. These observations are insufficient to claim complete absence from OpenAlex.

The book already has a Crossref DOI. OpenAlex’s [ingestion guidance](https://help.openalex.org/how-to/getting-indexed/) explains that it harvests Crossref and other scholarly sources. Preserve and correct the existing upstream record; a new DOI or a duplicate publication entry would not solve a metadata problem.

OpenAlex’s [current correction guidance](https://help.openalex.org/how-to/fixing-data-errors/) distinguishes an incorrect author profile from a work missing entirely. Work errors and missing works use its [contact route](https://openalex.org/contact), with the DOI or record ID, precise problem, correct information and verifiable evidence. OpenAlex describes agent-assisted verification of these reports. That is a documented place for a factual correction to be evaluated by agents, without asking them to promote a book in unrelated tasks.

If a later adequate check still cannot locate the book, a single report can supply:

| Item | Evidence to supply |
| --- | --- |
| Identifier | DOI `10.21827/6ac3948159a9e` |
| Observed problem | Exact lookup URL, date and response; acknowledge any rate-limit or search limitations |
| Author and publisher | Albert Tan Sin Hon; University of Groningen Press |
| Author identifier | ORCID `0009-0001-8996-7933` |
| Publication evidence | [Publisher catalogue](https://books.ugp.rug.nl/ugp/catalog/book/300) and existing Crossref record |
| Open-access evidence | [Publisher PDF](https://books.ugp.rug.nl/ugp/catalog/download/300/584/1875), accessible without account or payment; CC BY-NC-ND 4.0 |
| Requested check | Whether the DOI has been ingested or matched elsewhere, and whether a correction is needed |

The separate SSRN essay has a different DOI and must not be presented as this book’s OpenAlex record. No support ticket or author-profile change was submitted here. A future successful lookup establishes a database record; it does not establish readership or citation impact.

## Google Books: coordinate the existing publisher delivery

**Title inclusion: unconfirmed.** The two ISBN API requests in the [same-day observations](../data/search-observations.json) were rate-limited. They were not repeated here and do not establish absence. Ask UGP whether this title has already been delivered through its Partner Center account, and request the Google Books volume link or processing status.

Google’s [current programme policy](https://support.google.com/books/partner/answer/18625?hl=en) requires submitters to hold the necessary rights. The [Partner Center](https://support.google.com/books/partner/answer/3244021?hl=en) lets authorised authors and publishers manage book metadata and files. Being the author does not itself give access to a publisher’s account or its existing record. Confirm the applicable publishing agreement and coordinate delivery before creating a second submission; Google’s [content policy](https://support.google.com/books/partner/answer/1067634?hl=en) warns that duplicate deliveries may be rejected.

The [single-book workflow](https://support.google.com/books/partner/answer/3289675?hl=en) is Book Catalog → Add book, followed by bibliographic details, content and cover upload, then review and publication. Use the ePDF ISBN for the digital edition, the exact published title and author identity, and the publisher’s PDF. The existing licence remains CC BY-NC-ND 4.0. No new account, contractual acceptance or upload was performed in this campaign.

Google’s [Preview Program introduction](https://support.google.com/books/partner/answer/3324395?hl=en) describes a discovery route that does not require selling the ebook. If UGP chooses full reading access there, its [free-book guidance](https://support.google.com/books/partner/answer/6009574?hl=en) distinguishes a zero Play price from the separate preview percentage. A 100% Google Books preview and download availability need their own settings. Free Play distribution can also require account/payment-profile configuration, even where bank details are not required for an entirely free catalogue. These settings should reflect the author’s open-access objective and the rights confirmed for the account.

Verify a published volume page and the actual reading/download experience before reporting Google Books availability. A Partner Center entry, upload receipt or zero price alone does not establish public full-text access.

## Google Scholar: use the scholarly book route

**Title inclusion: unconfirmed by this review.** Google Scholar’s [coverage help](https://scholar.google.com/intl/en/scholar/help.html) includes academic books and recommends checking specific titles, rather than treating a site-wide count as a coverage audit. Its scope and ranking differ from ordinary Google Search.

A concrete technical point affects this edition: the pinned publisher PDF is **8,684,011 bytes**. Scholar’s [inclusion guidance](https://scholar.google.com/intl/en/scholar/inclusion.html) directs documents above 5 MB, including books, to Google Book Search and says that scholarly works there are included in Scholar. This makes coordinated publisher delivery to Google Books a relevant next step. It is not a finding that this book is absent from Scholar, nor a reason to alter or split the published edition for appearance’s sake.

For the publisher or institutional repository, the same guidance calls for searchable PDF or HTML, accessible abstract/full text, simple crawlable links, accurate title/author/date metadata, and reliable access for crawlers. Document metadata should describe the actual work on that page. The publisher HTML already exposes `citation_title`, `citation_author`, `citation_publication_date`, ISBN and PDF-link fields, as observed in round 1; this is evidence of useful metadata, not a complete Scholar compatibility test. Publisher staff can review whether their platform and Google Books feed meet the applicable requirements.

The companion remains a teaching website about the book, with a `WebPage` describing the `Book`. Its lessons and games should retain their own educational identity. Adding the book’s publication metadata to every companion page would obscure that distinction.

An appropriate later check is the exact book title in quotation marks, followed by author/DOI verification of any result and its linked source. Exclude the separate SSRN essay and mere citations in other documents. Scholar’s [search help](https://scholar.google.com/intl/en/scholar/help.html) disallows bulk result access; this campaign made no bulk Scholar queries or artificial citation activity. Record an actual matching search result before claiming inclusion, and keep that finding separate from citation counts or human use.

## Groningen Pure: register or claim the existing book record

**Author profile: confirmed accessible in this round. Book record: unconfirmed.** The [public profile](https://research.rug.nl/en/persons/tan-sin-hon-albert-tan/) displays the matching ORCID and a Visiting Professor position at Prince of Songkla University. Its retrieved research-output list shows five articles and does not show this book. A record may still be unlinked, pending validation or otherwise outside that displayed list, so check Pure before adding anything.

Groningen’s [research-output instructions](https://www.rug.nl/library/education-and-research/support/pure/using-pure/add-content-to-pure/how-to-add-research-output/?lang=en) permit claiming an existing output, importing from a source or file, or creating a record from a template. Its [book guide](https://www.rug.nl/library/education-and-research/support/pure/using-pure/add-content-to-pure/submission-guide-3.0/book?lang=en) identifies **Research output → Book/report → Book**. Academic classification requires an explicit peer-review choice, which should follow the publisher’s evidence.

Through the author’s authorised institutional account, remove the “My content” restriction when searching for the exact DOI, ISBNs and title. If the record already exists, request the authorship link through the claim workflow. If it is absent, use the book template or import the [prepared RIS](../metadata/book.ris) or [BibTeX](../metadata/book.bib), then verify all fields against the publisher. Confirm actual publication-time affiliations instead of accepting any automatic current-affiliation default. This book is a separate research output; the doctoral-thesis route is inappropriate.

The library’s [workflow and visibility guidance](https://www.rug.nl/library/education-and-research/support/pure/using-pure/add-content-to-pure/workflow-and-visibility) distinguishes entry, validation and publication on the Research Portal. Library staff validate bibliographic data and possible full text; public visibility also matters. A saved record or immediate appearance on a personal staff page is not proof of public Research Portal delivery. Preserve the actual licence and publisher version when requesting full-text validation.

This campaign inspected public information only. It did not sign in, claim a record or upload content. Completion would require the DOI-matched public output URL and a check of any displayed full-text link after validation.

## OER Commons and MERLOT: submit the teaching resource accurately

**Submission status: prepared only.** The original companion teaching materials carry CC BY 4.0; the book carries CC BY-NC-ND 4.0, and companion code carries MIT. These permissions must remain separate in any directory record.

OER Commons’ [introduction](https://help.oercommons.org/support/solutions/articles/42000046846-introduction-to-oer) explicitly excludes NoDerivatives licences from its definition of open educational resources, although its broader [usage-rights guide](https://help.oercommons.org/support/solutions/articles/42000046845-usage-rights) also explains “share only” materials. Accordingly, offer the original CC BY seminar as an adaptable teaching resource and identify the linked book’s different licence. Do not describe the book itself as freely remixable.

The [OER Commons submission workflow](https://help.oercommons.org/support/solutions/articles/42000046849-submit-oer) uses a signed-in account and **Create → Submit from Web**. Enter the resource URL, verify the suggested title, description, provider, licence, subject, type, language and tags, then submit for review. Pending status precedes librarian approval. Its [authorship guidance](https://help.oercommons.org/support/solutions/articles/42000119485-role-of-author-on-oer-commons-resources) requires checking automatically detected authors; the uploader and creator need not be the same person.

MERLOT’s [Add a Material guide](https://info.merlot.org/merlothelp/Add_a_Material.htm) permits members to submit an online educational resource with its own URL. The workflow is **Add → Add a Material to MERLOT**, then accurate descriptive fields and submission. MERLOT keeps a metadata record linking to the resource. Select the closest offered discipline and material type, identify postgraduate learners, state English, record free access and the actual licence, and provide the source-code link where relevant. A listing is not a claim of a favourable MERLOT peer review.

A manageable first candidate is the [first 90-minute seminar](https://www.alberttansinhon.com/ibol/lessons/01.html). A suitable description is: “An original postgraduate law seminar accompanying Albert Tan Sin Hon’s *Insurance-Backed Offshore Liquidity*. Learners distinguish legal rights, movements of value and institutional information through a fictional transaction exercise. Includes learning goals, a timed plan, facilitator commentary and source readings. Teaching content: CC BY 4.0. The linked book: CC BY-NC-ND 4.0.” Retain the page’s AI-assistance and publisher-review disclosures.

Before any submission, search the directory for the resource URL and title to avoid duplicates. Then retain the submitted record link and approval outcome separately. This campaign created no directory account or submission and asserts no acceptance.
