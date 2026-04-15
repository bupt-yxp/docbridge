#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT/src:${PYTHONPATH:-}"

echo "[1/4] Generate fixture images (needs Pillow)..."
if ! python3 scripts/generate_fixture_images.py; then
  echo "Image generation failed; install Pillow: pip install Pillow"
  exit 1
fi

echo "[2/4] Build sample.pdf..."
python3 scripts/build_sample_pdf.py

echo "[3/4] PDF to DOCX..."
OUT="$ROOT/fixtures/sample-out.docx"
python3 -m docbridge.cli.main pdf2docx "$ROOT/fixtures/sample.pdf" -o "$OUT" --dpi 288

echo "[4/4] Check output..."
if [[ ! -f "$OUT" ]]; then
  echo "Failed: missing $OUT"
  exit 1
fi
SZ=$(stat -c%s "$OUT" 2>/dev/null || stat -f%z "$OUT")
if [[ "$SZ" -lt 2000 ]]; then
  echo "Warning: output very small ($SZ bytes); inspect manually"
fi
echo "OK: $OUT ($SZ bytes)"
echo "Unzip the docx to inspect word/media/ image resolution."
