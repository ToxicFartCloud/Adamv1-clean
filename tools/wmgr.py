import logging
import subprocess
import sys
from typing import Any, Dict, List

METADATA = {
    "label": "Window Manager",
    "description": "Manage windows (list, focus, close). Linux-only for now.",
    "executable": True,
}

logger = logging.getLogger("adam")


def _is_linux() -> bool:
    """Check if running on Linux."""
    return sys.platform.startswith("linux")


def _get_windows_xdotool() -> List[Dict[str, Any]]:
    """Get list of windows using xdotool."""
    try:
        # Get all window IDs
        result = subprocess.run(
            ["xdotool", "search", "--onlyvisible", "--name", "."],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        window_ids = result.stdout.strip().splitlines()

        windows = []
        for wid in window_ids[:20]:  # Limit to 20 for performance
            if not wid.strip():
                continue

            # Get window name
            name_result = subprocess.run(
                ["xdotool", "getwindowname", wid],
                capture_output=True,
                text=True,
                timeout=2,
            )
            name = (
                name_result.stdout.strip()
                if name_result.returncode == 0
                else f"Window {wid}"
            )

            # Get window geometry
            geom_result = subprocess.run(
                ["xdotool", "getwindowgeometry", wid],
                capture_output=True,
                text=True,
                timeout=2,
            )
            geometry = "unknown"
            if geom_result.returncode == 0:
                lines = geom_result.stdout.splitlines()
                for line in lines:
                    if "Position:" in line:
                        geometry = line.split("Position:")[-1].strip()

            windows.append(
                {"id": wid, "name": name, "geometry": geometry, "platform": "linux"}
            )

        return windows
    except Exception as e:
        logger.debug("xdotool failed: %s", e)
        return []


def _mock_windows() -> List[Dict[str, Any]]:
    """Return mock window list."""
    return [
        {
            "id": "12345",
            "name": "Terminal - Adam",
            "geometry": "0,0 800x600",
            "platform": "mock",
        },
        {
            "id": "67890",
            "name": "File Manager",
            "geometry": "800,0 1024x768",
            "platform": "mock",
        },
        {
            "id": "54321",
            "name": "Web Browser",
            "geometry": "0,600 1200x800",
            "platform": "mock",
        },
    ]


def run(**kwargs) -> Dict[str, Any]:
    """
    List or manage windows.

    Expected kwargs:
        - action: str ("list", "focus", "close") — default: "list"
        - window_id: str (required for "focus", "close")

    Returns:
        { "ok": bool, "data": list[dict] or str, "error": str or None }
    """
    try:
        action = kwargs.get("action", "list").lower()
        window_id = kwargs.get("window_id", "").strip()

        if action == "list":
            if _is_linux():
                windows = _get_windows_xdotool()
                if not windows:
                    windows = _mock_windows()
                    logger.info("wmgr: xdotool not available — returning mock windows")
            else:
                windows = _mock_windows()
                logger.info("wmgr: Only Linux supported — returning mock windows")

            logger.info("wmgr: found %d windows", len(windows))
            return {
                "ok": True,
                "data": windows,
                "error": None,
            }

        elif action in ["focus", "close"]:
            if not window_id:
                return {
                    "ok": False,
                    "data": None,
                    "error": "'window_id' required for focus/close",
                }

            if not _is_linux():
                message = (
                    f"Action '{action}' not supported on this platform. Mock success."
                )
                logger.info("wmgr: %s", message)
                return {
                    "ok": True,
                    "data": message,
                    "error": None,
                }

            try:
                if action == "focus":
                    subprocess.run(
                        ["xdotool", "windowactivate", window_id], check=True, timeout=5
                    )
                    message = f"Window {window_id} focused."
                elif action == "close":
                    subprocess.run(
                        ["xdotool", "windowclose", window_id], check=True, timeout=5
                    )
                    message = f"Window {window_id} closed."

                logger.info("wmgr: %s", message)
                return {
                    "ok": True,
                    "data": message,
                    "error": None,
                }
            except Exception as e:
                error_msg = f"Failed to {action} window {window_id}: {str(e)}"
                logger.exception(error_msg)
                return {
                    "ok": False,
                    "data": None,
                    "error": error_msg,
                }

        else:
            return {"ok": False, "data": None, "error": f"Unknown action: {action}"}

    except Exception as e:
        error_msg = f"Window management failed: {str(e)}"
        logger.exception(error_msg)
        return {
            "ok": False,
            "data": None,
            "error": error_msg,
        }
