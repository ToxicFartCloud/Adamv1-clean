# src/ui/components/search.py
from __future__ import annotations

import logging
import tkinter as tk
from types import MethodType
from typing import List, Tuple

from .style import STYLE

logger = logging.getLogger(__name__)

Hit = Tuple[tk.Text, str, str]  # (widget, start_index, end_index)


def attach_search(app) -> None:
    """Attach in-chat search helpers to the app namespace."""
    # Local state on app (not in ui_state)
    if not hasattr(app, "_search_var") or not isinstance(
        getattr(app, "_search_var"), tk.StringVar
    ):
        app._search_var = tk.StringVar(value="")
    if not hasattr(app, "_search_hits"):
        app._search_hits: List[Hit] = []
    if not hasattr(app, "_search_pos"):
        app._search_pos = -1

    bindings = {
        "_search_clear": _search_clear,
        "_search_scan": _search_scan,
        "_search_goto": _search_goto,
        "_search_next": _search_next,
        "_search_prev": _search_prev,
    }
    for name, func in bindings.items():
        setattr(app, name, MethodType(func, app))


def _search_clear(self) -> None:
    """Clear search highlights and reset state."""
    self._search_hits = []
    self._search_pos = -1
    try:
        for rec in getattr(self, "_messages", {}).values():
            tw = rec.get("text_widget")
            if not tw:
                continue
            try:
                tw.tag_delete("search_hit")
                tw.tag_delete("search_focus")
            except Exception:
                pass
    except Exception:
        pass


def _search_scan(self) -> None:
    """Scan all message widgets for the current query and mark hits."""
    query = (
        getattr(self, "_search_var").get() if hasattr(self, "_search_var") else ""
    ).strip()
    hits: List[Hit] = []
    if not query:
        self._search_hits = []
        self._search_pos = -1
        # Also clear any stale highlighting
        _clear_all_tags(self)
        return

    # Colors for highlights (fallbacks if theme lacks entries)
    c = STYLE["colors"]
    hit_bg = c.get("search_hit_bg", "#ffe48a")
    focus_bg = c.get("search_focus_bg", "#ffd24a")

    for rec in getattr(self, "_messages", {}).values():
        tw = rec.get("text_widget")
        if not isinstance(tw, tk.Text):
            continue
        try:
            tw.tag_delete("search_hit")
            tw.tag_delete("search_focus")
            start = "1.0"
            while True:
                idx = tw.search(query, start, stopindex="end", nocase=True)
                if not idx:
                    break
                end = f"{idx}+{len(query)}c"
                tw.tag_add("search_hit", idx, end)
                hits.append((tw, idx, end))
                start = end
            tw.tag_config("search_hit", background=hit_bg)
            tw.tag_config("search_focus", background=focus_bg)
        except Exception:
            continue

    self._search_hits = hits
    self._search_pos = -1


def _search_goto(self, step: int) -> None:
    """Move focus to next/previous hit."""
    hits = getattr(self, "_search_hits", [])
    if not hits:
        self._search_scan()
        hits = getattr(self, "_search_hits", [])
        if not hits:
            return

    pos = getattr(self, "_search_pos", -1)
    pos = (pos + step) % len(hits)

    # Clear previous focus tag on all widgets
    for tw, _, _ in hits:
        try:
            tw.tag_remove("search_focus", "1.0", "end")
        except Exception:
            pass

    tw, idx, end = hits[pos]
    try:
        tw.tag_add("search_focus", idx, end)
        tw.see(idx)
        tw.focus_set()
    except Exception:
        pass

    self._search_pos = pos


def _search_next(self) -> None:
    """Jump to the next hit."""
    query = (
        getattr(self, "_search_var").get() if hasattr(self, "_search_var") else ""
    ).strip()
    if query and not getattr(self, "_search_hits", []):
        self._search_scan()
    self._search_goto(+1)


def _search_prev(self) -> None:
    """Jump to the previous hit."""
    query = (
        getattr(self, "_search_var").get() if hasattr(self, "_search_var") else ""
    ).strip()
    if query and not getattr(self, "_search_hits", []):
        self._search_scan()
    self._search_goto(-1)


# Helpers
def _clear_all_tags(self) -> None:
    try:
        for rec in getattr(self, "_messages", {}).values():
            tw = rec.get("text_widget")
            if not isinstance(tw, tk.Text):
                continue
            try:
                tw.tag_delete("search_hit")
                tw.tag_delete("search_focus")
            except Exception:
                pass
    except Exception:
        pass


__all__ = ["attach_search"]
