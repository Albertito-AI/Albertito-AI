"""Escaped, self-contained HTML. No scripts, external resources or active URLs."""
from __future__ import annotations
from html import escape
import json
from typing import Any

STYLE = """
:root{font-family:system-ui,-apple-system,Segoe UI,sans-serif;color:#142c40;background:#f2f5f7;line-height:1.55}
*{box-sizing:border-box}body{margin:0}header{background:#142c40;color:#fff;padding:38px max(5vw,20px)}
header small{color:#bad8e3;letter-spacing:.12em;text-transform:uppercase}h1{font-size:clamp(26px,4vw,40px);margin:10px 0}
header p{max-width:850px;color:#dbe5eb}.status{display:inline-block;border:1px solid #bad8e3;padding:6px 12px;border-radius:5px;font-weight:700}
main{max-width:1160px;margin:28px auto;padding:0 20px}section{background:#fff;border:1px solid #dae3e8;border-radius:10px;padding:25px;margin:20px 0}
h2{margin-top:0;font-size:23px}h3{font-size:16px}p{margin:8px 0 14px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:16px}
.metric{border-left:4px solid #387d87;padding:8px 14px;background:#f5f9fa}.metric strong{font-size:28px;display:block}.metric span{font-size:13px}
.notice{border-left:4px solid #bc8228;background:#fff9ee;padding:12px 16px}.muted{color:#536b7a;font-size:14px}
.scroll{overflow:auto}table{border-collapse:collapse;width:100%;font-size:14px}th,td{padding:12px;text-align:left;vertical-align:top;border-bottom:1px solid #dae3e8}th{background:#edf3f6}
code{font-family:ui-monospace,Consolas,monospace;font-size:12px;overflow-wrap:anywhere}details{border:1px solid #dbe5ea;border-radius:6px;padding:12px 15px;margin:12px 0}summary{cursor:pointer;font-weight:600}
.badge{display:inline-block;background:#edf3f6;padding:3px 7px;border-radius:4px;font-size:11px;letter-spacing:.02em;margin-right:8px}.CHECK_FINDING{background:#fbe9e7;color:#842f2f}.REVIEW_CANDIDATE{background:#fff1d7;color:#795413}.UNRESOLVED{background:#e7eff7;color:#204968}
pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f5f8fa;padding:15px;font-size:12px}blockquote{border-left:3px solid #adc3cf;margin:12px 0;padding:8px 16px;white-space:pre-wrap}footer{padding:28px 20px;text-align:center;color:#536b7a;font-size:13px}
@media print{body{background:white}header{background:white;color:#142c40}header p,header small{color:#142c40}section{break-inside:avoid}details{break-inside:avoid}}
"""


