"""Extract local native PDF text with provenance; full text stays in tmp/.

This uses Docling's model-free NativePdfPipeline, not its layout/OCR/table
models. A pdfplumber baseline can be selected explicitly. Extraction has no
access to the evaluation reference values or rectangles.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
import platform
import resource
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", choices=["docling-native", "pdfplumber"], required=True)
    args = parser.parse_args()
    network_attempts: list[str] = []

    def audit(event, event_args):
        if event in {"socket.connect", "socket.getaddrinfo"}:
            network_attempts.append(event)
            raise RuntimeError("Network access is disabled during extraction")

    sys.addaudithook(audit)
    sources = json.loads((ROOT / "sources.json").read_text())
    outdir = ROOT / "tmp" / "extracted" / args.engine
    outdir.mkdir(parents=True, exist_ok=True)
    converter = None
    if args.engine == "docling-native":
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import NativePdfPipelineOptions
        from docling.document_converter import DocumentConverter, NativePdfFormatOption

        options = NativePdfPipelineOptions(
            generate_page_images=False,
            parser_threads=1,
            document_timeout=30,
        )
        converter = DocumentConverter(
            allowed_formats=[InputFormat.PDF],
            format_options={InputFormat.PDF: NativePdfFormatOption(pipeline_options=options)},
        )
    else:
        import pdfplumber

    receipts = []
    for source in sources:
        path = ROOT / "tmp" / "pdfs" / (source["id"] + ".pdf")
        assert hashlib.sha256(path.read_bytes()).hexdigest() == source["sha256"]
        started = time.perf_counter()
        cells = []
        if converter is not None:
            result = converter.convert(path)
            if result.status.value != "success":
                raise RuntimeError(f"Conversion failed: {result.status}")
            doc = result.document
            pages = {str(k): {"width": p.size.width, "height": p.size.height} for k, p in doc.pages.items()}
            for item in doc.texts:
                for prov in item.prov:
                    size = pages[str(prov.page_no)]
                    box = prov.bbox.to_top_left_origin(page_height=size["height"])
                    cells.append({
                        "page": prov.page_no,
                        "text": item.text,
                        "bbox": [box.l/size["width"], box.t/size["height"], box.r/size["width"], box.b/size["height"]],
                    })
            structured_tables = len(doc.tables)
        else:
            pages = {}
            with pdfplumber.open(path) as pdf:
                for pno, page in enumerate(pdf.pages, 1):
                    pages[str(pno)] = {"width": page.width, "height": page.height}
                    for word in page.extract_words():
                        cells.append({"page": pno, "text": word["text"], "bbox": [word["x0"]/page.width,word["top"]/page.height,word["x1"]/page.width,word["bottom"]/page.height]})
            structured_tables = None
        elapsed = time.perf_counter() - started
        assert len(pages) == source["expected_pages"]
        (outdir / (source["id"] + ".json")).write_text(json.dumps({"pages":pages,"cells":cells}, ensure_ascii=False))
        receipts.append({"id":source["id"],"source_sha256":source["sha256"],"pages":len(pages),"text_cells":len(cells),"structured_tables_emitted":structured_tables,"elapsed_seconds":round(elapsed,4)})
        print(json.dumps(receipts[-1]))
    receipt = {
        "engine": args.engine,
        "python": platform.python_version(),
        "platform":platform.system(),
        "supported_reproduction_environment":"Linux with Python 3.12; resource.ru_maxrss is reported in KiB on Linux",
        "versions": {name: version(name) for name in ["docling-slim","docling-core","docling-parse","pdfplumber"]},
        "documents":receipts,
        "model_api_calls":0,
        "model_downloads":0,
        "network_attempts_blocked":network_attempts,
        "process_peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "models_present":{name:bool(importlib.util.find_spec(name)) for name in ["torch","transformers","onnxruntime","rapidocr"]},
        "limitations":"Native text only. Docling native emits text cells with boxes, not inferred reading order, headings or tables. Extraction does not OCR scanned pages. Timing excludes imports/converter construction and is a single local run, not a performance benchmark.",
    }
    (ROOT / f"receipt-{args.engine}.json").write_text(json.dumps(receipt,indent=2)+"\n")


if __name__ == "__main__":
    main()
