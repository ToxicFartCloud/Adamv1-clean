"""
Auto-import and register all available backends.

CONTRACT:
    Each backend module (eg., chroma.py, faiss.py) must:
        1. Define a class that implements MemorySearchBackend
        2. Call register_backend("name", BackendClass) at module level
"""

from .base import register_backend
from pathlib import Path
import importlib
import logging

logger = logging.getLogger("adam.backends")

# Import and auto-register each backend module if deps are available
for backend_file in Path(__file__).parent.glob("*.py"):
    if backend_file.stem in ("__init__", "base"):
        continue

    try:
        mod = importlib.import_module(f".{backend_file.stem}", package=__package__)
        # Expect each module to have a Backend class and auto-register via register_backend()
        logger.debug("Loaded backend module: %s", backend_file.stem)
    except Exception as e:
        logger.debug("Skipping backend '%s': %s", backend_file.stem, e)
        continue
