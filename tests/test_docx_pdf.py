from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from docx import Document as DocxDocument

from docbridge.base import ConversionOptions
from docbridge.converters.docx_pdf import DocxToPdfConverter
from docbridge.exceptions import ConversionFailedError


def _minimal_docx(path: Path) -> None:
    d = DocxDocument()
    d.add_paragraph("DocBridge docx→pdf test")
    d.save(str(path))


def test_docx_to_pdf_libreoffice_if_available(tmp_path: Path) -> None:
    if shutil.which("libreoffice") is None and shutil.which("soffice") is None:
        pytest.skip("no LibreOffice")
    src = tmp_path / "a.docx"
    out = tmp_path / "a.pdf"
    _minimal_docx(src)
    try:
        DocxToPdfConverter().convert(src, out, ConversionOptions(docx_pdf_backend="libreoffice"))
    except ConversionFailedError as e:
        # CI/沙箱常见：无法写 dconf、LO 用户配置等
        msg = str(e).lower()
        if "user installation" in msg or "cannot be started" in msg or "javaldx" in msg:
            pytest.skip(str(e))
        raise
    assert out.is_file()
    assert out.stat().st_size > 80


def test_docx_to_pdf_pandoc_if_available(tmp_path: Path) -> None:
    if shutil.which("pandoc") is None:
        pytest.skip("no pandoc")
    if not (shutil.which("xelatex") or shutil.which("lualatex") or shutil.which("tectonic")):
        pytest.skip("no LaTeX pdf engine")
    src = tmp_path / "b.docx"
    out = tmp_path / "b.pdf"
    _minimal_docx(src)
    DocxToPdfConverter().convert(src, out, ConversionOptions(docx_pdf_backend="pandoc"))
    assert out.is_file()
    assert out.stat().st_size > 80
