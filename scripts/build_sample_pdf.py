#!/usr/bin/env python3

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIX = ROOT / "fixtures"


def main() -> int:
    try:
        import fitz
    except ImportError:
        print("Requires PyMuPDF: pip install pymupdf", file=sys.stderr)
        return 1

    png = FIX / "test-diagram.png"
    jpg = FIX / "test-photo.jpg"
    if not png.is_file() or not jpg.is_file():
        print("Run first: python scripts/generate_fixture_images.py", file=sys.stderr)
        return 1

    FIX.mkdir(parents=True, exist_ok=True)
    out = FIX / "sample.pdf"

    doc = fitz.open()
    page = doc.new_page(width=595, height=842)

    y = 50
    page.insert_text((50, y), "PDF to Word fidelity test", fontsize=16)
    y += 28
    page.insert_text((50, y), "Body: bold/italic and embedded images.", fontsize=11)
    y += 40

    r1 = fitz.Rect(50, y, 50 + 180, y + 120)
    page.insert_image(r1, filename=str(png))
    y += 130

    page.insert_text((50, y), "JPEG photo:", fontsize=11)
    y += 16
    r2 = fitz.Rect(50, y, 50 + 220, y + 140)
    page.insert_image(r2, filename=str(jpg))

    doc.save(out)
    doc.close()
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
