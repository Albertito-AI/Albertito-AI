"""Local document intake with explicit extraction and citation-coverage limits.

This adapter is not an authority resolver or a semantic reviewer. It never follows
URLs, opens embedded files, runs macros, uses OCR or calls a model. Use fictional
or independently cleared material in a trusted local environment.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
import re
import signal
import stat
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from typing import Any

from .engine import InputError, MAX_BYTES, MAX_ITEMS, check_submission, whitespace
from .__main__ import load_package, write_report

MAX_TEXT = 2_000_000
MAX_PAGES = 200
MAX_XML = 5 * 1024 * 1024
MAX_ZIP_MEMBERS = 1000
PDF_WALL_SECONDS = 45
MAX_PDF_RESULT = 16 * 1024 * 1024
_PDF_WORKER = Path(__file__).with_name('_pdf_worker.py').resolve()
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
# Recognition is deliberately narrow. It is not exhaustive across any jurisdiction.
CITATION = re.compile(
    r'\[(?:19|20)\d{2}\]\s+'
    r'(?:SG(?:HC\(I\)|CA\(I\)|HCR|HCF|HC|CA|DC|MC|FC|SCT)|'
    r'UKSC|UKPC|EWCA\s+(?:Civ|Crim)|EWHC)\s+\d{1,6}'
    r'(?:\s+\((?:Admin|Ch|Comm|Fam|KB|QB|TCC|Pat|IPEC|SCCO)\))?(?!\w)'
)
PINPOINT = re.compile(r'^\s*(?:at\s+)?(?:\[(\d{1,6})\]|paras?\.?\s+(\d{1,6}))', re.I)
RANGE_OR_LIST = re.compile(r'^\s*(?:[-\u2013\u2014]|,|and\s+|to\s+)\s*\[?\d', re.I)


def _read_bytes(path: Path) -> bytes:
    if path.is_symlink() or not stat.S_ISREG(path.stat().st_mode):
        raise InputError('Document must be a regular local file, not a symlink or device')
    with path.open('rb') as stream:
        data = stream.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise InputError('Document exceeds 5 MiB input limit')
    return data


def _add_segment(segments: list, text: str, origin: dict) -> None:
    if not text.strip():
        return
    if len(text) > 100_000:
        raise InputError('One extracted block exceeds 100,000 characters; use a smaller reviewed document')
    if len(segments) >= MAX_ITEMS:
        raise InputError('Document exceeds 1,000 extracted blocks')
    if sum(len(s['text']) for s in segments) + len(text) > MAX_TEXT:
        raise InputError('Extracted text exceeds 2,000,000 characters')
    segments.append({'id': f'B{len(segments) + 1:04d}', 'text': text, 'origin': origin})


def _plain(data: bytes) -> tuple[list, list, dict]:
    try:
        text = data.decode('utf-8-sig')
    except UnicodeError as exc:
        raise InputError('Text input must be UTF-8') from exc
    segments: list[dict] = []
    # Preserve spans and original whitespace within each paragraph. No legal numbering inferred.
    for m in re.finditer(r'\S[\s\S]*?(?=\r?\n[ \t]*\r?\n|\Z)', text):
        _add_segment(segments, m.group(), {'kind': 'decoded-text-offset',
                                         'start': m.start(), 'end': m.end(),
                                         'line_start': text.count('\n', 0, m.start()) + 1})
    return segments, [], {'name': 'Python UTF-8 decoder', 'version': sys.version.split()[0]}


def _docx(data: bytes) -> tuple[list, list, dict]:
    segments: list[dict] = []
    notes = [
        'DOCX layout, displayed numbering, fields, images and pagination are not verified.',
        'Headers, footers, comments, external relationships and embedded objects are not extracted.',
        'Footnotes/endnotes are extracted separately; their association with body citations is not inferred.'
    ]
    try:
        with zipfile.ZipFile(BytesIO(data)) as archive:
            entries = archive.infolist()
            names = [x.filename for x in entries]
            if len(entries) > MAX_ZIP_MEMBERS or len(set(names)) != len(names):
                raise InputError('DOCX archive has too many or duplicate members')
            if sum(x.file_size for x in entries) > 25 * 1024 * 1024:
                raise InputError('DOCX archive exceeds the expanded-size limit')
            if any(x.flag_bits & 1 for x in entries):
                raise InputError('Encrypted DOCX archives are not supported')
            if any('vbaproject' in n.lower() for n in names):
                raise InputError('Macro-bearing documents are not supported')
            if 'word/document.xml' not in names:
                raise InputError('DOCX main document part is missing')
            for part in ('word/document.xml', 'word/footnotes.xml', 'word/endnotes.xml'):
                if part not in names:
                    continue
                if archive.getinfo(part).file_size > MAX_XML:
                    raise InputError('DOCX XML part exceeds 5 MiB')
                with archive.open(part) as stream:
                    raw = stream.read(MAX_XML + 1)
                if len(raw) > MAX_XML:
                    raise InputError('DOCX XML part exceeds 5 MiB')
                # Reject unsupported encodings and DTDs before invoking the XML parser.
                xml = raw.decode('utf-8-sig')
                if '<!DOCTYPE' in xml.upper() or '<!ENTITY' in xml.upper():
                    raise InputError('DTD/entity declarations are not supported')
                root = ET.fromstring(xml)
                expected = W + {'word/document.xml': 'document', 'word/footnotes.xml': 'footnotes',
                                'word/endnotes.xml': 'endnotes'}[part]
                if root.tag != expected:
                    raise InputError('Unsupported WordprocessingML namespace or root')
                if any(el.tag in {W + 'ins', W + 'del', W + 'moveFrom', W + 'moveTo'} for el in root.iter()):
                    raise InputError('Tracked changes require a separately reviewed clean copy; no automatic acceptance')
                for i, paragraph in enumerate(root.iter(W + 'p'), 1):
                    def content(node):
                        chunks = []
                        for el in node:
                            if el.tag == W + 'p':
                                continue  # nested text boxes are visited independently
                            if el.tag == W + 't':
                                chunks.append(el.text or '')
                            elif el.tag == W + 'tab':
                                chunks.append('\t')
                            elif el.tag in {W + 'br', W + 'cr'}:
                                chunks.append('\n')
                            else:
                                chunks.append(content(el))
                        return ''.join(chunks)
                    _add_segment(segments, content(paragraph), {'kind': 'docx-xml-paragraph',
                                                               'part': part, 'paragraph_index': i})
    except InputError:
        raise
    except (zipfile.BadZipFile, UnicodeError, ET.ParseError, RuntimeError, OSError, RecursionError) as exc:
        raise InputError('DOCX could not be safely read under the supported profile') from exc
    return segments, notes, {'name': 'Python bounded ZIP/WordprocessingML reader', 'version': '0.1'}


def _stop_pdf_worker(process: subprocess.Popen) -> None:
    """Stop the worker's private process group and reap the direct child."""
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    except OSError as exc:
        if process.poll() is None:
            process.kill()
        process.wait(timeout=5)
        raise InputError('PDF worker process group could not be terminated') from exc
    try:
        process.wait(timeout=5)
    except (OSError, subprocess.SubprocessError) as exc:
        raise InputError('PDF worker could not be reaped after termination') from exc


