"""Check public discovery paths and avoid conflicting canonical signals."""
from html.parser import HTMLParser
from pathlib import Path
import html
import json
import re
import unittest
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET


SITE = Path(__file__).resolve().parents[2] / "site"
BASE = "https://albertito-ai.github.io/Albertito-AI/"
NAMESPACE = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}


class CanonicalParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "link" and "canonical" in attributes.get("rel", "").split():
            self.urls.append(attributes.get("href"))


def local_file(url):
    if not url.startswith(BASE):
        raise ValueError("URL is outside this GitHub Pages project")
    suffix = url[len(BASE):]
    path = SITE / suffix
    return path / "index.html" if not suffix or suffix.endswith("/") else path


class PublicDiscoveryTests(unittest.TestCase):
    def test_all_eight_seminars_are_complete_without_javascript(self):
        lessons = json.loads((SITE / 'ibol/data/lessons.json').read_text())
        for lesson in lessons:
            path = SITE / 'ibol/lessons' / f"{lesson['id']:02d}.html"
            source = path.read_text()
            canonical = CanonicalParser(); canonical.feed(source)
            self.assertEqual(canonical.urls, [f"https://www.alberttansinhon.com/ibol/lessons/{lesson['id']:02d}"])
            for key in ['title', 'guide', 'exercise', 'answer', 'challenge', 'exit']:
                self.assertIn(html.escape(lesson[key]), source)
            self.assertNotIn('<script src=', source)
            self.assertIn('10.21827/6ac3948159a9e', source)
            self.assertIn('CC BY-NC-ND 4.0', source)

    def test_sitemap_urls_exist_and_do_not_conflict_with_declared_canonicals(self):
        root = ET.parse(SITE / "sitemap.xml").getroot()
        self.assertEqual(root.tag, "{" + NAMESPACE["s"] + "}urlset")
        urls = [node.text for node in root.findall("s:url/s:loc", NAMESPACE)]
        self.assertTrue(urls)
        self.assertEqual(len(urls), len(set(urls)))
        for url in urls:
            with self.subTest(url=url):
                parsed = urlsplit(url)
                self.assertEqual(parsed.scheme, "https")
                self.assertFalse(parsed.query or parsed.fragment)
                path = local_file(url)
                self.assertTrue(path.is_file(), path)
                self.assertEqual(path.suffix, ".html")
                canonical = CanonicalParser()
                canonical.feed(path.read_text(encoding="utf-8"))
                if canonical.urls:
                    self.assertEqual(canonical.urls, [url])
        # The root redirect and official-domain book mirror are not alternative
        # canonical requests in this project's sitemap.
        self.assertNotIn(BASE, urls)
        self.assertNotIn(BASE + "ibol/", urls)

    def test_project_navigation_resolves_every_same_project_resource(self):
        text = (SITE / "llms.txt").read_text(encoding="utf-8")
        urls = re.findall(r"\]\((https://[^\s)]+)\)", text)
        self.assertGreaterEqual(len(urls), 10)
        for url in urls:
            if url.startswith(BASE):
                with self.subTest(url=url):
                    self.assertTrue(local_file(url).is_file(), url)
        self.assertIn("https://books.ugp.rug.nl/ugp/catalog/book/300", urls)
        self.assertIn("https://www.alberttansinhon.com/ibol/", urls)


if __name__ == "__main__":
    unittest.main()
