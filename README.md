# DocBridge

可扩展的文档格式转换 **Python 库** 与 **CLI**。

| 能力 | 实现说明 |
|------|----------|
| **PDF → Word** | [pdf2docx](https://github.com/dothinking/pdf2docx)；默认 **后处理**：A4/2cm 边距、与 `md_theme` 一致的中文字体（eastAsia）、关闭中西文自动间距；**将 `wp:anchor` 浮动图改为 `wp:inline` 行内图**（显著减轻与正文/表格叠压；不再保留页内绝对坐标）。仍无法与 PDF 像素级一致 |
| **Markdown → Word** | `auto`：系统有 **pandoc** 则调用；否则 **markdown → HTML → python-docx**（内置管线与 md2pdf **共用 `md_theme`：字号、颜色、A4/2cm 边距、图片按像素+DPI 换算并 `max-width` 封顶，与 WeasyPrint 一致） |
| **Markdown → PDF** | **WeasyPrint**（`MARKDOWN_CSS` 与 DOCX 同源），可选依赖 `docbridge[pdf]` |
| **字体一致** | PDF/DOCX 共用 `md_theme`：`Microsoft YaHei` / `Noto Sans CJK` 等无衬线栈；DOCX 对 run 设置 `eastAsia`；PDF 对 `em/i` 使用 `font-style: oblique` 以在缺斜体字形时仍能倾斜中文 |

## 功能概览

- **库 API**：`convert_file()`、`list_supported_pairs()`、`ConversionOptions`
- **CLI**：`pdf2docx`、`md2docx`、`md2pdf`、`convert --from/--to`
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
docbridge pdf2docx input.pdf -o output.docx --dpi 288
docbridge pdf2docx input.pdf -o out.docx --float-image-gap 6   # 传给 pdf2docx，可调浮动图判定
docbridge pdf2docx input.pdf -o out.docx --no-pdf-inline-images # 不改为行内图（仍可能叠压）
docbridge pdf2docx input.pdf -o out.docx --no-pdf-trim-leading   # 保留 pdf2docx 原首段空行/段前距

# Markdown → Word（图片路径相对 .md 所在目录）
docbridge md2docx readme.md -o readme.docx
docbridge md2docx readme.md -o readme.docx --md-backend python   # 强制内置管线
docbridge md2docx readme.md -o readme.docx --md-backend pandoc    # 强制 pandoc（需已安装）

# Markdown → PDF（需已安装 WeasyPrint：pip install -e ".[pdf]"）
docbridge md2pdf readme.md -o readme.pdf

# 通用入口
docbridge convert --from pdf --to docx a.pdf -o a.docx
docbridge convert --from md --to docx x.md -o x.docx --md-backend auto
docbridge convert --from md --to pdf x.md -o x.pdf
```

### 常用参数

**PDF→DOCX**：`--dpi`、`--password`、`--start` / `--end`、`--pages`、`--no-ignore-page-error`（见 `docbridge convert --help`）。

**Markdown→DOCX**：`--md-backend` 为 `auto` | `python` | `pandoc`。

## Python API

```python
from pathlib import Path
from docbridge import convert_file, ConversionOptions

convert_file(Path("a.pdf"), Path("b.docx"), "pdf", "docx", ConversionOptions(render_dpi=300))
convert_file(Path("x.md"), Path("x.docx"), "md", "docx", ConversionOptions(md_backend="python"))
convert_file(Path("x.md"), Path("x.pdf"), "md", "pdf", ConversionOptions())
```

`ConversionOptions.md_resource_base` 可指定解析 `![img](./a.png)` 的基准目录（默认与源 `.md` 同目录）。

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
- MD→PDF：依赖系统字体与 WeasyPrint；部分环境需额外安装 [WeasyPrint 依赖](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#installation)。
