#!/usr/bin/env python3
"""
调试：打印 PDF 页内文本块与图片的边界框及阅读顺序（PyMuPDF）。
用于分析「文字相对图片错位」时，源 PDF 里究竟是叠放还是上下排列。
用法: python scripts/debug_pdf_layout.py [path/to.pdf] [page_index]
"""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    try:
        import fitz
    except ImportError:
        print("需要: pip install pymupdf", file=sys.stderr)
        return 1

    pdf = Path(sys.argv[1] if len(sys.argv) > 1 else "fixtures/sample.pdf")
    page_i = int(sys.argv[2]) if len(sys.argv) > 2 else 0

    if not pdf.is_file():
        print(f"文件不存在: {pdf}", file=sys.stderr)
        return 1

    doc = fitz.open(pdf)
    if page_i < 0 or page_i >= len(doc):
        print(f"页码越界: {page_i}", file=sys.stderr)
        doc.close()
        return 1

    page = doc[page_i]
    print(f"=== {pdf.name} 第 {page_i + 1}/{len(doc)} 页 尺寸 {page.rect} ===\n")

    blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]
    bi = 0
    for b in blocks:
        bi += 1
        if b.get("type") == 0:  # text
            bbox = b["bbox"]
            lines = []
            for line in b.get("lines", []):
                for span in line.get("spans", []):
                    lines.append(span.get("text", ""))
            text = "".join(lines).replace("\n", "↵")[:200]
            print(f"[文本块 {bi}] bbox={tuple(round(x, 1) for x in bbox)}")
            print(f"         预览: {text!r}")
        elif b.get("type") == 1:  # image
            bbox = b["bbox"]
            print(f"[图片块 {bi}] bbox={tuple(round(x, 1) for x in bbox)}")
        else:
            print(f"[其它块 {bi}] type={b.get('type')} {repr(b)[:120]}")

    print("\n--- 页内图片对象（get_images / xref）---")
    for img in page.get_images(full=True):
        xref = img[0]
        rects = page.get_image_rects(xref)
        for r in rects:
            print(f"  xref={xref} rect={r}")

    doc.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
