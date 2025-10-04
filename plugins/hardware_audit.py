"""Lightweight hardware audit plugin for Adam — fast by default, detailed on force."""

from __future__ import annotations

import json
import logging
import platform
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

METADATA = {
    "label": "Hardware Audit",
    "description": "Collects CPU, RAM, GPU, disk, OS info. Fast by default, detailed with force=True.",
    "ui_action": False,
    "executable": True,
}

logger = logging.getLogger("adam")

# Optional rich module
try:
    from src.adam.utils import hardware_audit as hardware_module
except ImportError:  # pragma: no cover
    hardware_module = None

# ➤ MODULE-LEVEL PSUTIL IMPORT — minor perf + cleaner logs
try:
    import psutil
except ImportError:
    psutil = None
    logger.debug("psutil not available — CPU/RAM/Disk metrics will be limited or zero.")


class HardwareAuditTool:
    name = "hardware_audit"
    description = "Audit system specs. Caches result. Full scan only on force=True."
    _cached_result: Optional[Dict[str, Any]] = None

    def run(self, force: bool = False, **kwargs) -> Dict[str, Any]:
        """Public entrypoint. Returns cached result unless force=True."""
        if self._cached_result is not None and not force:
            return self._cached_result

        try:
            hardware = self._collect_hardware(full_scan=force)
        except Exception as exc:
            logger.exception("Hardware audit failed")
            result = {"ok": False, "error": str(exc), "data": None}
            return result

        result = {"ok": True, "error": None, "data": hardware}
        self._cached_result = result
        self._write_report(result)
        return result

    def _collect_hardware(self, full_scan: bool = False) -> Dict[str, Any]:
        """Collect hardware info. Skip slow parts unless full_scan=True."""
        hw: Dict[str, Any] = {
            "os": self._get_os_info(),
            "cpu_cores": self._get_cpu_cores(),
            "ram_gb": self._get_ram_gb(),
            "gpu": self._get_gpu_info(full_scan),
        }

        if full_scan:
            hw["disk"] = self._get_disk_info()
        else:
            hw["disk"] = {"note": "Detailed disk info available with force=True"}

        return hw

    def _get_os_info(self) -> Dict[str, Any]:
        """Detect OS including macOS/iOS heuristics."""
        sys_name = platform.system()
        release = platform.release()
        machine = platform.machine()

        is_macos = sys_name == "Darwin" and not self._looks_like_ios(machine, release)
        is_ios = sys_name == "Darwin" and self._looks_like_ios(machine, release)
        is_linux = sys_name == "Linux"
        is_windows = sys_name == "Windows"

        return {
            "system": sys_name,
            "release": release,
            "machine": machine,
            "is_macos": is_macos,
            "is_ios": is_ios,
            "is_linux": is_linux,
            "is_windows": is_windows,
        }

    def _looks_like_ios(self, machine: str, release: str) -> bool:
        """Heuristic to detect iOS or iOS Simulator."""
        return (
            "iPhone" in machine
            or "iPad" in machine
            or "iPod" in machine
            or "SIMULATOR" in release.upper()
            or ("x86_64" in machine and "Darwin" in release)
            or ("arm64" in machine and "Darwin" in release)
        )

    def _get_cpu_cores(self) -> int:
        """Get physical CPU core count."""
        if psutil is None:
            return 0
        try:
            return psutil.cpu_count(logical=False) or 0
        except Exception:
            return 0

    def _get_ram_gb(self) -> int:
        """Get total RAM in GB."""
        if psutil is None:
            return 0
        try:
            return psutil.virtual_memory().total // (1024**3)
        except Exception:
            return 0

    def _get_gpu_info(self, full_scan: bool = False) -> Dict[str, Any]:
        """Get GPU info. NVIDIA via nvidia-smi. AMD/Intel only if full_scan=True."""
        gpus: List[Dict[str, Any]] = []

        # Always try NVIDIA first — it's fast and common
        nvidia_gpus = self._detect_nvidia_gpus()
        gpus.extend(nvidia_gpus)

        # AMD/Intel only on full scan
        if full_scan:
            vendor_gpus = self._detect_amd_intel_gpus()
            gpus.extend(vendor_gpus)

        return {"gpus": gpus, "count": len(gpus)}

    def _detect_nvidia_gpus(self) -> List[Dict[str, Any]]:
        """Fast NVIDIA detection via nvidia-smi."""
        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=name,memory.total",
                    "--format=csv,noheader",
                ],
                capture_output=True,
                text=True,
                timeout=3,
                check=False,
            )
            if result.returncode != 0 or not result.stdout.strip():
                return []

            devices = []
            for line in result.stdout.splitlines():
                parts = [p.strip() for p in line.split(",")]
                if len(parts) < 2:
                    continue
                try:
                    vram_gb = int(parts[1].replace("MiB", "")) // 1024
                except ValueError:
                    vram_gb = 0
                devices.append(
                    {"name": parts[0], "vram_gb": vram_gb, "vendor": "NVIDIA"}
                )
            return devices
        except Exception as e:
            logger.debug("NVIDIA GPU detection failed: %s", e)
            return []

    def _detect_amd_intel_gpus(self) -> List[Dict[str, Any]]:
        """Slower AMD/Intel detection — Linux/macOS only."""
        system = platform.system()
        gpus = []

        try:
            if system == "Linux":
                result = subprocess.run(
                    ["lspci"], capture_output=True, text=True, check=True
                )
                for line in result.stdout.splitlines():
                    if "VGA" in line or "3D controller" in line:
                        if "AMD" in line or "ATI" in line:
                            gpus.append(
                                {"name": line.strip(), "vendor": "AMD", "vram_gb": 0}
                            )
                        elif "Intel" in line:
                            gpus.append(
                                {"name": line.strip(), "vendor": "Intel", "vram_gb": 0}
                            )

            elif system == "Darwin":
                result = subprocess.run(
                    ["system_profiler", "SPDisplaysDataType", "-json"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                data = json.loads(result.stdout)
                for entry in data.get("SPDisplaysDataType", []):
                    vendor = entry.get("vendor", "")
                    if vendor in ("Intel", "AMD"):
                        model = entry.get("sppci_model", "Unknown")
                        vram_str = entry.get("vram_size", "0 MB")
                        try:
                            vram_gb = int(vram_str.replace("MB", "").strip()) // 1024
                        except:
                            vram_gb = 0
                        gpus.append(
                            {"name": model, "vendor": vendor, "vram_gb": vram_gb}
                        )

        except Exception as e:
            logger.debug("AMD/Intel GPU detection failed: %s", e)

        return gpus

    def _get_disk_info(self) -> Dict[str, Any]:
        """Get disk space + NVMe model/speed if possible (Linux/macOS)."""
        info = {"total_gb": 0, "free_gb": 0, "nvme_model": None, "nvme_speed": None}

        # ➤ Only use psutil if available
        if psutil is not None:
            try:
                usage = psutil.disk_usage("/")
                info["total_gb"] = usage.total // (1024**3)
                info["free_gb"] = usage.free // (1024**3)
            except Exception:
                pass

        system = platform.system()
        try:
            if system == "Linux":
                nvme_path = Path("/sys/class/nvme/")
                if nvme_path.exists():
                    for dev in nvme_path.iterdir():
                        if dev.name.startswith("nvme"):
                            model_file = dev / "model"
                            if model_file.exists():
                                info["nvme_model"] = model_file.read_text().strip()
                                device_link = dev / "device"
                                if device_link.exists():
                                    try:
                                        width = (
                                            (device_link / "current_link_width")
                                            .read_text()
                                            .strip()
                                        )
                                        speed = (
                                            (device_link / "current_link_speed")
                                            .read_text()
                                            .strip()
                                        )
                                        info["nvme_speed"] = f"PCIe {speed} x{width}"
                                    except Exception:
                                        pass
                                break

            elif system == "Darwin":
                result = subprocess.run(
                    ["diskutil", "info", "/"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                for line in result.stdout.splitlines():
                    if "Device / Media Name:" in line:
                        info["nvme_model"] = line.split(":")[-1].strip()
                    elif "Protocol:" in line and "PCI-Express" in line:
                        info["nvme_speed"] = "PCIe (detected)"

        except Exception as e:
            logger.debug("Disk/NVMe detail detection failed: %s", e)

        return info

    def _write_report(self, result: Dict[str, Any]):
        """Write structured report to logs/hardware_audit.json."""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        report_path = log_dir / "hardware_audit.json"

        try:
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, default=str)
            logger.info("Hardware audit report saved to %s", report_path)
        except Exception as e:
            logger.warning("Failed to write hardware report: %s", e)


def run(**kwargs):
    """Plugin entrypoint for Adam core."""
    tool = HardwareAuditTool()
    return tool.run(**kwargs)
