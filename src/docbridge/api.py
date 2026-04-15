from __future__ import annotations

import importlib
from pathlib import Path

from docbridge.base import ConversionOptions
from docbridge.conversion_logging import conversion_logging_context
from docbridge.convert_progress import conversion_tqdm
from docbridge.path_extensions import validate_path_extensions
from docbridge.registry import get_converter, iter_converters


def convert_file(
    source: str | Path,
    target: str | Path,
    source_format: str,
    target_format: str,
    options: ConversionOptions | None = None,
) -> None:
    opts = options or ConversionOptions()
    src = Path(source)
    dst = Path(target)
    if not opts.skip_extension_check:
        validate_path_extensions(src, dst, source_format, target_format)
    cls = get_converter(source_format, target_format)
    converter = cls()
    with conversion_logging_context(opts.verbose):
        with conversion_tqdm(source_format, target_format):
            converter.convert(src, dst, options)


def list_supported_pairs() -> list[tuple[str, str]]:
    return sorted(k for k, _ in iter_converters())


importlib.import_module("docbridge.converters")
