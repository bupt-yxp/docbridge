"""转换期间按 verbose 控制第三方库的日志级别，避免与 tqdm 混杂刷屏。"""

from __future__ import annotations

import logging
from collections.abc import Generator
from contextlib import contextmanager

# fontTools 子集化、WeasyPrint/CSS 等；非 verbose 时抑制 INFO/DEBUG
_QUIET_LOGGERS = (
    "fontTools",
    "fontTools.subset",
    "fontTools.subset.timer",
    "fontTools.ttLib",
    "weasyprint",
    "cssselect2",
    "pyphen",
    "PIL",
)


@contextmanager
def conversion_logging_context(verbose: bool) -> Generator[None, None, None]:
    """verbose 为 False 时将上述 logger 提到 WARNING，避免字体子集化等日志打断 tqdm。"""
    if verbose:
        yield
        return
    saved: dict[str, int] = {}
    for name in _QUIET_LOGGERS:
        lg = logging.getLogger(name)
        saved[name] = lg.level
        lg.setLevel(logging.WARNING)
    try:
        yield
    finally:
        for name, level in saved.items():
            logging.getLogger(name).setLevel(level)
