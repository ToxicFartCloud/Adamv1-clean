"""Utility helpers for collecting basic hardware information."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

try:  # Optional dependency, but preferred for accurate CPU/RAM data
    import psutil  # type: ignore
except Exception:  # pragma: no cover - psutil not available
    psutil = None  # type: ignore


def get_gpu_info() -> List[Dict[str, int | str]]:
    """Return a list of detected NVIDIA GPUs with VRAM (in GB)."""
    try:
        proc = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if proc.returncode != 0 or not proc.stdout.strip():
            return []

        gpus: List[Dict[str, int | str]] = []
        for line in proc.stdout.splitlines():
            parts = [p.strip() for p in line.split(",")]
            if len(parts) < 2:
                continue
            name = parts[0]
            try:
                vram_gb = int(parts[1].replace("MiB", "").strip()) // 1024
            except ValueError:
                vram_gb = 0
            gpus.append({"name": name, "vram_gb": vram_gb})
        return gpus
    except Exception:  # pragma: no cover - command missing/unavailable
        return []


def get_cpu_ram() -> Tuple[int, int]:
    """Return (cpu_cores, ram_gb). Falls back to zeros if psutil missing."""
    if psutil is None:
        return 0, 0

    try:
        cpu_cores = psutil.cpu_count(logical=False) or 0
        ram_gb = int(psutil.virtual_memory().total // (1024**3))
        return cpu_cores, ram_gb
    except Exception:  # pragma: no cover - psutil edge failure
        return 0, 0


def recommend_coding_model(hardware: Dict[str, object]) -> str:
    """Heuristic model recommendation for backward compatibility."""
    ram_gb = int(hardware.get("ram_gb", 0) or 0)
    gpu_section = hardware.get("gpu") or {}
    gpus = gpu_section.get("gpus", []) if isinstance(gpu_section, dict) else []
    has_powerful_gpu = any(
        (gpu or {}).get("vram_gb", 0) >= 16 for gpu in gpus if isinstance(gpu, dict)
    )

    if ram_gb >= 32 and has_powerful_gpu:
        return "qwen3-coder-30b-q4km"
    if ram_gb >= 16:
        return "qwen2.5-coder-14b-q5km"
    return "phi-3-mini-4k-instruct-q4km"


def audit_hardware() -> Dict[str, object]:
    """Assemble the hardware payload consumed by the Adam plugins."""
    gpus = get_gpu_info()
    cpu_cores, ram_gb = get_cpu_ram()
    return {
        "gpu": {
            "gpus": gpus,
            "count": len(gpus),
        },
        "cpu_cores": cpu_cores,
        "ram_gb": ram_gb,
    }


def main() -> None:  # pragma: no cover - command line helper
    hardware = audit_hardware()
    recommendation = recommend_coding_model(hardware)
    Path("best_coding_model.txt").write_text(recommendation + "\n", encoding="utf-8")
    print(json.dumps(hardware))


if __name__ == "__main__":  # pragma: no branch
    main()
