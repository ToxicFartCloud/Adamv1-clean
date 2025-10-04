from __future__ import annotations

import importlib
import importlib.util
import logging
import pkgutil
import sys
import types
from pathlib import Path
from typing import Any, Dict, List

PLUGIN_NAMESPACE = "plugins"
FALLBACK_NAMESPACE = "adam_tools.plugins"
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PLUGIN_DIR = PROJECT_ROOT / "plugins"

logger = logging.getLogger("adam")


def _import_from_path(name: str, file_path: Path):
    module_name = f"{PLUGIN_NAMESPACE}.{name}"
    if PLUGIN_NAMESPACE not in sys.modules:
        pkg = types.ModuleType(PLUGIN_NAMESPACE)
        pkg.__path__ = [str(PLUGIN_DIR)]  # type: ignore[attr-defined]
        sys.modules[PLUGIN_NAMESPACE] = pkg
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if not spec or not spec.loader:
        raise ImportError(f"Could not load spec for plugin '{name}'")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


def load_plugin_module(name: str):
    """Return the module object for the given plugin, searching filesystem first."""
    if PLUGIN_DIR.is_dir():
        file_candidate = PLUGIN_DIR / f"{name}.py"
        package_init = PLUGIN_DIR / name / "__init__.py"
        if file_candidate.is_file():
            return _import_from_path(name, file_candidate)
        if package_init.is_file():
            return _import_from_path(name, package_init)

    try:
        return importlib.import_module(f"{FALLBACK_NAMESPACE}.{name}")
    except ImportError:
        raise


def load_plugin(name: str, with_metadata: bool, plugins: List[Dict[str, Any]]) -> None:
    try:
        module = load_plugin_module(name)
    except Exception as exc:
        logger.warning("Could not load plugin '%s': %s", name, exc)
        return

    entry: Dict[str, Any] = {"name": name}
    meta = getattr(module, "METADATA", None)
    if isinstance(meta, dict):
        entry.update(meta)
    elif with_metadata:
        entry.update(
            {
                "label": name.replace("_", " ").title(),
                "description": f"Plugin: {name}",
                "ui_action": True,
            }
        )

    if isinstance(meta, dict) and not meta.get("executable", True):
        return

    plugins.append(entry)


def discover_plugins(with_metadata: bool = False) -> List[Dict[str, Any]]:
    plugins: List[Dict[str, Any]] = []
    seen = set()

    if PLUGIN_DIR.is_dir():
        for entry in sorted(PLUGIN_DIR.iterdir(), key=lambda p: p.name.lower()):
            if entry.name == "__pycache__":
                continue
            if (
                entry.is_file()
                and entry.suffix == ".py"
                and entry.name != "__init__.py"
            ):
                name = entry.stem
            elif entry.is_dir() and (entry / "__init__.py").is_file():
                name = entry.name
            else:
                continue
            if name in seen:
                continue
            load_plugin(name, with_metadata, plugins)
            seen.add(name)

    try:
        fallback_pkg = importlib.import_module(FALLBACK_NAMESPACE)
        for _, name, _ in pkgutil.iter_modules(fallback_pkg.__path__):
            if name in seen:
                continue
            load_plugin(name, with_metadata, plugins)
            seen.add(name)
    except ImportError:
        pass

    return plugins


def check_plugin_health() -> Dict[str, Any]:
    """Non-executing plugin health report. Only checks import + run() signature."""
    plugins = discover_plugins(with_metadata=False)
    health_report: Dict[str, Any] = {
        "ok": [],
        "missing_run": [],
        "import_error": [],
        "not_callable": [],
    }

    for plugin in plugins:
        name = plugin["name"]
        try:
            module = load_plugin_module(name)

            meta = getattr(module, "METADATA", None)
            if isinstance(meta, dict) and not meta.get("executable", True):
                health_report["ok"].append(name)
                continue

            if not hasattr(module, "run"):
                health_report["missing_run"].append(name)
                continue

            run_func = getattr(module, "run")
            if not callable(run_func):
                health_report["not_callable"].append(name)
                continue

            health_report["ok"].append(name)

        except Exception as exc:  # pragma: no cover - defensive reporting
            health_report["import_error"].append(
                {
                    "name": name,
                    "error": str(exc),
                }
            )

    return health_report
