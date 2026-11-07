#!/usr/bin/env python3
"""Read-only local MCP interface, using the official MCP Python SDK (MIT)."""
from __future__ import annotations

import json
from typing import Annotated, Literal

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

import catalog

mcp = FastMCP(
    "IBOL Open Learning Companion",
    instructions=("Read-only access to edition-specific materials for Albert Tan Sin Hon’s book. "
                  "Guide tools return companion summaries and fictional practice exercises. "
                  "search_book_text reads the separately installed, checksum-verified local publisher-PDF cache. "
                  "None of these results establishes current legal advice. "
                  "Retain source locators, legal cut-off and licence distinctions when using the material."),
)

READ_ONLY = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False)
Chapter = Annotated[int, Field(ge=1, le=8, strict=True)]


@mcp.tool(annotations=READ_ONLY)
def get_book_metadata() -> dict:
    """Read verified book identifiers, publisher and source record, legal cut-off and separate reuse terms."""
    return catalog.metadata()


@mcp.tool(annotations=READ_ONLY)
def get_citation(style: Literal["plain", "csl", "bibtex", "ris"] = "plain") -> dict:
    """Read a citation for the published book, with DOI and bibliographic provenance."""
    return catalog.citation(style)


@mcp.tool(annotations=READ_ONLY)
def search_guides(query: Annotated[str, Field(min_length=1, max_length=200)],
                  limit: Annotated[int, Field(ge=1, le=8, strict=True)] = 8) -> dict:
    """Search companion titles, guides, goals and exercises using all query terms. Does not search full-book text."""
    return catalog.search_guides(query, limit)


@mcp.tool(annotations=READ_ONLY)
def get_lesson(chapter: Chapter) -> dict:
    """Read one 90-minute companion seminar, including fictional exercise, commentary and source locator."""
    return catalog.lesson(chapter)


@mcp.tool(annotations=READ_ONLY)
def get_practice_questions(chapter: Chapter | None = None,
                           include_answers: Annotated[bool, Field(strict=True)] = False,
                           limit: Annotated[int, Field(ge=1, le=32, strict=True)] = 8) -> dict:
    """Read public formative questions. Answers and explanations are omitted unless explicitly requested."""
    return catalog.practice_questions(chapter, include_answers, limit)


@mcp.tool(annotations=READ_ONLY)
def search_book_text(query: Annotated[str, Field(min_length=1, max_length=200)],
                     limit: Annotated[int, Field(ge=1, le=10, strict=True)] = 5) -> dict:
    """Search a locally cached, checksum-verified publisher PDF extraction. Returns unavailable until fetch_book.py is explicitly run. Never downloads."""
    return catalog.search_book_text(query, limit)


@mcp.resource("ibol://book", name="Book metadata", mime_type="application/json")
def book_resource() -> str:
    return json.dumps(catalog.metadata(), ensure_ascii=False, indent=2)


@mcp.resource("ibol://lessons/{chapter}", name="Companion lesson", mime_type="application/json")
def lesson_resource(chapter: str) -> str:
    if not chapter.isdecimal():
        raise ValueError("chapter must be an integer from 1 to 8")
    return json.dumps(catalog.lesson(int(chapter)), ensure_ascii=False, indent=2)


if __name__ == "__main__":
    mcp.run(transport="stdio")
