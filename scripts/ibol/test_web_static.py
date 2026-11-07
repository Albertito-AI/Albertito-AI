"""Cross-file integrity checks for the built IBOL teaching companion.

Run after build.py. These tests verify the public package, data and navigation;
they do not substitute for browser, accessibility or doctrinal review.
"""
from collections import Counter
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import subprocess
import unittest
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET
import zipfile


ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "site" / "ibol"


class HTMLRecord(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.ids = []
        self.references = []
        self.canonical = None
        self.scripts = []
        self.image_alts = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        for attr in ("href", "src"):
            if attrs.get(attr):
                self.references.append(attrs[attr])
        if tag == "link" and attrs.get("rel") == "canonical":
            self.canonical = attrs.get("href")
        if tag == "script" and attrs.get("src"):
            self.scripts.append(attrs["src"])
        if tag == "img":
            self.image_alts.append(attrs.get("alt"))


class CompanionIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.book = json.loads((SITE / "data/book.json").read_text())
        cls.lessons = json.loads((SITE / "data/lessons.json").read_text())
        cls.quiz = json.loads((SITE / "data/quiz.json").read_text())
        cls.cases = json.loads((SITE / "data/cases.json").read_text())
        cls.index = HTMLRecord((SITE / "index.html").read_text())

    def test_chapters_have_complete_90_minute_lessons(self):
        self.assertEqual([l["id"] for l in self.lessons], list(range(1, 9)))
        for lesson in self.lessons:
            with self.subTest(chapter=lesson["id"]):
                self.assertEqual(sum(slot["minutes"] for slot in lesson["plan"]), 90)
                self.assertLessEqual(lesson["pages"][0], lesson["pages"][1])
                for key in ("title", "guide", "exercise", "answer", "challenge", "exit", "sections"):
                    self.assertTrue(lesson[key].strip(), key)
                self.assertTrue((SITE / f"lessons/{lesson['id']:02d}.md").is_file())

    def test_question_bank_has_usable_answers_and_balanced_coverage(self):
        self.assertEqual(len(self.quiz), 32)
        self.assertEqual(Counter(q["chapter"] for q in self.quiz), Counter({i: 4 for i in range(1, 9)}))
        self.assertEqual(len({q["id"] for q in self.quiz}), len(self.quiz))
        for q in self.quiz:
            with self.subTest(question=q["id"]):
                self.assertEqual(len(q["options"]), 4)
                self.assertEqual(len(set(q["options"])), 4)
                self.assertIs(type(q["answer"]), int)
                self.assertIn(q["answer"], range(4))
                self.assertTrue(q["explanation"].strip())
                self.assertTrue(q["source"].strip())

    def test_games_retain_fictional_status_and_complete_options(self):
        self.assertEqual(len(self.cases), 6)
        for case in self.cases:
            self.assertIs(case["fictional"], True)
            self.assertIn(case["answer"], range(len(case["options"])))
            self.assertTrue(case["facts"])
            self.assertTrue(case["source"])
        cards = json.loads((SITE / "data/sorter.json").read_text())
        self.assertEqual(len(cards), 9)
        for card in cards:
            self.assertIn(card["category"], {"Legal position", "Value movement", "Institutional information"})
            self.assertTrue(card["why"])

    def test_builtin_dom_targets_and_internal_anchors_exist(self):
        counts = Counter(self.index.ids)
        self.assertFalse([name for name, count in counts.items() if count > 1])
        js = (SITE / "app.js").read_text()
        # Only literal DOM lookups: dynamically created lesson IDs are checked
        # separately by the numbered lesson set.
        ids = set(re.findall(r"\$\('([^']+)'\)", js))
        self.assertFalse(ids - set(self.index.ids), f"Missing DOM IDs: {ids - set(self.index.ids)}")
        for ref in self.index.references:
            parts = urlsplit(ref)
            if ref.startswith("#"):
                self.assertIn(unquote(parts.fragment), self.index.ids)

    def test_html_local_links_and_assets_exist(self):
        missing = []
        for html_path in SITE.rglob("*.html"):
            record = HTMLRecord(html_path.read_text())
            for raw in record.references:
                ref = urlsplit(raw)
                if ref.scheme or ref.netloc or not ref.path:
                    continue
                if ref.path.startswith("/"):
                    # Site-root links depend on the deployment mount; the
                    # standalone kit should use external URLs for such links.
                    continue
                path = (html_path.parent / unquote(ref.path)).resolve()
                if not path.exists():
                    missing.append(f"{html_path.relative_to(SITE)} -> {raw}")
        self.assertFalse(missing, "Missing local links/assets: " + "; ".join(missing))

    def test_static_browser_requires_no_external_scripts(self):
        for ref in self.index.scripts:
            self.assertFalse(urlsplit(ref).scheme, ref)
            self.assertFalse(ref.startswith("//"), ref)
        self.assertTrue(self.index.image_alts)
        self.assertTrue(all(alt is not None and alt.strip() for alt in self.index.image_alts))

    def test_citation_exports_agree_on_identity_and_rights(self):
        csl = json.loads((SITE / "metadata/book.csl.json").read_text())[0]
        schema = json.loads((SITE / "metadata/book.jsonld").read_text())
        self.assertEqual(csl["DOI"], self.book["doi"])
        self.assertEqual(csl["ISBN"], self.book["isbn_epdf"])
        self.assertEqual(schema["isbn"], self.book["isbn_epdf"])
        self.assertEqual(schema["license"], self.book["book_licence_url"])
        self.assertEqual(schema["url"], self.book["catalogue_url"])
        self.assertEqual(schema["datePublished"], self.book["publication_date"])
        self.assertEqual(csl["author"][0]["family"], self.book["author_family"])
        self.assertEqual(csl["author"][0]["given"], self.book["author_given"])
        dc = ET.parse(SITE / "metadata/dublin-core.xml")
        identifiers = [n.text for n in dc.findall(".//{http://purl.org/dc/elements/1.1/}identifier")]
        self.assertIn("https://doi.org/" + self.book["doi"], identifiers)

    def test_landing_canonical_agrees_with_public_record(self):
        self.assertEqual(self.index.canonical, self.book["companion"]["canonical"])

    @unittest.skipUnless(shutil.which("node"), "Node.js needed to read the built browser data bundle")
    def test_browser_content_matches_reviewed_json(self):
        script = "const fs=require('fs'),vm=require('vm');const c={window:{}};vm.runInNewContext(fs.readFileSync(process.argv[1],'utf8'),c);process.stdout.write(JSON.stringify(c.window.IBOL));"
        result = subprocess.run(["node", "-e", script, str(SITE / "content.js")], check=True, capture_output=True, text=True)
        actual = json.loads(result.stdout)
        for name in ("book", "lessons", "quiz", "cases", "sorter"):
            with self.subTest(data=name):
                self.assertEqual(actual[name], json.loads((SITE / f"data/{name}.json").read_text()))

    def test_classroom_archive_contains_runtime_and_install_requirements(self):
        archive = SITE / "downloads/IBOL_Classroom_Kit.zip"
        with zipfile.ZipFile(archive) as z:
            names = set(z.namelist())
            root = "IBOL_Classroom_Kit/"
            for relative in ("index.html", "app.js", "content.js", "styles.css", "slides.html", "data/book.json", "data/lessons.json", "data/quiz.json", "data/cases.json", "data/sorter.json", "scripts/catalog.py", "scripts/cli.py", "scripts/mcp_server.py", "scripts/requirements.txt", "RIGHTS.md"):
                self.assertIn(root + relative, names)
            self.assertIsNone(z.testzip())
            # The downloaded copy must not contain links to absent siblings
            # such as the Research Lab or an excluded recursive ZIP download.
            landing = HTMLRecord(z.read(root + "index.html").decode())
            for raw in landing.references:
                ref = urlsplit(raw)
                if ref.scheme or ref.netloc or not ref.path:
                    continue
                normal = (Path(root) / unquote(ref.path)).as_posix()
                self.assertIn(normal, names, f"Offline link missing from ZIP: {raw}")


if __name__ == "__main__":
    unittest.main()
