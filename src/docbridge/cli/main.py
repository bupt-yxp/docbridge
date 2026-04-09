"""docbridge CLI：可扩展格式转换。"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import click

import docbridge.converters  # noqa: F401
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
@click.option("-v", "--verbose", is_flag=True, help="调试日志")
@click.pass_context
def main(ctx: click.Context, verbose: bool) -> None:
    """DocBridge：文档格式转换（可扩展注册更多格式）。"""
    _setup_logging(verbose)
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@main.command("list-formats")
def list_formats() -> None:
    """列出已注册的 源→目标 格式组合。"""
    pairs = list_supported_pairs()
    if not pairs:
        click.echo("暂无已注册转换器。")
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
    help="输出文件路径",
)
@click.option(
    "--from",
    "source_fmt",
    required=True,
    help="源格式（如 pdf）",
)
@click.option(
    "--to",
    "target_fmt",
    required=True,
    help="目标格式（如 docx）",
)
@click.option("--password", default=None, help="PDF 密码（若加密）")
@click.option(
    "--dpi",
    default=288.0,
    type=float,
    show_default=True,
    help="页面裁剪图等效分辨率（映射到 pdf2docx clip_image_res_ratio≈dpi/72）",
)
@click.option("--start", "start_page", type=int, default=None, help="起始页（0-based）")
@click.option("--end", "end_page", type=int, default=None, help="结束页（不含）")
@click.option(
    "--pages",
    type=str,
    default=None,
    help="页索引列表，逗号分隔，如 0,2,5（优先级高于 --start/--end）",
)
@click.option("--no-ignore-page-error", is_flag=True, help="单页失败时中止（默认忽略坏页）")
@click.option(
    "--md-backend",
    type=click.Choice(["auto", "python", "pandoc"]),
    default="auto",
    help="Markdown→DOCX 时：auto 优先 pandoc，否则 Python",
)
def convert_cmd(
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
    md_backend: str,
) -> None:
    """通用转换：指定 --from / --to 格式。"""
    page_indexes = None
    if pages:
        page_indexes = [int(p.strip()) for p in pages.split(",") if p.strip()]

    opts = ConversionOptions(
        password=password,
        render_dpi=dpi,
        start_page=start_page,
        end_page=end_page,
        page_indexes=page_indexes,
        ignore_page_error=not no_ignore_page_error,
        md_backend=md_backend,
    )
    try:
        convert_file(input_file, output_file, source_fmt, target_fmt, opts)
    except (UnsupportedConversionError, ConversionFailedError) as e:
        raise click.ClickException(str(e)) from e


@main.command("pdf2docx")
@click.argument("input_pdf", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("-o", "--output", type=click.Path(path_type=Path), required=True, help="输出 .docx")
@click.option("--password", default=None, help="PDF 密码")
@click.option("--dpi", default=288.0, type=float, show_default=True, help="等效渲染 DPI")
@click.option("--start", "start_page", type=int, default=None)
@click.option("--end", "end_page", type=int, default=None)
@click.option("--pages", type=str, default=None, help="逗号分隔页索引")
@click.option("--no-ignore-page-error", is_flag=True)
@click.option(
    "--no-pdf-postprocess",
    is_flag=True,
    help="关闭 PDF→DOCX 后处理（与 md_theme 对齐的边距/字体、CJK 断行、浮动图锚点修正）",
)
@click.option(
    "--no-pdf-inline-images",
    is_flag=True,
    help="不将浮动图改为行内图；仅作弱补救（allowOverlap=0），叠压风险更高",
)
@click.option(
    "--no-pdf-trim-leading",
    is_flag=True,
    help="不删除正文开头空段落、不清除首段段前距（若仍见首行空行可对比此开关）",
)
@click.option(
    "--float-image-gap",
    type=float,
    default=None,
    help="pdf2docx 参数 float_image_ignorable_gap（默认 5）；可调以影响浮动图判定",
)
def pdf2docx_cmd(
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
) -> None:
    """快捷命令：PDF → Word。"""
    page_indexes = None
    if pages:
        page_indexes = [int(p.strip()) for p in pages.split(",") if p.strip()]
    opts = ConversionOptions(
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
    )
    try:
        convert_file(input_pdf, output, "pdf", "docx", opts)
    except (UnsupportedConversionError, ConversionFailedError) as e:
        raise click.ClickException(str(e)) from e


@main.command("md2docx")
@click.argument("input_md", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("-o", "--output", type=click.Path(path_type=Path), required=True, help="输出 .docx")
@click.option(
    "--md-backend",
    type=click.Choice(["auto", "python", "pandoc"]),
    default="auto",
    help="auto：有 pandoc 则用之；python：强制内置管线",
)
def md2docx_cmd(input_md: Path, output: Path, md_backend: str) -> None:
    """Markdown → Word。"""
    opts = ConversionOptions(md_backend=md_backend)
    try:
        convert_file(input_md, output, "md", "docx", opts)
    except (UnsupportedConversionError, ConversionFailedError) as e:
        raise click.ClickException(str(e)) from e


@main.command("md2pdf")
@click.argument("input_md", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("-o", "--output", type=click.Path(path_type=Path), required=True, help="输出 .pdf")
def md2pdf_cmd(input_md: Path, output: Path) -> None:
    """Markdown → PDF（需 pip install \"docbridge[pdf]\"，依赖 WeasyPrint）。"""
    opts = ConversionOptions()
    try:
        convert_file(input_md, output, "md", "pdf", opts)
    except (UnsupportedConversionError, ConversionFailedError) as e:
        raise click.ClickException(str(e)) from e


if __name__ == "__main__":
    main()
