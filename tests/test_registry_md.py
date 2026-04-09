"""注册表：md 格式。"""

from __future__ import annotations

import docbridge.converters  # noqa: F401
from docbridge import list_supported_pairs
from docbridge.registry import get_converter


def test_md_pairs_registered() -> None:
    pairs = list_supported_pairs()
    assert ("md", "docx") in pairs
    assert ("md", "pdf") in pairs
    assert get_converter("md", "docx").__name__ == "MdToDocxConverter"
    assert get_converter("md", "pdf").__name__ == "MdToPdfConverter"
