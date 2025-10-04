"""
tool_base.py — Optional abstract base class for Adam Tools.

Adam does NOT require plugins or tools to inherit from this.
It only requires a module-level `run(**kwargs)` function that returns:
    { "ok": bool, "data": any, "error": str or None }

Use this class only if you prefer OOP-style tool definitions.
"""

METADATA = {
    "executable": False,
    "description": "Abstract base class for Tools.  Optional - Adam only required run(**kwargs)",
}

from abc import ABC, abstractmethod


class Tool(ABC):
    """Minimal interface for Adam tool wrappers."""

    name: str = ""
    description: str = ""

    @abstractmethod
    def run(self, **kwargs):
        """Execute the tool and return a result payload."""
        raise NotImplementedError
