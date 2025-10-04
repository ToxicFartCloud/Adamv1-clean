# spdx-FileCopyrightText: 2024 Eric Johnson
# spdx-License-Identifier: MIT

"""
nsp_supervisor.py -- Natural Semantic Parser (NSP) Supervisor Agent

A Hierarchical Task Network (HTN) planner that acts as a project manager.
Decomposes high-level natural language commands into structured, executable plans.

Plugin Contract:
    run(command: str, domain: str = "default", stream: bool = False, **kwargs) -> dict

Example:
    {
        "command": "Schedule a team sync for Friday to review the budget.",
        "domain": "project_management"
    }
"""

import logging
from typing import Any, Dict, List

# Use Adam's logger
logger = logging.getLogger("adam")

# --- HTN Domain Registry ---
# You can extend this with YAML/JSON domain files later
HTN_DOMAINS = {
    "default": {
        "tasks": {
            "LaunchCampaign": {
                "method": [
                    "define_target_audience",
                    "create_marketing_assets",
                    "schedule_social_media_posts",
                    "coordinate_with_sales_team",
                ]
            },
            "ScheduleMeeting": {
                "method": [
                    "check_availability",
                    "book_conference_room",
                    "send_calendar_invite",
                ]
            },
        },
        "primitives": {
            "define_target_audience",
            "create_marketing_assets",
            "schedule_social_media_posts",
            "coordinate_with_sales_team",
            "check_availability",
            "book_conference_room",
            "send_calendar_invite",
        },
    }
}


def parse_intent(command: str) -> Dict[str, Any]:
    """
    Simulate intent & parameter extraction.
    In production, replace with a fine-tuned NER model or LLM call.
    """
    command_lower = command.lower()

    # Simple keyword-based intent routing (replace with NLU model later)
    if "campaign" in command_lower and (
        "launch" in command_lower or "start" in command_lower
    ):
        return {
            "task": "LaunchCampaign",
            "parameters": {"product": "unspecified", "campaign_type": "launch"},
        }
    elif "meeting" in command_lower or "sync" in command_lower:
        # Basic extraction (improve with spaCy/transformers)
        return {
            "task": "ScheduleMeeting",
            "parameters": {
                "participants": ["team"],
                "datetime": "unspecified",
                "agenda": "unspecified",
            },
        }
    else:
        return {"task": "UnknownTask", "parameters": {"raw": command}}


def decompose_task(
    task_name: str, params: Dict[str, Any], domain: str = "default"
) -> List[Dict[str, Any]]:
    """Recursively decompose a task using HTN methods."""
    domain_def = HTN_DOMAINS.get(domain, HTN_DOMAINS["default"])
    tasks = domain_def["tasks"]
    primitives = domain_def["primitives"]

    plan = []

    def _decompose(t_name: str, t_params: Dict[str, Any]):
        if t_name in primitives:
            plan.append({"action": t_name, "args": t_params})
        elif t_name in tasks:
            method = tasks[t_name]["method"]
            for subtask in method:
                # Pass parameters down (simplified; could use parameter mapping)
                _decompose(subtask, t_params)
        else:
            # Fallback: treat as primitive if unknown
            plan.append({"action": t_name, "args": t_params})

    _decompose(task_name, params)
    return plan


def validate_plan(plan: List[Dict[str, Any]]) -> bool:
    """Optional: validate preconditions, resources, etc."""
    # Stub: always valid for now
    return True


def run(**kwargs) -> Dict[str, Any]:
    """
    NSP Supervisor Plugin Entry Point.

    Args:
        command (str): High-level natural language instruction.
        domain (str): HTN domain to use (default: "default").
        stream (bool): If True, return a generator (not implemented here yet).

    Returns:
        dict: Plugin response contract.
    """
    try:
        command = kwargs.get("command")
        if not isinstance(command, str) or not command.strip():
            return {
                "ok": False,
                "data": None,
                "error": "Missing or invalid 'command' argument.",
            }

        domain = kwargs.get("domain", "default")
        stream = kwargs.get("stream", False)

        if stream:
            return {
                "ok": False,
                "data": None,
                "error": "Streaming not yet implemented in NSP plugin.",
            }

        # Step 1: Parse intent
        goal = parse_intent(command)
        task_name = goal["task"]

        if task_name == "UnknownTask":
            return {
                "ok": False,
                "data": None,
                "error": f"Could not interpret command: '{command}'",
            }

        # Step 2: Decompose via HTN
        plan = decompose_task(task_name, goal["parameters"], domain=domain)

        # Step 3: Validate
        if not validate_plan(plan):
            return {
                "ok": False,
                "data": None,
                "error": "Generated plan failed validation.",
            }

        # Step 4: Return structured plan
        result = {
            "original_command": command,
            "goal": goal,
            "plan": plan,
            "domain_used": domain,
            "task_count": len(plan),
        }

        logger.info("NSP: successfully decomposed command into %d tasks", len(plan))
        return {"ok": True, "data": result, "error": None}

    except Exception as e:
        error_msg = f"NSP plugin error: {e}"
        logger.error(error_msg, exc_info=True)
        return {"ok": False, "data": None, "error": error_msg}
