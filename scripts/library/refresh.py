#!/usr/bin/env python3
"""Refresh a bounded public research index using publisher-deposited metadata.

No model, credential, full text, abstract, or private repository is used. Network
requests are restricted to Crossref's HTTPS works endpoint. Source inspection
and substantive review remain distinct from registry-metadata retrieval.
"""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import html
from html.parser import HTMLParser
import ipaddress
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
API = "https://api.crossref.org/works"
MAX_RESPONSE_BYTES = 3_000_000
SELECT_FIELDS = (
    "DOI,title,author,publisher,container-title,published,published-online,"
    "published-print,issued,type,update-to,updated-by,relation,subject,URL"
)
ALLOWED_TYPES = {"journal-article", "proceedings-article", "book-chapter"}
NOTICE = re.compile(r"^(?:retraction|retracted|withdrawal|withdrawn|correction|erratum|corrigendum)\b", re.I)
SGT = ZoneInfo("Asia/Singapore")


class ValidationError(ValueError):
    pass


class PlainText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.ignored = 0

    def handle_starttag(self, tag, attrs):
        if tag.lower() in {"script", "style"}:
            self.ignored += 1

    def handle_endtag(self, tag):
        if tag.lower() in {"script", "style"} and self.ignored:
            self.ignored -= 1

    def handle_data(self, data):
        if not self.ignored:
            self.parts.append(data)


def clean_text(value, limit=1500):
    if not isinstance(value, str):
        return ""
    parser = PlainText()
    parser.feed(value[:20_000])
    value = unicodedata.normalize("NFC", html.unescape(" ".join(parser.parts)))
    value = "".join(c for c in value if unicodedata.category(c) not in {"Cc", "Cf"} or c.isspace())
    return " ".join(value.split())[:limit]


def timestamp(value):
    if isinstance(value, dt.datetime):
        moment = value
    else:
        moment = dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if moment.tzinfo is None:
        raise ValidationError("Timestamps must include a timezone")
    return moment.astimezone(dt.timezone.utc).replace(microsecond=0)


def iso(value):
    return timestamp(value).isoformat().replace("+00:00", "Z")


def service_day(value):
    return timestamp(value).astimezone(SGT).date().isoformat()


def safe_url(value):
    if not isinstance(value, str) or len(value) > 2200 or any(ord(c) < 32 for c in value):
        return False
    try:
        parts = urllib.parse.urlsplit(value)
        host = parts.hostname or ""
        if parts.scheme != "https" or not host or parts.username or parts.password or parts.port not in (None, 443):
            return False
        if host.lower() == "localhost" or host.lower().endswith((".localhost", ".local", ".internal")):
            return False
        try:
            if not ipaddress.ip_address(host).is_global:
                return False
        except ValueError:
            if "." not in host:
                return False
        return not any(c in value for c in "<>\\\"{}")
    except (ValueError, TypeError):
        return False


def canonical_url(value):
    if not safe_url(value):
        return ""
    parts = urllib.parse.urlsplit(value)
    query = [(k, v) for k, v in urllib.parse.parse_qsl(parts.query) if not k.lower().startswith("utm_")]
    return urllib.parse.urlunsplit(("https", parts.netloc.lower(), parts.path.rstrip("/"), urllib.parse.urlencode(query), ""))


def normalise_doi(value):
    if not isinstance(value, str):
        return ""
    value = html.unescape(value.strip())
    if value.lower().startswith(("https://doi.org/", "http://doi.org/", "https://dx.doi.org/", "http://dx.doi.org/")):
        value = urllib.parse.urlsplit(value).path.lstrip("/")
    value = urllib.parse.unquote(re.sub(r"^doi:\s*", "", value, flags=re.I)).lower()
    if not re.fullmatch(r"10\.\d{4,9}/[^\s<>\\\"#?{}]+", value) or len(value) > 240 or any(unicodedata.category(c) in {"Cc", "Cf"} for c in value):
        return ""
    if any(segment in {".", ".."} for segment in value.split("/")):
        return ""
    return value


def doi_url(doi):
    return "https://doi.org/" + urllib.parse.quote(doi, safe="/():;._-+")


def work_url(doi):
    return API + "/" + urllib.parse.quote(doi, safe="")


def item_doi(item):
    return normalise_doi(item.get("doi") or item.get("citation", {}).get("doi"))


def item_url(item):
    if item_doi(item):
        return canonical_url(doi_url(item_doi(item)))
    return canonical_url(item.get("citation", {}).get("url") or item.get("verification", {}).get("source_url") or next((l.get("url") for l in item.get("links", []) if isinstance(l, dict)), ""))


def load_json(path, default=None):
    if not path.exists() and default is not None:
        return copy.deepcopy(default)
    if path.stat().st_size > 25_000_000:
        raise ValidationError(f"Oversized local input: {path.name}")
    return json.loads(path.read_text(encoding="utf-8"))


