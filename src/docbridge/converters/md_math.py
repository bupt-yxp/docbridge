from __future__ import annotations

import base64
import logging
import re
from io import BytesIO

from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)

_DOC_INLINE_CLS = "docbridge-math docbridge-math-inline"
_DOC_DISPLAY_CLS = "docbridge-math docbridge-math-display"


def _is_dollar_escaped(s: str, dollar_index: int) -> bool:
    """True if the '$' at dollar_index is preceded by an odd number of backslashes."""
    k = dollar_index - 1
    n = 0
    while k >= 0 and s[k] == "\\":
        n += 1
        k -= 1
    return n % 2 == 1


def substitute_tex_delimiters(md_text: str) -> str:
    """
    Replace $...$, $$...$$, \\(...\\), \\[...\\] with raw HTML placeholders so that
    (1) underscores inside math are not parsed as Markdown emphasis, and
    (2) downstream can emit OMML (Word) or SVG (PDF).
    """
    text = md_text
    text = _replace_display_brackets(text)
    text = _replace_inline_parens(text)
    text = _replace_dollar_delims(text)
    return text


def _b64_encode(s: str) -> str:
    return base64.standard_b64encode(s.encode("utf-8")).decode("ascii")


def _wrap_display(latex: str) -> str:
    return f'\n\n<div class="{_DOC_DISPLAY_CLS}" data-latex="{_b64_encode(latex)}"></div>\n\n'


def _wrap_inline(latex: str) -> str:
    return f'<span class="{_DOC_INLINE_CLS}" data-latex="{_b64_encode(latex)}"></span>'


def _replace_display_brackets(text: str) -> str:
    pattern = re.compile(
        r"\\\[([\s\S]*?)\\\]",
        re.MULTILINE,
    )

    def repl(m: re.Match[str]) -> str:
        return _wrap_display(m.group(1).strip())

    return pattern.sub(repl, text)


def _replace_inline_parens(text: str) -> str:
    out: list[str] = []
    i, n = 0, len(text)
    while i < n:
        if i + 1 < n and text[i : i + 2] == "\\(":
            j = i + 2
            depth = 1
            while j + 1 < n:
                if text[j : j + 2] == "\\(":
                    depth += 1
                    j += 2
                    continue
                if text[j : j + 2] == "\\)":
                    depth -= 1
                    if depth == 0:
                        latex = text[i + 2 : j].strip()
                        out.append(_wrap_inline(latex))
                        i = j + 2
                        break
                    j += 2
                    continue
                j += 1
            else:
                out.append(text[i])
                i += 1
            continue
        out.append(text[i])
        i += 1
    return "".join(out)


def _replace_dollar_delims(text: str) -> str:
    out: list[str] = []
    i, n = 0, len(text)
    while i < n:
        if i + 1 < n and text[i : i + 2] == "$$" and not _is_dollar_escaped(text, i):
            j = i + 2
            found = False
            while j + 1 < n:
                if text[j : j + 2] == "$$" and not _is_dollar_escaped(text, j):
                    latex = text[i + 2 : j].strip()
                    out.append(_wrap_display(latex))
                    i = j + 2
                    found = True
                    break
                j += 1
            if not found:
                out.append(text[i])
                i += 1
            continue

        if text[i] == "$" and not _is_dollar_escaped(text, i):
            j = i + 1
            while j < n:
                if text[j] == "$" and not _is_dollar_escaped(text, j):
                    latex = text[i + 1 : j]
                    if "\n" in latex:
                        out.append(text[i])
                        i += 1
                        break
                    out.append(_wrap_inline(latex.strip()))
                    i = j + 1
                    break
                j += 1
            else:
                out.append(text[i])
                i += 1
            continue

        out.append(text[i])
        i += 1
    return "".join(out)


def decode_latex_data_attr(b64: str) -> str:
    return base64.standard_b64decode(b64.encode("ascii")).decode("utf-8")


def latex_to_omml_elements(latex: str, *, display: bool) -> str:
    """Return XML string: either oMathPara (display) or w:r wrapping m:oMath (inline)."""
    import latex2mathml.converter as lc
    import mathml2omml

    mml = lc.convert(latex, display="block" if display else "inline")
    omml = mathml2omml.convert(mml)
    m_ns = "http://schemas.openxmlformats.org/officeDocument/2006/math"
    w_ns = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    if display:
        return (
            f'<m:oMathPara xmlns:m="{m_ns}">'
            f"{omml}"
            "</m:oMathPara>"
        )
    return (
        f'<w:r xmlns:w="{w_ns}" xmlns:m="{m_ns}">'
        f"{omml}"
        "</w:r>"
    )


def append_omml_to_paragraph(paragraph, latex: str, *, display: bool) -> None:
    from docx.oxml import parse_xml

    xml = latex_to_omml_elements(latex, display=display)
    paragraph._p.append(parse_xml(xml))


def expand_math_tags_for_pdf(html_fragment: str) -> str:
    """Replace docbridge math placeholders with matplotlib-rendered SVG for WeasyPrint."""
    wrapped = f"<html><body>{html_fragment}</body></html>"
    soup = BeautifulSoup(wrapped, "html.parser")
    body = soup.body
    if not body:
        return html_fragment

    for el in body.find_all(class_=lambda c: bool(c) and "docbridge-math" in c):
        if not isinstance(el, Tag):
            continue
        tag = el
        b64 = tag.get("data-latex")
        if not b64:
            continue
        try:
            latex = decode_latex_data_attr(b64)
        except Exception:
            tag.replace_with(f"[invalid math: {b64[:20]}…]")
            continue
        display = "docbridge-math-display" in (tag.get("class") or [])
        svg_html = _latex_to_svg_html(latex, display=display)
        if svg_html is None:
            tag.replace_with(f"${latex}$")
            continue
        frag = BeautifulSoup(svg_html, "html.parser")
        tag.replace_with(frag)

    inner = "".join(str(c) for c in body.contents)
    return inner


def _latex_to_svg_html(latex: str, *, display: bool) -> str | None:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return None

    fontsize = 13 if display else 11
    pad = 0.12 if display else 0.06
    try:
        fig = plt.figure(figsize=(min(6.4, 0.35 + 0.018 * len(latex)), 0.45))
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis("off")
        ax.text(
            0.5,
            0.5,
            f"${latex}$",
            fontsize=fontsize,
            ha="center",
            va="center",
        )
        buf = BytesIO()
        fig.savefig(buf, format="svg", bbox_inches="tight", pad_inches=pad, transparent=True)
        plt.close(fig)
        svg = buf.getvalue().decode("utf-8")
    except Exception as e:
        logger.warning("matplotlib SVG math failed: %s", e)
        return None

    if display:
        return f'<div class="docbridge-math-svg docbridge-math-svg-display">{svg}</div>'
    return f'<span class="docbridge-math-svg docbridge-math-svg-inline">{svg}</span>'
