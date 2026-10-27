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
}

REQUIRED_REPOSITORY_LINKS = {
    "https://github.com/Albertito-AI/AlberTito-MasterMind",
    "https://github.com/Albertito-AI/evtalbert",
    "https://github.com/Albertito-AI/policykit",
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

    svg_path = ROOT / "assets" / "research-header.svg"
    if svg_path.exists():
        try:
            root = ET.parse(svg_path).getroot()
        except ET.ParseError as exc:
            errors.append(f"invalid SVG XML: {exc}")
        else:
            if not root.tag.endswith("svg"):
                errors.append("research-header.svg root element is not <svg>")

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