def validate_config(config):
    if config.get("schema_version") != 1 or config.get("api_url") != API:
        raise ValidationError("Only the fixed Crossref HTTPS works API is supported")
    if not 1900 <= config.get("minimum_year", 0) <= 2100:
        raise ValidationError("Invalid minimum year")
    if not 1 <= config.get("daily_limit", 0) <= 20 or not 0 <= config.get("recheck_limit", 0) <= 12:
        raise ValidationError("Invalid bounded refresh limits")
    if not 1 <= config.get("recent_index_days", 30) <= 90 or not 0 <= config.get("backfill_max_offset", 400) <= 2000:
        raise ValidationError("Invalid bounded discovery windows")
    if not 1 <= config.get("pending_limit_per_topic", 120) <= 250 or config.get("chapter_limit_per_venue_per_day", 1) != 1:
        raise ValidationError("Invalid queue or chapter-diversity bounds")
    sources = config.get("sources", [])
    if not 1 <= len(sources) <= 8:
        raise ValidationError("A bounded source list is required")
    seen = set()
    for source in sources:
        if not re.fullmatch(r"[a-z0-9-]{3,60}", source.get("id", "")) or source["id"] in seen:
            raise ValidationError("Source identifiers must be unique")
        seen.add(source["id"])
        if not 1 <= source.get("rows", 0) <= 100 or not 1 <= source.get("daily_limit", 0) <= 5:
            raise ValidationError("Invalid source bounds")
        if not clean_text(source.get("label")) or not clean_text(source.get("query")):
            raise ValidationError("Source label and query are required")
        groups = source.get("required_groups", [])
        if not 2 <= len(groups) <= 5 or any(not isinstance(g, list) or not 1 <= len(g) <= 30 or any(not isinstance(t, str) or not t.strip() for t in g) for g in groups):
            raise ValidationError("Each topic needs at least two bounded relevance groups")


def validate_item(item):
    if not isinstance(item, dict):
        raise ValidationError("Each entry must be an object")
    for key in ("id", "title", "type", "description", "use_for"):
        if not isinstance(item.get(key), str) or not item[key].strip():
            raise ValidationError(f"Entry is missing {key}")
    if not re.fullmatch(r"[a-zA-Z0-9_-]{3,100}", item["id"]):
        raise ValidationError("Unsafe entry identifier")
    if item.get("origin") not in {"crossref", "curated_reference"}:
        raise ValidationError("Entry origin is required")
    if item.get("review_status") not in {"metadata_only", "source_inspected", "needs_review"}:
        raise ValidationError("Invalid review status")
    if item["origin"] == "crossref" and item["review_status"] == "source_inspected":
        raise ValidationError("Metadata ingestion cannot confer substantive source inspection")
    if not isinstance(item.get("topics"), list) or not item["topics"] or any(not isinstance(t, str) or not t for t in item["topics"]):
        raise ValidationError("Topics must be nonempty text labels")
    if not isinstance(item.get("links"), list) or not item["links"]:
        raise ValidationError("Source links are required")
    for link in item["links"]:
        if not isinstance(link, dict) or not safe_url(link.get("url")):
            raise ValidationError("Unsafe source link")
    verification = item.get("verification", {})
    if not safe_url(verification.get("source_url")) or not verification.get("scope"):
        raise ValidationError("Attributed verification scope is required")
    timestamp(verification.get("checked_at"))
    timestamp(item.get("added_at"))
    for part in (item.get("citation", {}), item.get("rights", {})):
        if part.get("url") and not safe_url(part["url"]):
            raise ValidationError("Unsafe citation or rights URL")
    if item["origin"] == "crossref":
        if not item_doi(item) or not isinstance(item.get("authors"), list) or not item["authors"] or not item.get("publisher"):
            raise ValidationError("Research metadata needs a DOI, authors and publisher")
        if not item.get("publication_date") or item.get("abstract") or item.get("full_text"):
            raise ValidationError("Metadata records must have a date and omit abstracts/full text")


def validate_library(library, base=None):
    if library.get("schema_version") != 1 or library.get("status") not in {"ok", "degraded", "failed"}:
        raise ValidationError("Invalid library header")
    timestamp(library.get("generated_at"))
    if library.get("last_successful_refresh"):
        timestamp(library["last_successful_refresh"])
    if not isinstance(library.get("items"), list) or not isinstance(library.get("source_runs"), list):
        raise ValidationError("Library items and source runs must be lists")
    ids, dois, urls = set(), set(), set()
    for item in (base or {}).get("items", []):
        ids.add(item.get("id"))
        if item_doi(item):
            dois.add(item_doi(item))
        if item_url(item):
            urls.add(item_url(item))
    for item in library["items"]:
        validate_item(item)
        doi, url = item_doi(item), item_url(item)
        if item["id"] in ids or (doi and doi in dois) or (url and url in urls):
            raise ValidationError("Duplicate identifier, DOI or primary URL")
        ids.add(item["id"])
        if doi:
            dois.add(doi)
        if url:
            urls.add(url)
    for item in library.get("pending", []):
        validate_item(item)
        doi, url = item_doi(item), item_url(item)
        if item["id"] in ids or (doi and doi in dois) or (url and url in urls):
            raise ValidationError("A pending record duplicates published or queued metadata")
        ids.add(item["id"])
        if doi:
            dois.add(doi)
        if url:
            urls.add(url)
    for archived in library.get("superseded_records", []):
        if not isinstance(archived, dict) or not archived.get("superseded_by"):
            raise ValidationError("A superseded record must identify its replacement")
        validate_item(archived.get("record"))
        timestamp(archived.get("superseded_at"))
    for run in library["source_runs"]:
        if run.get("status") not in {"ok", "degraded", "failed"}:
            raise ValidationError("Invalid source status")
        timestamp(run.get("checked_at"))
        if run.get("url") and not safe_url(run["url"]):
            raise ValidationError("Unsafe source receipt URL")


