# GitHub source publication | 1 November 2026

Action: `CSI-20261101-PUBLISH-02`. Owner: Albert Tan Sin Hon.
Version: `0.1.0a1`. Direct owner-requested publication; not scheduled-run credit.

## Hosting decision

The owner repeatedly instructed that this existing standalone program be published
on GitHub. The available connected GitHub tools can write files, branches, commits
and pull requests but do not expose repository creation. A standard local GitHub
session is not configured, and direct network name resolution was unavailable.

To deliver a public, inspectable program without asking for another permission or
subscription, the implementation is published as a self-contained project folder
in the existing public `Albertito-AI/Albertito-AI` research hub:
`projects/court-submission-integrity`.

This is **not** a newly created repository. The intended dedicated slug
`Albertito-AI/court-submission-integrity` remains uncreated by this work. The source
folder can be moved intact to a dedicated repository later without changing the
program's package imports. No RegNav files, main-profile README, generated library
records, scheduled tasks, existing licences or court systems are modified.

## Publication procedure and evidence

Initial checked base: `f9e7280f5da672b754f5e3fac3d89a95794de2d5`.
Branch: `publish/court-submission-integrity-20261101`.
The source is copied from the preserved original archive, reviewed, locally tested
and uploaded through the owner's connected account. AI assistance is disclosed;
this is not an independent maintainer or human legal review. The live commit and
PR history supply exact attribution and merge state. No result is inferred from
configuration alone. No tagged release, service deployment or independent use is
claimed.

## Included and archived artifacts

The GitHub folder contains the complete Python implementation, both regression
suites, build metadata, fictional TXT/JSON inputs, example generators, original
rights/authorship statements and product/input/integration/threat/roadmap notes.
Generated HTML/JSON reports, prebuilt DOCX/PDF samples and original machine-specific
validation logs are retained in the owner's separately saved original archive.
The core and TXT workflow need none of those omitted generated artifacts; reports
are reproduced locally. The optional binary-demo generator requires already
installed developer-only packages and never installs them automatically.

Original archive SHA-256:
`06216b5b8c1323b9b44f08b7cfff845fdefde9e2df5a579bf812dfa0d1eb8847`.
The original local Git object database was not included in that archive, so this
publication does not claim to preserve its local commit identity or Git history.

## Reproduce from this folder

```sh
python -m unittest discover -s tests -v
python -m court_integrity examples/adverse.json --output check-adverse
python -m court_integrity examples/matched.json --output check-matched
python -m court_integrity examples/unknown.json --output check-unknown
python -m court_integrity.intake examples/intake_submission.txt --sources examples/intake_sources.json --jurisdiction FICTIONAL --output check-intake
```

Use fresh output directory names. Source/tests use no external model or source API.
The two optional PDF tests skip when pypdf is absent. Full visual browser review,
independent human evaluation and production approval remain outstanding.

## Next bounded action

Implement and independently evaluate a permitted, version-pinned authoritative
source resolver before adding any truth or general semantic-review claim. A later
dedicated-repository migration must preserve rights, test evidence and provenance.
No court outreach, payments, new scheduler or operational integration is authorised
or performed merely by this publication.
