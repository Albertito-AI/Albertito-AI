"""Unit, command-line and official-client stdio tests for the IBOL interface."""
from __future__ import annotations

import asyncio
from functools import wraps
import json
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import catalog

HERE = Path(__file__).resolve().parent


class CatalogTests(unittest.TestCase):
    def test_metadata_identifies_published_book(self):
        result = catalog.metadata()
        self.assertEqual(result["book"]["doi"], "10.21827/6ac3948159a9e")
        self.assertEqual(result["book"]["publication_date"], "2026-11-06")
        self.assertEqual(result["provenance"]["book_licence"], "CC BY-NC-ND 4.0")
        self.assertEqual(result["provenance"]["teaching_licence"], "CC BY 4.0")

    def test_every_lesson_has_locator_and_ninety_minutes(self):
        for chapter in range(1, 9):
            result = catalog.lesson(chapter)
            item = result["lesson"]
            self.assertEqual(item["id"], chapter)
            self.assertEqual(sum(step["minutes"] for step in item["plan"]), 90)
            self.assertEqual(result["source_locator"]["printed_pages"], item["pages"])
            self.assertTrue(result["source_locator"]["pdf_url"].endswith("#page=" + str(item["pages"][0] + 2)))

    def test_invalid_chapters_rejected(self):
        for chapter in [0, 9, -1, True, 1.0, "1", None]:
            with self.subTest(chapter=chapter), self.assertRaises(ValueError):
                catalog.lesson(chapter)

    def test_search_finds_known_distinction(self):
        result = catalog.search_guides("protector")
        self.assertIn(5, [item["chapter"] for item in result["results"]])
        self.assertIn("Full book text is not searched", result["search_scope"])

    def test_search_casefold_and_limit(self):
        self.assertEqual(catalog.search_guides("POLICY", 2)["results"], catalog.search_guides("policy", 2)["results"])
        self.assertEqual(len(catalog.search_guides("policy", 2)["results"]), 2)

    def test_search_requires_all_terms(self):
        result = catalog.search_guides("protector nonexistingword")
        self.assertEqual(result["results"], [])

    def test_no_match_is_explicit(self):
        result = catalog.search_guides("qzxv-no-such-subject")
        self.assertEqual(result["total_matches"], 0)
        self.assertEqual(result["results"], [])

    def test_invalid_queries_rejected(self):
        for query in ["", "  ", "!@#$", "a" * 201, None]:
            with self.subTest(query=query), self.assertRaises(ValueError):
                catalog.search_guides(query)

    def test_invalid_limits_rejected(self):
        for limit in [0, 9, True, 1.5]:
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                catalog.search_guides("policy", limit)
        for limit in [0, 33, False, 2.5]:
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                catalog.practice_questions(limit=limit)

    def test_question_answers_absent_by_default(self):
        result = catalog.practice_questions()
        self.assertFalse(result["include_answers"])
        self.assertEqual(len(result["questions"]), 8)
        self.assertEqual(result["total_available"], 32)
        for item in result["questions"]:
            self.assertNotIn("answer", item)
            self.assertNotIn("explanation", item)
            self.assertTrue(item["source"])

    def test_explicit_answers_and_chapter_filter(self):
        result = catalog.practice_questions(chapter=5, include_answers=True, limit=32)
        self.assertEqual(result["total_available"], 4)
        self.assertEqual(len(result["questions"]), 4)
        for item in result["questions"]:
            self.assertEqual(item["chapter"], 5)
            self.assertIn("answer", item)
            self.assertTrue(item["explanation"])

    def test_question_read_does_not_mutate_data(self):
        catalog.practice_questions(include_answers=False)
        self.assertIn("answer", catalog.practice_questions(include_answers=True)["questions"][0])

    def test_boolean_option_validation(self):
        with self.assertRaises(ValueError):
            catalog.practice_questions(include_answers="false")

    def test_four_citation_formats(self):
        for style in ["plain", "csl", "bibtex", "ris"]:
            result = catalog.citation(style)
            self.assertIn("10.21827/6ac3948159a9e", json.dumps(result["citation"]))
        self.assertEqual(catalog.citation("csl")["citation"]["type"], "book")
        self.assertIn("@book", catalog.citation("bibtex")["citation"])
        with self.assertRaises(ValueError):
            catalog.citation("invented")

    def test_unknown_collection_and_paths_rejected(self):
        for name in ["missing", "../../etc/passwd"]:
            with self.assertRaises(ValueError):
                catalog.read_data(name)

    def test_every_output_has_provenance(self):
        outputs = [catalog.metadata(), catalog.citation(), catalog.lesson(1),
                   catalog.search_guides("unknown-term"), catalog.practice_questions()]
        for output in outputs:
            self.assertEqual(output["provenance"]["legal_cutoff"], "2026-08-01")
            self.assertEqual(output["provenance"]["source_locator"], "https://books.ugp.rug.nl/ugp/catalog/book/300")


