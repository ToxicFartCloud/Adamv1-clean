#!/usr/bin/env python3
import json
import os
import sys
import socket
import subprocess
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HOST, PORT = "127.0.0.1", 8000


def is_up(h, p, t=0.5):
    try:
        with socket.socket() as s:
            s.settimeout(t)
            try:
                s.connect((h, p))
                return True
            except Exception:
                return False
    except PermissionError:
        return False


def _collect(auto_start: bool = True, host: str = HOST, port: int = PORT) -> dict:
    original_cwd = os.getcwd()
    try:
        os.chdir(REPO)
        sys.path.insert(0, str(REPO))

        result = {"repo": str(REPO), "python": sys.executable, "steps": []}

        step = {"name": "core_import", "ok": False, "details": ""}
        try:
            from adam.core import main as _core_main  # noqa: F401

            step["ok"] = True
        except Exception as e:
            step["details"] = f"core import failed: {e}"
        result["steps"].append(step)

        step = {"name": "ui_module_present", "ok": False, "details": ""}
        try:
            import src.ui.app as _ui_app  # noqa: F401

            step["ok"] = True
        except Exception as e:
            step["details"] = f"ui/app import failed: {e}"
        result["steps"].append(step)

        step = {
            "name": "backend_health",
            "ok": False,
            "host": host,
            "port": port,
            "details": "",
        }

        if auto_start and not is_up(host, port):
            try:
                subprocess.Popen(
                    [
                        sys.executable,
                        "-m",
                        "uvicorn",
                        "server.app:app",
                        "--host",
                        host,
                        "--port",
                        str(port),
                    ],
                    cwd=str(REPO),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                t0 = time.time()
                while time.time() - t0 < 6:
                    if is_up(host, port):
                        break
                    time.sleep(0.25)
            except Exception as e:
                step["details"] = f"autostart failed: {e}"

        step["ok"] = is_up(host, port)
        if not step["ok"] and not step["details"]:
            step["details"] = "backend not reachable"
        result["steps"].append(step)

        return result
    finally:
        os.chdir(original_cwd)


def run(**kwargs):
    auto_start = kwargs.get("auto_start", False)
    host = kwargs.get("host", HOST)
    port = kwargs.get("port", PORT)

    result = _collect(auto_start=auto_start, host=host, port=port)
    ok = all(s.get("ok") for s in result.get("steps", []))
    error = None if ok else "One or more diagnostic steps failed."
    return {"ok": ok, "data": result, "error": error}


def main():
    outcome = run(auto_start=True)
    print(json.dumps(outcome["data"], indent=2))
    return 0 if outcome["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
