# 验证说明（与 `AI编码任务_PDF转Word与验证提示词.md` 对齐）

## 依赖与版本

- **PDF→Word**：`pdf2docx`（MIT），底层 **PyMuPDF** + **python-docx**。
- **Markdown→Word**：`markdown`、`beautifulsoup4`、`python-docx`；可选系统 **pandoc**（`--md-backend pandoc` / `auto` 检测）。
- **Word→Markdown**：系统 **pandoc**（`docx` → `markdown+tex_math_dollars`，公式 OMML→LaTeX）。
- **Markdown→PDF**：可选 `weasyprint`（`pip install -e ".[pdf]"`）。
- 固定版本见项目根目录 `pyproject.toml`。

## 自动化验证（推荐）

在项目根目录执行（需已 `pip install -e .` 或设置 `PYTHONPATH=src`）：

```bash
pip install -e ".[dev]"
pip install Pillow   # 用于生成 fixtures 图片
bash scripts/verify_fixture.sh
```

步骤含义：

1. 生成 `fixtures/test-diagram.png` 与 `fixtures/test-photo.jpg`
2. 用 `scripts/build_sample_pdf.py` 生成 `fixtures/sample.pdf`（**不依赖 pandoc**）
3. 调用 `docbridge convert --from pdf --to docx` 生成 `fixtures/sample-out.docx`
4. 检查输出文件大小

## Markdown 转换示例（本仓库）

```bash
pip install -e ".[pdf]"   # md→pdf 需要
docbridge convert --from md --to docx fixtures/sample.md -o /tmp/sample-md.docx --md-backend python
docbridge convert --from md --to pdf fixtures/sample.md -o /tmp/sample-md.pdf
```

## MD → PDF → Word（外链链路，仍可用）

1. 用任意工具将 `fixtures/sample.md` 转为 PDF，或直接用本仓库 `docbridge convert --from md --to pdf`。
2. 再执行：

   ```bash
   docbridge convert --from pdf --to docx your.pdf -o out.docx --dpi 288
   ```

## 验收清单（人工）

- [ ] Word 中文字可读、无乱码（对给定 `sample.pdf`）
- [ ] 图片区域与源 PDF 大致一致；若需量化，解压 `.docx` 查看 `word/media/` 内图片尺寸
- [ ] 控制台无未处理异常；日志含页处理信息

## 已知限制（诚实表述）

- PDF 与 Word 文档模型不同，**无法承诺像素级一致**。
- **扫描件 PDF** 以位图为主，可编辑性依赖 OCR，与本库基于 `pdf2docx` 的版式解析路径不同。
- `--dpi` 映射为 `pdf2docx` 的 `clip_image_res_ratio`（相对 72dpi），用于**页面裁剪类图像**清晰度；嵌入矢量图仍以解析结果为准。
