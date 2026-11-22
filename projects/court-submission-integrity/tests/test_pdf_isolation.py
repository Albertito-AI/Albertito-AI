"""Synthetic PDF and real child-process boundary checks; no case files are used."""
from __future__ import annotations

import hashlib
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import zlib

from court_integrity.engine import InputError
from court_integrity import intake

LINUX = sys.platform == 'linux'
HAS_PYPDF = importlib.util.find_spec('pypdf') is not None
WORKER = Path(intake._PDF_WORKER)


def fictional_pdf(pages, *, compressed=False, filter_name=None):
    """Build a small original text-only PDF with accurate byte offsets."""
    objects = [b'<< /Type /Catalog /Pages 2 0 R >>', b'',
               b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>']
    children = []
    for text in pages:
        page_id = len(objects) + 1
        children.append(f'{page_id} 0 R')
        objects.append((f'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 400 400] '
                        f'/Resources << /Font << /F1 3 0 R >> >> /Contents {page_id + 1} 0 R >>').encode())
        escaped = text.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
        content = f'BT /F1 12 Tf 10 350 Td ({escaped}) Tj ET'.encode('cp1252')
        if compressed:
            content = zlib.compress(content)
        filter_entry = b' /Filter /FlateDecode' if compressed else b''
        if filter_name is not None:
            filter_entry = b' /Filter /' + filter_name.encode('ascii')
        objects.append(b'<< /Length ' + str(len(content)).encode() + filter_entry
                       + b' >>\nstream\n' + content + b'\nendstream')
    objects[1] = f'<< /Type /Pages /Count {len(children)} /Kids [{" ".join(children)}] >>'.encode()
    result = bytearray(b'%PDF-1.4\n')
    offsets = [0]
    for number, value in enumerate(objects, 1):
        offsets.append(len(result))
        result.extend(f'{number} 0 obj\n'.encode() + value + b'\nendobj\n')
    xref = len(result)
    result.extend(f'xref\n0 {len(offsets)}\n0000000000 65535 f \n'.encode())
    for offset in offsets[1:]:
        result.extend(f'{offset:010d} 00000 n \n'.encode())
    result.extend((f'trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\n'
                   f'startxref\n{xref}\n%%EOF\n').encode())
    return bytes(result)


class PdfPlatformTests(unittest.TestCase):
    def test_unsupported_platforms_reject_before_launch(self):
        for platform in ('win32', 'darwin', 'freebsd14'):
            with self.subTest(platform=platform), patch.object(intake.sys, 'platform', platform):
                with patch.object(intake.subprocess, 'Popen') as launch:
                    with self.assertRaisesRegex(InputError, 'requires Linux resource isolation'):
                        intake._pdf(b'fictional unsupported input')
                    launch.assert_not_called()

    def test_input_limit_rejects_before_launch(self):
        with patch.object(intake.sys, 'platform', 'linux'):
            with patch.object(intake.subprocess, 'Popen') as launch:
                with self.assertRaisesRegex(InputError, '5 MiB'):
                    intake._pdf(b'x' * (intake.MAX_BYTES + 1))
                launch.assert_not_called()


@unittest.skipUnless(LINUX, 'Linux resource-isolation checks require Linux')
class PdfWorkerBoundaryTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix='court fictional worker ')
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.counter = 0

    def script(self, body):
        self.counter += 1
        path = self.root / f'worker-{self.counter}.py'
        path.write_text(body, encoding='utf-8')
        return patch.object(intake, '_PDF_WORKER', path)

    def worker_import(self):
        return ("import importlib.util, json, os, sys\n"
                f"spec = importlib.util.spec_from_file_location('isolated_worker', {str(WORKER)!r})\n"
                "worker = importlib.util.module_from_spec(spec)\n"
                "spec.loader.exec_module(worker)\n")

    def test_actual_production_limits_are_installed_and_read_back(self):
        import resource
        body = self.worker_import() + (
            "limits = worker._apply_limits()\n"
            "print(json.dumps({'pages': [json.dumps(limits)], 'version': 'fixture'}))\n"
        )
        with self.script(body):
            actual = json.loads(intake._pdf_result(b'')['pages'][0])
        requested = {'RLIMIT_AS': 1024 ** 3, 'RLIMIT_CPU': 35,
                     'RLIMIT_FSIZE': 16 * 1024 ** 2, 'RLIMIT_CORE': 0}
        for name, maximum in requested.items():
            soft, hard = resource.getrlimit(getattr(resource, name))
            expected = min([maximum, *[value for value in (soft, hard) if value != resource.RLIM_INFINITY]])
            self.assertEqual(actual[name], expected)

    def test_tighter_inherited_soft_limit_is_preserved(self):
        body = self.worker_import() + (
            "import resource\n"
            "resource.setrlimit(resource.RLIMIT_FSIZE, (2048, 4096))\n"
            "limits = worker._apply_limits()\n"
            "print(json.dumps({'pages': [json.dumps(limits)], 'version': 'fixture'}))\n"
        )
        with self.script(body):
            limits = json.loads(intake._pdf_result(b'')['pages'][0])
        self.assertEqual(limits['RLIMIT_FSIZE'], 2048)

    def test_limit_setup_failure_prevents_parser_call(self):
        body = self.worker_import() + (
            "import resource\n"
            "def unavailable(*args): raise OSError('synthetic limit failure')\n"
            "def forbidden(): raise AssertionError('parser must not run')\n"
            "resource.setrlimit = unavailable\n"
            "worker._extract = forbidden\n"
            "sys.exit(worker.main())\n"
        )
        with self.script(body):
            with self.assertRaisesRegex(InputError, 'limits could not be installed and verified'):
                intake._pdf(b'not parsed')

    def test_limit_readback_failure_prevents_parser_call(self):
        body = self.worker_import() + (
            "import resource\n"
            "resource.setrlimit = lambda *args: None\n"
            "resource.getrlimit = lambda *args: (resource.RLIM_INFINITY, resource.RLIM_INFINITY)\n"
            "sys.exit(worker.main())\n"
        )
        with self.script(body):
            with self.assertRaisesRegex(InputError, 'limits could not be installed and verified'):
                intake._pdf(b'not parsed')

    def test_real_memory_limit_stops_child_allocation(self):
        body = self.worker_import() + (
            "worker.MEMORY_BYTES = 128 * 1024 * 1024\n"
            "worker._apply_limits()\n"
            "try:\n"
            "    value = bytearray(256 * 1024 * 1024)\n"
            "    outcome = 'allocation incorrectly succeeded'\n"
            "except MemoryError:\n"
            "    outcome = 'memory limit enforced'\n"
            "print(json.dumps({'pages': [outcome], 'version': 'fixture'}))\n"
        )
        with self.script(body):
            result = intake._pdf_result(b'')
        self.assertEqual(result['pages'], ['memory limit enforced'])

    def test_real_cpu_limit_terminates_child_before_wall_deadline(self):
        body = self.worker_import() + (
            "worker.CPU_SECONDS = 1\n"
            "worker._apply_limits()\n"
            "while True: pass\n"
        )
        started = time.monotonic()
        with self.script(body), patch.object(intake, 'PDF_WALL_SECONDS', 5):
            with self.assertRaisesRegex(InputError, 'failed or reached a resource limit'):
                intake._pdf(b'')
        self.assertLess(time.monotonic() - started, 5)

    def test_real_file_limit_bounds_child_output(self):
        body = self.worker_import() + (
            "worker.MAX_RESULT = 4096\n"
            "worker._apply_limits()\n"
            "while True: os.write(1, b'x' * 8192)\n"
        )
        output_path = self.root / 'limited-output'
        with self.script(body), patch.object(intake.tempfile, 'TemporaryFile',
                                             side_effect=lambda: output_path.open('w+b')):
            with self.assertRaisesRegex(InputError, 'failed or reached a resource limit'):
                intake._pdf(b'')
        self.assertEqual(output_path.stat().st_size, 4096)

    def test_wall_deadline_kills_and_reaps_worker(self):
        processes = []
        real_popen = subprocess.Popen

        def launch(*args, **kwargs):
            process = real_popen(*args, **kwargs)
            processes.append(process)
            return process

        with self.script('import time\ntime.sleep(10)\n'):
            with patch.object(intake, 'PDF_WALL_SECONDS', 0.15), patch.object(intake.subprocess, 'Popen', side_effect=launch):
                with self.assertRaisesRegex(InputError, 'time limit; no partial result'):
                    intake._pdf(b'')
        self.assertEqual(len(processes), 1)
        self.assertEqual(processes[0].returncode, -signal.SIGKILL)
        with self.assertRaises(ChildProcessError):
            os.waitpid(processes[0].pid, os.WNOHANG)

    def test_descendant_is_stopped_after_successful_leader_exit(self):
        pid_file = self.root / 'descendant.pid'
        body = ("import json, os, time\nfrom pathlib import Path\n"
                "pid = os.fork()\n"
                "if pid == 0:\n"
                "    time.sleep(10)\n"
                "    os._exit(0)\n"
                f"Path({str(pid_file)!r}).write_text(str(pid))\n"
                "print(json.dumps({'pages': ['complete'], 'version': 'fixture'}))\n")
        pid = None
        try:
            with self.script(body):
                self.assertEqual(intake._pdf_result(b'')['pages'], ['complete'])
            pid = int(pid_file.read_text())
            deadline = time.monotonic() + 1
            while time.monotonic() < deadline:
                try:
                    state = Path(f'/proc/{pid}/stat').read_text().rsplit(') ', 1)[1].split()[0]
                except FileNotFoundError:
                    return
                if state == 'Z':
                    return  # terminated; the orphan's OS parent owns final reaping
                time.sleep(0.01)
            self.fail('Worker descendant remained running after successful extraction')
        finally:
            if pid is None and pid_file.exists():
                pid = int(pid_file.read_text())
            if pid is not None:
                try:
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass

    def test_parent_rejects_oversized_result(self):
        with self.script("import sys\nsys.stdout.write('x' * 1025)\n"):
            with patch.object(intake, 'MAX_PDF_RESULT', 1024):
                with self.assertRaisesRegex(InputError, 'output exceeds the result limit'):
                    intake._pdf(b'')

    def test_invalid_results_are_rejected(self):
        payloads = [b'not JSON', json.dumps({'pages': [1], 'version': 'fixture'}).encode(),
                    json.dumps({'pages': [''] * 201, 'version': 'fixture'}).encode(),
                    json.dumps({'pages': ['x' * 100001], 'version': 'fixture'}).encode(),
                    json.dumps({'pages': ['x' * 100000] * 21, 'version': 'fixture'}).encode(),
                    json.dumps({'pages': [], 'version': 'fixture', 'input_file_sha256': 'forged'}).encode()]
        for payload in payloads:
            with self.subTest(bytes=len(payload)):
                response = self.root / 'response.json'
                response.write_bytes(payload)
                with self.script(f"from pathlib import Path\nimport sys\nsys.stdout.buffer.write(Path({str(response)!r}).read_bytes())\n"):
                    with self.assertRaises(InputError):
                        intake._pdf(b'')

    def test_valid_partial_output_is_rejected_after_nonzero_exit(self):
        with self.script("print('{\"pages\":[\"partial\"],\"version\":\"fixture\"}')\nraise SystemExit(3)\n"):
            with self.assertRaisesRegex(InputError, 'no partial result'):
                intake._pdf(b'')

    def test_child_does_not_inherit_ambient_token(self):
        body = ("import json, os\n"
                "print(json.dumps({'pages': [os.environ.get('COURT_SYNTHETIC_TOKEN', 'absent')], 'version': 'fixture'}))\n")
        with self.script(body), patch.dict(os.environ, {'COURT_SYNTHETIC_TOKEN': 'fictional-canary'}):
            self.assertEqual(intake._pdf_result(b'')['pages'], ['absent'])

    def test_missing_optional_parser_is_explicit(self):
        body = self.worker_import() + (
            "class BlockParser:\n"
            "    def find_spec(self, fullname, *args):\n"
            "        if fullname == 'pypdf': raise ModuleNotFoundError('synthetic absent optional parser')\n"
            "sys.meta_path.insert(0, BlockParser())\n"
            "sys.exit(worker.main())\n"
        )
        with self.script(body):
            with self.assertRaisesRegex(InputError, 'pypdf in this Python interpreter or virtual environment'):
                intake._pdf(fictional_pdf(['fictional']))

    @unittest.skipUnless(HAS_PYPDF, 'optional pypdf not installed in this interpreter')
    def test_configured_jbig2_helper_is_blocked_on_text_stream(self):
        marker = self.root / 'decoder-was-called'
        helper = self.root / 'harmless-decoder'
        helper.write_text(f'#!{sys.executable}\nfrom pathlib import Path\nimport sys\n'
                          f'Path({str(marker)!r}).write_text("synthetic helper executed")\n'
                          'sys.stdout.buffer.write(b"BT /F1 12 Tf 10 350 Td (Fictional decoded text.) Tj ET")\n')
        helper.chmod(0o755)
        data = fictional_pdf(['unused encoded fixture'], filter_name='JBIG2Decode')
        configure = ('import pypdf\n'
                     f'pypdf.overwrite_configuration(jbig2dec_binary={str(helper)!r})\n')
        # Positive control proves this synthetic text stream reaches the helper
        # in pypdf when the application's decoder suppression is not applied.
        control = self.worker_import() + 'worker._apply_limits()\n' + configure + (
            'from io import BytesIO\n'
            'reader = pypdf.PdfReader(BytesIO(sys.stdin.buffer.read()), strict=True)\n'
            "print(json.dumps({'pages': [reader.pages[0].extract_text()], 'version': pypdf.__version__}))\n"
        )
        with self.script(control):
            self.assertEqual(intake._pdf_result(data)['pages'], ['Fictional decoded text.'])
        self.assertTrue(marker.exists())
        marker.unlink()
        with self.script(self.worker_import() + configure + 'sys.exit(worker.main())\n'):
            with self.assertRaisesRegex(InputError, 'PDF extraction failed'):
                intake._pdf_result(data)
        self.assertFalse(marker.exists())

    @unittest.skipUnless(HAS_PYPDF, 'optional pypdf not installed in this interpreter')
    def test_decoder_suppression_failure_prevents_parser_call(self):
        marker = self.root / 'parser-was-called'
        body = self.worker_import() + (
            'import pypdf\nfrom pathlib import Path\n'
            "pypdf.overwrite_configuration(jbig2dec_binary='/synthetic/not-executed')\n"
            'pypdf.overwrite_configuration = lambda **kwargs: pypdf.get_configuration()\n'
            f'def forbidden(*args, **kwargs): Path({str(marker)!r}).write_text("unexpected parser call")\n'
            'pypdf.PdfReader = forbidden\n'
            'sys.exit(worker.main())\n'
        )
        with self.script(body):
            with self.assertRaisesRegex(InputError, 'external-decoder suppression could not be verified'):
                intake._pdf_result(b'not parsed')
        self.assertFalse(marker.exists())


