"""Download exactly two public official PDFs into an excluded local cache.

The source URLs were followed from the organisations' official landing pages.
No accounts, API keys, cookies, model calls or publishing are used.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / "tmp" / "pdfs"
SOURCES = [
    {
        "id": "sg-mti-advance-gdp-2024",
        "title": "Singapore’s GDP Grew by 4.3 Per Cent in the Fourth Quarter of 2024 and by 4.0 Per Cent in 2024",
        "author": "Ministry of Trade and Industry, Singapore",
        "issued": [2025, 1, 2],
        "landing_url": "https://www.meti.gov.sg/newsroom/singapore-s-gdp-grew-by-4-3-per-cent-in-the-fourth-quarter-of-2024-and-by-4-0-per-cent-in-2024/",
        "pdf_url": "https://isomer-user-content.by.gov.sg/1004/bffa60b1-93e3-478e-8a38-53b1781a279e/AdvEst_4Q24.pdf",
        "expected_pages": 4,
        "source_note": "Historical advance estimate, not the latest/revised 2024 GDP. Landing page migrated to METI; retain the author printed on the original release.",
    },
    {
        "id": "th-bot-mpc-2025-1",
        "title": "Monetary Policy Committee’s Decision 1/2025",
        "author": "Bank of Thailand",
        "issued": [2025, 2, 26],
        "number": "6/2025",
        "landing_url": "https://www.bot.or.th/en/news-and-media/news/news-20250226.html",
        "pdf_url": "https://www.bot.or.th/content/dam/bot/documents/en/our-roles/monetary-policy/mpc-publication/press-statement/PressMPC_2025_1.pdf",
        "expected_pages": 2,
        "source_note": "Historical English press release; the stated rate is a 26 February 2025 decision, not a claim about today's rate.",
    },
]


def main() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    manifest_path=ROOT / "sources.json"
    pinned={r["id"]:r["sha256"] for r in json.loads(manifest_path.read_text())} if manifest_path.exists() else {}
    records = []
    for source in SOURCES:
        request = Request(source["pdf_url"], headers={"User-Agent": "AtlasResearchPilot/1.0"})
        with urlopen(request, timeout=30) as response:
            data = response.read(2_000_001)
            record = dict(source)
            record.update(
                resolved_url=response.url,
                http_status=response.status,
                content_type=response.headers.get("Content-Type"),
                retrieved_utc=datetime.now(timezone.utc).isoformat(),
            )
        if len(data) > 2_000_000 or not data.startswith(b"%PDF-"):
            raise RuntimeError(f"Unexpected size or format for {source['id']}")
        record.update(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
        if source["id"] in pinned and record["sha256"] != pinned[source["id"]]:
            raise RuntimeError(f"Source bytes changed for {source['id']}; review and re-annotate before updating the pinned manifest")
        (CACHE / f"{source['id']}.pdf").write_bytes(data)
        records.append(record)
        print(json.dumps({k: record[k] for k in ["id", "http_status", "bytes", "sha256"]}))
    (ROOT / "sources.json").write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
