#!/usr/bin/env python3
"""Explicitly fetch and index the pinned publisher PDF for local search (MIT)."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

import catalog

MAX_BYTES = 16 * 1024 * 1024


def index_pdf(pdf_path: Path, destination: Path, book: dict) -> dict:
    """Validate identity before extraction; publish a complete cache atomically."""
    source = book["source_verification"]
    if pdf_path.stat().st_size > MAX_BYTES:
        raise ValueError("Downloaded PDF exceeds the maximum permitted size")
    digest = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
    if digest != source["pdf_sha256"]:
        raise ValueError("Publisher PDF checksum differs from the pinned edition; no cache was installed")
    converter = shutil.which("pdftotext")
    if converter is None:
        raise RuntimeError("pdftotext is required for full-book extraction. Install Poppler and retry.")
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="ibol-extract-", dir=destination) as temporary:
        text_path = Path(temporary) / "book.txt"
        subprocess.run([converter, "-layout", "-enc", "UTF-8", str(pdf_path), str(text_path)],
                       check=True, capture_output=True, timeout=60)
        text = text_path.read_text(encoding="utf-8")
        pages = text.split("\f")
        if pages and not pages[-1].strip():
            pages.pop()
        if len(pages) != source["pdf_page_count"]:
            raise ValueError("Extracted PDF page count differs from the pinned edition")
        records = []
        for physical, page in enumerate(pages, 1):
            expected = physical - source["printed_page_to_pdf_offset"]
            numbers = re.findall(r"(?m)^\s*(\d{1,3})\s*$", page)
            printed = expected if numbers and int(numbers[-1]) == expected else None
            records.append({"pdf_page": physical, "printed_page": printed, "text": page})
        payload = {
            "source_pdf_url": book["pdf_url"], "source_pdf_sha256": digest,
            "source_doi": book["doi"], "book_licence": book["book_licence"],
            "book_licence_url": book["book_licence_url"], "author": book["author"],
            "title": book["title"] + ": " + book["subtitle"],
            "extraction": "pdftotext -layout -enc UTF-8; mechanical format conversion, no substantive editing",
            "pages_sha256": catalog.pages_digest(records), "pages": records,
        }
        index_path = Path(temporary) / "pages.json"
        index_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        copied_pdf = Path(temporary) / "book.pdf"
        shutil.copyfile(pdf_path, copied_pdf)
        # The index is installed last. Interrupted installs are detected by identity checks.
        os.replace(copied_pdf, destination / "book.pdf")
        os.replace(text_path, destination / "book.txt")
        os.replace(index_path, destination / "pages.json")
    return {"cache": str(destination.resolve()), "pages": len(records), "pdf_sha256": digest,
            "source_locator": book["catalogue_url"], "legal_cutoff": book["legal_cutoff"],
            "book_licence": book["book_licence"], "status": "Pinned publisher PDF verified and indexed locally"}


def fetch(destination: Path) -> dict:
    book = catalog.read_data("book")
    url = book["pdf_url"]
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname != "books.ugp.rug.nl":
        raise ValueError("The configured source must be the HTTPS University of Groningen Press host")
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="ibol-download-") as temporary:
        path = Path(temporary) / "publisher.pdf"
        request = Request(url, headers={"User-Agent": "IBOL-Open-Learning-Companion/1.0 (author-commissioned local retrieval)"})
        with urlopen(request, timeout=20) as response, path.open("wb") as output:
            final = urlsplit(response.geturl())
            if final.scheme != "https" or final.hostname != "books.ugp.rug.nl":
                raise ValueError("Publisher download redirected outside the expected HTTPS host")
            size = 0
            while True:
                chunk = response.read(65536)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_BYTES or time.monotonic() - started > 90:
                    raise ValueError("Publisher download exceeded size or time limit")
                output.write(chunk)
        return index_pdf(path, destination, book)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, help="Local cache directory; otherwise IBOL_CACHE_DIR or ~/.cache/ibol")
    args = parser.parse_args()
    try:
        result = fetch(args.cache.expanduser() if args.cache else catalog.cache_directory())
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        parser.exit(2, "IBOL fetch failed: " + str(error) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
