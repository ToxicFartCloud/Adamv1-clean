import os
from requests import post as requests_post


DEFAULT_URL = "http://127.0.0.1:8002"


def choose(
    task_hint: str, tags: list[str] | None = None, url: str | None = None
) -> dict:
    target = (url or DEFAULT_URL).rstrip("/") + "/choose"
    payload = {"task_hint": task_hint, "tags": tags or []}
    if os.getenv("DIRECTOR_CLIENT_LOG_ONLY", "0") == "1":
        return {"ok": True, "log_only": True, "target": target, "payload": payload}
    return http_post_json(target, payload)


def infer(
    model_id: str, prompt: str, params: dict | None = None, url: str | None = None
) -> dict:
    target = (url or DEFAULT_URL).rstrip("/") + "/infer"
    payload = {"model_id": model_id, "prompt": prompt, "params": params or {}}
    if os.getenv("DIRECTOR_CLIENT_LOG_ONLY", "0") == "1":
        return {"ok": True, "log_only": True, "target": target, "payload": payload}
    return http_post_json(target, payload)


def http_post_json(url: str, payload: dict) -> dict:
    r = requests_post(url, json=payload, timeout=10)
    r.raise_for_status()
    return r.json()
