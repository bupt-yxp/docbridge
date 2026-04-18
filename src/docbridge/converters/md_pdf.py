from __future__ import annotations

import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

from docbridge.base import ConversionOptions, Converter
from docbridge.converters.md_common import (
    markdown_to_html_fragment,
    read_markdown,
    wrap_html_document,
)
from docbridge.converters.md_math import (
    expand_math_tags_for_pdf,
    normalize_multiline_dollar_display_for_pandoc,
)
from docbridge.converters.md_theme import HEADING_PT, LINE_HEIGHT, MARKDOWN_CSS
from docbridge.exceptions import ConversionFailedError
from docbridge.registry import register

logger = logging.getLogger(__name__)

# tectonic：独立 TeX 发行版，conda-forge 可装，无需整套 TeX Live
_LATEX_ENGINES_PREFERENCE = ("xelatex", "lualatex", "tectonic", "pdflatex")


def _find_latex_pdf_engine() -> str | None:
    for name in _LATEX_ENGINES_PREFERENCE:
        if shutil.which(name):
            return name
    return None


def _pandoc_pdf_prereq_error(opts: ConversionOptions) -> str:
    """说明缺少 pandoc 还是缺少 PDF 引擎，并给出安装示例。"""
    lines = [
        "Markdown→PDF（pandoc）需要同时满足：",
        "  ① 可执行文件 pandoc",
        "  ② PDF 引擎：xelatex / lualatex / tectonic / pdflatex 之一（或 --md-pdf-pandoc-engine 指向的可执行文件）",
        "",
    ]
    pan = shutil.which("pandoc")
    if pan:
        lines.append(f"[√] pandoc → {pan}")
    else:
        lines.append("[×] 未在 PATH 中发现 pandoc")
        lines.append("    安装：sudo apt install pandoc")
        lines.append("      或：conda install -c conda-forge pandoc")
        lines.append("")

    if opts.md_pdf_pandoc_engine:
        eng = opts.md_pdf_pandoc_engine.strip()
        hit = shutil.which(eng)
        if hit:
            lines.append(f"[√] --md-pdf-pandoc-engine {eng!r} → {hit}")
        else:
            lines.append(f"[×] 未找到指定的引擎 {eng!r}（请检查 PATH 或安装对应 TeX）")
    else:
        fe = _find_latex_pdf_engine()
        if fe:
            lines.append(f"[√] 自动选用 PDF 引擎：{fe} → {shutil.which(fe)}")
        else:
            lines.append("[×] 未在 PATH 中发现 xelatex / lualatex / tectonic / pdflatex")
            lines.append("    （生成 PDF 必须由 LaTeX 或 tectonic 编译；仅安装 pandoc 不够）")
            lines.append("    安装示例（Ubuntu/Debian）：")
            lines.append("      sudo apt install texlive-xetex texlive-latex-extra fonts-noto-cjk fonts-noto")
            lines.append("    或轻量（conda）：conda install -c conda-forge tectonic")
            lines.append("    或完整：安装 TeX Live / MiKTeX，并确保 xelatex 在 PATH 中")

    lines.extend(
        [
            "",
            "若暂不安装 TeX，可改用：",
            "  docbridge convert --from md --to pdf 输入.md -o 输出.pdf --md-pdf-backend weasyprint",
            "（此时复杂 amsmath 公式由 matplotlib 渲染，能力有限。）",
        ]
    )
    return "\n".join(lines)


def _can_pandoc_md_to_pdf(opts: ConversionOptions) -> bool:
    if not shutil.which("pandoc"):
        return False
    if opts.md_pdf_pandoc_engine:
        return shutil.which(opts.md_pdf_pandoc_engine) is not None
    return _find_latex_pdf_engine() is not None


def _resolve_pdf_engine(opts: ConversionOptions) -> str:
    if opts.md_pdf_pandoc_engine:
        eng = opts.md_pdf_pandoc_engine.strip()
        if not shutil.which(eng):
            raise ConversionFailedError(
                f"指定的 LaTeX 引擎未在 PATH 中找到: {eng!r}（--md-pdf-pandoc-engine）"
            )
        return eng
    found = _find_latex_pdf_engine()
    if not found:
        raise ConversionFailedError(
            "未找到 LaTeX/PDF 引擎（xelatex / lualatex / tectonic / pdflatex）。"
            "请安装 TeX Live / MiKTeX，或使用 --md-pdf-backend weasyprint。"
        )
    return found


def _latex_baselineskip_pt(size_pt: int) -> int:
    """与 CSS line-height 接近的标题行距（含略大 leading）。"""
    return max(int(size_pt * LINE_HEIGHT + 0.5), size_pt + 2)


