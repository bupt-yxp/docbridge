"""DocBridge：可扩展文档格式转换库。"""

import docbridge.converters  # noqa: F401 — 注册内置转换器
from docbridge._version import __version__
from docbridge.api import convert_file, list_supported_pairs
from docbridge.base import ConversionOptions, Converter
from docbridge.registry import get_converter, iter_converters, register

__all__ = [
    "__version__",
    "ConversionOptions",
    "Converter",
    "convert_file",
    "get_converter",
    "iter_converters",
    "list_supported_pairs",
    "register",
]
