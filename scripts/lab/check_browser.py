"""Exercise the lab as a visitor, locally or after GitHub Pages publication."""
from __future__ import annotations

import argparse
import base64
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import tempfile
import threading
from urllib.parse import unquote

from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[2]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


def require(condition, message):
    if not condition:
        raise AssertionError(message)
    print("PASS:", message, flush=True)


def text_values(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from text_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from text_values(item)
    elif isinstance(value, str):
        yield value


def load_ready(page, url):
    response = page.goto(url, wait_until="networkidle", timeout=60000)
    require(response is not None and response.status == 200, "Research lab responds successfully")
    page.wait_for_function(
        "() => document.querySelector('#scenario-select')?.options.length > 0",
        timeout=30000,
    )
    page.wait_for_function(
        "() => document.querySelector('#catalog-results')?.children.length > 0",
        timeout=30000,
    )
    expect(page.locator("#lab-app")).to_have_attribute("aria-busy", "false", timeout=30000)


def catalog_download(page):
    with page.expect_download(timeout=10000) as event:
        page.locator("#download-catalog-json").click()
    return json.loads(Path(event.value.path()).read_text(encoding="utf-8"))


def visible_catalog_ids(page):
    return page.locator("#catalog-results .catalog-card").evaluate_all(
        "cards => cards.map(card => card.dataset.itemId)"
    )


def expect_catalog_count(page, matched, total):
    expect(page.locator("#catalog-count")).to_have_text(
        re.compile(rf"^{matched} of {total} (?:entry|entries)(?: |\.)")
    )


def check_library_controls(page, catalog, library):
    original = {item["id"]: item for item in catalog["items"]}
    combined = dict(original)
    for item in library["items"]:
        combined.setdefault(item["id"], item)
    total = len(combined)
    require(library["schema_version"] == 1 and library["items"],
            "The additional library contains actual published source records")
    page.locator("#catalog-clear").click()
    expect_catalog_count(page, total, total)
    require("unavailable" not in page.locator("#library-health").inner_text().lower(),
            "The additional library has loaded independently of the original catalog")
    require(page.locator("#catalog-results .catalog-card").count() == min(12, total),
            "The catalog renders a bounded first page of the combined records")
    require(total > 12, "The actual combined collection exercises multiple result pages")
    first_page_ids = set(visible_catalog_ids(page))
    page.locator("#catalog-next").click()
    expect(page.locator("#catalog-results")).to_be_focused()
    require(set(visible_catalog_ids(page)) != first_page_ids,
            "Next page changes the visible records and moves keyboard focus to the results")

    exported = catalog_download(page)
    exported_by_id = {item["id"]: item for item in exported["items"]}
    require(set(exported_by_id) == set(combined)
            and len(exported["items"]) == total
            and first_page_ids <= set(exported_by_id),
            "JSON exports all matching entries, including entries outside the visible second page")
    require(exported["record_type"] == "filtered_library_metadata"
            and exported["source_snapshot"]["library_generated_at"] == library["generated_at"]
            and exported["source_snapshot"]["last_successful_refresh"] == library.get("last_successful_refresh"),
            "The export distinguishes the snapshot rebuild from its last successful refresh")
    for identifier, item in original.items():
        require(exported_by_id[identifier]["title"] == item["title"]
                and exported_by_id[identifier].get("citation") == item.get("citation"),
                "The original title and citation survive the merge: " + identifier)
    require(all("_fromLibrary" not in item for item in exported["items"]),
            "Downloaded metadata excludes internal display fields")
    with page.expect_download(timeout=10000) as bib_event:
        page.locator("#download-catalog-bibtex").click()
    bibliography = Path(bib_event.value.path()).read_text(encoding="utf-8")
    citation_keys = re.findall(r"^@\w+\{([^,\n]+),", bibliography, flags=re.MULTILINE)
    require(len(citation_keys) == total and len(set(citation_keys)) == total,
            "BibTeX exports every match with a distinct citation key across pagination")
    discoveries = [item for item in library["items"] if item.get("origin") == "crossref"]
    require(discoveries, "Published metadata discoveries exercise publication citation links")
    for item in discoveries:
        citation_key = "lab-" + re.sub(r"[^a-zA-Z0-9_-]", "-", item["id"])
        entry = next(block for block in bibliography.split("\n\n")
                     if block.startswith("@misc{" + citation_key + ",\n"))
        url_field = re.search(r"^  url = \{(.*)\},?$", entry, flags=re.MULTILINE)
        require(url_field is not None, "A discovered publication exports a citation URL: " + item["id"])
        citation_url = re.sub(r"\\([{}%&#_$])", r"\1", url_field.group(1))
        citation_url = citation_url.replace(r"\textasciitilde{}", "~").replace(r"\textasciicircum{}", "^")
        require(citation_url.startswith("https://doi.org/")
                and unquote(citation_url.removeprefix("https://doi.org/")) == item["doi"],
                "A discovered publication's BibTeX URL points to its DOI, not the registry API")

    metadata = {item["id"] for item in combined.values() if item.get("review_status") == "metadata_only"}
    inspected = {item["id"] for item in combined.values() if item.get("review_status") == "source_inspected"}
    inspected.update(item["id"] for item in catalog["items"]
                     if not item.get("review_status") and item.get("verification", {}).get("checked_at"))
    require(metadata and inspected, "The published collection has both metadata and inspected-source records")
    for review, expected_ids in (("metadata_only", metadata), ("source_inspected", inspected)):
        page.select_option("#catalog-review", review)
        expect_catalog_count(page, len(expected_ids), total)
        expect(page.locator("#catalog-page")).to_have_text(re.compile(r"^Page 1 of "))
        result = catalog_download(page)
        require({item["id"] for item in result["items"]} == expected_ids
                and all(item["review_status"] == review for item in result["items"]),
                "Review-level filtering and export retain exactly the " + review + " records")
    page.select_option("#catalog-review", "metadata_only")
    first_metadata_id = visible_catalog_ids(page)[0]
    metadata_card = page.locator(f'.catalog-card[data-item-id="{first_metadata_id}"]')
    expect(metadata_card.locator(".item-review .label")).to_have_text("Metadata only")
    metadata_card.locator("summary").click()
    selected = combined[first_metadata_id]
    expected_notice = ("recording and transcript have not been reviewed"
                       if selected.get("medium") == "video" else "full text has not been reviewed")
    require("Source inspected:" not in metadata_card.inner_text()
            and expected_notice in metadata_card.inner_text().lower(),
            "A metadata retrieval is not presented as a source or content inspection")
    require(f"{len(metadata)} metadata-only records in total" in page.locator("#library-coverage").inner_text(),
            "Coverage counts metadata-only records from both catalogues")
    require(selected.get("publisher") and selected.get("authors") and selected.get("use_for"),
            "Real discovery records supply publisher, author and intended-use metadata")
    page.locator("#catalog-clear").click()
    for term in (selected["publisher"], selected["authors"][0], selected["use_for"]):
        page.locator("#catalog-search").fill(term)
        require(first_metadata_id in {item["id"] for item in catalog_download(page)["items"]},
                "A discovery record is searchable by its publisher, author or intended use")
    page.locator("#catalog-clear").click()
    topic = selected["topics"][0]
    page.select_option("#catalog-topic", topic)
    expected_topic = {identifier for identifier, item in combined.items() if topic in item.get("topics", [])}
    expect_catalog_count(page, len(expected_topic), total)
    require({item["id"] for item in catalog_download(page)["items"]} == expected_topic,
            "The topic selector filters the actual source topics across both catalogs")
    page.locator("#catalog-clear").click()
    page.select_option("#catalog-type", "reference")
    expected_references = {identifier for identifier, item in combined.items() if item.get("type") == "reference"}
    expect_catalog_count(page, len(expected_references), total)
    require(expected_references and {item["id"] for item in catalog_download(page)["items"]} == expected_references,
            "References can be selected independently of projects and research publications")
    page.locator("#catalog-clear").click()
    page.select_option("#catalog-sort", "title")
    require(page.locator("#catalog-results h3").evaluate_all("""headings => {
        const titles = headings.map(heading => heading.textContent);
        return titles.every((title, index) => index === 0 ||
            titles[index - 1].localeCompare(title, 'en', {sensitivity: 'base'}) <= 0);
    }"""), "Title ordering works on the visitor's visible results")
    page.select_option("#catalog-sort", "publication")
    dated = [item for item in combined.values() if item.get("publication_date")]
    most_recent_publication = max(item["publication_date"] for item in dated)
    require(combined[visible_catalog_ids(page)[0]].get("publication_date") == most_recent_publication,
            "Publication ordering starts with the latest recorded publication date")
    page.select_option("#catalog-sort", "recent")
    page.locator("#catalog-clear").click()
    require(page.locator('a[href$="docs/LIBRARY_READING_PATHS.md"]').count() == 1
            and page.locator('a[href$="docs/LIBRARY_WORKFLOW.md"]').count() == 1
            and page.locator('a[href$="template=library-source.yml"]').count() == 1,
            "Reading paths, maintenance evidence and source suggestions are discoverable")


def check_library_recovery(browser, url, catalog, library):
    original_ids = {item["id"] for item in catalog["items"]}
    combined_ids = original_ids | {item["id"] for item in library["items"]}
    recovery = browser.new_context(accept_downloads=True)
    recovery_page = recovery.new_page()
    errors = []
    recovery_page.on("pageerror", lambda error: errors.append(str(error)))
    recovery_page.route("**/data/library.json*", lambda route: route.fulfill(
        status=503, content_type="application/json", body='{"error":"fixture-unavailable"}'))
    load_ready(recovery_page, url)
    expect_catalog_count(recovery_page, len(original_ids), len(original_ids))
    require(set(visible_catalog_ids(recovery_page)) <= original_ids
            and len(visible_catalog_ids(recovery_page)) == min(12, len(original_ids))
            and {item["id"] for item in catalog_download(recovery_page)["items"]} == original_ids,
            "A failed library request preserves every original catalog entry")
    require("unavailable" in recovery_page.locator("#library-health").inner_text().lower()
            and "could not be loaded" in recovery_page.locator("#library-status-message").inner_text().lower(),
            "A failed request has a visible recovery explanation and cannot claim a successful update")
    expect(recovery_page.locator("#retry-library")).to_be_visible()
    recovery_page.unroute("**/data/library.json*")
    recovery_page.locator("#retry-library").click()
    expect(recovery_page.locator("#library-retry")).to_be_hidden(timeout=30000)
    expect_catalog_count(recovery_page, len(combined_ids), len(combined_ids))
    require({item["id"] for item in catalog_download(recovery_page)["items"]} == combined_ids,
            "Retry restores the complete merged library after the source record becomes available")
    require(not errors, "Library failure and recovery cause no uncaught JavaScript errors")
    recovery.close()

    stale = deepcopy(library)
    now = datetime.now(timezone.utc)
    stale["generated_at"] = now.isoformat(timespec="seconds").replace("+00:00", "Z")
    stale["last_successful_refresh"] = (now - timedelta(hours=72)).isoformat(timespec="seconds").replace("+00:00", "Z")
    stale["status"] = "ok"
    stale["refresh_mode"] = "curated_only"
    require(stale.get("source_runs"), "The offline-rebuild fixture retains actual source-check records")
    for index, source in enumerate(stale["source_runs"]):
        source["checked_at"] = (now - timedelta(hours=96 + index)).isoformat(timespec="seconds").replace("+00:00", "Z")
    stale["source_runs"][-1]["checked_at"] = stale["last_successful_refresh"]
    stale_context = browser.new_context()
    stale_page = stale_context.new_page()
    stale_page.route("**/data/library.json*", lambda route: route.fulfill(
        status=200, content_type="application/json", body=json.dumps(stale)))
    load_ready(stale_page, url)
    expect(stale_page.locator("#library-health")).to_have_attribute("data-state", "stale")
    require("overdue" in stale_page.locator("#library-health").inner_text().lower()
            and "48 hours" in stale_page.locator("#library-status-message").inner_text(),
            "A saved ok status cannot mask a source refresh older than 48 hours")
    attempt = stale_page.locator("#library-refresh-dates > div").filter(has_text="Latest source-update attempt").locator("dd").inner_text()
    success = stale_page.locator("#library-refresh-dates > div").filter(has_text="Latest successful source update").locator("dd").inner_text()
    rebuilt = stale_page.locator("#library-refresh-dates > div").filter(has_text="Snapshot rebuilt").locator("dd").inner_text()
    require(attempt == success and attempt != rebuilt and "Not recorded" not in (attempt, success, rebuilt),
            "An offline snapshot rebuild preserves the latest actual source-check date and older success date")
    expect_catalog_count(stale_page, len(combined_ids), len(combined_ids))
    stale_context.close()


def check(url):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context(viewport={"width": 1280, "height": 900}, accept_downloads=True)
        page = context.new_page()
        errors = []
        writes = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("request", lambda request: writes.append(request.url) if request.method not in ("GET", "HEAD") else None)
        try:
            load_ready(page, url)
        except Exception:
            print("LAB_FAILURE_PNG=" + base64.b64encode(page.screenshot()).decode("ascii"), flush=True)
            raise
        print("LAB_INITIAL_PNG=" + base64.b64encode(page.screenshot()).decode("ascii"), flush=True)
        data = page.evaluate("async () => (await fetch('./data/regnav.json')).json()")
        catalog = page.evaluate("async () => (await fetch('./data/catalog.json')).json()")
        library = page.evaluate("async () => (await fetch('./data/library.json')).json()")
        require(data["schema_version"] == 1 and data["receipts"] and data["scenarios"],
                "The interface loads a real structured execution record")
        require(len({scenario["id"] for scenario in data["scenarios"]}) == len(data["scenarios"]),
                "Recorded scenarios have distinct stable identities")
        for receipt in data["receipts"]:
            require(receipt["exit_code"] == receipt["expected_exit_code"],
                    "Recorded CLI exit status matches its stated expectation: " + receipt["id"])
        require({item["type"] for item in catalog["items"]} >= {"project", "research", "teaching"},
                "The catalogue connects projects, research and teaching")
        require("record" in page.locator("#replay .section-intro").inner_text().lower(),
                "The visitor is told that the exercise shows recorded execution")
        require(page.locator("#scenario-select option").count() == len(data["scenarios"]),
                "Every recorded scenario can be selected")

        evidence_views = set()
        for index, scenario in enumerate(data["scenarios"]):
            page.select_option("#scenario-select", str(index))
            expect(page.locator("#claims-list")).not_to_be_empty()
            for tab in ("before", "after", "review"):
                button = page.locator(f'#evidence-tabs [data-tab="{tab}"]')
                button.click()
                text = page.locator("#evidence-panel").inner_text().strip()
                require(len(text) > 30, f"{scenario['id']}: {tab} view contains an explanation")
                evidence_views.add(text)
        require(len(evidence_views) > len(data["scenarios"]),
                "Scenario choices expose materially different evidence and explanations")

        scenario_indexes = {item["id"]: str(index) for index, item in enumerate(data["scenarios"])}

        def choose_claim(scenario_id, claim_id):
            page.select_option("#scenario-select", scenario_indexes[scenario_id])
            page.locator('#evidence-tabs [data-tab="before"]').click()
            page.locator(f'.claim-button[data-claim-id="{claim_id}"]').click()

        choose_claim("irrelevant-pinpoint", "CLAIM-remedy")
        require("B.2" not in page.locator("#source-select option:checked").inner_text()
                and "No quoted passage is recorded" in page.locator(".source-quote blockquote").inner_text(),
                "Before the pinpoint edit, the selected claim has no invented passage")
        page.locator("#tab-after").click()
        require("B.2" in page.locator("#source-select option:checked").inner_text(),
                "After the pinpoint edit, the selected claim identifies B.2")
        expect(page.locator(".source-quote blockquote")).to_have_text("The reviewer responds within ten working days.")
        page.locator("#tab-before").click()
        require("B.2" not in page.locator("#source-select option:checked").inner_text()
                and "No quoted passage is recorded" in page.locator(".source-quote blockquote").inner_text(),
                "Returning to Before restores the missing pinpoint")

        choose_claim("invalid-source", "CLAIM-remedy")
        original_source = next(item["url"] for item in data["source_packet"]["sources"] if item["id"] == "SRC-draft-b")
        require("SRC-not-recorded" not in page.locator("#source-select option:checked").inner_text()
                and page.locator(".source-quote a").first.get_attribute("href") == original_source,
                "Before an invalid reference, the selected source still resolves to Draft B")
        page.locator("#tab-after").click()
        require("SRC-not-recorded" in page.locator("#source-select option:checked").inner_text()
                and "No quoted passage is recorded" in page.locator(".source-quote blockquote").inner_text()
                and page.locator(".source-quote a").count() == 0,
                "The invalid source remains unresolved in After without a borrowed quote or link")
        page.locator("#tab-before").click()
        require(page.locator(".source-quote a").first.get_attribute("href") == original_source,
                "Returning to Before restores the valid source reference")

        amendment = "Fictional amendment: the review target is now five days."
        for scenario_id in ("watch-source-changed", "watch-review-edited"):
            current = next(item for item in data["scenarios"] if item["id"] == scenario_id)
            old_claim = next(item for item in current["input"]["base_manifest"]["claims"] if item["id"] == "claim-routine")
            new_claim = next(item for item in current["input"]["manifest"]["claims"] if item["id"] == "claim-routine")
            choose_claim(scenario_id, "claim-routine")
            before_notes = "\n".join(page.locator("#evidence-panel > .claim-review-note").all_text_contents())
            require(old_claim["review"]["note"] in before_notes
                    and amendment not in page.locator(".source-quote blockquote").inner_text(),
                    scenario_id + ": Before retains the original source and review declaration")
            page.locator("#tab-after").click()
            after_notes = "\n".join(page.locator("#evidence-panel > .claim-review-note").all_text_contents())
            require(new_claim["review"]["note"] in after_notes
                    and amendment in page.locator(".source-quote blockquote").inner_text(),
                    scenario_id + ": After shows the actual amended fictional bytes and its declaration")
            require(page.locator(".source-quote").get_by_role("link", name="Original source context ↗", exact=True).count() == 1
                    and page.locator(".source-quote").get_by_role("link", name="Inspect the source at its recorded revision ↗", exact=True).count() == 0,
                    "Amended fictional text does not claim to be the unchanged upstream source")
            page.select_option("#source-select", "1")
            specialist = page.locator(".source-quote blockquote").inner_text()
            require("fourteen-day" in specialist and amendment not in specialist,
                    "The qualifying specialist source retains its own unchanged text")
            page.locator("#tab-before").click()
            expect(page.locator("#source-select")).to_have_value("0")
            require(amendment not in page.locator(".source-quote blockquote").inner_text()
                    and old_claim["review"]["note"] in "\n".join(page.locator("#evidence-panel > .claim-review-note").all_text_contents()),
                    "Changing tabs restores the correct original source and review note")

        first = "0"
        page.select_option("#scenario-select", first)
        page.locator('#evidence-tabs [data-tab="before"]').click()
        page.locator('.claim-button[data-claim-id="CLAIM-timing"]').click()
        require(page.locator("#source-select option").count() == 2,
                "The contested claim retains its two contrary source passages")
        if page.locator("#source-select option").count() > 1:
            choices = page.locator("#source-select option").evaluate_all("(items) => items.map(item => item.value)")
            source_views = set()
            for choice in choices:
                page.select_option("#source-select", choice)
                source_views.add(page.locator("#evidence-panel").inner_text())
            require(len(source_views) > 1, "Visitors can inspect distinct source records")

        for tab in ("before", "after"):
            page.locator(f'#evidence-tabs [data-tab="{tab}"]').click()
            page.select_option("#source-select", "1")
            expect(page.locator(".source-quote blockquote")).to_have_text("The reviewer responds within ten working days.")
            require("Recorded relation: contradicts" in page.locator(".source-quote figcaption").inner_text(),
                    "Contrary evidence keeps its actual passage and relation in " + tab)

        page.locator(".claim-button").first.click()
        page.locator('#evidence-tabs [data-tab="review"]').click()
        note = "<script>window.__lab_test=true</script> A visitor practice observation."
        page.locator("#review-note").fill(note)
        with page.expect_download(timeout=10000) as download_event:
            page.locator("#download-review").click()
        download = download_event.value
        exported = json.loads(Path(download.path()).read_text(encoding="utf-8"))
        require(note in list(text_values(exported)), "Downloaded annotation preserves the visitor's exact note")
        require(exported["record_type"] == "local_reviewer_annotations"
                and exported["recorded_dataset"]["generated_at"] == data["generated_at"],
                "Export identifies visitor annotations and the exact recorded dataset")
        require(page.evaluate("() => window.__lab_test !== true"), "Practice notes are rendered as text")
        page.reload(wait_until="networkidle")
        page.wait_for_function("() => document.querySelector('#scenario-select')?.options.length > 0")
        page.select_option("#scenario-select", first)
        page.locator('#evidence-tabs [data-tab="review"]').click()
        expect(page.locator("#review-note")).to_have_value(note)
        require(True, "A practice note survives reload for its recorded scenario and claim")
        if len(data["scenarios"]) > 1:
            page.select_option("#scenario-select", "1")
            page.locator('#evidence-tabs [data-tab="review"]').click()
            require(page.locator("#review-note").input_value() != note,
                    "A note is not silently attributed to another scenario")

        with page.expect_download(timeout=10000) as receipt_download:
            page.locator("#download-receipts").click()
        downloaded_record = json.loads(Path(receipt_download.value.path()).read_text(encoding="utf-8"))
        require(downloaded_record == data, "Visitor notes leave every recorded receipt unchanged")
        page.select_option("#scenario-select", first)
        page.locator('#evidence-tabs [data-tab="review"]').click()
        page.locator("#clear-review").click()
        expect(page.locator("#review-note")).to_have_value("")
        expect(page.locator("#download-review")).to_be_disabled()
        require(True, "Visitors can clear their saved practice note")

        check_library_controls(page, catalog, library)

        page.locator("#catalog-search").fill("source watch")
        page.wait_for_timeout(250)
        results = page.locator("#catalog-results").inner_text()
        require("Source Watch" in results and "RegNav" in results,
                "Catalogue search locates the relevant tool")
        page.locator("#catalog-search").fill("no-such-research-item-946810")
        page.wait_for_timeout(250)
        empty_text = page.locator("#catalog-results").inner_text().lower()
        require(any(word in empty_text for word in ("no ", "nothing", "try ", "match")),
                "An empty catalogue search has a useful explanation")
        page.locator("#catalog-search").fill("")
        options = page.locator("#catalog-type option").evaluate_all("(items) => items.map(item => item.value)")
        for kind in ("project", "research", "teaching"):
            require(kind in options, "Catalogue offers the " + kind + " filter")
            page.select_option("#catalog-type", kind)
            require(page.locator("#catalog-results").inner_text().strip(),
                    "Catalogue filter displays " + kind + " content")
        page.select_option("#catalog-type", options[0])

        page.select_option("#catalog-type", "project")
        regnav = next(item for item in catalog["items"] if item["id"] == "project-regnav")
        regnav_card = page.locator('.catalog-card[data-item-id="project-regnav"]')
        regnav_card.locator("summary").click()
        require(regnav["limitation"] in regnav_card.inner_text(),
                "Project scope and its concrete limitation are inspectable")
        contribution = next(item for item in catalog["contributions"] if item["project_id"] == regnav["id"])
        require(regnav_card.get_by_role("link", name=contribution["title"] + " ↗", exact=True).get_attribute("href") == contribution["url"],
                "The catalogue exposes the project's actual contribution route")
        with page.expect_download(timeout=10000) as citation_download:
            regnav_card.get_by_role("button", name="Download citation (.txt)", exact=True).click()
        require(Path(citation_download.value.path()).read_text(encoding="utf-8") == regnav["citation"]["text"] + "\n",
                "Citation download preserves the recorded attribution and version")
        related_id = "research-sg-th-accountability"
        regnav_card.locator(f'button[data-related-item-id="{related_id}"]').click()
        expect(page.locator("#catalog-type")).to_have_value("all")
        expect(page.locator("#catalog-search")).to_have_value("")
        expect(page.locator(f'.catalog-card[data-item-id="{related_id}"]')).to_be_focused()
        require(True, "A related-research route clears incompatible filters and moves keyboard focus")
        related_page = re.match(r"Page (\d+) of (\d+)", page.locator("#catalog-page").inner_text())
        require(related_page is not None and int(related_page.group(1)) > 1,
                "Related-item navigation finds and focuses an entry beyond the first results page")

        intent_options = page.locator("#guide-intent option").evaluate_all("(items) => items.map(item => item.value)")
        require(len(intent_options) >= 3, "Sparks offers task-based guidance")
        guide_answers = set()
        for intent in intent_options:
            page.select_option("#guide-intent", intent)
            answer = page.locator("#guide-answer").inner_text().strip()
            require(len(answer) > 40, "Sparks explains the selected task")
            guide_answers.add(answer)
        require(len(guide_answers) >= 3, "Sparks' guidance changes with the visitor's intention")

        page.select_option("#guide-intent", "trace")
        quickstart = next(entry["url"] for entry in regnav["links"] if entry["kind"] == "start")
        require(quickstart in page.locator("#guide-answer a").evaluate_all("(links) => links.map(link => link.href)"),
                "The claim-tracing guide points to the recorded quickstart")
        require(page.locator('#verification-record a[href$="#reproduce-the-recorded-executions"]').count() == 1,
                "Recorded command placeholders link to complete reproduction instructions")

        feedback = page.locator("#feedback-link").get_attribute("href")
        require(feedback is not None and "template=lab-feedback.yml" in feedback
                and feedback.startswith("https://github.com/Albertito-AI/Albertito-AI/issues/new"),
                "Feedback leads to the actual public GitHub issue form")
        require(len(page.locator("#verification-record a[href]").all()) > 0,
                "Execution records link to inspectable evidence")

        inputs = page.locator("input:not([type=hidden]), select, textarea").evaluate_all(
            """elements => elements.filter(element => !(
                element.labels?.length || element.getAttribute('aria-label') ||
                element.getAttribute('aria-labelledby')
            )).map(element => element.id || element.tagName)"""
        )
        require(not inputs, "Every visitor input has an associated accessible label")
        page.locator('#evidence-tabs [data-tab="before"]').focus()
        page.keyboard.press("ArrowRight")
        expect(page.locator("#tab-after")).to_be_focused()
        expect(page.locator("#tab-after")).to_have_attribute("aria-selected", "true")
        page.keyboard.press("End")
        expect(page.locator("#tab-review")).to_be_focused()
        page.keyboard.press("Home")
        expect(page.locator("#tab-before")).to_be_focused()
        page.keyboard.press("Enter")
        require(page.locator("#evidence-panel").inner_text().strip(),
                "Evidence controls work from the keyboard")

        for width in (320, 390, 768, 1280):
            page.set_viewport_size({"width": width, "height": 900})
            page.wait_for_timeout(100)
            dimensions = page.evaluate(
                "() => ({viewport: innerWidth, content: document.documentElement.scrollWidth})"
            )
            if dimensions["content"] > dimensions["viewport"] + 1:
                offenders = page.evaluate("""() => Array.from(document.body.querySelectorAll('*'))
                    .filter(element => {
                        const rectangle = element.getBoundingClientRect();
                        return rectangle.width && (rectangle.right > innerWidth + 1 || rectangle.left < -1);
                    }).slice(0, 30).map(element => ({
                        tag: element.tagName, id: element.id, class: element.className,
                        right: element.getBoundingClientRect().right,
                        left: element.getBoundingClientRect().left,
                        text: element.textContent.trim().slice(0, 100)
                    }))""")
                print("OVERFLOW_DIAGNOSTICS=" + json.dumps({"dimensions": dimensions, "elements": offenders}), flush=True)
                print("LAB_OVERFLOW_PNG=" + base64.b64encode(page.screenshot()).decode("ascii"), flush=True)
            require(dimensions["content"] <= dimensions["viewport"] + 1,
                    f"No horizontal page overflow at {width}px")
        require(not errors, "No uncaught browser JavaScript errors: " + repr(errors))
        require(not writes, "The exercise sends no form submissions or annotation uploads")

        page.evaluate("() => localStorage.clear()")
        page.reload(wait_until="networkidle")
        page.wait_for_function("() => document.querySelector('#scenario-select')?.options.length > 0")
        page.set_viewport_size({"width": 1280, "height": 900})
        page.evaluate("() => window.scrollTo(0, 0)")
        print("LAB_DESKTOP_PNG=" + base64.b64encode(page.screenshot()).decode("ascii"), flush=True)
        page.locator("#scenario-select").scroll_into_view_if_needed()
        print("LAB_REPLAY_PNG=" + base64.b64encode(page.screenshot()).decode("ascii"), flush=True)
        page.set_viewport_size({"width": 390, "height": 844})
        page.evaluate("() => window.scrollTo(0, 0)")
        print("LAB_MOBILE_PNG=" + base64.b64encode(page.screenshot()).decode("ascii"), flush=True)

        reduced = browser.new_context(viewport={"width": 390, "height": 844}, reduced_motion="reduce")
        reduced_page = reduced.new_page()
        load_ready(reduced_page, url)
        require(reduced_page.evaluate("() => matchMedia('(prefers-reduced-motion: reduce)').matches"),
                "Reduced-motion preference is available to the lab")
        reduced_page.locator('#evidence-tabs [data-tab="after"]').click()
        require(reduced_page.locator("#evidence-panel").inner_text().strip(),
                "The exercise remains usable with reduced motion")
        reduced.close()

        fallback = browser.new_context()
        fallback_page = fallback.new_page()
        fallback_page.route("**/data/regnav.json*", lambda route: route.fulfill(
            status=503, content_type="application/json", body='{"error":"unavailable"}'))
        fallback_page.goto(url, wait_until="networkidle", timeout=60000)
        fallback_text = fallback_page.locator("body").inner_text().lower()
        require(any(word in fallback_text for word in ("unavailable", "could not", "couldn't", "unable", "retry", "cannot load")),
                "An unavailable execution record has a visible recovery explanation")
        require(fallback_page.locator('a[href^="https://github.com/Albertito-AI/"]').count() > 0,
                "Source links remain available when the record cannot load")
        fallback_page.unroute("**/data/regnav.json*")
        fallback_page.locator("#replay-status").get_by_role("button", name="Try again", exact=True).click()
        fallback_page.wait_for_function("() => document.querySelector('#scenario-select')?.options.length > 0")
        expect(fallback_page.locator("#replay-status")).to_be_hidden()
        require(fallback_page.locator("#scenario-select option").count() == len(data["scenarios"]),
                "Try again restores all scenarios after the record becomes available")
        fallback.close()
        check_library_recovery(browser, url, catalog, library)
        context.close()
        browser.close()
    print("RESEARCH_LAB_BROWSER_VERIFIED", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", help="Published lab URL; omit to serve the tracked site locally")
    args = parser.parse_args()
    if args.url:
        if not args.url.startswith("https://albertito-ai.github.io/Albertito-AI/lab/"):
            raise SystemExit("Public verification is restricted to the canonical lab URL.")
        check(args.url)
        print("PUBLIC_RESEARCH_LAB_BROWSER_VERIFIED", flush=True)
        return
    handler = partial(QuietHandler, directory=str(ROOT / "site"))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        check(f"http://127.0.0.1:{server.server_port}/lab/")
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
