from __future__ import annotations

from pathlib import Path

import pytest

from docbridge.api import convert_file
from docbridge.base import ConversionOptions
from docbridge.exceptions import ConversionFailedError
from docbridge.path_extensions import validate_path_extensions


def test_ok_pdf_to_docx(tmp_path: Path) -> None:
    a = tmp_path / "a.pdf"
    b = tmp_path / "b.docx"
    a.write_bytes(b"%PDF-1.4")
    validate_path_extensions(a, b, "pdf", "docx")


def test_bad_source_suffix(tmp_path: Path) -> None:
    a = tmp_path / "a.txt"
    b = tmp_path / "b.docx"
    a.write_text("x", encoding="utf-8")
    with pytest.raises(ConversionFailedError, match="Source extension"):
        validate_path_extensions(a, b, "md", "docx")


def test_bad_target_suffix(tmp_path: Path) -> None:
    a = tmp_path / "a.md"
    b = tmp_path / "b.txt"
    a.write_text("# x", encoding="utf-8")
    with pytest.raises(ConversionFailedError, match="Target extension"):
        validate_path_extensions(a, b, "md", "pdf")


def test_missing_suffix_source(tmp_path: Path) -> None:
    a = tmp_path / "README"
    b = tmp_path / "o.pdf"
    a.write_text("x", encoding="utf-8")
    with pytest.raises(ConversionFailedError, match="Source path has no extension"):
        validate_path_extensions(a, b, "md", "pdf")


def test_convert_file_respects_skip_extension_check(tmp_path: Path) -> None:
    md = tmp_path / "note.txt"
    out = tmp_path / "out.docx"
    md.write_text("# x\n", encoding="utf-8")
    convert_file(md, out, "md", "docx", ConversionOptions(md_backend="python", skip_extension_check=True))
    assert out.is_file()
