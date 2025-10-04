# MCP Tools — Contracts

This document defines the contracts for local tools exposed via the `/v1/tools/{tool_name}` endpoint, following a Model-Centric Programming (MCP) pattern.

## Tool Call Envelope

All tool calls, regardless of the specific tool, use a consistent request and response envelope.

**Request**: `POST /v1/tools/{tool_name}`
```json
{
  "args": {
    "param1": "value1",
    "param2": "value2"
  }
}
```

**Response (Success)**:
```json
{
  "tool": "tool_name",
  "ok": true,
  "result": {
    "output_key": "output_value"
  }
}
```

**Response (Failure)**:
```json
{
  "tool": "tool_name",
  "ok": false,
  "error": "A descriptive error message."
}
```

---

## `web-fetch`

**Purpose**: Fetches content from a given URL.

-   **Command**: `fetch_url`
-   **Arguments**:
    -   `url` (string, required): The URL to fetch.
-   **Security & Constraints**:
    -   **Protocol Allowlist**: Must be `http://` or `https://`.
    -   **Domain Allowlist**: The target domain must be present in a configurable list in `adam.yaml`. If the list is empty, all domains are allowed.
    -   **Size Limit**: The response body cannot exceed 5 MB.
    -   **Content-Type Rejectlist**: Rejects binary content types like `application/octet-stream` by default.
-   **Return (`result`)**:
    -   `ok` (boolean): `true` if the fetch was successful (2xx status code).
    -   `status` (integer): The HTTP status code.
    -   `headers` (object): A key-value map of response headers.
    -   `content` (string): The decoded text content of the response body.
    -   `content_type` (string): The `Content-Type` header value.
    -   `bytes` (integer): The size of the response body in bytes.
-   **Errors**:
    -   "Network error: [reason]": For DNS lookup failures, timeouts, etc.
    -   "Disallowed domain": If the URL's domain is not in the allowlist.
    -   "Disallowed protocol": If the URL is not HTTP/HTTPS.
    -   "Content size exceeds limit of 5 MB."
    -   "Request failed with status code: [status]".

### `curl` Example
```bash
curl -X POST http://127.0.0.1:8000/v1/tools/web-fetch \
  -H "Content-Type: application/json" \
  -d '{"args": {"url": "https://example.com"}}'
```

---

## `file-io`

**Purpose**: Read from and write to the local filesystem within a sandboxed directory.

### `read_file`
-   **Command**: `read_file`
-   **Arguments**:
    -   `path` (string, required): The path to the file to read.
-   **Security**:
    -   **Path Allowlist**: The path must resolve to a location inside `/home/ToxicFartCloud/Projects/Adamv1/data`. Any attempts to traverse outside this directory (e.g., `../`) must be rejected.
-   **Return (`result`)**:
    -   `ok` (boolean): `true`.
    -   `contents` (string): The content of the file.
-   **Errors**:
    -   "File not found": If the path does not exist.
    -   "Access denied": If the path is outside the allowed directory.
    -   "Encoding error": If the file cannot be read as UTF-8 text.

### `write_file`
-   **Command**: `write_file`
-   **Arguments**:
    -   `path` (string, required): The path to the file to write.
    -   `content` (string, required): The content to write to the file.
-   **Security**:
    -   **Path Allowlist**: Same as `read_file`.
    -   **Behavior**: Creates parent directories if they do not exist (`mkdir -p`). Overwrites the file if it already exists.
-   **Return (`result`)**:
    -   `ok` (boolean): `true`.
    -   `bytes_written` (integer): The number of bytes written to the file.
-   **Errors**:
    -   "Access denied": If the path is outside the allowed directory.
    -   "Failed to write file": For filesystem errors (e.g., disk full).

### `curl` Examples
```bash
# Read a file
curl -X POST http://127.0.0.1:8000/v1/tools/file-io \
  -H "Content-Type: application/json" \
  -d '{"args": {"command": "read_file", "path": "my-notes.txt"}}'

# Write a file
curl -X POST http://127.0.0.1:8000/v1/tools/file-io \
  -H "Content-Type: application/json" \
  -d '{"args": {"command": "write_file", "path": "new-file.txt", "content": "Hello from Adam!"}}'
```

---

## `adam-sys-audit`

**Purpose**: Provides information about the system Adam is running on.

### `list_hardware`
-   **Command**: `list_hardware`
-   **Arguments**: None.
-   **Return (`result`)**:
    -   `cpu` (object): `{cores, threads, frequency_mhz}`.
    -   `gpus` (array): `[{name, vram_gb, driver_version}]`.
    -   `ram_gb` (object): `{total, used, free}`.
    -   `disks` (array): `[{mount, size_gb, used_gb}]`.
    -   `os` (string): e.g., "linux".

### `list_software`
-   **Command**: `list_software`
-   **Arguments**: None.
-   **Return (`result`)**:
    -   `os_version` (string): e.g., "Ubuntu 22.04.3 LTS".
    -   `kernel` (string): e.g., "5.15.0-78-generic".
    -   `python_version` (string): e.g., "3.11.4".
    -   `packages` (array): A list of key packages and their versions (e.g., `["fastapi==0.103.2", "lancedb==0.5.3"]`).

### `diff_baseline`
-   **Command**: `diff_baseline`
-   **Arguments**:
    -   `baseline` (object, required): A previous output from `list_hardware` or `list_software`.
-   **Return (`result`)**:
    -   `changes` (object): `{added: [...], removed: [...], modified: [...]}` detailing differences from the baseline.

### Logging
All calls to `adam-sys-audit` tools are logged to the main `adam.log` with the `tool_call` event type for security and monitoring purposes.

### `curl` Example
```bash
curl -X POST http://127.0.0.1:8000/v1/tools/adam-sys-audit \
  -H "Content-Type: application/json" \
  -d '{"args": {"command": "list_hardware"}}'
```
---
