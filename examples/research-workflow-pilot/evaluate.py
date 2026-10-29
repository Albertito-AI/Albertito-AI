"""Evaluate semantic locators against a visually annotated reference set.

V2 locators receive semantic/structural selectors, not expected target fields.
The original v1 date selector was answer-bearing; history records its correction.
They operate on full-document text cells from either extraction engine.
"""
from __future__ import annotations

import copy
import argparse
import hashlib
import json
import re
import statistics
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def norm(text):
    return " ".join(unicodedata.normalize("NFKC", text).split())


def union(items):
    return [min(x["bbox"][0] for x in items), min(x["bbox"][1] for x in items), max(x["bbox"][2] for x in items), max(x["bbox"][3] for x in items)]


def cy(item):
    return (item["bbox"][1]+item["bbox"][3])/2


def make_lines(document):
    pages = {}
    for pno in document["pages"]:
        cells = [c for c in document["cells"] if c["page"] == int(pno) and c["bbox"][0] >= .07 and c["bbox"][2] <= .92 and c["bbox"][3]-c["bbox"][1] < .06]
        lines = []
        for cell in sorted(cells, key=lambda c:(cy(c),c["bbox"][0])):
            if lines and abs(cy(cell)-cy(lines[-1])) < .005:
                lines[-1]["items"].append(cell)
                lines[-1]["bbox"] = union(lines[-1]["items"])
            else:
                lines.append({"page":int(pno),"bbox":cell["bbox"],"items":[cell]})
        for line in lines:
            line["items"].sort(key=lambda c:c["bbox"][0])
            line["text"] = norm(" ".join(c["text"] for c in line["items"]))
        pages[int(pno)] = lines
    return pages


def locate_paragraph(document, selector):
    if selector.get("role") == "issued_date_after_corporate_signature":
        candidates=[]
        signature=norm(selector["signature"]).casefold()
        for pno,lines in make_lines(document).items():
            for index,line in enumerate(lines[:-1]):
                if line["text"].casefold() != signature:
                    continue
                following=lines[index+1]
                if re.fullmatch(r"\d{1,2} [A-Za-z]+ \d{4}",following["text"]):
                    candidates.append({"page":pno,"bbox":following["bbox"],"text":following["text"]})
        if len(candidates)!=1:
            raise ValueError(f"Expected one date after corporate signature; found {len(candidates)}")
        return candidates[0]
    candidates = []
    for pno, lines in make_lines(document).items():
        for i, line in enumerate(lines):
            if selector.get("prefix") and not line["text"].startswith(selector["prefix"]):
                continue
            if selector.get("contains") and selector["contains"] not in line["text"]:
                continue
            selected = [line]
            if re.fullmatch(r"\d{1,2} [A-Za-z]+ \d{4}",line["text"]):
                candidates.append({"page":pno,"bbox":line["bbox"],"text":line["text"]})
                continue
            for next_line in lines[i+1:]:
                gap = next_line["bbox"][1]-selected[-1]["bbox"][3]
                if gap > .014 or next_line["bbox"][1] > .95:
                    break
                selected.append(next_line)
            candidates.append({"page":pno,"bbox":union(selected),"text":norm(" ".join(x["text"] for x in selected))})
    if len(candidates) != 1:
        raise ValueError(f"Expected one paragraph candidate; found {len(candidates)}")
    return candidates[0]