class CommandLineTests(unittest.TestCase):
    def test_search_outputs_json_and_clean_exit(self):
        proc = subprocess.run([sys.executable, str(HERE / "cli.py"), "search", "protector"], text=True, capture_output=True, timeout=10)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stderr, "")
        self.assertGreater(json.loads(proc.stdout)["total_matches"], 0)

    def test_invalid_chapter_has_failure_exit(self):
        proc = subprocess.run([sys.executable, str(HERE / "cli.py"), "lesson", "99"], text=True, capture_output=True, timeout=10)
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(proc.stdout, "")
        self.assertIn("chapter", json.loads(proc.stderr)["error"])

    def test_portable_classroom_kit_layout(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "IBOL_Classroom_Kit"
            (root / "scripts").mkdir(parents=True)
            shutil.copytree(catalog.data_directory(), root / "data")
            for name in ["catalog.py", "cli.py"]:
                shutil.copyfile(HERE / name, root / "scripts" / name)
            proc = subprocess.run([sys.executable, str(root / "scripts/cli.py"), "quiz", "--chapter", "8"], cwd=temp, text=True, capture_output=True, timeout=10)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(json.loads(proc.stdout)["total_available"], 4)


class BookCacheTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.cache = Path(self.temporary.name)
        self.env = patch.dict(os.environ, {"IBOL_CACHE_DIR": str(self.cache)})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.temporary.cleanup()

    def fixture(self):
        book = catalog.read_data("book")
        pdf = b"Synthetic PDF bytes for cache integrity tests only"
        book["source_verification"]["pdf_sha256"] = hashlib.sha256(pdf).hexdigest()
        book["source_verification"]["pdf_page_count"] = 2
        pages = [{"pdf_page": 1, "printed_page": None, "text": "Synthetic cover."},
                 {"pdf_page": 2, "printed_page": 1, "text": "A fictional protector question.\nStructural legibility is the test term."}]
        index = {"source_pdf_sha256": hashlib.sha256(pdf).hexdigest(), "pages": pages,
                 "pages_sha256": catalog.pages_digest(pages)}
        (self.cache / "book.pdf").write_bytes(pdf)
        (self.cache / "pages.json").write_text(json.dumps(index))
        return book, index

    def test_missing_cache_is_unavailable_without_network(self):
        result = catalog.search_book_text("protector")
        self.assertFalse(result["available"])
        self.assertIn("fetch_book.py", result["next_step"])
        self.assertEqual(list(self.cache.iterdir()), [])

    def test_valid_cache_returns_exact_excerpt_and_locator(self):
        book, index = self.fixture()
        with patch.object(catalog, "read_data", return_value=book):
            result = catalog.search_book_text("structural legibility")
        self.assertTrue(result["available"])
        self.assertEqual(result["total_matching_pages"], 1)
        found = result["results"][0]
        self.assertEqual(found["pdf_page"], 2)
        self.assertEqual(found["printed_page"], 1)
        self.assertIn(found["excerpt"], index["pages"][1]["text"])
        self.assertEqual(result["provenance"]["extracted_text_licence"], "CC BY-NC-ND 4.0")
        self.assertNotIn("teaching_licence", result["provenance"])

    def test_valid_cache_no_match(self):
        book, _ = self.fixture()
        with patch.object(catalog, "read_data", return_value=book):
            result = catalog.search_book_text("notpresent")
        self.assertTrue(result["available"])
        self.assertEqual(result["results"], [])

    def test_changed_pdf_is_unavailable(self):
        book, _ = self.fixture()
        (self.cache / "book.pdf").write_bytes(b"Changed")
        with patch.object(catalog, "read_data", return_value=book):
            result = catalog.search_book_text("protector")
        self.assertFalse(result["available"])
        self.assertIn("identity", result["reason"])

    def test_changed_index_is_unavailable(self):
        book, index = self.fixture()
        index["pages"][1]["text"] = "Changed extraction"
        (self.cache / "pages.json").write_text(json.dumps(index))
        with patch.object(catalog, "read_data", return_value=book):
            result = catalog.search_book_text("protector")
        self.assertFalse(result["available"])
        self.assertIn("integrity", result["reason"])

    def test_malformed_index_is_unavailable(self):
        self.fixture()
        (self.cache / "pages.json").write_text("not json")
        self.assertFalse(catalog.search_book_text("protector")["available"])

    def test_fetch_checks_identity_before_extraction(self):
        from fetch_book import index_pdf
        source = self.cache / "unexpected.pdf"
        source.write_bytes(b"Unverified file")
        with self.assertRaisesRegex(ValueError, "checksum"):
            index_pdf(source, self.cache / "result", catalog.read_data("book"))
        self.assertFalse((self.cache / "result").exists())

    def test_book_search_invalid_inputs(self):
        for query in ["", "  ", "???", "x" * 201]:
            with self.subTest(query=query), self.assertRaises(ValueError):
                catalog.search_book_text(query)
        for limit in [0, 11, True]:
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                catalog.search_book_text("policy", limit)


def official_client(test):
    @wraps(test)
    def run(self):
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
        async def scenario():
            params = StdioServerParameters(command=sys.executable, args=[str(HERE / "mcp_server.py")])
            async with stdio_client(params) as streams:
                async with ClientSession(*streams) as client:
                    self.client = client
                    self.initialized = await client.initialize()
                    await test(self)
        asyncio.run(scenario())
    return run


class MCPStdioTests(unittest.TestCase):
    @staticmethod
    def value(result):
        if result.structuredContent is not None:
            return result.structuredContent
        return json.loads(result.content[0].text)

    @official_client
    async def test_handshake_and_tool_discovery(self):
        self.assertEqual(self.initialized.protocolVersion, "2025-11-25")
        tools = (await self.client.list_tools()).tools
        self.assertEqual({tool.name for tool in tools}, {"get_book_metadata", "get_citation", "search_guides", "get_lesson", "get_practice_questions", "search_book_text"})
        self.assertTrue(all(tool.annotations.readOnlyHint for tool in tools))
        self.assertTrue(all(tool.annotations.openWorldHint is False for tool in tools))

    @official_client
    async def test_metadata_and_citation_calls(self):
        result = await self.client.call_tool("get_book_metadata", {})
        self.assertFalse(result.isError)
        self.assertEqual(self.value(result)["book"]["doi"], "10.21827/6ac3948159a9e")
        result = await self.client.call_tool("get_citation", {"style": "csl"})
        self.assertEqual(self.value(result)["citation"]["type"], "book")

    @official_client
    async def test_search_and_no_match(self):
        found = await self.client.call_tool("search_guides", {"query": "protector"})
        self.assertGreater(self.value(found)["total_matches"], 0)
        absent = await self.client.call_tool("search_guides", {"query": "qzxv-no-such-subject"})
        self.assertFalse(absent.isError)
        self.assertEqual(self.value(absent)["results"], [])

    @official_client
    async def test_lesson_and_resource_reads(self):
        result = await self.client.call_tool("get_lesson", {"chapter": 6})
        self.assertEqual(self.value(result)["lesson"]["id"], 6)
        resources = await self.client.list_resources()
        self.assertIn("ibol://book", [str(item.uri) for item in resources.resources])
        templates = await self.client.list_resource_templates()
        self.assertIn("ibol://lessons/{chapter}", [str(item.uriTemplate) for item in templates.resourceTemplates])
        result = await self.client.read_resource("ibol://lessons/6")
        self.assertEqual(json.loads(result.contents[0].text)["lesson"]["id"], 6)
        result = await self.client.read_resource("ibol://book")
        self.assertEqual(json.loads(result.contents[0].text)["book"]["publication_date"], "2026-11-06")

    @official_client
    async def test_default_and_requested_answers(self):
        result = await self.client.call_tool("get_practice_questions", {"chapter": 2})
        self.assertNotIn("answer", self.value(result)["questions"][0])
        self.assertNotIn("explanation", self.value(result)["questions"][0])
        result = await self.client.call_tool("get_practice_questions", {"chapter": 2, "include_answers": True})
        self.assertIn("answer", self.value(result)["questions"][0])

    @official_client
    async def test_unknown_tool_is_error(self):
        result = await self.client.call_tool("send_promotional_message", {})
        self.assertTrue(result.isError)

    @official_client
    async def test_book_search_reports_cache_state(self):
        result = await self.client.call_tool("search_book_text", {"query": "protector"})
        self.assertFalse(result.isError)
        value = self.value(result)
        self.assertIn("available", value)
        self.assertEqual(value["provenance"]["extracted_text_licence"], "CC BY-NC-ND 4.0")

    @official_client
    async def test_invalid_tool_arguments_are_errors(self):
        for name, args in [("get_lesson", {"chapter": 0}), ("get_lesson", {"chapter": 9}),
                           ("get_lesson", {"chapter": "one"}), ("search_guides", {"query": " "}),
                           ("get_practice_questions", {"limit": 33}),
                           ("get_practice_questions", {"include_answers": "false"})]:
            with self.subTest(name=name, args=args):
                result = await self.client.call_tool(name, args)
                self.assertTrue(result.isError)

    @official_client
    async def test_unknown_and_invalid_resources_are_errors(self):
        from mcp.shared.exceptions import McpError
        for uri in ["ibol://missing", "ibol://lessons/99", "ibol://lessons/not-a-chapter"]:
            with self.subTest(uri=uri), self.assertRaises(McpError):
                await self.client.read_resource(uri)


if __name__ == "__main__":
    unittest.main()
