from __future__ import annotations

from pathlib import Path

from docbridge.converters.md_math import substitute_tex_delimiters


def read_markdown(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def markdown_to_html_fragment(md_text: str) -> str:
    import markdown

    md_text = substitute_tex_delimiters(md_text)
    return markdown.markdown(
        md_text,
        extensions=[
            "markdown.extensions.tables",
            "markdown.extensions.fenced_code",
            "markdown.extensions.nl2br",
            "markdown.extensions.sane_lists",
        ],
    )


def wrap_html_document(fragment: str, title: str = "") -> str:
    safe = title.replace("<", "").replace(">", "") if title else ""
    return (
        '<!DOCTYPE html><html lang="en"><head>'
        '<meta charset="utf-8"/>'
        f"<title>{safe}</title>"
        "</head><body>"
        f"{fragment}"
        "</body></html>"
    )


def resolve_resource_path(base_dir: Path, src: str | None) -> Path | None:
    if not src or src.startswith(("http://", "https://", "data:")):
        return None
    p = Path(src)
    if p.is_absolute():
        return p if p.is_file() else None
    cand = (base_dir / p).resolve()
    return cand if cand.is_file() else None
