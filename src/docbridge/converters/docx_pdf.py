from __future__ import annotations

import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

from docbridge.base import ConversionOptions, Converter
from docbridge.converters.md_pdf import (
    _can_pandoc_md_to_pdf,
    _pandoc_pdf_prereq_error,
    _resolve_pdf_engine,
)
from docbridge.exceptions import ConversionFailedError
from docbridge.registry import register

logger = logging.getLogger(__name__)


def _xecjk_header_file_docx_pdf(engine: str) -> Path | None:
    """DOCX→PDF 经 pandoc→LaTeX 时，中文断行仍建议 xeCJK（与 md_pdf 一致）。"""
    if engine not in ("xelatex", "tectonic"):
        return None
    fd, name = tempfile.mkstemp(prefix="docbridge-docx-pdf-", suffix=".tex", text=True)
    with open(fd, "w", encoding="utf-8") as f:
        f.write(
            "\\usepackage{xeCJK}\n"
            "\\setCJKmainfont{Noto Sans CJK SC}\n"
            "\\setCJKsansfont{Noto Sans CJK SC}\n"
            '\\XeTeXlinebreaklocale "zh"\n'
            "\\XeTeXlinebreakskip = 0pt plus 0.15em\n"
        )
    return Path(name)


def _pandoc_docx_to_pdf(source: Path, target: Path, opts: ConversionOptions) -> None:
    engine = _resolve_pdf_engine(opts)
    target.parent.mkdir(parents=True, exist_ok=True)
    cmd: list[str] = [
        "pandoc",
        str(source.resolve()),
        "-f",
        "docx",
        "-o",
        str(target.resolve()),
        f"--pdf-engine={engine}",
        "-V",
        "geometry:margin=2cm",
    ]
    header = _xecjk_header_file_docx_pdf(engine)
    if header is not None:
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
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", check=False)
    finally:
        if header is not None:
            try:
                header.unlink(missing_ok=True)
            except OSError:
                pass
    if r.returncode != 0:
        err = (r.stderr or r.stdout or "").strip()
        raise RuntimeError(err or f"pandoc exited with code {r.returncode}")


def _find_libreoffice() -> str | None:
    for name in ("libreoffice", "soffice"):
        p = shutil.which(name)
        if p:
            return p
    return None


def _libreoffice_docx_to_pdf(source: Path, target: Path) -> None:
    lo = _find_libreoffice()
    if not lo:
        raise ConversionFailedError(
            "未找到 libreoffice / soffice。请安装 LibreOffice，或安装 pandoc + LaTeX 以使用 DOCX→PDF。"
        )
    target.parent.mkdir(parents=True, exist_ok=True)
    outdir = target.parent.resolve()
    cmd = [
        lo,
        "--headless",
        "--convert-to",
        "pdf",
        "--outdir",
        str(outdir),
        str(source.resolve()),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", check=False)
    if r.returncode != 0:
        err = (r.stderr or r.stdout or "").strip()
        raise ConversionFailedError(err or f"LibreOffice 退出码 {r.returncode}")

    produced = outdir / (source.stem + ".pdf")
    if not produced.is_file():
        raise ConversionFailedError(f"LibreOffice 未生成预期 PDF: {produced}")
    tgt = target.resolve()
    if produced != tgt:
        shutil.move(str(produced), str(tgt))


@register("docx", "pdf")
class DocxToPdfConverter(Converter):
    """
    Word（DOCX）→ PDF。

    - **auto**（默认）：优先 **LibreOffice** 无头转换（无需 TeX，与显式 `libreoffice` 一致）；不可用时再尝试 **pandoc+LaTeX**。
    - **pandoc**：强制 pandoc（需 LaTeX/xelatex 等）；`--md-pdf-pandoc-engine` 同样生效。
    - **libreoffice**：强制仅用 LibreOffice。
    """

    def convert(self, source: Path, target: Path, options: ConversionOptions | None = None) -> None:
        opts = options or ConversionOptions()
        source = source.resolve()
        target = target.resolve()
        if not source.is_file():
            raise ConversionFailedError(f"Source file not found: {source}")

        backend = (opts.docx_pdf_backend or "auto").strip().lower()
        if backend not in ("auto", "pandoc", "libreoffice"):
            raise ConversionFailedError(
                f"未知的 docx_pdf_backend: {backend!r}（允许 auto | pandoc | libreoffice）"
            )

        if backend == "libreoffice":
            logger.info("DOCX→PDF (LibreOffice): %s → %s", source, target)
            try:
                _libreoffice_docx_to_pdf(source, target)
            except ConversionFailedError:
                raise
            except Exception as e:
                raise ConversionFailedError(f"DOCX→PDF（LibreOffice）失败: {e}") from e
            if not target.is_file():
                raise ConversionFailedError(f"Output was not created: {target}")
            logger.info("Done (LibreOffice): %s (%d bytes)", target, target.stat().st_size)
            return

        if backend == "pandoc":
            if not _can_pandoc_md_to_pdf(opts):
                raise ConversionFailedError(
                    "DOCX→PDF（pandoc）需要 pandoc 与 PDF 引擎。\n" + _pandoc_pdf_prereq_error(opts)
                )
            try:
                logger.info("DOCX→PDF (pandoc+LaTeX): %s → %s", source, target)
                _pandoc_docx_to_pdf(source, target, opts)
            except ConversionFailedError:
                raise
            except Exception as e:
                raise ConversionFailedError(f"DOCX→PDF（pandoc）失败: {e}") from e
            if not target.is_file():
                raise ConversionFailedError(f"Output was not created: {target}")
            logger.info("Done (pandoc): %s (%d bytes)", target, target.stat().st_size)
            return

        # auto：与「libreoffice」相同，优先 LO；失败或无 LO 再 pandoc
        if _find_libreoffice():
            try:
                logger.info("DOCX→PDF (auto, LibreOffice 优先): %s → %s", source, target)
                _libreoffice_docx_to_pdf(source, target)
                if target.is_file():
                    logger.info("Done (LibreOffice): %s (%d bytes)", target, target.stat().st_size)
                    return
            except ConversionFailedError as e:
                logger.warning("DOCX→PDF：LibreOffice 失败，尝试 pandoc：%s", e)
            except Exception as e:
                logger.warning("DOCX→PDF：LibreOffice 异常，尝试 pandoc：%s", e)

        if _can_pandoc_md_to_pdf(opts):
            try:
                logger.info("DOCX→PDF (auto, pandoc): %s → %s", source, target)
                _pandoc_docx_to_pdf(source, target, opts)
            except ConversionFailedError:
                raise
            except Exception as e:
                raise ConversionFailedError(f"DOCX→PDF（pandoc）失败: {e}") from e
            if not target.is_file():
                raise ConversionFailedError(f"Output was not created: {target}")
            logger.info("Done (pandoc): %s (%d bytes)", target, target.stat().st_size)
            return

        raise ConversionFailedError(
            "DOCX→PDF（auto）：未找到 LibreOffice，且本机不具备 pandoc+PDF 引擎。\n"
            + _pandoc_pdf_prereq_error(opts)
        )