def publication_date(work, now, minimum_year):
    choices = []
    for key in ("published-online", "published-print", "published", "issued"):
        parts = work.get(key, {}).get("date-parts", []) if isinstance(work.get(key), dict) else []
        if not parts or not isinstance(parts[0], list) or not 1 <= len(parts[0]) <= 3:
            continue
        values = parts[0]
        if any(not isinstance(n, int) or isinstance(n, bool) for n in values):
            continue
        try:
            date = dt.date(values[0], values[1] if len(values) > 1 else 1, values[2] if len(values) > 2 else 1)
        except (ValueError, OverflowError):
            continue
        if minimum_year <= date.year and date <= timestamp(now).date():
            label = f"{date.year:04d}" + (f"-{date.month:02d}" if len(values) > 1 else "") + (f"-{date.day:02d}" if len(values) > 2 else "")
            choices.append((date, -len(values), label, key))
    if not choices:
        return None
    date, _, label, field = min(choices)
    return {"value": label, "year": date.year, "source_field": field, "precision": ["year", "month", "day"][label.count("-")]}


def relevance(work, source):
    title = clean_text(" ".join(t for t in work.get("title", []) if isinstance(t, str))) if isinstance(work.get("title"), list) else ""
    subjects = " ".join(clean_text(s) for s in work.get("subject", []) if isinstance(s, str)) if isinstance(work.get("subject"), list) else ""
    haystack = re.sub(r"[-–—]", " ", (title + " " + subjects).casefold())
    matches = []
    for group in source["required_groups"]:
        found = [term for term in group if re.search(r"(?<!\w)" + re.escape(term.casefold()) + r"(?!\w)", haystack)]
        if not found:
            return []
        matches.append(found)
    return matches


def update_flag(work):
    titles = work.get("title", [])
    if isinstance(titles, list) and titles and NOTICE.search(clean_text(titles[0])):
        return "Publisher metadata identifies an update, correction, withdrawal or retraction notice."
    for field in ("update-to", "updated-by"):
        for update in work.get(field, []) if isinstance(work.get(field, []), list) else []:
            if isinstance(update, dict) and any(term in str(update.get("type", "")).lower() for term in ("retract", "withdraw", "correct", "errat")):
                return "Publisher metadata includes a correction, withdrawal or retraction relationship."
    relation = work.get("relation", {})
    if isinstance(relation, dict) and any(relation.get(key) for key in ("is-retracted-by", "is-withdrawn-by", "is-corrected-by", "is-updated-by")):
        return "Publisher metadata includes a later update relationship requiring review."
    return ""


