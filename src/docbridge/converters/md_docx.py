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
        "--from=markdown+tex_math_dollars",
        "--to=docx",
        f"--resource-path={resource_dir.resolve()}",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, check=False)
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
