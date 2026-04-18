from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from docbridge.base import ConversionOptions
from docbridge.converters.docx_md import DocxToMdConverter
from docbridge.registry import get_converter


def test_docx_md_registered() -> None:
    from docbridge import list_supported_pairs

    assert ("docx", "md") in list_supported_pairs()
    assert get_converter("docx", "md").__name__ == "DocxToMdConverter"


@pytest.mark.skipif(not shutil.which("pandoc"), reason="pandoc not installed")
def test_docx_to_md_preserves_math_delimiters_roundtrip(tmp_path: Path) -> None:
    md1 = tmp_path / "in.md"
    md1.write_text("# Eq\n\nInline $a+b$ and display:\n\n$$x^2=1$$\n", encoding="utf-8")
    docx = tmp_path / "mid.docx"
    r = subprocess.run(
        ["pandoc", str(md1), "-f", "markdown+tex_math_dollars", "-o", str(docx)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0, r.stderr
    md2 = tmp_path / "out.md"
    DocxToMdConverter().convert(docx, md2, ConversionOptions())
    out = md2.read_text(encoding="utf-8")
    assert "a" in out and "b" in out
    assert "$" in out or "\\(" in out
