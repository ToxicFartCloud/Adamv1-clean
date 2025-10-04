# Adam Core API Contracts

## Overview
This document specifies the local-only HTTP API for Adam Core, built with FastAPI. The endpoints and data structures are designed to be "OpenAI-ish" to maximize compatibility with existing clients and future UI development. All endpoints are prefixed with `/v1`.

## /v1/chat (POST)
**Purpose**: Send a sequence of messages to a model and receive a completion.

**Request JSON**:
-   `model` (string, required): The model to use for the chat completion (e.g., `llama3:8b`). If not provided, falls back to `config.models.default`.
-   `messages` (array of objects, required): An array of message objects, where each object has a `role` (`system`, `user`, `assistant`, or `tool`) and `content` (string).
-   `temperature` (number, optional): Defaults to `0.7`.
-   `max_tokens` (number, optional): The maximum number of tokens to generate. Defaults to `4096`.
-   `stream` (boolean, optional): If `true`, the response will be streamed as Server-Sent Events (SSE). Defaults to `false`.

**Response JSON (non-stream)**:
```json
{
  "id": "chatcmpl-xxxxxxxx",
  "model": "llama3:8b",
  "created": 1677652288,
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! How can I help you today?"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 12,
    "completion_tokens": 9,
    "total_tokens": 21
  }
}
```

**Errors**:
-   `400 Bad Request`: Malformed request body.
-   `503 Service Unavailable`: The Ollama provider is not reachable.

**Example `curl` (non-stream)**:
```bash
curl http://127.0.0.1:8000/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3:8b",
    "messages": [{"role": "user", "content": "Say hi"}]
  }'
```

**Example `curl` (stream)**:
```bash
curl http://127.0.0.1:8000/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3:8b",
    "messages": [{"role": "user", "content": "Tell me a short story." }],
    "stream": true
  }'

# Expected SSE Output:
# data: {"id":"...","choices":[{"delta":{"content":"Once"}}]}
# data: {"id":"...","choices":[{"delta":{"content":" upon"}}]}
# data: {"id":"...","choices":[{"delta":{"content":" a time..."}}]}
# data: [DONE]
```

## /v1/embeddings (POST)
**Purpose**: Generate vector embeddings for a given text or list of texts using EmbeddingGemma.

**Request JSON**:
-   `model` (string, optional): The embedding model to use. Defaults to `embeddinggemma` or `config.models.embedding`.
-   `input` (string or array of strings, required): The text(s) to embed.
-   `dimensions` (integer, optional): For Matryoshka embeddings. If provided, truncate the embedding to this dimension. Supported values: `768`, `512`, `256`.
-   `normalize` (boolean, optional): Whether to normalize the output embeddings. Defaults to `true`.

**Response JSON**:
```json
{
  "data": [
    {
      "index": 0,
      "embedding": [0.0123, -0.0456, ..., 0.0789]
    }
  ],
  "model": "embeddinggemma:latest",
  "usage": {
    "prompt_tokens": 5,
    "total_tokens": 5
  }
}
```

**Errors**:
-   `400 Bad Request`: Malformed request body.
-   `503 Service Unavailable`: The Ollama provider is not reachable.

**Example `curl`**:
```bash
curl http://127.0.0.1:8000/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Hello, world!"
  }'
```

## /v1/ingest (POST)
**Purpose**: Ingest raw text, documents, or URLs. The content will be chunked, embedded, and upserted into the LanceDB vector store.

**Request JSON**:
-   `documents` (array of objects, optional): Each object contains `text` (required), and optional `id`, `source`, `title`.
-   `urls` (array of strings, optional): A list of URLs to fetch and ingest.
-   `chunk_size` (integer, optional): Character count for text chunking. Defaults to `1000`.
-   `chunk_overlap` (integer, optional): Character count for overlap. Defaults to `150`.
-   `metadata` (object, optional): A metadata object to be merged with each document's metadata.

**Response JSON**:
```json
{
  "inserted": 42,
  "vector_dim": 768,
  "index_name": "default_index",
  "sample_ids": ["doc1_chunk0", "doc1_chunk1"]
}
```

**Errors**:
-   `400 Bad Request`: Malformed request or missing `documents`/`urls`.
-   `500 Internal Server Error`: Failure during fetching, chunking, or indexing.

**Example `curl`**:
```bash
curl http://127.0.0.1:8000/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [{
      "source": "manual.txt",
      "text": "This is the first document..."
    }]
  }'
```

## /v1/search (POST)
**Purpose**: Perform a vector similarity search over the LanceDB index.

**Request JSON**:
-   `query` (string, required): The text to search for.
-   `top_k` (integer, optional): Number of results to return. Defaults to `8`.
-   `filters` (object, optional): Key-value pairs to filter metadata (e.g., `{"source": "manual.txt"}`).

**Response JSON**:
```json
{
  "matches": [
    {
      "id": "doc1_chunk5",
      "score": 0.89,
      "text": "... a relevant chunk of text ...",
      "metadata": {"source": "manual.txt", "title": "Manual"}
    }
  ],
  "query_embedding_dim": 768
}
```

**Errors**:
-   `400 Bad Request`: Malformed request.

**Example `curl`**:
```bash
curl http://127.0.0.1:8000/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do I start?",
    "top_k": 3
  }'
```

## /v1/tools/{tool_name} (POST)
**Purpose**: A proxy to execute a registered MCP-like tool.

**Request JSON**:
-   `args` (object, required): An object containing the arguments for the specified tool.

**Response JSON**:
```json
{
  "tool": "web-fetch",
  "ok": true,
  "result": {"status": 200, "content": "...", "bytes": 12345}
}
```

## Common Error Envelope
All `4xx` and `5xx` responses should conform to this structure.
```json
{
  "error": {
    "type": "invalid_request_error",
    "message": "The 'messages' field is required."
  },
  "request_id": "req_xxxxxxxx"
}
```