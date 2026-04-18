from __future__ import annotations

from docbridge import list_supported_pairs
from docbridge.registry import get_converter


def test_pdf_docx_registered() -> None:
    pairs = list_supported_pairs()
    assert ("pdf", "docx") in pairs
    cls = get_converter("pdf", "docx")
    assert cls.__name__ == "PdfToDocxConverter"


def test_docx_pdf_registered() -> None:
    pairs = list_supported_pairs()
    assert ("docx", "pdf") in pairs
    cls = get_converter("docx", "pdf")
    assert cls.__name__ == "DocxToPdfConverter"
