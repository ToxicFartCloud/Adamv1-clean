# plugins/model_registry.py
def run(hardware: dict, **kwargs) -> dict:
    """
    Given hardware specs, return best model options.

    Returns:
        {
            "ok": True,
            "data": {
                "recommended_model": {
                    "name": "mistral-7b-instruct-v0.3-q4_k_m",
                    "repo_id": "TheBloke/Mistral-7B-Instruct-v0.3-GGUF",
                    "filename": "mistral-7b-instruct-v0.3.Q4_K_M.gguf",
                    "min_vram_gb": 6,
                    "min_ram_gb": 16
                }
            }
        }
    """
    ram_gb = hardware.get("ram_gb", 0)
    gpu_vram = 0
    gpus = hardware.get("gpu", {}).get("gpus", [])
    if gpus:
        gpu_vram = max(gpu.get("vram_gb", 0) for gpu in gpus)

    # In real implementation, this would query a live registry
    # For now, use an embedded catalog
    MODEL_CATALOG = [
        {
            "name": "qwen3-coder-30b-q4km",
            "repo_id": "TheBloke/Qwen3-Coder-30B-GGUF",
            "filename": "qwen3-coder-30b-Q4_K_M.gguf",
            "min_vram_gb": 20,
            "min_ram_gb": 32,
        },
        {
            "name": "qwen2.5-14b-instruct-q4_k_m",
            "repo_id": "TheBloke/Qwen2.5-14B-Instruct-GGUF",
            "filename": "Qwen2.5-14B-Instruct-Q4_K_M.gguf",
            "min_vram_gb": 10,
            "min_ram_gb": 24,
        },
        {
            "name": "mistral-7b-instruct-v0.3-q4_k_m",
            "repo_id": "TheBloke/Mistral-7B-Instruct-v0.3-GGUF",
            "filename": "mistral-7b-instruct-v0.3.Q4_K_M.gguf",
            "min_vram_gb": 6,
            "min_ram_gb": 16,
        },
        {
            "name": "phi-3-mini-4k-instruct-q4_k_m",
            "repo_id": "TheBloke/Phi-3-mini-4k-instruct-GGUF",
            "filename": "phi-3-mini-4k-instruct-q4_k_m.gguf",
            "min_vram_gb": 2,
            "min_ram_gb": 8,
        },
    ]

    # Select best model that fits
    for model in MODEL_CATALOG:
        if gpu_vram >= model["min_vram_gb"] and ram_gb >= model["min_ram_gb"]:
            return {"ok": True, "data": {"recommended_model": model}, "error": None}

    # Fallback to smallest model
    return {"ok": True, "data": {"recommended_model": MODEL_CATALOG[-1]}, "error": None}
