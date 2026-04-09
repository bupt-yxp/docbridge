"""声明的格式与输入/输出文件扩展名一致性校验。"""

from __future__ import annotations

from pathlib import Path

from docbridge.exceptions import ConversionFailedError

# 与各 register("格式") 键对应；md 允许多种常见后缀
_FORMAT_SUFFIXES: dict[str, tuple[str, ...]] = {
    "pdf": (".pdf",),
    "docx": (".docx",),
    "md": (".md", ".markdown", ".mdown", ".mkd"),
}


def _fmt_suffixes(fmt: str) -> tuple[str, ...] | None:
    return _FORMAT_SUFFIXES.get(fmt.lower().strip())


def _human_allowed(allowed: tuple[str, ...]) -> str:
    return "、".join(allowed)


def validate_path_extensions(
    source: Path,
    target: Path,
    source_format: str,
    target_format: str,
) -> None:
    """若扩展名与声明格式不一致或缺少扩展名，抛出 :class:`ConversionFailedError`。"""
    sf = source_format.lower().strip()
    tf = target_format.lower().strip()

    src_sfx = source.suffix.lower()
    if not src_sfx:
        raise ConversionFailedError(
            f"源文件缺少扩展名，无法与声明的源格式 {sf!r} 对应：{source}"
        )
    want_src = _fmt_suffixes(sf)
    if want_src is not None and src_sfx not in want_src:
        raise ConversionFailedError(
            f"源文件扩展名与声明的源格式不符：声明为 {sf!r}，期望后缀为 {_human_allowed(want_src)}，"
            f"实际为 {src_sfx!r}（{source}）"
        )

    tgt_sfx = target.suffix.lower()
    if not tgt_sfx:
        raise ConversionFailedError(
            f"输出文件缺少扩展名，无法与声明的目标格式 {tf!r} 对应：{target}"
        )
    want_tgt = _fmt_suffixes(tf)
    if want_tgt is not None and tgt_sfx not in want_tgt:
        raise ConversionFailedError(
            f"输出文件扩展名与声明的目标格式不符：声明为 {tf!r}，期望后缀为 {_human_allowed(want_tgt)}，"
            f"实际为 {tgt_sfx!r}（{target}）"
        )
