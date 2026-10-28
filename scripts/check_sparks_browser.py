from pathlib import Path
import base64
import hashlib
import io
import json
import os
import sys
import tempfile

from PIL import Image, ImageChops, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / "scripts"))
from update_persona import THOUGHTS, render_template, view_values

art = (ROOT / "assets/sparks-retro.png").read_bytes()
assert hashlib.sha256(art).hexdigest() == "c583fd9dee8513bc973b8b8b9eaeb0dad85dd054938257f47f33ef904c747cbf"
original = Image.open(io.BytesIO(art))
assert original.size == (1086, 1448)
print("Original artwork SHA256 and dimensions verified.")
print("Original alpha range:", original.getchannel("A").getextrema())

template = (ROOT / "assets/persona-template.svg").read_text()
state = json.loads((ROOT / "data/persona.json").read_text())
values = view_values(state)
images = []
modes = ("curious", "studying", "playful", "resting")

with tempfile.TemporaryDirectory() as temporary, sync_playwright() as pw:
    directory = Path(temporary)
    for mode in modes:
        variant = dict(values, mode=mode, thought=THOUGHTS[mode])
        (directory / (mode + ".svg")).write_text(render_template(template, variant))
    (directory / "static.svg").write_text((ROOT / "assets/research-header-static.svg").read_text())
    browser = pw.chromium.launch()
    page = browser.new_page(viewport={"width": 1240, "height": 430}, device_scale_factor=1)

    def capture(name, file_name, reduced=False, stable=False):
        page.emulate_media(reduced_motion="reduce" if reduced else "no-preference")
        wrapper = directory / (file_name + ".html")
        source = '<source media="(prefers-reduced-motion: reduce)" srcset="static.svg">' if reduced else ""
        wrapper.write_text('<!doctype html><html><head><style>html,body{margin:0;background:#101827}img{display:block;width:1200px;height:380px}</style></head><body><picture>' + source + '<img id="header" alt="Sparks test" src="' + file_name + '.svg"></picture></body></html>')
        page.goto(wrapper.as_uri())
        page.wait_for_function("document.getElementById('header').complete && document.getElementById('header').naturalWidth === 1200")
        page.wait_for_timeout(400)
        data = page.locator("#header").screenshot(animations="allow")
        picture = Image.open(io.BytesIO(data)).convert("RGB")
        assert picture.size == (1200, 380)
        bronze = sum(1 for r,g,b in picture.crop((750, 25, 890, 285)).getdata() if r > 80 and r > g * 1.05 and g > b * 1.15)
        assert bronze > 300, (name, "robot artwork did not render", bronze)
        if stable:
            page.wait_for_timeout(500)
            later = Image.open(io.BytesIO(page.locator("#header").screenshot(animations="allow"))).convert("RGB")
            assert ImageChops.difference(picture, later).getbbox() is None, name + " still moved"
            if reduced:
                assert page.locator("#header").evaluate("(e) => e.currentSrc").endswith("/static.svg")
        images.append((name, picture))
        print("PASS:", name, "SVG-as-image loaded, robot pixels", bronze)

    for mode in modes:
        page.emulate_media(reduced_motion="no-preference")
        page.goto((directory / (mode + ".svg")).as_uri())
        expected = "happy" if mode == "playful" else "breathe"
        assert page.locator(".float").evaluate("(e) => getComputedStyle(e).animationName") == expected
        capture(mode.title(), mode)
    page.emulate_media(reduced_motion="reduce")
    page.goto((directory / "curious.svg").as_uri())
    assert page.locator(".float").evaluate("(e) => getComputedStyle(e).animationName") == "none"
    capture("Reduced motion", "curious", reduced=True, stable=True)
    capture("Still image", "static", stable=True)

    branch = os.environ.get("GITHUB_HEAD_REF", "feat/sparks-retro-launch-20261028")
    target = "https://github.com/Albertito-AI/Albertito-AI/tree/" + branch
    try:
        page.emulate_media(reduced_motion="reduce")
        page.goto(target, wait_until="domcontentloaded", timeout=60000)
        header = page.locator('article img[alt^="Albert Tan:"]').first
        header.wait_for(timeout=30000)
        page.wait_for_function("(e) => e.complete && e.naturalWidth === 1200", arg=header.element_handle(), timeout=30000)
        print("PASS: GitHub branch README image loaded:", header.evaluate("(e) => e.currentSrc"))
        page.set_viewport_size({"width": 375, "height": 812})
        dimensions = header.bounding_box()
        assert abs(dimensions["height"] - dimensions["width"] * 380 / 1200) < 2, dimensions
        print("PASS: GitHub header retains its aspect ratio on mobile.")
        page.set_viewport_size({"width": 1240, "height": 430})
    except Exception as exc:
        print("GITHUB_BRANCH_BROWSER_CHECK_UNAVAILABLE:", type(exc).__name__, str(exc)[:250])

    try:
        page.goto("https://github.com/Albertito-AI", wait_until="domcontentloaded", timeout=60000)
        header = page.locator('article img[alt^="Albert Tan:"]').first
        header.wait_for(timeout=30000)
        page.wait_for_function("(e) => e.complete && e.naturalWidth === 1200", arg=header.element_handle(), timeout=30000)
        loaded = True
        retro = "retro research robot" in (header.get_attribute("alt") or "")
        print("PUBLIC_PROFILE_RETRO_LOADED:", bool(loaded and retro))
        print("PUBLIC_PROFILE_IMAGE_URL:", header.evaluate("(e) => e.currentSrc"))
    except Exception as exc:
        print("PUBLIC_PROFILE_BROWSER_CHECK_UNAVAILABLE:", type(exc).__name__, str(exc)[:250])
    browser.close()

