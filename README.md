# DocBridge

可扩展的文档格式转换 **Python 库** 与 **CLI**。

| 能力 | 实现说明 |
|------|----------|
| **PDF → Word** | **可编辑公式**：若存在与 PDF **同名、同目录的 `.md`**（或 `--pdf-companion-md`），则**改走 Markdown→DOCX**，生成 **Word 原生 OMML**；纯 [pdf2docx](https://github.com/dothinking/pdf2docx) **无法从 PDF 恢复数学对象**，只能抽文字/坐标。**默认关闭**格子表/流式表（`--pdf-parse-tables` 可开）。另有后处理：字体、浮动图行内化等 |
| **Markdown → Word** | `auto`：系统有 **pandoc** 则调用；否则 **markdown → HTML → python-docx**（内置管线与 **Markdown→PDF** 共用 `md_theme`：字号、颜色、A4/2cm 边距、图片按像素+DPI 换算并 `max-width` 封顶，与 WeasyPrint 一致） |
| **Markdown → PDF** | **WeasyPrint**（`MARKDOWN_CSS` 与 DOCX 同源），可选依赖 `docbridge[pdf]` |
| **Word → PDF** | **`docx_pdf_backend`（CLI `--docx-pdf-backend`）**：`auto` **优先 LibreOffice**（无需 TeX）；失败或无 LO 时再 **pandoc + LaTeX**（与 `--md-pdf-pandoc-engine` 共用）；也可强制 `pandoc` 或 `libreoffice` |
| **Word → Markdown** | **Pandoc**（`docx` → `markdown+tex_math_dollars`）：**公式**由 OMML 转为 LaTeX（`$` / `$$`），与 MD→Word 的数学约定对齐；**图片**默认 `--extract-media` 到与 `.md` 同目录的 `<stem>_media/`。**排版**仅保留 Markdown 能表达的结构（标题、列表、表格、强调等），不还原分页、页眉页脚、文本框与浮动版式 |
| **字体一致** | PDF/DOCX 共用 `md_theme`：`Microsoft YaHei` / `Noto Sans CJK` 等无衬线栈；DOCX 对 run 设置 `eastAsia`；PDF 对 `em/i` 使用 `font-style: oblique` 以在缺斜体字形时仍能倾斜中文 |

## 功能概览

- **库 API**：`convert_file()`、`list_supported_pairs()`、`ConversionOptions`
- **CLI**：仅 `list-formats` 与统一入口 `convert --from/--to`
- **扩展**：`@register("源", "目标")` 注册新转换器（见下文）

## 安装

```bash
cd /path/to/云网测量26
pip install -e .
# Markdown→PDF
pip install -e ".[pdf]"
# 开发依赖
pip install -e ".[dev]"
```

安装后：`docbridge --help`

## CLI 用法

```bash
docbridge list-formats

# PDF → Word（默认开启后处理；不需要可加 --no-pdf-postprocess）
docbridge convert --from pdf --to docx input.pdf -o output.docx --dpi 288
docbridge convert --from pdf --to docx input.pdf -o out.docx --float-image-gap 6   # 传给 pdf2docx，可调浮动图判定
docbridge convert --from pdf --to docx input.pdf -o out.docx --no-pdf-inline-images # 不改为行内图（仍可能叠压）
docbridge convert --from pdf --to docx input.pdf -o out.docx --no-pdf-trim-leading   # 保留 pdf2docx 原首段空行/段前距
docbridge convert --from pdf --to docx table.pdf -o out.docx --pdf-parse-tables      # 需从 PDF 还原表格时开启（与旧版 pdf2docx 默认类同）
# 与 my.pdf 同目录下放 my.md（同源稿），则自动用 MD 生成带 OMML 公式的 Word；或：--pdf-companion-md ./源稿.md
docbridge convert --from pdf --to docx my.pdf -o out.docx --no-pdf-sibling-md       # 强制只用 pdf2docx、不要同名 .md

# Markdown → Word（图片路径相对 .md 所在目录）
docbridge convert --from md --to docx readme.md -o readme.docx
docbridge convert --from md --to docx readme.md -o readme.docx --md-backend python   # 强制内置管线
docbridge convert --from md --to docx readme.md -o readme.docx --md-backend pandoc    # 强制 pandoc（需已安装）

# Markdown → PDF
# 默认 auto：若已安装 pandoc + LaTeX（建议 xelatex），走 **完整 LaTeX 数学**（cases/pmatrix 等多行公式）
docbridge convert --from md --to pdf readme.md -o readme.pdf
# 仅 WeasyPrint+matplotlib（需 pip install -e ".[pdf]"；不支持 amsmath 多行环境）
docbridge convert --from md --to pdf readme.md -o readme.pdf --md-pdf-backend weasyprint
# 强制 Pandoc→PDF（需 pandoc、TeX，中文建议 xelatex + Noto CJK 等字体）
docbridge convert --from md --to pdf readme.md -o readme.pdf --md-pdf-backend pandoc

# Word → PDF（auto：优先 LibreOffice，否则 pandoc+LaTeX）
docbridge convert --from docx --to pdf readme.docx -o readme.pdf
docbridge convert --from docx --to pdf readme.docx -o readme.pdf --docx-pdf-backend libreoffice

# Word → Markdown（需已安装 pandoc；图片导出到 readme_media/）
docbridge convert --from docx --to md readme.docx -o readme.md
```

### 常用参数

**PDF→DOCX**：`--dpi`、`--password`、`--start` / `--end`、`--pages`、`--no-ignore-page-error`、`--no-pdf-postprocess`、`--pdf-md-theme-a4-margins`、`--no-pdf-inline-images`、`--no-pdf-trim-leading`、`--float-image-gap`（见 `docbridge convert --help`）。

**Markdown→DOCX**：`--md-backend` 为 `auto` | `python` | `pandoc`。

**DOCX→Markdown**：无额外 CLI 开关；输出格式与是否抽取图片由 `ConversionOptions.docx_md_pandoc_to`、`docx_extract_media` 控制（见 Python API）。

**Markdown→PDF**：`--md-pdf-backend` 为 `auto` | `weasyprint` | `pandoc`；`--md-pdf-pandoc-engine` 可指定 `xelatex` 等。

**DOCX→PDF**：`--docx-pdf-backend` 为 `auto` | `pandoc` | `libreoffice`（与 `--md-pdf-pandoc-engine` 共用 PDF 引擎时也适用）。

### 扩展名与声明格式

`convert_file` 会校验：源文件扩展名须与声明的**源格式**一致，输出路径扩展名须与**目标格式**一致（大小写不敏感）；缺少扩展名或后缀不符时会报错。

| 格式 | 允许的后缀 |
|------|------------|
| `pdf` | `.pdf` |
| `docx` | `.docx` |
| `md` | `.md`、`.markdown`、`.mdown`、`.mkd` |

若必须使用非标准扩展名，可在 API 中设置 `ConversionOptions(skip_extension_check=True)`。

## Python API

```python
from pathlib import Path
from docbridge import convert_file, ConversionOptions

convert_file(Path("a.pdf"), Path("b.docx"), "pdf", "docx", ConversionOptions(render_dpi=300))
convert_file(Path("x.md"), Path("x.docx"), "md", "docx", ConversionOptions(md_backend="python"))
convert_file(Path("x.md"), Path("x.pdf"), "md", "pdf", ConversionOptions())  # auto：有 LaTeX 则用 pandoc
convert_file(
    Path("x.md"), Path("x.pdf"), "md", "pdf",
    ConversionOptions(md_pdf_backend="weasyprint"),
)
convert_file(Path("w.docx"), Path("w.md"), "docx", "md", ConversionOptions())  # 需本机 pandoc
convert_file(Path("w.docx"), Path("w.pdf"), "docx", "pdf", ConversionOptions())  # auto：pandoc+TeX 或 LibreOffice
```

`ConversionOptions.md_resource_base` 可指定解析 `![img](./a.png)` 的基准目录（默认与源 `.md` 同目录）。

`ConversionOptions.docx_md_pandoc_to`（默认 `markdown+tex_math_dollars`）与 `docx_extract_media`（默认 `True`）用于 **DOCX→Markdown**。

`ConversionOptions.md_pdf_backend`（`auto` | `weasyprint` | `pandoc`）与 `md_pdf_pandoc_engine` 用于 **Markdown→PDF**。

`ConversionOptions.docx_pdf_backend`（`auto` | `pandoc` | `libreoffice`）用于 **DOCX→PDF**（`auto` 先 LibreOffice；回退 pandoc 时与 `md_pdf_pandoc_engine` 共用 PDF 引擎）。

## 扩展新格式

1. 在 `src/docbridge/converters/` 下新建模块，实现 `Converter` 子类并重写 `convert()`。
2. 使用 `@register("源扩展名", "目标扩展名")` 装饰类。
3. 在 `docbridge/converters/__init__.py` 中 `import` 该模块。

## 验证

见 [docs/verification.md](docs/verification.md)。

```bash
pip install Pillow
bash scripts/verify_fixture.sh
```

## 许可证

MIT。

## 限制说明

- PDF→Word：无法保证与 PDF **像素级**一致。
- MD→DOCX：内置管线支持常见语法（标题、强调、列表、表格、代码块、图片等）；极端复杂 HTML 或 pandoc 专有扩展以 **pandoc** 结果为准。
- MD→PDF：**`auto`**（默认）在检测到 **pandoc + LaTeX**（优先 xelatex）时走 **Pandoc→PDF**，可正确排版 `cases`、`pmatrix`、多行 `$$` 等；否则走 **WeasyPrint**。仅 WeasyPrint 路径需 `pip install docbridge[pdf]` 与 [WeasyPrint 系统依赖](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#installation)。**WeasyPrint 路径**下公式由 **matplotlib mathtext** 画成 SVG，**不支持** `\\begin{cases}`、`\\begin{pmatrix}` 等 amsmath 环境；若需复杂公式请安装 TeX 并使用 `auto`/`--md-pdf-backend pandoc`。Pandoc+xelatex/tectonic 会通过 **`xeCJK` 补入前言**，使中文在字间自动换行；若仅用 `fontspec` 配中文字体，整段汉字常被当作「一个单词」而在行末溢出页面。若缺 `xeCJK.sty`，请安装：`sudo apt install texlive-lang-chinese`。调用 Pandoc 前仍会将「单独成行」的 `$ … $` 规范化为 `$$ … $$`，**避免** `f'(x)=` 等落入正文而触发 ``! Missing $ inserted``。
- DOCX→MD：**必须**安装 [pandoc](https://pandoc.org/installing.html)；版式以 Markdown 表达能力为上限，复杂 Word 版式可能丢失或降级。
