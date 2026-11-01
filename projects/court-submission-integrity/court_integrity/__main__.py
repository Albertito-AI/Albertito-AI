"""Local CLI; source paths and URLs inside inputs are never opened or fetched."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import sys

from .engine import InputError, MAX_BYTES, check_submission
from .report import render_html


def _pairs(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise InputError(f"Duplicate JSON key: {key!r}")
        value[key] = item
    return value


def _constant(value):
    raise InputError(f"Non-standard JSON constant: {value}")


def load_package(path: Path) -> tuple[dict, str]:
    # Local trusted-operator boundary, not a hostile multiuser filesystem sandbox.
    if path.is_symlink() or not stat.S_ISREG(path.stat().st_mode):
        raise InputError("Input must be a regular local file, not a symlink or device")
    with path.open("rb") as stream:
        data = stream.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise InputError("Input exceeds 5 MiB limit")
    try:
        package = json.loads(data.decode("utf-8"), object_pairs_hook=_pairs, parse_constant=_constant)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise InputError("Input must be bounded UTF-8 JSON") from exc
    return package, hashlib.sha256(data).hexdigest()


def write_report(output: Path, report: dict, *, extra: dict[str, str] | None = None) -> None:
    """Refuse overwrite; clean only files created by this call on ordinary errors."""
    extra = extra or {}
    if any(name not in {"package.json", "intake.json"} for name in extra):
        raise InputError("Unsupported supplemental output filename")
    output.mkdir(mode=0o700, parents=False, exist_ok=False)
    created = []
    try:
        for name, content in [("report.json", json.dumps(report, ensure_ascii=False, indent=2) + "\n"),
                              ("report.html", render_html(report)), *extra.items()]:
            path = output / name
            # Exclusive creation; never replace an existing file.
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            created.append(path)
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                stream.write(content)
    except BaseException:
        for path in created:
            try:
                path.unlink()
            except OSError:
                pass
        try:
            output.rmdir()
        except OSError:
            pass
        raise


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Offline Court Submission Integrity alpha. Not a filing gate or truth verifier.")
    parser.add_argument("input", type=Path, help="structured JSON package, max 5 MiB")
    parser.add_argument("--output", required=True, type=Path, help="new output folder; parent must already exist")
    args = parser.parse_args(argv)
    try:
        package, raw_digest = load_package(args.input)
        report = check_submission(package)
        report["input_file_sha256"] = raw_digest
        write_report(args.output, report)
    except (InputError, OSError, RecursionError) as exc:
        print(json.dumps({"error": type(exc).__name__, "detail": str(exc),
                          "filing_decision": "NONE"}, ensure_ascii=True), file=sys.stderr)
        return 2
    print(json.dumps({"status": report["overall_status"], "output": str(args.output),
                      "finding_counts": report["finding_counts"], "filing_decision": "NONE"}))
    # 0 means report generation succeeded; never acceptance, legal validity or factuality.
    return 0


if __name__ == "__main__":
    sys.exit(main())
