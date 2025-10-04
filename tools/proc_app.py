import logging
import subprocess
from typing import Any, Dict, List

METADATA = {
    "label": "Process App",
    "description": "List running applications/processes.",
    "executable": True,
}

logger = logging.getLogger("adam")


def _get_processes_windows() -> List[Dict[str, Any]]:
    """Get running processes on Windows using tasklist."""
    try:
        result = subprocess.run(
            ["tasklist", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
        processes = []
        for line in result.stdout.splitlines():
            if not line.strip():
                continue
            parts = line.split('","')
            if len(parts) < 5:
                continue
            name = parts[0].strip('"')
            pid = parts[1].strip('"')
            mem = parts[4].strip('"').replace(" K", "").replace(",", "")
            try:
                mem_kb = int(mem)
            except ValueError:
                mem_kb = 0
            processes.append(
                {"name": name, "pid": pid, "memory_kb": mem_kb, "platform": "windows"}
            )
        return processes
    except Exception as e:
        logger.debug("Windows process listing failed: %s", e)
        return []


def _get_processes_linux() -> List[Dict[str, Any]]:
    """Get running processes on Linux using ps."""
    try:
        result = subprocess.run(
            ["ps", "-eo", "pid,comm,rss", "--no-headers"],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
        processes = []
        for line in result.stdout.splitlines():
            parts = line.split()
            if len(parts) < 3:
                continue
            pid = parts[0]
            name = parts[1]
            rss_kb = parts[2]
            try:
                mem_kb = int(rss_kb)
            except ValueError:
                mem_kb = 0
            processes.append(
                {"name": name, "pid": pid, "memory_kb": mem_kb, "platform": "linux"}
            )
        return processes
    except Exception as e:
        logger.debug("Linux process listing failed: %s", e)
        return []


def _get_processes_macos() -> List[Dict[str, Any]]:
    """Get running processes on macOS using ps."""
    try:
        result = subprocess.run(
            ["ps", "-eo", "pid,comm,rss", "-r"],  # -r for real memory
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
        processes = []
        for line in result.stdout.splitlines()[1:]:  # Skip header
            parts = line.split()
            if len(parts) < 3:
                continue
            pid = parts[0]
            # Command may have spaces — take everything except first and last
            name = " ".join(parts[1:-1])
            rss_kb = parts[-1]
            try:
                mem_kb = int(rss_kb)
            except ValueError:
                mem_kb = 0
            processes.append(
                {"name": name, "pid": pid, "memory_kb": mem_kb, "platform": "macos"}
            )
        return processes
    except Exception as e:
        logger.debug("macOS process listing failed: %s", e)
        return []


def run(**kwargs) -> Dict[str, Any]:
    """
    List running applications/processes.

    Expected kwargs:
        - filter: str (optional) — filter by process name
        - top: int (optional) — return top N by memory usage

    Returns:
        { "ok": bool, "data": list[dict], "error": str or None }
    """
    try:
        import platform

        system = platform.system().lower()

        if system == "windows":
            processes = _get_processes_windows()
        elif system == "darwin":
            processes = _get_processes_macos()
        else:  # linux or unknown
            processes = _get_processes_linux()

        # ➤ Optional filter
        filter_name = kwargs.get("filter", "").lower()
        if filter_name:
            processes = [p for p in processes if filter_name in p["name"].lower()]

        # ➤ Optional top N by memory
        top_n = kwargs.get("top")
        if top_n:
            try:
                top_n = int(top_n)
                processes.sort(key=lambda x: x["memory_kb"], reverse=True)
                processes = processes[:top_n]
            except (ValueError, TypeError):
                pass

        logger.info(
            "proc_app: found %d processes (filter='%s', top=%s)",
            len(processes),
            filter_name,
            top_n,
        )

        return {
            "ok": True,
            "data": processes,
            "error": None,
        }

    except Exception as e:
        error_msg = f"Process listing failed: {str(e)}"
        logger.exception(error_msg)
        return {
            "ok": False,
            "data": None,
            "error": error_msg,
        }
