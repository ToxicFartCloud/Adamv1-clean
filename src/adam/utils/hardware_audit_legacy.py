import platform
import psutil
import requests
import json
from pathlib import Path


def audit_hardware():
    """Audit system hardware specifications."""
    hardware_info = {
        "os": platform.system() + " " + platform.release(),
        "cpu": platform.processor(),
        "cpu_cores": psutil.cpu_count(logical=False),
        "ram_gb": round(psutil.virtual_memory().total / (1024**3)),
        "gpu": "None",
        "cuda_available": False,
    }

    # Check for GPU
    try:
        import torch

        if torch.cuda.is_available():
            hardware_info["gpu"] = torch.cuda.get_device_name(0)
            hardware_info["cuda_available"] = True
    except Exception:
        pass

    return hardware_info


def get_ollama_models():
    """Fetch available models from Ollama API."""
    try:
        response = requests.get("http://localhost:11434/api/tags")
        response.raise_for_status()
        return [model["name"] for model in response.json().get("models", [])]
    except Exception as e:
        print(f"Error fetching Ollama models: {str(e)}")
        return []


# ---- preferences + tags helpers ----
def load_user_prefs(path=None):
    """
    Load custom model preferences from ~/.config/adam/model_prefs.json
    Example:
    {
      "prefer": ["deepseek-coder", "codellama", "qwen2.5-coder"],
      "avoid":  ["qwen", "tinyllama"]
    }
    """
    try:
        cfg = (
            Path(path)
            if path
            else Path.home() / ".config" / "adam" / "model_prefs.json"
        )
        if cfg.is_file():
            with open(cfg, "r") as f:
                data = json.load(f)
            return {
                "prefer": [m.lower() for m in data.get("prefer", [])],
                "avoid": [m.lower() for m in data.get("avoid", [])],
            }
    except Exception:
        pass
    return {"prefer": [], "avoid": []}


def get_ollama_models_with_sizes():
    """
    Returns list of dicts: [{"name": "model:tag", "size": <bytes or None>}]
    Falls back to name-only if size not provided by /api/tags.
    """
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=2)
        r.raise_for_status()
        out = []
        for m in r.json().get("models", []):
            name = m.get("name") or ""
            size = m.get("size")  # some Ollama builds include size (bytes). OK if None.
            out.append({"name": name, "size": size})
        return out
    except Exception:
        return []


def _fits_memory(hardware, size_bytes):
    """
    Heuristic fit: if model size is known, ensure it fits within a safe fraction of RAM on CPU-only.
    If CUDA is present, be lenient.
    """
    if not size_bytes:
        return True
    ram_gb = hardware.get("ram_gb", 8)
    return (size_bytes / (1024**3)) <= max(1, 0.7 * ram_gb)


def select_best_model_v2(hardware, models_info, prefs):
    """
    Priority:
      1) user 'prefer' list (base name match), excluding 'avoid'
      2) coder models first (deepseek-coder, codellama, qwen2.5-coder, etc.)
      3) general fallbacks (llama3, phi3, mistral)
    Skips models that don't fit memory (if size known).
    Returns a single model name or None.
    """

    def base(model_name):
        return model_name.split(":", 1)[0].lower()

    # filter avoid + memory fit
    candidates = []
    for m in models_info:
        nm = m["name"]
        if base(nm) in prefs["avoid"]:
            continue
        if not _fits_memory(hardware, m.get("size")):
            continue
        candidates.append(nm)

    if not candidates:
        return None

    # 1) honor user prefs
    for pref in prefs["prefer"]:
        for nm in candidates:
            if base(nm) == pref:
                return nm

    # 2) coder-first
    coder_keywords = ("coder", "code", "codellama")
    coder = [nm for nm in candidates if any(k in base(nm) for k in coder_keywords)]
    if coder:
        if hardware.get("cuda_available"):
            return coder[0]
        sized = [m for m in models_info if m["name"] in coder and m.get("size")]
        if sized:
            return sorted(sized, key=lambda x: x["size"])[0]["name"]
        return coder[0]

    # 3) general fallbacks
    for fallback in ("llama3", "phi3", "mistral"):
        for nm in candidates:
            if base(nm).startswith(fallback):
                return nm

    return candidates[0] if candidates else None


def select_best_model(hardware, models):
    """Select the best coding model based on hardware capabilities."""
    # Prioritize models with 'code' in name
    code_models = [model for model in models if "code" in model.lower()]

    # If no code-specific models found, use general ones
    if not code_models:
        code_models = [
            model
            for model in models
            if "llama" in model.lower() or "phi" in model.lower()
        ]

    # Simple selection based on hardware
    if hardware["cuda_available"] and "codellama" in code_models:
        return "codellama"
    elif "llama3" in code_models:
        return "llama3"
    elif "phi3" in code_models:
        return "phi3"
    else:
        return code_models[0] if code_models else None


def save_update_file(model_name, file_path):
    """Save the selected model to a text file."""
    try:
        with open(file_path, "w") as f:
            f.write(f"Best Coding Model for {platform.system()}:\n{model_name}")
        print(f"Saved update to: {file_path}")
    except Exception as e:
        print(f"Error saving file: {str(e)}")


def main():
    # Get script directory
    script_dir = Path(__file__).parent
    update_file = script_dir / "best_coding_model.txt"

    # Audit hardware
    hardware = audit_hardware()
    print("Hardware Audit:")
    for k, v in hardware.items():
        print(f"{k}: {v}")

    # Get Ollama models (+sizes) and user preferences
    models_info = get_ollama_models_with_sizes()
    print("\nAvailable Ollama Models:", [m["name"] for m in models_info])
    prefs = load_user_prefs()

    # Select best model (v2)
    best_model = select_best_model_v2(hardware, models_info, prefs) or None

    if best_model:
        print(f"\nSelected Best Model: {best_model}")
        save_update_file(best_model, update_file)
    else:
        print("No suitable model found for coding tasks.")


if __name__ == "__main__":
    main()
