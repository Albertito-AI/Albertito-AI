"""Manually reproduce the archived canvas choreography; no live site is changed."""
from pathlib import Path
import base64
import hashlib
import io
import json
import math
import shutil
import subprocess
import tempfile

from PIL import Image, ImageChops, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

ROOT = Path.cwd()
WIDTH, HEIGHT, FPS = 304, 540, 10
ASSETS = ROOT / "assets"
ARCHIVE_SOURCE = "archive/sparks/dance-floor.html"
GIF_LIMIT = 4 * 1024 * 1024
START_BEATS = {"hip": 5, "beok": 4, "pumpkin": 8, "slowmo": 3.5, "fishes": 2, "ramalama": 11}

with tempfile.TemporaryDirectory() as temp, sync_playwright() as pw:
    directory = Path(temp)
    browser = pw.chromium.launch()
    context = browser.new_context(viewport={"width": 360, "height": 820}, device_scale_factor=1, reduced_motion="reduce")
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto((ROOT / ARCHIVE_SOURCE).as_uri(), wait_until="domcontentloaded")
    page.wait_for_function("window.__spark && document.querySelectorAll('.move').length === 6")
    page.add_style_tag(content="#stage { width:304px !important; height:540px !important; aspect-ratio:auto !important; }")
    page.evaluate("__spark.resize()")
    page.wait_for_timeout(500)
    page.evaluate("document.fonts.ready")
    assert not errors, errors
    routines = page.evaluate("__spark.R.map(r => ({id:r.id,name:r.name,bpm:r.bpm,beats:r.beats}))")
    frames = []
    sampled = []
    poster = None
    contact = []
    offsets = []
    for index, routine in enumerate(routines):
        count = math.ceil(routine["beats"] * 60 / routine["bpm"] * FPS)
        offset = len(frames)
        offsets.append(offset)
        for n in range(count):
            encoded = page.evaluate("""args => {
              const [index, time] = args, d = __spark;
              d.S0.mode = "single"; d.S0.idx = index; d.S0.t = time; d.S0.playing = false;
              d.render();
              return document.getElementById("stage").toDataURL("image/png").split(",")[1];
            }""", [index, n / FPS])
            data = base64.b64decode(encoded)
            picture = Image.open(io.BytesIO(data)).convert("RGB")
            assert picture.size == (WIDTH, HEIGHT)
            (directory / ("frame-%05d.png" % len(frames))).write_bytes(data)
            frames.append(picture)
        start = round(START_BEATS[routine["id"]] * 60 / routine["bpm"] * FPS)
        start = min(start, count - 30)
        sampled.extend(frames[offset + start:offset + start + 30])
        best = min(count - 1, round(11 * 60 / routine["bpm"] * FPS))
        contact.append((routine["name"], frames[offset + best]))
        if index == 0:
            poster = frames[offset + best]
        print("RENDERED:", routine["name"], count, "frames", flush=True)
    assert not errors, errors
    poster.save(ASSETS / "sparks-dance-still.png", optimize=True)

    # A shared palette keeps the stage stable and avoids noisy dithering.
    atlas = Image.new("RGB", (WIDTH * 6, HEIGHT))
    for index, (_, picture) in enumerate(contact):
        atlas.paste(picture, (WIDTH * index, 0))
    gif_path = ASSETS / "sparks-dance.gif"
    used_colors, used_fps = None, None
    for colors, rate in ((128, 10), (96, 10), (96, 8), (64, 8)):
        palette = atlas.quantize(colors=colors, method=Image.Quantize.MEDIANCUT)
        selected = [sampled[min(len(sampled)-1, round(n * FPS / rate))]
                    for n in range(round(len(sampled) * rate / FPS))]
        indexed = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in selected]
        durations = [round((n + 1) * 100 / rate) * 10 - round(n * 100 / rate) * 10
                     for n in range(len(indexed))]
        indexed[0].save(gif_path, save_all=True, append_images=indexed[1:], duration=durations,
                        loop=0, optimize=True, disposal=1)
        print("GIF_CANDIDATE:", colors, rate, gif_path.stat().st_size, flush=True)
        if gif_path.stat().st_size <= GIF_LIMIT:
            used_colors, used_fps = colors, rate
            break
    assert used_colors is not None, "GIF exceeds the 4 MiB profile budget"
    with Image.open(gif_path) as gif:
        assert gif.format == "GIF" and gif.is_animated and gif.n_frames >= 120
        assert gif.info.get("loop") == 0
        count = gif.n_frames
        total_ms = 0
        first = gif.convert("RGB").copy()
        different = False
        for n in range(count):
            gif.seek(n)
            assert gif.info.get("duration", 0) > 0
            total_ms += gif.info["duration"]
            if n and ImageChops.difference(first, gif.convert("RGB")).getbbox():
                different = True
        assert different
    ffmpeg = shutil.which("ffmpeg")
    assert ffmpeg, "ffmpeg is required to produce the full silent video"
    subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
                    "-framerate", str(FPS), "-i", str(directory / "frame-%05d.png"),
                    "-c:v", "libx264", "-crf", "24", "-pix_fmt", "yuv420p",
                    "-movflags", "+faststart", str(ASSETS / "sparks-dance.mp4")], check=True)
    manifest = {
        "source": ARCHIVE_SOURCE,
        "source_sha256": hashlib.sha256((ROOT / ARCHIVE_SOURCE).read_bytes()).hexdigest(),
        "dimensions": [WIDTH, HEIGHT],
        "gif": {"frames": count, "duration_ms": total_ms, "fps": used_fps, "colors": used_colors,
                "bytes": gif_path.stat().st_size, "loop": 0,
                "sha256": hashlib.sha256(gif_path.read_bytes()).hexdigest()},
        "video": {"frames": len(frames), "fps": FPS, "duration_seconds": len(frames) / FPS,
                  "bytes": (ASSETS / "sparks-dance.mp4").stat().st_size, "audio": False},
        "routines": [r["name"] for r in routines],
    }
    (ASSETS / "sparks-dance-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("MEDIA_MANIFEST:", json.dumps(manifest), flush=True)

    # The retired stage is verified locally by check_sparks_media.py.
    browser.close()

sheet = Image.new("RGB", (684, 870), "#1b1424")
draw = ImageDraw.Draw(sheet)
for index, (name, picture) in enumerate(contact):
    x, y = (index % 3) * 228, (index // 3) * 435
    draw.text((x + 5, y + 4), name, fill="#ffb02e", font=ImageFont.load_default(size=12))
    sheet.paste(picture.resize((228, 405), Image.Resampling.LANCZOS), (x, y + 26))
buffer = io.BytesIO()
sheet.save(buffer, "PNG", optimize=True)
encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
for start in range(0, len(encoded), 2000):
    print("MEDIA_PNG_CHUNK " + encoded[start:start + 2000])
print("Dance media exports verified.")
