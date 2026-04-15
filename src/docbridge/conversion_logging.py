from __future__ import annotations

import logging
from collections.abc import Generator
from contextlib import contextmanager

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
