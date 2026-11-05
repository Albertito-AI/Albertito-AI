# Contributions to other projects

This record links work submitted through **Albertito-AI** to repositories
maintained by other people. Each entry identifies the problem, the change and
the verification performed. The pull request is the primary record of review
and acceptance.

**Status checked: 5 November 2026, Asia/Singapore.** All five contributions
below are open and awaiting maintainer review. None has been merged or carries
a confirmed payment. They were prepared, reviewed and tested with AI assistance;
internal agent review is distinct from acceptance by an upstream maintainer.

| Project and submission | Problem addressed | Verification | Observed status |
| --- | --- | --- | --- |
| [pypa/readme_renderer #391](https://github.com/pypa/readme_renderer/pull/391) | Correct links to Markdown headings beginning with `fn-` or `fnref-`. Handle collisions with footnote IDs and URL-encoded fragments while preserving generated footnote references and backreferences. | The regression fixture fails before the fix. Locally, 105 tests pass and 2 are skipped with comrak 0.0.16; all 50 Markdown tests pass with the minimum supported comrak 0.0.13. Ruff, flake8 and mypy pass. Separate AI review also checked misleading marker text in quoted attributes and encoded fragments. | Open; [CI](https://github.com/pypa/readme_renderer/actions/runs/41969828701) and [zizmor](https://github.com/pypa/readme_renderer/actions/runs/41969828560) report `action_required`, awaiting maintainer action; one approving review is required. |
| [tscircuit/jscad-planner #25](https://github.com/tscircuit/jscad-planner/pull/25) | Preserve a convex hull operation with one concave input, including after removing construction references. The original planner returned the unchanged input, giving area 3 instead of 3.5 and volume 6 instead of 7 in the regression fixtures. | Four native JSCAD regressions fail before the fix. Locally, all 41 Bun tests pass with 305 assertions after the fix. TypeScript, changed-file formatting and the CJS/declaration build pass. | Open; hosted type checking and package preview passed. |
| [tscircuit/format-si-unit #27](https://github.com/tscircuit/format-si-unit/pull/27) | Convert prefixed degree values correctly: `250mdeg` should become `0.25` degrees. A missing degree mapping prevented the existing prefix logic from applying. | Three new regression tests fail before the fix; a fourth control passes. After the fix, all 23 Bun tests pass with 106 assertions. TypeScript, changed-file formatting, ESM/declaration build and six built-package checks pass. | Open; upstream `test` check passed. |
| [simonw/datasette #3031](https://github.com/simonw/datasette/pull/3031) | Correct the contributor guide's fixture commands so configuration, metadata and plugins are generated and loaded in the intended positions. | Reproduced the original incorrect output and failing command. Corrected commands work sequentially; generated JSON, all six plugins, homepage metadata and a stored query were checked. Documentation tests: 13 tests and 143 subtests passed. Strict Sphinx build, formatting and Cog checks passed. | Open; six hosted workflows await maintainer approval. |
| [tari-project/bounties #2](https://github.com/tari-project/bounties/pull/2) | Preserve the existing bounty board when a repository issue-list query fails, instead of publishing an incomplete board. | Five command-line tests pass. The original implementation fails three failure-handling cases and passes two controls. The GitGuardian security check passed; it is separate from the local regression suite. | Open; awaiting maintainer review. |

## Revisions and scope

| Submission | Base reviewed | Submitted head |
| --- | --- | --- |
| readme_renderer #391 | `148d75a1672c34253e9a327be9b06ed1bc70bbc2` | `502ad57d3265213d7b32d0c2ac57679601698503` |
| jscad-planner #25 | `d6d30903b1c747faa1a48e9aa4e70ac7bb9b3b37` | `9417982f555ebcf67398e62fea747539fac641c4` |
| format-si-unit #27 | `8e7562eac1ed08430b704100e63c4262d45c0d13` | `e7fe7124824032190aa1b2bbf994a621c5f96318` |
| Datasette #3031 | `d1cc495a966cafaed3e50dad73cd88e790031704` | `ccee292f8e9a2f75546c7c30f4b24ad0d019c415` |
| Tari #2 | `1a0dc2fb7e1c019a56857d3eb418a74af2263e56` | `19eadb49faafa4f718b201048a82af866fc2cbc2` |

The readme_renderer checks used Python 3.12.14. Both tested comrak versions
passed the relevant Markdown suite; the broader supported Python matrix has
not been run locally. The jscad-planner regression suite ran locally with Bun
1.4.4 and native `@jscad/modeling` 2.13.0. Its hosted type checking and package
preview do not establish a hosted regression-test run.

Datasette's example checks used the prepared virtual environment to execute
the documented arguments. They verify command behaviour, rather than a new
installation into a clean machine. The full Datasette application suite was
not run for this documentation-only change.

The Tari change covers failed issue-list queries. Individual pull-request
state lookup failures and atomic filesystem writes remain outside that scope.

## Discuss a bounded piece of work

These submissions provide inspectable examples of bug reproduction, regression
coverage and developer documentation. For a software-maintenance enquiry,
send a non-confidential repository link, the observed problem, intended
behaviour and acceptance criteria through the
[existing contact route](https://www.alberttansinhon.com/#contact).
Scope, permissions, price and delivery terms are agreed separately before
commissioned work begins.

This record will be updated when review, merge or payment evidence changes.
An open pull request demonstrates a submitted proposal and its checks; it does
not establish maintainer endorsement, production deployment or customer delivery.
