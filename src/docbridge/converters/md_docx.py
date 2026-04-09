"""Markdown → DOCX（Pandoc 优先可选，否则 Python HTML 管线）。"""

from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path

from docbridge.base import ConversionOptions, Converter
from docbridge.converters.md_common import markdown_to_html_fragment, read_markdown
from docbridge.converters.md_html_docx import html_fragment_to_docx
from docbridge.exceptions import ConversionFailedError
from docbridge.registry import register

logger = logging.getLogger(__name__)


def _pandoc_md_to_docx(source: Path, target: Path, resource_dir: Path) -> None:
    if not shutil.which("pandoc"):
        raise FileNotFoundError("pandoc")
    target.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "pandoc",
        str(source.resolve()),
        "-o",
        str(target.resolve()),
        "--from=markdown",
        "--to=docx",
        f"--resource-path={resource_dir.resolve()}",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if r.returncode != 0:
        err = (r.stderr or r.stdout or "").strip()
        raise RuntimeError(err or f"pandoc 退出码 {r.returncode}")


@register("md", "docx")
class MdToDocxConverter(Converter):
    """Markdown → Word。auto：若系统存在 pandoc 则优先使用，否则用 Python 解析。"""

    def convert(self, source: Path, target: Path, options: ConversionOptions | None = None) -> None:
        opts = options or ConversionOptions()
        source = source.resolve()
        target = target.resolve()
        if not source.is_file():
            raise ConversionFailedError(f"源文件不存在: {source}")

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
                logger.info("使用 pandoc: %s → %s", source, target)
                _pandoc_md_to_docx(source, target, base_dir)
                if target.is_file():
                    logger.info("完成 (pandoc): %s", target.stat().st_size)
                    return
            except Exception as e:
                if backend == "pandoc":
                    raise ConversionFailedError(f"pandoc 转换失败: {e}") from e
                logger.warning("pandoc 不可用或失败，回退 Python 管线: %s", e)

        try:
            logger.info("使用 Python 管线 (markdown→HTML→docx): %s → %s", source, target)
            md_text = read_markdown(source)
            html = markdown_to_html_fragment(md_text)
            doc = html_fragment_to_docx(html, base_dir)
            target.parent.mkdir(parents=True, exist_ok=True)
            doc.save(str(target))
        except Exception as e:
            raise ConversionFailedError(f"Markdown→DOCX 失败: {e}") from e

        if not target.is_file():
            raise ConversionFailedError(f"未生成输出: {target}")
        logger.info("完成 (Python): %s (%d bytes)", target, target.stat().st_size)
