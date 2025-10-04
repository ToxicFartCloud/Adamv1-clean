# Adam Plugins Guide

This guide provides instructions for developers on how to create and use plugins within the Adam framework.

## Creating a Plugin

1.  **Create a Directory**: Create a new directory for your plugin under `adam_tools/plugins/`. The directory name should be the name of your plugin (e.g., `my_awesome_plugin`).

2.  **Implement the `run` function**: In the `__init__.py` file within your plugin's directory, define a function `run(**kwargs)`. This function is the entrypoint for your plugin. It must accept keyword arguments and return a dictionary with the following structure:
    ```python
    {
        "ok": True,      # boolean
        "data": ...,     # any
        "error": None    # str or None
    }
    ```

3.  **Register the Plugin**: Add an entry for your plugin in `adam_tools/plugins/registry.yaml`. Follow the existing format:
    ```yaml
    - name: "my_awesome_plugin"
      version: "0.1.0"
      entrypoint: "adam_tools.plugins.my_awesome_plugin"
      enabled": true
    ```

4.  **Add Tests**: Create a test file in the `tests/` directory (e.g., `tests/test_my_awesome_plugin.py`) to ensure your plugin works as expected.

## Calling a Plugin

Use the `call_plugin` function from `adam_tools.plugins.base`.

```python
from adam_tools.plugins.base import call_plugin

result = call_plugin("plugin_name", {"param1": "value1", "param2": "value2"})

if result["ok"]:
    print("Plugin succeeded:", result["data"])
else:
    print("Plugin failed:", result["error"])

```

## First-wave Safe Ops

The first-wave safe operations plugins provide vetted shells around higher-risk automation. They all accept payloads shaped as:

```
{"action": "<verb>", "args": {...}, "dry_run": true|false, "reason": "<why>"}
```

Every plugin returns:

```
{
  "ok": true|false,
  "action": "...",
  "dry_run": true|false,
  "approval_required": true|false,
  "plan": ["step 1", ...],
  "report": {"summary": "...", "details": {...}},
  "artifacts": [<paths or blobs>],
  "logs_path": "logs/audit.jsonl"
}
```

All safe-ops calls append an audit line to `logs/audit.jsonl` containing timestamp, user (`Adam`), plugin, action, args, cwd, `dry_run`, `ok`, and reason. Use dry-run by default; real execution must flow through `guard.approval` and `backup.snapshot`.

### Plugin overview
- `proc.app`: Plans application launch/focus/kill steps; `kill` requires approval when `dry_run` is false.
- `proc.ps`: Returns stub process listings for monitoring dashboards (read-only).
- `web.search`: Returns demo results until a provider (e.g., SearxNG) is configured.
- `git.ops`: Summarises git status/branches and drafts guarded commit plans.
- `wmgr`: Lists windows and documents focus/move strategies without moving anything.
- `guard.approval`: Shells out to `scripts/automation/approval_cmd.py` to collect human approval.
- `backup.snapshot`: Records pre/post snapshot commands against `auto_snapshot.sh` to gate risky changes.

Safety posture: treat `dry_run=true` as the default. Before executing state-changing actions (`dry_run=false`), acquire approval via `guard.approval` and run `backup.snapshot` hooks to capture the environment.
