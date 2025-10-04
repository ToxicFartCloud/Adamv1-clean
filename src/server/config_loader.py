import yaml
from pathlib import Path

DEFAULT_CONFIG = {
    "ui": {
        "enabled": True,
        "dir": "./ui",
        "index": "index.html",
        "static_route": "/static",
    }
}


def load_config(config_path: Path):
    if not config_path.is_file():
        # still return defaults, but make dir absolute relative to repo root
        base_dir = config_path.parent.parent
        cfg = DEFAULT_CONFIG.copy()
        ui_dir = (Path(base_dir) / cfg["ui"]["dir"]).resolve()
        cfg["ui"]["dir"] = str(ui_dir)
        route = cfg["ui"].get("static_route", "/static")
        cfg["ui"]["static_route"] = route if str(route).startswith("/") else f"/{route}"
        return cfg

    with open(config_path, "r", encoding="utf-8") as f:
        user_config = yaml.safe_load(f) or {}

    config = DEFAULT_CONFIG.copy()
    if (
        isinstance(user_config, dict)
        and "ui" in user_config
        and isinstance(user_config["ui"], dict)
    ):
        config["ui"].update(user_config["ui"])

    # normalize values
    base_dir = config_path.parent.parent  # e.g., .../Adamv1
    ui_dir = (Path(base_dir) / config["ui"].get("dir", "./ui")).resolve()
    config["ui"]["dir"] = str(ui_dir)

    route = config["ui"].get("static_route", "/static")
    config["ui"]["static_route"] = route if str(route).startswith("/") else f"/{route}"

    return config


def safe_join(base: str, rel: str):
    """Return an absolute path inside 'base' for 'rel', or None if traversal."""
    base_abs = Path(base).resolve()
    target = (base_abs / rel).resolve()
    try:
        target.relative_to(base_abs)
    except Exception:
        return None
    return str(target)
