"""Internal fictional document-intake and adverse-input checks, not legal validation."""
from copy import deepcopy
import hashlib
from io import BytesIO
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from court_integrity.engine import InputError, check_submission, digest
from court_integrity.intake import extract_document, prepare_package, main, _docx, _pdf, CITATION
from court_integrity.report import render_html
from court_integrity.__main__ import write_report

NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
TOKEN = '[2099] SGHC 900001'  # explicitly fictional parser fixture, not a legal authority


def source():
    locations = {'para:12': 'Fictional source passage. No legal rule is expressed.'}
    return {'id': 'fixture-1', 'kind': 'authority', 'title': 'Fictional parser exercise',
            'citation': TOKEN, 'jurisdiction': 'FICTIONAL', 'version': 'fictional-v1',
            'origin': 'Fictional, created for testing; not a real authority', 'completeness': 'complete',
            'locators': locations, 'expected_text_digest': digest(locations)}


def document(text):
    return {'input_name': 'fictional.txt', 'input_file_sha256': hashlib.sha256(text.encode()).hexdigest(),
            'input_bytes': len(text.encode()), 'format': 'txt', 'parser': {'name': 'fixture', 'version': '1'},
            'extraction_status': 'UNVERIFIED_TRANSCRIPTION', 'notes': [],
            'segments': [{'id': 'B0001', 'text': text, 'origin': {'kind': 'test-fixture'}}]}


def docx(body, extra=None):
    stream = BytesIO()
    with zipfile.ZipFile(stream, 'w') as z:
        z.writestr('word/document.xml', f'<w:document xmlns:w="{NS}"><w:body>{body}</w:body></w:document>')
        for name, text in (extra or {}).items():
            z.writestr(name, text)
    return stream.getvalue()


class CitationIntakeTests(unittest.TestCase):
    def test_supported_sg_neutral(self):
        p, manifest = prepare_package(document(f'{TOKEN} at [12].'), [source()])
        self.assertEqual(manifest['candidate_count'], 1)
        self.assertEqual(p['claims'][0]['evidence'][0]['locator'], 'para:12')
        self.assertEqual(check_submission(p)['citation_checks'][0]['text_status'], 'LOCATOR_PRESENT_NO_QUOTATION')

    def test_no_automatic_quote_assignment(self):
        p, m = prepare_package(document(f'"Invented quote" {TOKEN} at [12].'), [source()])
        self.assertEqual(p['claims'][0]['evidence'][0]['quotation'], '')
        self.assertEqual(check_submission(p)['coverage']['quote_matches_in_supplied_passages'], 0)

    def test_unknown_source_never_fabricated(self):
        p, m = prepare_package(document(f'{TOKEN} at [12].'))
        self.assertEqual(m['citation_candidates'][0]['source_match'], 'NOT_SUPPLIED')
        self.assertIn('SOURCE_NOT_SUPPLIED', {f['code'] for f in check_submission(p)['findings']})
        self.assertFalse(check_submission(p)['truth_certification'])

    def test_bad_pinpoint_is_flagged_against_supplied_text(self):
        p, _ = prepare_package(document(f'{TOKEN} at [999].'), [source()])
        self.assertIn('PINPOINT_NOT_FOUND', {f['code'] for f in check_submission(p)['findings']})

    def test_ambiguous_sources_not_silently_chosen(self):
        a, b = source(), source()
        b['id'] = 'fixture-2'
        p, m = prepare_package(document(f'{TOKEN} at [12].'), [a, b])
        self.assertEqual(m['citation_candidates'][0]['source_match'], 'AMBIGUOUS_SUPPLIED_METADATA')
        self.assertEqual(check_submission(p)['citation_checks'][0]['source_status'], 'NOT_SUPPLIED')

    def test_missing_pinpoint(self):
        p, _ = prepare_package(document(f'{TOKEN}.'), [source()])
        self.assertEqual(p['claims'][0]['evidence'][0]['locator'], '')

    def test_ranges_and_lists_not_truncated(self):
        for tail in ('at [12]-[14]', 'at [12]–[14]', 'at [12], [14]', 'at paras 12 and 14', 'at paras 12 to 14'):
            with self.subTest(tail=tail):
                p, m = prepare_package(document(f'{TOKEN} {tail}.'))
                self.assertEqual(p['claims'][0]['evidence'][0]['locator'], '')
                self.assertEqual(m['citation_candidates'][0]['pinpoint_state'], 'RANGE_OR_LIST_REQUIRES_ANNOTATION')

    def test_punctuation_after_single_pinpoint(self):
        p, _ = prepare_package(document(f'{TOKEN} at [12], discussed here.'))
        self.assertEqual(p['claims'][0]['evidence'][0]['locator'], 'para:12')

    def test_selected_other_neutral_patterns(self):
        for code in ('SGHC(I)', 'SGCA(I)', 'SGHCR', 'SGHCF', 'SGCA', 'UKSC', 'UKPC', 'EWCA Civ', 'EWCA Crim', 'EWHC'):
            with self.subTest(code=code):
                self.assertEqual(len(CITATION.findall(f'[2099] {code} 900001')), 1)

    def test_division_suffix_preserved(self):
        _, m = prepare_package(document('[2099] EWHC 900001 (Admin) at [2].'))
        self.assertEqual(m['citation_candidates'][0]['normalised_citation'], '[2099] EWHC 900001 (Admin)')

    def test_no_citations_not_pass(self):
        p, m = prepare_package(document('Unsupported reporter citation and an unverified fact.'))
        r = check_submission(p)
        self.assertEqual(m['candidate_count'], 0)
        self.assertEqual(m['citation_coverage'], 'NOT_EXHAUSTIVE')
        self.assertIn('BLOCK_WITHOUT_ANCHORED_CLAIM', {f['code'] for f in r['findings']})
        self.assertEqual(r['overall_status'], 'HUMAN_REVIEW_REQUIRED')

    def test_source_library_not_mutated(self):
        sources = [source()]
        before = deepcopy(sources)
        prepare_package(document(TOKEN), sources)
        self.assertEqual(before, sources)

    def test_candidate_offsets_round_trip(self):
        d = document(f'Fictional text: {TOKEN} at [12].')
        _, m = prepare_package(d)
        c = m['citation_candidates'][0]
        self.assertEqual(d['segments'][0]['text'][c['start']:c['end']], c['citation_text'])

    def test_intake_manifest_html_escaped(self):
        d = document(TOKEN)
        d['input_name'] = '<script>alert(1)</script>.txt'
        p, m = prepare_package(d)
        r = check_submission(p)
        r['intake'] = m
        html = render_html(r)
        self.assertNotIn('<script>', html)
        self.assertIn('NOT_EXHAUSTIVE', html)

    def test_more_than_100_references_rejected(self):
        with self.assertRaises(InputError):
            prepare_package(document((' ' + TOKEN) * 101))


