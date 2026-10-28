# Profile change record

## 28 October 2026: Sparks begins useful public-project work

Albert requested that Sparks grow into a useful agent whose abilities develop
over time. This adds a bounded autonomous work loop with persistent public-source
memory, separate from fictional care experience.

- A reviewed catalogue covers RegNav Evidence Ledger, RegNav Source Watch,
  Symbolon, Piepowder and Tallystick.
- The worker verifies public visibility before reading a project, pins source
  observations to exact revisions and checks selected starting/contribution files.
- The first observation establishes a baseline. Later runs can report changed
  README fingerprints and published release records with links to the evidence.
- Unavailable sources remain unavailable, with dated last-known evidence.
- The [workbench](SPARKS_WORKBENCH.md) presents useful navigation, source checks,
  observed changes and the next bounded task. It does not assess a project's
  correctness or infer meaning merely from a changed fingerprint.

The existing companion schedule supplies one normal observation per Singapore
date and retries unavailable sources on later runs. Care submissions do not
launch project scans. All generated writes share the existing queue and normal
push protection. No model service or new paid infrastructure is used.

Implemented procedures and their demonstrated outputs define capability. Age,
care points and activity counts do not establish educational achievement or
increasing general intelligence. Private preparation and assessment records are
outside the public repository. Deployment evidence will be added after the first
live source observation.

## 28 October 2026: Sparks and public care

### Request and behaviour

Albert named the companion **Sparks**, requested care controls for visitors, and
asked him to decline care once he has enough. The new state format retains the
original birth time, values, care history and growth while changing his name.

Four links beneath the header let anyone signed into GitHub submit a prefilled
public care issue. Sparks evaluates his current needs before applying any care:
he declines food when full of ideas, play when content, rest when refreshed, and
study when too tired or already occupied with enough ideas. Refusals grant no
care effect or experience and do not restart the successful-care cooldown.

The existing 15-minute shared cooldown also applies to public requests, with
one accepted public action per account per hour. Fixed responses appear in the
generated [care diary](SPARKS_CARE_LOG.md); recognised issues receive a result
label and are closed after their decision has been saved. The worker does not
interpret issue bodies or publish bot comments.

### Reliability and scope

Public requests use their issue number as a durable receipt. State and receipts
are saved together before acknowledgement, and retries do not repeat care.
All companion writers share one queue. Scheduled runs also inspect pending
requests, with bounded processing, a 24-hour eligibility window, retained
unacknowledged receipts and a fail-closed storage cap.

The companion uses explicit game rules, without a language model. This change
does not modify Albert's scholarly profile text, project rights or other
automation. The [Sparks guide](SPARKS.md) explains public participation, needs,
limits and maintenance.

### Activation and observed results

