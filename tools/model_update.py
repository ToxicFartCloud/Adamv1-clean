import logging
from pathlib import Path
from typing import Any, Dict

METADATA = {
    "label": "Model Update",
    "description": "Updates assigned model for a given task (e.g., code, creative).",
    "executable": True,
}

logger = logging.getLogger("adam")


def _read_best_model() -> str:
    """Read best coding model from best_coding_model.txt."""
    path = Path("best_coding_model.txt")
    if not path.exists():
        raise FileNotFoundError("best_coding_model.txt not found")
    with open(path, "r", encoding="utf-8") as f:
        model = f.read().strip()
    if not model:
        raise ValueError("Empty best_coding_model.txt")
    return model


def run(**kwargs) -> Dict[str, Any]:
    """
    Update assigned model for a task.

    Expected kwargs:
        - task: str ("code", "creative", "analysis", "general")
        - model: str (optional) — model name to assign
        - use_best_coding: bool (optional) — if True and model=None, read from best_coding_model.txt

    Returns:
        { "ok": bool, "data": dict, "error": str or None }
    """
    try:
        task = kwargs.get("task", "code")
        model = kwargs.get("model")
        use_best_coding = kwargs.get("use_best_coding", False)

        if not isinstance(task, str):
            return {"ok": False, "data": None, "error": "'task' must be a string."}

        # ➤ Backward compatibility: read from best_coding_model.txt
        if model is None and use_best_coding:
            try:
                model = _read_best_model()
            except Exception as e:
                error_msg = f"Could not read best_coding_model.txt: {e}"
                logger.error(error_msg)
                return {"ok": False, "data": None, "error": error_msg}

        if not model:
            return {"ok": False, "data": None, "error": "No model specified"}

        # ➤ Call model_update.py script
        script = Path("model_update.py")
        if not script.exists():
            error_msg = f"Missing script: {script}"
            logger.error(error_msg)
    except Exception:
        pass
