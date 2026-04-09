"""对外稳定 API。"""

from __future__ import annotations

from pathlib import Path

import docbridge.converters  # noqa: F401 — 确保注册内置转换器
from docbridge.base import ConversionOptions
from docbridge.registry import get_converter, iter_converters


def convert_file(
    source: str | Path,
    target: str | Path,
    source_format: str,
    target_format: str,
    options: ConversionOptions | None = None,
) -> None:
    """根据已注册的格式组合执行转换。"""
    cls = get_converter(source_format, target_format)
    src = Path(source)
    dst = Path(target)
    converter = cls()
    converter.convert(src, dst, options)


def list_supported_pairs() -> list[tuple[str, str]]:
    """返回 (源格式, 目标格式) 列表。"""
    return sorted(k for k, _ in iter_converters())
