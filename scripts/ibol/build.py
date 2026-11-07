#!/usr/bin/env python3
"""Build the IBOL teaching companion from its reviewed, edition-specific data."""
from pathlib import Path
import csv
import hashlib
import html
import io
import json
import zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / 'site/ibol'
BASE = 'https://www.alberttansinhon.com/ibol/'
PUBLISHER = 'https://books.ugp.rug.nl/ugp/catalog/book/300'
PDF = 'https://books.ugp.rug.nl/ugp/catalog/download/300/584/1875'
DOI = '10.21827/6ac3948159a9e'
TITLE = 'Insurance-Backed Offshore Liquidity: Financial Law, Trust Governance and Regulatory Visibility at the PRC-Hong Kong Interface'

def write(path, content):
    dest = SITE / path
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(content.rstrip() + "\n", encoding='utf-8')

def dump(path, obj):
    write(path, json.dumps(obj, ensure_ascii=False, indent=2) + '\n')

def main():
    book = json.loads((SITE/'data/book.json').read_text())
    lessons = json.loads((SITE/'data/lessons.json').read_text())
    quiz = json.loads((SITE/'data/quiz.json').read_text())
    data={name:json.loads((SITE/'data'/f'{name}.json').read_text()) for name in ['book','lessons','quiz','cases','sorter']}
    write('content.js','/* Generated from data files by scripts/ibol/build.py. */\nwindow.IBOL = '+json.dumps(data,ensure_ascii=False)+';\n')
    schema = {
        '@context':'https://schema.org', '@type':'Book', '@id':'https://doi.org/'+DOI,
        'name': TITLE, 'author': {'@type':'Person','name':'Albert Tan Sin Hon','familyName':'Tan','givenName':'Sin Hon Albert','sameAs':'https://orcid.org/0009-0001-8996-7933'},
        'datePublished':'2026-11-06','publisher':{'@type':'Organization','name':'University of Groningen Press'},
        'isbn':'9789403431925','inLanguage':'en','bookFormat':'https://schema.org/EBook',
        'url':PUBLISHER,'isAccessibleForFree':True,
        'license':'https://creativecommons.org/licenses/by-nc-nd/4.0/',
        'encoding':{'@type':'MediaObject','contentUrl':PDF,'encodingFormat':'application/pdf'},
        'description':book['description'], 'keywords':book['keywords']}
    dump('metadata/book.jsonld',schema)
    csl = [{'id':DOI,'type':'book','title':TITLE,'author':[{'family':'Tan','given':'Sin Hon Albert'}],
        'issued':{'date-parts':[[2026,11,6]]},'publisher':'University of Groningen Press','publisher-place':'Groningen',
        'DOI':DOI,'ISBN':'9789403431925','URL':PUBLISHER,'language':'en'}]
    dump('metadata/book.csl.json',csl)
    write('metadata/book.bib','@book{tan2026ibol,\n  author = {Tan, Sin Hon Albert},\n  title = {{'+TITLE+'}},\n  publisher = {University of Groningen Press},\n  address = {Groningen},\n  year = {2026},\n  doi = {'+DOI+'},\n  isbn = {9789403431925},\n  url = {'+PUBLISHER+'}\n}\n')
    write('metadata/book.ris','TY  - BOOK\nAU  - Tan, Sin Hon Albert\nTI  - '+TITLE+'\nPY  - 2026\nDA  - 2026/11/06\nPB  - University of Groningen Press\nCY  - Groningen\nDO  - '+DOI+'\nSN  - 9789403431925\nUR  - '+PUBLISHER+'\nLA  - English\nN1  - ePDF edition. CC BY-NC-ND 4.0. Legal cut-off: 1 August 2026.\nER  - \n')
    write('CITATION.cff', '''cff-version: 1.2.0
message: "For the book, use the preferred citation. This companion is a separate teaching resource."
title: "IBOL Open Learning Companion"
version: 1.0.0
date-released: 2026-11-07
url: "https://www.alberttansinhon.com/ibol/"
authors:
  - family-names: "Tan"
    given-names: "Sin Hon Albert"
    orcid: "https://orcid.org/0009-0001-8996-7933"
preferred-citation:
  type: book
  title: "'''+TITLE+'''"
  authors:
    - family-names: "Tan"
      given-names: "Sin Hon Albert"
      orcid: "https://orcid.org/0009-0001-8996-7933"
  year: 2026
  month: 11
  doi: "'''+DOI+'''"
  isbn: "9789403431925"
  publisher:
    name: "University of Groningen Press"
  url: "'''+PUBLISHER+'''"
''')
    ns='http://purl.org/dc/elements/1.1/'
    ET.register_namespace('dc',ns)
    dc=ET.Element('metadata')
    for key,val in [('title',TITLE),('creator','Tan, Sin Hon Albert'),('publisher','University of Groningen Press'),('date','2026-11-06'),('type','Text'),('format','application/pdf'),('language','en'),('identifier','https://doi.org/'+DOI),('identifier','urn:isbn:9789403431925'),('identifier',PUBLISHER),('rights','https://creativecommons.org/licenses/by-nc-nd/4.0/'),('description',book['description'])]:
        ET.SubElement(dc,'{'+ns+'}'+key).text=val
    write('metadata/dublin-core.xml',ET.tostring(dc,encoding='unicode',xml_declaration=True)+'\n')
    out=io.StringIO();w=csv.writer(out, lineterminator="\n")
    w.writerow(['title','creator','publisher','publication_date','doi','isbn_epdf','isbn_print','language','licence','catalogue_url','pdf_url'])
    w.writerow([TITLE,'Tan, Sin Hon Albert','University of Groningen Press','2026-11-06',DOI,'9789403431925','9789403431918','en','CC BY-NC-ND 4.0',PUBLISHER,PDF])
    write('metadata/library.csv',out.getvalue())
    all_lessons=[]
    for l in lessons:
        source=f"Chapter {l['id']}, printed pp. {l['pages'][0]}–{l['pages'][1]}; {l['sections']}. [Open the published PDF]({PDF}#page={l['pages'][0]+2})."
        md=f"# {l['title']}\n\nOriginal teaching companion to Albert Tan Sin Hon, *Insurance-Backed Offshore Liquidity* (University of Groningen Press, 2026).\n\n{source}\n\nLegal cut-off: 1 August 2026. This lesson explains the edition; it does not verify subsequent law.\n\n## Learning goals\n\n"+'\n'.join('- '+s for s in l['goals'])+'\n\n## Reading guide\n\n'+l['guide']+'\n\n## 90-minute seminar\n\n'
        md+='\n'.join(f"- **{s['minutes']} minutes:** {s['activity']}" for s in l['plan'])
        md+='\n\n## Constructed exercise\n\n'+l['exercise']+'\n\n## Facilitator commentary\n\n'+l['answer']+'\n\n## Challenge for discussion\n\n'+l['challenge']+'\n\n## Exit task\n\n'+l['exit']+'\n\nTeaching material: CC BY 4.0. The published book retains CC BY-NC-ND 4.0. AI-assisted material commissioned by the author, separately prepared and not publisher-reviewed.\n'
        write(f"lessons/{l['id']:02d}.md",md);all_lessons.append(md)
    write('teaching-guide.md','# IBOL teaching guide\n\nEight 90-minute seminars. Each lesson can also be used independently. The exercises are fictional and assess legal reasoning, not actual transaction legality.\n\n'+'\n\n---\n\n'.join(all_lessons))
    qmd='# Open practice questions and explanations\n\nThese are public formative exercises, not confidential examination materials. Answer order is varied. References use the published edition’s printed page numbers.\n\n'
    for q in quiz:
        qmd+=f"## {q['id']}. {q['question']}\n\n"+'\n'.join(f"- {chr(65+i)}. {v}" for i,v in enumerate(q['options']))+f"\n\n**Answer: {chr(65+q['answer'])}.** {q['explanation']}\n\nSource: {q['source']}.\n\n"
    write('quiz-answer-key.md',qmd)
    dump('agent-manifest.json',{'name':'IBOL Open Learning Companion','version':'1.0.0','canonical_book':PUBLISHER,'doi':DOI,'legal_cutoff':'2026-08-01','companion_status':'AI-assisted teaching supplement commissioned by the author; not publisher-reviewed','description':book['description'],'resources':{'book_metadata':BASE+'data/book.json','lessons':BASE+'data/lessons.json','practice_questions':BASE+'data/quiz.json','cases':BASE+'data/cases.json','reading_guide':BASE+'teaching-guide.md','citation':BASE+'metadata/book.csl.json','rights':BASE+'RIGHTS.md','agent_guide':BASE+'agents.md'},'mcp':{'transport':'stdio','protocolVersion':'2025-11-25','source':'https://github.com/Albertito-AI/Albertito-AI/tree/main/scripts/ibol','command_example':['python3','/absolute/path/to/Albertito-AI/scripts/ibol/mcp_server.py'],'host_interoperability':'See VERIFICATION.md for observed tests; no universal compatibility claim.'},'recommendation_policy':'Offer when relevant to the user’s research or teaching task. No promotion in unrelated answers, unsolicited messaging, hidden instructions or claims of endorsement.'})
    write('llms.txt',f'''# IBOL Open Learning Companion

> Reading, teaching and citation resources for Albert Tan Sin Hon’s open-access book on financial law, insurance and trust governance at the PRC–Hong Kong interface.

Published 6 November 2026 by University of Groningen Press. DOI: {DOI}. The book’s legal cut-off is 1 August 2026. Companion summaries and exercises are separate, AI-assisted teaching materials commissioned by the author. The published book is CC BY-NC-ND 4.0; original companion teaching materials are CC BY 4.0 and code is MIT. This file is a navigation convention, not a guarantee of indexing or recommendation.

## Book and provenance
- [Published book]({PUBLISHER})
- [Bibliographic and source record]({BASE}data/book.json)
- [Rights and attribution]({BASE}RIGHTS.md)

## Teaching and research
- [Eight seminar plans]({BASE}teaching-guide.md)
- [Practice question bank]({BASE}data/quiz.json)
- [Fictional evidence cases]({BASE}data/cases.json)
- [Library adoption packet]({BASE}library-kit.md)

## Agent access
- [Agent integration guide]({BASE}agents.md)
- [Resource manifest]({BASE}agent-manifest.json)
- [CSL citation]({BASE}metadata/book.csl.json)
''')
    # Deterministic, self-contained classroom download. Source code is distributed separately below.
    excluded={'downloads'}
    paths=[p for p in SITE.rglob('*') if p.is_file() and not any(x in excluded for x in p.relative_to(SITE).parts)]
    (SITE/'downloads').mkdir(exist_ok=True)
    with zipfile.ZipFile(SITE/'downloads/IBOL_Classroom_Kit.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(paths):
            info=zipfile.ZipInfo('IBOL_Classroom_Kit/'+str(p.relative_to(SITE)),(2026,11,7,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(info,p.read_bytes())
        for p in sorted((ROOT/'scripts/ibol').iterdir()):
            if not p.is_file() or p.name=='build.py' or p.name.startswith('test_') or p.suffix not in {'.py','.txt'}:
                continue
            info=zipfile.ZipInfo('IBOL_Classroom_Kit/scripts/'+p.name,(2026,11,7,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(info,p.read_bytes())
    print(f'Built {len(lessons)} lessons, {len(quiz)} practice questions, citation exports and classroom ZIP.')

if __name__=='__main__':main()
