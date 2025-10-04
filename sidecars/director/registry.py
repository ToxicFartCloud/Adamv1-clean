from importlib import import_module
from sidecars.director.yaml_compat import yaml_safe_load

MODELS_CACHE = None
ADAPTERS_CACHE = {}
CONFIG_PATH = "configs/models.yaml"


def _load_models():
    global MODELS_CACHE
    if MODELS_CACHE is not None:
        return MODELS_CACHE
    cfg = yaml_safe_load_path(CONFIG_PATH)
    MODELS_CACHE = list(cfg.get("models", []) or [])
    return MODELS_CACHE


def get_models():
    return _load_models()


def get_tags():
    tags = set()
    for m in _load_models():
        for t in m.get("tags", []) or []:
            tags.add(str(t))
    return tags


def get_adapter(model_id: str):
    model = next((m for m in _load_models() if m.get("id") == model_id), None)
    if not model:
        return None
    name = str(model.get("adapter", "")).strip()
    if name == "llama_cpp":
        return import_adapter("sidecars.models.adapters.llama_cpp")
    if name == "hf_pipeline":
        return import_adapter("sidecars.models.adapters.hf_pipeline")
    if name == "vllm":
        return import_adapter("sidecars.models.adapters.vllm")
    if name == "tool_exec":
        return import_adapter("sidecars.models.adapters.tool_exec")
    return None


def yaml_safe_load_path(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return yaml_safe_load(f.read())


def import_adapter(dotted: str):
    if dotted in ADAPTERS_CACHE:
        return ADAPTERS_CACHE[dotted]
    mod = import_module(dotted)
    ADAPTERS_CACHE[dotted] = mod
    return mod
