"""
PDF Service providing the public interface for structured research paper PDF generation.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.pdf_generator import generate_pdf as _generate_pdf


def generate_research_paper_pdf(
    paper_data: dict[str, Any],
    format_type: str = "ieee",
    output_dir: str | Path = "generated_outputs"
) -> str:
    """
    Main entrypoint for structured data → validated LaTeX source → PDF compilation.
    """
    return _generate_pdf(paper_data, format_type=format_type, output_dir=output_dir)
