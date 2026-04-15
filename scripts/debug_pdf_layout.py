#!/usr/bin/env python3

from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    try:
        import fitz
    except ImportError:
        print("Requires: pip install pymupdf", file=sys.stderr)
        return 1

    pdf = Path(sys.argv[1] if len(sys.argv) > 1 else "fixtures/sample.pdf")
    page_i = int(sys.argv[2]) if len(sys.argv) > 2 else 0

    if not pdf.is_file():
        print(f"File not found: {pdf}", file=sys.stderr)
        return 1

    doc = fitz.open(pdf)
    if page_i < 0 or page_i >= len(doc):
        print(f"Page index out of range: {page_i}", file=sys.stderr)
        doc.close()
        return 1

    page = doc[page_i]
    print(f"=== {pdf.name} page {page_i + 1}/{len(doc)} size {page.rect} ===\n")

    blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]
    bi = 0
    for b in blocks:
        bi += 1
        if b.get("type") == 0:
            bbox = b["bbox"]
            lines = []
            for line in b.get("lines", []):
                for span in line.get("spans", []):
                    lines.append(span.get("text", ""))
            text = "".join(lines).replace("\n", "↵")[:200]
            print(f"[text {bi}] bbox={tuple(round(x, 1) for x in bbox)}")
            print(f"         preview: {text!r}")
        elif b.get("type") == 1:
            bbox = b["bbox"]
            print(f"[image {bi}] bbox={tuple(round(x, 1) for x in bbox)}")
        else:
            print(f"[other {bi}] type={b.get('type')} {repr(b)[:120]}")

    print("\n--- Page images (get_images / xref) ---")
    for img in page.get_images(full=True):
        xref = img[0]
        rects = page.get_image_rects(xref)
        for r in rects:
            print(f"  xref={xref} rect={r}")

    doc.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
