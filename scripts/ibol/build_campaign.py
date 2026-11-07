"""Render the dated assignment ledger from its public, reviewable JSON record."""
import html
import json
from pathlib import Path

SITE = Path(__file__).resolve().parents[2] / 'site/ibol'


def render():
    path = SITE / 'data/campaign-66.json'
    if not path.exists():
        return
    data = json.loads(path.read_text(encoding='utf-8'))
    items = data['assignments']
    complete = sum(item['status'] == 'completed' for item in items)
    esc = html.escape
    rows = []
    for item in items:
        sources = ''.join('<li><a href="' + esc(source['url'], quote=True) + '">' +
                          esc(source.get('observation', 'Source')) + '</a></li>'
                          for source in item.get('evidence', []))
        files = ''.join('<li><a href="../' + esc(name.removeprefix('site/ibol/'), quote=True) +
                        '">' + esc(name.removeprefix('site/ibol/')) + '</a></li>'
                        for name in item.get('files', []) if name.startswith('site/ibol/'))
        limitations = ' '.join(item.get('limitations', []))
        checks = ' '.join(item.get('checks', []))
        detail = ('<details><summary>Evidence and checks</summary><ul>' + sources + files +
                  '</ul><p>' + esc(checks) + '</p><p>' + esc(limitations) + '</p></details>') if sources or files or checks or limitations else ''
        rows.append('<tr><th scope="row">' + esc(item['task_id']) + '</th><td>' + esc(item['task']) +
                    '</td><td>' + esc(item['status']) + '</td><td>' + esc(item.get('outcome', 'Awaiting assignment.')) + detail + '</td></tr>')
    output = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>IBOL dissemination work record | 66 assignments</title><meta name="description" content="Dated evidence for eleven rounds of six assignments supporting the open-access textbook Insurance-Backed Offshore Liquidity.">
<link rel="canonical" href="https://www.alberttansinhon.com/ibol/discovery/campaign"><link rel="stylesheet" href="../styles.css">
<style>.table-wrap{overflow-x:auto}table{border-collapse:collapse;width:100%;min-width:44rem;font-size:.9rem}th,td{text-align:left;vertical-align:top;border-bottom:1px solid #ccd4d6;padding:.8rem}td:nth-child(2){width:25%}details{margin-top:.7rem}summary{cursor:pointer}td a{overflow-wrap:anywhere}caption{text-align:left;margin-bottom:1rem}@media print{details{display:block}table{min-width:0;font-size:8pt}.table-wrap{overflow:visible}}</style>
</head><body><a class="skip" href="#main">Skip to record</a><header><a class="brand" href="../index.html">IBOL <span>OPEN LEARNING</span></a><nav aria-label="Record navigation"><a href="index.html">Discovery</a><a href="../adoption/index.html">Teaching</a></nav></header><main id="main"><section><p class="eyebrow">DATED WORK RECORD</p><h1>Eleven rounds. Six workers.</h1>
<p class="intro">''' + str(complete) + ''' of 66 distinct assignments completed.</p><p>These are assignments carried out by six AI workers across eleven rounds. They are not 66 simultaneous agents, 66 external placements or evidence of readership. Completed research can document an inaccessible service or an unresolved requirement.</p>
<p>Book: Albert Tan Sin Hon, <em>Insurance-Backed Offshore Liquidity</em> (University of Groningen Press, 2026). <a href="https://books.ugp.rug.nl/ugp/catalog/book/300">Publisher record</a>. Record date: ''' + esc(data['date']) + '''.</p>
<p><a href="../data/campaign-66.json">Download the machine-readable ledger</a> · <a href="../data/reach-receipts-2026-11-07.json">Earlier distribution receipts</a></p></section>
<section><h2>Assignments and evidence</h2><div class="table-wrap" role="region" aria-label="Assignment table, horizontally scrollable" tabindex="0"><table><caption>Research, creation, checks and documented limits</caption><thead><tr><th scope="col">ID</th><th scope="col">Assignment</th><th scope="col">Status</th><th scope="col">Outcome</th></tr></thead><tbody>''' + ''.join(rows) + '''</tbody></table></div></section>
<section><h2>What this record does not measure</h2><p>No search ranking change, library holding, downstream agent installation or classroom adoption is inferred from task completion. External publication and submission receipts must be assessed separately. These checks are AI-assisted and do not constitute independent human peer review.</p></section></main><footer><a href="../index.html">Return to the open learning companion</a></footer></body></html>'''
    (SITE / 'discovery/campaign.html').write_text(output + '\n', encoding='utf-8')


if __name__ == '__main__':
    render()
