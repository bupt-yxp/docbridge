#!/usr/bin/env bash
# 验证：生成图片 → 生成 PDF → docbridge pdf2docx → 检查输出
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT/src:${PYTHONPATH:-}"

echo "[1/4] 生成测试图片（需 Pillow）..."
if ! python3 scripts/generate_fixture_images.py; then
  echo "跳过图片生成：请 pip install Pillow 后重试"
  exit 1
fi

echo "[2/4] 生成 sample.pdf..."
python3 scripts/build_sample_pdf.py

echo "[3/4] PDF → DOCX..."
OUT="$ROOT/fixtures/sample-out.docx"
python3 -m docbridge.cli.main pdf2docx "$ROOT/fixtures/sample.pdf" -o "$OUT" --dpi 288

echo "[4/4] 检查输出..."
if [[ ! -f "$OUT" ]]; then
  echo "失败: 未生成 $OUT"
  exit 1
fi
SZ=$(stat -c%s "$OUT" 2>/dev/null || stat -f%z "$OUT")
if [[ "$SZ" -lt 2000 ]]; then
  echo "警告: 输出文件过小 ($SZ bytes)，请人工检查"
fi
echo "成功: $OUT ($SZ bytes)"
echo "可解压 docx 查看 word/media/ 下图片分辨率。"
