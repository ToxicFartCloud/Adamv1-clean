# src/ui/components/theme.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, List, Optional

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

from ..state import ui_state
from .style import STYLE
from ..utils.paths import get_data_dir

# Default palette (keys should match STYLE["colors"] you want overridable)
# Mapped to web UI CSS vars in style.css:
#   background      ← --color-bg
#   panel           ← --color-bg-elevated
#   panel_light     ← --color-bg-muted
#   border          ← --border
#   text_primary    ← --color-text
#   text_secondary  ← --color-text-muted
#   accent          ← --color-accent
DEFAULT_THEME = {
    "background": "#0f172a",      # --color-bg
    "panel": "#111c34",           # --color-bg-elevated
    "panel_light": "#15213d",     # --color-bg-muted
    "border": "#242d40",  # --border
    "text_primary": "#e2e8f0",    # --color-text
    "text_secondary": "#94a3b8",  # --color-text-muted
    "accent": "#38bdf8",          # --color-accent
    "accent_fg": "#ffffff",
    # Composer (input area) tokens
    "composer_bg": "#111c34",            # matches elevated panel
    "composer_placeholder": "#94a3b8",   # muted text
    # Header status dot colors
    "status_ok": "#10b981",
    "status_warn": "#f59e0b",
    "status_error": "#ef4444",
    "status_idle": "#94a3b8",
    # Chat bubbles (role-based)
    "bubble_user_bg": "#0b2a42",         # accent-tinted dark for user
    "bubble_user_fg": "#e2f3ff",
    "bubble_assistant_bg": "#222230",    # elevated panel for assistant
    "bubble_assistant_fg": "#e6e6f0",
    # Hover tints for bubbles
    "bubble_user_bg_hover": "#0f3656",
    "bubble_assistant_bg_hover": "#2a2a3a",
    # Sidebar row hover/active
    "sidebar_row_hover_bg": "#15213d",
    "sidebar_row_active_bg": "#1a2a4a",
    # keep existing semantic extras used around the app (search/success)
    "search_hit_bg": "#f7ec6a",
    "search_focus_bg": "#ffe066",
    "success_bg": "#34d399",      # align w/ web success
    "success_fg": "#052e1b",
}

# Optional light palette to mirror web UI
LIGHT_THEME = {
    "background": "#ffffff",
    "panel": "#f7fafc",
    "panel_light": "#f1f5f9",
    "border": "#e2e8f0",
    "text_primary": "#0f172a",
    "text_secondary": "#475569",
    "accent": "#0ea5e9",
    "accent_fg": "#ffffff",
    # Header status dot colors
    "status_ok": "#16a34a",
    "status_warn": "#d97706",
    "status_error": "#dc2626",
    "status_idle": "#64748b",
    # bubbles (light)
    "bubble_user_bg": "#e0f2fe",
    "bubble_user_fg": "#0f172a",
    "bubble_assistant_bg": "#f8fafc",
    "bubble_assistant_fg": "#0f172a",
    "bubble_user_bg_hover": "#dbeafe",
    "bubble_assistant_bg_hover": "#eef2f7",
    # keep semantic extras
    "search_hit_bg": "#fff3b0",
    "search_focus_bg": "#ffe066",
    "success_bg": "#10b981",
    "success_fg": "#052e1b",
}


# ---------- Public wiring ----------


def attach_theme(app) -> None:
    """
    Expose theme management methods on the app instance.
    Idempotent; safe to call multiple times.
    """
    ui_state.setdefault("theme", DEFAULT_THEME.copy())

    app._theme_dir = _theme_dir.__get__(app)
    app._theme_path = _theme_path.__get__(app)  # preset file path
    app._current_theme_path = _current_theme_path.__get__(
        app
    )  # where current theme is serialized
    app._legacy_theme_path = _legacy_theme_path.__get__(
        app
    )  # old ui_theme.json (for migration)

    app._theme_list = _theme_list.__get__(app)
    app._load_theme = _load_theme.__get__(app)
    app._save_theme = _save_theme.__get__(app)
    app._delete_theme = _delete_theme.__get__(app)
    app._apply_theme = _apply_theme.__get__(app)
    app.set_theme_mode = _set_theme_mode.__get__(app)

    # Ensure a theme is loaded into STYLE/colors on first attach
    # (will migrate legacy file if present)
    try:
        app._load_theme()
        app._apply_theme()
    except Exception:
        pass


# ---------- Paths & IO ----------


def _theme_dir(self) -> Path:
    """Directory that stores theme presets."""
    d = get_data_dir() / "themes"
    try:
        d.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return d


