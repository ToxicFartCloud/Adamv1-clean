import yaml


def yaml_safe_load(text: str):
    return yaml.safe_load(text) or {}
