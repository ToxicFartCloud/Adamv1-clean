"""
agent_tester.py — Tester agent that generates and runs unit tests.
"""

import logging

from src.adam.core import _call_llm_with_fallback

METADATA = {
    "label": "Tester Agent",
    "description": "Generates and runs unit tests for code.",
    "ui_action": False,
    "executable": True,
}

logger = logging.getLogger("adam")


def run(**kwargs) -> dict:
    """
    Generate or execute test cases using centralized LLM routing.

    Expected kwargs:
    - prompt: str (required) → code or description to generate tests for
    - framework: str (optional) → testing framework (default: "pytest")

    Returns:
    { "ok": bool, "data": str, "error": str or None }
    """
    try:
        prompt = kwargs.get("prompt", "").strip()
        framework = kwargs.get("framework", "pytest")

        if not prompt:
            return {"ok": False, "data": None, "error": "'prompt' is required."}

        test_prompt = f"Generate {framework} tests for the following:\n\n{prompt}"

        # Route through core with task="test"
        result = _call_llm_with_fallback(
            prompt=test_prompt,
            task="test",
            hardware={},  # core will fill actual hardware state
            config={},  # core will fill system config
        )

        if not result.get("ok"):
            return {"ok": False, "data": None, "error": result.get("error")}

        model_identifier = result.get("model_used") or result.get(
            "model_name", "unknown"
        )
        logger.info(
            "agent_tester: produced %d chars using %s",
            len(result["data"]),
            model_identifier,
        )

        return {"ok": True, "data": result["data"], "error": None}

    except Exception as e:
        error_msg = f"Test generation failed: {str(e)}"
        logger.exception(error_msg)
        return {"ok": False, "data": None, "error": error_msg}
