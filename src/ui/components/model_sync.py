from __future__ import annotations

import tkinter as tk
from typing import Iterable, Tuple, Dict, List

from ..state import ui_state

DEFAULT_OPTIONS: List[Tuple[str, str]] = [("Auto (Backend)", "auto")]


def _ensure_state() -> Dict[str, object]:
    state = ui_state.setdefault("model", {})
    available = state.get("available")
    if not isinstance(available, list) or not available:
        available = list(DEFAULT_OPTIONS)
    state["available"] = available
    selected = state.get("selected_label")
    mapping = dict(available)
    if not selected or selected not in mapping:
        selected = available[0][0]
    state["selected_label"] = selected
    return state


def _init_models(self) -> None:
    state = _ensure_state()
    self._set_available_models(state.get("available", DEFAULT_OPTIONS), persist=False)


def attach_model_sync(app) -> None:
    state = _ensure_state()
    app.model_var = tk.StringVar(value=state["selected_label"])
    app.model_var.trace_add("write", lambda *_: _sync_model_var(app))
    app._init_models = _init_models.__get__(app)
    app._get_selected_model = _get_selected_model.__get__(app)
    app._set_available_models = _set_available_models.__get__(app)
    app.backend_list_models = backend_list_models.__get__(app)
    app._refresh_models_from_backend = _refresh_models_from_backend.__get__(app)
    app._set_model_label = _set_model_label.__get__(app)
    app._model_map = {}
    app._set_available_models(state.get("available", DEFAULT_OPTIONS), persist=False)
    if not hasattr(app, "model_menu") and hasattr(app, "model_var"):
        app.model_var.set(state["selected_label"])


def _normalize_models(models: Iterable) -> List[Tuple[str, str]]:
    normalized: List[Tuple[str, str]] = []
    seen = set()
    for item in models or []:
        if isinstance(item, tuple) and len(item) == 2:
            label, model_id = item
        elif isinstance(item, dict):
            model_id = item.get("id") or item.get("model_id") or item.get("name")
            label = item.get("name") or model_id
        elif isinstance(item, str):
            label = model_id = item
        else:
            continue
        if model_id and (label, model_id) not in seen:
            normalized.append((label, model_id))
            seen.add((label, model_id))
    mapping = dict(normalized)
    if "Auto (Backend)" not in mapping:
        normalized.insert(0, ("Auto (Backend)", "auto"))
    return normalized


def _set_available_models(self, models: Iterable, *, persist: bool = True) -> None:
    normalized = _normalize_models(models)
    mapping = dict(normalized)
    self._model_map = mapping
    state = _ensure_state()
    if persist:
        state["available"] = normalized
    selected = state.get("selected_label", normalized[0][0])
    if selected not in mapping:
        selected = normalized[0][0]
    state["selected_label"] = selected
    if self.model_var.get() != selected:
        self.model_var.set(selected)
    if hasattr(self, "model_menu"):
        menu = self.model_menu["menu"]
        menu.delete(0, "end")
        for label in mapping.keys():
            menu.add_command(
                label=label, command=lambda v=label: self._set_model_label(v)
            )


def _set_model_label(self, label: str) -> None:
    if self.model_var.get() != label:
        self.model_var.set(label)
    state = _ensure_state()
    state["selected_label"] = label


def _sync_model_var(app, *_args) -> None:
    state = _ensure_state()
    state["selected_label"] = app.model_var.get()


def _get_selected_model(self) -> str:
    state = _ensure_state()
    return dict(state.get("available", DEFAULT_OPTIONS)).get(
        state.get("selected_label"), "auto"
    )


def backend_list_models(self):
    return [
        {"id": "llama3.1:8b", "name": "Llama 3.1 8B"},
        {"id": "qwen2.5:7b", "name": "Qwen 2.5 7B"},
        "phi3:mini",
    ]


def _refresh_models_from_backend(self) -> None:
    try:
        fetch = getattr(self, "backend_list_models", None)
        if callable(fetch):
            models = fetch()
            self._set_available_models(models)
    except Exception:
        pass


__all__ = ["attach_model_sync"]
