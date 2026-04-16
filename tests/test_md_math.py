from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile

import pytest

from docbridge.base import ConversionOptions
from docbridge.converters.md_docx import MdToDocxConverter
from docbridge.converters.md_math import expand_math_tags_for_pdf, substitute_tex_delimiters


def test_substitute_tex_delimiters_inserts_placeholders() -> None:
    s = "Hi $x^2$ and $$a+b=c$$\n"
    out = substitute_tex_delimiters(s)
    assert "docbridge-math-inline" in out
    assert "docbridge-math-display" in out
    assert "$$" not in out
    assert "$x^2$" not in out


def test_md_to_docx_python_emits_omml(tmp_path: Path) -> None:
    md = tmp_path / "m.md"
    md.write_text("Inline $x^2+y^2=z^2$ and display:\n\n$$\\int_0^1 x\\,dx$$\n", encoding="utf-8")
    out = tmp_path / "m.docx"
    MdToDocxConverter().convert(md, out, ConversionOptions(md_backend="python"))
    with ZipFile(out) as z:
        xml = z.read("word/document.xml").decode()
    assert "m:oMath" in xml


def test_expand_math_for_pdf_inserts_svg(tmp_path: Path) -> None:
    pytest.importorskip("weasyprint")
    from docbridge.converters.md_common import markdown_to_html_fragment

    frag = markdown_to_html_fragment("$t$")
    expanded = expand_math_tags_for_pdf(frag)
    assert "<svg" in expanded.lower()
