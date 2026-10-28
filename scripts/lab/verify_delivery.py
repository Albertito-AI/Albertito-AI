"""Verify that GitHub Pages serves the exact tracked site files."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import time
from urllib.parse import quote, urljoin
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
CANONICAL = "https://albertito-ai.github.io/Albertito-AI/"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=CANONICAL)
    args = parser.parse_args()
    if args.url != CANONICAL:
        raise SystemExit("The delivery check requires the canonical GitHub Pages URL.")
    files = sorted(p for p in (ROOT / "site").rglob("*") if p.is_file()
                   and not any(part.startswith(".") for part in p.relative_to(ROOT / "site").parts))
    if not files or not (ROOT / "site/lab/data/regnav.json").exists():
        raise SystemExit("The complete research lab must exist before publication.")
    for path in files:
        relative = path.relative_to(ROOT / "site").as_posix()
        expected = hashlib.sha256(path.read_bytes()).hexdigest()
        target = "" if relative == "index.html" else relative
        url = urljoin(args.url, quote(target, safe="/")) + "?revision=" + expected[:16]
        for attempt in range(6):
            try:
                request = Request(url, headers={
                    "Cache-Control": "no-cache",
                    "User-Agent": "Sparks-Research-Lab-Delivery-Verification",
                })
                with urlopen(request, timeout=20) as response:
                    if response.status != 200:
                        raise ValueError(f"HTTP {response.status}")
                    actual = hashlib.sha256(response.read()).hexdigest()
                if actual != expected:
                    raise ValueError("Delivered bytes differ from the committed source")
                print(f"PASS: published {relative} SHA256 {expected}", flush=True)
                break
            except Exception as error:
                if attempt == 5:
                    raise SystemExit(f"Failed delivery verification for {relative}: {error}") from error
                print(f"Delivery retry for {relative}: {type(error).__name__}", flush=True)
                time.sleep(5)
    print(f"PUBLIC_RESEARCH_LAB_DELIVERY_VERIFIED: {len(files)} files", flush=True)


if __name__ == "__main__":
    main()
