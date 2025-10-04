"""
agent_researcher.py — Researcher agent that finds best practices and patterns.
"""

import logging

from src.adam.core import _call_llm_with_fallback

METADATA = {
    "label": "Researcher Agent",
    "description": "Finds best practices and patterns for code improvement.",
    "ui_action": False,
    "executable": True,
}

logger = logging.getLogger("adam")


def run(**kwargs) -> dict:
    """
    Perform research and summarize findings using centralized LLM routing.

    Expected kwargs:
    - prompt: str (required) → the research query
    - sources: list[str] (optional) → external sources or context
    - depth: str (optional) → "summary", "detailed"

    Returns:
    { "ok": bool, "data": str, "error": str or None }
    """
    try:
        prompt = kwargs.get("prompt", "").strip()
        sources = kwargs.get("sources", [])
        depth = kwargs.get("depth", "summary")

        if not prompt:
            return {"ok": False, "data": None, "error": "'prompt' is required."}

        # Build research directive string
        research_prompt = f"Research request (depth={depth}).\n\nQuery: {prompt}\n"
        if sources:
            research_prompt += f"Consider these sources:\n{chr(10).join(sources)}\n"

        # Route through core with task="research"
        result = _call_llm_with_fallback(
            prompt=research_prompt,
            task="research",
            hardware={},  # core will fill actual hardware state
            config={},  # core will fill system config
        )

        if not result.get("ok"):
            return {"ok": False, "data": None, "error": result.get("error")}

        model_identifier = result.get("model_used") or result.get(
            "model_name", "unknown"
        )
        logger.info(
            "agent_researcher: produced %d chars using %s",
            len(result["data"]),
            model_identifier,
        )

        return {"ok": True, "data": result["data"], "error": None}

    except Exception as e:
        error_msg = f"Research task failed: {str(e)}"
        logger.exception(error_msg)
        return {"ok": False, "data": None, "error": error_msg}