def _theme_path(self, name: str) -> Path:
    """File path for a named theme preset."""
    safe = (name or "Unnamed").strip().replace("/", "_").replace("\\", "_")
    return self._theme_dir() / f"{safe}.json"


def _current_theme_path(self) -> Path:
    """File path for the currently active theme snapshot."""
    return self._theme_dir() / "current.json"


def _legacy_theme_path(self) -> Path:
    """
    Backward-compat: where older builds saved ui_theme.json.
    Kept here for a one-time migration.
    """
    return get_data_dir() / "ui_theme.json"


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8")) or {}
    except Exception:
        pass
    return {}


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except Exception:
        pass


# ---------- Core API ----------


def _theme_list(self) -> List[str]:
    """Return the list of available named theme presets (without .json)."""
    try:
        return sorted(
            p.stem for p in self._theme_dir().glob("*.json") if p.name != "current.json"
        )
    except Exception:
        return []


def _load_theme(self, name: Optional[str] = None) -> None:
    """
    Load a theme into ui_state["theme"].
    Order of precedence:
      1) If `name` is given → themes/{name}.json
      2) themes/current.json
      3) (one-time) migrate get_data_dir()/ui_theme.json (legacy)
      4) DEFAULT_THEME
    """
    loaded: Dict[str, Any] = {}

    if name:
        loaded = _read_json(self._theme_path(name))
    if not loaded:
        loaded = _read_json(self._current_theme_path())
    if not loaded:
        # migrate legacy once if found
        legacy = _read_json(self._legacy_theme_path())
        if legacy:
            loaded = legacy
            # persist as current for future sessions
            _write_json(self._current_theme_path(), legacy)

    base = DEFAULT_THEME.copy()
    base.update(loaded if isinstance(loaded, dict) else {})
    ui_state["theme"] = base


def _save_theme(self, name: Optional[str] = None) -> None:
    """
    Save current ui_state["theme"].
    If `name` is given → save as themes/{name}.json AND set as current.
    Otherwise → refresh themes/current.json.
    """
    theme = ui_state.get("theme", {}) or {}
    if not isinstance(theme, dict):
        theme = {}

    if name:
        _write_json(self._theme_path(name), theme)  # named preset
    # Always update current snapshot
    _write_json(self._current_theme_path(), theme)


def _delete_theme(self, name: str) -> None:
    """Delete a named preset. Does not affect the in-memory or current theme."""
    try:
        p = self._theme_path(name)
        if p.exists():
            p.unlink()
    except Exception:
        pass


def _set_theme_mode(self, mode: str = "dark") -> None:
    """
    Swap current theme tokens to a built-in 'dark' or 'light' preset, then apply.
    Look-only; does not change behavior or files.
    """
    base = (ui_state.get("theme") or DEFAULT_THEME).copy()
    preset = DEFAULT_THEME if str(mode).lower() != "light" else LIGHT_THEME
    base.update(preset)
    ui_state["theme"] = base
    try:
        self._apply_theme()
    except Exception:
        pass


