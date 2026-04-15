from __future__ import annotations

import pytest

from docbridge.base import ConversionOptions
from docbridge.converters.md_pdf import MdToPdfConverter


def test_md_to_pdf_weasyprint(tmp_path):
    pytest.importorskip("weasyprint")
    md = tmp_path / "t.md"
    md.write_text("# H\n\nHello **world**.\n", encoding="utf-8")
    out = tmp_path / "t.pdf"
    MdToPdfConverter().convert(md, out, ConversionOptions())
    assert out.is_file()
    assert out.stat().st_size > 100
