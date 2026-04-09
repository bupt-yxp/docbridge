"""PDF→DOCX 集成测试。"""

from __future__ import annotations

from pathlib import Path

import pytest

import docbridge.converters  # noqa: F401
from docbridge.base import ConversionOptions
from docbridge.converters.pdf_docx import PdfToDocxConverter


def test_minimal_pdf_to_docx(tmp_path: Path) -> None:
    fitz = pytest.importorskip("fitz")
    pdf = tmp_path / "minimal.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "DocBridge test", fontsize=12)
    doc.save(pdf)
    doc.close()

    out = tmp_path / "out.docx"
    PdfToDocxConverter().convert(pdf, out, ConversionOptions(render_dpi=200.0))
    assert out.is_file()
    assert out.stat().st_size > 500
