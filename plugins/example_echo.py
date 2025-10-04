"""
example_echo.py — Simple echo plugin for testing and debugging.
Returns input text unchanged.
"""

import logging

METADATA = {
    "label": "Echo Test",
    "description": "Returns input text for testing.",
    "ui_action": False,
    "executable": True,
}

logger = logging.getLogger("adam")


def run(**kwargs) -> dict:
    """
    Echo back input text.

    Expected kwargs:
        - text: str (required)

    Returns:
        { "ok": bool, "data": str, "error": str or None }
    """
    text = kwargs.get("text", "")

    if not isinstance(text, str):
        error_msg = "Input 'text' must be a string."
        logger.warning("example_echo validation failed: %s", error_msg)
        return {"ok": False, "data": None, "error": error_msg}

    logger.info("example_echo: '%s'", text[:50] + "..." if len(text) > 50 else text)

    return {
        "ok": True,
        "data": text,
        "error": None,
    }