def _pdf_result(data: bytes) -> dict:
    """Accept only a bounded result from a worker with mandatory Linux limits."""
    if sys.platform != 'linux':
        raise InputError('PDF intake requires Linux resource isolation; this platform is unsupported. '
                         'Use a separately reviewed TXT or DOCX copy instead')
    if len(data) > MAX_BYTES:
        raise InputError('Document exceeds 5 MiB input limit')
    process = None
    try:
        # A regular temporary file provides an OS-enforced output-size boundary;
        # communicate() never accumulates unbounded child output in the parent.
        with tempfile.TemporaryFile() as output:
            process = subprocess.Popen(
                [sys.executable, '-I', '-B', str(_PDF_WORKER)],
                stdin=subprocess.PIPE, stdout=output, stderr=subprocess.DEVNULL,
                env={'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8'},
                close_fds=True, start_new_session=True,
            )
            try:
                process.communicate(input=data, timeout=PDF_WALL_SECONDS)
            except subprocess.TimeoutExpired as exc:
                raise InputError('PDF extraction exceeded the 45-second time limit; no partial result is accepted') from exc
            finally:
                # Also stop descendants whose leader has already exited. Do this
                # before accepting output that another group member could alter.
                _stop_pdf_worker(process)
            if process.returncode != 0:
                raise InputError('PDF worker failed or reached a resource limit; no partial result is accepted')
            output.seek(0)
            raw = output.read(MAX_PDF_RESULT + 1)
    except InputError:
        raise
    except (OSError, subprocess.SubprocessError) as exc:
        raise InputError('PDF isolation could not complete; no inline parsing is attempted') from exc
    finally:
        if process is not None:
            if process.stdin is not None:
                process.stdin.close()
    if len(raw) > MAX_PDF_RESULT:
        raise InputError('PDF worker output exceeds the result limit')
    try:
        result = json.loads(raw)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise InputError('PDF worker returned an invalid result; no partial result is accepted') from exc
    errors = {
        'isolation_unavailable': 'PDF resource limits could not be installed and verified; no inline parsing is attempted',
        'parser_unavailable': 'PDF intake requires pypdf in this Python interpreter or virtual environment; no automatic installation is attempted',
        'decoder_policy_unavailable': 'PDF external-decoder suppression could not be verified; parsing is refused',
        'input_limit': 'Document exceeds 5 MiB input limit',
        'encrypted': 'Encrypted PDFs are not supported; supply a permitted readable copy',
        'page_limit': 'PDF exceeds 200-page local prototype limit',
        'block_limit': 'One extracted block exceeds 100,000 characters; use a smaller reviewed document',
        'text_limit': 'Extracted text exceeds 2,000,000 characters',
        'memory_limit': 'PDF processing exceeded its memory limit; no partial result is accepted',
        'parse_failed': 'PDF extraction failed; no clean-document conclusion may be drawn',
    }
    if isinstance(result, dict) and set(result) == {'error'} and isinstance(result['error'], str):
        raise InputError(errors.get(result['error'], 'PDF worker returned an unsupported error'))
    if (not isinstance(result, dict) or set(result) != {'pages', 'version'}
            or not isinstance(result['version'], str) or not 1 <= len(result['version']) <= 80
            or not isinstance(result['pages'], list) or len(result['pages']) > MAX_PAGES):
        raise InputError('PDF worker returned an invalid result structure')
    total = 0
    for text in result['pages']:
        if not isinstance(text, str) or len(text) > 100_000:
            raise InputError('PDF worker returned an invalid or oversized page')
        total += len(text)
        if total > MAX_TEXT:
            raise InputError('PDF worker returned too much extracted text')
    return result


