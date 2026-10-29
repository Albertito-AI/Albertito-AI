# Evaluation history and independent review correction

The records below distinguish original observations from corrections made after
seeing their results. All stages use the same two source PDFs. No expected
content targets, physical page numbers or reference rectangles were changed.

## V1: original frozen reference and first pass

`reference_set.json` and `reference_set.sha256` preserve the original reference
bytes and checksum. Targets and selectors were manually defined from rendered
source pages before the first extraction evaluation.

`results-first-pass.json` records 13/16 joint checks for Docling native and 15/16
for pdfplumber. One shared issue was date-line grouping that included contact
text. A general standalone-date grouping rule was then added, and the hybrid
route refined Docling value locations using unique pdfplumber word boxes.

`results-v1-final.json` preserves those pre-review results: 14/16, 16/16 and
16/16 respectively. These are historical development observations, with the
known TH06 content-check limitation below; they are not clean independent
accuracy evidence.

## Independent review finding

The v1 TH06 selector contained the exact date that its content check expected.
Withholding the separate `expected_tokens` field was therefore insufficient:
the selector itself leaked the answer. The prior claim that all locators were
independent of expected values was too broad.

## V2: semantic date selector, changed after outcomes

`reference_set.v2.json` replaces only TH06's selector with:

```json
{
  "role": "issued_date_after_corporate_signature",
  "signature": "Bank of Thailand"
}
```

The generic locator finds an exact corporate-signature line, then requires the
next line to be a standalone date of the form day, month name and year. It
rejects zero or multiple candidates. It does not receive a target date, page,
rectangle or source-specific branch hidden in code. The corporate name is a
structural anchor, not the date answer.

V2 keeps all original expected values, ordered cues, pages and rectangles.
Both reference hashes are recorded. **The v2 selector was revised after the
outcomes and independent review; v2 was not frozen before all observation.**
The final evaluator defaults to v2. `results.json` identifies that file/version
and its checksum explicitly.

The existing wrong-number, wrong-page and wrong-region controls remain. Two
additional controls change the input date to a synthetic date and remove the
corporate signature. The first must return the changed date; the second must
reject the lookup. These are targeted checks of the reviewed risk, not evidence
of unseen-document generalisation.

V2 reruns the three routes and preserves the final report's development-set
qualification. The expected annotations were not independently relabelled by
a human; a separate agent reviewed the methodology and flagged this defect.
