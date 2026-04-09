"""
pdf2docx 生成结果的后处理：与 md_theme 对齐的页边距/字体，并将浮动图改为行内图以减轻叠压。

pdf2docx 对「浮动」内容使用 wp:anchor + 页坐标，在 Word 中易与正文/表格叠压。
将 wp:anchor 转为 wp:inline 后，图片随段落流动，与 PDF 绝对坐标不完全一致，但可避免典型错位。
"""

from __future__ import annotations

import logging
from pathlib import Path

from docx import Document
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Pt
from docx.text.paragraph import Paragraph
from lxml import etree

from docbridge.converters.md_docx_fonts import apply_docx_run_font
from docbridge.converters.md_theme import apply_a4_margins_2cm

logger = logging.getLogger(__name__)

_W_DRAWING = qn("w:drawing")

# DrawingML / WordprocessingML
_WP_NS = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
_WP_ANCHOR = f"{{{_WP_NS}}}anchor"
_WP_INLINE = f"{{{_WP_NS}}}inline"

# anchor 内与坐标/环绕相关的子节点，行内图不需要
_SKIP_ANCHOR_CHILD = frozenset(
    {
        "simplePos",
        "positionH",
        "positionV",
        "wrapNone",
        "wrapTopAndBottom",
        "wrapSquare",
        "wrapTight",
        "wrapThrough",
    }
)

_INLINE_CHILD_ORDER = {"extent": 0, "effectExtent": 1, "docPr": 2, "cNvGraphicFramePr": 3, "graphic": 4}


def _paragraph_has_drawing(p_element) -> bool:
    """段落内是否含 w:drawing（python-docx 的 BaseOxmlElement.xpath 不支持 namespaces= 参数）。"""
    for node in p_element.iter():
        if node.tag == _W_DRAWING:
            return True
    return False


def _inline_child_sort_key(el) -> int:
    tag = etree.QName(el).localname
    return _INLINE_CHILD_ORDER.get(tag, 99)


def _iter_document_parts(doc: Document):
    """正文 + 各节页眉页脚（浮动图偶见）。"""
    yield doc.part
    seen = {id(doc.part)}
    for sec in doc.sections:
        for part in (getattr(sec.header, "part", None), getattr(sec.footer, "part", None)):
            if part is not None and id(part) not in seen:
                seen.add(id(part))
                yield part


def _convert_one_anchor_to_inline(anchor) -> None:
    """将单个 wp:anchor 替换为 wp:inline，保留 extent/docPr/graphic 等。"""
    parent = anchor.getparent()
    if parent is None:
        return

    to_move: list = []
    for child in list(anchor):
        tag = etree.QName(child).localname
        if tag in _SKIP_ANCHOR_CHILD:
            continue
        to_move.append(child)
    to_move.sort(key=_inline_child_sort_key)
    if not to_move:
        logger.warning("跳过空 anchor（无非定位子节点）")
        return

    nsmap = anchor.nsmap
    if not nsmap and parent is not None:
        nsmap = parent.nsmap

    inline = etree.Element(_WP_INLINE, nsmap=nsmap)
    for k in ("distT", "distB", "distL", "distR"):
        inline.set(k, "0")

    for el in to_move:
        anchor.remove(el)
        inline.append(el)

    parent.remove(anchor)
    parent.append(inline)


def _convert_all_anchors_to_inline(doc: Document) -> int:
    n = 0
    for part in _iter_document_parts(doc):
        root = part.element
        anchors = [el for el in root.iter(_WP_ANCHOR)]
        for anchor in anchors:
            try:
                _convert_one_anchor_to_inline(anchor)
                n += 1
            except Exception as e:
                logger.warning("anchor→inline 失败（已跳过该图）: %s", e)
    if n:
        logger.info("已将 %d 个 wp:anchor 转为 wp:inline（行内图，随段落排版）", n)
    return n


def _iter_paragraphs(doc: Document):
    for p in doc.paragraphs:
        yield p
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    yield p
    for sec in doc.sections:
        for part in (sec.header, sec.footer):
            if part is None:
                continue
            for p in part.paragraphs:
                yield p


def _apply_cjk_autospace_off(paragraph) -> None:
    """关闭中西文间自动间距，减少异常断行。"""
    p = paragraph._p
    p_pr = p.get_or_add_pPr()
    if p_pr.find(qn("w:autoSpaceDE")) is None:
        p_pr.insert(0, parse_xml(r'<w:autoSpaceDE {} w:val="0"/>'.format(nsdecls("w"))))
    if p_pr.find(qn("w:autoSpaceDN")) is None:
        p_pr.insert(0, parse_xml(r'<w:autoSpaceDN {} w:val="0"/>'.format(nsdecls("w"))))


def _normalize_text_runs(paragraph) -> None:
    for run in paragraph.runs:
        if not run.text:
            continue
        fn = run.font.name or ""
        if "Courier" in fn or "Consolas" in fn or "Mono" in fn:
            continue
        sz = run.font.size
        bold = run.bold
        italic = run.italic
        apply_docx_run_font(run)
        if sz is not None:
            run.font.size = sz
        if bold is not None:
            run.bold = bold
        if italic is not None:
            run.italic = italic


def _strip_leading_empty_paragraphs(doc: Document) -> int:
    """删除 document.body 开头的空段落（pdf2docx 常产生首行空行）。"""
    body = doc.element.body
    removed = 0
    while len(body) > 0:
        el = body[0]
        if el.tag != qn("w:p"):
            break
        p = Paragraph(el, doc)
        if p.text.strip() or _paragraph_has_drawing(el):
            break
        body.remove(el)
        removed += 1
    if removed:
        logger.info("已删除正文开头 %d 个空段落", removed)
    return removed


def _clear_first_paragraph_space_before(doc: Document) -> None:
    """首个正文段落段前距置 0，避免标题/首行上方额外留白。"""
    body = doc.element.body
    for el in body:
        if el.tag != qn("w:p"):
            continue
        p = Paragraph(el, doc)
        if p.text.strip() or _paragraph_has_drawing(el):
            p.paragraph_format.space_before = Pt(0)
            break


def _patch_floating_anchors_allow_overlap(doc: Document) -> int:
    """仅将 allowOverlap 置 0（不改为 inline 时的弱补救）。"""
    n = 0
    for part in _iter_document_parts(doc):
        for el in part.element.iter(_WP_ANCHOR):
            el.set("allowOverlap", "0")
            n += 1
    if n:
        logger.info("已调整 %d 个浮动图 anchor（allowOverlap=0）", n)
    return n


def postprocess_pdf_docx(
    path: Path,
    *,
    normalize_fonts: bool = True,
    match_margins: bool = True,
    cjk_autospace_fix: bool = True,
    convert_float_images_to_inline: bool = True,
    patch_floating_anchors: bool = False,
    trim_leading_empty_paragraphs: bool = True,
    clear_first_paragraph_space_before: bool = True,
) -> None:
    path = path.resolve()
    doc = Document(str(path))

    if match_margins:
        apply_a4_margins_2cm(doc)

    for p in _iter_paragraphs(doc):
        if cjk_autospace_fix:
            _apply_cjk_autospace_off(p)
        if normalize_fonts:
            _normalize_text_runs(p)

    if convert_float_images_to_inline:
        _convert_all_anchors_to_inline(doc)
    elif patch_floating_anchors:
        _patch_floating_anchors_allow_overlap(doc)

    if trim_leading_empty_paragraphs:
        _strip_leading_empty_paragraphs(doc)
    if clear_first_paragraph_space_before:
        _clear_first_paragraph_space_before(doc)

    doc.save(str(path))
