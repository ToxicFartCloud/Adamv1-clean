from fastapi import FastAPI
from sidecars.director.registry import (
    get_models as registry_get_models,
    get_adapter as registry_get_adapter,
)
from sidecars.director.task_routing import choose as routing_choose
from sidecars.models.adapters.base import infer as adapter_infer

APP_NAME = "director"
APP_VERSION = "0.1.0"

app = FastAPI(title=f"Adam {APP_NAME}", version=APP_VERSION)


@app.get("/admin/health")
def admin_health():
    return {"ok": True, "app": APP_NAME, "version": APP_VERSION}


@app.post("/choose")
def choose(body: dict):
    hint = str(body.get("task_hint", "")).strip()
    tags = list(body.get("tags", []) or [])
    models = registry_get_models()
    choice = routing_choose(hint, tags, models)
    return {"ok": True, "choice": choice}


@app.post("/infer")
def infer(body: dict):
    model_id = str(body.get("model_id", "")).strip()
    prompt = str(body.get("prompt", "")).strip()
    params = dict(body.get("params", {}) or {})
    adapter = registry_get_adapter(model_id)
    if adapter is None:
        return {"ok": False, "error": f"unknown model_id: {model_id}"}
    result = adapter_infer(adapter, prompt, **params)
    return {"ok": True, "result": result}
