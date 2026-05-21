"""
Reference sanitization and IEEE/APA/ACM bibliography generation utilities.

This module produces clean \bibitem entries from structured reference data
and sanitizes malformed reference strings from AI output.
"""
from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# Patterns that indicate a reference is a raw JSON fragment, not real text
_JSON_ARTIFACT_RE = re.compile(
    r'^\s*[\[{\"]?\s*"text"\s*:', re.IGNORECASE
)
_DICT_REPR_RE = re.compile(r"^\s*\{.*'text'\s*:", re.DOTALL)

# Garbage bracket prefix like [1] [2] at start of reference
_BRACKET_NUM_RE = re.compile(r"^\[\d+\]\s*")

# Repeated quotes/commas that indicate JSON fragments in a string
_JSON_COMMA_FRAGMENT_RE = re.compile(r'"\s*,\s*\{\s*"text"\s*:', re.DOTALL)

# Invalid unicode escapes
_INVALID_UNICODE_RE = re.compile(r'\\u(?![0-9a-fA-F]{4})')


def _is_json_artifact(text: str) -> bool:
    """Return True if the reference text looks like raw JSON, not a real citation."""
    stripped = text.strip()
    if _JSON_ARTIFACT_RE.match(stripped):
        return True
    if _DICT_REPR_RE.match(stripped):
        return True
    # Contains JSON-array like fragments
    if _JSON_COMMA_FRAGMENT_RE.search(stripped):
        return True
    # Looks like a Python dict repr
    if stripped.startswith("{'") or stripped.startswith('{"text"'):
        return True
    return False


def sanitize_reference_text(raw: Any) -> str | None:
    """
    Clean a single reference value (may be str, dict, or junk).

    Returns the cleaned citation string, or None if it cannot be salvaged.
    """
    # Handle dict with "text" key
    if isinstance(raw, dict):
        text = raw.get("text") or raw.get("reference") or raw.get("citation") or ""
        if isinstance(text, dict):
            # Double-nested dict — stringify contents
            text = " ".join(str(v) for v in text.values())
        raw = text

    if not isinstance(raw, str):
        raw = str(raw)

    text = raw.strip()
    if not text:
        return None

    # Reject pure JSON artifacts
    if _is_json_artifact(text):
        logger.debug("Rejected JSON artifact reference: %.80r", text)
        return None

    # Strip leading [1] / [2] bracket numbers (LaTeX auto-numbers)
    text = _BRACKET_NUM_RE.sub("", text).strip()

    # If the text contains embedded JSON fragments like `..., {"text": "..."}`
    # trim at the first occurrence of such a pattern
    m = _JSON_COMMA_FRAGMENT_RE.search(text)
    if m:
        text = text[:m.start()].strip().rstrip('",').strip()

    # Remove invalid unicode escapes
    text = _INVALID_UNICODE_RE.sub("", text)

    # Collapse excessive whitespace
    text = re.sub(r"\s+", " ", text).strip()

    # Must be at least 15 chars to be a real reference
    if len(text) < 15:
        return None

    return text


def normalize_references(raw_refs: list[Any]) -> list[dict[str, str]]:
    """
    Convert a list of raw reference values (strings, dicts, or mixed) into
    a clean list of {key, text, formatted} dicts ready for LaTeX rendering.

    Deduplicates, rejects JSON artifacts, and numbers entries sequentially.
    """
    if not raw_refs:
        return []

    seen: set[str] = set()
    result: list[dict[str, str]] = []

    for raw in raw_refs:
        # Handle the case where the entire remaining list got concatenated into one entry
        # (Gemini sometimes returns references as one big JSON array string)
        if isinstance(raw, str) and _JSON_COMMA_FRAGMENT_RE.search(raw):
            # Split on }, { patterns to recover individual references
            parts = re.split(r'",\s*\{', raw)
            for part in parts:
                # Strip leading { and trailing }
                cleaned_part = part.strip().lstrip("{").rstrip("}").strip()
                # Extract text value if it looks like "text": "..."
                m = re.search(r'"text"\s*:\s*"([^"]{15,})"', cleaned_part)
                if m:
                    candidate = sanitize_reference_text(m.group(1))
                    if candidate and candidate.lower() not in seen:
                        seen.add(candidate.lower())
                        result.append({
                            "key": f"ref{len(result) + 1}",
                            "text": candidate,
                        })
            continue

        candidate = sanitize_reference_text(raw)
        if candidate and candidate.lower() not in seen:
            seen.add(candidate.lower())
            result.append({
                "key": f"ref{len(result) + 1}",
                "text": candidate,
            })

    logger.debug("normalize_references: %d in → %d valid", len(raw_refs), len(result))
    return result


def build_bibliography_latex(references: list[dict[str, str]], format_type: str = "ieee") -> str:
    """
    Generate a complete LaTeX thebibliography block from cleaned reference dicts.

    Each dict must have:
      - key:  str  (bibitem label, e.g. "ref1")
      - text: str  (plain citation text, will be LaTeX-escaped by caller)

    Returns an empty string if no valid references.
    """
    if not references:
        return ""

    lines = ["\\begin{thebibliography}{99}"]
    for ref in references:
        key = ref.get("key", "")
        text = ref.get("text", "")
        if not key or not text:
            continue
        lines.append(f"\\bibitem{{{key}}}")
        lines.append(text)
        lines.append("")  # blank line for readability

    lines.append("\\end{thebibliography}")
    return "\n".join(lines)