def normalise_work(work, source, now, minimum_year):
    if not isinstance(work, dict):
        return None, "malformed"
    doi = normalise_doi(work.get("DOI"))
    title = clean_text(work.get("title", [""])[0]) if isinstance(work.get("title"), list) and work["title"] else ""
    publisher = clean_text(work.get("publisher"), 300)
    authors = []
    for author in work.get("author", []) if isinstance(work.get("author", []), list) else []:
        if not isinstance(author, dict):
            continue
        name = clean_text(" ".join(filter(None, [clean_text(author.get("given"), 150), clean_text(author.get("family"), 150)])), 300) or clean_text(author.get("name"), 300)
        if name and name not in authors:
            authors.append(name)
    date = publication_date(work, now, minimum_year)
    if not doi or len(title) < 8 or not publisher or not authors or not date:
        return None, "missing_or_invalid_metadata"
    if work.get("type") not in ALLOWED_TYPES:
        return None, "unsupported_record_type"
    if update_flag(work):
        return None, "update_notice"
    matched = relevance(work, source)
    if not matched:
        return None, "outside_topic"
    venue = clean_text(work.get("container-title", [""])[0], 300) if isinstance(work.get("container-title"), list) and work["container-title"] else ""
    url = doi_url(doi)
    source_url = work_url(doi)
    citation = "; ".join(authors) + f" ({date['year']}). {title}." + (f" {venue}." if venue else "") + " " + url
    item = {
        "id": "discovery-" + hashlib.sha256(doi.encode()).hexdigest()[:20],
        "title": title,
        "type": "research",
        "work_type": work["type"],
        "description": "Publisher-deposited bibliographic record discovered through Crossref. Its title or subject terms match this collection; the article's contents have not been reviewed here.",
        "maturity": "Bibliographic record; content review pending",
        "topics": [source["label"]],
        "authors": authors,
        "publisher": publisher,
        "venue": venue,
        "year": date["year"],
        "publication_date": date["value"],
        "publication_date_precision": date["precision"],
        "publication_date_source": date["source_field"],
        "doi": doi,
        "origin": "crossref",
        "review_status": "metadata_only",
        "discovery_source_id": source["id"],
        "added_at": iso(now),
        "last_metadata_check": iso(now),
        "use_for": "Locate and assess this publication for " + source["label"].lower() + ". The relevance match is available in the exported record.",
        "relevance": {"basis": "Title and publisher-supplied subject terms", "matched_groups": matched, "source_id": source["id"]},
        "limitation": "Registry metadata is not a full-text review, peer-review certification, legal conclusion or confirmation of free access. Check the publisher's current record before relying on the work.",
        "links": [{"label": "Open publication via DOI", "url": url, "kind": "publication"}, {"label": "Inspect registry metadata", "url": source_url, "kind": "source"}],
        "verification": {"checked_at": iso(now), "source_url": source_url, "revision": None, "scope": "Bibliographic fields retrieved from Crossref and checked for required fields, topic fit and duplicates. DOI landing page and full text were not fetched; substantive review remains pending."},
        "citation": {"available": True, "format": "text", "url": url, "text": citation, "doi": doi},
        "rights": {"summary": "This entry contains bibliographic metadata and a source link. Full text and third-party materials retain their own access and reuse terms."},
        "related_item_ids": [],
    }
    item["metadata_sha256"] = hashlib.sha256(json.dumps({key: item[key] for key in ("title", "authors", "publisher", "venue", "publication_date", "doi")}, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    return item, ""


def backfill_position(source, config, previous, now):
    saved = previous.get("coverage", {}).get("sources", {}).get(source["id"], {})
    year = saved.get("year", timestamp(now).year)
    offset = saved.get("offset", 0)
    if not isinstance(year, int) or not config["minimum_year"] <= year <= timestamp(now).year:
        year = timestamp(now).year
    if not isinstance(offset, int) or not 0 <= offset <= config.get("backfill_max_offset", 400):
        offset = 0
    return {"year": year, "offset": offset}


def next_backfill_position(source, config, position, returned, now):
    next_offset = position["offset"] + source["rows"]
    if returned < source["rows"] or next_offset > config.get("backfill_max_offset", 400):
        return {"year": position["year"] - 1 if position["year"] > config["minimum_year"] else timestamp(now).year, "offset": 0}
    return {"year": position["year"], "offset": next_offset}


def source_url(source, config, now, mode="recent", position=None):
    today = timestamp(now).date()
    params = {"query.title": source["query"], "rows": source["rows"], "order": "desc", "select": SELECT_FIELDS}
    if mode == "recent":
        start = today - dt.timedelta(days=config.get("recent_index_days", 30))
        params.update({"sort": "indexed", "filter": f"from-index-date:{start.isoformat()},until-index-date:{today.isoformat()},from-pub-date:{config['minimum_year']}-01-01,until-pub-date:{today.isoformat()}"})
    else:
        if position is None:
            raise ValidationError("Historical retrieval needs a stored position")
        end = min(dt.date(position["year"], 12, 31), today)
        params.update({"sort": "published", "offset": position["offset"], "filter": f"from-pub-date:{position['year']}-01-01,until-pub-date:{end.isoformat()}"})
    return API + "?" + urllib.parse.urlencode(params)


def approved_api_url(url):
    if not safe_url(url):
        return False
    parts = urllib.parse.urlsplit(url)
    return parts.hostname == "api.crossref.org" and (parts.path == "/works" or parts.path.startswith("/works/"))


class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not approved_api_url(newurl):
            raise ValidationError("Crossref redirected outside the allowed API")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_json(url):
    if not approved_api_url(url):
        raise ValidationError("Network access is restricted to Crossref works")
    opener = urllib.request.build_opener(SafeRedirect())
    request = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "AlbertitoAIResearchLibrary/1.0 (+https://github.com/Albertito-AI/Albertito-AI)"})
    for attempt in range(2):
        try:
            with opener.open(request, timeout=20) as response:
                data = response.read(MAX_RESPONSE_BYTES + 1)
                if len(data) > MAX_RESPONSE_BYTES:
                    raise ValidationError("Crossref response exceeds the size limit")
                payload = json.loads(data.decode("utf-8"))
                if not isinstance(payload, dict) or payload.get("status") != "ok" or not isinstance(payload.get("message"), dict):
                    raise ValidationError("Unexpected Crossref response shape")
                return payload["message"], hashlib.sha256(data).hexdigest()
        except urllib.error.HTTPError as error:
            if error.code in {429, 502, 503, 504} and attempt == 0:
                retry = error.headers.get("Retry-After", "2")
                time.sleep(min(5, max(1, int(retry))) if str(retry).isdigit() else 2)
                continue
            raise
    raise ValidationError("Crossref request failed")


def get_responses(config, previous, now):
    responses = {}
    for source in config["sources"]:
        position = backfill_position(source, config, previous, now)
        result = {"items": [], "queries": [], "url": source_url(source, config, now)}
        errors = []
        for mode in ("recent", "historical"):
            url = source_url(source, config, now, mode, position)
            receipt = {"mode": mode, "url": url, "status": "failed", "checked_at": iso(now)}
            try:
                message, digest = fetch_json(url)
                works = message.get("items")
                if not isinstance(works, list) or len(works) > source["rows"]:
                    raise ValidationError("Unexpected or oversized Crossref item list")
                result["items"].extend(works)
                receipt.update({"status": "ok", "returned": len(works), "response_sha256": digest, "reported_total": message.get("total-results")})
                if mode == "historical":
                    result["backfill_position_after"] = next_backfill_position(source, config, position, len(works), now)
                    receipt["position"] = position
            except (OSError, ValueError, urllib.error.URLError) as error:
                receipt["error"] = clean_text(str(error), 300)
                errors.append(mode + ": " + receipt["error"])
            result["queries"].append(receipt)
        result["status"] = "failed" if len(errors) == 2 else "degraded" if errors else "ok"
        if errors:
            result["error"] = "; ".join(errors)
        responses[source["id"]] = result
    old_records = sorted((i for i in previous.get("items", []) if i.get("origin") == "crossref"), key=lambda i: (i.get("last_metadata_attempt", i.get("last_metadata_check", "")), i["id"]))[:config["recheck_limit"]]
    rechecks = {}
    for item in old_records:
        doi = item_doi(item)
        if not doi:
            continue
        try:
            message, digest = fetch_json(work_url(doi))
            if normalise_doi(message.get("DOI")) != doi:
                raise ValidationError("Crossref returned another DOI")
            rechecks[doi] = {"item": message, "response_sha256": digest}
        except (OSError, ValueError, urllib.error.URLError) as error:
            rechecks[doi] = {"error": clean_text(str(error), 300)}
    return responses, rechecks


