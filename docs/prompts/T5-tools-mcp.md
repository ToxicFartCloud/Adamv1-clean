Task: Define MCP tool contracts. Save to: docs/specs/tools-mcp.md
Tools:
- web-fetch.fetch_url({url}) -> {status, headers, content, content_type}; domain allowlist.
- file-io.read_file / write_file under /home/ToxicFartCloud/Projects/Adamv1/data (allowlist).
- adam-sys-audit.{list_hardware,list_software,diff_baseline} JSON schemas.
Include: example invocations, error handling rules.
