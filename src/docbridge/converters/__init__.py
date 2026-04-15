from __future__ import annotations

import importlib

for _name in ("md_docx", "md_pdf", "pdf_docx"):
    importlib.import_module(f"docbridge.converters.{_name}")
