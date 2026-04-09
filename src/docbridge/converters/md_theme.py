"""
Markdown 导出「单一事实来源」：md2pdf（WeasyPrint）与 md2docx（python-docx）共用同一套版式参数。

与 CSS 对齐：A4、2cm 边距、正文字号/颜色、标题字号、图片 max-width:100%（按内容区宽度折算）。
"""

from __future__ import annotations

from pathlib import Path

# A4 210mm，左右各 2cm 边距 → 正文区域宽度（与 md2pdf 中 @page margin 一致）
_PAGE_WIDTH_MM = 210.0
_MARGIN_MM = 20.0
CONTENT_WIDTH_MM = _PAGE_WIDTH_MM - 2 * _MARGIN_MM
CONTENT_WIDTH_IN = CONTENT_WIDTH_MM / 25.4

# 与 MARKDOWN_CSS 中 body / h* / code 一致
BODY_PT = 11
CODE_PT = 9
HEADING_PT = {1: 20, 2: 16, 3: 13, 4: 12, 5: 11, 6: 11}
TEXT_RGB = (0x22, 0x22, 0x22)
LINE_HEIGHT = 1.45

# 浏览器/WeasyPrint 对 img 的默认像素密度参考（与 max-width:100% 组合时的常见行为）
REFERENCE_DPI = 96.0

# 与 Word 侧 DOCX_FONT_PRIMARY 对齐：中文无衬线优先，避免 PDF 用 DejaVu、中文落到衬体
FONT_STACK_CSS = (
    '"Microsoft YaHei", "Microsoft YaHei UI", "PingFang SC", '
    '"Noto Sans CJK SC", "Noto Sans", "DejaVu Sans", sans-serif'
)

# python-docx：主文与标题（eastAsia 与 ascii 一致）
DOCX_FONT_PRIMARY = "Microsoft YaHei"
DOCX_FONT_CODE = "Consolas"

MARKDOWN_CSS = f"""
@page {{ size: A4; margin: 2cm; }}
html {{
  font-family: {FONT_STACK_CSS};
}}
body {{
  font-family: {FONT_STACK_CSS};
  font-size: 11pt;
  line-height: 1.45;
  color: #222;
  font-synthesis: style;
}}
h1, h2, h3, h4, h5, h6 {{
  font-family: {FONT_STACK_CSS};
  font-weight: bold;
  color: #222;
}}
h1 {{ font-size: 20pt; }}
h2 {{ font-size: 16pt; }}
h3 {{ font-size: 13pt; }}
h4 {{ font-size: 12pt; }}
h5 {{ font-size: 11pt; }}
h6 {{ font-size: 11pt; }}
p, li, td, th, blockquote {{
  font-family: {FONT_STACK_CSS};
  color: #222;
}}
strong, b {{
  font-weight: bold;
}}
em, i {{
  font-style: oblique;
}}
table {{ border-collapse: collapse; width: 100%; margin: 0.6em 0; }}
th, td {{ border: 1px solid #999; padding: 4px 8px; color: #222; }}
pre {{ background: #f5f5f5; padding: 8px; font-size: 9pt; font-family: {FONT_STACK_CSS}; }}
code {{ font-family: "DejaVu Sans Mono", "Consolas", monospace; font-size: 9pt; }}
img {{ max-width: 100%; height: auto; }}
"""


def image_display_size_inches(path: str | Path) -> tuple[float, float]:
    """
    模拟 CSS「width 按像素显示、且不超过内容区宽度」：先按 DPI 换算英寸，再宽度封顶 CONTENT_WIDTH_IN。
    与 WeasyPrint 下 img{max-width:100%;height:auto} 在单列正文中的效果一致。
    """
    p = Path(path)
    from PIL import Image

    max_w = CONTENT_WIDTH_IN
    with Image.open(p) as im:
        w_px, h_px = im.size
        dpi_x, dpi_y = REFERENCE_DPI, REFERENCE_DPI
        dpi = im.info.get("dpi")
        if isinstance(dpi, tuple) and len(dpi) >= 2:
            if dpi[0] and dpi[0] > 0:
                dpi_x = float(dpi[0])
            if dpi[1] and dpi[1] > 0:
                dpi_y = float(dpi[1])

    w_in = w_px / dpi_x
    h_in = h_px / dpi_y
    if w_in > max_w:
        s = max_w / w_in
        w_in *= s
        h_in *= s
    return w_in, h_in


def image_display_size_inches_safe(path: str | Path) -> tuple[float, float]:
    """同 image_display_size_inches，失败时退回保守占位尺寸。"""
    try:
        return image_display_size_inches(path)
    except Exception:
        return (CONTENT_WIDTH_IN * 0.45, CONTENT_WIDTH_IN * 0.25)


def apply_a4_margins_2cm(document: object) -> None:
    """与 WeasyPrint @page margin: 2cm 对齐；装订线 0；页眉/页脚距边界用常见默认，减少正文上方异常留白。"""
    from docx.shared import Cm

    for section in document.sections:
        section.page_height = Cm(29.7)
        section.page_width = Cm(21.0)
        section.left_margin = Cm(2)
        section.right_margin = Cm(2)
        section.top_margin = Cm(2)
        section.bottom_margin = Cm(2)
        try:
            section.gutter = Cm(0)
        except Exception:
            pass
        try:
            section.header_distance = Cm(1.25)
            section.footer_distance = Cm(1.25)
        except Exception:
            pass
