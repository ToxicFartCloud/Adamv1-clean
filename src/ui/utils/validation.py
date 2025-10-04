# src/ui/utils/validation.py
"""Validation and parsing helpers for Adam UI."""

from __future__ import annotations

import re
from typing import List, Tuple

# GitHub-style fenced blocks:
# - supports ``` or ~~~ with length >= 3
# - optional language token after fence
# - optional trailing attributes on the same line
# - non-greedy capture of the code until a matching fence of the same length/char
_FENCE_RE = re.compile(
    r"""
    ^(?P<fence>(`{3,}|~{3,}))       # opening fence (backticks or tildes, len>=3)
    [ \t]*                          # optional spaces
    (?P<lang>[A-Za-z0-9_+\-\.]*)?   # optional language token
    [^\n]*                          # optional rest-of-line (attributes etc.)
    \n                              # end of fence line
    (?P<code>.*?)                   # code block (non-greedy)
    \n(?P=fence)[ \t]*$             # matching closing fence at start of line
    """,
    re.MULTILINE | re.VERBOSE | re.DOTALL,
)


def extract_code_blocks(text: str) -> List[str]:
    """
    Return only the code contents from fenced blocks in `text`.

    Compatible with previous behavior:
    - Returns a list[str] (code bodies only).
    - Ignores language; use extract_code_blocks_with_lang for that.
    """
    if not text:
        return []
    return [
        m.group("code").rstrip("\n")
        for m in _FENCE_RE.finditer(_normalize_newlines(text))
    ]


def extract_code_blocks_with_lang(text: str) -> List[Tuple[str, str]]:
    """
    Like extract_code_blocks, but also returns the language hint ('' if none).

    Returns:
        List of (language, code) tuples.
    """
    if not text:
        return []
    out: List[Tuple[str, str]] = []
    for m in _FENCE_RE.finditer(_normalize_newlines(text)):
        lang = (m.group("lang") or "").strip()
        code = (m.group("code") or "").rstrip("\n")
        out.append((lang, code))
    return out


# ---- helpers ----


def _normalize_newlines(s: str) -> str:
    """Normalize to LF so regex anchors behave as expected."""
    return s.replace("\r\n", "\n").replace("\r", "\n")
