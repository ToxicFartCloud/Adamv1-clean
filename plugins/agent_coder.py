"""
agent_coder.py — Coder agent that writes code based on prompts.
"""

import logging
from typing import Any, Dict

from src.adam.core import _call_llm_with_fallback

METADATA = {
    "label": "Coder Agent",
    "description": "Writes code based on prompts.",
    "ui_action": False,
    "executable": True,
}

logger = logging.getLogger("adam")


def run(**kwargs) -> Dict[str, Any]:
    """
    Generate code based on prompt using centralized LLM routing.

    Expected kwargs:
    - prompt: str (required)
    - language: str (optional, default: "python")

    Returns:
    { "ok": bool, "data": str, "error": str or None }
    """
    try:
        prompt = kwargs.get("prompt", "").strip()
        language = kwargs.get("language", "python")

        if not prompt:
            return {"ok": False, "data": None, "error": "'prompt' is required."}

        # Use centralized LLM routing with task="code"
        result = _call_llm_with_fallback(
            prompt=prompt,
            task="code",
            hardware={},  # core will fill actual hardware state
            config={},  # core will fill system config
        )

        if not result.get("ok"):
            return {"ok": False, "data": None, "error": result.get("error")}

        model_identifier = result.get("model_used") or result.get(
            "model_name", "unknown"
        )
        logger.info(
            "agent_coder: generated %d chars using %s",
            len(result["data"]),
            model_identifier,
        )

        return {
            "ok": True,
            "data": result["data"],
            "error": None,
        }

    except Exception as e:
        error_msg = f"Code generation failed: {str(e)}"
        logger.exception(error_msg)
        return {
            "ok": False,
            "data": None,
            "error": error_msg,
        }
