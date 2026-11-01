# Publication-stage validation | 1 November 2026

Action: `CSI-20261101-PUBLISH-02`. Interactive publication, not a scheduled AFW
service occurrence. All checks are internal AI-assisted engineering checks.
Independent human legal review and independent court/user evaluation have not
been performed.

## Source and scope

The original `0.1.0a1` archive has SHA-256
`06216b5b8c1323b9b44f08b7cfff845fdefde9e2df5a579bf812dfa0d1eb8847`.
Its ZIP CRC check passed before safe extraction. All five runtime Python files,
both test files, example generators, supplied TXT/JSON fixtures, rights and
substantive design documents are copied without changing their implementation.
Publication documentation explains the actual hosting location and the distinction
between source publication and formal release. The original archive, generated
binary demonstrations and historical logs remain preserved separately.

## Checks actually run for this publication

- CPython 3.13.5 on Linux, with the pre-existing optional pypdf 5.9.0 parser.
- `python -m unittest discover -s tests -v`: **87 tests passed, zero skips**.
- The structured adverse, matched and unknown examples generated HTML and JSON.
- TXT document intake with the supplied fictional source library generated the
  report, package and intake manifest and recognised four citation candidates.
- All outputs retained `HUMAN_REVIEW_REQUIRED`, automatic filing decision `NONE`
  and no truth certification.
- Runtime and test file Git blob identifiers are compared with the original
  tested files during publication. A matching identifier checks bytes, not truth.

## Remaining limits

No hosted CI run, multi-version/platform result, fresh independent review or
court-system test is claimed by this publication. No workflow is added, and
publication commits use `[skip ci]` to avoid starting unrelated hosted work.
The tests exercise the declared implementation, not real-world factual accuracy,
source authenticity, semantic legal support, current-law completeness, adversarial
parser security or judicial efficiency. Passing tests are not adoption evidence.

The original attempt at a full visual browser review was blocked by the execution
environment; accessibility, responsive layout and cross-browser validation remain
unverified. The optional PDF parser has not completed a production dependency
security assessment. No real filings should be processed before the separate
security, data-rights, purpose and human-oversight gates are met.

See [PUBLICATION.md](PUBLICATION.md) for the hosting decision and reproducible
checks. The actual remote commit and PR are recorded in GitHub's own history and
the owner's private project record after readback, not predicted in this file.
