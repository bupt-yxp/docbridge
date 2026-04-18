from __future__ import annotations

import importlib

for _name in ("docx_md", "docx_pdf", "md_docx", "md_pdf", "pdf_docx"):
    importlib.import_module(f"docbridge.converters.{_name}")