def build_library(config, references, base, previous, responses, now, rechecks=None, run_url=None, curated_only=False):
    """Pure transform, with injectable source results for offline testing."""
    validate_config(config)
    now = timestamp(now)
    day = service_day(now)
    old = {i["id"]: copy.deepcopy(i) for i in previous.get("items", [])}
    # Reconciliation removes promoted entries from the active working map. Keep
    # their original identities and dates available for the replacement below.
    previous_ids = {i["id"]: i for i in previous.get("items", [])}
    previous_dois = {item_doi(i): i for i in previous.get("items", []) if item_doi(i)}
    previous_urls = {item_url(i): i for i in previous.get("items", []) if item_url(i)}
    superseded = copy.deepcopy(previous.get("superseded_records", []))
    base_ids = {i.get("id"): i.get("id") for i in base.get("items", [])}
    base_dois = {item_doi(i): i.get("id") for i in base.get("items", []) if item_doi(i)}
    base_urls = {item_url(i): i.get("id") for i in base.get("items", []) if item_url(i)}
    configured_refs = references if isinstance(references, list) else references.get("items", [])
    ref_ids = {i.get("id"): i.get("id") for i in configured_refs}
    ref_dois = {item_doi(i): i.get("id") for i in configured_refs if item_doi(i)}
    ref_urls = {item_url(i): i.get("id") for i in configured_refs if item_url(i)}

    def superseded_by_base(item):
        return base_ids.get(item.get("id")) or base_dois.get(item_doi(item)) or base_urls.get(item_url(item))

    transferred = []
    for item_id, item in list(old.items()):
        replacement_id = superseded_by_base(item)
        replacement_kind = "base catalogue"
        configured_replacement = ref_ids.get(item_id) or ref_dois.get(item_doi(item)) or ref_urls.get(item_url(item))
        if not replacement_id and configured_replacement and (item.get("origin") == "crossref" or configured_replacement != item_id):
            replacement_id = configured_replacement
            replacement_kind = "curated references configuration"
        if replacement_id:
            superseded.append({"record": copy.deepcopy(item), "superseded_by": replacement_id, "superseded_at": iso(now), "reason": f"The maintained {replacement_kind} now provides this source; the prior record is retained here for provenance."})
            transferred.append(item_id)
            del old[item_id]
    items = copy.deepcopy(old)
    refs = [r for r in configured_refs if not superseded_by_base(r)]
    changes = {"added": [], "updated": [], "flagged": [], "superseded": transferred, "rejected": {}}
    for raw in refs:
        item = copy.deepcopy(raw)
        item["origin"] = "curated_reference"
        item.setdefault("review_status", "source_inspected")
        predecessor = previous_ids.get(item.get("id")) or previous_dois.get(item_doi(item)) or previous_urls.get(item_url(item))
        if predecessor:
            item["added_at"] = predecessor["added_at"]
        else:
            item.setdefault("added_at", iso(now))
        if item.get("review_status") == "source_inspected":
            age = (now - timestamp(item.get("verification", {}).get("checked_at"))).days
            if age > config.get("curated_review_after_days", 90):
                item["review_status"] = "needs_review"
                item["review_note"] = "The recorded source inspection is older than the configured review interval."
        validate_item(item)
        items[item["id"]] = item
        if predecessor is None:
            changes["added"].append(item["id"])
        elif item != predecessor:
            changes["updated"].append(item["id"])
    # Removing a configured reference does not silently erase a published source.
    current_ref_ids = {i["id"] for i in refs}
    for item in items.values():
        if item["origin"] == "curated_reference" and item["id"] not in current_ref_ids:
            item["review_status"] = "needs_review"
            item["review_note"] = "This reference is no longer in the active curation configuration; retained pending an explicit editorial decision."
    ids = {i.get("id") for i in base.get("items", [])} | set(items)
    doi_to_id = {item_doi(i): i.get("id") for i in base.get("items", []) + list(items.values()) if item_doi(i)}
    urls = {item_url(i) for i in base.get("items", []) + list(items.values()) if item_url(i)}
    quota_records = list(items.values()) + [r["record"] for r in superseded]
    added_today = list({i["id"]: i for i in quota_records if i.get("origin") == "crossref" and service_day(i["added_at"]) == day}.values())
    used_total = len(added_today)
    source_runs = []
    prior_runs = {r["id"]: r for r in previous.get("source_runs", [])}
    sources = {s["id"]: s for s in config["sources"]}
    pending = {i["id"]: copy.deepcopy(i) for i in previous.get("pending", []) if i["id"] not in ids and item_doi(i) not in doi_to_id and item_url(i) not in urls}
    coverage = copy.deepcopy(previous.get("coverage", {"sources": {}}))
    coverage["mode"] = "bounded_discovery"
    coverage["notice"] = "Discovery samples a recent index-date window and a rotating bounded page of historical publication years. It is not an exhaustive literature search. A full pending queue may defer additional discoveries until a later sampling cycle."
    coverage["limits"] = {"recent_index_days": config.get("recent_index_days", 30), "historical_minimum_year": config["minimum_year"], "historical_max_offset": config.get("backfill_max_offset", 400), "discovery_requests_per_refresh": len(config["sources"]) * 2, "pending_per_topic": config.get("pending_limit_per_topic", 120)}
    coverage.setdefault("sources", {})
    chapter_usage = {}
    for item in added_today:
        if item.get("work_type") == "book-chapter" and item.get("venue"):
            key = (item.get("discovery_source_id"), item["venue"].casefold())
            chapter_usage[key] = chapter_usage.get(key, 0) + 1

    def update_existing(work, source):
        doi = normalise_doi(work.get("DOI")) if isinstance(work, dict) else ""
        existing_id = doi_to_id.get(doi)
        if not existing_id or existing_id not in items or items[existing_id]["origin"] != "crossref":
            return False
        existing = items[existing_id]
        existing["last_metadata_attempt"] = iso(now)
        # A broad query may return a known record from another collection. Its
        # original admission rules, not this incidental query, govern updates.
        matching_source = source
        source = sources.get(existing.get("discovery_source_id"), source)
        flag = update_flag(work)
        if flag:
            existing["review_status"] = "needs_review"
            existing["review_note"] = flag
            existing["maturity"] = "Publisher update requires review"
            existing["last_metadata_check"] = iso(now)
            existing["verification"]["checked_at"] = iso(now)
            existing["verification"]["scope"] = "Registry update relationship detected. The existing bibliographic record is retained and flagged pending substantive review."
            changes["flagged"].append(existing_id)
            return True
        replacement, reason = normalise_work(work, source, now, config["minimum_year"])
        if replacement is None:
            existing["review_status"] = "needs_review"
            existing["review_note"] = "Fresh registry metadata did not pass the admission checks: " + reason
            changes["flagged"].append(existing_id)
            return True
        replacement["added_at"] = existing["added_at"]
        replacement["last_metadata_attempt"] = iso(now)
        if existing.get("discovered_at"):
            replacement["discovered_at"] = existing["discovered_at"]
        for key in ("last_update_notice_check", "update_notice_url"):
            if key in existing:
                replacement[key] = existing[key]
        replacement["discovery_source_id"] = existing.get("discovery_source_id", source["id"])
        replacement["topics"] = sorted(set(existing.get("topics", []) + replacement["topics"]))
        if matching_source["id"] != source["id"] and relevance(work, matching_source):
            replacement["topics"] = sorted(set(replacement["topics"] + [matching_source["label"]]))
        if existing.get("review_status") == "needs_review":
            replacement["review_status"] = "needs_review"
            replacement["review_note"] = existing.get("review_note", "An earlier update flag awaits editorial resolution.")
        if replacement["metadata_sha256"] != existing.get("metadata_sha256"):
            changes["updated"].append(existing_id)
        items[existing_id] = replacement
        return True

    notice_targets = set()

    def propagate_notice(work):
        if not isinstance(work, dict) or not update_flag(work):
            return
        for update in work.get("update-to", []) if isinstance(work.get("update-to", []), list) else []:
            if not isinstance(update, dict) or not any(t in str(update.get("type", "")).lower() for t in ("retract", "withdraw", "correct", "errat")):
                continue
            target_doi = normalise_doi(update.get("DOI"))
            if not target_doi:
                continue
            notice_targets.add(target_doi)
            target = items.get(doi_to_id.get(target_doi)) or next((p for p in pending.values() if item_doi(p) == target_doi), None)
            if target and target.get("origin") == "crossref":
                target["review_status"] = "needs_review"
                target["review_note"] = "A separately retrieved publisher notice reports an update, correction, withdrawal or retraction of this DOI."
                target["last_update_notice_check"] = iso(now)
                notice_doi = normalise_doi(work.get("DOI"))
                if notice_doi:
                    target["update_notice_url"] = doi_url(notice_doi)
                changes["flagged"].append(target["id"])

    # Inspect notice relationships before admission, so a later source response
    # can prevent a new original from being admitted earlier in this same run.
    if not curated_only:
        for result in responses.values():
            for work in result.get("items", []):
                propagate_notice(work)
        for result in (rechecks or {}).values():
            propagate_notice(result.get("item"))

    for source in ([] if curated_only else config["sources"]):
        result = responses.get(source["id"], {"error": "No response supplied"})
        source_status = result.get("status", "failed" if result.get("error") else "ok")
        receipt = {"id": source["id"], "label": source["label"], "checked_at": iso(now), "url": result.get("url", source_url(source, config, now)), "status": source_status, "discovered": 0, "accepted": 0, "rejected": {}, "daily_limit": source["daily_limit"]}
        if result.get("queries"):
            receipt["queries"] = copy.deepcopy(result["queries"])
        if result.get("error"):
            receipt["error"] = clean_text(result["error"], 600)
        receipt["last_successful_check"] = iso(now) if source_status == "ok" else prior_runs.get(source["id"], {}).get("last_successful_check")
        position = result.get("backfill_position_after")
        if position is not None:
            coverage["sources"][source["id"]] = {**position, "last_advanced_at": iso(now)}
        elif source["id"] not in coverage["sources"]:
            coverage["sources"][source["id"]] = backfill_position(source, config, previous, now)
        if result.get("response_sha256"):
            receipt["response_sha256"] = result["response_sha256"]
        for work in result.get("items", []):
            receipt["discovered"] += 1
            if update_existing(work, source):
                continue
            raw_doi = normalise_doi(work.get("DOI")) if isinstance(work, dict) else ""
            if raw_doi and raw_doi in notice_targets:
                receipt["rejected"]["update_notice"] = receipt["rejected"].get("update_notice", 0) + 1
                continue
            existing_pending = next((p for p in pending.values() if item_doi(p) == raw_doi), None)
            if existing_pending and update_flag(work):
                existing_pending["review_status"] = "needs_review"
                existing_pending["review_note"] = update_flag(work)
                continue
            item, reason = normalise_work(work, source, now, config["minimum_year"])
            if reason:
                receipt["rejected"][reason] = receipt["rejected"].get(reason, 0) + 1
                continue
            doi, url = item_doi(item), item_url(item)
            if item["id"] in ids or doi in doi_to_id or url in urls:
                receipt["rejected"]["duplicate"] = receipt["rejected"].get("duplicate", 0) + 1
                continue
            if existing_pending:
                if existing_pending.get("discovery_source_id") == source["id"]:
                    item["discovered_at"] = existing_pending.get("discovered_at", existing_pending["added_at"])
                    item["added_at"] = existing_pending["added_at"]
                    if existing_pending["review_status"] == "needs_review":
                        item["review_status"] = "needs_review"
                        item["review_note"] = existing_pending.get("review_note")
                    pending[item["id"]] = item
                receipt["rejected"]["duplicate"] = receipt["rejected"].get("duplicate", 0) + 1
                continue
            item["discovered_at"] = iso(now)
            pending[item["id"]] = item
        candidates = [i for i in pending.values() if i.get("discovery_source_id") == source["id"]]
        candidates.sort(key=lambda i: (i.get("discovered_at", i["added_at"]), -int(i["publication_date"].replace("-", "").ljust(8, "0")), i["doi"]))
        used_source = sum(i.get("discovery_source_id") == source["id"] for i in added_today)
        for item in candidates:
            doi, url = item_doi(item), item_url(item)
            if item["review_status"] == "needs_review":
                continue
            if used_total >= config["daily_limit"] or used_source >= source["daily_limit"]:
                receipt["queued_by_daily_limit"] = receipt.get("queued_by_daily_limit", 0) + 1
                continue
            chapter_key = (source["id"], item.get("venue", "").casefold())
            if item.get("work_type") == "book-chapter" and item.get("venue") and chapter_usage.get(chapter_key, 0) >= config.get("chapter_limit_per_venue_per_day", 1):
                receipt["queued_for_container_diversity"] = receipt.get("queued_for_container_diversity", 0) + 1
                continue
            item["added_at"] = iso(now)
            items[item["id"]] = item
            del pending[item["id"]]
            ids.add(item["id"])
            doi_to_id[doi] = item["id"]
            urls.add(url)
            if item.get("work_type") == "book-chapter" and item.get("venue"):
                chapter_usage[chapter_key] = chapter_usage.get(chapter_key, 0) + 1
            used_source += 1
            used_total += 1
            receipt["accepted"] += 1
            changes["added"].append(item["id"])
        queued = sorted((i for i in pending.values() if i.get("discovery_source_id") == source["id"]), key=lambda i: (i.get("discovered_at", i["added_at"]), i["id"]))
        overflow = queued[config.get("pending_limit_per_topic", 120):]
        for item in overflow:
            del pending[item["id"]]
        receipt["pending_limit"] = config.get("pending_limit_per_topic", 120)
        receipt["pending_count"] = len(queued) - len(overflow)
        receipt["pending_overflow"] = len(overflow)
        for reason, count in receipt["rejected"].items():
            changes["rejected"][reason] = changes["rejected"].get(reason, 0) + count
        source_runs.append(receipt)

    if rechecks and not curated_only:
        failed = 0
        for doi, result in rechecks.items():
            existing = items.get(doi_to_id.get(doi))
            if not existing:
                continue
            existing["last_metadata_attempt"] = iso(now)
            if result.get("error"):
                failed += 1
                continue
            source = sources.get(existing.get("discovery_source_id"), config["sources"][0])
            update_existing(result.get("item", {}), source)
        source_runs.append({"id": "known-record-rechecks", "label": "Previously indexed records", "status": "ok" if not failed else "degraded" if failed < len(rechecks) else "failed", "checked_at": iso(now), "discovered": len(rechecks), "accepted": 0, "failed_checks": failed, "error": f"{failed} record checks failed; earlier records and inspection dates were retained." if failed else None})
    if curated_only:
        source_runs = copy.deepcopy(previous.get("source_runs", []))
    statuses = [r["status"] for r in source_runs]
    status = "ok" if all(s == "ok" for s in statuses) else "failed" if all(s == "failed" for s in statuses) else "degraded"
    result = {
        "schema_version": 1,
        "generated_at": iso(now),
        "refresh_mode": "curated_only" if curated_only else "network",
        "service_day": day,
        "last_successful_refresh": iso(now) if status == "ok" and not curated_only else previous.get("last_successful_refresh"),
        "status": status,
        "scope_note": "Curated source references and automatically indexed publisher metadata have different review levels. Discovery does not verify article contents, legal currency, free access or independent usefulness.",
        "source_runs": source_runs,
        "coverage": coverage,
        "pending": sorted(pending.values(), key=lambda i: (i.get("discovered_at", i["added_at"]), i["id"])),
        "superseded_records": superseded,
        "items": sorted(items.values(), key=lambda i: (i["added_at"], i["id"]), reverse=True),
        "changes": {k: sorted(set(v)) if isinstance(v, list) else v for k, v in changes.items()},
        "stats": {"total": len(items), "curated_references": sum(i["origin"] == "curated_reference" for i in items.values()), "metadata_records": sum(i["origin"] == "crossref" for i in items.values()), "needs_review": sum(i["review_status"] == "needs_review" for i in items.values()), "added_this_run": len(set(changes["added"])), "new_metadata_today": used_total, "pending": len(pending), "pending_overflow_this_run": sum(r.get("pending_overflow", 0) for r in source_runs) if not curated_only else 0, "superseded_records": len(superseded)},
    }
    if run_url and safe_url(run_url):
        result["workflow_url"] = run_url
    validate_library(result, base)
    return result


