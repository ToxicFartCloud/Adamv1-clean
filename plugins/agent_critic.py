"""
agent_critic.py — Critic agent that reviews code for quality, bugs, and improvements.
"""

import logging

from src.adam.core import _call_llm_with_fallback

METADATA = {
    "label": "Critic Agent",
    "description": "Reviews code for quality, bugs, and improvements.",
    "ui_action": False,
    "executable": True,
}

logger = logging.getLogger("adam")


def run(**kwargs) -> dict:
    """
    Provide a code review / critique using centralized LLM routing.

    Expected kwargs:
    - prompt: str (required) → code or description to review
    - style: str (optional)  → e.g., "pep8", "security", "performance"

    Returns:
    { "ok": bool, "data": str, "error": str or None }
    """
    try:
        prompt = kwargs.get("prompt", "").strip()
        style = kwargs.get("style", "general")

        if not prompt:
            return {"ok": False, "data": None, "error": "'prompt' is required."}

        # Route through core with task="critique"
        result = _call_llm_with_fallback(
            prompt=f"Review the following code ({style} style):\n\n{prompt}",
            task="critique",
            hardware={},  # core fills in actual hardware state
            config={},  # core fills in system config
        )

        if not result.get("ok"):
            return {"ok": False, "data": None, "error": result.get("error")}

        model_identifier = result.get("model_used") or result.get(
            "model_name", "unknown"
        )
        logger.info(
            "agent_critic: generated %d chars using %s",
            len(result["data"]),
            model_identifier,
        )

        return {"ok": True, "data": result["data"], "error": None}

    except Exception as e:
        error_msg = f"Code critique failed: {str(e)}"
        logger.exception(error_msg)
        return {"ok": False, "data": None, "error": error_msg}
