"""Verify the public Research Lab entry, sharing and non-JavaScript fallback.

The legacy script filename keeps existing workflow references compatible.
"""
from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import threading
from urllib.parse import parse_qs, urlencode, urljoin, urlsplit

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = "https://albertito-ai.github.io/Albertito-AI/"


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


def require(condition, message):
    if not condition:
        raise AssertionError(message)
    print("PASS:", message, flush=True)


def check_entry(browser, entry_url):
    target = urljoin(entry_url, "lab/")
    record = json.loads((ROOT / "site/lab/data/regnav.json").read_text())
    scenario = next(item for item in record["scenarios"] if item["id"] == "watch-source-changed")
    errors = []
    context = browser.new_context(viewport={"width": 1280, "height": 900})
    page = context.new_page()
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(entry_url, wait_until="networkidle", timeout=60000)
    page.wait_for_url(re.compile(re.escape(target) + r"(?:[?#]|$)"), timeout=30000)
    page.wait_for_function("document.querySelector('#scenario-select')?.options.length > 0")
    page.wait_for_function("document.querySelector('#catalog-results')?.children.length > 0")
    expect(page.locator("#lab-app")).to_have_attribute("aria-busy", "false")
    require("Research Lab" in page.title(), "The root entry opens the Research Lab")
    require(not page.locator(".hero-sparks").count(), "The research hero contains no retired mascot")
    require(not page.get_by_role("link", name=re.compile("dance floor", re.I)).count(),
            "Research navigation does not advertise the retired Dance Floor")
    require(not re.search(r"\bSparks\b", page.locator("body").inner_text()),
            "The active Research Lab presents its useful work without mascot branding")

    parameters = {"scenario": scenario["id"], "record": record["generated_at"],
                  "private": "ENTRY_PRIVATE_SENTINEL"}
    page.goto(entry_url + "?" + urlencode(parameters) + "#replay",
              wait_until="networkidle", timeout=60000)
    page.wait_for_url(re.compile(re.escape(target) + r"\?"), timeout=30000)
    expect(page.locator("#scenario-select")).to_have_value(str(record["scenarios"].index(scenario)))
    parts = urlsplit(page.url)
    require(parse_qs(parts.query) == {"scenario": [scenario["id"]], "record": [record["generated_at"]]}
            and parts.fragment == "replay",
            "The root entry preserves a public example and drops unrelated query values")
    page.set_viewport_size({"width": 375, "height": 812})
    require(page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1"),
            "The research entry fits a mobile viewport")
    require(not errors, "The root entry and restored example produce no page errors")
    context.close()

    fallback = browser.new_context(java_script_enabled=False)
    fallback_page = fallback.new_page()
    fallback_page.goto(entry_url, wait_until="networkidle", timeout=60000)
    links = [link for link in fallback_page.get_by_role("link").all()
             if urljoin(entry_url, link.get_attribute("href") or "") == target]
    require(bool(links), "The root entry has an ordinary Research Lab link without JavaScript")
    links[0].click()
    fallback_page.wait_for_url(target, timeout=30000)
    require("Research Lab" in fallback_page.title(), "The fallback link opens the Research Lab")
    require(fallback_page.get_by_role("link", name="profile repository", exact=True).is_visible(),
            "The Lab retains an accessible source route without JavaScript")
    fallback.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", help="Verify the canonical published root instead of local files")
    args = parser.parse_args()
    if args.url and args.url != CANONICAL:
        raise SystemExit("Published entry checks require the canonical GitHub Pages root.")
    readme = (ROOT / "README.md").read_text()
    require(not re.search(r"\bSparks\b", readme), "The main profile has no active mascot promotion")
    require("https://www.youtube.com/@chanxinghong" in readme
            and "https://albertito-ai.github.io/Albertito-AI/lab/" in readme,
            "The profile retains its YouTube and Research Lab destinations")
    server = None
    if args.url:
        entry_url = args.url
    else:
        server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(ROOT / "site")))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        entry_url = f"http://127.0.0.1:{server.server_port}/"
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            try:
                check_entry(browser, entry_url)
            finally:
                browser.close()
    finally:
        if server:
            server.shutdown()
            server.server_close()
    print("PUBLIC_RESEARCH_ENTRY_VERIFIED", flush=True)


if __name__ == "__main__":
    main()
