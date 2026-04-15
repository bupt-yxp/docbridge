from __future__ import annotations

import logging
from pathlib import Path

from docbridge.base import ConversionOptions, Converter
from docbridge.converters.md_common import (
    markdown_to_html_fragment,
    read_markdown,
    wrap_html_document,
)
from docbridge.converters.md_theme import MARKDOWN_CSS
from docbridge.exceptions import ConversionFailedError
from docbridge.registry import register

logger = logging.getLogger(__name__)


@register("md", "pdf")
class MdToPdfConverter(Converter):
    def convert(self, source: Path, target: Path, options: ConversionOptions | None = None) -> None:
        opts = options or ConversionOptions()
        source = source.resolve()
        target = target.resolve()
        if not source.is_file():
            raise ConversionFailedError(f"Source file not found: {source}")

        try:
            from weasyprint import CSS, HTML
        except ImportError as e:
            raise ConversionFailedError(
                'Markdown→PDF requires WeasyPrint: pip install "docbridge[pdf]"'
            ) from e

        base_dir = (opts.md_resource_base or source.parent).resolve()
        base_url = base_dir.as_uri() + "/"

        md_text = read_markdown(source)
        fragment = markdown_to_html_fragment(md_text)
        full_html = wrap_html_document(fragment, title=source.stem)

        target.parent.mkdir(parents=True, exist_ok=True)
        logger.info("WeasyPrint: %s → %s (base_url=%s)", source, target, base_url)

        try:
            wp_html = HTML(string=full_html, base_url=base_url)
            wp_html.write_pdf(target, stylesheets=[CSS(string=MARKDOWN_CSS)])
        except Exception as e:
            raise ConversionFailedError(f"Markdown→PDF failed: {e}") from e

        if not target.is_file():
            raise ConversionFailedError(f"Output was not created: {target}")
        logger.info("Done: %s (%d bytes)", target, target.stat().st_size)
