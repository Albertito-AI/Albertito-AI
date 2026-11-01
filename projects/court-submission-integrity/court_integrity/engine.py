"""Deterministic checks over an explicitly annotated, supplied evidence package.

No network, language-model, identity, merits, admissibility or filing decisions.
A supplied transcription and its hash do not authenticate the original source.
"""
from __future__ import annotations

from collections import Counter, defaultdict, deque
from datetime import date
from decimal import Decimal, InvalidOperation, localcontext
import hashlib
import json
import re
from typing import Any

VERSION = "0.1.0a1"
SCHEMA_VERSION = "0.1"
MAX_BYTES = 5 * 1024 * 1024
MAX_ITEMS = 1000
LOCATOR = re.compile(r"^(para|pdf-page|printed-page|section):[^\s]{1,80}$")
DECIMAL = re.compile(r"^-?\d{1,18}(?:\.\d{1,8})?$")


class InputError(ValueError):
    """The supplied package violates the documented input contract."""


def canonical_bytes(value: Any) -> bytes:
    """Canonical JSON for this program only, not an external signing standard."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def whitespace(text: str) -> str:
    """Normalise whitespace only; retain case, punctuation, negation and numbers."""
    return " ".join(text.split())


def _object(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise InputError(f"{path}: expected object")
    return value


def _keys(value: dict, required: set[str], optional: set[str], path: str) -> None:
    missing, extra = required - value.keys(), value.keys() - required - optional
    if missing:
        raise InputError(f"{path}: missing fields {', '.join(sorted(missing))}")
    if extra:
        raise InputError(f"{path}: unsupported fields {', '.join(sorted(extra))}")


def _text(value: Any, path: str, *, empty: bool = False, maximum: int = 100_000) -> str:
    if not isinstance(value, str) or len(value) > maximum or (not empty and not value.strip()):
        raise InputError(f"{path}: expected {'possibly empty ' if empty else 'non-empty '}text (max {maximum})")
    # Unpaired surrogates cannot be serialised safely to UTF-8.
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise InputError(f"{path}: invalid Unicode") from exc
    return value


def _list(value: Any, path: str, maximum: int = MAX_ITEMS) -> list:
    if not isinstance(value, list) or len(value) > maximum:
        raise InputError(f"{path}: expected list (max {maximum})")
    return value


def _enum(value: Any, allowed: set[str], path: str) -> None:
    if not isinstance(value, str) or value not in allowed:
        raise InputError(f"{path}: expected one of {', '.join(sorted(allowed))}")


def _identifier(value: Any, path: str) -> str:
    return _text(value, path, maximum=160)


def _entries(values: Any, name: str, required: set[str], optional: set[str]) -> list[dict]:
    result, identifiers = [], set()
    for i, entry in enumerate(_list(values, name)):
        path = f"{name}[{i}]"
        entry = _object(entry, path)
        _keys(entry, required | {"id"}, optional, path)
        identifier = _identifier(entry["id"], path + ".id")
        if identifier in identifiers:
            raise InputError(f"{name}: duplicate id {identifier!r}")
        identifiers.add(identifier)
        result.append(entry)
    return result


def _date(value: Any, path: str) -> date:
    _text(value, path, maximum=10)
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise InputError(f"{path}: use YYYY-MM-DD")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise InputError(f"{path}: invalid calendar date") from exc


def _decimal(value: Any, path: str) -> Decimal:
    if not isinstance(value, str) or not DECIMAL.fullmatch(value):
        raise InputError(f"{path}: use a finite decimal string, without exponent, commas or currency sign")
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise InputError(f"{path}: invalid decimal") from exc


def validate_package(package: Any) -> None:
    """Strict contract validation. This is not substantive or legal verification."""
    p = _object(package, "package")
    required = {"schema_version", "profile", "submission", "sources", "claims"}
    optional = {"arithmetic", "chronology", "arguments", "requests", "responses"}
    _keys(p, required, optional, "package")
    if p["schema_version"] != SCHEMA_VERSION:
        raise InputError("package.schema_version: unsupported version")
    profile = _object(p["profile"], "profile")
    _keys(profile, {"id", "version", "jurisdiction", "stage", "status"}, set(), "profile")
    for k in profile:
        _text(profile[k], "profile." + k, maximum=160)
    # No unreviewed rule pack can be presented as court-approved in this alpha.
    _enum(profile["status"], {"fictional", "unvalidated"}, "profile.status")
    sub = _object(p["submission"], "submission")
    _keys(sub, {"id", "title", "jurisdiction", "stage", "blocks"}, set(), "submission")
    for k in ("id", "title", "jurisdiction", "stage"):
        _text(sub[k], "submission." + k, maximum=500)
    blocks = _entries(sub["blocks"], "blocks", {"text"}, set())
    if not blocks:
        raise InputError("submission.blocks: at least one block is required")
    for b in blocks:
        _text(b["text"], "block.text")
    for s in _entries(p["sources"], "sources",
                      {"kind", "title", "citation", "jurisdiction", "version", "origin",
                       "completeness", "locators"}, {"expected_text_digest"}):
        for k in ("title", "version", "origin", "jurisdiction"):
            _text(s[k], "source." + k, maximum=2000)
        _text(s["citation"], "source.citation", empty=True, maximum=500)
        _enum(s["kind"], {"authority", "exhibit"}, "source.kind")
        _enum(s["completeness"], {"complete", "partial", "unreadable"}, "source.completeness")
        locators = _object(s["locators"], "source.locators")
        if len(locators) > MAX_ITEMS:
            raise InputError("source.locators: too many locators")
        for loc, text in locators.items():
            if not isinstance(loc, str) or not LOCATOR.fullmatch(loc):
                raise InputError("source.locators: use explicit para:, pdf-page:, printed-page: or section: locators")
            _text(text, "source.locators.text", empty=True)
        if "expected_text_digest" in s:
            if not isinstance(s["expected_text_digest"], str) or not re.fullmatch(r"[0-9a-f]{64}", s["expected_text_digest"]):
                raise InputError("source.expected_text_digest: expected lowercase SHA-256")
    claims = _entries(p["claims"], "claims", {"block_id", "text", "kind", "evidence"}, {"assertion"})
    for c in claims:
        _identifier(c["block_id"], "claim.block_id")
        _text(c["text"], "claim.text")
        _enum(c["kind"], {"fact", "allegation", "legal_argument", "inference"}, "claim.kind")
        for ref in _list(c["evidence"], "claim.evidence", 100):
            _object(ref, "evidence")
            _keys(ref, {"source_id", "locator", "quotation"}, {"cited_as"}, "evidence")
            _identifier(ref["source_id"], "evidence.source_id")
            _text(ref["locator"], "evidence.locator", empty=True, maximum=100)
            if ref["locator"] and not LOCATOR.fullmatch(ref["locator"]):
                raise InputError("evidence.locator: explicit locator type required")
            _text(ref["quotation"], "evidence.quotation", empty=True)
            if "cited_as" in ref:
                _text(ref["cited_as"], "evidence.cited_as", maximum=500)
        if "assertion" in c:
            a = _object(c["assertion"], "claim.assertion")
            _keys(a, {"key", "context", "position", "scenario", "unit", "value"}, set(), "claim.assertion")
            for key in a:
                _text(a[key], "assertion." + key, maximum=2000)
    for a in _entries(p.get("arithmetic", []), "arithmetic", {"block_id", "components", "total", "unit"}, set()):
        _identifier(a["block_id"], "arithmetic.block_id")
        _text(a["unit"], "arithmetic.unit", maximum=160)
        components = _list(a["components"], "arithmetic.components")
        if not components:
            raise InputError("arithmetic.components: cannot be empty")
        for number in components:
            _decimal(number, "arithmetic.component")
        _decimal(a["total"], "arithmetic.total")
    for t in _entries(p.get("chronology", []), "chronology",
                      {"block_id", "description", "earlier", "later"}, set()):
        _identifier(t["block_id"], "chronology.block_id")
        _text(t["description"], "chronology.description", maximum=2000)
        _date(t["earlier"], "chronology.earlier")
        _date(t["later"], "chronology.later")
    for a in _entries(p.get("arguments", []), "arguments", {"conclusion", "premises"}, set()):
        _identifier(a["conclusion"], "argument.conclusion")
        for key in _list(a["premises"], "argument.premises"):
            _identifier(key, "argument.premise")
        if len(set(a["premises"])) != len(a["premises"]):
            raise InputError("argument.premises: duplicate premise")
    for r in _entries(p.get("requests", []), "requests", {"text"}, set()):
        _text(r["text"], "request.text")
    response_ids = set()
    for r in _list(p.get("responses", []), "responses"):
        _object(r, "response")
        _keys(r, {"request_id", "status", "source_ids", "explanation"}, set(), "response")
        _identifier(r["request_id"], "response.request_id")
        if r["request_id"] in response_ids:
            raise InputError("responses: duplicate request_id")
        response_ids.add(r["request_id"])
        _enum(r["status"], {"produced", "withheld", "not_held", "objected", "unknown"}, "response.status")
        _text(r["explanation"], "response.explanation", empty=True)
        for key in _list(r["source_ids"], "response.source_ids"):
            _identifier(key, "response.source_id")
    try:
        raw = canonical_bytes(p)
    except (TypeError, ValueError, UnicodeError, RecursionError) as exc:
        raise InputError("package cannot be serialised safely") from exc
    if len(raw) > MAX_BYTES:
        raise InputError("package exceeds 5 MiB limit")


def check_submission(package: dict[str, Any]) -> dict[str, Any]:
    """Return a reproducible report without modifying inputs or making decisions."""
    validate_package(package)
    p = package
    sources = {s["id"]: s for s in p["sources"]}
    blocks = {b["id"]: b["text"] for b in p["submission"]["blocks"]}
    claims = {c["id"]: c for c in p["claims"]}
    findings, citations = [], []
    source_records, unusable = [], set()

    def finding(code: str, status: str, location: str, detail: str,
                next_action: str, evidence: dict | None = None) -> None:
        findings.append({"id": f"F{len(findings) + 1:04d}", "code": code,
                         "status": status, "location": location, "detail": detail,
                         "next_action": next_action, "evidence": evidence or {}})

    finding("SCOPE_LIMIT", "UNRESOLVED", "submission",
            "Only supplied structured annotations and source transcriptions are checked. "
            "No source authenticity, real-world truth, legal support, current law, general logical validity "
            "or overall fitness for purpose is established.",
            "Obtain independent substantive review; do not use this report to accept or refuse a filing.")
    if p["profile"]["jurisdiction"] != p["submission"]["jurisdiction"] or p["profile"]["stage"] != p["submission"]["stage"]:
        finding("PROFILE_MISMATCH", "CHECK_FINDING", "profile",
                "The declared jurisdiction or procedural stage does not match the selected profile.",
                "Select and independently validate the correct local profile.")
    finding("PROFILE_NOT_APPROVED", "UNRESOLVED", "profile",
            f"Profile {p['profile']['id']} is {p['profile']['status']}; no court-approved procedural rules are implemented.",
            "Validate an exact court, proceeding, document type and effective rule version before operational use.")
    for sid, s in sources.items():
        actual = digest(s["locators"])
        expected = s.get("expected_text_digest")
        integrity = "UNPINNED" if expected is None else ("MATCHED_SUPPLIED_DIGEST" if expected == actual else "DIGEST_MISMATCH")
        source_records.append({"id": sid, "title": s["title"], "kind": s["kind"],
                               "citation": s["citation"], "origin": s["origin"],
                               "version": s["version"], "text_digest": actual,
                               "integrity": integrity, "completeness": s["completeness"],
                               "authenticity": "NOT_AUTHENTICATED"})
        if integrity == "DIGEST_MISMATCH":
            unusable.add(sid)
            finding("SOURCE_DIGEST_MISMATCH", "CHECK_FINDING", sid,
                    "The supplied transcription differs from its supplied expected digest.",
                    "Check the retained source version and mapping; do not silently reset the expected digest.")
        if s["completeness"] != "complete":
            finding("SOURCE_INCOMPLETE", "UNRESOLVED", sid,
                    f"Source extraction is declared {s['completeness']}.",
                    "Inspect the original or obtain a complete permitted transcription.")

    mapped_blocks, assertion_groups = set(), defaultdict(list)
    for cid, claim in claims.items():
        block_id = claim["block_id"]
        if block_id not in blocks:
            finding("BLOCK_NOT_FOUND", "CHECK_FINDING", cid,
                    f"Referenced submission block {block_id!r} is absent.", "Repair the claim-to-submission mapping.")
        elif whitespace(claim["text"]) not in whitespace(blocks[block_id]):
            finding("CLAIM_TEXT_NOT_ANCHORED", "CHECK_FINDING", cid,
                    "The annotated claim is not a whitespace-normalised substring of its stated block.",
                    "Correct the mapping against the unchanged submission; do not rewrite the original.")
        else:
            mapped_blocks.add(block_id)
        if not claim["evidence"]:
            finding("EVIDENCE_NOT_LINKED", "UNRESOLVED", cid,
                    "No supporting source has been linked in the supplied annotation.",
                    "Provide a permitted source or explain the evidential basis. Absence of a link is not falsity.")
        for index, ref in enumerate(claim["evidence"], 1):
            loc = f"{cid}/reference-{index}"
            sid, locator, quote = ref["source_id"], ref["locator"], ref["quotation"]
            row = {"claim_id": cid, "block_id": block_id, "source_id": sid,
                   "locator": locator, "submitted_quotation": quote, "source_passage": None,
                   "source_status": "NOT_SUPPLIED", "text_status": "NOT_CHECKED",
                   "support_status": "HUMAN_REVIEW_REQUIRED"}
            citations.append(row)
            if sid not in sources:
                finding("SOURCE_NOT_SUPPLIED", "UNRESOLVED", loc,
                        f"Source {sid!r} is not in this package. No external search was performed.",
                        "Supply or retrieve the permitted original. Do not label the source fictitious.")
                continue
            s = sources[sid]
            row["source_status"] = "SUPPLIED_NOT_AUTHENTICATED"
            if "cited_as" in ref and whitespace(ref["cited_as"]) != whitespace(s["citation"]):
                finding("CITATION_METADATA_MISMATCH", "CHECK_FINDING", loc,
                        "The cited reference differs from the supplied source citation metadata.",
                        "Check source identity and legitimate citation variants against the original.",
                        {"cited_as": ref["cited_as"], "source_citation": s["citation"]})
            if sid in unusable or s["completeness"] == "unreadable":
                row["text_status"] = "SOURCE_UNUSABLE"
                continue
            if not locator:
                row["text_status"] = "PINPOINT_NOT_SUPPLIED"
                finding("PINPOINT_NOT_SUPPLIED", "UNRESOLVED", loc,
                        "The reference has no typed pinpoint.", "Supply a paragraph, section or explicitly typed page locator.")
                continue
            if locator not in s["locators"]:
                code = "PINPOINT_NOT_FOUND" if s["completeness"] == "complete" else "PINPOINT_UNAVAILABLE"
                row["text_status"] = code
                finding(code, "CHECK_FINDING" if code == "PINPOINT_NOT_FOUND" else "UNRESOLVED", loc,
                        "The pinpoint is absent from the supplied transcription. This does not establish that it is absent from the original.",
                        "Inspect the original and distinguish paragraph, printed page and physical PDF page numbering.")
                continue
            passage = s["locators"][locator]
            row["source_passage"] = passage
            if not passage.strip():
                row["text_status"] = "SOURCE_PASSAGE_EMPTY"
                finding("SOURCE_PASSAGE_EMPTY", "UNRESOLVED", loc,
                        "The located source passage is empty.", "Inspect the original and repair the transcription.")
                continue
            if not quote.strip():
                row["text_status"] = "LOCATOR_PRESENT_NO_QUOTATION"
                finding("QUOTATION_NOT_SUPPLIED", "UNRESOLVED", loc,
                        "A source location exists but no quotation was supplied for comparison.",
                        "Read the passage in context and assess the proposition; quotation may not be appropriate for a paraphrase.")
            elif whitespace(quote) in whitespace(passage):
                row["text_status"] = "QUOTE_MATCH_IN_SUPPLIED_PASSAGE"
            else:
                other = [key for key, text in s["locators"].items()
                         if whitespace(quote) in whitespace(text)]
                code = "QUOTE_AT_DIFFERENT_PINPOINT" if other else "QUOTE_NOT_MATCHED"
                row["text_status"] = code
                finding(code, "CHECK_FINDING", loc,
                        "The quotation was not matched at the cited location using whitespace-only normalisation.",
                        "Inspect the original, punctuation, ellipses, translation and context. No correction has been applied.",
                        {"submitted_quotation": quote, "source_passage": passage,
                         "other_supplied_locations": other})
        finding("SUBSTANTIVE_REVIEW_REQUIRED", "UNRESOLVED", cid,
                f"The {claim['kind']} has not been verified for truth, legal support, relevance or inferential validity.",
                "Review the source and the argument in context. A matched quotation does not establish support.")
        if "assertion" in claim:
            a = claim["assertion"]
            key = tuple(a[k] for k in ("key", "context", "position", "scenario", "unit"))
            assertion_groups[key].append((cid, a["value"]))
    for key, values in assertion_groups.items():
        if len({whitespace(value) for _, value in values}) > 1:
            finding("ASSERTION_INCONSISTENCY_CANDIDATE", "REVIEW_CANDIDATE", ", ".join(cid for cid, _ in values),
                    "Different annotated values share the same key, context, party position, scenario and unit.",
                    "Check the annotation, temporal context and alternatives. This is not a finding of dishonesty or falsity.",
                    {"key": key[0], "context": key[1], "position": key[2], "scenario": key[3],
                     "unit": key[4], "values": [{"claim_id": cid, "value": value} for cid, value in values]})
    for block_id in blocks:
        if block_id not in mapped_blocks:
            finding("BLOCK_WITHOUT_ANCHORED_CLAIM", "UNRESOLVED", block_id,
                    "No correctly anchored claim annotation covers this block.",
                    "Review the original block. The program does not infer that unannotated content is sound.")
    for a in p.get("arithmetic", []):
        if a["block_id"] not in blocks:
            finding("BLOCK_NOT_FOUND", "CHECK_FINDING", a["id"],
                    "Arithmetic annotation references an absent block.", "Repair the annotation.")
        with localcontext() as context:
            context.prec = 64
            total = sum((Decimal(x) for x in a["components"]), Decimal(0))
        if total != Decimal(a["total"]):
            finding("ARITHMETIC_MISMATCH", "CHECK_FINDING", a["id"],
                    "The supplied components do not sum to the supplied total in the declared single unit.",
                    "Check the transcription, components, unit and intended calculation.",
                    {"components": a["components"], "stated_total": a["total"], "computed_sum": str(total), "unit": a["unit"]})
    for t in p.get("chronology", []):
        if t["block_id"] not in blocks:
            finding("BLOCK_NOT_FOUND", "CHECK_FINDING", t["id"],
                    "Chronology annotation references an absent block.", "Repair the annotation.")
        if date.fromisoformat(t["earlier"]) > date.fromisoformat(t["later"]):
            finding("CHRONOLOGY_ORDER_CONFLICT", "CHECK_FINDING", t["id"],
                    "The dates conflict with the ordering explicitly declared in the annotation.",
                    "Check the dates and whether that order is actually required. No legal deadline is calculated.",
                    {"description": t["description"], "earlier": t["earlier"], "later": t["later"]})
    edges, indegree = defaultdict(set), {cid: 0 for cid in claims}
    for a in p.get("arguments", []):
        refs = [a["conclusion"], *a["premises"]]
        missing = [cid for cid in refs if cid not in claims]
        if missing:
            finding("ARGUMENT_REFERENCE_MISSING", "CHECK_FINDING", a["id"],
                    "The argument annotation refers to missing claims.", "Repair the argument map.", {"missing_claims": missing})
            continue
        if not a["premises"]:
            finding("ARGUMENT_PREMISES_NOT_LINKED", "UNRESOLVED", a["id"],
                    "No premises are linked for the declared conclusion.", "Explain the basis or review whether premises are needed.")
        for premise in a["premises"]:
            if a["conclusion"] not in edges[premise]:
                edges[premise].add(a["conclusion"])
                indegree[a["conclusion"]] += 1
    ready = deque(cid for cid, n in indegree.items() if n == 0)
    while ready:
        node = ready.popleft()
        for child in sorted(edges[node]):
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)
    unresolved_graph = sorted(cid for cid, n in indegree.items() if n > 0)
    if unresolved_graph:
        finding("ARGUMENT_DEPENDENCY_CYCLE", "REVIEW_CANDIDATE", "argument map",
                "The declared dependency graph contains a cycle. Listed claims may be in or downstream of that cycle.",
                "Inspect the argument map and independent evidential basis. This does not prove a logical fallacy.",
                {"affected_claims": unresolved_graph})
    requests = {r["id"]: r for r in p.get("requests", [])}
    responses = {r["request_id"]: r for r in p.get("responses", [])}
    for rid in requests:
        if rid not in responses:
            finding("REQUEST_RESPONSE_NOT_SUPPLIED", "UNRESOLVED", rid,
                    "No response record is supplied for this declared request.",
                    "Record the response or a reasoned objection; do not compel privileged material.")
    for rid, r in responses.items():
        if rid not in requests:
            finding("UNKNOWN_REQUEST", "CHECK_FINDING", rid,
                    "The response references an absent request.", "Repair the request-response mapping.")
        if r["status"] == "produced" and not r["source_ids"]:
            finding("PRODUCED_SOURCE_NOT_LINKED", "UNRESOLVED", rid,
                    "The response is marked produced without linked source records.", "Link the permitted documents or correct the response.")
        for sid in r["source_ids"]:
            if sid not in sources:
                finding("RESPONSE_SOURCE_NOT_SUPPLIED", "UNRESOLVED", rid,
                        f"Linked response source {sid!r} is absent from this package.", "Reconcile the production index, without publishing private evidence.")
        if r["status"] in {"withheld", "not_held", "objected"} and not r["explanation"].strip():
            finding("RESPONSE_EXPLANATION_NOT_SUPPLIED", "UNRESOLVED", rid,
                    "The non-production response has no explanation in this package.",
                    "Record a permitted explanation; privilege and legal sufficiency require human decision.")
        if r["status"] == "unknown":
            finding("RESPONSE_UNRESOLVED", "UNRESOLVED", rid,
                    "The supplied response status is unknown.", "Resolve or expressly retain the uncertainty.")
    statuses = Counter(f["status"] for f in findings)
    text_statuses = Counter(c["text_status"] for c in citations)
    return {
        "report_schema_version": SCHEMA_VERSION, "engine_version": VERSION,
        "package_digest": digest(p), "submission_id": p["submission"]["id"],
        "title": p["submission"]["title"], "profile": dict(p["profile"]),
        "overall_status": "HUMAN_REVIEW_REQUIRED", "automatic_filing_decision": "NONE",
        "truth_certification": False, "independent_human_review": "NOT_PERFORMED",
        "coverage": {"blocks_total": len(blocks), "blocks_with_anchored_annotations": len(mapped_blocks),
                     "claims_supplied": len(claims), "references_supplied": len(citations),
                     "quote_matches_in_supplied_passages": text_statuses["QUOTE_MATCH_IN_SUPPLIED_PASSAGE"],
                     "source_authenticity": "NOT_ASSESSED", "legal_entailment": "NOT_ASSESSED",
                     "real_world_truth": "NOT_ASSESSED", "general_coherence": "NOT_ASSESSED",
                     "annotation_completeness": "NOT_ASSESSED", "current_law": "NOT_ASSESSED"},
        "finding_counts": dict(sorted(statuses.items())), "findings": findings,
        "citation_checks": citations, "source_records": source_records,
        "submission_blocks": [{"id": k, "text": text} for k, text in blocks.items()],
    }