def _pandoc_pdf_titlesec_fragment() -> str:
    """
    与 md_theme / Python 管线 DOCX 的标题字号一致（Heading 级别对应 LaTeX section … subparagraph）。
    """
    h = HEADING_PT
    bs = _latex_baselineskip_pt
    section = h[1]
    subsection = h[2]
    subsubsection = h[3]
    paragraph = h[4]
    subparagraph = h[5]
    lines = [
        "% docbridge: align PDF headings with md_theme / md_html_docx",
        r"\usepackage{titlesec}",
        rf"\titleformat{{\section}}{{\bfseries\fontsize{{{section}pt}}{{{bs(section)}pt}}\selectfont}}{{\thesection}}{{0.45em}}{{}}",
        rf"\titleformat{{\subsection}}{{\bfseries\fontsize{{{subsection}pt}}{{{bs(subsection)}pt}}\selectfont}}{{\thesubsection}}{{0.45em}}{{}}",
        rf"\titleformat{{\subsubsection}}{{\bfseries\fontsize{{{subsubsection}pt}}{{{bs(subsubsection)}pt}}\selectfont}}{{\thesubsubsection}}{{0.45em}}{{}}",
        rf"\titleformat{{\paragraph}}{{\bfseries\fontsize{{{paragraph}pt}}{{{bs(paragraph)}pt}}\selectfont}}{{\theparagraph}}{{0.45em}}{{}}",
        rf"\titleformat{{\subparagraph}}{{\bfseries\fontsize{{{subparagraph}pt}}{{{bs(subparagraph)}pt}}\selectfont}}{{\thesubparagraph}}{{0.45em}}{{}}",
        # 与 Word 管线 _add_theme_heading 中 space_before / space_after 大致对齐
        r"\titlespacing*{\section}{0pt}{10pt}{6pt}",
        r"\titlespacing*{\subsection}{0pt}{8pt}{6pt}",
        r"\titlespacing*{\subsubsection}{0pt}{6pt}{6pt}",
        r"\titlespacing*{\paragraph}{0pt}{6pt}{6pt}",
        r"\titlespacing*{\subparagraph}{0pt}{6pt}{6pt}",
    ]
    return "\n".join(lines) + "\n"


def _pandoc_pdf_include_header_file(engine: str) -> Path:
    """
    生成 pandoc --include-in-header 片段：
    - xelatex / tectonic：xeCJK 中文断行（与现有逻辑一致）+ titlesec 标题样式
    - lualatex / pdflatex：仅 titlesec（字体仍由 -V mainfont 等控制）
    """
    fd, name = tempfile.mkstemp(prefix="docbridge-pdf-", suffix=".tex", text=True)
    parts: list[str] = []
    if engine in ("xelatex", "tectonic"):
        parts.append(
            "% docbridge: xeCJK — 中文合法断行；勿仅用 fontspec 主字体（易整段溢出）\n"
            "\\usepackage{xeCJK}\n"
            "\\setCJKmainfont{Noto Sans CJK SC}\n"
            "\\setCJKsansfont{Noto Sans CJK SC}\n"
            '\\XeTeXlinebreaklocale "zh"\n'
            "\\XeTeXlinebreakskip = 0pt plus 0.15em\n"
        )
    parts.append(_pandoc_pdf_titlesec_fragment())
    with open(fd, "w", encoding="utf-8") as f:
        f.write("".join(parts))
    return Path(name)


def _pandoc_md_to_pdf(source: Path, target: Path, resource_dir: Path, opts: ConversionOptions) -> None:
    engine = _resolve_pdf_engine(opts)
    target.parent.mkdir(parents=True, exist_ok=True)
    md_text = read_markdown(source)
    md_text = normalize_multiline_dollar_display_for_pandoc(md_text)
    cmd: list[str] = [
        "pandoc",
        "-",
        "-o",
        str(target.resolve()),
        "--from=markdown+tex_math_dollars",
        f"--pdf-engine={engine}",
        f"--resource-path={resource_dir.resolve()}",
        # 与 md_theme / Python 管线 DOCX / MARKDOWN_CSS 一致：A4、左右上下 2cm、11pt 正文、1.45 倍行距
        "-V",
        "geometry:margin=2cm",
        "-V",
        "papersize=a4",
        "-V",
        "fontsize=11pt",
        "-V",
        f"linestretch={LINE_HEIGHT}",
        "-V",
        "colorlinks=true",
        "-V",
        "linkcolor=black",
        "-V",
        "urlcolor=black",
        "-V",
        "citecolor=black",
    ]
    header = _pandoc_pdf_include_header_file(engine)
    cmd.extend(["--include-in-header", str(header)])
    if engine == "lualatex":
        cmd.extend(
            [
                "-V",
                "mainfont=Noto Sans CJK SC",
                "-V",
                "sansfont=Noto Sans CJK SC",
            ]
        )
        logger.warning(
            "Markdown→PDF 使用 lualatex：中文自动换行依赖环境；若仍溢出请改用 "
            "--md-pdf-pandoc-engine xelatex"
        )
    try:
        r = subprocess.run(
            cmd,
            input=md_text,
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )
    finally:
        try:
            header.unlink(missing_ok=True)
        except OSError:
            pass
    if r.returncode != 0:
        err = (r.stderr or r.stdout or "").strip()
        base = err or f"pandoc exited with code {r.returncode}"
        low = base.lower()
        if "ctexhook" in low or "ctex.sty" in low:
            base += (
                "\n\n若仍提示缺少 ctex / xeCJK：sudo apt install texlive-lang-chinese "
                "texlive-fonts-recommended"
            )
        if "xecjk" in low and ".sty" in low:
            base += (
                "\n\n缺少 xeCJK：sudo apt install texlive-lang-chinese  "
                "或 texlive-xetex（含 CJK 支持与断行）"
            )
        raise RuntimeError(base)


