Task: Define RAG pipeline. Save to: docs/specs/rag-pipeline.md
Ingest: chunk_size=1000, overlap=150; metadata {source,title,page,language}.
Embed: EmbeddingGemma (768-d default; MRL 512/256 optional).
Store: LanceDB @ ./data/lancedb (schema + indices).
Search: cosine, top_k=8; return {chunks,scores,citations}.
Include a tiny eval plan + sample index layout.