def render_html(report: dict[str, Any]) -> str:
    e = lambda value: escape(str(value), quote=True)
    cov = report["coverage"]
    cards = "".join(f'<div class="metric"><strong>{e(value)}</strong><span>{e(label)}</span></div>'
                    for label, value in [("Submission blocks", cov["blocks_total"]),
                                         ("Blocks with anchored annotations", cov["blocks_with_anchored_annotations"]),
                                         ("Supplied references", cov["references_supplied"]),
                                         ("Quotes matched in supplied text", cov["quote_matches_in_supplied_passages"])])
    findings = []
    for f in report["findings"]:
        evidence = "" if not f["evidence"] else f'<pre>{e(json.dumps(f["evidence"], ensure_ascii=False, indent=2))}</pre>'
        findings.append(f'''<details open><summary><span class="badge {e(f['status'])}">{e(f['status'])}</span>
{e(f['code'])} <span class="muted">{e(f['id'])}</span></summary>
<p class="muted">Location: {e(f['location'])}</p><p>{e(f['detail'])}</p>
<p><strong>Next check:</strong> {e(f['next_action'])}</p>{evidence}</details>''')
    intake_section = ""
    if "intake" in report:
        intake = report["intake"]
        notes = "".join(f"<li>{e(note)}</li>" for note in intake["notes"])
        candidate_rows = "".join(
            f"<tr><td>{e(c['block_id'])}<br>{e(c['citation_text'])}</td>"
            f"<td>{e(c['locator'] or 'Not resolved')}<br>{e(c['pinpoint_state'])}</td>"
            f"<td>{e(c['source_match'])}</td></tr>" for c in intake["citation_candidates"])
        origins = "".join(f"<tr><td>{e(o['block_id'])}</td><td><code>{e(json.dumps({k: v for k, v in o.items() if k != 'block_id'}, ensure_ascii=False))}</code></td></tr>" for o in intake["block_origins"])
        intake_section = f'''<section><h2>Document intake and extraction limits</h2>
<p>Input: <strong>{e(intake['input_name'])}</strong> · {e(intake['format'])} · {e(intake['input_bytes'])} bytes</p>
<p class="muted">Parser: {e(intake['parser']['name'])} {e(intake['parser']['version'])}<br>
Original file SHA-256: <code>{e(intake['input_file_sha256'])}</code></p>
<p class="notice">Extraction: {e(intake['extraction_status'])}. Citation recognition: {e(intake['citation_coverage'])}.
A recognised occurrence is not a verified source, legal proposition or complete citation audit.</p>
<details open><summary>What this intake did not establish</summary><ul>{notes}</ul></details>
<h3>Recognised citation candidates ({e(intake['candidate_count'])})</h3>
<div class="scroll"><table><thead><tr><th>Block / citation</th><th>Pinpoint candidate</th><th>Supplied source metadata</th></tr></thead><tbody>{candidate_rows}</tbody></table></div>
<details><summary>Extracted block provenance</summary><div class="scroll"><table><tbody>{origins}</tbody></table></div></details></section>'''
    references = []
    for c in report["citation_checks"]:
        passage = "No source passage available" if c["source_passage"] is None else c["source_passage"]
        references.append(f'''<details open><summary>{e(c['claim_id'])} → {e(c['source_id'])} · {e(c['locator'] or 'No pinpoint')}</summary>
<p><code>{e(c['text_status'])}</code></p><p class="muted">Source: {e(c['source_status'])}; substantive support: {e(c['support_status'])}.</p>
<h3>Submitted quotation</h3><blockquote>{e(c['submitted_quotation'] or 'No quotation supplied')}</blockquote>
<h3>Supplied source passage</h3><blockquote>{e(passage)}</blockquote></details>''')
    sources = "".join(f'''<tr><td>{e(s['id'])}<br>{e(s['title'])}</td><td>{e(s['version'])}<br>{e(s['completeness'])}</td>
<td>{e(s['origin'])}</td><td>{e(s['integrity'])}<br><code>{e(s['text_digest'])}</code></td></tr>''' for s in report["source_records"])
    blocks = "".join(f'<details><summary>{e(b["id"])}</summary><blockquote>{e(b["text"])}</blockquote></details>' for b in report["submission_blocks"])
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'; img-src 'none'">
<title>Court Submission Integrity | {e(report['submission_id'])}</title><style>{STYLE}</style></head>
<body><header><small>Albert Tan · Research prototype · {e(report['engine_version'])}</small>
<h1>Court Submission Integrity</h1><p>{e(report['title'])}</p><span class="status">HUMAN REVIEW REQUIRED</span>
<p>An itemised preflight report, not a truth certificate, judicial decision or filing permission.</p></header>
<main><section><h2>Coverage, not a quality score</h2><div class="grid">{cards}</div>
<p class="notice">Structured-input alpha. Source transcriptions and annotations are supplied, not independently authenticated. Unannotated content, legal support, real-world truth, general coherence and current law remain unassessed.</p>
<p class="muted">Profile: {e(report['profile']['id'])} / {e(report['profile']['version'])} · {e(report['profile']['status'])}<br>
Package digest: <code>{e(report['package_digest'])}</code><br>Independent human review: NOT PERFORMED. Automatic filing decision: NONE.</p></section>
{intake_section}<section><h2>Itemised checks and review questions</h2><p class="muted">CHECK_FINDING means an observed discrepancy in supplied data. REVIEW_CANDIDATE requires contextual assessment. UNRESOLVED means not determined, not false.</p>{''.join(findings)}</section>
<section><h2>Citation and quotation comparison</h2><p class="muted">Whitespace-only matching. A match does not establish that a quotation is complete, representative or supports the proposition.</p>{''.join(references) or '<p>No references were supplied.</p>'}</section>
<section><h2>Source inventory</h2><p class="muted">Origins and versions are supplied metadata. Hashes identify transcriptions; they do not authenticate the original documents.</p>
<div class="scroll"><table><thead><tr><th>Source</th><th>Version / coverage</th><th>Declared origin</th><th>Integrity / text digest</th></tr></thead><tbody>{sources}</tbody></table></div></section>
<section><h2>Original supplied blocks</h2>{blocks}</section></main>
<footer>Offline, deterministic checks. No external API calls or automated court connection. AI-assisted implementation; not independently validated for judicial use.</footer></body></html>'''
