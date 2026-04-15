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
    pdf_match_page_margins: bool = False
    pdf_cjk_autospace_fix: bool = True
    pdf_convert_float_images_to_inline: bool = True
    pdf_patch_floating_anchors: bool = False
    pdf_trim_leading_empty_paragraphs: bool = True
    pdf_clear_first_paragraph_space_before: bool = True
    pdf_float_image_ignorable_gap: float | None = None
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