def _apply_theme(self) -> None:
    """
    Apply ui_state["theme"] into STYLE["colors"] and update root bg.
    """
    theme = ui_state.get("theme", DEFAULT_THEME)
    colors = STYLE.setdefault("colors", {})
    for key, value in (theme or {}).items():
        if isinstance(value, str):
            colors[key] = value

    # Layout tokens (read by layout.py) — fixed 240px sidebar per UI spec
    layout_tokens = STYLE.setdefault("layout", {})
    layout_tokens.setdefault("sidebar_width", 240)  # px
    layout_tokens.setdefault("chat_ratio_with_canvas", 0.62)
    layout_tokens.setdefault("sash_width", 6)

    try:
        self.root.configure(bg=colors.get("background", DEFAULT_THEME["background"]))
    except Exception:
        pass

    # === Apply defaults to classic Tk + ttk (look-only) ===
    bg = colors.get("background", "#0f172a")
    panel = colors.get("panel", "#111c34")
    muted = colors.get("panel_light", "#15213d")
    border = colors.get("border", "#242d40")  # pre-blended hex
    text = colors.get("text_primary", "#e2e8f0")
    text_m = colors.get("text_secondary", "#94a3b8")
    accent = colors.get("accent", "#38bdf8")

    # --- Typography: match web CSS scale ---
    try:
        # You can tweak these if your CSS changes
        _font_family = "Inter"  # or "Segoe UI", "Noto Sans", fallback picked by Tk
        # CSS reference (approx):
        # --font-xs: 11px, --font-sm: 12px, --font-base: 13px, --font-lg: 15px
        base = tkfont.nametofont("TkDefaultFont")
        textf = tkfont.nametofont("TkTextFont")
        fixed = tkfont.nametofont("TkFixedFont")
        menu = tkfont.nametofont("TkMenuFont")
        head = tkfont.nametofont("TkHeadingFont")

        for fnt in (base, textf, menu):
            fnt.configure(family=_font_family, size=13)  # --font-base
        head.configure(family=_font_family, size=15, weight="bold")  # --font-lg bold
        fixed.configure(size=12)

        # Make Tk use these updated sizes everywhere
        tkfont.nametofont("TkDefaultFont").configure(size=13)
    except Exception:
        pass

    # Classic Tk option database (affects tk.* widgets used across your UI)
    if isinstance(self.root, tk.Misc):
        try:
            opt = self.root.option_add
            # Buttons
            opt("*Button.background", panel)
            opt("*Button.activeBackground", muted)
            opt("*Button.foreground", text)
            opt("*Button.activeForeground", text)
            opt("*Button.highlightThickness", 0)
            opt("*Button.borderWidth", 1)

            # Entries / Text
            opt("*Entry.background", panel)
            opt("*Entry.foreground", text)
            opt("*Entry.insertBackground", text)
            opt("*Entry.highlightThickness", 0)
            opt("*Text.background", panel)
            opt("*Text.foreground", text)
            opt("*Label.background", bg)
            opt("*Label.foreground", text_m)

            # Listboxes (chat history)
            opt("*Listbox.background", panel)
            opt("*Listbox.foreground", text)
            opt("*Listbox.selectBackground", muted)
            opt("*Listbox.selectForeground", text)

            # Scrollbars (classic Tk)
            opt("*Scrollbar.background", panel)  # trough/track
            opt("*Scrollbar.troughColor", panel)  # some Tk builds respect this
            opt("*Scrollbar.activeBackground", muted)  # thumb hover/active
            opt("*Scrollbar.highlightThickness", 0)
            opt("*Scrollbar.borderWidth", 0)

            # Canvas (chat area) edge contrast
            opt("*Canvas.background", muted)
            opt("*Canvas.highlightThickness", 0)

            # Text/Entry selection + caret — match accent
            opt("*Text.selectBackground", accent)
            opt("*Text.selectForeground", colors.get("accent_fg", "#ffffff"))
            opt("*Entry.selectBackground", accent)
            opt("*Entry.selectForeground", colors.get("accent_fg", "#ffffff"))
            opt("*Entry.insertBackground", accent)  # caret color
        except Exception:
            pass

    # ttk styles (if any ttk widgets are present)
    try:
        s = ttk.Style(self.root)
        # spacing scale
        pad_x, pad_y = 12, 8

        # Buttons
        s.configure(
            "TButton",
            background=panel,
            foreground=text,
            bordercolor=border,
            focusthickness=1,
            focuscolor=accent,
            relief="flat",
            padding=(pad_x, pad_y),
        )
        s.map(
            "TButton",
            background=[("active", muted), ("pressed", muted)],
            relief=[("pressed", "flat")],
            focuscolor=[("focus", accent)],
        )

        # Accent variant (if you later set style="Accent.TButton" anywhere)
        s.configure(
            "Accent.TButton",
            background=accent,
            foreground=colors.get("accent_fg", "#ffffff"),
            bordercolor=accent,
            focusthickness=1,
            relief="flat",
            padding=(pad_x, pad_y),
        )
        s.map(
            "Accent.TButton",
            background=[("active", accent), ("pressed", accent)],
            foreground=[("disabled", text_m)],
            focuscolor=[("focus", accent)],
        )

        # Entries
        s.configure(
            "TEntry",
            fieldbackground=panel,
            foreground=text,
            bordercolor=border,
            relief="flat",
            padding=(10, 8),
        )
        s.map(
            "TEntry",
            bordercolor=[("focus", accent)],
            fieldbackground=[("readonly", panel), ("disabled", muted)],
        )

        # Labels / Frames
        s.configure("TLabel", background=bg, foreground=text)
        s.configure("TFrame", background=bg)

        # Combobox (if present)
        s.configure(
            "TCombobox",
            fieldbackground=panel,
            foreground=text,
            bordercolor=border,
            relief="flat",
            padding=(10, 8),
        )
        s.map("TCombobox", bordercolor=[("focus", accent)])

    except Exception:
        pass
