from __future__ import annotations

from typing import Any


def extract_image(file_path: str, lang: str = "eng", max_chars: int = 15000) -> dict[str, Any]:
    try:
        import pytesseract
        from PIL import Image
        from pytesseract import TesseractNotFoundError
    except Exception as exc:
        return {
            "tool": "extract_image",
            "status": "error",
            "error": f"OCR dependencies unavailable: {exc}",
            "text": "",
        }

    try:
        with Image.open(file_path) as image:
            text = pytesseract.image_to_string(image, lang=lang).strip()
        return {
            "tool": "extract_image",
            "status": "success",
            "file_path": file_path,
            "text": text[:max_chars],
        }
    except TesseractNotFoundError:
        return {
            "tool": "extract_image",
            "status": "error",
            "error": "Tesseract binary not found. Install `tesseract` on your system.",
            "text": "",
        }
    except Exception as exc:
        return {
            "tool": "extract_image",
            "status": "error",
            "error": str(exc),
            "text": "",
        }
