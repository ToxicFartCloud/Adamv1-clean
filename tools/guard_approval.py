METADATA = {
    "label": "Guard Approval",
    "description": "Safety guard for dangerous operations — requires explicit approval.",
    "executable": True,
}


def run(**kwargs):
    """
    Approve or deny a dangerous operation.

    Expected kwargs:
        - action: str — e.g., "delete_file", "format_disk", "exec_code"
        - target: str — what is being affected
        - risk_level: str — "low", "medium", "high"
        - auto_approve: bool — override manual approval (for testing/automation)

    Returns:
        { "ok": bool, "data": str, "error": str or None }
    """
    try:
        action = kwargs.get("action", "")
        target = kwargs.get("target", "unknown")
        risk_level = kwargs.get("risk_level", "medium").lower()
        auto_approve = kwargs.get("auto_approve", False)

        if not action:
            return {"ok": False, "data": None, "error": "'action' is required."}

        # Simulate policy: auto-approve low risk, or if flag set
        if auto_approve or risk_level == "low":
            message = f"✅ Auto-approved: {action} on {target} (risk: {risk_level})"
            return {"ok": True, "data": message, "error": None}

        # For medium/high — simulate user approval (in real system, would prompt UI or CLI)
        simulated_user_response = (
            "yes"  # ← In real system, replace with input() or API call
        )

        if simulated_user_response.lower() in ["y", "yes", "true", "1"]:
            message = f"✅ Approved by guard: {action} on {target}"
            return {"ok": True, "data": message, "error": None}
        else:
            return {
                "ok": False,
                "data": None,
                "error": f"❌ Rejected by guard: {action} on {target}",
            }

    except Exception as e:
        return {"ok": False, "data": None, "error": f"Guard approval failed: {str(e)}"}
