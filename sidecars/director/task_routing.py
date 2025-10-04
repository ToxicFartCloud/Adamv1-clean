DEFAULT_TAGS_BY_HINT = {
    "code": ["code"],
    "summarize": ["summary"],
    "math": ["math", "reasoning"],
}


def choose(task_hint: str, tags: list[str], models: list[dict]) -> dict:
    wanted = list(tags or [])
    if not wanted:
        key = (task_hint or "").lower()
        for k, v in DEFAULT_TAGS_BY_HINT.items():
            if k in key:
                wanted = v
                break
    best = None
    best_score = -1
    wantset = set(wanted)
    for m in models:
        tagset = set(str(t) for t in (m.get("tags") or []))
        score = len(tagset & wantset)
        if score > best_score:
            best, best_score = m, score
    return best or (models[0] if models else {})
