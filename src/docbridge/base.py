from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ConversionOptions:
    """各转换器可识别的通用选项；未知键由各实现自行忽略或校验。"""

    password: str | None = None
    # 与 pdf2docx 中 clip_image_res_ratio 对应：等效 DPI ≈ 72 * ratio（页面裁剪图）
    render_dpi: float = 288.0
    start_page: int | None = None
    end_page: int | None = None
    page_indexes: list[int] | None = None
    ignore_page_error: bool = True
    multi_processing: bool = False
    # Markdown：md→docx 后端 auto=有 pandoc 则用之，否则 Python；md_resource_base 默认同源文件目录
    md_backend: str = "auto"
    md_resource_base: Path | None = None
    # PDF→DOCX（pdf2docx）：后处理与可选调参
    pdf_postprocess: bool = True
    pdf_normalize_fonts: bool = True
    pdf_match_page_margins: bool = True
    pdf_cjk_autospace_fix: bool = True
    # 将 pdf2docx 的 wp:anchor 浮动图改为 wp:inline，随段落排版，显著减轻叠压/错位（损失绝对坐标）
    pdf_convert_float_images_to_inline: bool = True
    # 若未做 inline 化，仅将 allowOverlap 置 0（通常不如 inline 化有效）
    pdf_patch_floating_anchors: bool = False
    # 删除 pdf2docx 常在正文开头产生的空段落；首段段前距置 0
    pdf_trim_leading_empty_paragraphs: bool = True
    pdf_clear_first_paragraph_space_before: bool = True
    # 传给 pdf2docx；None 表示使用库默认 5.0（越大越易把邻近行判为「连通」，浮动图可能增多）
    pdf_float_image_ignorable_gap: float | None = None
    extra: dict[str, Any] = field(default_factory=dict)


class Converter(ABC):
    """格式转换器抽象基类。子类应通过 :func:`docbridge.registry.register` 注册。"""

    source_format: str
    target_format: str

    @abstractmethod
    def convert(self, source: Path, target: Path, options: ConversionOptions | None = None) -> None:
        """执行转换。实现中应记录日志并抛出 :class:`docbridge.exceptions.ConversionFailedError`。"""

    @classmethod
    def describe(cls) -> str:
        return f"{cls.source_format} → {cls.target_format}"
