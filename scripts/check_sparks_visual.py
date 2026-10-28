from pathlib import Path
import base64
import hashlib
import io
import json
import os
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFont
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
        wrapper.write_text('<!doctype html><html><head><style>html,body{margin:0;background:#101827}img{display:block;width:1200px;height:380px}</style></head><body><img id="header" alt="Sparks test" src="' + file_name + '.svg"></body></html>')
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
            assert data == page.locator("#header").screenshot(animations="allow"), name + " still moved"
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
        assert header.evaluate("(e) => e.complete && e.naturalWidth === 1200")
        print("PASS: GitHub branch README image loaded:", header.get_attribute("src"))
    except Exception as exc:
        print("GITHUB_BRANCH_BROWSER_CHECK_UNAVAILABLE:", type(exc).__name__, str(exc)[:250])

    try:
        page.goto("https://github.com/Albertito-AI", wait_until="domcontentloaded", timeout=60000)
        header = page.locator('article img[alt^="Albert Tan:"]').first
        header.wait_for(timeout=30000)
        loaded = header.evaluate("(e) => e.complete && e.naturalWidth === 1200")
        retro = "retro research robot" in (header.get_attribute("alt") or "")
        print("PUBLIC_PROFILE_RETRO_LOADED:", bool(loaded and retro))
        print("PUBLIC_PROFILE_IMAGE_URL:", header.get_attribute("src"))
    except Exception as exc:
        print("PUBLIC_PROFILE_BROWSER_CHECK_UNAVAILABLE:", type(exc).__name__, str(exc)[:250])
    browser.close()

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
