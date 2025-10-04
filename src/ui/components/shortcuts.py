# src/ui/components/shortcuts.py
from __future__ import annotations

import tkinter as tk
from types import MethodType

# Pairs of (Control, Command) equivalents
CONTROL_BINDINGS = [
    ("<Control-Return>", "<Command-Return>"),
    ("<Control-n>", "<Command-n>"),
    ("<Control-1>", "<Command-1>"),
    ("<Control-3>", "<Command-3>"),
    ("<Control-t>", "<Command-t>"),
]


def attach_shortcuts(app) -> None:
    """
    Attach global and widget-specific keyboard shortcuts.
    Safe to call before widgets exist; entry bindings are deferred.
    """
    # Expose helper so other components can re-run if needed
    app._bind_entry_shortcuts = MethodType(_bind_entry_shortcuts, app)

    # Global bindings (root-level, fire anywhere)
    _maybe_bind_global(app, "<Control-Return>", "_on_send_shortcut")
    _maybe_bind_global(app, "<Command-Return>", "_on_send_shortcut")

    _maybe_bind_global(app, "<Control-n>", "_new_chat")
    _maybe_bind_global(app, "<Command-n>", "_new_chat")

    _maybe_bind_global(app, "<F2>", "_start_rename_chat")

    _maybe_bind_global(app, "<Control-1>", "_toggle_sidebar")
    _maybe_bind_global(app, "<Command-1>", "_toggle_sidebar")

    _maybe_bind_global(app, "<Control-3>", "_toggle_canvas")
    _maybe_bind_global(app, "<Command-3>", "_toggle_canvas")

    _maybe_bind_global(app, "<Control-t>", "_toggle_timestamps")
    _maybe_bind_global(app, "<Command-t>", "_toggle_timestamps")

    # Entry-specific (needs self.entry). Defer until created by chat.render_chat.
    app.root.after(50, app._bind_entry_shortcuts)


def _bind_entry_shortcuts(self) -> None:
    """Bind shortcuts that require the chat entry widget; retry if not ready yet."""
    entry = getattr(self, "entry", None)
    if not isinstance(entry, tk.Text):
        # Try again shortly; render_chat may not have created it yet.
        try:
            self.root.after(100, self._bind_entry_shortcuts)
        except Exception:
            pass
        return

    # Allow Shift+Enter to insert newline (handled by widget)
    try:
        entry.bind("<Shift-Return>", lambda e: entry.insert("insert", "\n"))
    except Exception:
        pass

    # Enter submits (chat handler expects event)
    try:
        entry.bind("<Return>", getattr(self, "_handle_return"))
    except Exception:
        pass


# ---------------- helpers ----------------


def _maybe_bind_global(app, sequence: str, handler_name: str) -> None:
    """Bind a global accelerator if the handler exists on app."""
    handler = getattr(app, handler_name, None)
    if not callable(handler):
        return

    def wrapper(_event):
        res = handler()
        return res if res is not None else "break"

    try:
        app.root.bind_all(sequence, wrapper)
    except Exception:
        pass


__all__ = ["attach_shortcuts"]
