"""Verify that the committed dance exports actually play on GitHub."""
from pathlib import Path
import argparse
import hashlib
import io
import json
import re
import tempfile

from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright

ROOT = Path.cwd()
parser = argparse.ArgumentParser()
parser.add_argument("--public", action="store_true")
args = parser.parse_args()
manifest = json.loads((ROOT / "assets/sparks-dance-manifest.json").read_text())
assert manifest["source_sha256"] == hashlib.sha256((ROOT / manifest["source"]).read_bytes()).hexdigest()
gif_path = ROOT / "assets/sparks-dance.gif"
assert gif_path.stat().st_size <= 4 * 1024 * 1024
assert hashlib.sha256(gif_path.read_bytes()).hexdigest() == manifest["gif"]["sha256"]
with Image.open(gif_path) as gif:
    assert gif.format == "GIF" and gif.is_animated
    assert gif.size == tuple(manifest["dimensions"])
    assert gif.n_frames == manifest["gif"]["frames"] and gif.n_frames >= 120
    assert gif.info.get("loop") == 0
    first = gif.convert("RGB").copy()
    different, duration = False, 0
    for index in range(gif.n_frames):
        gif.seek(index)
        assert gif.info.get("duration", 0) > 0
        duration += gif.info["duration"]
        if ImageChops.difference(first, gif.convert("RGB")).getbbox():
            different = True
    assert different and duration == 18000
with Image.open(ROOT / "assets/sparks-dance-still.png") as still:
    assert still.format == "PNG" and still.size == tuple(manifest["dimensions"])
assert (ROOT / "assets/sparks-dance.mp4").stat().st_size == manifest["video"]["bytes"]
print("PASS: Real animated GIF, distinct decoded frames, 18-second loop, matching still, source checksum and size budget.")

readme = (ROOT / "README.md").read_text()
picture = re.search(r'<picture>\s*<source[^>]+sparks-dance-still[^>]+>\s*<img[^>]+sparks-dance\.gif[^>]+>\s*</picture>', readme).group(0)
stage_url = re.search(r'\*\*\[Open the interactive stage\]\((https://[^)]+)\)', readme).group(1)
assert stage_url == "https://albertito-ai.github.io/Albertito-AI/", stage_url
selector = 'img[alt^="Sparks dancing through six routines"]'

def check_picture(page, url, reduced):
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    photo = page.locator(selector).first
    preview = page.locator("summary").filter(has_text="Open Sparks' care controls and dance preview")
    if preview.count() and not photo.is_visible():
        preview.click()
    photo.wait_for(timeout=30000)
    photo.scroll_into_view_if_needed()
    page.wait_for_function("(e) => e.complete && e.naturalWidth === 304", arg=photo.element_handle(), timeout=60000)
    current = photo.evaluate("(e) => e.currentSrc")
    assert ("sparks-dance-still.png" if reduced else "sparks-dance.gif") in current, current
    a = Image.open(io.BytesIO(photo.screenshot(animations="allow"))).convert("RGB")
    differences = []
    for _ in range(3):
        page.wait_for_timeout(350)
        b = Image.open(io.BytesIO(photo.screenshot(animations="allow"))).convert("RGB")
        differences.append(ImageChops.difference(a, b).getbbox() is not None)
    assert not any(differences) if reduced else any(differences), (current, differences)
    page.set_viewport_size({"width": 375, "height": 900})
    photo.scroll_into_view_if_needed()
    dimensions = photo.bounding_box()
    assert dimensions["width"] <= 375
    assert abs(dimensions["height"] - dimensions["width"] * 540 / 304) < 2
    print("PASS:", "public profile" if url.startswith("https:") else "README picture",
          "still" if reduced else "animated", current)

with tempfile.TemporaryDirectory() as temp, sync_playwright() as pw:
    directory = Path(temp)
    local_picture = picture.replace("assets/", (ROOT / "assets").as_uri() + "/")
    wrapper = directory / "profile.html"
    wrapper.write_text('<!doctype html><meta name="viewport" content="width=device-width"><style>body{margin:16px}img{max-width:100%;height:auto}</style>' + local_picture)
    browser = pw.chromium.launch()
    for reduced in (False, True):
        context = browser.new_context(viewport={"width": 1200, "height": 1000},
                                      reduced_motion="reduce" if reduced else "no-preference")
        page = context.new_page()
        check_picture(page, wrapper.as_uri(), reduced)
        context.close()
    video = directory / "video.html"
    video.write_text('<video controls muted src="' + (ROOT / "assets/sparks-dance.mp4").as_uri() + '"></video>')
    page = browser.new_page()
    page.goto(video.as_uri())
    page.wait_for_function("document.querySelector('video').readyState >= 2")
    duration = page.locator("video").evaluate("(v) => v.duration")
    assert abs(duration - manifest["video"]["duration_seconds"]) < 0.2
    page.locator("video").evaluate("(v) => v.play()")
    page.wait_for_function("document.querySelector('video').currentTime > 0.2")
    print("PASS: Full MP4 decodes and plays in Chromium,", duration, "seconds.")

    external = browser.new_page(viewport={"width": 1280, "height": 900})
    errors = []
    external.on("pageerror", lambda error: errors.append(str(error)))
    external.goto(stage_url, wait_until="domcontentloaded", timeout=60000)
    external.wait_for_function("window.__spark && document.querySelectorAll('.move').length === 6", timeout=30000)
    for index in range(6):
        external.locator(".move").nth(index).click()
        assert external.evaluate("__spark.S0.idx") == index
    external.locator("#play").click()
    assert not external.evaluate("__spark.S0.playing")
    external.locator("#sound").click()
    assert external.locator("#sound").get_attribute("aria-pressed") == "true"
    external.locator("#sound").click()
    external.locator("#all").click()
    assert external.evaluate("__spark.S0.mode") == "set"
    external.set_viewport_size({"width": 375, "height": 900})
    assert external.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert not errors, errors
    print("PASS: GitHub Pages stage, six routines, pause, audio toggle, whole set and mobile layout.", external.url)

    if args.public:
        for reduced in (False, True):
            context = browser.new_context(viewport={"width": 1280, "height": 1100},
                                          reduced_motion="reduce" if reduced else "no-preference")
            check_picture(context.new_page(), "https://github.com/Albertito-AI", reduced)
            context.close()
        print("PUBLIC_DANCE_PROFILE_VERIFIED")
    browser.close()
print("All dance media checks passed.")