@register("md", "pdf")
class MdToPdfConverter(Converter):
    """
    Markdown → PDF。

    - **Pandoc + LaTeX**（`md_pdf_backend` 为 `pandoc`，或 `auto` 且系统存在 pandoc+LaTeX）：由 **真实 LaTeX** 排版，支持 `cases`、`pmatrix`、多行 `$$` 等；页边距、正文字号/行距、标题层级字号与 **`md_theme` / Python 管线 DOCX** 对齐（中文字体在 XeLaTeX 上为 Noto Sans CJK SC，与 CSS 栈接近；WPS「微软雅黑」需在本地自行换字体变量）。
    - **WeasyPrint + matplotlib**（`weasyprint` 或 `auto` 且无 LaTeX）：直接使用 `MARKDOWN_CSS`，与 `md_theme` 一致，但 mathtext **不支持** `\\begin{...}` 等 amsmath 环境。
    """

    def convert(self, source: Path, target: Path, options: ConversionOptions | None = None) -> None:
        opts = options or ConversionOptions()
        source = source.resolve()
        target = target.resolve()
        if not source.is_file():
            raise ConversionFailedError(f"Source file not found: {source}")

        base_dir = (opts.md_resource_base or source.parent).resolve()
        backend = (opts.md_pdf_backend or "auto").strip().lower()

        if backend == "pandoc":
            if not _can_pandoc_md_to_pdf(opts):
                raise ConversionFailedError(_pandoc_pdf_prereq_error(opts))
            try:
                logger.info("pandoc+LaTeX: %s → %s", source, target)
                _pandoc_md_to_pdf(source, target, base_dir, opts)
            except ConversionFailedError:
                raise
            except Exception as e:
                raise ConversionFailedError(f"Markdown→PDF（pandoc）失败: {e}") from e
            if not target.is_file():
                raise ConversionFailedError(f"Output was not created: {target}")
            logger.info("Done (pandoc): %s (%d bytes)", target, target.stat().st_size)
            return

        if backend == "auto" and _can_pandoc_md_to_pdf(opts):
            try:
                logger.info("pandoc+LaTeX (auto): %s → %s", source, target)
                _pandoc_md_to_pdf(source, target, base_dir, opts)
                if target.is_file():
                    logger.info("Done (pandoc): %s (%d bytes)", target, target.stat().st_size)
                    return
            except Exception as e:
                logger.warning("pandoc PDF 失败，回退 WeasyPrint：%s", e)

        if backend not in ("auto", "weasyprint"):
            raise ConversionFailedError(
                f"未知的 md_pdf_backend: {backend!r}（允许 auto | weasyprint | pandoc）"
            )

        try:
            from weasyprint import CSS, HTML
        except ImportError as e:
            raise ConversionFailedError(
                'Markdown→PDF（WeasyPrint）需要: pip install "docbridge[pdf]"'
            ) from e

        base_url = base_dir.as_uri() + "/"

        md_text = read_markdown(source)
        fragment = markdown_to_html_fragment(md_text)
        fragment = expand_math_tags_for_pdf(fragment)
        full_html = wrap_html_document(fragment, title=source.stem)

        target.parent.mkdir(parents=True, exist_ok=True)
        logger.info("WeasyPrint: %s → %s (base_url=%s)", source, target, base_url)

        try:
            wp_html = HTML(string=full_html, base_url=base_url)
            wp_html.write_pdf(target, stylesheets=[CSS(string=MARKDOWN_CSS)])
        except Exception as e:
            raise ConversionFailedError(f"Markdown→PDF failed: {e}") from e

        if not target.is_file():
            raise ConversionFailedError(f"Output was not created: {target}")
        logger.info("Done (WeasyPrint): %s (%d bytes)", target, target.stat().st_size)
