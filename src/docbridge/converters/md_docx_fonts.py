"""Word run 字体：与 md_theme / WeasyPrint 使用同一主字体，并显式设置 eastAsia，避免中文落到宋体。"""

from __future__ import annotations

from docx.oxml import OxmlElement
from docx.oxml.ns import qn

from docbridge.converters.md_theme import DOCX_FONT_CODE, DOCX_FONT_PRIMARY


def apply_docx_run_font(run, font_name: str = DOCX_FONT_PRIMARY) -> None:
    """设置 ascii/hAnsi/eastAsia/cs，使中英混排与 PDF 的 sans-serif 栈一致。"""
    run.font.name = font_name
    r_pr = run._element.get_or_add_rPr()
    r_fonts = r_pr.rFonts
    if r_fonts is None:
        r_fonts = OxmlElement("w:rFonts")
        r_pr.insert(0, r_fonts)
    r_fonts.set(qn("w:ascii"), font_name)
    r_fonts.set(qn("w:hAnsi"), font_name)
    r_fonts.set(qn("w:eastAsia"), font_name)
    r_fonts.set(qn("w:cs"), font_name)


def apply_docx_code_font(run) -> None:
    """行内/块代码：等宽拉丁字体（与 CSS monospace 一致）。"""
    name = DOCX_FONT_CODE
    run.font.name = name
    r_pr = run._element.get_or_add_rPr()
    r_fonts = r_pr.rFonts
    if r_fonts is None:
        r_fonts = OxmlElement("w:rFonts")
        r_pr.insert(0, r_fonts)
    r_fonts.set(qn("w:ascii"), name)
    r_fonts.set(qn("w:hAnsi"), name)
    r_fonts.set(qn("w:eastAsia"), name)
    r_fonts.set(qn("w:cs"), name)
