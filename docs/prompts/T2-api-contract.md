Task: Define Adam Core API (spec only). Save to: docs/specs/api-contracts.md
Endpoints:
- /v1/chat (OpenAI-ish: messages[], model, temperature, stream)
- /v1/embeddings (input[], model)
- /v1/ingest (docs/urls, chunk_size, overlap, metadata)
- /v1/search (query, top_k, filters)
- /v1/tools/<tool> (name, args)
Include: error shapes; curl examples; all-local assumptions (Ollama).
