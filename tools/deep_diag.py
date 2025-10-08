#!/usr/bin/env python3
import json
import os
import sys
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


def read(p):
    try:
        with open(REPO / p, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None


def exists(p):
    return (REPO / p).exists()


def _build_report() -> dict:
    report = {"repo": str(REPO), "exists": {}, "checks": [], "config": {}, "plugins": {}}
    paths = {
        "launcher": "run_adam.py",
        "core": "src/adam/core.py",
        "backend": "src/server/main.py",
        "ui": "src/ui/app.py",
        "sled": "sidecars/sled/app.py",
        "plugins_list": "config/plugins.txt",
        "config_yaml": "config/adam.yaml",
        "models_dir": "models",
    }
    for k, p in paths.items():
        report["exists"][k] = exists(p)
    launcher_src = read("run_adam.py") or ""
    report["checks"].append(
        {
            "name": "launcher_imports_core",
            "ok": ("from adam.core import" in launcher_src or "import adam.core" in launcher_src),
            "details": "run_adam.py should import the orchestrator and stay thin.",
        }
    )
    core_src = read("src/adam/core.py") or ""
    report["checks"].append(
        {
            "name": "core_exports_run_ui",
            "ok": ("def run_ui" in core_src and "ensure_backend" in core_src),
            "details": "core.py should provide run_ui and ensure_backend.",
        }
    )
    report["checks"].append(
        {
            "name": "core_handles_plugins",
            "ok": ("manager.run_plugin" in core_src),
            "details": "core.py should delegate work through the plugin manager.",
        }
    )
    ui_src = read("src/ui/app.py") or ""
    report["checks"].append(
        {
            "name": "ui_main_entry",
            "ok": ("def main" in ui_src and "root.mainloop" in ui_src),
            "details": "src/ui/app.py should expose the Tk main entry point.",
        }
    )
    be = read("src/server/main.py") or ""
    report["checks"].append(
        {
            "name": "backend_has_admin_endpoints",
            "ok": (("/admin/health" in be) and ("/admin/shutdown" in be)),
            "details": "src/server/main.py should expose admin endpoints",
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
    report["ok"] = ok_all
    return report


def run(**_kwargs):
    report = _build_report()
    ok = report.get("ok", False)
    data = report
    error = None if ok else "Deep diagnostics failed."
    return {"ok": ok, "data": data, "error": error}


def main():
    outcome = run()
    print(json.dumps(outcome["data"], indent=2))
    return 0 if outcome["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
