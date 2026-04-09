"""Markdown → DOCX（Python 管线）。"""

from __future__ import annotations

from pathlib import Path

import docbridge.converters  # noqa: F401
from docbridge.base import ConversionOptions
from docbridge.converters.md_docx import MdToDocxConverter


def test_md_to_docx_python(tmp_path: Path) -> None:
    md = tmp_path / "t.md"
    md.write_text("# T\n\n**bold** and *italic*.\n\n- a\n- b\n", encoding="utf-8")
    out = tmp_path / "t.docx"
    MdToDocxConverter().convert(md, out, ConversionOptions(md_backend="python"))
    assert out.is_file()
    assert out.stat().st_size > 2000
