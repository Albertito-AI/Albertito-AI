"""Read-only, standard-library access to the IBOL teaching companion (MIT)."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any


def data_directory() -> Path:
    """Support a repository checkout and the portable classroom-kit layout."""
    here = Path(__file__).resolve()
    candidates = (here.parents[2] / "site/ibol/data", here.parent.parent / "data")
    for candidate in candidates:
        if (candidate / "book.json").is_file() and (candidate / "lessons.json").is_file():
            return candidate
    raise FileNotFoundError("IBOL data not found. Keep scripts with the repository or classroom kit.")


def read_data(name: str) -> Any:
    if name not in {"book", "lessons", "quiz", "cases", "sorter"}:
        raise ValueError("Unknown companion data collection")
    return json.loads((data_directory() / (name + ".json")).read_text(encoding="utf-8"))


def cache_directory() -> Path:
    configured = os.environ.get("IBOL_CACHE_DIR")
    return Path(configured).expanduser() if configured else Path.home() / ".cache" / "ibol"


def pages_digest(pages: list[dict]) -> str:
    return hashlib.sha256(json.dumps(pages, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()


def provenance() -> dict[str, Any]:
    book = read_data("book")
    return {
        "resource_type": "teaching_companion",
        "status": book["companion"]["status"],
        "companion_version": book["companion"]["version"],
        "source_locator": book["catalogue_url"],
        "source_pdf": book["pdf_url"],
        "source_doi": book["doi"],
        "legal_cutoff": book["legal_cutoff"],
        "book_licence": book["book_licence"],
        "teaching_licence": book["companion"]["teaching_licence"],
        "scope": "Edition-specific companion material, not the full book or current legal advice.",
    }


def envelope(**payload: Any) -> dict[str, Any]:
    return {"provenance": provenance(), **payload}


def validate_chapter(chapter: int) -> int:
    if type(chapter) is not int or not 1 <= chapter <= 8:
        raise ValueError("chapter must be an integer from 1 to 8")
    return chapter


def metadata() -> dict[str, Any]:
    return envelope(book=read_data("book"))


def citation(style: str = "plain") -> dict[str, Any]:
    book = read_data("book")
    title = book["title"] + ": " + book["subtitle"]
    author = book["author"]
    doi = book["doi"]
    if style == "plain":
        value = f"{author}, {title} ({book['publisher']} 2026), https://doi.org/{doi}."
    elif style == "csl":
        value = {
            "id": doi, "type": "book", "title": title,
            "author": [{"family": book["author_family"], "given": book["author_given"]}],
            "issued": {"date-parts": [[2026, 11, 6]]},
            "publisher": book["publisher"], "publisher-place": "Groningen",
            "DOI": doi, "ISBN": book["isbn_epdf"], "URL": book["catalogue_url"], "language": "en",
        }
    elif style == "bibtex":
        value = ("@book{tan2026ibol,\n"
                 f"  author = {{{book['author_family']}, {book['author_given']}}},\n"
                 f"  title = {{{{{title}}}}},\n"
                 f"  publisher = {{{book['publisher']}}},\n"
                 "  address = {Groningen},\n  year = {2026},\n"
                 f"  doi = {{{doi}}},\n  isbn = {{{book['isbn_epdf']}}},\n"
                 f"  url = {{{book['catalogue_url']}}}\n}}\n")
    elif style == "ris":
        value = (f"TY  - BOOK\nAU  - {book['author_family']}, {book['author_given']}\n"
                 f"TI  - {title}\nPY  - 2026\nDA  - 2026/11/06\nPB  - {book['publisher']}\n"
                 f"CY  - Groningen\nDO  - {doi}\nSN  - {book['isbn_epdf']}\n"
                 f"UR  - {book['catalogue_url']}\nLA  - English\nER  - \n")
    else:
        raise ValueError("style must be plain, csl, bibtex or ris")
    return envelope(style=style, citation=value)


def lesson(chapter: int) -> dict[str, Any]:
    validate_chapter(chapter)
    selected = next(item for item in read_data("lessons") if item["id"] == chapter)
    book = read_data("book")
    locator = {
        "chapter": chapter, "printed_pages": selected["pages"],
        "sections": selected["sections"],
        "pdf_url": book["pdf_url"] + "#page=" + str(selected["pages"][0] + book["source_verification"]["printed_page_to_pdf_offset"]),
    }
    return envelope(lesson=selected, source_locator=locator)


def search_guides(query: str, limit: int = 8) -> dict[str, Any]:
    if not isinstance(query, str) or not query.strip() or len(query) > 200:
        raise ValueError("query must contain 1 to 200 characters")
    if type(limit) is not int or not 1 <= limit <= 8:
        raise ValueError("limit must be an integer from 1 to 8")
    terms = re.findall(r"[^\W_]+", query.casefold())
    if not terms:
        raise ValueError("query must contain at least one word or number")
    results = []
    for item in read_data("lessons"):
        text = " ".join([item["title"], item["guide"], item["exercise"], *item["goals"]]).casefold()
        if all(term in text for term in terms):
            results.append({
                "chapter": item["id"], "title": item["title"], "guide": item["guide"],
                "printed_pages": item["pages"], "sections": item["sections"],
                "score": sum(text.count(term) for term in terms),
                "source_locator": lesson(item["id"])["source_locator"],
            })
    results.sort(key=lambda item: (-item["score"], item["chapter"]))
    return envelope(query=query, search_scope="Companion titles, reading guides, goals and exercises. Full book text is not searched.",
                    total_matches=len(results), results=results[:limit])


def practice_questions(chapter: int | None = None, include_answers: bool = False, limit: int = 8) -> dict[str, Any]:
    if chapter is not None:
        validate_chapter(chapter)
    if type(include_answers) is not bool:
        raise ValueError("include_answers must be true or false")
    if type(limit) is not int or not 1 <= limit <= 32:
        raise ValueError("limit must be an integer from 1 to 32")
    selected = [deepcopy(q) for q in read_data("quiz") if chapter is None or q["chapter"] == chapter]
    for question in selected:
        if not include_answers:
            question.pop("answer", None)
            question.pop("explanation", None)
    return envelope(chapter=chapter, include_answers=include_answers, total_available=len(selected),
                    questions=selected[:limit],
                    assessment_status="Public formative practice, not confidential assessment or certification.")


def search_book_text(query: str, limit: int = 5) -> dict[str, Any]:
    """Search a verified, explicitly installed local PDF extraction. Never fetch."""
    if not isinstance(query, str) or not query.strip() or len(query) > 200:
        raise ValueError("query must contain 1 to 200 characters")
    terms = re.findall(r"[^\W_]+", query.casefold())
    if not terms:
        raise ValueError("query must contain at least one word or number")
    if type(limit) is not int or not 1 <= limit <= 10:
        raise ValueError("limit must be an integer from 1 to 10")
    book = read_data("book")
    cache = cache_directory()
    status = {**provenance(), "resource_type": "mechanical_book_extraction",
              "status": "Mechanical extraction of the published book, separate from the companion teaching content.",
              "scope": "Local extraction of the pinned published PDF. Formatting and reading order may differ; verify quotations against the PDF.",
              "extracted_text_licence": book["book_licence"]}
    status.pop("teaching_licence", None)
    try:
        pdf_path, index_path = cache / "book.pdf", cache / "pages.json"
        if not pdf_path.is_file() or not index_path.is_file():
            return {"provenance": status, "available": False, "reason": "No local book cache is installed.",
                    "next_step": "Run scripts/ibol/fetch_book.py (scripts/fetch_book.py in the classroom kit), then restart the query. Use the same IBOL_CACHE_DIR for fetch and search.", "results": []}
        if pdf_path.stat().st_size > 16 * 1024 * 1024 or index_path.stat().st_size > 16 * 1024 * 1024:
            raise ValueError("Cache exceeds the expected maximum size")
        digest = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
        index = json.loads(index_path.read_text(encoding="utf-8"))
        if digest != book["source_verification"]["pdf_sha256"] or index["source_pdf_sha256"] != digest:
            raise ValueError("Cached PDF identity differs from the pinned edition")
        pages = index["pages"]
        if len(pages) != book["source_verification"]["pdf_page_count"] or pages_digest(pages) != index["pages_sha256"]:
            raise ValueError("Cached extraction failed its page-count or integrity check")
        for position, page in enumerate(pages, 1):
            if page["pdf_page"] != position or not isinstance(page["text"], str) or (page["printed_page"] is not None and type(page["printed_page"]) is not int):
                raise ValueError("Cached extraction contains an invalid page record")
    except (OSError, KeyError, TypeError, json.JSONDecodeError, ValueError) as error:
        return {"provenance": status, "available": False, "reason": str(error),
                "next_step": "Recreate the local cache with fetch_book.py before relying on book-text results.", "results": []}
    found = []
    for page in pages:
        original = page["text"]
        normalised = re.sub(r"-\s*\n\s*", "", original)
        normalised = re.sub(r"\s+", " ", normalised).strip()
        folded = normalised.casefold()
        if all(term in folded for term in terms):
            # Return an exact extracted-text excerpt. Search normalisation is not presented as quotation.
            match = next((re.search(re.escape(term), original, re.IGNORECASE) for term in terms
                          if re.search(re.escape(term), original, re.IGNORECASE)), None)
            start = max(0, (match.start() if match else 0) - 120)
            excerpt = original[start:start + 900]
            found.append({"pdf_page": page["pdf_page"], "printed_page": page["printed_page"],
                          "source_locator": book["pdf_url"] + "#page=" + str(page["pdf_page"]),
                          "score": sum(folded.count(term) for term in terms), "excerpt": excerpt,
                          "excerpt_note": "Exact substring of mechanical extraction, possibly starting or ending mid-sentence. Check PDF layout before quoting."})
    found.sort(key=lambda item: (-item["score"], item["pdf_page"]))
    return {"provenance": status, "available": True, "query": query,
            "source_pdf_sha256": digest, "total_matching_pages": len(found), "results": found[:limit]}
