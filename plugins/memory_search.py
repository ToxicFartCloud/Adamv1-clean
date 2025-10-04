# plugins/memory_search.py

import logging
from typing import Any, Dict

# Import the concrete adapter implementations
from src.adam.adapters import SentenceTransformerEmbedder, ChromaVectorStore

logger = logging.getLogger("adam")

METADATA = {
    "label": "Memory Search",
    "description": "Searches the vector store for information relevant to a query.",
    "ui_action": False,
    "executable": True,
}


def run(**kwargs) -> Dict[str, Any]:
    """
    Embeds a query and searches the vector store for the most relevant document chunks.

    Expected kwargs:
        - query: str (The natural language query to search for)
        - top_k: int (Optional, the number of results to return. Defaults to 3)
    """
    query = kwargs.get("query")
    top_k = kwargs.get("top_k", 3)

    if not query or not isinstance(query, str):
        return {
            "ok": False,
            "data": None,
            "error": "A 'query' argument is required and must be a string.",
        }

    if not isinstance(top_k, int) or top_k < 1:
        top_k = 3

    try:
        logger.info(f"Searching memory for query: '{query[:50]}...'")

        # 1. Initialize adapters
        embedder = SentenceTransformerEmbedder()
        vector_store = ChromaVectorStore()

        # 2. Validate adapters initialized correctly
        if not hasattr(embedder, "model") or embedder.model is None:
            return {
                "ok": False,
                "data": None,
                "error": "Embedding model failed to initialize. Check sentence-transformers installation.",
            }

        if not hasattr(vector_store, "collection") or vector_store.collection is None:
            return {
                "ok": False,
                "data": None,
                "error": "Vector store failed to initialize. Check chromadb installation.",
            }

        logger.debug("RAG adapters initialized successfully.")

        # 3. Generate query embedding
        query_vector = embedder.embed_texts([query])[0]
        logger.debug("Query embedding generated.")

        # 4. Search vector store
        search_results = vector_store.search(query_vector=query_vector, top_k=top_k)
        logger.info(f"Memory search completed. Found {len(search_results)} results.")

        return {"ok": True, "data": search_results, "error": None}

    except Exception as e:
        error_msg = f"Memory search failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {"ok": False, "data": None, "error": error_msg}
