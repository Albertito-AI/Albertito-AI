"""Exercise the lab as a visitor, locally or after GitHub Pages publication."""
from __future__ import annotations

import argparse
import base64
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import tempfile
import threading

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
        require(regnav_card.locator("a").evaluate_all("(links) => links.map(link => link.href)").count(contribution["url"]) == 1,
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
        fallback.close()
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
