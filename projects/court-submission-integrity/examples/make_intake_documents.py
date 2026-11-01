"""Generate original fictional intake demos. python-docx/reportlab are developer-only.

No real source or user document is included. Generation is not part of runtime.
"""
from pathlib import Path
import json
from court_integrity.engine import digest


def build(directory: Path) -> None:
    from docx import Document
    from docx.shared import Inches, Pt
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from xml.sax.saxutils import escape
    text = (directory / 'intake_submission.txt').read_text(encoding='utf-8')
    paras = text.strip().split('\n\n')
    document = Document()
    section = document.sections[0]
    section.top_margin = section.bottom_margin = Inches(0.8)
    document.styles['Normal'].font.name = 'Arial'
    document.styles['Normal'].font.size = Pt(11)
    for i, para in enumerate(paras):
        document.add_paragraph(para, style='Heading 1' if i == 0 else 'Normal')
    document.core_properties.author = 'AI-assisted fictional demonstration for Albert Tan'
    document.core_properties.title = 'Fictional court-submission integrity intake exercise'
    document.save(directory / 'intake_submission.docx')
    styles = getSampleStyleSheet()
    elements = []
    for i, para in enumerate(paras):
        elements.append(Paragraph(escape(para), styles['Heading2' if i == 0 else 'BodyText']))
        elements.append(Spacer(1, 14))
    SimpleDocTemplate(str(directory / 'intake_submission.pdf'), pagesize=A4,
                      title='Fictional court-submission integrity intake exercise',
                      author='AI-assisted fictional demonstration for Albert Tan').build(elements)
    sources = []
    for id_, citation, locators, completeness in [
        ('fictional-sg', '[2099] SGHC 900001', {'para:12': 'This is an invented source passage for software testing. No legal rule is expressed.'}, 'complete'),
        ('fictional-uk', '[2099] UKSC 900002', {'para:4': 'This is an invented partial transcription for range-handling tests.'}, 'partial'),
    ]:
        sources.append({'id': id_, 'kind': 'authority', 'title': 'Fictional parser exercise, not an authority',
                        'citation': citation, 'jurisdiction': 'FICTIONAL', 'version': 'fixture-v1',
                        'origin': 'Original fictional test data, created 1 November 2026',
                        'completeness': completeness, 'locators': locators,
                        'expected_text_digest': digest(locators)})
    (directory / 'intake_sources.json').write_text(json.dumps({'schema_version':'0.1', 'sources':sources}, indent=2) + '\n')


if __name__ == '__main__':
    build(Path(__file__).parent)
