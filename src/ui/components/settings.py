# src/ui/components/settings.py
"""
Settings behavior wiring — theme editor, timestamp toggle, and preferences.
This module does not render visible UI; it wires actions used by chat, sidebar, etc.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import colorchooser, messagebox

from .theme import attach_theme, DEFAULT_THEME
from ..state import ui_state


def render_settings(app) -> None:
    """
    Attach settings-related behaviors to the app.
    This module does not render visible UI; it wires settings actions
    (theme dialog, timestamp toggle) used elsewhere.
    """
    # Ensure theme hooks exist (idempotent)
    if not hasattr(app, "_apply_theme") or not hasattr(app, "_save_theme"):
        attach_theme(app)

    _attach_settings_methods(app)


def _attach_settings_methods(app) -> None:
    app._open_theme_dialog = _open_theme_dialog.__get__(app)
    app._toggle_timestamps = _toggle_timestamps.__get__(app)


def _open_theme_dialog(self) -> None:
    """
    Open a theme editor that prompts for key colors.
    Applies and saves the theme on completion.
    """
    # Ensure theme is loaded
    theme = ui_state.setdefault("theme", DEFAULT_THEME.copy())

    # Define editable theme keys with human-readable labels
    editable = [
        ("background", "Window / Background"),
        ("panel", "Sidebar / Panel"),
        ("panel_light", "Canvas Background"),
        ("text_primary", "Main Text"),
        ("text_secondary", "Secondary Text"),
        ("accent", "Button Background"),
        ("accent_fg", "Button Text"),
        ("border", "Borders"),
    ]

    # Confirm before opening multiple dialogs
    try:
        if not messagebox.askyesno(
            "Edit Theme",
            "This will open a series of color pickers.\nContinue?",
            parent=self.root,
        ):
            return
    except Exception:
        pass  # Silent fallback if messagebox fails

    changed = False
    for key, label in editable:
        current = theme.get(key, DEFAULT_THEME.get(key, "#ffffff"))
        try:
            _rgb, hexval = colorchooser.askcolor(
                title=f"Theme: {label}", initialcolor=current, parent=self.root
            )
        except Exception:
            hexval = None
        if hexval and hexval.lower() != current.lower():
            theme[key] = hexval
            changed = True

    if not changed:
        return

    ui_state["theme"] = theme
    try:
        self._save_theme()
        self._apply_theme()
        # Optional: notify user
        # messagebox.showinfo("Theme Updated", "Theme applied and saved.", parent=self.root)
    except Exception:
        pass


def _toggle_timestamps(self) -> None:
    """
    Toggle per-message timestamps, update UI labels, and persist preference.
    """
    show = not bool(getattr(self, "show_timestamps", True))
    self.show_timestamps = show

    # Update timestamp button text if it exists
    try:
        if hasattr(self, "timestamp_button") and isinstance(
            self.timestamp_button, tk.Button
        ):
            text = "Timestamps: ON" if show else "Timestamps: OFF"
            self.timestamp_button.configure(text=text)
    except Exception:
        pass

    # Refresh responsive toolbar and overflow menu
    try:
        if hasattr(self, "_refresh_kebab_labels"):
            self._refresh_kebab_labels()
        if hasattr(self, "_toolbar_responsive"):
            self._toolbar_responsive()
    except Exception:
        pass

    # Persist preference
    prefs = ui_state.setdefault("preferences", {})
    prefs["show_timestamps"] = show
    try:
        if hasattr(self, "_save_chats") and callable(self._save_chats):
            self._save_chats()
    except Exception:
        pass


__all__ = ["render_settings"]
