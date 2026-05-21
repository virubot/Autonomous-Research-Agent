"""
LaTeX-based academic paper PDF compiler.
Converts structured paper data into publication-quality PDFs using
real document classes: IEEEtran, acmart, apa7.

Pipeline: Structured JSON → Jinja2 LaTeX template → pdflatex → PDF
"""
from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from backend.utils.reference_utils import normalize_references, sanitize_reference_text

logger = logging.getLogger(__name__)

TEMPLATE_DIR = Path(__file__).parent / "templates" / "latex"
OUTPUT_DIR = Path("generated_outputs")

from backend.utils.latex_utils import latex_escape, latex_escape_reference

# Strip leading roman / arabic section numbers from titles
_SECTION_NUM_RE = re.compile(
    r"^(?:\d+\.?\s+|[IVXLC]+\.\s+)",
    re.IGNORECASE,
)

# Strip leading [1] from reference text
_REF_BRACKET_RE = re.compile(r"^\[\d+\]\s*")


# ── Jinja2 environment ────────────────────────────────────────────────────

def _make_jinja_env() -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        block_start_string="((*",
        block_end_string="*))",
        variable_start_string="(((",
        variable_end_string=")))",
        comment_start_string="((#",
        comment_end_string="#))",
        keep_trailing_newline=True,
        autoescape=False,
    )
    env.filters["latex_escape"] = latex_escape
    return env


# ── Section title cleaning ────────────────────────────────────────────────

def _strip_section_number(title: str) -> str:
    """Remove leading '1. ' or 'III. ' from a section title."""
    if not isinstance(title, str):
        return "Section"
    return _SECTION_NUM_RE.sub("", title).strip()


# ── Data normalisation ────────────────────────────────────────────────────

def _normalize_paper_data(data: dict[str, Any], format_type: str) -> dict[str, Any]:
    """
    Normalise and fill defaults so templates always have required keys.
    This is the defensive layer — every field is validated before rendering.
    """
    # ── Authors ──
    raw_authors = data.get("authors") or []
    if isinstance(raw_authors, str):
        raw_authors = [raw_authors]
    authors = [
        a for a in raw_authors
        if isinstance(a, str) and a.strip()
        and "First A." not in a
        and "Second B." not in a
        and "Author" not in a   # catches generic "Author Name" placeholders
    ]
    if not authors:
        authors = ["Autonomous Research Assistant"]

    # ── References — use the hardened reference_utils pipeline ──
    raw_refs = data.get("references") or []
    if not isinstance(raw_refs, list):
        raw_refs = []
    references = normalize_references(raw_refs)

    # ── Sections ──
    raw_sections = data.get("sections") or []
    if not isinstance(raw_sections, list):
        raw_sections = []

    normalized_sections: list[dict[str, Any]] = []
    for sec in raw_sections:
        if not isinstance(sec, dict):
            continue

        title = _strip_section_number(sec.get("title") or "Section")

        content = sec.get("content") or []
        if isinstance(content, str):
            content = [content]
        # Keep only real paragraphs — reject placeholder templates
        clean_content: list[str] = []
        for p in content:
            if not isinstance(p, str):
                continue
            p = p.strip()
            if not p:
                continue
            if p.startswith("<substantive") or p.startswith("<paragraph"):
                continue
            # Reject tiny or obviously fake paragraphs
            if len(p) < 20:
                continue
            clean_content.append(p)

        entry: dict[str, Any] = {"title": title, "content": clean_content}

        # Optional table — validate structure
        table = sec.get("table")
        if isinstance(table, dict) and table.get("columns") and table.get("header"):
            rows = table.get("rows") or []
            if isinstance(rows, list) and rows:
                entry["table"] = table

        # Optional figure
        fig_cap = sec.get("figure_caption")
        if isinstance(fig_cap, str) and fig_cap.strip():
            entry["figure_caption"] = fig_cap.strip()

        normalized_sections.append(entry)

    # ── Abstract ──
    abstract = data.get("abstract") or ""
    if not isinstance(abstract, str):
        abstract = str(abstract)
    abstract = abstract.strip()

    # ── Keywords ──
    kws = data.get("keywords") or []
    if not isinstance(kws, list):
        kws = []
    keywords = [str(k).strip() for k in kws if str(k).strip()]

    # ── Title ──
    full_title = data.get("title") or "Untitled Research Paper"
    if not isinstance(full_title, str):
        full_title = str(full_title)
    full_title = full_title.strip()
    words = full_title.split()
    short_title = " ".join(words[:6]) if len(words) > 6 else full_title

    return {
        "title":         full_title,
        "short_title":   short_title,
        "authors":       authors,
        "affiliation":   str(data.get("affiliation") or "Autonomous Research Assistant Platform"),
        "contact_email": str(data.get("contact_email") or "research@ara-platform.ai"),
        "abstract":      abstract,
        "keywords":      keywords,
        "sections":      normalized_sections,
        "citations":     list(data.get("citations") or []),
        "references":    references,
        "format_type":   format_type.lower(),
    }


# ── Bibliography generation (Python-side, not from template) ─────────────

def _build_bibliography_block(references: list[dict[str, str]]) -> str:
    """
    Generate a LaTeX thebibliography block from cleaned reference dicts.

    Each ref dict must have: key (str), text (str).
    The text is escaped here to prevent any LaTeX injection.
    Returns empty string if no valid references.
    """
    if not references:
        return ""

    lines = ["\\begin{thebibliography}{99}", ""]
    for ref in references:
        key = ref.get("key", "")
        text = ref.get("text", "")
        if not key or not text:
            continue
        # Escape for LaTeX — use the reference-specific escaper
        escaped = latex_escape_reference(text)
        lines.append(f"\\bibitem{{{key}}}")
        lines.append(escaped)
        lines.append("")

    lines.append("\\end{thebibliography}")
    return "\n".join(lines)


