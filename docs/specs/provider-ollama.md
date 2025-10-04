---FILE_START path: docs/specs/provider-ollama.md
# Ollama Provider (Chat + Embeddings) — Spec

## Base
-   **Base URL**: The provider will read its base URL from the `OLLAMA_BASE_URL` environment variable, falling back to `http://127.0.0.1:11434` if not set. This can also be configured in `config/adam.yaml`.
-   **Endpoints Used**:
    -   `/api/chat`
    -   `/api/embed`

## Chat (`/api/chat`)

### Request Mapping
The provider must translate the OpenAI-ish request from `/v1/chat` into the format expected by Ollama's `/api/chat`.

| Adam API Field  | Ollama API Field      | Notes                                                              |
| :-------------- | :-------------------- | :----------------------------------------------------------------- |
| `model`         | `model`               | Direct mapping.                                                    |
| `messages`      | `messages`            | Direct mapping.                                                    |
| `stream`        | `stream`              | Direct mapping.                                                    |
| `temperature`   | `options.temperature` | Direct mapping.                                                    |
| `max_tokens`    | `options.num_predict` | Maps to `num_predict`.                                             |
| `stop`          | `options.stop`        | Maps to an array of stop strings.                                  |
| (Not available) | `options.num_ctx`     | Configurable in `adam.yaml` per model, not per-request.            |
| (Not available) | `options.repeat_penalty`, `options.top_p`, `options.top_k`, `options.seed` | Can be exposed in Adam's API in the future if needed. For now, use Ollama defaults or set in `adam.yaml`. |

### Behavior
-   **Streaming**: If `stream: true`, the provider will iterate over the chunked SSE response from Ollama. Each JSON chunk will be parsed. If it contains a `message` object, it's forwarded to the client. If `done: true`, the stream is closed.
-   **Non-Stream**: The provider will make a single request and wait for the full response. The `message.content` will be returned.
-   **Retries**: On connection errors or `5xx` HTTP status codes, the provider will implement an exponential backoff retry strategy.
    -   Max attempts: 3
    -   Initial delay: 1 second
    -   Multiplier: 2
-   **Timeouts**:
    -   Connect timeout: 5 seconds
    -   Read timeout: 120 seconds
-   **Error Handling**: Ollama errors (e.g., model not found) will be parsed and mapped to Adam's common error envelope with an appropriate HTTP status code (e.g., 404 or 500).

## Embeddings (`/api/embed`)

### Request
-   `model`: Defaults to `embeddinggemma` or the value from `config.models.embedding`.
-   `prompt`: The `input` from the Adam API request is mapped to Ollama's `prompt` field.
-   **Matryoshka Dimensions**: Ollama's `/api/embed` does not currently have a `dimensions` parameter. If the user requests smaller dimensions (e.g., 512, 256), the provider will receive the full 768-dimension embedding and **truncate it** before returning the response. This must be logged clearly.
-   **Normalization**: The provider will not perform normalization itself but will rely on the underlying model's behavior. We assume `embeddinggemma` provides normalized embeddings.

### Response
-   The `embedding` array from the Ollama response is extracted.
-   The provider will verify that the length of the returned embedding matches the expected dimensions (either default 768 or the requested truncated dimension) and log the shape on first successful call.

## Keep-alive Guidance
-   The provider will allow a `keep_alive` parameter in the request body's `options`. This controls how long the model stays loaded in memory after the request.
-   Default: `5m` (unload after 5 minutes of inactivity).
-   This can be overridden by the `OLLAMA_KEEP_ALIVE` environment variable, which sets a system-wide default. The per-request value takes precedence.

## Examples

### 1. Non-Stream Chat
**Request to Ollama `/api/chat`**:
```json
{
  "model": "llama3:8b",
  "messages": [{"role": "user", "content": "Say hi"}],
  "stream": false,
  "options": {
    "temperature": 0.7,
    "num_predict": 4096
  }
}
```
**Response from Ollama `/api/chat` (skeleton)**:
```json
{
  "model": "llama3:8b",
  "created_at": "...",
  "message": {
    "role": "assistant",
    "content": "Hello there!"
  },
  "done": true,
  "total_duration": "...",
  "prompt_eval_count": 12,
  "eval_count": 9
}
```

### 2. Stream Chat
**Request to Ollama `/api/chat`**:
```json
{
  "model": "llama3:8b",
  "messages": [{"role": "user", "content": "Say hi"}],
  "stream": true
}
```
**Response from Ollama `/api/chat` (skeleton)**:
```
{"model":"...","message":{"role":"assistant","content":"Hello"}}
{"model":"...","message":{"role":"assistant","content":" there"}}
{"model":"...","done":true,"total_duration":"..."}
```

### 3. Embeddings
**Request to Ollama `/api/embed`**:
```json
{
  "model": "embeddinggemma",
  "prompt": "This is the text to embed."
}
```
**Response from Ollama `/api/embed` (skeleton)**:
```json
{
  "embedding": [0.1, 0.2, ..., -0.5]
}
```
---FILE_END