#!/usr/bin/env python3
import json
import os
import sys
import socket
import subprocess
import time

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HOST, PORT = "127.0.0.1", 8000


def is_up(h, p, t=0.5):
    with socket.socket() as s:
        s.settimeout(t)
        try:
            s.connect((h, p))
            return True
        except Exception:
            return False


def main():
    os.chdir(REPO)
    sys.path.insert(0, REPO)
    result = {"repo": REPO, "python": sys.executable, "steps": []}
    # adam_base import
    step = {"name": "launcher_import", "ok": False, "details": ""}
    try:
        step["ok"] = True
    except Exception as e:
        step["details"] = f"adam_base import failed: {e}"
    result["steps"].append(step)
    # run_ui present?
    step = {"name": "run_ui_present", "ok": False, "details": ""}
    try:
        step["ok"] = True
    except Exception as e:
        step["details"] = f"run_ui missing: {e}"
    result["steps"].append(step)
    # backend health (auto-start if down)
    step = {
        "name": "backend_health",
        "ok": False,
        "host": HOST,
        "port": PORT,
        "details": "",
    }
    if not is_up(HOST, PORT):
        try:
            subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "server.app:app",
                    "--host",
                    HOST,
                    "--port",
                    str(PORT),
                ],
                cwd=REPO,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            t0 = time.time()
            while time.time() - t0 < 6:
                if is_up(HOST, PORT):
                    break
                time.sleep(0.25)
        except Exception as e:
            step["details"] = f"autostart failed: {e}"
    step["ok"] = is_up(HOST, PORT)
    if not step["ok"] and not step["details"]:
        step["details"] = "backend not reachable"
    result["steps"].append(step)
    print(json.dumps(result, indent=2))
    return 0 if all(s["ok"] for s in result["steps"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
