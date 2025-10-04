"""Health and discovery endpoint for memory search system."""

import logging
from .backends.base import list_backends
from .utils.config import load_config, CONFIG_PATHS

logger = logging.getLogger("adam.health")

_CONFIG = load_config()


def list_backends_info() -> dict:
    """Return detailed info about available backends and config."""
    info = {
        "available_backends": list_backends(),
        "default_backend": _CONFIG.get("default_backend", "mock"),
        "config_loaded_from": next((p for p in CONFIG_PATHS if p.exists()), None),
        "config": _CONFIG,
    }
    logger.debug("health report: %s", info)
    return info