class DocumentIntakeTests(unittest.TestCase):
    def test_utf8_spans_and_lines(self):
        text = '  First paragraph.\nStill the first.\n\nSecond paragraph.\n'
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'fictional.txt'
            path.write_text(text, encoding='utf-8')
            result = extract_document(path)
            self.assertEqual(len(result['segments']), 2)
            for s in result['segments']:
                self.assertEqual(text[s['origin']['start']:s['origin']['end']], s['text'])
            self.assertEqual(result['segments'][1]['origin']['line_start'], 4)
            self.assertEqual(result['input_file_sha256'], hashlib.sha256(path.read_bytes()).hexdigest())

    def test_empty_text_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'empty.txt'
            path.write_text('  \n\n')
            with self.assertRaises(InputError):
                extract_document(path)

    def test_invalid_utf8_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'bad.txt'
            path.write_bytes(b'\xff\xfe')
            with self.assertRaises(InputError):
                extract_document(path)

    def test_unsupported_extension_rejected(self):
        with self.assertRaises(InputError):
            extract_document(Path('/not-read.xls'))

    def test_docx_text_and_notes(self):
        data = docx('<w:p><w:r><w:t>One</w:t><w:tab/><w:t>Two</w:t></w:r></w:p>',
                    {'word/footnotes.xml': f'<w:footnotes xmlns:w="{NS}"><w:footnote w:id="1"><w:p><w:r><w:t>Note text</w:t></w:r></w:p></w:footnote></w:footnotes>'})
        segments, warnings, _ = _docx(data)
        self.assertEqual(segments[0]['text'], 'One\tTwo')
        self.assertEqual(segments[1]['origin']['part'], 'word/footnotes.xml')
        self.assertTrue(any('pagination' in n for n in warnings))

    def test_docx_table_paragraph_included(self):
        segments, _, _ = _docx(docx('<w:tbl><w:tr><w:tc><w:p><w:r><w:t>Cell text</w:t></w:r></w:p></w:tc></w:tr></w:tbl>'))
        self.assertEqual(segments[0]['text'], 'Cell text')

    def test_docx_tracked_changes_rejected(self):
        for tag in ('ins', 'del', 'moveFrom', 'moveTo'):
            with self.subTest(tag=tag):
                with self.assertRaises(InputError):
                    _docx(docx(f'<w:{tag}><w:p><w:r><w:t>Changed</w:t></w:r></w:p></w:{tag}>'))

    def test_docx_macros_rejected(self):
        with self.assertRaises(InputError):
            _docx(docx('', {'word/vbaProject.bin': b'macro fixture'}))

    def test_docx_dtd_rejected(self):
        stream = BytesIO()
        with zipfile.ZipFile(stream, 'w') as z:
            z.writestr('word/document.xml', '<!DOCTYPE x [<!ENTITY a "bad">]><x>&a;</x>')
        with self.assertRaises(InputError):
            _docx(stream.getvalue())

    def test_docx_external_url_is_not_fetched(self):
        data = docx('<w:p><w:r><w:t>Literal https://example.invalid</w:t></w:r></w:p>')
        with patch('socket.socket', side_effect=AssertionError('network attempted')):
            segments, _, _ = _docx(data)
        self.assertIn('https://example.invalid', segments[0]['text'])

    def test_malformed_docx_rejected(self):
        with self.assertRaises(InputError):
            _docx(b'not a zip')

    def test_docx_wrong_namespace_rejected(self):
        stream = BytesIO()
        with zipfile.ZipFile(stream, 'w') as z:
            z.writestr('word/document.xml', '<document>Wrong namespace</document>')
        with self.assertRaises(InputError):
            _docx(stream.getvalue())

    def test_oversized_file_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'large.txt'
            path.write_bytes(b'A' * (5 * 1024 * 1024 + 1))
            with self.assertRaises(InputError):
                extract_document(path)

    def test_pdf_empty_page_warns(self):
        try:
            from pypdf import PdfWriter
        except ImportError:
            self.skipTest('optional pypdf not installed')
        writer = PdfWriter()
        writer.add_blank_page(width=100, height=100)
        stream = BytesIO()
        writer.write(stream)
        segments, warnings, _ = _pdf(stream.getvalue())
        self.assertEqual(segments, [])
        self.assertTrue(any('page 1' in n and 'unextractable' in n for n in warnings))

    def test_encrypted_pdf_rejected(self):
        try:
            from pypdf import PdfWriter
        except ImportError:
            self.skipTest('optional pypdf not installed')
        writer = PdfWriter()
        writer.add_blank_page(width=100, height=100)
        writer.encrypt('fictional-test-password')
        stream = BytesIO()
        writer.write(stream)
        with self.assertRaises(InputError):
            _pdf(stream.getvalue())

    def test_complete_text_workflow(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            path = root / 'fictional.txt'
            path.write_text(f'FICTIONAL EXERCISE\n\n{TOKEN} at [99].', encoding='utf-8')
            library = root / 'sources.json'
            library.write_text(json.dumps({'schema_version': '0.1', 'sources': [source()]}))
            output = root / 'out'
            with patch('socket.socket', side_effect=AssertionError('network attempted')):
                result = main([str(path), '--sources', str(library), '--output', str(output)])
            self.assertEqual(result, 0)
            self.assertEqual({p.name for p in output.iterdir()}, {'report.json', 'report.html', 'package.json', 'intake.json'})
            r = json.loads((output / 'report.json').read_text())
            self.assertIn('PINPOINT_NOT_FOUND', {f['code'] for f in r['findings']})
            self.assertEqual(r['automatic_filing_decision'], 'NONE')
            self.assertEqual(main([str(path), '--output', str(output)]), 2)

    def test_extra_output_failure_cleans_workspace(self):
        import os
        with tempfile.TemporaryDirectory() as d:
            output = Path(d) / 'out'
            real_open = os.open
            def fail(path, flags, mode):
                if str(path).endswith('intake.json'):
                    raise OSError('injected additional-file failure')
                return real_open(path, flags, mode)
            p, _ = prepare_package(document(TOKEN))
            with patch('court_integrity.__main__.os.open', side_effect=fail):
                with self.assertRaises(OSError):
                    write_report(output, check_submission(p), extra={'package.json': '{}', 'intake.json': '{}'})
            self.assertFalse(output.exists())

    def test_path_traversal_output_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p, _ = prepare_package(document(TOKEN))
            output = Path(d) / 'out'
            with self.assertRaises(InputError):
                write_report(output, check_submission(p), extra={'../outside.json': '{}'})
            self.assertFalse(output.exists())

    def test_invalid_library_returns_error(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / 'in.txt').write_text('text')
            (root / 'sources.json').write_text('[]')
            self.assertEqual(main([str(root / 'in.txt'), '--sources', str(root / 'sources.json'), '--output', str(root / 'out')]), 2)
            self.assertFalse((root / 'out').exists())


if __name__ == '__main__':
    unittest.main()