def locate_table_cell(document, selector):
    candidates = []
    for pno, lines in make_lines(document).items():
        headings = [x for x in lines if x["text"].startswith(selector["table_heading"])]
        for heading in headings:
            headers = [x for x in lines if x["bbox"][1] < heading["bbox"][1] and selector["column"] in x["text"]]
            if not headers:
                continue
            header = max(headers,key=lambda x:x["bbox"][1])
            columns = re.findall(r"\b(?:[1-4]Q\d{2}\*?|\d{4}\*?)",header["text"])
            if selector["column"] not in columns:
                continue
            rows = [x for x in lines if x["text"].startswith(selector["row"]) and x["bbox"][1] > heading["bbox"][1]]
            for row in rows:
                # Multiline labels can place numeric cells between label baselines.
                nearby = [c for c in document["cells"] if c["page"]==pno and c["bbox"][0]>.35 and abs(cy(c)-cy(row))<.025 and re.fullmatch(r"[-+\d. ]+", norm(c["text"]))]
                if not nearby:
                    continue
                closest_y = cy(min(nearby,key=lambda c:abs(cy(c)-cy(row))))
                numeric_cells = sorted([c for c in nearby if abs(cy(c)-closest_y)<.005],key=lambda c:c["bbox"][0])
                values = []
                for cell in numeric_cells:
                    for token in norm(cell["text"]).split():
                        if re.fullmatch(r"-?\d+(?:\.\d+)?",token):
                            values.append({"page":pno,"bbox":cell["bbox"],"text":token})
                if len(values) == len(columns):
                    candidates.append(values[columns.index(selector["column"])])
    if len(candidates) != 1:
        raise ValueError(f"Expected one table candidate; found {len(candidates)}")
    return candidates[0]