- [Pull request #9](https://github.com/Albertito-AI/Albertito-AI/pull/9) passed
  [hosted validation](https://github.com/Albertito-AI/Albertito-AI/actions/runs/40648725801)
  and was merged as `54e4224b99e4882a20176041b7dbd60e69bf35e8`.
- All 46 tests passed, together with image/state, receipt/diary and profile
  integrity checks. The first [Sparks companion run](https://github.com/Albertito-AI/Albertito-AI/actions/runs/40648803169)
  completed successfully on the merged code.
- Public request [#10](https://github.com/Albertito-AI/Albertito-AI/issues/10)
  was accepted at **15:15:17 Singapore time** and closed with the
  `sparks: accepted` label. It added exactly one care point and one experience
  point in the [first issue-triggered run](https://github.com/Albertito-AI/Albertito-AI/actions/runs/40648862441).
- Public request [#11](https://github.com/Albertito-AI/Albertito-AI/issues/11)
  was declined at **15:15:46 Singapore time** with the response, “Thanks, I have
  enough ideas for now.” The [second issue-triggered run](https://github.com/Albertito-AI/Albertito-AI/actions/runs/40648919052)
  closed it with `sparks: enough for now`. Total experience and successful care
  remained at one, and the successful-care timestamp remained 15:15:17.
- Both live checks used Albert's account through the public issue route.
  Non-owner participation was verified in automated tests, not by claiming a
  separate live visitor account. The public form and all four live profile
  controls were inspected. No bot comments were posted.

The original birth timestamp, **28 October 2026 at 14:34:57 Singapore time**,
was preserved. GitHub may briefly display a cached image after a saved-state
update; the committed diary records the decisions independently of that cache.

AI assistance: implementation and review were performed with ChatGPT. No
independent human engineering audit is claimed.

## 28 October 2026: Albertito companion activated

### Request and design

Albert requested a Tamagotchi-like living persona in the existing profile header
and explicitly approved activation after reviewing the candidate. The design
retains the navy-and-gold research identity and introduces an original fictional
scholar with glasses, an open book and a constellation.

### Implemented behaviour

- Self-contained SVG motion: breathing, blinking, stars and page shimmer.
- Persistent fictional energy, curiosity, joy, age and care-based growth.
- A Singapore day-and-night routine and four daily scheduled state updates.
- Repository-writer care actions through GitHub Actions, with cooldown and
  workflow-replay protection.
- Reduced-motion support, a still-image variant and a documented state engine.

The character does not measure Albert's actual state or scholarly performance.
Visitors see the saved companion; care controls require repository write access.

### Activation and verification

- [Pull request #8](https://github.com/Albertito-AI/Albertito-AI/pull/8) was merged
  as commit `c213f9cf2e520e244494649d010a2b40a7e1cfa5`.
- The [first automatic companion update](https://github.com/Albertito-AI/Albertito-AI/actions/runs/40646152858)
  succeeded, including tests, image validation and the state-save step.
- Its [bot commit](https://github.com/Albertito-AI/Albertito-AI/commit/c449b9a52ae3e1fa1d207168d8d28ed53d142f5d)
  changed only `data/persona.json`, `assets/research-header.svg` and
  `assets/research-header-static.svg`.
- The saved state advanced to **28 October 2026, 14:49:02 Singapore time**,
  preserving the original birth timestamp and zero care experience.
- All 17 state/rendering tests and profile integrity checks passed in hosted
  validation. The live public profile was inspected with the new header loaded;
  the displayed snapshot time was **14:49 SGT**.

The first verified update was triggered by the merge. The scheduled times are
07:17, 13:17, 19:17 and 22:17 Asia/Singapore; future scheduled executions are
not asserted as already observed. Browser animation and saved-state updates are
separate, and image caching may delay the snapshot a visitor sees.

AI assistance: the design, implementation and code review were performed with
ChatGPT. User approval of activation is recorded; no independent human
engineering audit is claimed.

## 28 October 2026: separate Source Watch Action discovery

### Evidence and reader problem

The public profile linked RegNav but omitted its newly released standalone
GitHub Action. [RegNav Source Watch v0.1.0](https://github.com/Albertito-AI/regnav-source-watch/releases/tag/v0.1.0)
was published on 27 October 2026. The release tag resolves to commit
`5e9d6a897dc96685347114b9c1abce14807f9d16`, with four successful
hosted release checks (Linux, macOS, Windows and packaged Action smoke test).
The Action's manifest contract differs from RegNav's ledger JSON.

### Change and expected benefit

- Added a distinct Action entry with a reproducible installation guide and the
  verified versioned release. No Marketplace listing is asserted.
- Added a synthetic demonstration and manifest contribution route.
- Clarified that the Action's Apache-2.0 licence does not change reserved
  rights for RegNav's `policykit` repository.
- Added the public Action to the portfolio visibility policy and link validator.

Readers can locate and try the released Action without confusing the two
repositories or inferring legal correctness from byte-level change detection.

### Verification and remaining evidence

Checked release tag, commit-matched hosted checks, README, Action metadata and
original project rights. The profile integrity workflow validates local links,
portfolio links, SVG structure and required files. Independent setup, actual
human legal review, external adoption, Marketplace acceptance and paying demand
are unverified. This change does not alter the private institutional repository.


## 26 October 2026: public portfolio and collaboration routes

### Observed problem

The profile featured RegNav alone. Symbolon, Piepowder and Tallystick had become
public, but readers could not discover them or identify a bounded way to help.
Paid-work enquiries and support were buried at the end.

### Change

- Added a four-project table with direct runnable or explanatory entry points.
- Added contribution paths and concrete starter activities.
- Brought scoped paid-work and optional support routes into a dedicated section.
- Preserved selected scholarship, forthcoming books, teaching, music and legacy
  exploration, with their existing status and attribution.
- Added the evidence-based profile maintenance approach.

### Evidence checked

- Current GitHub metadata showed all seven Albertito-AI repositories public.
- Project descriptions were checked against the current repository material.
- The University of Groningen records supported the three selected publication
  entries and the PhD research description:
  - https://research.rug.nl/en/persons/tan-sin-hon-albert-tan/
  - https://research.rug.nl/en/publications/converging-standards-divergent-accountability-sustainability-repo/
  - https://research.rug.nl/en/publications/when-does-a-sustainability-report-count-as-securities-disclosure-/
  - https://research.rug.nl/en/publications/constraint-without-succession-external-legal-review-and-retained-/
- Existing website and PayPal destinations were retained without claiming an
  account change or a received payment.

### Remaining work

Independent use, new enquiries, funded collaborations and collections are outcomes
to observe. They are not established by this profile update. The website could
not be fetched by the research tool during this review, so its current page
availability was not revalidated through that tool.

AI assistance: the update was drafted and checked with ChatGPT. No independent
human review is recorded for this edit.
