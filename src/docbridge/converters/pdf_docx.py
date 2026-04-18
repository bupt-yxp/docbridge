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


def _resolve_pdf_companion_markdown(source: Path, opts: ConversionOptions) -> Path | None:
    """
    pdf2docx 只能抽取文字与坐标，无法生成 Word 可编辑公式(OMML)。
    若存在同源 Markdown，则改走 MdToDocxConverter。
    """
    if opts.pdf_companion_md is not None:
        p = Path(opts.pdf_companion_md).expanduser().resolve()
        if not p.is_file():
            raise ConversionFailedError(f"pdf_companion_md 不是有效文件: {p}")
        return p
    if opts.pdf_auto_use_sibling_markdown:
        sib = source.with_suffix(".md")
        if sib.is_file():
            return sib.resolve()
    return None


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

        md_src = _resolve_pdf_companion_markdown(source, opts)
        if md_src is not None:
            logger.info(
                "PDF→DOCX：改用同源 Markdown %s → DOCX（生成 Word 原生 OMML 公式）。"
                "pdf2docx 无法从 PDF 还原可编辑数学对象。",
                md_src,
            )
            from docbridge.converters.md_docx import MdToDocxConverter

            MdToDocxConverter().convert(md_src, target, opts)
            return

        logger.info(
            "PDF→DOCX：未检测到伴生 .md，使用 pdf2docx 版式提取（公式为片段文字，非 OMML）。"
            "需要可编辑公式请将同源 .md 与 PDF 同名放同目录，或设置 pdf_companion_md。",
        )

        target.parent.mkdir(parents=True, exist_ok=True)

        kwargs: dict = {
            "ignore_page_error": opts.ignore_page_error,
            "clip_image_res_ratio": _dpi_to_clip_ratio(opts.render_dpi),
            "parse_lattice_table": opts.pdf_parse_lattice_table,
            "parse_stream_table": opts.pdf_parse_stream_table,
        }
        if opts.pdf_float_image_ignorable_gap is not None:
            kwargs["float_image_ignorable_gap"] = opts.pdf_float_image_ignorable_gap
        kwargs.update(opts.extra)

        start = opts.start_page if opts.start_page is not None else 0
        end = opts.end_page
        pages = opts.page_indexes

        logger.info(
            "PDF→DOCX: %s → %s (clip_image_res_ratio=%.3f, ~%.0f dpi, "
            "parse_lattice_table=%s, parse_stream_table=%s)",
            source,
            target,
            kwargs["clip_image_res_ratio"],
            opts.render_dpi,
            kwargs["parse_lattice_table"],
            kwargs["parse_stream_table"],
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
                    remap_tex_math_fonts=opts.pdf_remap_tex_math_fonts,
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
