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
    return max(dpi / 72.0, 0.1)


@register("pdf", "docx")
class PdfToDocxConverter(Converter):
    def convert(self, source: Path, target: Path, options: ConversionOptions | None = None) -> None:
        opts = options or ConversionOptions()
        source = source.resolve()
        target = target.resolve()
        if not source.is_file():
            raise ConversionFailedError(f"Source file not found: {source}")

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
            "PDF→DOCX: %s → %s (clip_image_res_ratio=%.3f, ~%.0f dpi)",
            source,
            target,
            kwargs["clip_image_res_ratio"],
            opts.render_dpi,
        )

        try:
            cv = Pdf2DocxConverter(str(source), password=opts.password)
        except Exception as e:
            raise ConversionFailedError(f"Cannot open PDF: {e}") from e

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
            raise ConversionFailedError(f"Conversion failed: {e}") from e
        finally:
            cv.close()

        if not target.is_file():
            raise ConversionFailedError(f"Output file was not created: {target}")

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
                logger.warning("PDF→DOCX postprocess incomplete (disable with pdf_postprocess=False): %s", e)

        logger.info("Done: %s (%d bytes)", target, target.stat().st_size)
