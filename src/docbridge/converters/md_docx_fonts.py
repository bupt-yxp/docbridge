from __future__ import annotations

from docx.oxml import OxmlElement
from docx.oxml.ns import qn

from docbridge.converters.md_theme import DOCX_FONT_CODE, DOCX_FONT_PRIMARY

# Word/WPS 通常附带；TeX 提取的 Latin Modern Math 在未装 TeX 的机器上易 □，可映射为此字体
DOCX_FONT_MATH_FALLBACK = "Cambria Math"


def apply_docx_run_font(run, font_name: str = DOCX_FONT_PRIMARY) -> None:
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


def apply_docx_math_fallback_font(run, font_name: str = DOCX_FONT_MATH_FALLBACK) -> None:
    """将 PDF 提取的 TeX 数学轮廓字体替换为 Office 常见数学字体（与 WPS/Word 兼容）。"""
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
