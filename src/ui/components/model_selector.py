# src/ui/components/model_selector.py
from __future__ import annotations

import logging
import os
from pathlib import Path
import tkinter as tk
from typing import Mapping, Dict, List

logger = logging.getLogger(__name__)

# What we consider as "model files"
_MODEL_EXTS = {".json", ".yaml", ".yml", ".bin", ".gguf", ".pt", ".safetensors"}


def render_model_selector(app, parent: tk.Misc, colors: Mapping[str, str]) -> None:
    """
    Render the model dropdown inside the given parent container.

    Priority for options:
    1) If app._model_map already set by model_sync, use it.
    2) Else, discover local models from filesystem and build a map.
    3) If still empty, show: ["Auto (Backend)"].
    """
    # Ensure variables exist
    if not hasattr(app, "model_var") or not isinstance(
        getattr(app, "model_var"), tk.StringVar
    ):
        app.model_var = tk.StringVar(value="")

    # If no map from model_sync, try to discover locally
    model_map: Dict[str, str] = (
        getattr(app, "_model_map", {}) or _discover_local_models()
    )

    # Always keep a safe fallback
    if not model_map:
        model_map = {"Auto (Backend)": ""}

    # Persist back so other components can use it
    app._model_map = model_map

    # UI
    tk.Label(
        parent,
        text="Model:",
        fg=colors["text_secondary"],
        bg=colors["background"],
        font=("Segoe UI", 10),
    ).pack(side="right", padx=(0, 6))

    options: List[str] = list(model_map.keys())
    # Keep existing selection if valid; otherwise select first
    current = app.model_var.get()
    if current not in options:
        app.model_var.set(options[0])

    app.model_menu = tk.OptionMenu(parent, app.model_var, *options)
    app.model_menu.configure(
        bg=colors["panel"],
        fg=colors["text_primary"],
        activebackground=colors.get("panel_light", colors["panel"]),
        activeforeground=colors["text_primary"],
        highlightthickness=1,
        highlightbackground=colors["border"],
        relief="flat",
        bd=0,
        cursor="hand2",
        width=24,
    )

    # Rebuild underlying menu to wire our handler + tint hover
    menu = app.model_menu["menu"]
    menu.delete(0, "end")
    try:
        menu.configure(
            tearoff=0,
            bg=colors["panel"],
            fg=colors["text_primary"],
            activebackground=colors.get("panel_light", colors["panel"]),
            activeforeground=colors["text_primary"],
            relief="flat",
            bd=0,
        )
    except Exception:
        pass
    for label in options:
        menu.add_command(
            label=label, command=lambda v=label: _apply_model_choice(app, v)
        )

    app.model_menu.pack(side="left", padx=6)


def _apply_model_choice(app, label: str) -> None:
    """Set the model label and notify any sync hooks if present."""
    try:
        app.model_var.set(label)
    except Exception:
        pass

    # Prefer existing handler from model_sync if present
    if hasattr(app, "_set_model_label") and callable(app._set_model_label):
        try:
            app._set_model_label(label)
            return
        except Exception:
            logger.exception("app._set_model_label failed")

    # Fallback: if a generic hook exists
    if hasattr(app, "_on_model_changed") and callable(app._on_model_changed):
        try:
            app._on_model_changed(label, app._model_map.get(label, ""))
            return
        except Exception:
            logger.exception("app._on_model_changed failed")

    # Otherwise, silent no-op — UI state already reflects the choice.


def _discover_local_models() -> Dict[str, str]:
    """
    Discover local models from common locations:

    - $ADAM_MODELS_DIR
    - <project_root>/models
    - <project_root>/src/models
    - CWD/models

    Returns: {display_name: absolute_path}
    """
    candidates: List[Path] = []

    # 1) Environment override
    env_dir = os.environ.get("ADAM_MODELS_DIR")
    if env_dir:
        candidates.append(Path(env_dir))

    # 2) Project root based on this file path
    #   this file: <root>/src/ui/components/model_selector.py
    here = Path(__file__).resolve()
    # parents: [components, ui, src, <root>]
    project_root = here.parents[3] if len(here.parents) >= 4 else Path.cwd()

    for p in [
        project_root / "models",
        project_root / "src" / "models",
        Path.cwd() / "models",
    ]:
        candidates.append(p)

    found: Dict[str, str] = {}
    seen = set()

    for base in candidates:
        try:
            if not base.exists() or not base.is_dir():
                continue
            for item in sorted(base.iterdir()):
                # Directory with recognizable files → use directory name as label
                if item.is_dir():
                    if _dir_has_models(item):
                        label = item.name
                        abspath = str(item.resolve())
                        if label not in seen:
                            found[label] = abspath
                            seen.add(label)
                    continue

                # File with known extension → use stem
                if item.is_file() and item.suffix.lower() in _MODEL_EXTS:
                    label = item.stem
                    abspath = str(item.resolve())
                    if label not in seen:
                        found[label] = abspath
                        seen.add(label)
        except Exception:
            # Never fail discovery
            continue

    return found


def _dir_has_models(path: Path) -> bool:
    """Heuristic: A directory 'has models' if it contains any known model files."""
    try:
        for sub in path.iterdir():
            if sub.is_file() and sub.suffix.lower() in _MODEL_EXTS:
                return True
    except Exception:
        pass
    return False


__all__ = ["render_model_selector"]