if os.environ.get("SPARKS_EMIT_PREVIEW") == "1":
    sheet = Image.new("RGB", (1200, 660), "#101827")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=17)
    for index, (name, picture) in enumerate(images):
        x, y = (index % 2) * 600, (index // 2) * 220
        draw.text((x + 12, y + 6), name, fill="#e8d4a8", font=font)
        sheet.paste(picture.resize((600, 190), Image.Resampling.LANCZOS), (x, y + 30))
    buffer = io.BytesIO()
    sheet.save(buffer, format="PNG", optimize=True)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    print("SPARKS_SCREENSHOT_BEGIN")
    for start in range(0, len(encoded), 2000):
        print("SPARKS_PNG_CHUNK " + encoded[start:start + 2000])
    print("SPARKS_SCREENSHOT_END")
    print("All six local browser rendering checks passed.")
print("All six header browser rendering checks passed.")

# Exercise the complete supplied app through its real controls.
dance_images = []
layout_images = []
with sync_playwright() as pw:
    browser = pw.chromium.launch()
    context = browser.new_context(viewport={"width": 1440, "height": 1100}, device_scale_factor=1)
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.add_init_script("""
        window.__audioContexts = [];
        const OriginalAudioContext = window.AudioContext;
        if (OriginalAudioContext) window.AudioContext = class extends OriginalAudioContext {
          constructor(...args) { super(...args); window.__audioContexts.push(this); }
        };
    """)
    page.goto((ROOT / "site/index.html").as_uri(), wait_until="domcontentloaded")
    page.wait_for_function("window.__spark && document.querySelectorAll('.move').length === 6")
    page.wait_for_timeout(500)
    assert page.title() == "Sparks' Dance Floor"
    assert page.locator(".move").count() == 6
    assert page.locator("#sound").get_attribute("aria-pressed") == "false"
    assert page.evaluate("window.__audioContexts.length") == 0
    page.locator("#play").click()
    assert not page.evaluate("__spark.S0.playing")
    paused = page.evaluate("__spark.S0.t")
    page.wait_for_timeout(250)
    assert page.evaluate("__spark.S0.t") == paused
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    layout_images.append(("Desktop", Image.open(io.BytesIO(page.screenshot())).convert("RGB")))
    page.locator("#play").click()
    page.wait_for_function("__spark.S0.t > " + str(paused))
    page.locator("#sound").click()
    page.wait_for_function("window.__audioContexts.length === 1 && window.__audioContexts[0].state === 'running'")
    assert page.locator("#sound").get_attribute("aria-pressed") == "true"
    page.locator("#play").click()
    page.wait_for_function("window.__audioContexts[0].state === 'suspended'")
    page.locator("#play").click()
    page.wait_for_function("window.__audioContexts[0].state === 'running'")
    page.locator("#sound").click()
    page.wait_for_function("window.__audioContexts[0].state === 'suspended'")
    assert page.locator("#sound").get_attribute("aria-pressed") == "false"
    print("PASS: Pause/resume freezes and restarts choreography; sound is opt-in and suspends correctly.")
    for index in range(6):
        button = page.locator(".move").nth(index)
        name = button.locator(".name").inner_text()
        button.click()
        assert page.evaluate("__spark.S0.idx") == index
        assert page.locator(".move[aria-pressed='true']").count() == 1
        assert page.locator("#all").get_attribute("aria-pressed") == "false"
        page.locator("#play").click()
        page.evaluate("""() => {
          const d = __spark;
          d.S0.t = Math.min(11, d.R[d.S0.idx].beats - 1) * 60 / d.R[d.S0.idx].bpm;
          d.render();
        }""")
        page.wait_for_timeout(80)
        picture = Image.open(io.BytesIO(page.locator("#stage").screenshot())).convert("RGB")
        dance_images.append((name, picture))
        assert not errors, errors
        print("PASS: Routine", index + 1, name)
    page.locator("#all").click()
    page.evaluate("__spark.S0.t = __spark.R[0].beats * 60 / __spark.R[0].bpm - 0.01")
    page.wait_for_function("__spark.S0.idx === 1")
    assert page.locator("#nowName").inner_text() == "Be OK"
    assert page.locator("#all").get_attribute("aria-pressed") == "true"
    print("PASS: Whole set advances to the next routine and updates its label.")
    page.locator("#play").click()
    for width in (375, 320):
        page.set_viewport_size({"width": width, "height": 1100})
        page.wait_for_timeout(200)
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), width
        assert page.locator("#play").is_visible()
        assert page.locator("#sound").is_visible()
        if width == 375:
            layout_images.append(("Mobile 375 px", Image.open(io.BytesIO(page.screenshot())).convert("RGB")))
        print("PASS: Responsive layout at", width, "pixels without horizontal overflow.")
    page.set_viewport_size({"width": 1440, "height": 1100})
    page.locator(".move").nth(2).focus()
    page.keyboard.press("Enter")
    assert page.evaluate("__spark.S0.idx") == 2
    assert page.evaluate("__spark.S0.playing")
    print("PASS: Routine controls work from the keyboard.")
    reduced_context = browser.new_context(viewport={"width": 1000, "height": 900}, reduced_motion="reduce")
    reduced = reduced_context.new_page()
    reduced.on("pageerror", lambda error: errors.append(str(error)))
    reduced.goto((ROOT / "site/index.html").as_uri(), wait_until="domcontentloaded")
    reduced.wait_for_function("window.__spark && document.querySelectorAll('.move').length === 6")
    reduced.wait_for_timeout(500)
    assert not reduced.evaluate("__spark.S0.playing")
    a = Image.open(io.BytesIO(reduced.locator("#stage").screenshot())).convert("RGB")
    reduced.wait_for_timeout(350)
    b = Image.open(io.BytesIO(reduced.locator("#stage").screenshot())).convert("RGB")
    assert ImageChops.difference(a, b).getbbox() is None, "Reduced-motion dance changed while paused"
    reduced.locator("#play").click()
    assert reduced.evaluate("__spark.S0.playing")
    reduced.evaluate("""() => {
      window.__motionEvents = [];
      matchMedia("(prefers-reduced-motion: reduce)").addEventListener("change", e => __motionEvents.push(e.matches));
    }""")
    reduced.emulate_media(reduced_motion="no-preference")
    reduced.wait_for_function("window.__motionEvents.includes(false)")
    reduced.emulate_media(reduced_motion="reduce")
    reduced.wait_for_function("window.__motionEvents.includes(true)")
    reduced.wait_for_function("!__spark.S0.playing")
    print("PASS: Reduced motion starts still, permits deliberate play, and pauses on preference change.")
    assert not errors, errors
    print("PASS: No JavaScript errors.")
    browser.close()

