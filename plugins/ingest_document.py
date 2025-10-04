# plugins/ingest_document.py

import os
import hashlib
from typing import Any, Dict

# Fixed import path
from src.adam.adapters import EmbeddingAdapter, VectorStoreAdapter

METADATA = {
    "label": "Document Ingestor",
    "description": "Chunks and stores a document in the vector store for RAG.",
    "ui_action": False,
    "executable": True,
}


def run(**kwargs) -> Dict[str, Any]:
    """
    Reads a document, splits it into chunks, and upserts it into the vector store.

    Expected kwargs:
        - file_path: str (The full path to the document to ingest)
    """
    file_path = kwargs.get("file_path")
    if not file_path or not isinstance(file_path, str):
        return {
            "ok": False,
            "data": None,
            "error": "file_path must be a non-empty string.",
        }
    if not os.path.exists(file_path):
        return {"ok": False, "data": None, "error": f"File not found: {file_path}"}

    try:
        # 1. Read the document content
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        if not content.strip():
            return {"ok": False, "data": None, "error": "File is empty."}

        # 2. Split into chunks (improved: handle various formats)
        chunks = _split_into_chunks(content)
        if not chunks:
            return {"ok": False, "data": None, "error": "No valid text chunks found."}

        # 3. Prepare data
        ids = [
            hashlib.md5(chunk.encode("utf-8", errors="ignore")).hexdigest()
            for chunk in chunks
        ]
        metadata = [{"source": file_path, "chunk_index": i} for i in range(len(chunks))]

        # 4. Initialize adapters
        embedder = EmbeddingAdapter()
        vector_store = VectorStoreAdapter()

        # 5. Generate embeddings
        embeddings = embedder.embed_texts(chunks)

        # 6. Upsert to vector store
        vector_store.upsert(
            ids=ids, documents=chunks, embeddings=embeddings, metadata=metadata
        )

        return {
            "ok": True,
            "data": f"Successfully ingested {len(chunks)} chunks from {file_path}.",
            "error": None,
        }

    except Exception as e:
        return {
            "ok": False,
            "data": None,
            "error": f"Failed to ingest document: {str(e)}",
        }


def _split_into_chunks(text: str, max_chunk_size: int = 500) -> list[str]:
    """Split text into chunks with overlap for better context retention."""
    if not text.strip():
        return []

    # First try paragraph splitting
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if len(paragraphs) > 1 and all(len(p) < max_chunk_size for p in paragraphs):
        return paragraphs

    # Fallback to recursive character splitting
    chunks = []
    current_chunk = ""
    sentences = text.replace("\n", " ").split(". ")

    for sentence in sentences:
        if len(current_chunk) + len(sentence) < max_chunk_size:
            current_chunk += sentence + ". "
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence + ". "

    if current_chunk:
        chunks.append(current_chunk.strip())

    return [c for c in chunks if c]
