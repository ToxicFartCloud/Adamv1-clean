---FILE_START path: docs/specs/anythingllm-port-map.md
# AnythingLLM → Adam Port Map (Clean-Room Notes)

## Goal
We are re-creating observed behavior from AnythingLLM, not its code, to build our local-only Python agent, "Adam". This document summarizes the parts we will mirror and where we will intentionally differ, ensuring a clean-room implementation.

## Map

| Observed in AnythingLLM (Behavior/Shape) | Adam Behavior (Our Implementation) |
| :--- | :--- |
| **Workspaces** | A workspace is a directory containing a LanceDB table and settings. Adam manages this via a single `config/adam.yaml` file, which can define multiple "contexts" that map to different data stores. |
| **Model Selection** | UI dropdown per workspace for chat & embeddings. | Models are defined in `config/adam.yaml` (`models.default`, `models.heavy`, `models.embedding`). The API request can override the default. |
| **Message Schema** | OpenAI-like: `role` ("system", "user", "assistant"), `content`. | Identical: `{"role": "user", "content": "..."}`. We will also support `tool_calls` and `tool_responses` for agentic workflows. |
| **Provider Selection** | Pluggable providers (OpenAI, Azure, Anthropic, Ollama). | Hardcoded to a single provider type: Ollama. The base URL is configurable. |
| **Embeddings Path** | Separate model selection for embeddings. Chunks text and sends to the provider's embedding endpoint. | Uses `embeddinggemma` via Ollama's `/api/embed` endpoint. Configurable via `models.embedding` in `adam.yaml`. |
| **Chunking Strategy** | UI-configurable chunk size and overlap. Recursive character text splitter. | Fixed strategy initially: `chunk_size=1000` characters, `overlap=150`. Implemented in our `/v1/ingest` endpoint. |
| **Vector Store** | Pluggable (LanceDB, Chroma, Pinecone, etc.). | LanceDB only. Path configured in `adam.yaml`. Schema is fixed. |
| **RAG Flow** | 1. User query -> 2. Embed query -> 3. Vector search -> 4. Stuff results into context -> 5. Generate response -> 6. Show citations. | Identical flow. 1. `/v1/search` retrieves context. 2. Context is formatted into a system prompt. 3. `/v1/chat` generates the response. 4. Citations are derived from search results' metadata. |
| **Tool Execution** | "Tools" are custom functions that can be called. Seems to follow a specific JSON format for requests/responses. | We will adopt a similar pattern, exposing local plugins via `/v1/tools/{tool_name}`. This is inspired by the MCP (Model-Centric Programming) pattern. |
| **Error/Timeout Handling** | General error messages in UI; seems to have basic timeouts. | Explicit timeouts (connect/read) and retry logic (exponential backoff) for the Ollama provider. Standard HTTP error codes (4xx, 5xx) with a consistent JSON error envelope. |
| **API: Chat** | `/api/v1/workspace/{slug}/chat` | `/v1/chat` (non-workspace specific; context is managed by the caller or higher-level orchestrator). |
| **API: Embeddings** | Handled internally or via a generic provider endpoint. | `/v1/embeddings` for direct access to the embedding model. |
| **API: Ingest** | `/api/v1/document/upload` (files), `/api/v1/workspace/{slug}/update-embeddings` (URLs/text). | `/v1/ingest` for all data sources (raw text, URLs). |
| **API: Search** | Internal; likely not a public endpoint. | `/v1/search` for direct vector search queries. |
| **Logging** | Logs to console and/or a file. | Structured logging (JSON) to `logs/adam.log`. Key events like API calls, tool usage, and errors will be logged with request IDs. |
| **System Prompt** | Customizable per workspace. | A base system prompt is defined, but can be overridden or extended by the RAG pipeline or API caller. |
| **Citations** | Appears in UI, linking back to source documents. | The `/v1/search` response includes source metadata, which clients can use to display citations. The agent itself may optionally append citation markers like `[source:1]` to its response. |
| **Streaming** | SSE (Server-Sent Events) for chat responses. | Identical: `/v1/chat` with `stream: true` will use SSE. |
| **Environment Vars** | Uses `.env` file for configuration (e.g., `OLLAMA_BASE_URL`). | Uses a central `config/adam.yaml` file. Environment variables can override YAML values for containerized deployments. |
| **Authentication** | API keys for multi-user instances. | None. Adam is local-only and single-tenant. The API is exposed on localhost without authentication. |

## Notes

-   **License Stance**: This is a clean-room implementation. We are replicating observed functionality, not using or viewing any of AnythingLLM's source code. Our goal is to create a compatible but independent system tailored to our specific stack.
-   **Deviations**:
    -   **Stack**: We are Python/FastAPI/LanceDB, whereas AnythingLLM is Node.js. This is a fundamental architectural difference.
    -   **Configuration**: We use a single `adam.yaml` file instead of a `.env` file and database-stored settings to simplify setup and version control of configurations.
    -   **Single-Provider**: We are intentionally limiting Adam to Ollama only to reduce complexity.
    -   **Stateless API**: Adam's core API is stateless. The concept of a "workspace" or "context" is managed by the client or a higher-level orchestrator, not persisted inside the API's state. This makes the core services more robust and scalable.
---FILE_END