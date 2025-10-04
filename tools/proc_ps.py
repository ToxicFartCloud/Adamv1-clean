import logging
import subprocess
import platform
from typing import Any, Dict, List

METADATA = {
    "label": "Process PS",
    "description": "List running processes with resource usage.",
    "executable": True,
}

logger = logging.getLogger("adam")


def _get_processes_windows() -> List[Dict[str, Any]]:
    """Get detailed process info on Windows using wmic."""
    try:
        # Use wmic for more detailed info
        result = subprocess.run(
            [
                "wmic",
                "process",
                "get",
                "ProcessId,Name,WorkingSetSize,CommandLine",
                "/format:csv",
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=15,
        )
        lines = result.stdout.strip().splitlines()
        if len(lines) < 2:
            return []

        headers = lines[0].split(",")
        processes = []
        for line in lines[1:]:
            if not line.strip():
                continue
            parts = line.split(",", len(headers) - 1)
            if len(parts) < 4:
                continue

            try:
                pid = parts[1].strip()
                name = parts[2].strip()
                memory_kb = (
                    int(parts[3].strip()) // 1024 if parts[3].strip().isdigit() else 0
                )
                cmdline = parts[4].strip() if len(parts) > 4 else ""

                processes.append(
                    {
                        "pid": pid,
                        "name": name,
                        "memory_kb": memory_kb,
                        "cmdline": cmdline[:100] + "..."
                        if len(cmdline) > 100
                        else cmdline,
                        "platform": "windows",
                    }
                )
            except Exception:
                continue

        return processes
    except Exception as e:
        logger.debug("Windows process listing failed: %s", e)
        return []


def _get_processes_linux() -> List[Dict[str, Any]]:
    """Get detailed process info on Linux using ps."""
    try:
        result = subprocess.run(
            ["ps", "-eo", "pid,comm,%cpu,rss,cmd", "--no-headers"],
            capture_output=True,
            text=True,
            check=True,
            timeout=15,
        )
        processes = []
        for line in result.stdout.splitlines():
            parts = line.split(maxsplit=4)
            if len(parts) < 5:
                continue

            pid = parts[0]
            name = parts[1]
            cpu_percent = parts[2]
            rss_kb = parts[3]
            cmdline = parts[4]

            try:
                memory_kb = int(rss_kb)
                cpu_usage = float(cpu_percent)
            except ValueError:
                memory_kb = 0
                cpu_usage = 0.0

            processes.append(
                {
                    "pid": pid,
                    "name": name,
                    "memory_kb": memory_kb,
                    "cpu_percent": cpu_usage,
                    "cmdline": cmdline[:100] + "..." if len(cmdline) > 100 else cmdline,
                    "platform": "linux",
                }
            )

        return processes
    except Exception as e:
        logger.debug("Linux process listing failed: %s", e)
        return []


def _get_processes_macos() -> List[Dict[str, Any]]:
    """Get detailed process info on macOS using ps."""
    try:
        result = subprocess.run(
            ["ps", "-eo", "pid,comm,%cpu,rss,command", "-r"],
            capture_output=True,
            text=True,
            check=True,
            timeout=15,
        )
        lines = result.stdout.strip().splitlines()
        if len(lines) < 2:
            return []

        processes = []
        for line in lines[1:]:  # Skip header
            parts = line.split(maxsplit=4)
            if len(parts) < 5:
                continue

            pid = parts[0]
            name = parts[1]
            cpu_percent = parts[2]
            rss_kb = parts[3]
            cmdline = parts[4]

            try:
                memory_kb = int(rss_kb)
                cpu_usage = float(cpu_percent)
            except ValueError:
                memory_kb = 0
                cpu_usage = 0.0

            processes.append(
                {
                    "pid": pid,
                    "name": name,
                    "memory_kb": memory_kb,
                    "cpu_percent": cpu_usage,
                    "cmdline": cmdline[:100] + "..." if len(cmdline) > 100 else cmdline,
                    "platform": "macos",
                }
            )

        return processes
    except Exception as e:
        logger.debug("macOS process listing failed: %s", e)
        return []


def run(**kwargs) -> Dict[str, Any]:
    """
    List running processes with resource usage.

    Expected kwargs:
        - filter: str (optional) — filter by process name
        - top_memory: int (optional) — return top N by memory usage
        - top_cpu: int (optional) — return top N by CPU usage

    Returns:
        { "ok": bool, "data": list[dict], "error": str or None }
    """
    try:
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
            processes = [
                p
                for p in processes
                if filter_name in p["name"].lower()
                or filter_name in p.get("cmdline", "").lower()
            ]

        # ➤ Optional top N by memory
        top_memory = kwargs.get("top_memory")
        if top_memory:
            try:
                top_memory = int(top_memory)
                processes.sort(key=lambda x: x["memory_kb"], reverse=True)
                processes = processes[:top_memory]
            except (ValueError, TypeError):
                pass

        # ➤ Optional top N by CPU
        top_cpu = kwargs.get("top_cpu")
        if top_cpu:
            try:
                top_cpu = int(top_cpu)
                processes.sort(key=lambda x: x.get("cpu_percent", 0), reverse=True)
                processes = processes[:top_cpu]
            except (ValueError, TypeError):
                pass

        logger.info(
            "proc_ps: found %d processes (filter='%s', top_memory=%s, top_cpu=%s)",
            len(processes),
            filter_name,
            top_memory,
            top_cpu,
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
