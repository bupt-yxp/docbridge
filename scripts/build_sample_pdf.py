#!/usr/bin/env python3
"""使用 PyMuPDF 从 fixtures 图片生成 sample.pdf（不依赖 pandoc）。"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIX = ROOT / "fixtures"


def main() -> int:
    try:
        import fitz
    except ImportError:
        print("需要 PyMuPDF（pdf2docx 已依赖）: pip install pymupdf", file=sys.stderr)
        return 1

    png = FIX / "test-diagram.png"
    jpg = FIX / "test-photo.jpg"
    if not png.is_file() or not jpg.is_file():
        print("请先运行: python scripts/generate_fixture_images.py", file=sys.stderr)
        return 1

    FIX.mkdir(parents=True, exist_ok=True)
    out = FIX / "sample.pdf"

    doc = fitz.open()
    page = doc.new_page(width=595, height=842)

    y = 50
    page.insert_text((50, y), "PDF→Word 保真测试", fontsize=16)
    y += 28
    page.insert_text((50, y), "普通段落：粗体/斜体 与 图片嵌入。", fontsize=11)
    y += 40

    r1 = fitz.Rect(50, y, 50 + 180, y + 120)
    page.insert_image(r1, filename=str(png))
    y += 130

    page.insert_text((50, y), "JPEG 照片：", fontsize=11)
    y += 16
    r2 = fitz.Rect(50, y, 50 + 220, y + 140)
    page.insert_image(r2, filename=str(jpg))

    doc.save(out)
    doc.close()
    print(f"已生成 {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
