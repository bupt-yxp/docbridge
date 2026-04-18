from __future__ import annotations

import logging
import sys
from pathlib import Path

import click

from docbridge import __version__
from docbridge.api import convert_file, list_supported_pairs
from docbridge.base import ConversionOptions
from docbridge.exceptions import ConversionFailedError, UnsupportedConversionError


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="[%(levelname)s] %(message)s",
        stream=sys.stderr,
    )


@click.group(invoke_without_command=True)
@click.version_option(__version__, prog_name="docbridge")
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Verbose logs (fontTools, WeasyPrint, etc.)",
)
@click.pass_context
def main(ctx: click.Context, verbose: bool) -> None:
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    _setup_logging(verbose)
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


def _cli_verbose(ctx: click.Context) -> bool:
    return bool(ctx.parent and ctx.parent.obj and ctx.parent.obj.get("verbose"))


@main.command("list-formats")
def list_formats() -> None:
    pairs = list_supported_pairs()
    if not pairs:
        click.echo("No converters registered.")
        return
    for src, dst in pairs:
        click.echo(f"  {src} → {dst}")


@main.command("convert")
@click.argument("input_file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option(
    "-o",
    "--output",
    "output_file",
    type=click.Path(path_type=Path),
    required=True,
    help="Output file path",
)
@click.option(
    "--from",
    "source_fmt",
    required=True,
    help="Source format (e.g. pdf)",
)
@click.option(
    "--to",
    "target_fmt",
    required=True,
    help="Target format (e.g. docx)",
)
@click.option("--password", default=None, help="PDF password if encrypted")
@click.option(
    "--dpi",
    default=288.0,
    type=float,
    show_default=True,
    help="Clip image resolution (maps to pdf2docx clip_image_res_ratio ≈ dpi/72)",
)
@click.option("--start", "start_page", type=int, default=None, help="Start page (0-based)")
@click.option("--end", "end_page", type=int, default=None, help="End page (exclusive)")
@click.option(
    "--pages",
    type=str,
    default=None,
    help="Comma-separated page indices (overrides --start/--end)",
)
@click.option(
    "--no-ignore-page-error",
    is_flag=True,
    help="Abort on single-page errors (default: ignore bad pages)",
)
@click.option(
    "--pdf-md-theme-a4-margins",
    is_flag=True,
    help="PDF→DOCX postprocess: force A4 portrait 2cm margins (md_theme). "
    "Default off: keep source PDF page size and orientation.",
)
@click.option(
    "--no-pdf-postprocess",
    is_flag=True,
    help="PDF→DOCX: disable postprocess (fonts/CJK, floating images). "
    "Default postprocess keeps PDF page size; see --pdf-md-theme-a4-margins",
)
@click.option(
    "--no-pdf-inline-images",
    is_flag=True,
    help="PDF→DOCX: keep floating anchors; weak fix only (allowOverlap=0), higher overlap risk",
)
@click.option(
    "--no-pdf-trim-leading",
    is_flag=True,
    help="PDF→DOCX: do not strip leading empty paragraphs or clear first-para space-before",
)
@click.option(
    "--float-image-gap",
    type=float,
    default=None,
    help="PDF→DOCX: pdf2docx float_image_ignorable_gap (default 5)",
)
@click.option(
    "--pdf-parse-tables",
    "pdf_parse_tables",
    is_flag=True,
    default=False,
    help="PDF→DOCX: 启用 pdf2docx 格子表+流式表解析（需从 PDF 还原表格时用）。"
    "默认关闭：含 LaTeX 公式的 PDF 常被误判成表格，公式碎进单元格。",
)
@click.option(
    "--pdf-companion-md",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="PDF→DOCX：指定与 PDF 同源的 Markdown；将改走 MD→DOCX 以生成 Word 可编辑公式(OMML)。",
)
@click.option(
    "--no-pdf-sibling-md",
    "no_pdf_sibling_md",
    is_flag=True,
    default=False,
    help="PDF→DOCX：禁用「与 PDF 同名的 .md」自动作为公式源（强制仅用 pdf2docx 提取）。",
)
@click.option(
    "--md-backend",
    type=click.Choice(["auto", "python", "pandoc"]),
    default="auto",
    help="Markdown→DOCX: auto prefers pandoc, else Python",
)
@click.option(
    "--md-pdf-backend",
    type=click.Choice(["auto", "weasyprint", "pandoc"]),
    default="auto",
    help="Markdown→PDF: auto uses pandoc+LaTeX when available; else WeasyPrint",
)
@click.option(
    "--md-pdf-pandoc-engine",
    type=str,
    default=None,
    help="Markdown→PDF: pandoc --pdf-engine (e.g. xelatex); default auto-detect",
)
@click.option(
    "--docx-pdf-backend",
    type=click.Choice(["auto", "pandoc", "libreoffice"]),
    default="auto",
    help="DOCX→PDF：auto 优先 LibreOffice，否则 pandoc+LaTeX（与 --md-pdf-pandoc-engine 共用）",
)
@click.pass_context
def convert_cmd(
    ctx: click.Context,
    input_file: Path,
    output_file: Path,
    source_fmt: str,
    target_fmt: str,
    password: str | None,
    dpi: float,
    start_page: int | None,
    end_page: int | None,
    pages: str | None,
    no_ignore_page_error: bool,
    pdf_md_theme_a4_margins: bool,
    no_pdf_postprocess: bool,
    no_pdf_inline_images: bool,
    no_pdf_trim_leading: bool,
    float_image_gap: float | None,
    pdf_parse_tables: bool,
    pdf_companion_md: Path | None,
    no_pdf_sibling_md: bool,
    md_backend: str,
    md_pdf_backend: str,
    md_pdf_pandoc_engine: str | None,
    docx_pdf_backend: str,
) -> None:
    page_indexes = None
    if pages:
        page_indexes = [int(p.strip()) for p in pages.split(",") if p.strip()]

    opts = ConversionOptions(
        verbose=_cli_verbose(ctx),
        password=password,
        render_dpi=dpi,
        start_page=start_page,
        end_page=end_page,
        page_indexes=page_indexes,
        ignore_page_error=not no_ignore_page_error,
        pdf_match_page_margins=pdf_md_theme_a4_margins,
        pdf_postprocess=not no_pdf_postprocess,
        pdf_float_image_ignorable_gap=float_image_gap,
        pdf_convert_float_images_to_inline=not no_pdf_inline_images,
        pdf_patch_floating_anchors=no_pdf_inline_images,
        pdf_trim_leading_empty_paragraphs=not no_pdf_trim_leading,
        pdf_clear_first_paragraph_space_before=not no_pdf_trim_leading,
        pdf_parse_lattice_table=pdf_parse_tables,
        pdf_parse_stream_table=pdf_parse_tables,
        pdf_companion_md=pdf_companion_md,
        pdf_auto_use_sibling_markdown=not no_pdf_sibling_md,
        md_backend=md_backend,
        md_pdf_backend=md_pdf_backend,
        md_pdf_pandoc_engine=md_pdf_pandoc_engine,
        docx_pdf_backend=docx_pdf_backend,
    )
    try:
        convert_file(input_file, output_file, source_fmt, target_fmt, opts)
    except (UnsupportedConversionError, ConversionFailedError) as e:
        raise click.ClickException(str(e)) from e


if __name__ == "__main__":
    main()
