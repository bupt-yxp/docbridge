"""PDF → DOCX，基于 pdf2docx（PyMuPDF + python-docx）。"""

from __future__ import annotations

import logging
from pathlib import Path

from pdf2docx import Converter as Pdf2DocxConverter

from docbridge.base import ConversionOptions, Converter
from docbridge.converters._pdf2docx_progress import pdf2docx_tqdm_logging
from docbridge.converters.pdf_docx_postprocess import postprocess_pdf_docx
from docbridge.exceptions import ConversionFailedError
from docbridge.registry import register

logger = logging.getLogger(__name__)


def _dpi_to_clip_ratio(dpi: float) -> float:
    """pdf2docx 使用 clip_image_res_ratio，基准为 72dpi。"""
    return max(dpi / 72.0, 0.1)


@register("pdf", "docx")
class PdfToDocxConverter(Converter):
    """将 PDF 转为 Word；版式与图片尽量保留，受 PDF 与 docx 模型差异限制。"""

    def convert(self, source: Path, target: Path, options: ConversionOptions | None = None) -> None:
        opts = options or ConversionOptions()
        source = source.resolve()
        target = target.resolve()
        if not source.is_file():
            raise ConversionFailedError(f"源文件不存在: {source}")

        target.parent.mkdir(parents=True, exist_ok=True)

        kwargs: dict = {
            "ignore_page_error": opts.ignore_page_error,
            "clip_image_res_ratio": _dpi_to_clip_ratio(opts.render_dpi),
        }
        if opts.pdf_float_image_ignorable_gap is not None:
            kwargs["float_image_ignorable_gap"] = opts.pdf_float_image_ignorable_gap
        kwargs.update(opts.extra)

        start = opts.start_page if opts.start_page is not None else 0
        end = opts.end_page
        pages = opts.page_indexes

        logger.info(
            "开始 PDF→DOCX: %s → %s (等效 clip_image_res_ratio=%.3f, 约 %.0f dpi)",
            source,
            target,
            kwargs["clip_image_res_ratio"],
            opts.render_dpi,
        )

        try:
            cv = Pdf2DocxConverter(str(source), password=opts.password)
        except Exception as e:
            raise ConversionFailedError(f"无法打开 PDF: {e}") from e

        try:
            with pdf2docx_tqdm_logging():
                cv.convert(
                    str(target),
                    start=start,
                    end=end,
                    pages=pages,
                    **kwargs,
                )
        except Exception as e:
            raise ConversionFailedError(f"转换失败: {e}") from e
        finally:
            cv.close()

        if not target.is_file():
            raise ConversionFailedError(f"未生成输出文件: {target}")

        if opts.pdf_postprocess:
            try:
                postprocess_pdf_docx(
                    target,
                    normalize_fonts=opts.pdf_normalize_fonts,
                    match_margins=opts.pdf_match_page_margins,
                    cjk_autospace_fix=opts.pdf_cjk_autospace_fix,
                    convert_float_images_to_inline=opts.pdf_convert_float_images_to_inline,
                    patch_floating_anchors=opts.pdf_patch_floating_anchors,
                    trim_leading_empty_paragraphs=opts.pdf_trim_leading_empty_paragraphs,
                    clear_first_paragraph_space_before=opts.pdf_clear_first_paragraph_space_before,
                )
            except Exception as e:
                logger.warning("PDF→DOCX 后处理未完全成功（可关闭 pdf_postprocess）: %s", e)

        logger.info("完成: %s (%d bytes)", target, target.stat().st_size)
