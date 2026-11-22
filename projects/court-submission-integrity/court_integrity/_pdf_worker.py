"""Private, resource-limited PDF text worker; this is not an OS security sandbox.

Executed as an absolute script with Python isolated mode. It does not import the
application package, accept paths to source files, or expose an inline fallback.
"""
from __future__ import annotations

from io import BytesIO
import json
import sys

MAX_BYTES = 5 * 1024 * 1024
MAX_PAGES = 200
MAX_BLOCK = 100_000
MAX_TEXT = 2_000_000
MAX_RESULT = 16 * 1024 * 1024
MEMORY_BYTES = 1024 * 1024 * 1024
CPU_SECONDS = 35


class WorkerError(Exception):
    pass


def _apply_limits() -> dict[str, int]:
    """Install and read back hard limits before importing the optional parser."""
    if sys.platform != 'linux':
        raise WorkerError('isolation_unavailable')
    try:
        import resource
        requested = {
            'RLIMIT_AS': MEMORY_BYTES,
            'RLIMIT_CPU': CPU_SECONDS,
            'RLIMIT_FSIZE': MAX_RESULT,
            'RLIMIT_CORE': 0,
        }
        applied = {}
        for name, maximum in requested.items():
            kind = getattr(resource, name)
            soft, hard = resource.getrlimit(kind)
            # Do not widen either pre-existing limit, including a tighter soft cap.
            finite = [value for value in (soft, hard) if value != resource.RLIM_INFINITY]
            limit = min([maximum, *finite])
            resource.setrlimit(kind, (limit, limit))
            if resource.getrlimit(kind) != (limit, limit):
                raise WorkerError('isolation_unavailable')
            applied[name] = limit
        return applied
    except (ImportError, AttributeError, ValueError, OSError) as exc:
        raise WorkerError('isolation_unavailable') from exc


def _extract() -> dict:
    data = sys.stdin.buffer.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise WorkerError('input_limit')
    try:
        import pypdf
    except ImportError as exc:
        raise WorkerError('parser_unavailable') from exc
    try:
        pypdf.overwrite_configuration(jbig2dec_binary=None)
        if pypdf.get_configuration().jbig2dec_binary is not None:
            raise WorkerError('decoder_policy_unavailable')
    except Exception as exc:
        raise WorkerError('decoder_policy_unavailable') from exc
    reader = pypdf.PdfReader(BytesIO(data), strict=True)
    if reader.is_encrypted:
        raise WorkerError('encrypted')
    if len(reader.pages) > MAX_PAGES:
        raise WorkerError('page_limit')
    pages, total = [], 0
    for page in reader.pages:
        text = page.extract_text() or ''
        if not text.strip():
            # The intake contract records a note, not a block, for these pages.
            pages.append('')
            continue
        if len(text) > MAX_BLOCK:
            raise WorkerError('block_limit')
        total += len(text)
        if total > MAX_TEXT:
            raise WorkerError('text_limit')
        pages.append(text)
    return {'pages': pages, 'version': pypdf.__version__}


def main() -> int:
    try:
        _apply_limits()
        result = _extract()
    except WorkerError as exc:
        result = {'error': str(exc)}
    except MemoryError:
        result = {'error': 'memory_limit'}
    except Exception:
        result = {'error': 'parse_failed'}
    try:
        encoded = json.dumps(result, ensure_ascii=True, allow_nan=False,
                             separators=(',', ':')).encode('ascii')
        if len(encoded) > MAX_RESULT:
            return 1
        sys.stdout.buffer.write(encoded)
        sys.stdout.buffer.flush()
    except (MemoryError, OSError):
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
