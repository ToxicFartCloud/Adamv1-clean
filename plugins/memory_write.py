# plugins/memory_write.py
import logging
import hashlib
from typing import Any, Dict
from src.adam.adapters import SentenceTransformerEmbedder, ChromaVectorStore

logger = logging.getLogger("adam")

METADATA = {
    "label": "Memory Writer",
    "description": "Writes a single piece of information to long-term memory.",
    "ui_action": False,
    "executable": True,
}


def run(**kwargs) -> Dict[str, Any]:
    content = kwargs.get("content")
    if not content or not isinstance(content, str):
        return {
            "ok": False,
            "data": None,
            "error": "'content' must be a non-empty string.",
        }

    try:
        logger.info("Writing to memory...")
        embedder = SentenceTransformerEmbedder()
        vector_store = ChromaVectorStore()

        if not embedder.model:
            return {
                "ok": False,
                "data": None,
                "error": "Embedding model not available.",
            }
        if not vector_store.collection:
            return {"ok": False, "data": None, "error": "Vector store not available."}

        # Generate ID and embedding
        doc_id = hashlib.md5(content.encode()).hexdigest()
        embedding = embedder.embed_texts([content])[0]

        # Store in vector DB
        vector_store.upsert(
            ids=[doc_id],
            documents=[content],
            embeddings=[embedding],
            metadata=[{"source": "memory_write", "type": "user_note"}],
        )

        logger.info("Memory write successful.")
        return {
            "ok": True,
            "data": f"Stored content with ID: {doc_id[:8]}...",
            "error": None,
        }

    except Exception as e:
        logger.error(f"Memory write failed: {e}", exc_info=True)
        return {"ok": False, "data": None, "error": str(e)}
