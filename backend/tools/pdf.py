from __future__ import annotations

from typing import Any


def extract_pdf(file_path: str, max_chars: int = 20000) -> dict[str, Any]:
    try:
        from pypdf import PdfReader
    except Exception as exc:
        return {
            "tool": "extract_pdf",
            "status": "error",
            "error": f"pypdf is unavailable: {exc}",
            "text": "",
        }

    try:
        reader = PdfReader(file_path)
        pages_text: list[str] = []
        for page in reader.pages:
            pages_text.append((page.extract_text() or "").strip())

        text = "\n\n".join(part for part in pages_text if part).strip()
        return {
            "tool": "extract_pdf",
            "status": "success",
            "file_path": file_path,
            "pages": len(reader.pages),
            "text": text[:max_chars],
        }
    except Exception as exc:
        return {
            "tool": "extract_pdf",
            "status": "error",
            "error": str(exc),
            "text": "",
        }
