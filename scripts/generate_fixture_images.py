#!/usr/bin/env python3
"""生成 fixtures 内测试用 PNG/JPEG（需 Pillow）。"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIX = ROOT / "fixtures"


def main() -> int:
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print("请安装 Pillow: pip install Pillow", file=sys.stderr)
        return 1

    FIX.mkdir(parents=True, exist_ok=True)

    # 线条清晰的小图（PNG，透明底）
    w, h = 240, 160
    img = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([10, 10, w - 10, h - 10], outline=(0, 80, 200, 255), width=3)
    d.line([20, h // 2, w - 20, h // 2], fill=(200, 40, 40, 255), width=2)
    png_path = FIX / "test-diagram.png"
    img.save(png_path, "PNG")
    print(f"写入 {png_path}")

    # 简单照片风格 JPEG
    photo = Image.new("RGB", (320, 240), (40, 60, 90))
    pd = ImageDraw.Draw(photo)
    for i in range(0, 320, 8):
        pd.line([(i, 0), (i, 240)], fill=(90 + i // 8, 120, 160))
    jpg_path = FIX / "test-photo.jpg"
    photo.save(jpg_path, "JPEG", quality=92)
    print(f"写入 {jpg_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
