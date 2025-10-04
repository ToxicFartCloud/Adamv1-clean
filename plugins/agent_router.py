"""
agent_router.py — Police Monitor + Flow Controller for multi-agent system.
"""

import logging
from typing import Any, Dict, List

METADATA = {
    "label": "Agent Router",
    "description": "Routes messages between agents, prevents loops, validates responses.",
    "ui_action": False,
    "executable": True,
}

logger = logging.getLogger("adam")

# Import shared state
from .group_chat import get_chat_history, append_message, clear_chat_history


def _detect_loop(history: List[Dict], max_repeats: int = 3) -> bool:
    """Detect if last N messages are identical or cycling."""
    if len(history) < max_repeats:
        return False

    last_messages = [msg["content"].strip() for msg in history[-max_repeats:]]
    if len(set(last_messages)) == 1:
        return True  # Identical messages

    # Check for cycling pattern
    if max_repeats >= 4:
        cycle = last_messages[-4:]
        if cycle[0] == cycle[2] and cycle[1] == cycle[3]:
            return True

    return False


def _validate_content(content: str) -> bool:
    """Validate response content."""
    if not content.strip():
        return False
    if "error" in content.lower() or "failed" in content.lower():
        return False
    if len(content) < 5:
        return False
    return True


def run(**kwargs) -> Dict[str, Any]:
    """
    Route message to next agent, validate response, prevent loops.

    Expected kwargs:
        - from_agent: str (name of sending agent)
        - content: str (message content)
        - next_agent: str (optional — override routing)

    Returns:
        { "ok": bool, "data": dict, "error": str or None }
    """
    try:
        from_agent = kwargs.get("from_agent", "").strip()
        content = kwargs.get("content", "").strip()
        next_agent = kwargs.get("next_agent")

        if not from_agent or not content:
            return {
                "ok": False,
                "data": None,
                "error": "'from_agent' and 'content' required.",
            }

        # Append to chat history
        append_message(from_agent, content)

        # Get full history
        history = get_chat_history()

        # ➤ LOOP DETECTION
        if _detect_loop(history):
            error_msg = "Loop detected — terminating conversation."
            logger.warning(error_msg)
            clear_chat_history()
            return {
                "ok": False,
                "data": {"action": "terminate", "reason": "loop_detected"},
                "error": error_msg,
            }

        # ➤ CONTENT VALIDATION
        if not _validate_content(content):
            error_msg = (
                "Invalid content — empty, too short, or contains error keywords."
            )
            logger.warning(error_msg)
            return {
                "ok": False,
                "data": {"action": "retry", "reason": "invalid_content"},
                "error": error_msg,
            }

        # ➤ ROUTING LOGIC (simple round-robin for now)
        if not next_agent:
            agents = ["coder", "researcher", "critic"]
            last_agent = history[-1]["agent"] if history else ""
            next_idx = (
                (agents.index(last_agent) + 1) % len(agents)
                if last_agent in agents
                else 0
            )
            next_agent = agents[next_idx]

        logger.info("agent_router: %s → %s", from_agent, next_agent)

        return {
            "ok": True,
            "data": {
                "next_agent": next_agent,
                "history_length": len(history),
                "status": "routed",
            },
            "error": None,
        }

    except Exception as e:
        error_msg = f"Agent routing failed: {str(e)}"
        logger.exception(error_msg)
        return {
            "ok": False,
            "data": None,
            "error": error_msg,
        }
