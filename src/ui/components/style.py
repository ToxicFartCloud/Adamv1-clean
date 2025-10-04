# src/ui/components/style.py
"""
Design tokens — SINGLE SOURCE OF TRUTH for UI appearance.
"""

import tkinter.font as tkfont
from typing import Dict, Any


def _get_font_family() -> str:
    """Safely detect font family — works even if called before Tk root exists."""
    try:
        families = tkfont.families()
        for candidate in ["Segoe UI", "Helvetica Neue", "Helvetica", "Arial"]:
            if candidate in families:
                return candidate
    except (RuntimeError, Exception):
        # RuntimeError: called before Tk root exists
        # Exception: other font system issues
        pass
    return "TkDefaultFont"


# Get font family safely (may be TkDefaultFont if too early)
FONT_FAMILY = _get_font_family()

# Base spacing
_BASE_SPACING = {
    "xxs": 2,
    "xs": 4,
    "s": 8,
    "m": 12,
    "l": 16,
    "xl": 24,
    "xxl": 32,
    "inner": 6,
    "widget": 8,
    "outer": 16,
}

_spacing_scale = 1.0


class DynamicSpacing:
    def __getitem__(self, key):
        base = _BASE_SPACING.get(key, 8)
        return int(base * _spacing_scale)

    def __setitem__(self, key, value):
        _BASE_SPACING[key] = value

    def keys(self):
        return _BASE_SPACING.keys()

    def get(self, key, default=8):
        return self[key] if key in _BASE_SPACING else default


# ✅ FULL font definitions — no missing keys
STYLE: Dict[str, Any] = {
    "colors": {},
    "fonts": {
        "title": (FONT_FAMILY, 14, "bold"),
        "subtitle": (FONT_FAMILY, 12, "bold"),  # ← MUST be present
        "body": (FONT_FAMILY, 12),
        "small": (FONT_FAMILY, 10),
        "input": (FONT_FAMILY, 12),
        "button": (FONT_FAMILY, 11, "bold"),
        "code": ("Consolas", 11),
        "main": (FONT_FAMILY, 12),
        "main_bold": (FONT_FAMILY, 12, "bold"),
    },
    "spacing": DynamicSpacing(),
    "radius": {"small": 4, "medium": 8},
    "layout": {
        "sidebar_width": 280,
        "canvas_min_width": 320,
        "chat_ratio_with_canvas": 0.65,
        "chat_ratio_solo": 0.98,
        "sash_width": 6,
    },
}

STYLE["padding"] = STYLE["spacing"]


def set_spacing_scale(scale: float):
    global _spacing_scale
    _spacing_scale = max(0.5, min(2.0, scale))
