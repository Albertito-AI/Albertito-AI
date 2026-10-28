"""Integration checks for the narrowly permitted embedded Sparks PNG."""
from __future__ import annotations

import base64
import binascii
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import validate_profile as profile


def tiny_png() -> bytes:
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", binascii.crc32(kind + data) & 0xffffffff)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(b"\x00\x12\x34\x56\xff"))
        + chunk(b"IEND", b"")
    )


class EmbeddedArtworkPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for relative in profile.REQUIRED_PATHS:
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("", encoding="utf-8")
        (self.root / "README.md").write_text(
            "\n".join(sorted(profile.REQUIRED_REPOSITORY_LINKS))
            + "\nhttps://www.alberttansinhon.com/\n[Policy](docs/PORTFOLIO_VISIBILITY_POLICY.md)\n",
            encoding="utf-8",
        )
        self.png = tiny_png()
        (self.root / "assets/sparks-retro.png").write_bytes(self.png)
        self.uri = "data:image/png;base64," + base64.b64encode(self.png).decode("ascii")
        self.scope = patch.object(profile, "ROOT", self.root)
        self.scope.start()
        self.addCleanup(self.scope.stop)
        self.images('<image href="' + self.uri + '"/>')

    def images(self, markup: str) -> None:
        text = (
            '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">'
            '<title>Sparks test</title><desc>Artwork validation fixture.</desc>'
            + markup + '</svg>'
        )
        for name in ("persona-template.svg", "research-header.svg", "research-header-static.svg"):
            (self.root / "assets" / name).write_text(text, encoding="utf-8")

    def test_exact_committed_png_is_allowed(self) -> None:
        self.assertEqual([], profile.validate())

    def test_xlink_and_local_fragments_remain_allowed(self) -> None:
        self.images('<image xlink:href="' + self.uri + '"/><use href="#local"/>')
        self.assertEqual([], profile.validate())

    def test_external_and_other_data_references_are_rejected(self) -> None:
        for uri in ("https://example.com/robot.png", "../robot.png",
                    "data:image/svg+xml;base64,PHN2Zy8+", "data:text/html;base64,PGgxLz4=",
                    "data:image/png;base64,%%%"):
            with self.subTest(uri=uri):
                self.images('<image href="' + uri + '"/>')
                self.assertTrue(profile.validate())

    def test_data_uri_on_other_element_is_rejected(self) -> None:
        self.images('<a href="' + self.uri + '"/>')
        self.assertTrue(profile.validate())

    def test_different_png_bytes_are_rejected(self) -> None:
        (self.root / "assets/sparks-retro.png").write_bytes(self.png + b"different")
        self.assertTrue(profile.validate())

    def test_signature_is_required_even_when_bytes_match(self) -> None:
        bad = b"not a PNG"
        (self.root / "assets/sparks-retro.png").write_bytes(bad)
        self.images('<image href="data:image/png;base64,' + base64.b64encode(bad).decode("ascii") + '"/>')
        self.assertTrue(profile.validate())

    def test_missing_canonical_artwork_is_reported(self) -> None:
        (self.root / "assets/sparks-retro.png").unlink()
        self.assertTrue(profile.validate())

    def test_active_content_remains_rejected(self) -> None:
        for extra in ('<script/>', '<image onload="alert(1)" href="' + self.uri + '"/>',
                      '<style>@import "https://example.com/style.css";</style>'):
            with self.subTest(extra=extra):
                self.images('<image href="' + self.uri + '"/>' + extra)
                self.assertTrue(profile.validate())


if __name__ == "__main__":
    unittest.main()
