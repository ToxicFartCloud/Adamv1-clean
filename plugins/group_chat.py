"""
group_chat.py — Shared state for multi-agent conversations.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

METADATA = {
    "executable": False,
    "description": "Shared state for multi-agent system — not an executable plugin.",
}

logger = logging.getLogger("adam")
STATE_FILE = Path("data/agent_state.json")


def get_chat_history() -> List[Dict[str, Any]]:
    """Load conversation history."""
    if not STATE_FILE.exists():
        return []
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.debug("Failed to load chat history: %s", e)
        return []


def append_message(agent: str, content: str, metadata: Dict[str, Any] = None) -> None:
    """Append message to chat history."""
    history = get_chat_history()
    message = {
        "timestamp": __import__("time").strftime("%Y-%m-%d %H:%M:%S"),
        "agent": agent,
        "content": content,
        "metadata": metadata or {},
    }
    history.append(message)
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)


def clear_chat_history() -> None:
    """Clear conversation history."""
    if STATE_FILE.exists():
        STATE_FILE.unlink()