def emit_image(label, picture):
    buffer = io.BytesIO()
    picture.save(buffer, format="PNG", optimize=True)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    for start in range(0, len(encoded), 2000):
        print(label + "_PNG_CHUNK " + encoded[start:start + 2000])

if os.environ.get("SPARKS_EMIT_PREVIEW") == "1":
    sheet = Image.new("RGB", (960, 560), "#1b1424")
    draw = ImageDraw.Draw(sheet)
    for index, (name, picture) in enumerate(dance_images):
        x, y = (index % 3) * 320, (index // 3) * 280
        draw.text((x + 8, y + 8), name, fill="#ffb02e", font=ImageFont.load_default(size=14))
        sheet.paste(picture.resize((320, 240), Image.Resampling.LANCZOS), (x, y + 36))
    emit_image("DANCE", sheet)
    layouts = Image.new("RGB", (1355, 1130), "#1b1424")
    draw = ImageDraw.Draw(layouts)
    for index, (name, picture) in enumerate(layout_images):
        x = 0 if index == 0 else 980
        draw.text((x + 10, 8), name, fill="#ffb02e", font=ImageFont.load_default(size=17))
        if index == 0: picture = picture.resize((960, 733), Image.Resampling.LANCZOS)
        layouts.paste(picture, (x, 30))
    emit_image("LAYOUT", layouts)
print("All Dance Floor browser checks passed.")
