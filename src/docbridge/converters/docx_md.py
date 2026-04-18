from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path

from docbridge.base import ConversionOptions, Converter
from docbridge.exceptions import ConversionFailedError
from docbridge.registry import register

logger = logging.getLogger(__name__)


def _pandoc_docx_to_md(
    source: Path,
    target: Path,
    *,
    to_format: str,
    extract_media: bool,
) -> None:
    if not shutil.which("pandoc"):
        raise FileNotFoundError("pandoc")
    target.parent.mkdir(parents=True, exist_ok=True)
    cmd: list[str | Path] = [
        "pandoc",
        str(source.resolve()),
        "--from=docx",
        f"--to={to_format}",
        "-o",
        str(target.resolve()),
    ]
    if extract_media:
        media_dir = target.parent / f"{target.stem}_media"
        media_dir.mkdir(parents=True, exist_ok=True)
        cmd.append(f"--extract-media={media_dir.resolve()}")
    r = subprocess.run([str(x) for x in cmd], capture_output=True, text=True, check=False)
    if r.returncode != 0:
        err = (r.stderr or r.stdout or "").strip()
        raise RuntimeError(err or f"pandoc exited with code {r.returncode}")


@register("docx", "md")
class DocxToMdConverter(Converter):
    """
    Word → Markdown via Pandoc.

    - **公式**：OMML 由 Pandoc/texmath 转为 TeX（通常为 `$...$` / `$$...$$`），与 MD→DOCX 管线中的数学约定一致。
    - **排版**：Markdown 以语义结构为主（标题、列表、表格、强调），无法还原 Word 的页眉页脚、分节、浮动体锚点与精确版心；复杂文本框/形状可能丢失或降级为 HTML/纯文本（取决于 Pandoc 版本与文档内容）。
    """

    def convert(self, source: Path, target: Path, options: ConversionOptions | None = None) -> None:
        opts = options or ConversionOptions()
        source = source.resolve()
        target = target.resolve()
        if not source.is_file():
            raise ConversionFailedError(f"Source file not found: {source}")

        to_fmt = str(opts.docx_md_pandoc_to or "markdown+tex_math_dollars").strip()
        extract = bool(opts.docx_extract_media)

        try:
            logger.info("pandoc docx→md: %s → %s (to=%s)", source, target, to_fmt)
            _pandoc_docx_to_md(source, target, to_format=to_fmt, extract_media=extract)
        except FileNotFoundError as e:
            raise ConversionFailedError(
                "DOCX→Markdown 需要系统已安装 pandoc（含 OMML 公式转 LaTeX）。"
                "参见 https://pandoc.org/installing.html"
            ) from e
        except Exception as e:
            raise ConversionFailedError(f"DOCX→Markdown failed: {e}") from e

        if not target.is_file():
            raise ConversionFailedError(f"Output was not created: {target}")
        logger.info("Done: %s (%d bytes)", target, target.stat().st_size)
