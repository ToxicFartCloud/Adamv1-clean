# src/ui/utils/paths.py
"""
Cross-platform path utilities for user data, config, cache, logs, and models.
Designed for Linux/Bazzite (XDG) but works everywhere.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import List, Optional, Union

# ---- App identity ----
APP_NAME = "Adam"
APP_AUTHOR = "AdamProject"  # change if you want vendor/org tagging


# ---- XDG / platformdirs helpers ----
def _xdg_data_home() -> Path:
    x = os.environ.get("XDG_DATA_HOME")
    if x:
        return Path(x)
    # Fallbacks by platform
    if os.name == "nt":  # Windows
        base = os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming"
        return Path(base)
    if os.name == "posix":
        return Path.home() / ".local" / "share"
    return Path.home() / ".adam"


def _xdg_config_home() -> Path:
    x = os.environ.get("XDG_CONFIG_HOME")
    if x:
        return Path(x)
    if os.name == "nt":
        base = os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming"
        return Path(base)
    if os.name == "posix":
        return Path.home() / ".config"
    return Path.home() / ".adam"


def _xdg_cache_home() -> Path:
    x = os.environ.get("XDG_CACHE_HOME")
    if x:
        return Path(x)
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local"
        return Path(base) / "Cache"
    if os.name == "posix":
        return Path.home() / ".cache"
    return Path.home() / ".adam" / "cache"


# Prefer platformdirs if present
try:
    from platformdirs import (
        user_data_dir,
        user_config_dir,
        user_cache_dir,
        user_log_dir,
    )  # type: ignore

    def _data_root() -> Path:
        return Path(user_data_dir(APP_NAME, APP_AUTHOR))

    def _config_root() -> Path:
        return Path(user_config_dir(APP_NAME, APP_AUTHOR))

    def _cache_root() -> Path:
        return Path(user_cache_dir(APP_NAME, APP_AUTHOR))

    def _logs_root() -> Path:
        return Path(user_log_dir(APP_NAME, APP_AUTHOR))
except Exception:

    def _data_root() -> Path:
        return _xdg_data_home() / APP_NAME

    def _config_root() -> Path:
        return _xdg_config_home() / APP_NAME

    def _cache_root() -> Path:
        return _xdg_cache_home() / APP_NAME

    def _logs_root() -> Path:
        # XDG doesn’t define logs dir; put under cache by convention
        return _xdg_cache_home() / APP_NAME / "logs"


# ---- Public roots ----
def get_data_dir() -> Path:
    p = _data_root()
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_config_dir() -> Path:
    p = _config_root()
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_cache_dir() -> Path:
    p = _cache_root()
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_logs_dir() -> Path:
    p = _logs_root()
    p.mkdir(parents=True, exist_ok=True)
    return p


# ---- Common subpaths ----
def get_state_path() -> Path:
    """Unified persistent UI state (projects, chats, prefs)."""
    return get_data_dir() / "state.json"


def get_themes_dir() -> Path:
    d = get_data_dir() / "themes"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_chats_dir() -> Path:
    d = get_data_dir() / "chats"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_index_path() -> Path:
    """Optional index file if you index chats separately."""
    return get_data_dir() / "saved_chats.jsonl"


# ---- Atomic writes (avoid corruption) ----
def atomic_write_text(
    path: Union[str, Path], text: str, encoding: str = "utf-8"
) -> None:
    """Write text atomically (to avoid partial/corrupt files)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", delete=False, encoding=encoding, dir=str(path.parent)
    ) as tmp:
        tmp.write(text)
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp_path = Path(tmp.name)
    tmp_path.replace(path)


def atomic_write_json(path: Union[str, Path], obj) -> None:
    """Write JSON atomically with pretty indent."""
    atomic_write_text(path, json.dumps(obj, indent=2))


# ---- Project root & models discovery ----
def _find_project_root(start: Optional[Path] = None) -> Path:
    """
    Walk upward from `start` (or CWD) looking for a project marker.
    Returns first directory that contains one of: pyproject.toml, .git, src/.
    Falls back to CWD.
    """
    cur = (start or Path.cwd()).resolve()
    markers = {"pyproject.toml", ".git"}
    while True:
        if any((cur / m).exists() for m in markers) or (cur / "src").exists():
            return cur
        if cur.parent == cur:
            return (start or Path.cwd()).resolve()
        cur = cur.parent


def get_models_dirs(start: Optional[Path] = None) -> List[Path]:
    """
    Candidate directories where local models might live.
    Order of precedence:
      1) ADAM_MODELS_DIRS (comma-separated)
      2) <project>/models
      3) <project>/src/models
      4) ~/.local/share/Adam/models  (inside data dir)
    """
    # 1) Explicit env var
    env = os.environ.get("ADAM_MODELS_DIRS")
    if env:
        paths = [Path(p).expanduser().resolve() for p in env.split(",") if p.strip()]
    else:
        # 2/3) Project-relative
        root = _find_project_root(start)
        candidates = [root / "models", root / "src" / "models"]
        paths = [p.resolve() for p in candidates]

    # 4) App data fallback
    paths.append((get_data_dir() / "models").resolve())

    # Dedupe while preserving order
    seen = set()
    uniq: List[Path] = []
    for p in paths:
        if p not in seen:
            seen.add(p)
            uniq.append(p)
    return uniq


def ensure_dir(path: Union[str, Path]) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p
