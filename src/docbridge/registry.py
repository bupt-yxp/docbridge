from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING

from docbridge.exceptions import UnsupportedConversionError

if TYPE_CHECKING:
    from docbridge.base import Converter

_REGISTRY: dict[tuple[str, str], type[Converter]] = {}


def register(source_format: str, target_format: str):
    """装饰器：注册转换器类。"""

    def decorator(cls: type[Converter]) -> type[Converter]:
        key = (source_format.lower(), target_format.lower())
        if key in _REGISTRY:
            raise ValueError(f"转换器已注册: {source_format} → {target_format}")
        _REGISTRY[key] = cls
        cls.source_format = source_format.lower()
        cls.target_format = target_format.lower()
        return cls

    return decorator


def get_converter(source_format: str, target_format: str) -> type[Converter]:
    key = (source_format.lower(), target_format.lower())
    cls = _REGISTRY.get(key)
    if cls is None:
        raise UnsupportedConversionError(
            f"不支持: {source_format} → {target_format}。使用 `docbridge list-formats` 查看已注册组合。"
        )
    return cls


def iter_converters() -> Iterator[tuple[tuple[str, str], type[Converter]]]:
    yield from _REGISTRY.items()
