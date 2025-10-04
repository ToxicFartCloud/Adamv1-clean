# SLED client plugin: simple HTTP client to the local SLED FastAPI server.
# Contract:
#   run(action, **kwargs) -> {"ok": bool, "data": Any, "error": str|None}
# Actions:
#   - "health"
#   - "generate" (prompt, mode, gen_args)
#   - "calibrate" (path)
import json
import os
import logging
from typing import Any, Dict
import urllib.request

METADATA = {
    "label": "SLED Client",
    "description": "HTTP client for local SLED FastAPI server.",
    "ui_action": False,
    "executable": True,
}

CONFIG_PATH = "config/plugins.sled.yaml"


def _json_logger(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    logger = logging.getLogger("sled_client")
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(path)
    formatter = logging.Formatter("%(message)s")
    handler.setFormatter(formatter)
    if logger.handlers:
        logger.handlers.clear()
    logger.addHandler(handler)
    return logger


LOGGER = _json_logger("logs/plugins/sled_client.log")
ogger = logging.getLogger("adam.sled_client")


def _read_yaml(path: str) -> Dict[str, Any]:
    # Minimal YAML reader (no external deps): accept key: value per line.
    cfg = {}
    if not os.path.exists(path):
        return cfg
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line:
                k, v = line.split(":", 1)
                cfg[k.strip()] = v.strip()
    return cfg


def _server_url(cfg: Dict[str, Any]) -> str:
    host = cfg.get("host", "127.0.0.1")
    port = cfg.get("port", "8010")
    return f"http://{host}:{port}"


def _post_json(url: str, payload: Dict[str, Any], timeout: int = 120) -> Dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read()
        return json.loads(body.decode("utf-8"))


def run(action: str, **kwargs) -> Dict[str, Any]:
    try:
        cfg = _read_yaml(CONFIG_PATH)
        base = _server_url(cfg)
        timeout = int(cfg.get("timeout_s", "120"))
        if action == "health":
            # attempt a tiny generate with baseline mode to ensure server responds
            url = base + "/generate"
            payload = {
                "mode": "baseline",
                "prompt": "ping",
                "gen_args": {"max_new_tokens": 1},
            }
            data = _post_json(url, payload, timeout=timeout)
            ok = bool(data.get("ok"))
            out = {
                "ok": ok,
                "data": data if ok else None,
                "error": None if ok else str(data),
            }
            LOGGER.info(json.dumps({"event": "health", "ok": ok}))
            return out

        if action == "generate":
            url = base + "/generate"
            payload = {
                "mode": kwargs.get("mode", "sled"),
                "prompt": kwargs.get("prompt", ""),
                "gen_args": kwargs.get("gen_args", {}) or {},
            }
            if "weights_path" in kwargs and kwargs["weights_path"]:
                payload["weights_path"] = kwargs["weights_path"]
            data = _post_json(url, payload, timeout=timeout)
            ok = bool(data.get("ok"))
            LOGGER.info(json.dumps({"event": "generate", "ok": ok}))
            return {
                "ok": ok,
                "data": data.get("data") if ok else None,
                "error": None if ok else data.get("error"),
            }

        if action == "calibrate":
            url = base + "/calibrate"
            payload = {"path": kwargs.get("path", "eval/items.jsonl")}
            for key in ("out_path", "layers", "k", "weighting"):
                if key in kwargs and kwargs[key] is not None:
                    payload[key] = kwargs[key]
            data = _post_json(url, payload, timeout=timeout)
            ok = bool(data.get("ok"))
            LOGGER.info(json.dumps({"event": "calibrate", "ok": ok}))
            return {
                "ok": ok,
                "data": data.get("data") if ok else None,
                "error": None if ok else data.get("error"),
            }

        return {"ok": False, "data": None, "error": f"Unknown action: {action}"}
    except Exception as e:
        LOGGER.info(json.dumps({"event": "error", "error": str(e)}))
        return {"ok": False, "data": None, "error": str(e)}
