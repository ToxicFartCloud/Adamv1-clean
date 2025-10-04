"""
tools.py -- Dynamic tool loader for Adam.

Tools are heavier, task-specific modules stored in ./tools/.
Unlike plugins, they are loaded on-demand to reduce startup overhead.
"""

import importlib.util
import sys
from pathlib import Path
from typing import Any, Dict

TOOL_DIR = Path("tools")


def load_tool_module(name: str):
    """Dynamically load a tool module by name from ./tools/."""
    if not TOOL_DIR.is_dir():
        raise ImportError(f"Tool directory '{TOOL_DIR}' not found.")

    file_candidate = TOOL_DIR / f"{name}.py"
    if not file_candidate.is_file():
        raise ImportError(f"Tool '{name}' not found at {file_candidate}")

    spec = importlib.util.spec_from_file_location(f"tools.{name}", file_candidate)
    if not spec or not spec.loader:
        raise ImportError(f"Could not load spec for tool '{name}'")

    module = importlib.util.module_from_spec(spec)
    sys.modules[f"tools.{name}"] = module
    spec.loader.exec_module(module)
    return module


def run_tool(name: str, **kwargs) -> Dict[str, Any]:
    """Load and execute a tool dynamically. Returns standard {ok, data, error} contract."""
    try:
        module = load_tool_module(name)
        if not hasattr(module, "run") or not callable(getattr(module, "run")):
            return {
                "ok": False,
                "data": None,
                "error": f"Tool '{name}' does not have a callable 'run' function.",
            }

        result = module.run(**kwargs)

        # Validate response format
        if not isinstance(result, dict) or not {"ok", "data", "error"} <= result.keys():
            return {
                "ok": False,
                "data": None,
                "error": f"Tool '{name}' returned invalid response format.",
            }

        return result

    except Exception as e:
        return {
            "ok": False,
            "data": None,
            "error": f"Failed to load or run tool '{name}': {str(e)}",
        }
