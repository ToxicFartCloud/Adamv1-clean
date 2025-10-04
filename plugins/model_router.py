# plugins/model_router.py

import logging
from typing import Any, Dict

METADATA = {
    "label": "Unified Model Router",
    "description": "Selects the optimal LLM based on task, hardware, and configuration.",
    "ui_action": False,
    "executable": True,
}

logger = logging.getLogger("adam")

# --- Unified Model Catalog ---
MODEL_CATALOG = [
    {
        "name": "qwen3-coder-30b-q4km",
        "repo_id": "TheBloke/Qwen3-Coder-30B-GGUF",
        "filename": "qwen3-coder-30b-Q4_K_M.gguf",
        "min_vram_gb": 20,
        "min_ram_gb": 32,
        "class": "heavy",
    },
    {
        "name": "qwen2.5-14b-instruct-q4_k_m",
        "repo_id": "TheBloke/Qwen2.5-14B-Instruct-GGUF",
        "filename": "Qwen2.5-14B-Instruct-Q4_K_M.gguf",
        "min_vram_gb": 10,
        "min_ram_gb": 24,
        "class": "heavy",
    },
    {
        "name": "mistral-7b-instruct-v0.3-q4_k_m",
        "repo_id": "TheBloke/Mistral-7B-Instruct-v0.3-GGUF",
        "filename": "mistral-7b-instruct-v0.3.Q4_K_M.gguf",
        "min_vram_gb": 6,
        "min_ram_gb": 16,
        "class": "heavy",
    },
    {
        "name": "light-condenser",  # Logical name for your conductor model
        "repo_id": "TheBloke/Phi-3-mini-4k-instruct-GGUF",
        "filename": "phi-3-mini-4k-instruct-q4_k_m.gguf",
        "min_vram_gb": 2,
        "min_ram_gb": 8,
        "class": "light",
    },
]
# ---------------------------------------------


def _detect_task_type(query: str, config: Dict[str, Any]) -> str:
    """Analyze user query and return best-guess task type."""
    if not isinstance(query, str):
        return "chat"

    q = query.lower().strip()
    classifier_cfg = config.get("task_classifier", {})
    code_keywords = classifier_cfg.get("code_keywords", [])
    reason_keywords = classifier_cfg.get("reason_keywords", [])

    if any(kw in q for kw in code_keywords):
        return "code"
    if any(kw in q for kw in reason_keywords):
        return "reason"
    return "chat"


def _select_model(
    task: str, hardware: Dict[str, Any], config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Selects the best model by checking hardware constraints and then task type.
    """
    # Step 1: Extract hardware specs safely
    ram_gb = hardware.get("ram_gb", 0) or 0
    gpus = hardware.get("gpu", {}).get("gpus", [])
    gpu_vram = 0
    if gpus:
        vram_values = []
        for gpu in gpus:
            vram = gpu.get("vram_gb", 0)
            vram_values.append(vram if isinstance(vram, (int, float)) else 0)
        gpu_vram = max(vram_values) if vram_values else 0

    # Step 2: Find capable models
    capable_models = [
        model
        for model in MODEL_CATALOG
        if gpu_vram >= model["min_vram_gb"] and ram_gb >= model["min_ram_gb"]
    ]

    if not capable_models:
        capable_models = [MODEL_CATALOG[-1]]  # Fallback to light model

    # Step 3: Select best model for task
    if task in ("code", "reason"):
        # Prefer heavy models for complex tasks
        heavy_models = [m for m in capable_models if m["class"] == "heavy"]
        if heavy_models:
            # Pick the heaviest (highest VRAM requirement = most capable)
            best_model = max(heavy_models, key=lambda x: x["min_vram_gb"])
            return {
                "model_name": best_model["name"],
                "preprocess_with": "light-condenser",  # Always condense with light model
                "reason": f"Complex task ({task}) → best capable heavy model",
                "params": {
                    "temperature": 0.2 if task == "code" else 0.4,
                    "max_tokens": 4096,
                },
                "repo_id": best_model["repo_id"],
                "filename": best_model["filename"],
            }

    # For chat or if no heavy model fits
    light_models = [m for m in capable_models if m["class"] == "light"]
    best_light = light_models[0] if light_models else capable_models[-1]

    return {
        "model_name": best_light["name"],
        "preprocess_with": None,  # No condensation needed for simple tasks
        "reason": "Simple task (chat) or hardware constraints → light model",
        "params": {"temperature": 0.7, "max_tokens": 512},
        "repo_id": best_light["repo_id"],
        "filename": best_light["filename"],
    }


def run(**kwargs) -> Dict[str, Any]:
    """
    Determines the single best model for a task based on query, hardware, and config.
    """
    try:
        query = kwargs.get("query")
        task = kwargs.get("task")
        hardware = kwargs.get("hardware", {})
        config = kwargs.get("config", {})

        if not isinstance(hardware, dict):
            return {"ok": False, "data": None, "error": "'hardware' must be a dict."}

        # Determine task type
        if query is not None:
            task = _detect_task_type(query, config)
        elif task is None:
            task = "chat"

        # Make the final decision
        selection = _select_model(task, hardware, config)

        # Log decision (only essential fields)
        logger.info(
            "Model routing decision: task=%s → model=%s (%s)",
            task,
            selection["model_name"],
            selection["reason"],
        )

        return {"ok": True, "data": selection, "error": None}

    except Exception as e:
        error_msg = f"Model routing failed: {e}"
        logger.exception(error_msg)
        return {"ok": False, "data": None, "error": error_msg}
