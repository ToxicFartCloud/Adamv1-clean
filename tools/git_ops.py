import subprocess
import os

METADATA = {
    "label": "Git Operations",
    "description": "Performs git actions like clone, commit, push.",
    "executable": True,
}


def run(**kwargs):
    """
    Execute a git operation.

    Expected kwargs:
        - action: str — "clone", "commit", "push", "status", "pull"
        - repo: str — URL or path (for clone)
        - message: str — commit message (for commit)
        - cwd: str — working directory (optional)

    Returns:
        { "ok": bool, "data": str, "error": str or None }
    """
    try:
        action = kwargs.get("action", "").lower()
        cwd = kwargs.get("cwd", os.getcwd())

        if action == "clone":
            repo = kwargs.get("repo")
            if not repo:
                return {
                    "ok": False,
                    "data": None,
                    "error": "'repo' required for clone.",
                }
            result = subprocess.run(
                ["git", "clone", repo], cwd=cwd, capture_output=True, text=True
            )
        elif action == "commit":
            message = kwargs.get("message", "Auto-commit by Adam")
            result = subprocess.run(
                ["git", "commit", "-am", message],
                cwd=cwd,
                capture_output=True,
                text=True,
            )
        elif action == "push":
            result = subprocess.run(
                ["git", "push"], cwd=cwd, capture_output=True, text=True
            )
        elif action == "pull":
            result = subprocess.run(
                ["git", "pull"], cwd=cwd, capture_output=True, text=True
            )
        elif action == "status":
            result = subprocess.run(
                ["git", "status"], cwd=cwd, capture_output=True, text=True
            )
        else:
            return {"ok": False, "data": None, "error": f"Unsupported action: {action}"}

        if result.returncode == 0:
            return {
                "ok": True,
                "data": result.stdout.strip()
                or f"Git {action} completed successfully.",
                "error": None,
            }
        else:
            return {
                "ok": False,
                "data": None,
                "error": f"Git {action} failed: {result.stderr.strip()}",
            }

    except Exception as e:
        return {
            "ok": False,
            "data": None,
            "error": f"Exception during git {action}: {str(e)}",
        }
