from __future__ import annotations

import re
import shutil
from pathlib import Path
from zipfile import ZipFile

import pytest

from docbridge.base import ConversionOptions
from docbridge.converters.md_docx import MdToDocxConverter
from docx.oxml import parse_xml

from docbridge.converters.md_math import (
    decode_latex_data_attr,
    expand_math_tags_for_pdf,
    latex_to_omml_elements,
    normalize_multiline_dollar_display_for_pandoc,
    substitute_tex_delimiters,
)


def test_latex_bar_produces_parseable_omml() -> None:
    """mathml2omml 曾生成非良构 groupChr；修复后须能通过 python-docx parse_xml。"""
    for display in (True, False):
        xml = latex_to_omml_elements(r"\bar{f}=\frac{1}{b-a}", display=display)
        parse_xml(xml)


def test_substitute_tex_delimiters_inserts_placeholders() -> None:
    s = "Hi $x^2$ and $$a+b=c$$\n"
    out = substitute_tex_delimiters(s)
    assert "docbridge-math-inline" in out
    assert "docbridge-math-display" in out
    assert "$$" not in out
    assert "$x^2$" not in out


def test_normalize_multiline_dollar_for_pandoc_uses_double_dollar() -> None:
    s = "导数：\n$\nf'(x)=a\n$\n"
    out = normalize_multiline_dollar_display_for_pandoc(s)
    assert "$$\n" in out
    assert "\n$$\n" in out
    assert "f'(x)=a" in out


def test_substitute_multiline_single_dollar_display() -> None:
    s = "导数：\n$\nf'(x)=x\n$\n后文"
    out = substitute_tex_delimiters(s)
    assert "docbridge-math-display" in out
    m = re.search(r'data-latex="([^"]+)"', out)
    assert m
    assert "f'(x)=x" in decode_latex_data_attr(m.group(1))


@pytest.mark.skipif(shutil.which("pandoc") is None, reason="pandoc not installed")
def test_md_to_docx_pandoc_normalizes_multiline_display_dollar(tmp_path: Path) -> None:
    """多行单 `$...$` 须先规范为 `$$...$$`，否则 Pandoc 会解坏公式（见 normalize_multiline_dollar_display_for_pandoc）。"""
    md = tmp_path / "m.md"
    md.write_text(
        "标题\n\n$\nf'(x)=x\n$\n后文\n",
        encoding="utf-8",
    )
    out = tmp_path / "m.docx"
    MdToDocxConverter().convert(md, out, ConversionOptions(md_backend="pandoc"))
    with ZipFile(out) as z:
        xml = z.read("word/document.xml").decode()
    assert "m:oMath" in xml


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
