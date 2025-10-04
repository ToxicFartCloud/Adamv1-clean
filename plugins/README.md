# Adam Plugin Specification

This document outlines the standards for creating, registering, and using plugins within the Adam ecosystem.

## Plugin Contract
- **Entrypoint**: Each plugin must expose a `run(**kwargs)` function in its `__init__.py`.
- **Return Schema**: The `run` function must return a dictionary with the shape `{"ok": bool, "data": any, "error": str|None}`.
- **Configuration**: Plugins can have an optional `config/plugins.{plugin_name}.yaml` file.
- **Logging**: Plugins must log JSON objects to `logs/plugins/{plugin_name}.log`.

## Registration
Plugins are registered in `plugins/registry.yaml`. The registry includes `name`, `version`, `entrypoint`, and an `enabled` flag.
