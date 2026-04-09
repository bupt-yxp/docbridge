"""对外稳定 API。"""

from __future__ import annotations

from pathlib import Path

import docbridge.converters  # noqa: F401 — 确保注册内置转换器
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
    """根据已注册的格式组合执行转换。

    默认校验源/目标路径扩展名与 *source_format* / *target_format* 一致；
    若 ``options.skip_extension_check`` 为 True 则跳过该校验。
    """
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
    """返回 (源格式, 目标格式) 列表。"""
    return sorted(k for k, _ in iter_converters())
