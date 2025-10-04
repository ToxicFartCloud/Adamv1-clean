"""Load memory search configuration from YAML/JSON."""

from pathlib import Path
import json
import logging

logger = logging.getLogger("adam.config")

CONFIG_PATHS = [
    Path("config/memory_config.yaml"),
    Path("config/memory_config.json"),
    Path(".memory_config.yaml"),
    Path(".memory_config.json"),
]

try:
    import yaml

    _yaml_available = True
except ImportError:
    _yaml_available = False


def load_config() -> dict:
    """Load first found config file. Returns empty dict if none found."""
    for path in CONFIG_PATHS:
        if not path.exists():
            continue
        try:
            if path.suffix == ".yaml" and _yaml_available:
                with open(path, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f) or {}
            elif path.suffix == ".json":
                with open(path, "r", encoding="utf-8") as f:
                    config = json.load(f)
            else:
                continue  # Skip unsupported format

            logger.info("Loaded memory config from: %s", path)
            return config

        except Exception as e:
            logger.warning("Failed to load config %s: %s", path, e)
            continue  # Try next file

    logger.debug("No memory config found — using defaults.")
    return {}
