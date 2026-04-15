from __future__ import annotations

from pathlib import Path

from docbridge.exceptions import ConversionFailedError

_FORMAT_SUFFIXES: dict[str, tuple[str, ...]] = {
    "pdf": (".pdf",),
    "docx": (".docx",),
    "md": (".md", ".markdown", ".mdown", ".mkd"),
}


def _fmt_suffixes(fmt: str) -> tuple[str, ...] | None:
    return _FORMAT_SUFFIXES.get(fmt.lower().strip())


def _human_allowed(allowed: tuple[str, ...]) -> str:
    return ", ".join(allowed)


def validate_path_extensions(
    source: Path,
    target: Path,
    source_format: str,
    target_format: str,
) -> None:
    sf = source_format.lower().strip()
    tf = target_format.lower().strip()

    src_sfx = source.suffix.lower()
    if not src_sfx:
        raise ConversionFailedError(
            f"Source path has no extension; cannot match declared source format {sf!r}: {source}"
        )
    want_src = _fmt_suffixes(sf)
    if want_src is not None and src_sfx not in want_src:
        raise ConversionFailedError(
            f"Source extension does not match declared format {sf!r}: expected one of "
            f"{_human_allowed(want_src)}, got {src_sfx!r} ({source})"
        )

    tgt_sfx = target.suffix.lower()
    if not tgt_sfx:
        raise ConversionFailedError(
            f"Target path has no extension; cannot match declared target format {tf!r}: {target}"
        )
    want_tgt = _fmt_suffixes(tf)
    if want_tgt is not None and tgt_sfx not in want_tgt:
        raise ConversionFailedError(
            f"Target extension does not match declared format {tf!r}: expected one of "
            f"{_human_allowed(want_tgt)}, got {tgt_sfx!r} ({target})"
        )
