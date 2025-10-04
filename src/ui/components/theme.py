# src/ui/components/theme.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, List, Optional

from ..state import ui_state
from .style import STYLE
from ..utils.paths import get_data_dir

# Default palette (keys should match STYLE["colors"] you want overridable)
DEFAULT_THEME = {
    "background": "#1a1a24",  # Deeper, neutral dark
    "panel": "#222230",
    "panel_light": "#2a2a3a",
    "border": "#3c3c4e",
    "colors": "#3a4a6a",
    "text_primary": "#e6e6f0",  # Crisper white (WCAG AA+ on #1a1a24)
    "text_secondary": "#b0b0c4",
    "accent": "#6c5ce7",  # Softer purple (from "Amethyst")
    "accent_fg": "#ffffff",
    "search_hit_bg": "#f7ec6a",  # Warmer, less jarring yellow
    "search_focus_bg": "#ffe066",
    "success_bg": "#194d33",
    "success_fg": "#d9f2e6",
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


def _apply_theme(self) -> None:
    """
    Apply ui_state["theme"] into STYLE["colors"] and update root bg.
    """
    theme = ui_state.get("theme", DEFAULT_THEME)
    colors = STYLE.setdefault("colors", {})
    for key, value in (theme or {}).items():
        if isinstance(value, str):
            colors[key] = value

    try:
        self.root.configure(bg=colors.get("background", DEFAULT_THEME["background"]))
    except Exception:
        pass
