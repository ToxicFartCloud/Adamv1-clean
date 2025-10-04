from __future__ import annotations

METADATA = {
    "executable": False,
    "description": "Shared utilities for plugins — not an executable plugin.",
}

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

LOG_PATH = Path("logs") / "audit.jsonl"
AUDIT_USER = "Adam"


def _json_default(obj: Any) -> str:
    """Fallback serializer for objects that aren't JSON serializable."""
    return repr(obj)


def ensure_log_file() -> Path:
    """Ensure the audit log file exists and return the path."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not LOG_PATH.exists():
        LOG_PATH.touch()
    return LOG_PATH


def append_audit_log(
    plugin: str,
    action: str,
    args: Dict[str, Any],
    dry_run: bool,
    ok: bool,
    reason: str,
    report_summary: str,
) -> None:
    """Append a structured audit line for every plugin invocation."""
    ensure_log_file()
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user": AUDIT_USER,
        "plugin": plugin,
        "action": action,
        "args": args,
        "cwd": os.getcwd(),
        "dry_run": dry_run,
        "ok": ok,
        "reason": reason,
        "summary": report_summary,
    }
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, default=_json_default) + "\n")


def build_response(
    *,
    action: str,
    dry_run: bool,
    plan: List[str],
    summary: str,
    ok: bool = True,
    approval_required: bool = False,
    details: Dict[str, Any] | None = None,
    artifacts: List[Any] | None = None,
) -> Dict[str, Any]:
    """Standard response schema used by safe-op plugins."""
    return {
        "ok": ok,
        "action": action,
        "dry_run": dry_run,
        "approval_required": approval_required,
        "plan": plan,
        "report": {"summary": summary, "details": details or {}},
        "artifacts": artifacts or [],
        "logs_path": str(LOG_PATH),
    }


def build_error_response(
    *,
    action: str,
    dry_run: bool,
    summary: str,
    plan: List[str] | None = None,
    details: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Return a standard failure response."""
    return build_response(
        action=action,
        dry_run=dry_run,
        plan=plan or [],
        summary=summary,
        ok=False,
        details=details or {},
    )


def prepare_payload(payload: Dict[str, Any]) -> Tuple[str, Dict[str, Any], bool, str]:
    """Validate shared payload requirements and normalize defaults."""
    if not isinstance(payload, dict):
        raise ValueError("Payload must be a dictionary.")

    action = str(payload.get("action", "")).strip()
    if not action:
        raise ValueError("Missing action.")

    args = payload.get("args") or {}
    if not isinstance(args, dict):
        raise ValueError("Args must be a dictionary.")

    dry_run = bool(payload.get("dry_run", True))
    reason = str(payload.get("reason", "")).strip()

    return action, args, dry_run, reason
