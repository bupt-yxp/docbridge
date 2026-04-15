from __future__ import annotations

from pathlib import Path

import pytest
from docx import Document as DocxDocument

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


def test_landscape_pdf_preserves_orientation_after_postprocess(tmp_path: Path) -> None:
    fitz = pytest.importorskip("fitz")
    pdf = tmp_path / "landscape.pdf"
    doc = fitz.open()
    page = doc.new_page(width=842, height=595)
    page.insert_text((72, 72), "landscape", fontsize=12)
    doc.save(pdf)
    doc.close()

    out = tmp_path / "out.docx"
    PdfToDocxConverter().convert(
        pdf,
        out,
        ConversionOptions(render_dpi=200.0, pdf_postprocess=True, pdf_match_page_margins=False),
    )
    assert out.is_file()
    d = DocxDocument(str(out))
    sec = d.sections[0]
    assert sec.page_width > sec.page_height


def test_pdf_match_md_theme_a4_forces_portrait(tmp_path: Path) -> None:
    fitz = pytest.importorskip("fitz")
    pdf = tmp_path / "landscape.pdf"
    doc = fitz.open()
    page = doc.new_page(width=842, height=595)
    page.insert_text((72, 72), "landscape", fontsize=12)
    doc.save(pdf)
    doc.close()

    out = tmp_path / "out_a4.docx"
    PdfToDocxConverter().convert(
        pdf,
        out,
        ConversionOptions(
            render_dpi=200.0,
            pdf_postprocess=True,
            pdf_match_page_margins=True,
        ),
    )
    d = DocxDocument(str(out))
    sec = d.sections[0]
    assert sec.page_height > sec.page_width
