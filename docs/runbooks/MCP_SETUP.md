# Local MCP System Setup for Adam

This document outlines how to manage the offline-only Model Context Protocol (MCP) adapter. This system allows Adam to use local tools without any network access. All configuration is handled through the `config/mcp/registry.local.json` file.

## Managing MCP Servers

### How to Add a New Server

1.  **Open `config/mcp/registry.local.json`**.
2.  Add a new JSON object to the `servers` list.
3.  The object must contain:
    - `name`: A unique string (e.g., `"my_new_tool"`).
    - `protocol`: Must be `"local"`.
    - `connection`: Must specify `{ "type": "python_module", "module": "path.to.your.server.module" }`.
    - `tools`: A list of tools the server provides, each with a `name`, `description`, and `args` definition.
4.  **Important**: The Python module you reference (e.g., `path.to.your.server.module`) **must** contain a function `run_tool(tool_name, args, config)` that executes the logic.

### How to Disable a Server

To temporarily disable a server without deleting its configuration, simply remove its JSON object from the `servers` list in `registry.local.json`. You can paste it into a separate text file for backup.

## Refreshing the Registry Safely

The term "refresh" in this offline context means **manually editing the JSON file**.

-   **Safety First**: The JSON file must be perfectly formatted. A single missing comma or bracket will cause the adapter to fail when loading the registry.
-   **Recommendation**: Before saving changes to `registry.local.json`, copy its contents and paste them into an online JSON validator (like `jsonlint.com` or a tool in your code editor) to ensure the syntax is correct. This prevents runtime errors for Adam.