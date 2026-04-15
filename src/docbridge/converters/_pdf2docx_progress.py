from __future__ import annotations

import logging
import re
import sys
from collections.abc import Generator
from contextlib import contextmanager

from tqdm import tqdm

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
_PAGE_RE = re.compile(r"^\((\d+)/(\d+)\) Page (\d+)$")
_PHASE_RE = re.compile(r"\[(\d)/4\]")


def _strip_ansi(s: str) -> str:
    return ANSI_RE.sub("", s)


class _Pdf2DocxProgressFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if record.name != "root":
            return True
        if record.levelno != logging.INFO:
            return True
        msg = _strip_ansi(record.getMessage())
        if "Start to convert" in msg:
            return False
        if _PHASE_RE.search(msg):
            return False
        if _PAGE_RE.match(msg):
            return False
        if msg.startswith("Terminated in ") and msg.endswith("s."):
            return False
        return True


class _Pdf2DocxTqdmHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__(level=logging.INFO)
        self._pbar: tqdm | None = None

    def emit(self, record: logging.LogRecord) -> None:
        if record.name != "root" or record.levelno != logging.INFO:
            return
        msg = _strip_ansi(record.getMessage())

        m = _PAGE_RE.match(msg)
        if m:
            n = int(m.group(2))
            page = int(m.group(3))
            if self._pbar is None:
                self._pbar = tqdm(
                    total=2 * n,
                    desc="PDF→DOCX · pages",
                    unit="pg",
                    file=sys.stderr,
                    dynamic_ncols=True,
                )
            self._pbar.update(1)
            self._pbar.set_postfix(page=page)
            return

        pm = _PHASE_RE.search(msg)
        if pm and self._pbar is not None:
            phase = int(pm.group(1))
            names = {
                1: "open",
                2: "layout",
                3: "pages",
                4: "word",
            }
            self._pbar.set_description(f"PDF→DOCX · {names.get(phase, str(phase))}", refresh=False)
            return

    def close(self) -> None:
        if self._pbar is not None:
            self._pbar.close()
            self._pbar = None
        super().close()


@contextmanager
def pdf2docx_tqdm_logging() -> Generator[None, None, None]:
    root = logging.getLogger()
    tqdm_handler = _Pdf2DocxTqdmHandler()
    flt = _Pdf2DocxProgressFilter()

    for h in root.handlers:
        if isinstance(h, logging.StreamHandler) and not isinstance(h, _Pdf2DocxTqdmHandler):
            h.addFilter(flt)

    root.addHandler(tqdm_handler)
    try:
        yield
    finally:
        root.removeHandler(tqdm_handler)
        tqdm_handler.close()
        for h in root.handlers:
            if isinstance(h, logging.StreamHandler) and not isinstance(h, _Pdf2DocxTqdmHandler):
                h.removeFilter(flt)
