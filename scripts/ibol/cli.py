#!/usr/bin/env python3
"""Read IBOL companion material as JSON. Requires Python 3.10+, no packages."""
from __future__ import annotations

import argparse
import json
import sys

from catalog import citation, envelope, lesson, metadata, practice_questions, search_book_text, search_guides


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("metadata", help="Book identity, source record and rights")
    cite = commands.add_parser("citation", help="Citation in the requested format, inside a JSON envelope")
    cite.add_argument("--style", choices=["plain", "csl", "bibtex", "ris"], default="plain")
    search = commands.add_parser("search", help="Search companion guides, not the full book")
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=8)
    fulltext = commands.add_parser("search-book", help="Search an explicitly installed local publisher-PDF cache")
    fulltext.add_argument("query")
    fulltext.add_argument("--limit", type=int, default=5)
    read = commands.add_parser("lesson", help="One complete companion lesson")
    read.add_argument("chapter", type=int)
    quiz = commands.add_parser("quiz", help="Public practice questions; answers omitted by default")
    quiz.add_argument("--chapter", type=int)
    quiz.add_argument("--limit", type=int, default=8)
    quiz.add_argument("--answers", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "metadata":
            result = metadata()
        elif args.command == "citation":
            result = citation(args.style)
        elif args.command == "search":
            result = search_guides(args.query, args.limit)
        elif args.command == "lesson":
            result = lesson(args.chapter)
        elif args.command == "search-book":
            result = search_book_text(args.query, args.limit)
        else:
            result = practice_questions(args.chapter, args.answers, args.limit)
    except (ValueError, FileNotFoundError) as error:
        try:
            failure = envelope(error=str(error))
        except FileNotFoundError:
            failure = {"error": str(error), "provenance_available": False}
        print(json.dumps(failure, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
