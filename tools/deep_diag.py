#!/usr/bin/env python3
import json
import os
import sys
import re

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(REPO)
sys.path.insert(0, REPO)


def read(p):
    try:
        with open(p, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None


def exists(p):
    return os.path.exists(p)


def main():
    report = {"repo": REPO, "exists": {}, "checks": [], "config": {}, "plugins": {}}
    paths = {
        "launcher": "Adam.py",
        "orchestrator": "adam_base.py",
        "backend": "server/app.py",
        "ui": "ui/UI.py",
        "sled": "sidecars/sled/app.py",
        "plugins_list": "config/plugins.txt",
        "config_yaml": "config/adam.yaml",
        "models_dir": "models",
    }
    for k, p in paths.items():
        report["exists"][k] = exists(p)
    s = read("Adam.py") or ""
    report["checks"].append(
        {
            "name": "launcher_is_thin",
            "ok": ("adam_base" in s and "uvicorn" not in s),
            "details": "Adam.py should import adam_base and not contain FastAPI/uvicorn code.",
        }
    )
    ab = read("adam_base.py") or ""
    report["checks"].append(
        {
            "name": "orchestrator_has_run_ui",
            "ok": ("def run_ui" in ab and "run_adam_ui" in ab),
            "details": "adam_base should export run_ui and call ui/UI.py",
        }
    )
    report["checks"].append(
        {
            "name": "orchestrator_has_ensure_backend",
            "ok": ("def ensure_backend" in ab),
            "details": "adam_base can autostart backend",
        }
    )
    ui = read("ui/UI.py") or ""
    report["checks"].append(
        {
            "name": "ui_has_server_menu",
            "ok": ("Server" in ui and "_start_backend" in ui and "_stop_backend" in ui),
            "details": "UI should include Start/Stop or helpers",
        }
    )
    be = read("server/app.py") or ""
    report["checks"].append(
        {
            "name": "backend_has_admin_endpoints",
            "ok": (("/admin/health" in be) and ("/admin/shutdown" in be)),
            "details": "server/app.py should expose admin endpoints",
        }
    )
    y = read("config/adam.yaml") or ""
    m = re.search(r"default_model_path[^\n]*", y)
    report["config"]["default_model_path_line"] = m.group(0) if m else None
    report["checks"].append(
        {
            "name": "models_dir_exists",
            "ok": exists("models"),
            "details": "create models/ if you store local models",
        }
    )
    plugins = []
    if report["exists"]["plugins_list"]:
        txt = read("config/plugins.txt") or ""
        plugins = [
            ln.strip()
            for ln in txt.splitlines()
            if ln.strip() and not ln.strip().startswith("#")
        ]
    report["plugins"]["declared"] = plugins
    report["plugins"]["count"] = len(plugins)
    ok_all = all(c["ok"] for c in report["checks"])
    print(json.dumps({"ok": ok_all, **report}, indent=2))
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