# ── LaTeX source generation ───────────────────────────────────────────────

def generate_latex_source(paper_data: dict[str, Any], format_type: str = "ieee") -> str:
    """
    Render the Jinja2 LaTeX template and inject a clean bibliography block.
    The bibliography is generated in Python (not from the template) to guarantee
    no raw JSON leaks into the .tex source.
    """
    fmt = format_type.lower().strip()
    if fmt not in ("ieee", "apa", "acm"):
        fmt = "ieee"

    env = _make_jinja_env()
    template = env.get_template(f"{fmt}.tex.j2")
    normalized = _normalize_paper_data(paper_data, fmt)

    # Build bibliography block in Python, then inject as a string variable
    bib_block = _build_bibliography_block(normalized["references"])
    normalized["bibliography_block"] = bib_block

    latex_src = template.render(**normalized)

    # Safety check: if template still has raw JSON fragments, abort early
    if '"text":' in latex_src or "'text':" in latex_src:
        logger.error(
            "JSON fragment detected in generated LaTeX. Aborting to prevent corrupt PDF."
        )
        raise RuntimeError(
            "JSON fragment leaked into LaTeX source — bibliography not properly rendered."
        )

    return latex_src


# ── PDF compilation ───────────────────────────────────────────────────────

def _find_latex_binary(engine: str) -> str:
    """Find the LaTeX binary on the system PATH or common install locations."""
    latex_bin = shutil.which(engine, path=os.environ.get("PATH", ""))
    if latex_bin:
        return latex_bin
    for candidate in [
        f"/Library/TeX/texbin/{engine}",
        f"/usr/local/texlive/2026/bin/universal-apple-darwin/{engine}",
        f"/usr/local/texlive/2025/bin/universal-apple-darwin/{engine}",
        f"/usr/local/texlive/2024/bin/universal-apple-darwin/{engine}",
        f"/usr/bin/{engine}",
    ]:
        if os.path.isfile(candidate):
            return candidate
    raise RuntimeError(
        f"'{engine}' binary not found. Install TeX Live: https://tug.org/texlive/"
    )


def compile_latex_to_pdf(
    latex_source: str,
    output_dir: str | Path = OUTPUT_DIR,
    engine: str = "pdflatex",
) -> Path:
    """
    Write the LaTeX source to a temp directory, compile with pdflatex (×2),
    and copy the resulting PDF to output_dir.
    Returns the final PDF path.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    job_id = uuid.uuid4().hex[:10]
    pdf_filename = f"research_paper_{job_id}.pdf"
    final_pdf = output_dir / pdf_filename

    latex_bin = _find_latex_binary(engine)

    with tempfile.TemporaryDirectory() as tmpdir:
        tex_file = Path(tmpdir) / "paper.tex"
        tex_file.write_text(latex_source, encoding="utf-8")

        compile_cmd = [
            latex_bin,
            "-interaction=nonstopmode",
            "-halt-on-error",
            f"-output-directory={tmpdir}",
            str(tex_file),
        ]

        last_log = ""
        # Two passes for cross-references
        for run in range(2):
            try:
                proc = subprocess.run(
                    compile_cmd,
                    capture_output=True,
                    text=True,
                    timeout=90,
                    cwd=tmpdir,
                )
                last_log = proc.stdout or ""
                if proc.returncode != 0:
                    # On first pass, non-zero is sometimes expected (aux files missing)
                    if run == 1:
                        error_tail = last_log[-2500:] if last_log else "(no log)"
                        logger.error(
                            "LaTeX compilation failed on pass 2 (exit %d):\n%s",
                            proc.returncode, error_tail
                        )
                        raise RuntimeError(
                            f"LaTeX compilation failed (exit {proc.returncode}).\n"
                            + error_tail[-1500:]
                        )
            except subprocess.TimeoutExpired:
                raise RuntimeError("LaTeX compilation timed out after 90 s.")

        compiled_pdf = Path(tmpdir) / "paper.pdf"
        if not compiled_pdf.exists():
            logger.error("PDF not found after LaTeX run. Log tail:\n%s", last_log[-2000:])
            raise RuntimeError("Compiled PDF not found after LaTeX run.")

        shutil.copy2(compiled_pdf, final_pdf)
        logger.info("PDF generated → %s", final_pdf)

    return final_pdf


# ── Public API ────────────────────────────────────────────────────────────

def generate_pdf(
    paper_data: dict[str, Any],
    format_type: str = "ieee",
    output_dir: str | Path = OUTPUT_DIR,
) -> str:
    """
    Full pipeline: structured paper dict → validated LaTeX source → PDF.
    Returns the relative path string of the generated PDF.
    Raises RuntimeError with a descriptive message on failure.
    """
    fmt = (format_type or "ieee").lower().strip()
    if fmt not in ("ieee", "apa", "acm"):
        fmt = "ieee"

    engine = "pdflatex"

    try:
        latex_src = generate_latex_source(paper_data, fmt)
        pdf_path = compile_latex_to_pdf(latex_src, output_dir=output_dir, engine=engine)
        return str(pdf_path)
    except RuntimeError:
        raise
    except Exception as exc:
        logger.exception("Unexpected error in PDF generation pipeline")
        raise RuntimeError(f"PDF generation failed: {exc}") from exc