@unittest.skipUnless(LINUX, 'PDF parsing requires the validated Linux worker')
@unittest.skipUnless(HAS_PYPDF, 'optional pypdf not installed in this interpreter')
class SyntheticPdfTests(unittest.TestCase):
    def test_text_metadata_and_original_hash_are_preserved(self):
        data = fictional_pdf(['FICTIONAL café [2099] SGHC 900001 at [12].', '', 'Fictional final page.'])
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'fictional.pdf'
            source.write_bytes(data)
            result = intake.extract_document(source)
            self.assertEqual(source.read_bytes(), data)
        self.assertEqual(set(result), {'input_name', 'input_file_sha256', 'input_bytes',
                                      'format', 'parser', 'extraction_status', 'notes', 'segments'})
        self.assertEqual(result['input_file_sha256'], hashlib.sha256(data).hexdigest())
        self.assertEqual(result['input_bytes'], len(data))
        self.assertEqual(result['parser'], {'name': 'pypdf', 'version': importlib.metadata.version('pypdf')})
        self.assertEqual(result['extraction_status'], 'UNVERIFIED_TRANSCRIPTION')
        self.assertEqual(result['segments'], [
            {'id': 'B0001', 'text': 'FICTIONAL café [2099] SGHC 900001 at [12].',
             'origin': {'kind': 'physical-pdf-page', 'page': 1}},
            {'id': 'B0002', 'text': 'Fictional final page.',
             'origin': {'kind': 'physical-pdf-page', 'page': 3}},
        ])
        self.assertEqual(result['notes'], [
            'PDF extraction is unverified. Physical page numbers are not printed-page or paragraph numbers.',
            'No OCR, image understanding, attachment extraction or layout verification is performed.',
            'Physical PDF page 2 is empty or unextractable; it has not been checked.',
        ])

    def test_compressed_oversized_text_block_is_rejected(self):
        data = fictional_pdf(['A' * 100001], compressed=True)
        self.assertLess(len(data), 5000)
        with self.assertRaisesRegex(InputError, '100,000 characters'):
            intake._pdf(data)

    def test_more_than_200_pages_is_rejected(self):
        with self.assertRaisesRegex(InputError, '200-page'):
            intake._pdf(fictional_pdf([''] * 201))

    def test_total_text_limit_is_enforced_in_worker(self):
        data = fictional_pdf(['A' * 96000] * 21, compressed=True)
        self.assertLess(len(data), 20000)
        with self.assertRaisesRegex(InputError, '2,000,000 characters'):
            intake._pdf(data)

    def test_whitespace_only_page_retains_empty_page_contract(self):
        segments, notes, _ = intake._pdf(fictional_pdf([' ' * 100001], compressed=True))
        self.assertEqual(segments, [])
        self.assertTrue(any('page 1 is empty or unextractable' in note for note in notes))

    def test_pythonpath_cannot_replace_child_parser(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            marker = root / 'unexpected-import'
            (root / 'pypdf.py').write_text(f"from pathlib import Path\nPath({str(marker)!r}).write_text('wrong module')\nraise RuntimeError('wrong module')\n")
            with patch.dict(os.environ, {'PYTHONPATH': str(root)}):
                segments, _, _ = intake._pdf(fictional_pdf(['Fictional isolated import.']))
            self.assertEqual(segments[0]['text'], 'Fictional isolated import.')
            self.assertFalse(marker.exists())

    def test_malformed_pdf_cli_does_not_create_report(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'fictional-malformed.pdf'
            source.write_bytes(b'%PDF-1.4\nnot a valid document\n%%EOF\n')
            output = Path(directory) / 'report'
            self.assertEqual(intake.main([str(source), '--output', str(output)]), 2)
            self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
