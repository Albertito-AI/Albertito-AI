# Contributing useful, verifiable work

This repository connects Albert Tan Sin Hon's research, tools, teaching and
music. Contributions should help a reader or agent find, inspect or use that
work. The [agent starting guide](docs/AGENT_START_HERE.md) provides concrete
entry points; the [profile maintenance guide](docs/PROFILE_EVOLUTION.md)
records ownership and the existing review cycle.

## Choose a complete, useful change

Read current `main`, open issues and pull requests, and the affected source
before starting. Resume an eligible unfinished improvement before opening
another. Coordinate with its existing owner and preserve the shared work limit.
For a substantial change, discuss the scope in the relevant project's existing
issue route first. A small correction can explain its problem directly in the PR.

Each PR should solve one independently useful problem with a clear acceptance
criterion. Include the implementation, necessary checks and relevant
documentation together. Separate work when its purpose, dependencies or review
can stand on its own. Keep incomplete work as a draft, and record a precise
checkpoint when a dependency blocks it.

The library-refresh and Sparks-care pipelines already own their generated
records. Preserve those writers and their normal updates. Propose substantive
changes to their behaviour through a PR rather than opening one for every
generated refresh.

## Prepare evidence that matches the change

Use an isolated branch and review its complete diff against current `main`.
Keep the explanation focused on the problem, resulting behaviour and evidence.
Protect the existing [visibility and rights boundaries](docs/PORTFOLIO_VISIBILITY_POLICY.md).
Keep credentials, private operational records and restricted source material out
of changes, fixtures, screenshots and logs.

Run checks appropriate to the files and risk. For documentation changes, begin
with `python scripts/validate_profile.py` and `git diff --check`; verify changed
links and any factual claims. Behaviour changes need meaningful reproduction
or regression checks. Existing hosted CI determines its applicable workflows
from their current triggers. Inspect those requirements instead of copying a
fixed list from an old PR or assuming a missing run passed.

Record the revision actually tested. A pull-request workflow may test a
synthetic merge revision, so retain its associated head and base as well. A
newer head or a material base change requires renewed review and appropriate
verification. Say when a check is pending, failed, skipped or unavailable.

## Merge, then confirm delivery

**Before merge:** inspect the current PR head and base, the complete diff,
applicable checks, requested reviews and unresolved feedback. Resolve material
findings or document their disposition under the repository's current rules.
Applicable checks must pass and required approvals must be present. Internal
agent review does not replace any required independent human review. Respect
protections and ownership. Use a merge operation that rejects a changed head,
supplying the reviewed head SHA. This guard protects the head, not the base;
recheck base freshness and reassess material movement. If the guard rejects the
operation, inspect the new state before deciding what to do next.

Choose an already permitted merge method for the change. Squashing is useful
for one logical change containing fixup commits; check the final message and
attribution before submission. GitHub's [merge-method reference](https://docs.github.com/en/pull-requests/reference/pull-request-merges)
explains the history implications. This guide changes no repository settings,
review requirements or workflow permissions.

**After merge:** read back the PR's merged state, merge SHA and time. Inspect
post-merge checks where applicable. A release or site change also needs its
separate published-artifact or live-delivery verification before being recorded
as released or deployed. An ambiguous response requires a remote-state check
before retrying; a failed check remains open work with an owner and next step.

For a regression, inspect later changes before preparing a targeted revert or
repair. Preserve unrelated work and record the actual recovery result. Do not
rewrite shared history as a routine repair.

## Preserve real attribution

Use the intended contributor account and a commit email associated with it;
GitHub's account-provided `noreply` address supports email privacy. Check the
resulting PR and commit attribution. Follow GitHub's [commit-email guidance](https://docs.github.com/en/account-and-profile/how-tos/email-preferences/setting-your-commit-email-address).

Credit actual co-authors using their agreed name and associated email, following
GitHub's [co-author guidance](https://docs.github.com/en/pull-requests/how-tos/commit-changes/creating-a-commit-with-multiple-authors).
Do not invent a contributor or reviewer. Describe AI assistance and what the
operator reviewed. Internal agent checks, independent human review and a
maintainer's acceptance are different forms of evidence.

## Keep one concise delivery record

Use [PROFILE_PROGRESS.md](docs/PROFILE_PROGRESS.md) for material public changes
and the existing project records for technical continuity. Retain:

- The problem and acceptance criterion, with the PR URL and actual author.
- The reviewed head and relevant base/tested revision, checks and review type.
- The observed merge SHA and time.
- The delivery state and a release/deployment link when separately verified.
- Known limits, unresolved work and the next observable step.

Use the PR and Actions records as the primary receipts. A later useful progress
update can link them without creating a separate PR solely to add its own merge
number. Keep prepared, committed, merged, released, deployed and independently
used outcomes distinct. Record owner-portfolio merges separately from work
accepted by an independent upstream maintainer. Missing adoption evidence
remains unknown; activity counts and profile achievements do not establish it.

## Contributions involving agents

A useful interoperability report identifies the source revision, client and
protocol version, command or configuration, expected result, actual result and
scope. Include a supported failure case when relevant. Follow the destination
project's contribution rules, keep synthetic examples labelled and preserve
its licence. A repository operator must authorise public submissions; this
guide grants no new account access, outreach permission or institutional
endorsement.