def review_queue(library):
    pending_ids = {i["id"] for i in library.get("pending", [])}
    return {"schema_version": 1, "generated_at": library["generated_at"], "scope": "Editorial work queue. Inclusion does not imply the full text was accessed or reviewed.", "items": [{"id": i["id"], "title": i["title"], "doi": item_doi(i) or None, "topics": i["topics"], "review_status": i["review_status"], "publication_state": "pending_admission" if i["id"] in pending_ids else "published_index", "source_url": i["verification"]["source_url"], "publication_date": i.get("publication_date"), "next_action": "Inspect the source and any update notice; record a bounded use case, exact supporting location, limitations and an actual review date before promoting the review level."} for i in library["items"] + library.get("pending", []) if i["review_status"] in {"metadata_only", "needs_review"}]}


def atomic_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as stream:
        stream.write(body)
        temporary = Path(stream.name)
    temporary.replace(path)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--refresh", action="store_true", help="Fetch bounded Crossref metadata and write a checked snapshot")
    mode.add_argument("--curated-only", action="store_true", help="Rebuild curator changes offline while preserving actual network-check timestamps")
    mode.add_argument("--check", action="store_true", help="Validate the existing public snapshot without networking")
    mode.add_argument("--offline-validate", action="store_true", help="Alias for --check")
    parser.add_argument("--config", type=Path, default=ROOT / "config/library_sources.json")
    parser.add_argument("--references", type=Path, default=ROOT / "config/library_references.json")
    parser.add_argument("--catalog", type=Path, default=ROOT / "site/lab/data/catalog.json")
    parser.add_argument("--output", type=Path, default=ROOT / "site/lab/data/library.json")
    parser.add_argument("--now", help="Explicit timezone-aware time for reproducible offline tests")
    args = parser.parse_args(argv)
    try:
        config = load_json(args.config)
        validate_config(config)
        base = load_json(args.catalog)
        if args.check or args.offline_validate:
            library = load_json(args.output)
            validate_library(library, base)
            print(json.dumps({"status": "valid", "items": len(library["items"]), "network_requests": 0}))
            return 0
        references = load_json(args.references)
        previous = load_json(args.output, {"items": [], "source_runs": []})
        if previous.get("items"):
            validate_library(previous)
        if args.curated_only and not previous.get("schema_version"):
            raise ValidationError("A curator-only rebuild requires a previous checked snapshot")
        now = timestamp(args.now) if args.now else dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
        responses, rechecks = ({}, {}) if args.curated_only else get_responses(config, previous, now)
        run_id = os.environ.get("GITHUB_RUN_ID", "")
        run_url = "https://github.com/Albertito-AI/Albertito-AI/actions/runs/" + run_id if run_id.isdigit() else None
        library = build_library(config, references, base, previous, responses, now, rechecks, run_url, args.curated_only)
        queue = review_queue(library)
        history_path = args.output.with_name("library-history.json")
        history = load_json(history_path, {"schema_version": 1, "runs": []})
        entry = {"checked_at": library["generated_at"], "status": library["status"], "changes": library["changes"], "total": library["stats"]["total"], "workflow_url": run_url}
        runs = [r for r in history.get("runs", []) if r.get("checked_at") != entry["checked_at"]]
        history["runs"] = (runs + [entry])[-365:]
        # All documents are prepared and validated before any public snapshot changes.
        atomic_json(args.output, library)
        atomic_json(args.output.with_name("library-review-queue.json"), queue)
        atomic_json(history_path, history)
        print(json.dumps({"status": library["status"], **library["stats"], "source_statuses": {r["id"]: r["status"] for r in library["source_runs"]}}))
        if library["status"] != "ok":
            print("Some source checks failed. Previously indexed records were retained; inspect source_runs before claiming freshness.", file=sys.stderr)
        # Nonzero only for malformed state. A valid degraded health receipt should
        # still be published, with the external failure visible in its own fields.
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        print("Library refresh failed before publication: " + clean_text(str(error), 400), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
