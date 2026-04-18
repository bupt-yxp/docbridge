from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path

from docbridge.base import ConversionOptions, Converter
from docbridge.converters.md_common import markdown_to_html_fragment, read_markdown
from docbridge.converters.md_html_docx import html_fragment_to_docx
from docbridge.converters.md_math import normalize_multiline_dollar_display_for_pandoc
from docbridge.converters.md_theme import TEXT_RGB
from docbridge.exceptions import ConversionFailedError
from docbridge.registry import register

logger = logging.getLogger(__name__)


def _pandoc_docx_apply_heading_text_color(path: Path) -> None:
    """
    Pandoc 生成的 docx 中标题使用 Word 内置「标题」样式，往往绑.theme 强调色（在 WPS/Word 中呈蓝色），
    与 md_theme 正文色 #222222 不一致。此处将标题样式及既有标题段落的 run 设为统一深灰。
    """
    from docx import Document
    from docx.shared import RGBColor

    doc = Document(str(path))
    rgb = RGBColor(*TEXT_RGB)
    for style_name in (
        "Heading 1",
        "Heading 2",
        "Heading 3",
        "Heading 4",
        "Heading 5",
        "Heading 6",
        "Title",
        "Subtitle",
    ):
        try:
            doc.styles[style_name].font.color.rgb = rgb
        except (KeyError, AttributeError, ValueError):
            continue
    for p in doc.paragraphs:
        name = p.style.name if p.style else ""
        if name.startswith("Heading") or name in ("Title", "Subtitle"):
            for r in p.runs:
                if r.text:
                    r.font.color.rgb = rgb
    doc.save(str(path))


def _pandoc_md_to_docx(source: Path, target: Path, resource_dir: Path) -> None:
    if not shutil.which("pandoc"):
        raise FileNotFoundError("pandoc")
    target.parent.mkdir(parents=True, exist_ok=True)
    md_text = read_markdown(source)
    # 与 Markdown→PDF（pandoc）一致：单独成行的 `$ … $` 显示块先规范为 `$$ … $$`，否则 Pandoc 会解坏 lim/tex_math_dollars
    md_text = normalize_multiline_dollar_display_for_pandoc(md_text)
    cmd = [
        "pandoc",
        "-",
        "-o",
        str(target.resolve()),
        "--from=markdown+tex_math_dollars",
        "--to=docx",
        f"--resource-path={resource_dir.resolve()}",
    ]
    r = subprocess.run(
        cmd,
        input=md_text,
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
    )
    if r.returncode != 0:
        err = (r.stderr or r.stdout or "").strip()
        raise RuntimeError(err or f"pandoc exited with code {r.returncode}")


@register("md", "docx")
class MdToDocxConverter(Converter):
    def convert(self, source: Path, target: Path, options: ConversionOptions | None = None) -> None:
        opts = options or ConversionOptions()
        source = source.resolve()
        target = target.resolve()
        if not source.is_file():
            raise ConversionFailedError(f"Source file not found: {source}")

        base_dir = opts.md_resource_base or source.parent
        backend = (opts.md_backend or "auto").lower()

        if backend == "auto":
            use_pandoc = shutil.which("pandoc") is not None
        elif backend == "pandoc":
            use_pandoc = True
        else:
            use_pandoc = False

        if use_pandoc:
            try:
                logger.info("pandoc: %s → %s", source, target)
                _pandoc_md_to_docx(source, target, base_dir)
                if target.is_file():
                    try:
                        _pandoc_docx_apply_heading_text_color(target)
                    except Exception as e:
                        logger.warning("pandoc docx 标题颜色与 md_theme 对齐失败（可忽略）: %s", e)
                    logger.info("Done (pandoc): %s", target.stat().st_size)
                    return
            except Exception as e:
                if backend == "pandoc":
                    raise ConversionFailedError(f"pandoc failed: {e}") from e
                logger.warning("pandoc unavailable or failed, using Python pipeline: %s", e)

        try:
            logger.info("Python pipeline (markdown→HTML→docx): %s → %s", source, target)
            md_text = read_markdown(source)
            html = markdown_to_html_fragment(md_text)
            doc = html_fragment_to_docx(html, base_dir)
            target.parent.mkdir(parents=True, exist_ok=True)
            doc.save(str(target))
        except Exception as e:
            raise ConversionFailedError(f"Markdown→DOCX failed: {e}") from e

        if not target.is_file():
            raise ConversionFailedError(f"Output was not created: {target}")
        logger.info("Done (Python): %s (%d bytes)", target, target.stat().st_size)
