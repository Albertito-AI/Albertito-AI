"""Generate original fictional examples; these are not court authorities or evidence."""
from copy import deepcopy
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from court_integrity.engine import digest


def source(sid, kind, locators, citation=""):
    return {"id": sid, "kind": kind, "title": "Fictional training source " + sid,
            "citation": citation, "jurisdiction": "FICTIONAL", "version": "fixture-v1",
            "origin": "fictional://training/" + sid, "completeness": "complete",
            "locators": locators, "expected_text_digest": digest(locators)}


def matched_package():
    text = "The fictional invoice records a total of SGD 1,250."
    return {"schema_version": "0.1",
            "profile": {"id": "fictional-production-demo", "version": "1", "jurisdiction": "FICTIONAL",
                        "stage": "document-production", "status": "fictional"},
            "submission": {"id": "SYN-MATCHED-001", "title": "Fictional source-linked submission",
                           "jurisdiction": "FICTIONAL", "stage": "document-production",
                           "blocks": [{"id": "p1", "text": text}]},
            "sources": [source("EX-1", "exhibit", {"printed-page:1": "Fictional invoice. Total: SGD 1,250."})],
            "claims": [{"id": "C1", "block_id": "p1", "text": text, "kind": "fact",
                        "evidence": [{"source_id": "EX-1", "locator": "printed-page:1",
                                      "quotation": "Total: SGD 1,250."}]}],
            "arithmetic": [{"id": "SUM-1", "block_id": "p1", "components": ["1000", "250"],
                            "total": "1250", "unit": "SGD"}],
            "requests": [{"id": "R1", "text": "Produce the fictional invoice."}],
            "responses": [{"request_id": "R1", "status": "produced", "source_ids": ["EX-1"], "explanation": "Training example only."}]}


def adverse_package():
    p = matched_package()
    p["submission"]["id"] = "SYN-ADVERSE-001"
    p["submission"]["title"] = "Fictional discovery-stage submission: intentionally defective example"
    sentences = [
        "The fictional invoice records a total of SGD 1,400.",
        "The fictional rule requires disclosure without any exception.",
        "The fictional rule states that a court may order production.",
        "The same transfer was SGD 1,200.",
        "The same transfer was SGD 1,500.",
        "The absent training authority supports this application.",
        "The notice was sent on 15 May 2026 and received on 10 May 2026.",
        "The partly transcribed record confirms receipt.",
        "Additional narrative has not been mapped to any claim."
    ]
    p["submission"]["blocks"] = [{"id": f"p{i}", "text": text} for i, text in enumerate(sentences, 1)]
    p["claims"][0]["text"] = sentences[0]
    p["claims"][0]["evidence"][0]["quotation"] = "Total: SGD 1,400."
    p["sources"].append(source("AUTH-1", "authority", {
        "para:8": "In this fictional exercise, a court may order production.",
        "para:9": "This fictional direction contains exceptions. Privileged material is not included in this training request."
    }, "DEMO-AUTHORITY-001"))
    p["sources"].append(source("EX-PARTIAL", "exhibit", {"pdf-page:1": "Fictional partial transcript."}))
    p["sources"][-1]["completeness"] = "partial"
    def claim(n, kind, evidence):
        return {"id": f"C{n}", "block_id": f"p{n}", "text": sentences[n-1], "kind": kind, "evidence": evidence}
    p["claims"].append(claim(2, "legal_argument", [{"source_id": "AUTH-1", "locator": "para:9",
        "quotation": "Disclosure is required without any exception.", "cited_as": "DEMO-AUTHORITY-002"}]))
    p["claims"].append(claim(3, "legal_argument", [{"source_id": "AUTH-1", "locator": "para:9",
        "quotation": "a court may order production.", "cited_as": "DEMO-AUTHORITY-001"}]))
    for n, amount in [(4, "1200"), (5, "1500")]:
        c = claim(n, "allegation", [])
        c["assertion"] = {"key": "transfer.amount", "context": "same-transfer-1", "position": "claimant",
                          "scenario": "primary", "unit": "SGD", "value": amount}
        p["claims"].append(c)
    p["claims"].append(claim(6, "legal_argument", [{"source_id": "AUTH-NOT-SUPPLIED", "locator": "para:42", "quotation": "Relief follows."}]))
    p["claims"].append(claim(7, "fact", []))
    p["claims"].append(claim(8, "fact", [{"source_id": "EX-PARTIAL", "locator": "pdf-page:8", "quotation": "Received."}]))
    p["arithmetic"][0]["total"] = "1400"
    p["chronology"] = [{"id": "DATE-1", "block_id": "p7", "description": "Declared send date must not be after declared receipt date.",
                         "earlier": "2026-05-15", "later": "2026-05-10"}]
    p["arguments"] = [{"id": "ARG1", "conclusion": "C2", "premises": ["C3"]},
                      {"id": "ARG2", "conclusion": "C3", "premises": ["C2"]}]
    p["requests"].append({"id": "R2", "text": "State the response to the fictional second request."})
    p["responses"][0]["source_ids"] = ["EX-MISSING"]
    return p


def unknown_package():
    p = matched_package()
    p["submission"]["id"] = "SYN-UNKNOWN-001"
    p["submission"]["title"] = "Fictional unavailable-source example: uncertainty is not falsity"
    p["sources"] = []
    p["arithmetic"] = []
    return p


if __name__ == "__main__":
    directory = Path(__file__).parent
    for name, package in [("matched", matched_package()), ("adverse", adverse_package()), ("unknown", unknown_package())]:
        (directory / f"{name}.json").write_text(json.dumps(package, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
