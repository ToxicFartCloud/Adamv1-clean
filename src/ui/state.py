# src/ui/state.py
"""
Global UI state (single source of truth).

- `ui_state` is a plain dict used across components.
- `ensure_defaults()` initializes required keys and delegates
  history/projects bootstrapping to components.history.initialize_history_state(),
  imported lazily to avoid circular imports.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

ui_state: Dict[str, Any] = {}


def ensure_defaults(config_path: Optional[str] = None) -> None:
    """
    Ensure required keys exist in ui_state with sane defaults.
    Safe to call multiple times (idempotent).

    Args:
        config_path: optional path to a user config file (reserved for future use).
    """
    # Core chat structure (legacy compatibility)
    _setdefault_typed("chats", list, [{"id": 1, "title": "Chat 1"}])
    _setdefault_typed("active_chat_id", int, 1)
    _setdefault_typed("chat_messages", dict, {})

    # Preferences
    prefs = ui_state.setdefault("preferences", {})
    if not isinstance(prefs, dict):
        prefs = {}
        ui_state["preferences"] = prefs
    prefs.setdefault("show_timestamps", True)

    # Theme storage (theme.attach_theme will merge effective colors to STYLE)
    ui_state.setdefault(
        "theme", {}
    )  # actual defaults come from components.theme.DEFAULT_THEME

    # Defer project/chat history bootstrapping to components.history
    # Import lazily to avoid circular imports at module import time.
    try:
        from .components.history import initialize_history_state  # type: ignore

        initialize_history_state()
    except Exception:
        # If history module fails to import/initialize, keep legacy defaults above.
        # The fallback UI should still run; full UI may rely on fallback console.
        pass


# -------- helpers --------


def _setdefault_typed(key: str, typ, default_value):
    """
    Like dict.setdefault, but if an existing value exists with the wrong type,
    it will be replaced by `default_value`.
    """
    cur = ui_state.get(key)
    if not isinstance(cur, typ):
        ui_state[key] = default_value
