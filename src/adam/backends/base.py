"""
Base protocol and global backend registry.

All memory search backends must implement MemorySearchBackend.
Modules auto-register via register_backend("name", BackendClass).
"""

from typing import Protocol, Dict, Type, List
import logging

logger = logging.getLogger("adam.backends")


class MemorySearchBackend(Protocol):
    def search(self, query: str, top_k: int) -> List[str]:
        """Sync search."""
        ...

    async def asearch(self, query: str, top_k: int) -> List[str]:
        """Async search."""
        ...


# ➤ Global registry
_BACKEND_REGISTRY: Dict[str, Type[MemorySearchBackend]] = {}


def register_backend(name: str, cls: Type[MemorySearchBackend]):
    """Register backend class under a name."""
    _BACKEND_REGISTRY[name] = cls
    logger.debug("Registered backend: %s", name)


def get_backend_class(name: str) -> Type[MemorySearchBackend]:
    if name not in _BACKEND_REGISTRY:
        raise ValueError(
            f"Unknown backend: {name}. Available: {list(_BACKEND_REGISTRY.keys())}"
        )
    return _BACKEND_REGISTRY[name]


def list_backends() -> List[str]:
    return list(_BACKEND_REGISTRY.keys())
