"""ChromaDB backend for memory search."""

from typing import List
from .base import MemorySearchBackend, register_backend

try:
    import chromadb
    from chromadb.config import Settings

    _available = True
except ImportError:
    _available = False


if _available:

    class ChromaMemoryBackend(MemorySearchBackend):
        def __init__(self, collection_name: str = "default"):
            self.client = chromadb.Client(Settings())
            self.collection = self.client.get_or_create_collection(collection_name)
            print(
                f"[DEBUG] ChromaDB backend initialized with collection: {collection_name}"
            )

        def search(self, query: str, top_k: int) -> List[str]:
            results = self.collection.query(query_texts=[query], n_results=top_k)
            docs = results.get("documents", [])
            return [doc for doc_list in docs for doc in doc_list] if docs else []

        async def asearch(self, query: str, top_k: int) -> List[str]:
            import asyncio

            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self.search, query, top_k)

    register_backend("chroma", ChromaMemoryBackend)
