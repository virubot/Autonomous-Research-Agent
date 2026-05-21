"""
Robust JSON cleaning and safe parsing utilities for Gemini model output.
Handles malformed escapes, markdown fences, trailing commas, and partial content.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# Regex to strip markdown code fences (```json ... ``` or ``` ... ```)
_FENCE_RE = re.compile(r"^```(?:json)?\s*\n?(.*?)\n?```\s*$", re.DOTALL | re.IGNORECASE)

# Trailing commas before ] or }
_TRAILING_COMMA_RE = re.compile(r",\s*([}\]])", re.MULTILINE)

# JSON comments (// ... or /* ... */)  — illegal in JSON but Gemini sometimes adds them
_COMMENT_RE = re.compile(r"//[^\n]*|/\*.*?\*/", re.DOTALL)

# LaTeX-style backslash sequences that are valid in text but break JSON parsing
# e.g. \alpha → \\alpha; already-doubled ones are left alone
_SINGLE_BACKSLASH_RE = re.compile(r'(?<!\\)\\(?!["\\/bfnrtu])')


def strip_code_fences(text: str) -> str:
    """Remove markdown triple-backtick fences if present."""
    stripped = text.strip()
    m = _FENCE_RE.match(stripped)
    if m:
        return m.group(1).strip()
    # Handle case where only opening fence exists
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        # Remove first line (the fence) and last line if it's a closing fence
        start = 1
        end = len(lines)
        if lines[-1].strip() == "```":
            end -= 1
        return "\n".join(lines[start:end]).strip()
    return stripped


def repair_escape_sequences(text: str) -> str:
    r"""
    Fix unescaped single backslashes that are not valid JSON escape sequences.
    e.g. \alpha → \\alpha, \sum → \\sum, \\ is left alone.
    """
    # Replace single backslashes (not already doubled) with double backslashes
    # Valid JSON escapes: \", \\, \/, \b, \f, \n, \r, \t, \uXXXX
    result = _SINGLE_BACKSLASH_RE.sub(r"\\\\", text)
    return result


def remove_json_comments(text: str) -> str:
    """Remove JavaScript-style // and /* */ comments from JSON-like text."""
    return _COMMENT_RE.sub("", text)


def fix_trailing_commas(text: str) -> str:
    """Remove trailing commas before } or ] which are illegal in JSON."""
    return _TRAILING_COMMA_RE.sub(r"\1", text)


def clean_json_response(raw: str) -> str:
    """
    Apply all cleaning steps to a raw Gemini response string to produce
    the best possible valid JSON string.
    """
    text = raw.strip()
    text = strip_code_fences(text)
    text = remove_json_comments(text)
    text = repair_escape_sequences(text)
    text = fix_trailing_commas(text)
    return text.strip()


def safe_parse_json(raw: str, context: str = "") -> dict[str, Any] | list | None:
    """
    Attempt to parse JSON from a raw Gemini response.

    Strategy:
    1. Try direct parse
    2. Apply cleaning and retry
    3. Attempt to find the outermost JSON object/array via brace matching
    4. Return None on total failure (never raises)

    Args:
        raw: Raw string from Gemini
        context: Label for log messages

    Returns:
        Parsed Python object, or None if all attempts fail
    """
    label = f"[{context}] " if context else ""

    # --- Attempt 1: direct ---
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # --- Attempt 2: after cleaning ---
    cleaned = clean_json_response(raw)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # --- Attempt 3: extract outermost { ... } or [ ... ] ---
    for start_char, end_char in [('{', '}'), ('[', ']')]:
        start_idx = cleaned.find(start_char)
        end_idx = cleaned.rfind(end_char)
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            fragment = cleaned[start_idx:end_idx + 1]
            try:
                result = json.loads(fragment)
                logger.warning("%sUsed brace-extraction fallback for JSON parse", label)
                return result
            except json.JSONDecodeError:
                pass

    # --- Attempt 4: try to fix remaining escapes more aggressively ---
    try:
        # Replace any remaining problematic sequences
        aggressive = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', cleaned)
        return json.loads(aggressive)
    except json.JSONDecodeError as exc:
        logger.error(
            "%sFailed to parse JSON after all repair attempts. Error: %s. "
            "First 300 chars: %r",
            label, exc, raw[:300]
        )
        return None


def extract_paper_sections(raw: str) -> dict[str, Any]:
    """
    Try to extract research paper fields even from severely malformed JSON.
    Returns whatever fields could be recovered.
    """
    result: dict[str, Any] = {}

    # Try standard parse first
    parsed = safe_parse_json(raw, context="paper_sections")
    if isinstance(parsed, dict):
        return parsed

    # Regex-based field extraction as last resort
    patterns = {
        "title": r'"title"\s*:\s*"([^"]{1,300})"',
        "abstract": r'"abstract"\s*:\s*"([^"]{100,3000})"',
    }
    for field, pattern in patterns.items():
        m = re.search(pattern, raw, re.DOTALL)
        if m:
            result[field] = m.group(1)

    if result:
        logger.warning("Recovered %d fields via regex from malformed JSON", len(result))

    return result
