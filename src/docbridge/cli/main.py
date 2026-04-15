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
    "--md-backend",
    type=click.Choice(["auto", "python", "pandoc"]),
    default="auto",
    help="Markdown→DOCX: auto prefers pandoc, else Python",
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
    md_backend: str,
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
        md_backend=md_backend,
    )
    try:
        convert_file(input_file, output_file, source_fmt, target_fmt, opts)
    except (UnsupportedConversionError, ConversionFailedError) as e:
        raise click.ClickException(str(e)) from e


@main.command("pdf2docx")
@click.argument("input_pdf", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("-o", "--output", type=click.Path(path_type=Path), required=True, help="Output .docx")
@click.option("--password", default=None, help="PDF password")
@click.option("--dpi", default=288.0, type=float, show_default=True, help="Effective render DPI")
@click.option("--start", "start_page", type=int, default=None)
@click.option("--end", "end_page", type=int, default=None)
@click.option("--pages", type=str, default=None, help="Comma-separated page indices")
@click.option("--no-ignore-page-error", is_flag=True)
@click.option(
    "--no-pdf-postprocess",
    is_flag=True,
    help="Disable PDF→DOCX postprocess (fonts/CJK, floating images). "
    "Default postprocess keeps PDF page size; see --pdf-md-theme-a4-margins",
)
@click.option(
    "--pdf-md-theme-a4-margins",
    is_flag=True,
    help="Postprocess: force A4 portrait 2cm (md_theme). Default off to keep PDF page geometry",
)
@click.option(
    "--no-pdf-inline-images",
    is_flag=True,
    help="Keep floating anchors; weak fix only (allowOverlap=0), higher overlap risk",
)
@click.option(
    "--no-pdf-trim-leading",
    is_flag=True,
    help="Do not strip leading empty paragraphs or clear first-para space-before",
)
@click.option(
    "--float-image-gap",
    type=float,
    default=None,
    help="pdf2docx float_image_ignorable_gap (default 5)",
)
@click.pass_context
def pdf2docx_cmd(
    ctx: click.Context,
    input_pdf: Path,
    output: Path,
    password: str | None,
    dpi: float,
    start_page: int | None,
    end_page: int | None,
    pages: str | None,
    no_ignore_page_error: bool,
    no_pdf_postprocess: bool,
    no_pdf_inline_images: bool,
    no_pdf_trim_leading: bool,
    float_image_gap: float | None,
    pdf_md_theme_a4_margins: bool,
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
        pdf_postprocess=not no_pdf_postprocess,
        pdf_float_image_ignorable_gap=float_image_gap,
        pdf_convert_float_images_to_inline=not no_pdf_inline_images,
        pdf_patch_floating_anchors=no_pdf_inline_images,
        pdf_trim_leading_empty_paragraphs=not no_pdf_trim_leading,
        pdf_clear_first_paragraph_space_before=not no_pdf_trim_leading,
        pdf_match_page_margins=pdf_md_theme_a4_margins,
    )
    try:
        convert_file(input_pdf, output, "pdf", "docx", opts)
    except (UnsupportedConversionError, ConversionFailedError) as e:
        raise click.ClickException(str(e)) from e


@main.command("md2docx")
@click.argument("input_md", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("-o", "--output", type=click.Path(path_type=Path), required=True, help="Output .docx")
@click.option(
    "--md-backend",
    type=click.Choice(["auto", "python", "pandoc"]),
    default="auto",
    help="auto: pandoc if available; python: built-in pipeline only",
)
@click.pass_context
def md2docx_cmd(ctx: click.Context, input_md: Path, output: Path, md_backend: str) -> None:
    opts = ConversionOptions(verbose=_cli_verbose(ctx), md_backend=md_backend)
    try:
        convert_file(input_md, output, "md", "docx", opts)
    except (UnsupportedConversionError, ConversionFailedError) as e:
        raise click.ClickException(str(e)) from e


@main.command("md2pdf")
@click.argument("input_md", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("-o", "--output", type=click.Path(path_type=Path), required=True, help="Output .pdf")
@click.pass_context
def md2pdf_cmd(ctx: click.Context, input_md: Path, output: Path) -> None:
    opts = ConversionOptions(verbose=_cli_verbose(ctx))
    try:
        convert_file(input_md, output, "md", "pdf", opts)
    except (UnsupportedConversionError, ConversionFailedError) as e:
        raise click.ClickException(str(e)) from e


if __name__ == "__main__":
    main()
