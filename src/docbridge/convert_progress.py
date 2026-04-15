from __future__ import annotations

import sys
from collections.abc import Generator
from contextlib import contextmanager

from tqdm import tqdm


@contextmanager
def conversion_tqdm(source_format: str, target_format: str) -> Generator[None, None, None]:
    src = source_format.lower().strip()
    tgt = target_format.lower().strip()
    if src == "pdf" and tgt == "docx":
        yield
        return

    desc = f"{src} → {tgt}"
    pbar = tqdm(
        total=1,
        desc=desc,
        unit="step",
        file=sys.stderr,
        dynamic_ncols=True,
    )
    try:
        yield
    finally:
        pbar.update(1)
        pbar.close()