def score(prediction, reference):
    if reference["kind"] == "table_cell":
        content_ok = prediction["text"] == reference["expected_value"]
    else:
        pattern = ".*?".join(r"(?<![\w.])"+re.escape(x)+r"(?![\w.])" for x in reference["expected_tokens"])
        content_ok = re.search(pattern,prediction["text"],re.I) is not None
    p = prediction["bbox"]
    g = reference["expected_bbox"]
    center = [(p[0]+p[2])/2,(p[1]+p[3])/2]
    # Center criterion is separate from content and the lookup algorithm.
    location_ok = prediction["page"]==reference["expected_page"] and g[0]<=center[0]<=g[2] and g[1]<=center[1]<=g[3]
    return {"content_correct":bool(content_ok),"location_correct":bool(location_ok),"joint_correct":bool(content_ok and location_ok)}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--reference",default="reference_set.v2.json")
    args=parser.parse_args()
    reference_path=ROOT/args.reference
    raw = reference_path.read_bytes()
    expected_hash = reference_path.with_suffix(".sha256").read_text().split()[0]
    assert hashlib.sha256(raw).hexdigest() == expected_hash
    reference_data=json.loads(raw)
    refs = reference_data["references"]
    results = {"reference_file":args.reference,"reference_set_version":reference_data.get("reference_set_version",1),"reference_sha256":expected_hash,"reference_count":len(refs),"engines":{},"negative_controls":[]}
    predictions = {}
    for engine in ["docling-native","pdfplumber","docling-plus-word-grounding"]:
        source_engine = "docling-native" if engine=="docling-plus-word-grounding" else engine
        docs = {sid:json.loads((ROOT/"tmp/extracted"/source_engine/(sid+".json")).read_text()) for sid in {r["source"] for r in refs}}
        word_docs = {sid:json.loads((ROOT/"tmp/extracted/pdfplumber"/(sid+".json")).read_text()) for sid in docs} if engine=="docling-plus-word-grounding" else {}
        rows = []
        for reference in refs:
            row = {k:reference[k] for k in ["id","source","kind","description"]}
            row.update(expected_page=reference["expected_page"],expected_value=reference.get("expected_value"))
            try:
                locator = locate_table_cell if reference["kind"]=="table_cell" else locate_paragraph
                prediction = locator(docs[reference["source"]],reference["selector"])
                if engine=="docling-plus-word-grounding" and reference["kind"]=="table_cell":
                    box=prediction["bbox"]
                    words=[c for c in word_docs[reference["source"]]["cells"] if c["page"]==prediction["page"] and norm(c["text"])==prediction["text"] and box[0] <= (c["bbox"][0]+c["bbox"][2])/2 <= box[2] and box[1] <= cy(c) <= box[3]]
                    if len(words)!=1:
                        raise ValueError(f"Word grounding is ambiguous: {len(words)} matches")
                    prediction={**prediction,"bbox":words[0]["bbox"]}
                predictions[engine,reference["id"]] = prediction
                row.update(score(prediction,reference))
                row.update(found_page=prediction["page"],found_bbox=[round(v,5) for v in prediction["bbox"]],found_value=prediction["text"] if reference["kind"]=="table_cell" else None,paragraph_word_count=len(prediction["text"].split()) if reference["kind"]=="paragraph" else None)
            except ValueError as exc:
                row.update(content_correct=False,location_correct=False,joint_correct=False,error=str(exc))
            rows.append(row)
        results["engines"][engine]={"content_correct":sum(x["content_correct"] for x in rows),"location_correct":sum(x["location_correct"] for x in rows),"joint_correct":sum(x["joint_correct"] for x in rows),"rows":rows}
    byid = {r["id"]:r for r in refs}
    for name,refid,field,value in [
        ("wrong_number","SG03","expected_value","999.9"),
        ("wrong_page","TH03","expected_page",1),
        ("wrong_cell_region","SG03","expected_bbox",[.81,.384,.89,.416]),
    ]:
        altered = copy.deepcopy(byid[refid])
        altered[field]=value
        outcome = score(predictions["docling-native",refid],altered)
        assert not outcome["joint_correct"],name
        results["negative_controls"].append({"name":name,"reference":refid,"rejected":True,**outcome})
    # A changed-input control verifies that the structural selector does not
    # merely recognise the literal date embedded in the original v1 selector.
    if byid["TH06"]["selector"].get("role")=="issued_date_after_corporate_signature":
        date_ref=byid["TH06"]
        original=json.loads((ROOT/"tmp/extracted/docling-native"/(date_ref["source"]+".json")).read_text())
        located=locate_paragraph(original,date_ref["selector"])
        changed=copy.deepcopy(original)
        changed_cells=[c for c in changed["cells"] if c["page"]==located["page"] and norm(c["text"])==located["text"]]
        assert len(changed_cells)==1
        changed_cells[0]["text"]="17 March 2031"
        changed_result=locate_paragraph(changed,date_ref["selector"])
        assert changed_result["text"]=="17 March 2031"
        assert not score(changed_result,date_ref)["content_correct"]
        absent=copy.deepcopy(original)
        for cell in absent["cells"]:
            if norm(cell["text"]).casefold()==norm(date_ref["selector"]["signature"]).casefold():
                cell["text"]="Unrelated organisation"
        try:
            locate_paragraph(absent,date_ref["selector"])
            raise AssertionError("Signature removal should reject the date lookup")
        except ValueError:
            pass
        results["structural_date_controls"]=[
            {"name":"changed_input_date","passed":True,"original_target_content_correct":False,"note":"Synthetic date returned after changing the input date and rejected by the original content target; no expected date supplied to locator."},
            {"name":"missing_corporate_signature","passed":True,"note":"Date lookup rejected when the signature anchor was removed."},
        ]
    results["method_limits"] = [
        "16 selected references; manually annotated and evaluated by the same assistant, not a blinded held-out benchmark.",
        "Location means correct physical PDF page and prediction center inside the manually drawn region; it does not measure exact bounding-box overlap.",
        "Paragraph content means selected ordered tokens/cues, not complete transcription or semantic equivalence.",
        "Table-cell retrieval uses an original deterministic row/column locator above native text cells; Docling native itself emitted zero structured tables.",
        "Only digital PDFs with native text were tested; no scanned pages or Thai-language body text were evaluated.",
        "V1 TH06 embedded the expected date in its selector. V2 replaces it with a structural date-after-signature selector after independent review. This post-outcome correction is recorded; original v1 targets/results are preserved. V2 was not frozen before all observation.",
        "Both the earlier date-line grouping fix and v2 semantic-selector correction were developed after outcomes. This is a development-set result, not held-out performance.",
        "The hybrid uses Docling values and pdfplumber word boxes. It must not be described as Docling-only location accuracy.",
    ]
    (ROOT/"results.json").write_text(json.dumps(results,indent=2)+"\n")
    print(json.dumps({k:{x:v[x] for x in ["content_correct","location_correct","joint_correct"]} for k,v in results["engines"].items()}))
    for engine,stats in results["engines"].items():
        for row in stats["rows"]:
            if not row["joint_correct"]:
                print(engine,json.dumps(row))


if __name__ == "__main__":
    main()
