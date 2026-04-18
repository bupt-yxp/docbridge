from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ConversionOptions:
    password: str | None = None
    render_dpi: float = 288.0
    start_page: int | None = None
    end_page: int | None = None
    page_indexes: list[int] | None = None
    ignore_page_error: bool = True
    multi_processing: bool = False
    verbose: bool = False
    skip_extension_check: bool = False
    md_backend: str = "auto"
    md_resource_base: Path | None = None
    pdf_postprocess: bool = True
    pdf_normalize_fonts: bool = True
    #: PDF→DOCX：将 Latin Modern Math / CMSY 等 TeX 数学轮廓字体映射为 Cambria Math，减轻 WPS/Office 未装 TeX 字体时的 □
    pdf_remap_tex_math_fonts: bool = True
    #: PDF→DOCX（pdf2docx）：解析「格子表 / 流式表」。LaTeX 公式页易被误判为表格，公式碎片进单元格；默认 False。
    #: 若源 PDF 以真表格为主、需还原表格结构，请改 True（可 CLI --pdf-parse-tables）。
    pdf_parse_lattice_table: bool = False
    pdf_parse_stream_table: bool = False
    pdf_match_page_margins: bool = False
    pdf_cjk_autospace_fix: bool = True
    pdf_convert_float_images_to_inline: bool = True
    pdf_patch_floating_anchors: bool = False
    pdf_trim_leading_empty_paragraphs: bool = True
    pdf_clear_first_paragraph_space_before: bool = True
    pdf_float_image_ignorable_gap: float | None = None
    #: PDF→DOCX：指定与 PDF 同源的 `.md` 时 **改走 Markdown→DOCX**，以生成 **Word 原生公式(OMML)**。
    #: pdf2docx 无法从 PDF 恢复可编辑公式。未指定时若 `pdf_auto_use_sibling_markdown` 为 True，且存在与 PDF 同名的 `.md`，则自动使用。
    pdf_companion_md: Path | None = None
    pdf_auto_use_sibling_markdown: bool = True
    #: DOCX→Markdown（Pandoc）：输出格式，默认带 `tex_math_dollars` 以输出可逆的 LaTeX 数学
    docx_md_pandoc_to: str = "markdown+tex_math_dollars"
    #: DOCX→Markdown：是否 `--extract-media` 到 `<输出名>_media/`
    docx_extract_media: bool = True
    #: Markdown→PDF：`auto` 在检测到 pandoc+LaTeX 时走 **Pandoc→PDF**（完整 LaTeX 数学）；否则 **WeasyPrint+matplotlib**
    md_pdf_backend: str = "auto"
    #: Markdown→PDF（pandoc 路径）：`--pdf-engine`，默认自动选 xelatex / lualatex / pdflatex
    md_pdf_pandoc_engine: str | None = None
    #: DOCX→PDF：`auto` 优先 LibreOffice（无需 TeX），失败或无 LO 时再 pandoc+LaTeX；亦可强制 `pandoc` / `libreoffice`
    docx_pdf_backend: str = "auto"
    extra: dict[str, Any] = field(default_factory=dict)


class Converter(ABC):
    source_format: str
    target_format: str

    @abstractmethod
    def convert(self, source: Path, target: Path, options: ConversionOptions | None = None) -> None:
        ...

    @classmethod
    def describe(cls) -> str:
        return f"{cls.source_format} → {cls.target_format}"
