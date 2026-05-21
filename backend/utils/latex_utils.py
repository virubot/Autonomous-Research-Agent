"""
LaTeX formatting and escaping utilities to prevent compile failures and injection attacks.
"""
from __future__ import annotations

import re

LATEX_ESCAPE_MAP = {
    "&":  r"\&",
    "%":  r"\%",
    "$":  r"\$",
    "#":  r"\#",
    "_":  r"\_",
    "{":  r"\{",
    "}":  r"\}",
    "~":  r"\textasciitilde{}",
    "^":  r"\textasciicircum{}",
    "\\": r"\textbackslash{}",
    "<":  r"\textless{}",
    ">":  r"\textgreater{}",
}

_LATEX_ESCAPE_RE = re.compile(
    "|".join(re.escape(k) for k in sorted(LATEX_ESCAPE_MAP, key=len, reverse=True))
)


def latex_escape(text: str) -> str:
    """Escape special LaTeX characters in plain text (not inside math mode)."""
    if not isinstance(text, str):
        text = str(text)
    return _LATEX_ESCAPE_RE.sub(lambda m: LATEX_ESCAPE_MAP[m.group()], text)


def latex_escape_reference(text: str) -> str:
    """
    Escape a reference string for use inside \\bibitem.
    Conservative — preserves italic/bold macros and keeps DOI urls fully functional.
    """
    if not isinstance(text, str):
        text = str(text)
    escapes = [
        ("&", r"\&"),
        ("%", r"\%"),
        ("#", r"\#"),
        ("~", r"\textasciitilde{}"),
        ("^", r"\textasciicircum{}"),
    ]
    for char, replacement in escapes:
        text = text.replace(char, replacement)
    return text
