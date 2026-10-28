from __future__ import annotations

from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_PATHS = {
    "README.md",
    "assets/research-header.svg",
    "docs/PORTFOLIO_VISIBILITY_POLICY.md",
    "docs/PROFILE_EVOLUTION.md",
    "docs/PROFILE_PROGRESS.md",
    "docs/ALBERTITO.md",
    "assets/persona-template.svg",
    "assets/research-header-static.svg",
    "data/persona.json",
    "scripts/update_persona.py",
    "tests/test_persona.py",
    ".github/workflows/persona.yml",
}

REQUIRED_REPOSITORY_LINKS = {
    "https://github.com/Albertito-AI/AlberTito-MasterMind",
    "https://github.com/Albertito-AI/evtalbert",
    "https://github.com/Albertito-AI/policykit",
    "https://github.com/Albertito-AI/regnav-source-watch",
    "https://github.com/Albertito-AI/symbolon",
    "https://github.com/Albertito-AI/piepowder",
    "https://github.com/Albertito-AI/tallystick",
}

CONFLICT_MARKERS = ("<<<<<<<", "=======", ">>>>>>>")
LINK_PATTERN = re.compile(r"!?\[[^\]]*\]\((<[^>]+>|[^\s)]+)")


def _local_target(markdown_file: Path, raw_target: str) -> Path | None:
    target = raw_target.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1]

    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc or target.startswith(("#", "mailto:", "tel:", "data:")):
        return None

    path_text = unquote(parsed.path)
    if not path_text:
        return None

    if path_text.startswith("/"):
        candidate = ROOT / path_text.lstrip("/")
    else:
        candidate = markdown_file.parent / path_text

    resolved = candidate.resolve()
    try:
        resolved.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise ValueError(f"link escapes repository: {target}") from exc
    return resolved


def validate() -> list[str]:
    errors: list[str] = []

    for relative in sorted(REQUIRED_PATHS):
        if not (ROOT / relative).exists():
            errors.append(f"missing required path: {relative}")

    markdown_files = sorted(ROOT.rglob("*.md"))
    if not markdown_files:
        errors.append("no Markdown files found")

    for markdown_file in markdown_files:
        text = markdown_file.read_text(encoding="utf-8")
        relative = markdown_file.relative_to(ROOT)

        for marker in CONFLICT_MARKERS:
            if marker in text:
                errors.append(f"merge-conflict marker {marker!r} in {relative}")

        for match in LINK_PATTERN.finditer(text):
            raw_target = match.group(1)
            try:
                local = _local_target(markdown_file, raw_target)
            except ValueError as exc:
                errors.append(f"{relative}: {exc}")
                continue
            if local is not None and not local.exists():
                errors.append(
                    f"broken local link in {relative}: {raw_target} -> "
                    f"{local.relative_to(ROOT)}"
                )

    readme_path = ROOT / "README.md"
    if readme_path.exists():
        readme = readme_path.read_text(encoding="utf-8")
        for url in sorted(REQUIRED_REPOSITORY_LINKS):
            if url not in readme:
                errors.append(f"README omits portfolio repository: {url}")
        if "https://www.alberttansinhon.com/" not in readme:
            errors.append("README omits the canonical website URL")
        if "docs/PORTFOLIO_VISIBILITY_POLICY.md" not in readme:
            errors.append("README does not reference the portfolio visibility policy")

    for name in ("research-header.svg", "research-header-static.svg", "persona-template.svg"):
        svg_path = ROOT / "assets" / name
        if not svg_path.exists():
            continue
        try:
            root = ET.parse(svg_path).getroot()
        except ET.ParseError as exc:
            errors.append(f"invalid SVG XML in {name}: {exc}")
        else:
            if root.tag != "{http://www.w3.org/2000/svg}svg":
                errors.append(f"{name} root element is not an SVG document")
            tags = {element.tag.split("}")[-1] for element in root.iter()}
            if not {"title", "desc"}.issubset(tags):
                errors.append(f"{name} needs an accessible title and description")
            if tags & {"script", "foreignObject", "iframe", "object", "embed"}:
                errors.append(f"{name} contains active embedded content")
            for element in root.iter():
                for attribute, value in element.attrib.items():
                    local = attribute.split("}")[-1]
                    if local.lower().startswith("on"):
                        errors.append(f"{name} contains an event handler")
                    if local == "href" and not value.startswith("#"):
                        errors.append(f"{name} contains an external reference")
            svg_text = svg_path.read_text(encoding="utf-8")
            if "@import" in svg_text.lower():
                errors.append(f"{name} imports an external stylesheet")
            for reference in re.findall(r"url\(([^)]+)\)", svg_text, flags=re.I):
                if not reference.strip(" \t\"'").startswith("#"):
                    errors.append(f"{name} contains a nonlocal CSS reference")

    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("Profile integrity validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    markdown_count = sum(1 for _ in ROOT.rglob("*.md"))
    print(
        "Profile integrity validation passed: "
        f"{markdown_count} Markdown files, required records present, "
        "local links resolved, SVG parsed and portfolio links retained."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