def _pdf(data: bytes) -> tuple[list, list, dict]:
    result = _pdf_result(data)
    segments: list[dict] = []
    notes = ['PDF extraction is unverified. Physical page numbers are not printed-page or paragraph numbers.',
             'No OCR, image understanding, attachment extraction or layout verification is performed.']
    for page_number, text in enumerate(result['pages'], 1):
        if not text.strip():
            notes.append(f'Physical PDF page {page_number} is empty or unextractable; it has not been checked.')
            continue
        _add_segment(segments, text, {'kind': 'physical-pdf-page', 'page': page_number})
    return segments, notes, {'name': 'pypdf', 'version': result['version']}


def extract_document(path: Path) -> dict[str, Any]:
    suffix = path.suffix.lower()
    if suffix not in {'.txt', '.md', '.docx', '.pdf'}:
        raise InputError('Supported inputs: UTF-8 .txt/.md, bounded .docx and optional text-bearing .pdf')
    data = _read_bytes(path)
    parser = _plain if suffix in {'.txt', '.md'} else (_docx if suffix == '.docx' else _pdf)
    segments, notes, implementation = parser(data)
    if not segments:
        raise InputError('No reviewable text was extracted; no report of a clean submission is possible')
    return {'input_name': path.name, 'input_file_sha256': hashlib.sha256(data).hexdigest(),
            'input_bytes': len(data), 'format': suffix[1:], 'parser': implementation,
            'extraction_status': 'UNVERIFIED_TRANSCRIPTION', 'notes': notes, 'segments': segments}


