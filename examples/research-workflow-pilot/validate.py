"""Read-only checks on the portable pilot evidence and published outputs.

Writes only validation.json and a temporary bibliography round-trip. Does not
fetch documents, install packages, invoke models or contact external services.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

from lxml import html
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent


def main():
    checks=[]

    def check(label,condition):
        if not condition:
            raise AssertionError(label)
        checks.append(label)

    sources=json.loads((ROOT/"sources.json").read_text())
    byid={s["id"]:s for s in sources}
    check("Two distinct verified source records",len(sources)==len(byid)==2)
    check("Source hashes and six-page corpus recorded",all(re.fullmatch(r"[0-9a-f]{64}",s["sha256"]) for s in sources) and sum(s["expected_pages"] for s in sources)==6)
    for source in sources:
        cached=ROOT/"tmp/pdfs"/(source["id"]+".pdf")
        if cached.exists():
            check("Cached PDF matches pinned source hash: "+source["id"],hashlib.sha256(cached.read_bytes()).hexdigest()==source["sha256"])
    gold_bytes=(ROOT/"reference_set.json").read_bytes()
    gold=json.loads(gold_bytes)
    v1_hash=hashlib.sha256(gold_bytes).hexdigest()
    check("Original v1 reference-set SHA-256 unchanged",v1_hash==(ROOT/"reference_set.sha256").read_text().split()[0])
    check("Sixteen unique references with eight table cells",len({r["id"] for r in gold["references"]})==16 and sum(r["kind"]=="table_cell" for r in gold["references"])==8)
    v2_bytes=(ROOT/"reference_set.v2.json").read_bytes()
    v2=json.loads(v2_bytes)
    v2_hash=hashlib.sha256(v2_bytes).hexdigest()
    check("V2 checksum and v1 parent recorded",v2_hash==(ROOT/"reference_set.v2.sha256").read_text().split()[0] and v2["based_on_v1_sha256"]==v1_hash)
    oldrefs={r["id"]:r for r in gold["references"]}
    newrefs={r["id"]:r for r in v2["references"]}
    check("V2 preserves all expected targets and changes only TH06 selector",set(oldrefs)==set(newrefs) and [rid for rid in oldrefs if oldrefs[rid]["selector"]!=newrefs[rid]["selector"]]==["TH06"] and all({k:v for k,v in oldrefs[rid].items() if k!="selector"}=={k:v for k,v in newrefs[rid].items() if k!="selector"} for rid in oldrefs))
    check("V2 date selector is structural and contains no target date or coordinates",newrefs["TH06"]["selector"]=={"role":"issued_date_after_corporate_signature","signature":"Bank of Thailand"} and not re.search(r"\d",json.dumps(newrefs["TH06"]["selector"])))
    metrics=json.loads((ROOT/"results.json").read_text())
    check("Final metrics explicitly use v2 reference hash",metrics["reference_file"]=="reference_set.v2.json" and metrics["reference_set_version"]==2 and metrics["reference_sha256"]==v2_hash)
    for engine,data in metrics["engines"].items():
        check("Metric totals agree with all rows: "+engine,len(data["rows"])==16 and all(data[k]==sum(r[k] for r in data["rows"]) for k in ["content_correct","location_correct","joint_correct"]))
    check("Recorded joint scores are 14, 16, 16",[metrics["engines"][k]["joint_correct"] for k in ["docling-native","pdfplumber","docling-plus-word-grounding"]]==[14,16,16])
    check("All three negative controls rejected",len(metrics["negative_controls"])==3 and all(r["rejected"] and not r["joint_correct"] for r in metrics["negative_controls"]))
    check("Both structural-date controls pass",{r["name"] for r in metrics["structural_date_controls"]}=={"changed_input_date","missing_corporate_signature"} and all(r["passed"] for r in metrics["structural_date_controls"]))
    first=json.loads((ROOT/"results-first-pass.json").read_text())
    check("First-pass results preserved",first["engines"]["docling-native"]["joint_correct"]==13 and first["engines"]["pdfplumber"]["joint_correct"]==15)
    oldfinal=json.loads((ROOT/"results-v1-final.json").read_text())
    check("Pre-review v1 results retain original hash",oldfinal["reference_sha256"]==v1_hash and first["reference_sha256"]==v1_hash)
    csl=json.loads((ROOT/"references.csl.json").read_text())
    check("CSL JSON has two source records",{r["id"] for r in csl}==set(byid))
    for record in csl:
        source=byid[record["id"]]
        check("CSL title, corporate author, date and URL match: "+record["id"],record["title"]==source["title"] and record["author"]==[{"literal":source["author"]}] and record["issued"]["date-parts"]==[source["issued"]] and record["URL"]==source["landing_url"])
    (ROOT/"tmp").mkdir(exist_ok=True)
    completed=subprocess.run(["pandoc","references.bib","--from=bibtex","--to=csljson","--output=tmp/references-roundtrip.json"],cwd=ROOT,capture_output=True,text=True,timeout=30)
    check("Pandoc parses BibTeX",completed.returncode==0)
    roundtrip=json.loads((ROOT/"tmp/references-roundtrip.json").read_text())
    check("BibTeX round-trip retains both identifiers and dates",{r["id"] for r in roundtrip}==set(byid) and all(r["issued"]["date-parts"]==[byid[r["id"]]["issued"]] for r in roundtrip))
    tree=html.fromstring((ROOT/"output/report.html").read_bytes())
    bibids=set(tree.xpath('//*[contains(concat(" ",normalize-space(@class)," ")," csl-entry ")]/@id'))
    check("HTML bibliography resolves both citation identifiers",bibids=={"ref-"+sid for sid in byid})
    check("HTML has no unresolved source markers",all("@"+sid not in tree.text_content() for sid in byid))
    check("HTML report is self-contained, no scripts or external assets",not tree.xpath('//script|//img[@src]|//link[@rel="stylesheet"]'))
    reader=PdfReader(ROOT/"output/pdf/report.pdf")
    text=unicodedata.normalize("NFKC"," ".join((p.extract_text() or "") for p in reader.pages))
    text=" ".join(text.split())
    check("Generated PDF has two readable pages",len(reader.pages)==2 and len(text)>4000)
    check("PDF includes outcome, review correction, attribution and bibliography",all(term in text for term in ["14/16","16/16","Docling","Pandoc 3.1.3","not held-out","References","Bank of Thailand","Ministry of Trade and Industry","Albert Tan Sin Hon","AI-assisted pilot","v2 was not frozen","answer-bearing","Linux"]))
    logs=json.loads((ROOT/"publishing-log.json").read_text())
    check("Both Pandoc publishing commands succeeded without warnings",len(logs["commands"])==2 and all(x["returncode"]==0 and not x["stderr"] for x in logs["commands"]))
    for engine in ["docling-native","pdfplumber"]:
        receipt=json.loads((ROOT/f"receipt-{engine}.json").read_text())
        check("No model calls/downloads/network attempts in extraction: "+engine,receipt["model_api_calls"]==receipt["model_downloads"]==0 and not receipt["network_attempts_blocked"] and not any(receipt["models_present"].values()))
        check("Linux reproduction environment explicit: "+engine,receipt["platform"]=="Linux" and receipt["python"].startswith("3.12") and "Linux" in receipt["supported_reproduction_environment"])
    allowlist=json.loads((ROOT/"public-allowlist.json").read_text())
    for rel in allowlist["repository_files"]+allowlist["local_preview_files"]:
        path=ROOT/rel
        check("Safe public/local output path: "+rel,path.resolve().is_relative_to(ROOT.resolve()) and not rel.startswith("tmp/") and (path.is_file() or rel=="validation.json"))
    check("No third-party PDF in repository allowlist",not any(p.endswith(".pdf") for p in allowlist["repository_files"]))
    result={"status":"passed","validated_utc":datetime.now(timezone.utc).isoformat(),"checks_passed":len(checks),"checks":checks,"caveat":"Validates this saved pilot and publication; independent annotation and unseen-document generalisation were not tested."}
    (ROOT/"validation.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({"status":result["status"],"checks_passed":result["checks_passed"]}))


if __name__ == "__main__":
    main()
