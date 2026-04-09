"""统一转换进度条：任意已注册格式组合在 `convert_file` 中均使用 tqdm。"""

from __future__ import annotations

import sys
from collections.abc import Generator
from contextlib import contextmanager

from tqdm import tqdm


@contextmanager
def conversion_tqdm(source_format: str, target_format: str) -> Generator[None, None, None]:
    """在转换期间显示 tqdm。

    * ``pdf → docx``：由 ``PdfToDocxConverter`` 内嵌的 pdf2docx 日志驱动条展示，此处不再套外层，避免双进度条。
    * 其它组合：单步进度条（整次转换计 1 步）。
    """
    src = source_format.lower().strip()
    tgt = target_format.lower().strip()
    if src == "pdf" and tgt == "docx":
        yield
        return

    desc = f"{src} → {tgt}"
    pbar = tqdm(
        total=1,
        desc=desc,
        unit="步",
        file=sys.stderr,
        dynamic_ncols=True,
    )
    try:
        yield
    finally:
        pbar.update(1)
        pbar.close()