def prepare_package(document: dict, sources: list | None = None, *, jurisdiction: str = 'UNSPECIFIED',
                    stage: str = 'written-submission') -> tuple[dict, dict]:
    """Prepare candidate block annotations. No fact/claim/quotation association is inferred."""
    supplied = deepcopy(sources if sources is not None else [])
    package = {
        'schema_version': '0.1',
        'profile': {'id': 'neutral-citation-intake', 'version': '0.1', 'jurisdiction': jurisdiction,
                    'stage': stage, 'status': 'unvalidated'},
        'submission': {'id': 'document-' + document['input_file_sha256'][:16],
                       'title': document['input_name'], 'jurisdiction': jurisdiction, 'stage': stage,
                       'blocks': [{'id': x['id'], 'text': x['text']} for x in document['segments']]},
        'sources': supplied, 'claims': []
    }
    # Validate the supplied source records through the core before accessing their fields.
    from .engine import validate_package
    validate_package(package)
    by_citation: dict[str, list] = {}
    for source in supplied:
        if source['kind'] == 'authority' and source['citation'].strip():
            by_citation.setdefault(whitespace(source['citation']), []).append(source)
    candidates, notes = [], list(document['notes'])
    for segment in document['segments']:
        refs = []
        for match in CITATION.finditer(segment['text']):
            label = whitespace(match.group())
            found = by_citation.get(label, [])
            sid = found[0]['id'] if len(found) == 1 else 'unresolved-citation-' + hashlib.sha256(label.encode()).hexdigest()[:16]
            # Do not accidentally resolve a generated unresolved ID to a user-supplied ID.
            while sid in {s['id'] for s in supplied} and len(found) != 1:
                sid = '_' + sid
            tail = segment['text'][match.end():]
            pm = PINPOINT.match(tail)
            locator = ''
            pinpoint_state = 'NOT_RECOGNISED'
            if pm:
                if RANGE_OR_LIST.match(tail[pm.end():]):
                    pinpoint_state = 'RANGE_OR_LIST_REQUIRES_ANNOTATION'
                else:
                    locator = 'para:' + (pm.group(1) or pm.group(2))
                    pinpoint_state = 'SINGLE_PARAGRAPH_CANDIDATE'
            candidates.append({'block_id': segment['id'], 'citation_text': match.group(),
                               'start': match.start(), 'end': match.end(), 'normalised_citation': label,
                               'source_match': 'UNIQUE_SUPPLIED_METADATA' if len(found) == 1 else
                                               ('AMBIGUOUS_SUPPLIED_METADATA' if found else 'NOT_SUPPLIED'),
                               'locator': locator, 'pinpoint_state': pinpoint_state})
            refs.append({'source_id': sid, 'locator': locator, 'quotation': '', 'cited_as': label})
            if len(refs) > 100:
                raise InputError('More than 100 recognised citations in one block; use reviewed smaller blocks')
        if refs:
            package['claims'].append({'id': 'candidate-' + segment['id'], 'block_id': segment['id'],
                                      'text': segment['text'], 'kind': 'legal_argument', 'evidence': refs})
    notes.extend([
        'Citation recognition supports selected SG, UKSC, UKPC, EWCA and EWHC neutral-citation patterns only; coverage is not exhaustive.',
        'Citation occurrences are candidate block annotations, not separately extracted legal propositions.',
        'Source matching uses supplied citation metadata, not an official-source resolver or external legal search.',
        'Quotations, factual claims, issue coverage, legal support, current treatment and general coherence are not automatically extracted or assessed.',
        'A zero candidate count is not evidence that no citations or citation defects exist.'
    ])
    manifest = {k: deepcopy(v) for k, v in document.items() if k != 'segments'}
    manifest.update({'block_origins': [{'block_id': s['id'], **s['origin']} for s in document['segments']],
                     'notes': notes, 'citation_candidates': candidates,
                     'candidate_count': len(candidates), 'citation_coverage': 'NOT_EXHAUSTIVE'})
    validate_package(package)
    return package, manifest


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description='Local document-intake alpha. Fictional/cleared inputs only; not a court filing gate.')
    parser.add_argument('document', type=Path)
    parser.add_argument('--sources', type=Path, help='optional JSON object containing schema_version and sources; no remote retrieval')
    parser.add_argument('--jurisdiction', default='UNSPECIFIED')
    parser.add_argument('--stage', default='written-submission')
    parser.add_argument('--output', type=Path, required=True, help='new output directory; never overwritten')
    args = parser.parse_args(argv)
    try:
        sources = []
        if args.sources:
            library, _ = load_package(args.sources)
            if not isinstance(library, dict) or set(library) != {'schema_version', 'sources'} or library['schema_version'] != '0.1':
                raise InputError('Source library must contain exactly schema_version="0.1" and sources')
            sources = library['sources']
        document = extract_document(args.document)
        package, intake = prepare_package(document, sources, jurisdiction=args.jurisdiction, stage=args.stage)
        report = check_submission(package)
        report['input_file_sha256'] = document['input_file_sha256']
        report['intake'] = intake
        extra = {'package.json': json.dumps(package, ensure_ascii=False, indent=2) + '\n',
                 'intake.json': json.dumps(intake, ensure_ascii=False, indent=2) + '\n'}
        write_report(args.output, report, extra=extra)
    except (InputError, OSError, RecursionError) as exc:
        print(json.dumps({'error': type(exc).__name__, 'detail': str(exc), 'filing_decision': 'NONE'}, ensure_ascii=True), file=sys.stderr)
        return 2
    print(json.dumps({'status': 'HUMAN_REVIEW_REQUIRED', 'output': str(args.output),
                      'blocks_extracted': len(document['segments']), 'citation_candidates': intake['candidate_count'],
                      'citation_coverage': 'NOT_EXHAUSTIVE', 'filing_decision': 'NONE'}))
    return 0


if __name__ == '__main__':
    sys.exit(main())
