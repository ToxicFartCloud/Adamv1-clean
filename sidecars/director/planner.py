def plan(task: str) -> list[str]:
    task = (task or "").strip()
    if not task:
        return []
    return [f"Do: {task}"]
